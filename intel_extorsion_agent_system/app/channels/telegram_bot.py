import asyncio
import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

# Configuración personalizada del bot de Telegram
TELEGRAM_CONFIG = {
    "BOT_NAME": "IntelExtorsión Telegram",
    "BOT_USERNAME": "intelextorsion_bot",
    "WELCOME_MESSAGE": "¡Bienvenido al sistema de Inteligencia Ciudadana!",
    "SUPPORT_CHANNEL": "@intelextorsion_support",
}


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self._task = None
        self.user_states = {}  # chat_id -> state
        self.user_data = {}    # chat_id -> dict with extra data
        self.start_time = datetime.now()

    def start_background(self):
        """Inicia el bot en una tarea en segundo plano de asyncio"""
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

    async def process_update(self, update: dict):
        # Handle callback queries (inline keyboard buttons)
        callback_query = update.get("callback_query")
        if callback_query:
            await self.handle_callback_query(callback_query)
            return

        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        voice = message.get("voice")
        audio = message.get("audio")

        # Recuperar estado de sesión del usuario (default 'idle')
        chat_state = self.user_states.get(chat_id, 'idle')

        # Comando /start o /help (siempre disponible)
        if text and (text.startswith("/start") or text.startswith("/help")):
            welcome_msg = (
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
            )
            await self.send_message(chat_id, welcome_msg)
            return

        # Comando de cancelación (siempre disponible si está en proceso)
        if text:
            clean_text = text.lower().strip()
            if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
                self.user_states[chat_id] = 'idle'
                await self.send_message(
                    chat_id,
                    "❌ *Reporte cancelado.*\n\n"
                    "El asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué deseas hacer hoy? Puedes volver a iniciar escribiendo 'reportar' o 'denunciar'."
                )
                return

        # --- FLUJO ESTADO: CLASSIFYING (RF-01) ---
        if chat_state == 'classifying':
            clean_text = text.lower().strip() if text else ""
            if clean_text in ["1", "uno", "particular", "banda", "criminal", "delincuente"]:
                self.user_states[chat_id] = 'waiting_for_denuncia'
                await self.send_message(
                    chat_id,
                    "📝 *Asistente de Ingesta Activado.*\n\n"
                    "Por favor, describa detalladamente lo sucedido **en su siguiente mensaje**. Recuerde incluir:\n"
                    "• Teléfonos desde donde le contactaron\n"
                    "• Nombres o cuentas bancarias de cobro si se las dieron\n"
                    "• Tipo de amenaza o exigencias de dinero\n"
                    "• Zona o lugar donde ocurrieron los hechos\n\n"
                    "También puede adjuntar imágenes o documentos de evidencia.\n\n"
                    "⚠️ Su información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa. Si desea abortar, escriba *cancelar*."
                )
                return
            elif clean_text in ["2", "dos", "funcionario", "policía", "policia", "autoridad", "pnp"]:
                self.user_states[chat_id] = 'idle'
                await self.send_message(
                    chat_id,
                    "🛡️ *Reporte contra servidor público / PNP*\n\n"
                    "Este canal está destinado a reportes de extorsión por *particulares o bandas criminales*. "
                    "Si la amenaza proviene de un funcionario público o policía, le recomendamos canales especializados:\n\n"
                    "• *Inspectoría General PNP:* línea 111 o https://www.pnp.gob.pe\n"
                    "• *Fiscalía Anticorrupción:* https://www.fiscalia.gob.pe\n\n"
                    "Su reporte *NO* será registrado en el dashboard de la DIVINCRI por protección institucional. "
                    "Si desea reportar otro tipo de caso, escriba *reportar*."
                )
                return
            else:
                await self.send_message(chat_id, "⚠️ Por favor responda con *1* (particular/banda) o *2* (funcionario/policía).")
                return

        # --- FLUJO ESTADO: WAITING_ZONE (RF-03: zona opcional post-denuncia) ---
        if chat_state == 'waiting_zone':
            self.user_states[chat_id] = 'idle'
            zone_data = self.user_data.pop(chat_id, {})
            denuncia_id = zone_data.get('denuncia_id')

            if clean_text in ["omitir", "saltar", "no", "skip"]:
                await self.send_message(chat_id, "✅ *Zona omitida.* Su reporte ha sido registrado correctamente.")
                return

            # Guardar zona en la denuncia
            if denuncia_id:
                try:
                    async with AsyncSessionLocal() as db:
                        from sqlalchemy import update
                        from app.models.database import Denuncia
                        await db.execute(
                            update(Denuncia)
                            .where(Denuncia.id == denuncia_id)
                            .values(zona_detectada=text.strip())
                        )
                        await db.commit()
                    await self.send_message(chat_id, f"📍 *Zona registrada:* {text.strip()}\n\n✅ Su reporte ha sido actualizado con esta información.")
                except Exception as e:
                    logger.error(f"Error guardando zona: {e}")
                    await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip()}\n\n✅ Su reporte ha sido registrado correctamente.")
            else:
                await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip()}\n\n✅ Su reporte ha sido registrado correctamente.")
            return

        # --- FLUJO ESTADO: IDLE ---
        if chat_state == 'idle':
            if text:
                clean_text = text.lower().strip()
                
                # 1. Búsqueda de denuncia por código TRJ
                if clean_text.startswith("trj-") or (len(clean_text) == 8 and clean_text.startswith("trj")):
                    tracking_code = clean_text.upper()
                    await self.send_message(chat_id, f"🔍 _Buscando estado de la denuncia {tracking_code}..._")
                    try:
                        async with AsyncSessionLocal() as db:
                            from sqlalchemy import select
                            from app.models.database import Denuncia
                            result = await db.execute(
                                select(Denuncia).where(Denuncia.tracking_code == tracking_code)
                            )
                            denuncia = result.scalar_one_or_none()
                            if denuncia:
                                nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "NO DETERMINADO"
                                msg = (
                                    f"🎫 *Denuncia encontrada:* `{tracking_code}`\n"
                                    f"⚖️ *Nivel de Riesgo:* *{nivel_riesgo_str}*\n"
                                    f"📋 *Estado:* `{denuncia.estado.value.upper()}`\n\n"
                                    f"Puedes consultar el análisis completo de la IA y blockchain en:\n"
                                    f"{settings.TRACKING_URL}?code={tracking_code}"
                                )
                                await self.send_message(chat_id, msg)
                            else:
                                await self.send_message(chat_id, f"❌ No se encontró ninguna denuncia con el código `{tracking_code}`. Verifica que esté bien escrito.")
                    except Exception as e:
                        await self.send_message(chat_id, f"❌ Ocurrió un error al buscar la denuncia: {str(e)}")
                    return

                # 2. Saludos
                saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
                if clean_text in saludos or any(s == clean_text for s in saludos) or clean_text in ["hola!", "hola."]:
                    await self.send_message(
                        chat_id,
                        "👋 *¡Hola!* Soy el asistente de Inteligencia Ciudadana IntelExtorsión.\n\nEste sistema recibe reportes de extorsión, los analiza con IA forense y entrega información procesada a las autoridades competentes para combatir el crimen organizado.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Recuerda: Este NO es un canal directo de denuncia formal a la policía. Para denuncias oficiales, usa la línea 111 o acude a la comisaría."
                    )
                    return

                # 3. Activar asistente de denuncia -> menú de clasificación RF-01
                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "quiero reportar", "reportar", "aportar informacion", "aportar información", "/denunciar"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[chat_id] = 'classifying'
                    inline_keyboard = {
                        "inline_keyboard": [
                            [{"text": "👤 Particular / Banda criminal", "callback_data": "clasif_1"}],
                            [{"text": "👮 Funcionario público / Policía", "callback_data": "clasif_2"}]
                        ]
                    }
                    await self.send_message(
                        chat_id,
                        "🛡️ *Menú de Clasificación del Reporte*\n\n"
                        "¿La amenaza proviene de:",
                        reply_markup=inline_keyboard
                    )
                    return

                # Fallback en IDLE
                await self.send_message(
                    chat_id,
                    f"🤖 *Hola. Soy {TELEGRAM_CONFIG['BOT_NAME']}.*\n\nEste sistema recibe reportes de extorsión para análisis forense con IA y entrega de inteligencia a las autoridades competentes.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría más cercana."
                )
                return
            else:
                # Si envían audios/archivos en IDLE, pedir que activen el asistente
                await self.send_message(
                    chat_id,
                    "🤖 *Detecté un archivo, pero el asistente de ingesta no está activo.*\n\n"
                    "Por favor, escribe *reportar* o *denunciar* primero para poder registrar tu caso correctamente."
                )
                return

        # --- FLUJO ESTADO: WAITING_FOR_DENUNCIAS ---
        # Procesar contenido: texto o audio
        tipo_contenido = TipoContenido.TEXTO
        contenido_raw = text
        url_archivo = None
        voice_or_audio = voice or audio

        if text:
            clean_text = text.lower().strip()
            
            # Filtros conversacionales y de relleno en estado activo
            saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
            intencionesPuras = [
                "quiero denunciar", "quisiera hacer una denuncia", "hacer una denuncia", "hacer otra denuncia", 
                "otra denuncia", "nueva denuncia", "registrar otra", "iniciar denuncia", "denunciar", 
                "quiero hacer una denuncia", "quisiera denunciar", "quiero reportar", "quisiera reportar", 
                "reportar una extorsion", "hacer un reporte", "quiero hacer un reporte", "ayuda por favor", 
                "ayudeme", "quiero registrar una denuncia"
            ]
            frases_relleno = [
                "esta bien", "está bien", "ahora te envio", "ahora te envío", "te envio lo necesario", 
                "te envío lo necesario", "ya te envio", "ya te envío", "te lo envio", "te lo envío", 
                "un momento", "un minuto", "un segundo", "espera", "esperame", "espérame", "listo", 
                "ok", "okay", "entendido", "vale", "bien", "espera un momento", "ya te mando", 
                "ahora te mando", "te mando lo necesario", "te lo mando", "voy a redactar", 
                "te envio", "te envío", "te mando", "ahora te paso lo necesario", "ahora te paso",
                "ya te lo envio", "ya te lo envío", "ya te lo paso"
            ]

            es_saludo = clean_text in saludos or any(s == clean_text for s in saludos)
            es_intencion = clean_text in intencionesPuras or any(i == clean_text for i in intencionesPuras) or \
                           (any(i in clean_text for i in intencionesPuras) and len(clean_text) < 50 and not any(c.isdigit() for c in clean_text))
            es_relleno = clean_text in frases_relleno or any(f == clean_text for f in frases_relleno) or \
                         (any(clean_text.startswith(f) for f in frases_relleno) and len(clean_text) < 50 and not any(c.isdigit() for c in clean_text))

            if (es_saludo or es_intencion or es_relleno) and not voice_or_audio:
                await self.send_message(
                    chat_id,
                    "📝 *Asistente Esperando Detalles del Reporte.*\n\n"
                    "⚠️ No detectamos detalles del hecho en tu mensaje.\n\n"
                    "Por favor, redacta **en un único mensaje consolidado** toda la información relevante cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas, zona), o envíanos una nota de voz explicativa.\n\n"
                    "*Si deseas cancelar el reporte actual, escribe **cancelar**.*"
                )
                return

            # Evitar registrar textos demasiado cortos que no aporten detalles
            if len(clean_text) < 15 and not voice_or_audio:
                await self.send_message(
                    chat_id,
                    "ℹ️ *Tu mensaje es muy corto.* Para poder procesar tu reporte y generar inteligencia útil para las autoridades, por favor escribe una descripción más detallada de los hechos o envía una nota de voz."
                )
                return

        if voice_or_audio:
            file_id = voice_or_audio["file_id"]
            # Obtener información del archivo desde los servidores de Telegram
            file_info = await self.get_file(file_id)
            if file_info:
                file_path = file_info.get("file_path")
                # URL de descarga del archivo de audio para transcribir
                url_archivo = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                tipo_contenido = TipoContenido.AUDIO
                
                await self.send_message(chat_id, "🎙️ _Nota de voz recibida. Transcribiendo y procesando con agentes de IA..._")
                
                # Transcribir audio mediante Whisper
                stt_res = await transcribe_audio(url_archivo)
                if stt_res.get("transcripcion"):
                    contenido_raw = stt_res["transcripcion"]
                else:
                    await self.send_message(chat_id, f"❌ Error al procesar el audio: {stt_res.get('error', 'desconocido')}")
                    return
            else:
                await self.send_message(chat_id, "❌ No se pudo recuperar el archivo de audio de los servidores de Telegram.")
                return

        if not contenido_raw or not contenido_raw.strip():
            await self.send_message(chat_id, "❌ Por favor, escribe un mensaje o envía una nota de voz explicativa para que podamos generar inteligencia útil.")
            return

        await self.send_message(chat_id, "🔍 _Procesando tu reporte... Guardando evidencias y analizando con agentes de IA forense..._")

        try:
            # Crear denuncia y ejecutar grafo
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                import hashlib
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.TELEGRAM,
                    id_externo=str(message["message_id"]),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata={
                        "canal_origen": "telegram",
                        "session_id": hashlib.sha256(str(chat_id).encode()).hexdigest()[:16]
                    }
                )
                denuncia = await service.crear_denuncia(req)
                
                # Ejecución del grafo de agentes de forma síncrona
                await service.ejecutar_grafo(denuncia, modo="completo")
                
                # REFRESCAR DENUNCIA para recuperar tracking_code y nivel_riesgo actualizados de la DB
                await db.refresh(denuncia)

            # Recuperar datos finales y restablecer estado a IDLE
            self.user_states[chat_id] = 'idle'
            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "NO DETERMINADO"
            
            msg_reply = (
                f"✅ *Reporte Registrado Exitosamente*\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Estimado:* *{nivel_riesgo_str}*\n\n"
                f"Su información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa.\n\n"
                f"Puede consultar el estado de análisis de su reporte en:\n"
                f"{settings.TRACKING_URL}?code={tracking_code}\n\n"
                f"⚠️ Recuerde: Este sistema es de inteligencia ciudadana. Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría."
            )
            await self.send_message(chat_id, msg_reply)

            # RF-03: Pregunta opcional de zona si no se detectó
            zona = getattr(denuncia, 'zona_detectada', None)
            if not zona:
                self.user_states[chat_id] = 'waiting_zone'
                self.user_data[chat_id] = {'denuncia_id': str(denuncia.id)}
                await self.send_message(
                    chat_id,
                    "📍 *Una pregunta más (opcional):*\n\n"
                    "¿En qué zona o cerro ocurrió esto?\n\n"
                    "_Escribe la zona o responde *omitir* para saltar._"
                )
        except Exception as e:
            logger.error(f"Error procesando denuncia de Telegram: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Ocurrió un error al procesar tu denuncia: {str(e)}")

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

    async def handle_callback_query(self, callback_query: dict):
        """Maneja botones inline (clasificación RF-01)"""
        chat_id = callback_query["message"]["chat"]["id"]
        data = callback_query.get("data", "")
        query_id = callback_query["id"]

        print(f"[Telegram] Callback query received: data={data}, chat_id={chat_id}", flush=True)
        logger.info(f"Callback query: data={data}, chat_id={chat_id}")

        # Answer callback query to remove loading indicator
        await self.answer_callback_query(query_id)

        if data == "clasif_1":
            # Particular / Banda criminal
            self.user_states[chat_id] = 'waiting_content'
            self.user_data[chat_id] = {'clasificacion': 'particular'}
            await self.send_message(
                chat_id,
                "✅ *Clasificación registrada:* Particular / Banda criminal\n\n"
                "📝 *Ahora envía tu reporte:*\n"
                "• Escribe el texto con los detalles\n"
                "• Envía una imagen de la carta/extorsión\n"
                "• Envía una nota de voz o audio\n\n"
                "_Puedes enviar múltiples archivos. Cuando termines, escribe *enviar*._"
            )
        elif data == "clasif_2":
            # Funcionario público / Policía -> redirigir
            self.user_states[chat_id] = 'idle'
            await self.send_message(
                chat_id,
                "⚠️ *Canal especializado*\n\n"
                "Las denuncias contra funcionarios públicos o policías son atendidas por canales especializados:\n\n"
                "🏛️ *Inspectoría General PNP*\n"
                "📞 Línea: 1818 (Central de denuncias Mininter)\n"
                "📧 Email: lineas1818@mininter.gob.pe\n\n"
                "⚖️ *Fiscalía Anticorrupción*\n"
                "📞 Línea: 0800-00-205 (Línea de Integridad)\n"
                "📧 Email: denunciascorrupcion@mpfn.gob.pe\n\n"
                "_Tu reporte NO será registrado en el dashboard de la DIVINCRI para proteger la integridad de la investigación._"
            )

    async def answer_callback_query(self, query_id: int):
        url = f"{self.api_url}/answerCallbackQuery"
        try:
            await self.http_client.post(url, json={"callback_query_id": query_id})
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            await self.http_client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error al enviar mensaje a Telegram: {e}")
