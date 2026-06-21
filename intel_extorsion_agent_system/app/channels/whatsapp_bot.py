import asyncio
import logging
import httpx
from typing import Dict, Any, Optional

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
    """
    
    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://gate.whapi.cloud"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.user_states: Dict[str, str] = {}  # chat_id -> 'idle' | 'waiting_for_denuncia'
        
    async def close(self):
        await self.http_client.aclose()
        logger.info("Cliente HTTP de WhatsAppBot cerrado.")
        
    async def send_message(self, chat_id: str, text: str):
        """Envía un mensaje de texto de WhatsApp a un chat específico"""
        url = f"{self.api_url}/messages/text"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "to": chat_id,
            "body": text
        }
        try:
            resp = await self.http_client.post(url, json=payload, headers=headers)
            if resp.status_code not in [200, 201]:
                logger.error(f"Error al enviar mensaje de WhatsApp ({resp.status_code}): {resp.text}")
            else:
                logger.debug(f"Mensaje enviado con éxito a {chat_id}")
        except Exception as e:
            logger.error(f"Error HTTP al enviar mensaje a WhatsApp: {e}")
            
    async def process_webhook(self, data: dict):
        """Procesa el JSON entrante del webhook de Whapi.cloud"""
        print(f"[WhatsApp Webhook] Payload recibido: {data}", flush=True)
        messages = data.get("messages", [])
        if not messages:
            print("[WhatsApp Webhook] No se encontraron mensajes en el payload.", flush=True)
            return
            
        for msg in messages:
            # Ignorar mensajes salientes enviados por el propio bot
            if msg.get("from_me") or msg.get("fromMe"):
                print("[WhatsApp Webhook] Ignorando mensaje saliente (from_me=True).", flush=True)
                continue
                
            print(f"[WhatsApp Webhook] Procesando mensaje: {msg}", flush=True)
            try:
                await self._process_message(msg)
            except Exception as ex:
                print(f"[WhatsApp Webhook] Error al procesar mensaje: {ex}", flush=True)
                logger.exception("Error en _process_message")
            
    async def _process_message(self, msg: dict):
        chat_id = msg.get("chat_id") or msg.get("chatId")
        if not chat_id:
            return
            
        # Ignorar mensajes de grupos para evitar spam
        if "@g.us" in chat_id:
            print(f"[WhatsApp Webhook] Ignorando mensaje de grupo: {chat_id}", flush=True)
            return
            
        msg_id = msg.get("id")
        msg_type = msg.get("type", "text")
        
        # Obtener el texto del mensaje
        text = ""
        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
        else:
            # Si tiene un caption/texto acompañando al archivo
            text = msg.get("caption", "") or msg.get(msg_type, {}).get("caption", "") or ""
            
        text = text.strip()
        clean_text = text.lower().strip()
        
        # Recuperar estado de sesión del usuario
        chat_state = self.user_states.get(chat_id, 'idle')
        
        # Comando de ayuda o bienvenida (siempre disponible)
        if clean_text in ["!start", "!help", "help", "ayuda", "info", "/start", "/help"]:
            welcome_msg = (
                "🛡️ *Bienvenido al canal oficial de IntelExtorsión en WhatsApp*\n\n"
                "Esta plataforma te permite registrar denuncias de extorsión de forma 100% anónima y segura.\n\n"
                "✍️ *¿Cómo registrar tu denuncia?*\n"
                "• Escribe una descripción detallada en un mensaje de texto.\n"
                "• Envía una nota de voz o archivo de audio explicando los hechos (lo transcribiremos automáticamente).\n\n"
                "🔍 *¿Cómo consultar un caso?*\n"
                "• Envía el código de tu caso en formato `TRJ-XXXX` para consultar su estado actual.\n\n"
                "Tus evidencias quedarán custodiadas inmutablemente con hash criptográfico en la blockchain zkSYS."
            )
            await self.send_message(chat_id, welcome_msg)
            return

        # Comando de cancelación (siempre disponible)
        if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
            self.user_states[chat_id] = 'idle'
            await self.send_message(
                chat_id,
                "❌ *Reporte cancelado.*\n\n"
                "El asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué deseas hacer hoy? Puedes volver a iniciar escribiendo *denunciar*."
            )
            return

        # --- FLUJO ESTADO: IDLE ---
        if chat_state == 'idle':
            if clean_text:
                # A. Búsqueda y Tracking de Denuncias
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
                                nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"
                                msg_status = (
                                    f"🎫 *Denuncia Encontrada:* `{tracking_code}`\n"
                                    f"⚖️ *Nivel de Riesgo:* *{nivel_riesgo_str}*\n"
                                    f"📋 *Estado del Expediente:* `{denuncia.estado.value.upper()}`\n\n"
                                    f"Puedes auditar todo el historial de IA y blockchain en nuestro Portal de Tracking:\n"
                                    f"http://localhost:3000/tracking?code={tracking_code}"
                                )
                                await self.send_message(chat_id, msg_status)
                            else:
                                await self.send_message(chat_id, f"❌ No se encontró ninguna denuncia con el código `{tracking_code}`. Verifica que esté bien escrito.")
                    except Exception as e:
                        logger.error(f"Error al rastrear denuncia {tracking_code}: {e}")
                        await self.send_message(chat_id, f"❌ Ocurrió un error al buscar la denuncia: {str(e)}")
                    return

                # B. Respuestas conversacionales (Saludos)
                saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
                if clean_text in saludos or any(s == clean_text for s in saludos) or clean_text in ["hola!", "hola."]:
                    await self.send_message(
                        chat_id,
                        "👋 *¡Hola!* Estoy aquí para ayudarte a registrar tu reporte de extorsión de forma segura.\n\n"
                        "Por favor, escribe *denunciar* o presiona el comando /denunciar para activar el asistente de ingesta."
                    )
                    return

                # C. Activar Asistente
                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "quiero reportar"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[chat_id] = 'waiting_for_denuncia'
                    await self.send_message(
                        chat_id,
                        "📝 *Asistente de Ingesta Activado.*\n\n"
                        "Por favor, descríbeme detalladamente los hechos *en tu siguiente mensaje*. Recuerda incluir:\n"
                        "- Teléfonos desde donde te contactaron.\n"
                        "- Nombres o cuentas bancarias de cobro si te las dieron.\n"
                        "- Tipo de amenaza o exigencias de dinero.\n\n"
                        "También puedes adjuntar imágenes o documentos de soporte. Si deseas abortar el proceso, escribe *cancelar*."
                    )
                    return

            # Fallback en IDLE
            await self.send_message(
                chat_id,
                "🤖 *Hola. Para poder registrar una denuncia formal de extorsión, primero debemos activar el asistente de ingesta.*\n\n"
                "Por favor, escribe la palabra *denunciar* para comenzar."
            )
            return

        # --- FLUJO ESTADO: WAITING_FOR_DENUNCIAS ---
        tipo_contenido = TipoContenido.TEXTO
        contenido_raw = text
        url_archivo = None
        
        # Validar si contiene adjuntos
        has_attachment = msg_type in ["image", "audio", "voice", "document", "video"]
        
        if text:
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

            if (es_saludo or es_intencion or es_relleno) and not has_attachment:
                await self.send_message(
                    chat_id,
                    "📝 *Asistente Esperando Detalles.*\n\n"
                    "⚠️ No detectamos detalles del hecho en tu mensaje.\n\n"
                    "Por favor, redacta *en un único mensaje consolidado* todo lo sucedido cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas), o envíanos un audio explicativo.\n\n"
                    "*Si deseas cancelar el reporte actual, escribe **cancelar**.*"
                )
                return

            # Validar longitud mínima
            if len(clean_text) < 15 and not has_attachment:
                await self.send_message(
                    chat_id,
                    "ℹ️ *Descripción muy corta.* Para poder procesar y correlacionar tu caso, por favor proporciona una explicación más detallada de lo sucedido (mínimo 15 caracteres) o envía un audio explicativo."
                )
                return

        # Procesar adjuntos
        if has_attachment:
            media_obj = msg.get(msg_type, {})
            url_archivo = media_obj.get("link")
            
            if msg_type in ["audio", "voice"]:
                tipo_contenido = TipoContenido.AUDIO
                await self.send_message(chat_id, "🎙️ _Audio recibido. Transcribiendo y ejecutando agentes de IA..._")
                
                # Transcribir usando Whisper
                stt_res = await transcribe_audio(url_archivo)
                if stt_res.get("transcripcion"):
                    contenido_raw = stt_res["transcripcion"]
                else:
                    await self.send_message(chat_id, f"❌ Error en la transcripción: {stt_res.get('error', 'desconocido')}")
                    return
            else:
                if msg_type == "image":
                    tipo_contenido = TipoContenido.IMAGEN
                else:
                    tipo_contenido = TipoContenido.DOCUMENTO
                
                if not contenido_raw:
                    filename = media_obj.get("filename") or f"evidencia.{msg_type}"
                    contenido_raw = f"[Evidencia adjunta: {filename}]"
                    
        if not contenido_raw or not contenido_raw.strip():
            await self.send_message(chat_id, "❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia.")
            return
            
        await self.send_message(chat_id, "🔍 _Procesando denuncia formal... Guardando evidencias y analizando con agentes de IA..._")
        
        try:
            # Crear denuncia y ejecutar grafo
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.WHATSAPP,
                    id_externo=str(msg_id),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata={
                        "whatsapp_sender": msg.get("from"),
                        "whatsapp_name": msg.get("from_name") or msg.get("fromName"),
                        "chat_id": chat_id
                    }
                )
                denuncia = await service.crear_denuncia(req)
                
                # Ejecutar grafo
                await service.ejecutar_grafo(denuncia, modo="completo")
                await db.refresh(denuncia)
                
            # Restablecer estado a IDLE al registrar con éxito
            self.user_states[chat_id] = 'idle'
            
            # Datos de respuesta
            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"
            
            reply_msg = (
                f"✅ *Denuncia Registrada Exitosamente*\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Estimado:* *{nivel_riesgo_str}*\n\n"
                f"Puedes auditar el análisis de IA forense y el sellado de blockchain en:\n"
                f"http://localhost:3000/tracking?code={tracking_code}"
            )
            await self.send_message(chat_id, reply_msg)
            
        except Exception as e:
            logger.error(f"Error procesando denuncia de WhatsApp: {e}", exc_info=True)
            await self.send_message(chat_id, f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")
