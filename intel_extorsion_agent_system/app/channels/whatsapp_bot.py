import asyncio
import logging
import httpx
from typing import Dict, Any, Optional, List

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)


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

    async def close(self):
        await self.http_client.aclose()
        logger.info("Cliente HTTP de WhatsAppBot cerrado.")

    # -----------------------------------------
    # Envío de mensajes
    # -----------------------------------------

    async def send_message(self, chat_id: str, text: str):
        """Envía un mensaje de texto de WhatsApp a un chat específico"""
        url = f"{self.api_url}/messages/text"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"to": chat_id, "body": text}
        try:
            resp = await self.http_client.post(url, json=payload, headers=headers)
            if resp.status_code not in [200, 201]:
                logger.error(f"Error al enviar mensaje de WhatsApp ({resp.status_code}): {resp.text}")
            else:
                logger.debug(f"Mensaje enviado con éxito a {chat_id}")
        except Exception as e:
            logger.error(f"Error HTTP al enviar mensaje a WhatsApp: {e}")

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
                "🛡️ *Bienvenido al canal oficial de IntelExtorsión en WhatsApp*\n\n"
                "Esta plataforma te permite registrar denuncias de extorsión de forma 100% anónima y segura.\n\n"
                "✍️ *¿Cómo registrar tu denuncia?*\n"
                "• Escribe una descripción detallada en un mensaje de texto.\n"
                "• Envía una nota de voz o archivo de audio explicando los hechos (lo transcribiremos automáticamente).\n\n"
                "🔍 *¿Cómo consultar un caso?*\n"
                "• Envía el código de tu caso en formato `TRJ-XXXX` para consultar su estado actual.\n\n"
                "Tus evidencias quedarán custodiadas inmutablemente con hash criptográfico en la blockchain zkSYS."
            )
            await self.send_message(chat_id, welcome)
            return

        if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
            self.user_states[chat_id] = 'idle'
            await self.send_message(chat_id, "❌ *Reporte cancelado.*\n\nEl asistente de ingesta ha sido desactivado. Escribe *denunciar* para comenzar.")
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
                await self.send_message(chat_id, "👋 *¡Hola!* Escribe *denunciar* para activar el asistente de ingesta.")
                return

            intenciones = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia",
                           "nueva denuncia", "registrar otra", "denunciar", "quiero reportar"]
            if any(i in clean_text for i in intenciones):
                self.user_states[chat_id] = 'waiting_for_denuncia'
                await self.send_message(
                    chat_id,
                    "📝 *Asistente de Ingesta Activado.*\n\n"
                    "Por favor, descríbeme detalladamente los hechos *en tu siguiente mensaje*. "
                    "Recuerda incluir teléfonos, cuentas bancarias, amenazas.\n\n"
                    "También puedes adjuntar imágenes o documentos de soporte. Escribe *cancelar* para abortar."
                )
                return

            await self.send_message(chat_id, "🤖 Escribe *denunciar* para activar el asistente de ingesta.")
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
                        archivos_descargados.append({
                            "path": dest_path,
                            "tipo": msg_type,
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
                tipo_contenido = TipoContenido.IMAGEN if t == "image" else \
                                TipoContenido.AUDIO if t in ["audio", "voice"] else \
                                TipoContenido.VIDEO if t == "video" else TipoContenido.DOCUMENTO
            else:
                tipo_contenido = TipoContenido.MIXTO
        else:
            tipo_contenido = TipoContenido.TEXTO

        # Contenido raw: texto consolidado
        contenido_raw = "\n\n".join(textos) if textos else "[Sin texto descriptivo]"

        # URL del archivo principal (primero)
        url_archivo = archivos_descargados[0]["path"] if archivos_descargados else None

        # Archivos adicionales en metadata
        metadata = {
            "whatsapp_sender": sender,
            "whatsapp_name": sender_name,
            "chat_id": chat_id,
            "batch_size": len(messages),
        }
        if len(archivos_descargados) > 1:
            metadata["archivos_adicionales"] = archivos_descargados[1:]

        # Validaciones de contenido
        clean_text = contenido_raw.lower().strip()
        if not contenido_raw.strip() or contenido_raw == "[Sin texto descriptivo]":
            if not archivos_descargados:
                await self.send_message(chat_id, "❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia.")
                return

        # Filtros de relleno solo si no hay adjuntos
        if not archivos_descargados and len(clean_text) < 15:
            await self.send_message(chat_id, "ℹ️ *Descripción muy corta.* Por favor proporciona más detalles (mínimo 15 caracteres) o envía un audio.")
            return

        await self.send_message(chat_id, "🔍 _Procesando denuncia formal... Guardando evidencias y analizando con agentes de IA..._")

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
                f"✅ *Denuncia Registrada Exitosamente*{archivos_msg}\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Estimado:* *{nivel_riesgo_str}*\n\n"
                f"Puedes auditar el análisis de IA forense y el sellado de blockchain en:\n"
                f"http://localhost:3000/tracking?code={tracking_code}"
            )
            await self.send_message(chat_id, reply_msg)

        except Exception as e:
            logger.error(f"Error procesando denuncia de WhatsApp: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")
