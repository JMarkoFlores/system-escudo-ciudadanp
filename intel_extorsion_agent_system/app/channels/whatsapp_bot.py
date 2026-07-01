import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

# Configuración personalizada del bot de WhatsApp
WHATSAPP_CONFIG = {
    "BOT_NAME": "IntelExtorsión WhatsApp",
    "BUSINESS_NAME": "IntelExtorsión",
    "WELCOME_MESSAGE": "¡Bienvenido al sistema de Inteligencia Ciudadana!",
    "SUPPORT_NUMBER": "+51 111",
    "INSPECTORIA_URL": "https://www.pnp.gob.pe/inspectoría-general",  # URL informativa
    "FISCALIA_URL": "https://www.fiscalia.gob.pe",  # URL informativa
}


class WhatsAppBot:
    """
    Cliente de WhatsApp utilizando la pasarela de Whapi.cloud
    para procesar denuncias de extorsión, transcribir audios y ejecutar agentes de IA.

    Soporte para múltiples imágenes/videos/audios agrupados en una sola denuncia
    mediante batching temporal (3 segundos de ventana).
    """

    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://gate.whapi.cloud"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.user_states: Dict[str, str] = {}  # chat_id -> 'idle' | 'waiting_for_denuncia'
        self.pending_batches: Dict[str, Dict[str, Any]] = {}  # chat_id -> {messages: [], timer: asyncio.Task | None}
        self.start_time = datetime.now()

    async def close(self):
        await self.http_client.aclose()
        logger.info("Cliente HTTP de WhatsAppBot cerrado.")

    # -----------------------------------------
    # Envío de mensajes
    # -----------------------------------------

    async def send_message(self, chat_id: str, text: str, buttons=None):
        """Envía un mensaje de texto de WhatsApp a un chat específico"""
        url = f"{self.api_url}/messages/text"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"to": chat_id, "body": text}
        if buttons:
            payload["buttons"] = buttons
        try:
            resp = await self.http_client.post(url, json=payload, headers=headers)
            if resp.status_code not in [200, 201]:
                logger.error(f"Error al enviar mensaje de WhatsApp ({resp.status_code}): {resp.text}")
            else:
                logger.debug(f"Mensaje enviado con éxito a {chat_id}")
        except Exception as e:
            logger.error(f"Error HTTP al enviar mensaje a WhatsApp: {e}")

    async def _send_classification_menu(self, chat_id: str):
        """Envía el menú de clasificación RF-01 y pasa a estado 'classifying'."""
        self.user_states[chat_id] = 'classifying'
        menu = "🛡️ *Menú de Clasificación del Reporte*\n\n¿La amenaza proviene de:"
        buttons = [
            {"type": "reply", "reply": {"id": "clasif_1", "title": "👤 Particular / Banda criminal"}},
            {"type": "reply", "reply": {"id": "clasif_2", "title": "👮 Funcionario público / Policía"}}
        ]
        await self.send_message(chat_id, menu, buttons=buttons)

    # -----------------------------------------
    # Descarga de archivos
    # -----------------------------------------

    async def download_media(self, media_id: str, dest_path: str) -> bool:
        """Descarga un archivo multimedia desde Whapi.cloud y lo guarda localmente."""
        url = f"{self.api_url}/media/{media_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = await self.http_client.get(url, headers=headers, follow_redirects=True)
            if resp.status_code == 200:
                import os
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                return True
            else:
                logger.warning(f"Whapi download_media status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Error al descargar media de Whapi: {e}")
        return False

    # -----------------------------------------
    # Webhook principal
    # -----------------------------------------

    async def process_webhook(self, data: dict):
        """Procesa el JSON entrante del webhook de Whapi.cloud."""
        messages = data.get("messages", [])
        if not messages:
            return

        for msg in messages:
            if msg.get("from_me") or msg.get("fromMe"):
                continue

            chat_id = msg.get("chat_id") or msg.get("chatId")
            if not chat_id or "@g.us" in chat_id:
                continue

            msg_type = msg.get("type", "text")

            # Handle button replies (RF-01 classification)
            if msg_type == "button" or msg.get("button"):
                button = msg.get("button") or msg.get("selectedButtonId") or msg.get("data", "")
                button_id = button.get("id") if isinstance(button, dict) else button
                if button_id:
                    await self._handle_button_reply(chat_id, button_id)
                continue

            # Ignorar mensajes de tipo album (solo indicador de grupo de imágenes)
            if msg_type == "album":
                logger.info(f"[WhatsApp] Ignorando mensaje tipo 'album' de {chat_id}")
                continue

            # Ignorar tipos que no procesamos (sticker, action, unknown, etc.)
            if msg_type not in ["text", "image", "audio", "voice", "document", "video"]:
                continue

            try:
                await self._handle_incoming_message(msg)
            except Exception as ex:
                logger.exception("Error en _handle_incoming_message")

    # -----------------------------------------
    # Batching temporal
    # -----------------------------------------

    async def _handle_button_reply(self, chat_id: str, button_id: str):
        """Maneja respuestas de botones inline (clasificación RF-01)"""
        if button_id == "clasif_1":
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
        elif button_id == "clasif_2":
            self.user_states[chat_id] = 'idle'
            await self.send_message(
                chat_id,
                "⚠️ *Canal especializado*\n\n"
                "Las denuncias contra funcionarios públicos o policías son atendidas por canales especializados:\n\n"
                "🏛️ *Inspectoría General PNP*\n"
                "📞 Línea: 0800-22221\n"
                "📧 Email: igp@pnp.gob.pe\n\n"
                "⚖️ *Fiscalía Anticorrupción*\n"
                "📞 Línea: 0800-22222\n"
                "📧 Email: fiscalia@mpfn.gob.pe\n\n"
                "_Tu reporte NO será registrado en el dashboard de la DIVINCRI para proteger la integridad de la investigación._"
            )

    async def _handle_incoming_message(self, msg: dict):
        """
        Decide si procesar inmediatamente o agregar a un batch temporal.
        Mensajes con adjuntos se agrupan por chat durante 3 segundos.
        """
        chat_id = msg.get("chat_id") or msg.get("chatId")
        msg_type = msg.get("type", "text")
        has_attachment = msg_type in ["image", "audio", "voice", "document", "video"]

        # Si es texto puro sin adjunto → procesar inmediatamente
        if not has_attachment and msg_type == "text":
            await self._process_single_message(msg)
            return

        # Si tiene adjunto → agregar al batch
        batch = self.pending_batches.get(chat_id)
        if batch is None:
            batch = {"messages": [], "timer": None}
            self.pending_batches[chat_id] = batch

        batch["messages"].append(msg)

        # Cancelar timer anterior si existe
        if batch["timer"]:
            batch["timer"].cancel()

        # Programar procesamiento del batch en 3 segundos
        async def _trigger():
            await asyncio.sleep(3.0)
            await self._flush_batch(chat_id)

        batch["timer"] = asyncio.create_task(_trigger())
        logger.info(f"[WhatsApp] Mensaje {msg_type} agregado a batch de {chat_id}. Total en batch: {len(batch['messages'])}")

    async def _flush_batch(self, chat_id: str):
        """Procesa el batch acumulado para un chat y lo limpia."""
        batch = self.pending_batches.pop(chat_id, None)
        if not batch or not batch["messages"]:
            return

        messages = batch["messages"]
        logger.info(f"[WhatsApp] Procesando batch de {chat_id} con {len(messages)} mensaje(s)")

        try:
            await self._process_message_batch(chat_id, messages)
        except Exception as e:
            logger.exception(f"Error procesando batch de {chat_id}")
            await self.send_message(chat_id, f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")

    # -----------------------------------------
    # Procesamiento de mensaje único (texto)
    # -----------------------------------------

    async def _process_single_message(self, msg: dict):
        """Procesa un mensaje de texto individual (sin adjuntos)."""
        chat_id = msg.get("chat_id") or msg.get("chatId")
        text = msg.get("text", {}).get("body", "").strip()
        clean_text = text.lower().strip()
        chat_state = self.user_states.get(chat_id, 'idle')

        # Comandos globales
        if clean_text in ["!start", "!help", "help", "ayuda", "info", "/start", "/help"]:
            welcome = (
                f"🛡️ *{WHATSAPP_CONFIG['WELCOME_MESSAGE']}*\n\n"
                f"🤖 *{WHATSAPP_CONFIG['BOT_NAME']}*\n\n"
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
            await self.send_message(chat_id, welcome)
            return

        if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
            self.user_states[chat_id] = 'idle'
            await self.send_message(chat_id, "❌ *Reporte cancelado.*\n\nEl asistente de ingesta ha sido desactivado. Escribe *reportar* o *denunciar* para comenzar.")
            return

        # --- CLASSIFYING (RF-01) ---
        if chat_state == 'classifying':
            if clean_text in ["1", "uno", "particular", "banda", "criminal", "delincuente"]:
                self.user_states[chat_id] = 'waiting_for_denuncia'
                await self.send_message(
                    chat_id,
                    "✅ *Clasificación:* Particular / Banda criminal\n\n"
                    "📝 *Asistente de Ingesta Activado.*\n\n"
                    "Por favor, descríbeme detalladamente los hechos *en tu siguiente mensaje*. Recuerda incluir:\n"
                    "• Teléfonos desde donde te contactaron\n"
                    "• Nombres o cuentas bancarias de cobro si te las dieron\n"
                    "• Tipo de amenaza o exigencias de dinero\n\n"
                    "También puedes adjuntar imágenes o documentos de evidencia.\n\n"
                    "⚠️ Tu información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa. Si deseas abortar, escribe *cancelar*."
                )
                return
            elif clean_text in ["2", "dos", "funcionario", "policía", "policia", "autoridad", "pnp"]:
                self.user_states[chat_id] = 'idle'
                await self.send_message(
                    chat_id,
                    "🛡️ *Reporte contra servidor público / PNP*\n\n"
                    "Este canal está destinado a reportes de extorsión por *particulares o bandas criminales*. "
                    "Si la amenaza proviene de un funcionario público o policía, te recomendamos canales especializados:\n\n"
                    "• *Inspectoría General PNP:* línea 111 o https://www.pnp.gob.pe\n"
                    "• *Fiscalía Anticorrupción:* https://www.fiscalia.gob.pe\n\n"
                    "Tu reporte *NO* será registrado en el dashboard de la DIVINCRI por protección institucional. "
                    "Si deseas reportar otro tipo de caso, escribe *reportar*."
                )
                return
            else:
                await self.send_message(chat_id, "⚠️ Por favor responde con *1* (particular/banda) o *2* (funcionario/policía).")
                return

        # --- WAITING_ZONE (RF-03: zona opcional post-denuncia) ---
        if chat_state == 'waiting_zone':
            self.user_states[chat_id] = 'idle'
            zone_data = self.user_data.pop(chat_id, {})
            denuncia_id = zone_data.get('denuncia_id')

            if clean_text in ["omitir", "saltar", "no", "skip"]:
                await self.send_message(chat_id, "✅ *Zona omitida.* Tu reporte ha sido registrado correctamente.")
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
                    await self.send_message(chat_id, f"📍 *Zona registrada:* {text.strip()}\n\n✅ Tu reporte ha sido actualizado con esta información.")
                except Exception as e:
                    logger.error(f"Error guardando zona: {e}")
                    await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip()}\n\n✅ Tu reporte ha sido registrado correctamente.")
            else:
                await self.send_message(chat_id, f"📍 *Zona recibida:* {text.strip()}\n\n✅ Tu reporte ha sido registrado correctamente.")
            return

        # --- IDLE ---
        if chat_state == 'idle':
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
                            nivel = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"
                            await self.send_message(chat_id, f"🎫 *Denuncia Encontrada:* `{tracking_code}`\n⚖️ *Nivel de Riesgo:* *{nivel}*\n📋 *Estado:* `{denuncia.estado.value.upper()}`")
                        else:
                            await self.send_message(chat_id, f"❌ No se encontró denuncia `{tracking_code}`.")
                except Exception as e:
                    logger.error(f"Error tracking: {e}")
                    await self.send_message(chat_id, f"❌ Error al buscar: {str(e)}")
                return

            saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
            if clean_text in saludos or clean_text in ["hola!", "hola."]:
                await self.send_message(chat_id, "👋 *¡Hola!* Soy el asistente de Inteligencia Ciudadana IntelExtorsión.\n\nEste sistema recibe reportes de extorsión, los analiza con IA forense y entrega información procesada a las autoridades competentes para combatir el crimen organizado.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Recuerda: Este NO es un canal directo de denuncia formal a la policía. Para denuncias oficiales, usa la línea 111 o acude a la comisaría.")
                return

            intenciones = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia",
                           "nueva denuncia", "registrar otra", "denunciar", "quiero reportar", "reportar", "aportar informacion", "aportar información"]
            if any(i in clean_text for i in intenciones):
                await self._send_classification_menu(chat_id)
                return

            await self.send_message(chat_id, f"🤖 *Hola. Soy {WHATSAPP_CONFIG['BOT_NAME']}.*\n\nEste sistema recibe reportes de extorsión para análisis forense con IA y entrega de inteligencia a las autoridades competentes.\n\nPara aportar información, escribe *reportar* o *denunciar* para activar el asistente de ingesta.\n\n⚠️ Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría más cercana.")
            return

        # --- WAITING_FOR_DENUNCIA ---
        # Texto puro en estado activo: procesar como denuncia de texto
        await self._create_denuncia_from_batch(chat_id, [msg])

    # -----------------------------------------
    # Procesamiento de batch (múltiples mensajes)
    # -----------------------------------------

    async def _process_message_batch(self, chat_id: str, messages: List[dict]):
        """Procesa un grupo de mensajes (imágenes, audios, etc.) como una sola denuncia."""
        chat_state = self.user_states.get(chat_id, 'idle')

        # Si está en idle y llega un batch con adjuntos, activar asistente implícitamente
        if chat_state == 'idle':
            self.user_states[chat_id] = 'waiting_for_denuncia'

        await self._create_denuncia_from_batch(chat_id, messages)

    async def _create_denuncia_from_batch(self, chat_id: str, messages: List[dict]):
        """
        Crea una sola denuncia a partir de uno o más mensajes.
        Combina textos/captions y descarga todos los archivos adjuntos.
        """
        textos = []
        archivos_descargados = []
        msg_id_principal = None
        sender = None
        sender_name = None

        for msg in messages:
            msg_type = msg.get("type", "text")
            msg_id = msg.get("id")

            # Tomar el primer msg_id como ID principal de la denuncia
            if msg_id_principal is None:
                msg_id_principal = msg_id
                sender = msg.get("from")
                sender_name = msg.get("from_name") or msg.get("fromName")

            # Extraer texto/caption
            texto_msg = ""
            if msg_type == "text":
                texto_msg = msg.get("text", {}).get("body", "")
            else:
                # Buscar caption en el objeto del tipo o en el msg directo
                media_obj = msg.get(msg_type, {})
                texto_msg = msg.get("caption", "") or media_obj.get("caption", "") or ""

            texto_msg = texto_msg.strip()
            if texto_msg:
                textos.append(texto_msg)

            # Descargar adjunto si existe
            if msg_type in ["image", "audio", "voice", "document", "video"]:
                media_obj = msg.get(msg_type, {})
                media_id = media_obj.get("id")
                if media_id:
                    ext = media_obj.get("mime_type", "").split("/")[-1] or msg_type
                    if ext == "jpeg":
                        ext = "jpg"
                    safe_name = f"{msg_id or 'unknown'}_{msg_type}.{ext}"
                    dest_path = f"/app/uploads/evidencias/{safe_name}"
                    downloaded = await self.download_media(media_id, dest_path)
                    if downloaded:
                        # Mapear tipo de WhatsApp a tipo interno consistente
                        tipo_mapped = msg_type
                        if msg_type == "image":
                            tipo_mapped = "imagen"
                        elif msg_type == "voice":
                            tipo_mapped = "audio"
                        elif msg_type == "document":
                            tipo_mapped = "documento"
                        archivos_descargados.append({
                            "path": dest_path,
                            "tipo": tipo_mapped,
                            "mime": media_obj.get("mime_type", f"{msg_type}/{ext}"),
                            "filename": media_obj.get("filename") or safe_name,
                        })

        # Determinar tipo de contenido
        tiene_texto = bool(textos)
        tiene_adjuntos = bool(archivos_descargados)

        if tiene_texto and tiene_adjuntos:
            tipo_contenido = TipoContenido.MIXTO
        elif tiene_adjuntos:
            # Todos los adjuntos son del mismo tipo
            tipos = set(a["tipo"] for a in archivos_descargados)
            if len(tipos) == 1:
                t = list(tipos)[0]
                tipo_contenido = TipoContenido.IMAGEN if t == "imagen" else \
                                TipoContenido.AUDIO if t == "audio" else \
                                TipoContenido.VIDEO if t == "video" else TipoContenido.DOCUMENTO
            else:
                tipo_contenido = TipoContenido.MIXTO
        else:
            tipo_contenido = TipoContenido.TEXTO

        # Contenido raw: texto consolidado
        contenido_raw = "\n\n".join(textos) if textos else "[Sin texto descriptivo]"

        # URL del archivo principal (primero)
        url_archivo = archivos_descargados[0]["path"] if archivos_descargados else None

        # Archivos adicionales en metadata (sin PII del denunciante, RNF-01)
        import hashlib
        metadata = {
            "canal_origen": "whatsapp",
            "session_id": hashlib.sha256(str(chat_id).encode()).hexdigest()[:16],
            "batch_size": len(messages),
        }
        if len(archivos_descargados) > 1:
            metadata["archivos_adicionales"] = archivos_descargados[1:]

        # Validaciones de contenido
        clean_text = contenido_raw.lower().strip()
        if not contenido_raw.strip() or contenido_raw == "[Sin texto descriptivo]":
            if not archivos_descargados:
                await self.send_message(chat_id, "❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia para que podamos generar inteligencia útil.")
                return

        # Filtros de relleno solo si no hay adjuntos
        if not archivos_descargados and len(clean_text) < 15:
            await self.send_message(chat_id, "ℹ️ *Descripción muy corta.* Por favor proporciona más detalles para generar inteligencia útil (mínimo 15 caracteres) o envía un audio.")
            return

        await self.send_message(chat_id, "🔍 _Procesando tu reporte... Guardando evidencias y analizando con agentes de IA forense..._")

        try:
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.WHATSAPP,
                    id_externo=str(msg_id_principal),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata=metadata
                )
                denuncia = await service.crear_denuncia(req)
                await service.ejecutar_grafo(denuncia, modo="completo")
                await db.refresh(denuncia)

            # Restablecer estado
            self.user_states[chat_id] = 'idle'

            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"
            n_archivos = len(archivos_descargados)
            archivos_msg = f" ({n_archivos} archivos adjuntos)" if n_archivos > 1 else ""

            reply_msg = (
                f"✅ *Reporte Registrado Exitosamente*{archivos_msg}\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Estimado:* *{nivel_riesgo_str}*\n\n"
                f"Tu información será analizada por IA forense y entregada a las autoridades competentes para inteligencia operativa.\n\n"
                f"Puedes consultar el estado de análisis de tu reporte en:\n"
                f"http://localhost:3000/tracking?code={tracking_code}\n\n"
                f"⚠️ Recuerda: Este sistema es de inteligencia ciudadana. Para denuncias formales ante la Fiscalía o PNP, utiliza la línea 111 o acude a la comisaría."
            )
            await self.send_message(chat_id, reply_msg)

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
            logger.error(f"Error procesando denuncia de WhatsApp: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")
