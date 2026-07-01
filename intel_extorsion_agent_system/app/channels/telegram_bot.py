import asyncio
import logging
import httpx
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

TELEGRAM_CONFIG = {
    "BOT_NAME": "IntelExtorsión Telegram",
    "BOT_USERNAME": "intelextorsion_bot",
    "WELCOME_MESSAGE": "¡Bienvenido al sistema de Inteligencia Ciudadana!",
    "SUPPORT_CHANNEL": "@intelextorsion_support",
}

UPLOAD_DIR = "/app/uploads/evidencias"


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self._task = None
        self.user_states = {}
        self.user_data = {}
        self.pending_batches = {}
        self.start_time = datetime.now()

    def start_background(self):
        if not self.token:
            print("TELEGRAM_BOT_TOKEN no configurado en settings. El bot no iniciará.", flush=True)
            logger.warning("TELEGRAM_BOT_TOKEN no configurado en settings. El bot de Telegram no se iniciará.")
            return
        print(f"Bot de Telegram programado en segundo plano con token: {self.token[:10]}...", flush=True)
        self._task = asyncio.create_task(self._start_loop())
        logger.info("Bot de Telegram programado para iniciar en segundo plano.")

    async def _start_loop(self):
        self.is_running = True
        print("Ciclo de escucha del bot de Telegram iniciado.", flush=True)
        logger.info("Iniciando ciclo de escucha del bot de Telegram...")

        while self.is_running:
            try:
                updates = await self.get_updates()
                for update in updates:
                    print(f"Actualización recibida del bot: {update}", flush=True)
                    await self.process_update(update)
            except Exception as e:
                print(f"Error en ciclo de actualización del bot de Telegram: {e}", flush=True)
                logger.error(f"Error en ciclo de actualización del bot de Telegram: {e}")
            await asyncio.sleep(2)

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
        await self.http_client.aclose()
        logger.info("Bot de Telegram detenido.")

    async def get_updates(self) -> list:
        url = f"{self.api_url}/getUpdates"
        params = {"offset": self.offset, "timeout": 20}
        try:
            resp = await self.http_client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        self.offset = updates[-1]["update_id"] + 1
                    return updates
            else:
                print(f"[Telegram Bot] Error en getUpdates (HTTP {resp.status_code}): {resp.text}", flush=True)
                logger.error(f"Error en getUpdates de Telegram (HTTP {resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[Telegram Bot] Excepción al conectar con Telegram: {e}", flush=True)
            logger.debug(f"Error al obtener actualizaciones de Telegram: {e}")
        return []

    # ---------------------------------------------------------------------------
    # Procesamiento de actualizaciones
    # ---------------------------------------------------------------------------

    async def process_update(self, update: dict):
        callback_query = update.get("callback_query")
        if callback_query:
            await self.handle_callback_query(callback_query)
            return

        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        caption = message.get("caption", "")
        voice = message.get("voice")
        audio = message.get("audio")
        photo = message.get("photo")
        document = message.get("document")
        video = message.get("video")

        chat_state = self.user_states.get(chat_id, 'idle')

        # Comandos globales
        if text and (text.startswith("/start") or text.startswith("/help")):
            await self.send_message(chat_id, (
                f"🛡️ *{TELEGRAM_CONFIG['WELCOME_MESSAGE']}*\n\n"
                f"🤖 *{TELEGRAM_CONFIG['BOT_NAME']}*\n\n"
                "⚠️ *IMPORTANTE:* Este sistema NO es un canal directo de denuncia a la policía.\n"
                "Es una plataforma de *INTELIGENCIA CIUDADANA* que recibe reportes de extorsión, los analiza con IA forense, y entrega información procesada a las autoridades competentes (DIVINCRI La Libertad) para que tomen acciones operativas.\n\n"
                "📋 *¿Qué hace este sistema?*\n"
                "• Recibe tu reporte de forma 100% anónima\n"
                "• Analiza la información con 10 agentes de IA especializados\n"
                "• Correlaciona tu caso con otros reportes similares\n"
                "• Entrega inteligencia procesada a las autoridades para operativos\n"
                "• Sella evidencias en blockchain para trazabilidad judicial\n\n"
                "✍️ *¿Cómo reportar información?*\n"
                "• Escribe una descripción detallada en un mensaje de texto\n"
                "• Envía una nota de voz o archivo de audio (lo transcribiremos automáticamente)\n"
                "• Adjunta imágenes o documentos de evidencia\n\n"
                "🔍 *¿Cómo consultar tu reporte?*\n"
                "• Envía el código de tu caso en formato `TRJ-XXXX` para ver su estado de análisis\n\n"
                "📞 *Para denuncias formales:* Si necesitas presentar una denuncia formal ante la Fiscalía o la PNP, utiliza la línea 111 o acude a la comisaría más cercana. Este sistema complementa, pero no reemplaza, los canales oficiales de denuncia."
            ))
            return

        if text:
            clean_text = text.lower().strip()
            if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
                self.user_states[chat_id] = 'idle'
                if chat_id in self.pending_batches:
                    batch = self.pending_batches.pop(chat_id)
                    if batch.get("timer"):
                        batch["timer"].cancel()
                await self.send_message(chat_id, "❌ *Reporte cancelado.*\n\nEl asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué deseas hacer hoy? Puedes volver a iniciar escribiendo 'reportar' o 'denunciar'.")
                return

        # --- CLASSIFYING (RF-01) ---
        if chat_state == 'classifying':
            clean_text = text.lower().strip() if text else ""
            if clean_text in ["1", "uno", "particular", "banda", "criminal", "delincuente"]:
                self.user_states[chat_id] = 'waiting_for_denuncia'
                await self.send_message(chat_id, "📝 *Asistente de Ingesta Activado.*\n\nPor favor, describa detalladamente lo sucedido **en su siguiente mensaje**. Recuerde incluir:\n• Teléfonos desde donde le contactaron\n• Nombres o cuentas bancarias de cobro si se las dieron\n• Tipo de amenaza o exigencias de dinero\n• Zona o lugar donde ocurrieron los hechos\n\nTambién puede adjuntar imágenes o documentos de evidencia.\n\n⚠️ Su información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa. Si desea abortar, escriba *cancelar*.")
                return
            elif clean_text in ["2", "dos", "funcionario", "policía", "policia", "autoridad", "pnp"]:
                self.user_states[chat_id] = 'idle'
                await self.send_message(chat_id, "🛡️ *Reporte contra servidor público / PNP*\n\nEste canal está destinado a reportes de extorsión por *particulares o bandas criminales*. Si la amenaza proviene de un funcionario público o policía, le recomendamos canales especializados:\n\n• *Inspectoría General PNP:* línea 111 o https://www.pnp.gob.pe\n• *Fiscalía Anticorrupción:* https://www.fiscalia.gob.pe\n\nSu reporte *NO* será registrado en el dashboard de la DIVINCRI por protección institucional. Si desea reportar otro tipo de caso, escriba *reportar*.")
                return
            else:
                await self.send_message(chat_id, "⚠️ Por favor responda con *1* (particular/banda) o *2* (funcionario/policía).")
                return

        # --- WAITING_ZONE (RF-03) ---
        if chat_state == 'waiting_zone':
            self.user_states[chat_id] = 'idle'
            zone_data = self.user_data.pop(chat_id, {})
            denuncia_id = zone_data.get('denuncia_id')
            if clean_text in ["omitir", "saltar", "no", "skip"]:
                await self.send_message(chat_id, "✅ *Zona omitida.* Su reporte ha sido registrado correctamente.")
                return
            if denuncia_id and text:
                try:
                    async with AsyncSessionLocal() as db:
                        from sqlalchemy import update
                        from app.models.database import Denuncia
                        await db.execute(update(Denuncia).where(Denuncia.id == denuncia_id).values(zona_detectada=text.strip()))
                        await db.commit()
                    await self.send_message(chat_id, f"📍 *Zona registrada:* {text.strip()}\n\n✅ Su reporte ha sido actualizado con esta información.")
                except Exception as e:
                    logger.error(f"Error guardando zona: {e}")
                    await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip()}\n\n✅ Su reporte ha sido registrado correctamente.")
            else:
                await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip() if text else 'N/A'}\n\n✅ Su reporte ha sido registrado correctamente.")
            return

        # --- IDLE ---
        if chat_state == 'idle':
            if text:
                clean_text = text.lower().strip()
                if clean_text.startswith("trj-") or (len(clean_text) == 8 and clean_text.startswith("trj")):
                    tracking_code = clean_text.upper()
                    await self.send_message(chat_id, f"🔍 _Buscando estado de la denuncia {tracking_code}..._")
                    try:
                        async with AsyncSessionLocal() as db:
                            from sqlalchemy import select
                            from app.models.database import Denuncia
                            result = await db.execute(select(Denuncia).where(Denuncia.tracking_code == tracking_code))
                            denuncia = result.scalar_one_or_none()
                            if denuncia:
                                nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "NO DETERMINADO"
                                await self.send_message(chat_id, f"🎫 *Denuncia encontrada:* `{tracking_code}`\n⚖️ *Nivel de Riesgo:* *{nivel_riesgo_str}*\n📋 *Estado:* `{denuncia.estado.value.upper()}`\n\nPuedes consultar el análisis completo de la IA y blockchain en:\n{settings.TRACKING_URL}?code={tracking_code}")
                            else:
                                await self.send_message(chat_id, f"❌ No se encontró ninguna denuncia con el código `{tracking_code}`. Verifica que esté bien escrito.")
                    except Exception as e:
                        await self.send_message(chat_id, f"❌ Ocurrió un error al buscar la denuncia: {str(e)}")
                    return

                saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
                if clean_text in saludos or any(s == clean_text for s in saludos) or clean_text in ["hola!", "hola."]:
                    await self.send_message(chat_id, "👋 *¡Hola!* Soy el asistente de Inteligencia Ciudadana IntelExtorsión.\n\nEste sistema recibe reportes de extorsión, los analiza con IA forense y entrega información procesada a las autoridades competentes para combatir el crimen organizado.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Recuerda: Este NO es un canal directo de denuncia formal a la policía. Para denuncias oficiales, usa la línea 111 o acude a la comisaría.")
                    return

                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "quiero reportar", "reportar", "aportar informacion", "aportar información", "/denunciar"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[chat_id] = 'classifying'
                    inline_keyboard = {"inline_keyboard": [[{"text": "👤 Particular / Banda criminal", "callback_data": "clasif_1"}], [{"text": "👮 Funcionario público / Policía", "callback_data": "clasif_2"}]]}
                    await self.send_message(chat_id, "🛡️ *Menú de Clasificación del Reporte*\n\n¿La amenaza proviene de:", reply_markup=inline_keyboard)
                    return

                await self.send_message(chat_id, f"🤖 *Hola. Soy {TELEGRAM_CONFIG['BOT_NAME']}.*\n\nEste sistema recibe reportes de extorsión para análisis forense con IA y entrega de inteligencia a las autoridades competentes.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría más cercana.")
                return
            else:
                await self.send_message(chat_id, "🤖 *Detecté un archivo, pero el asistente de ingesta no está activo.*\n\nPor favor, escribe *reportar* o *denunciar* primero para poder registrar tu caso correctamente.")
                return

        # --- WAITING_FOR_DENUNCIA / WAITING_CONTENT ---
        # Acumular en batch para soporte multi-archivo + texto
        has_attachment = bool(photo or document or video or voice or audio)
        if not has_attachment and text:
            has_attachment = False

        if text:
            await self._handle_incoming_message(chat_id, message, text=text)
        elif caption:
            await self._handle_incoming_message(chat_id, message, text=caption)
        elif has_attachment:
            await self._handle_incoming_message(chat_id, message, text="")
        else:
            await self.send_message(chat_id, "❌ Por favor, escribe un mensaje o envía una nota de voz/imagen explicativa para que podamos generar inteligencia útil.")

    # ---------------------------------------------------------------------------
    # Batch system (3-second debounce, like WhatsApp/Discord)
    # ---------------------------------------------------------------------------

    async def _handle_incoming_message(self, chat_id: int, message: dict, text: str):
        has_attachment = bool(message.get("photo") or message.get("document") or message.get("video") or message.get("voice") or message.get("audio"))

        if not has_attachment:
            clean_text = text.lower().strip()
            saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
            intencionesPuras = ["quiero denunciar", "quisiera hacer una denuncia", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "iniciar denuncia", "denunciar", "quiero hacer una denuncia", "quisiera denunciar", "quiero reportar", "quisiera reportar", "reportar una extorsion", "hacer un reporte", "quiero hacer un reporte", "ayuda por favor", "ayudeme", "quiero registrar una denuncia"]
            frases_relleno = ["esta bien", "está bien", "ahora te envio", "ahora te envío", "te envio lo necesario", "te envío lo necesario", "ya te envio", "ya te envío", "te lo envio", "te lo envío", "un momento", "un minuto", "un segundo", "espera", "esperame", "espérame", "listo", "ok", "okay", "entendido", "vale", "bien", "espera un momento", "ya te mando", "ahora te mando", "te mando lo necesario", "te lo mando", "voy a redactar", "te envio", "te envío", "te mando", "ahora te paso lo necesario", "ahora te paso", "ya te lo envio", "ya te lo envío", "ya te lo paso"]

            es_saludo = clean_text in saludos or any(s == clean_text for s in saludos)
            es_intencion = clean_text in intencionesPuras or any(i == clean_text for i in intencionesPuras) or (any(i in clean_text for i in intencionesPuras) and len(clean_text) < 50 and not any(c.isdigit() for c in clean_text))
            es_relleno = clean_text in frases_relleno or any(f == clean_text for f in frases_relleno) or (any(clean_text.startswith(f) for f in frases_relleno) and len(clean_text) < 50 and not any(c.isdigit() for c in clean_text))

            if es_saludo or es_intencion or es_relleno:
                await self.send_message(chat_id, "📝 *Asistente Esperando Detalles del Reporte.*\n\n⚠️ No detectamos detalles del hecho en tu mensaje.\n\nPor favor, redacta **en un único mensaje consolidado** toda la información relevante cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas, zona), o envíanos una nota de voz explicativa.\n\n*Si deseas cancelar el reporte actual, escribe **cancelar**.*")
                return

            if len(clean_text) < 15:
                await self.send_message(chat_id, "ℹ️ *Tu mensaje es muy corto.* Para poder procesar tu reporte y generar inteligencia útil para las autoridades, por favor escribe una descripción más detallada de los hechos o envía una nota de voz.")
                return

        batch = self.pending_batches.get(chat_id)
        if batch is None:
            batch = {"messages": [], "timer": None}
            self.pending_batches[chat_id] = batch

        batch["messages"].append(message)

        if batch["timer"]:
            batch["timer"].cancel()

        async def _trigger():
            await asyncio.sleep(3.0)
            await self._flush_batch(chat_id)

        batch["timer"] = asyncio.create_task(_trigger())
        logger.info(f"[Telegram] Mensaje agregado a batch de {chat_id}. Total en batch: {len(batch['messages'])}")

    async def _flush_batch(self, chat_id: int):
        batch = self.pending_batches.pop(chat_id, None)
        if not batch or not batch["messages"]:
            return
        messages = batch["messages"]
        logger.info(f"[Telegram] Procesando batch de {chat_id} con {len(messages)} mensaje(s)")
        try:
            await self._create_denuncia_from_batch(chat_id, messages)
        except Exception as e:
            logger.exception(f"Error procesando batch de {chat_id}")
            await self.send_message(chat_id, f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")

    # ---------------------------------------------------------------------------
    # Creación de denuncia desde batch
    # ---------------------------------------------------------------------------

    async def _create_denuncia_from_batch(self, chat_id: int, messages: List[dict]):
        textos = []
        archivos_descargados = []
        msg_id_principal = None

        for msg in messages:
            if msg_id_principal is None:
                msg_id_principal = msg["message_id"]

            msg_text = msg.get("text", "") or msg.get("caption", "") or ""
            msg_text = msg_text.strip()
            if msg_text:
                textos.append(msg_text)

            voice = msg.get("voice")
            audio = msg.get("audio")
            photo = msg.get("photo")
            document = msg.get("document")
            video = msg.get("video")

            if voice or audio:
                media = voice or audio
                file_id = media["file_id"]
                file_info = await self.get_file(file_id)
                if file_info and file_info.get("file_path"):
                    file_path_tg = file_info["file_path"]
                    ext = os.path.splitext(file_path_tg)[1] or ".ogg"
                    safe_name = f"{msg_id_principal}_{file_id[:10]}_audio{ext}"
                    dest_path = os.path.join(UPLOAD_DIR, safe_name)
                    downloaded = await self.download_file(file_id, dest_path)
                    if downloaded:
                        url_archivo = f"https://api.telegram.org/file/bot{self.token}/{file_path_tg}"
                        await self.send_message(chat_id, "🎙️ _Audio recibido. Transcribiendo con IA..._")
                        stt_res = await transcribe_audio(url_archivo)
                        if stt_res.get("transcripcion"):
                            textos.append(f"[Transcripción de audio]: {stt_res['transcripcion']}")
                        archivos_descargados.append({"path": dest_path, "tipo": "audio", "mime": media.get("mime_type", "audio/ogg"), "filename": os.path.basename(file_path_tg)})

            if photo:
                file_id = photo[-1]["file_id"]
                file_info = await self.get_file(file_id)
                if file_info and file_info.get("file_path"):
                    file_path_tg = file_info["file_path"]
                    ext = os.path.splitext(file_path_tg)[1] or ".jpg"
                    safe_name = f"{msg_id_principal}_{file_id[:10]}_imagen{ext}"
                    dest_path = os.path.join(UPLOAD_DIR, safe_name)
                    downloaded = await self.download_file(file_id, dest_path)
                    if downloaded:
                        archivos_descargados.append({"path": dest_path, "tipo": "imagen", "mime": f"image/{ext.lstrip('.').replace('jpeg','jpg')}", "filename": safe_name})

            if document:
                file_id = document["file_id"]
                file_name = document.get("file_name", "documento")
                mime_type = document.get("mime_type", "application/octet-stream")
                file_info = await self.get_file(file_id)
                if file_info and file_info.get("file_path"):
                    file_path_tg = file_info["file_path"]
                    ext = os.path.splitext(file_name)[1] or os.path.splitext(file_path_tg)[1] or ".bin"
                    safe_name = f"{msg_id_principal}_{file_id[:10]}_documento{ext}"
                    dest_path = os.path.join(UPLOAD_DIR, safe_name)
                    downloaded = await self.download_file(file_id, dest_path)
                    if downloaded:
                        archivos_descargados.append({"path": dest_path, "tipo": "documento", "mime": mime_type, "filename": file_name})

            if video:
                file_id = video["file_id"]
                file_name = video.get("file_name", "video.mp4")
                mime_type = video.get("mime_type", "video/mp4")
                file_info = await self.get_file(file_id)
                if file_info and file_info.get("file_path"):
                    file_path_tg = file_info["file_path"]
                    ext = os.path.splitext(file_name)[1] or ".mp4"
                    safe_name = f"{msg_id_principal}_{file_id[:10]}_video{ext}"
                    dest_path = os.path.join(UPLOAD_DIR, safe_name)
                    downloaded = await self.download_file(file_id, dest_path)
                    if downloaded:
                        archivos_descargados.append({"path": dest_path, "tipo": "video", "mime": mime_type, "filename": file_name})

        tiene_texto = bool(textos)
        tiene_adjuntos = bool(archivos_descargados)

        if tiene_texto and tiene_adjuntos:
            tipo_contenido = TipoContenido.MIXTO
        elif tiene_adjuntos:
            tipos = set(a["tipo"] for a in archivos_descargados)
            if len(tipos) == 1:
                t = list(tipos)[0]
                tipo_contenido = TipoContenido.IMAGEN if t == "imagen" else TipoContenido.AUDIO if t == "audio" else TipoContenido.VIDEO if t == "video" else TipoContenido.DOCUMENTO
            else:
                tipo_contenido = TipoContenido.MIXTO
        else:
            tipo_contenido = TipoContenido.TEXTO

        contenido_raw = "\n\n".join(textos) if textos else "[Sin texto descriptivo]"
        url_archivo = archivos_descargados[0]["path"] if archivos_descargados else None

        import hashlib
        metadata = {
            "canal_origen": "telegram",
            "session_id": hashlib.sha256(str(chat_id).encode()).hexdigest()[:16],
            "batch_size": len(messages),
            "total_archivos": len(archivos_descargados),
        }
        if len(archivos_descargados) > 1:
            metadata["archivos_adicionales"] = archivos_descargados[1:]

        if not contenido_raw.strip() or contenido_raw == "[Sin texto descriptivo]":
            if not archivos_descargados:
                await self.send_message(chat_id, "❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia para que podamos generar inteligencia útil.")
                return

        clean_text = contenido_raw.lower().strip()
        if not archivos_descargados and len(clean_text) < 15:
            await self.send_message(chat_id, "ℹ️ *Descripción muy corta.* Para poder procesar tu reporte y generar inteligencia útil para las autoridades, por favor proporciona más detalles (mínimo 15 caracteres) o envía un audio.")
            return

        n_archivos = len(archivos_descargados)
        archivos_msg = f" ({n_archivos} archivos adjuntos)" if n_archivos > 1 else ""
        await self.send_message(chat_id, f"🔍 _Procesando tu reporte{archivos_msg}... Guardando evidencias y analizando con agentes de IA forense..._")

        try:
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.TELEGRAM,
                    id_externo=str(msg_id_principal),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata=metadata,
                )
                denuncia = await service.crear_denuncia(req)
                await service.ejecutar_grafo(denuncia, modo="completo")
                await db.refresh(denuncia)

            self.user_states[chat_id] = 'idle'
            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "NO DETERMINADO"

            reply_msg = (
                f"✅ *Reporte Registrado Exitosamente*{archivos_msg}\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Estimado:* *{nivel_riesgo_str}*\n\n"
                f"Su información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa.\n\n"
                f"Puede consultar el estado de análisis de su reporte en:\n"
                f"{settings.TRACKING_URL}?code={tracking_code}\n\n"
                f"⚠️ Recuerde: Este sistema es de inteligencia ciudadana. Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría."
            )
            await self.send_message(chat_id, reply_msg)

            zona = getattr(denuncia, 'zona_detectada', None)
            if not zona:
                self.user_states[chat_id] = 'waiting_zone'
                self.user_data[chat_id] = {'denuncia_id': str(denuncia.id)}
                await self.send_message(chat_id, "📍 *Una pregunta más (opcional):*\n\n¿En qué zona o cerro ocurrió esto?\n\n_Escribe la zona o responde *omitir* para saltar._")
        except Exception as e:
            logger.error(f"Error procesando denuncia de Telegram: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Ocurrió un error al procesar tu denuncia: {str(e)}")

    # ---------------------------------------------------------------------------
    # Descarga de archivos desde Telegram
    # ---------------------------------------------------------------------------

    async def download_file(self, file_id: str, dest_path: str) -> bool:
        file_info = await self.get_file(file_id)
        if not file_info or not file_info.get("file_path"):
            return False
        file_url = f"https://api.telegram.org/file/bot{self.token}/{file_info['file_path']}"
        try:
            resp = await self.http_client.get(file_url)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"[Telegram] Archivo descargado: {dest_path} ({len(resp.content)} bytes)")
                return True
        except Exception as e:
            logger.error(f"[Telegram] Error descargando archivo {file_id}: {e}")
        return False

    async def get_file(self, file_id: str) -> Optional[dict]:
        url = f"{self.api_url}/getFile"
        try:
            resp = await self.http_client.get(url, params={"file_id": file_id})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return data.get("result")
        except Exception as e:
            logger.error(f"Error al obtener información del archivo en Telegram: {e}")
        return None

    # ---------------------------------------------------------------------------
    # Callback queries (inline buttons)
    # ---------------------------------------------------------------------------

    async def handle_callback_query(self, callback_query: dict):
        chat_id = callback_query["message"]["chat"]["id"]
        data = callback_query.get("data", "")
        query_id = callback_query["id"]

        await self.answer_callback_query(query_id)

        if data == "clasif_1":
            self.user_states[chat_id] = 'waiting_for_denuncia'
            self.user_data[chat_id] = {'clasificacion': 'particular'}
            await self.send_message(chat_id, "✅ *Clasificación registrada:* Particular / Banda criminal\n\n📝 *Ahora envía tu reporte:*\n• Escribe el texto con los detalles\n• Envía una imagen de la carta/extorsión\n• Envía una nota de voz o audio\n\n_Puedes enviar múltiples archivos. Cuando termines, escribe *enviar*._")
        elif data == "clasif_2":
            self.user_states[chat_id] = 'idle'
            await self.send_message(chat_id, "⚠️ *Canal especializado*\n\nLas denuncias contra funcionarios públicos o policías son atendidas por canales especializados:\n\n🏛️ *Inspectoría General PNP*\n📞 Línea: 1818 (Central de denuncias Mininter)\n📧 Email: lineas1818@mininter.gob.pe\n\n⚖️ *Fiscalía Anticorrupción*\n📞 Línea: 0800-00-205 (Línea de Integridad)\n📧 Email: denunciascorrupcion@mpfn.gob.pe\n\n_Tu reporte NO será registrado en el dashboard de la DIVINCRI para proteger la integridad de la investigación._")

    async def answer_callback_query(self, query_id: int):
        url = f"{self.api_url}/answerCallbackQuery"
        try:
            await self.http_client.post(url, json={"callback_query_id": query_id})
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        url = f"{self.api_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            await self.http_client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error al enviar mensaje a Telegram: {e}")
