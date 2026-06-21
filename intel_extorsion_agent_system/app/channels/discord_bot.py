import asyncio
import logging
import discord
from typing import Optional, Dict

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

class DiscordBot(discord.Client):
    """
    Cliente de Discord para recibir denuncias ciudadanas de extorsión,
    transcribir audios de forma automática y ejecutar el grafo de agentes de IA.
    """
    
    def __init__(self, token: str):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.token = token
        self.user_states: Dict[int, str] = {}  # user_id -> 'idle' | 'waiting_for_denuncia'
        
    async def on_ready(self):
        print(f"Bot de Discord conectado exitosamente como {self.user} (ID: {self.user.id})", flush=True)
        logger.info(f"Bot de Discord conectado exitosamente como {self.user}")
        
    async def on_message(self, message: discord.Message):
        # Evitar responderse a sí mismo
        if message.author == self.user:
            return
            
        # Responder solo a Mensajes Privados (DM) o menciones directas
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions
        
        if not is_dm and not is_mentioned:
            return
            
        # Limpiar la mención en el texto si la hay
        text_content = message.content
        if is_mentioned:
            mention_str = f"<@{self.user.id}>"
            mention_str_nick = f"<@!{self.user.id}>"
            text_content = text_content.replace(mention_str, "").replace(mention_str_nick, "")
            
        text = text_content.strip()
        clean_text = text.lower().strip()
        
        # Si está vacío y no hay adjuntos, ignorar
        if not clean_text and not message.attachments:
            return
            
        # 1. Comandos de ayuda o bienvenida (siempre disponibles)
        if clean_text in ["!start", "!help", "help", "ayuda", "info", "/start", "/help"]:
            welcome_msg = (
                "🛡️ **Bienvenido al canal oficial de IntelExtorsión en Discord**\n\n"
                "Esta plataforma te permite registrar denuncias de extorsión de forma 100% anónima y segura.\n\n"
                "✍️ **¿Cómo registrar tu denuncia?**\n"
                "• Escribe una descripción detallada en un mensaje de texto.\n"
                "• Envía una nota de voz o archivo de audio explicando los hechos (lo transcribiremos automáticamente).\n\n"
                "🔍 **¿Cómo consultar un caso?**\n"
                "• Envía el código de tu caso en formato `TRJ-XXXX` para consultar su estado actual.\n\n"
                "Tus evidencias quedarán custodiadas inmutablemente con hash criptográfico en la blockchain zkSYS."
            )
            await message.channel.send(welcome_msg)
            return

        # 2. Comando de cancelación (siempre disponible)
        if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
            self.user_states[message.author.id] = 'idle'
            await message.channel.send(
                "❌ **Reporte cancelado.**\n\n"
                "El asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué deseas hacer hoy? Puedes volver a iniciar escribiendo 'denunciar'."
            )
            return

        # Recuperar estado de sesión
        chat_state = self.user_states.get(message.author.id, 'idle')

        # --- FLUJO ESTADO: IDLE ---
        if chat_state == 'idle':
            if clean_text:
                # A. Búsqueda y Tracking de Denuncias
                if clean_text.startswith("trj-") or (len(clean_text) == 8 and clean_text.startswith("trj")):
                    tracking_code = clean_text.upper()
                    await message.channel.send(f"🔍 *Buscando estado de la denuncia {tracking_code}...*")
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
                                msg = (
                                    f"🎫 **Denuncia Encontrada:** `{tracking_code}`\n"
                                    f"⚖️ **Nivel de Riesgo:** **{nivel_riesgo_str}**\n"
                                    f"📋 **Estado del Expediente:** `{denuncia.estado.value.upper()}`\n\n"
                                    f"Puedes auditar todo el historial de IA y blockchain en nuestro Portal de Tracking:\n"
                                    f"http://localhost:3000/tracking?code={tracking_code}"
                                )
                                await message.channel.send(msg)
                            else:
                                await message.channel.send(f"❌ No se encontró ninguna denuncia con el código `{tracking_code}`. Verifica que esté bien escrito.")
                    except Exception as e:
                        logger.error(f"Error al rastrear denuncia {tracking_code}: {e}")
                        await message.channel.send(f"❌ Ocurrió un error al buscar la denuncia: {str(e)}")
                    return

                # B. Respuestas conversacionales (Saludos)
                saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
                if clean_text in saludos or any(s == clean_text for s in saludos) or clean_text in ["hola!", "hola."]:
                    await message.channel.send(
                        "👋 **¡Hola!** Estoy aquí para ayudarte a registrar tu reporte de extorsión de forma segura.\n\n"
                        "Por favor, escribe **denunciar** o envía el comando `!denunciar` para activar el asistente de ingesta."
                    )
                    return

                # C. Intención de reportar
                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "quiero reportar"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[message.author.id] = 'waiting_for_denuncia'
                    await message.channel.send(
                        "📝 **Asistente de Ingesta Activado.**\n\n"
                        "Por favor, descríbeme detalladamente los hechos **en tu siguiente mensaje**. Recuerda incluir:\n"
                        "- Teléfonos desde donde te contactaron.\n"
                        "- Nombres o cuentas bancarias de cobro si te las dieron.\n"
                        "- Tipo de amenaza o exigencias de dinero.\n\n"
                        "También puedes adjuntar imágenes o documentos de soporte. Si deseas abortar el proceso, escribe **cancelar**."
                    )
                    return

            # Fallback en IDLE
            await message.channel.send(
                "🤖 **Hola. Para poder registrar una denuncia formal de extorsión, primero debemos activar el asistente de ingesta.**\n\n"
                "Por favor, escribe la palabra **denunciar** para comenzar."
            )
            return

        # --- FLUJO ESTADO: WAITING_FOR_DENUNCIAS ---
        tipo_contenido = TipoContenido.TEXTO
        contenido_raw = text
        url_archivo = None
        
        # Validar si contiene adjuntos
        is_audio_file = False
        if message.attachments:
            attachment = message.attachments[0]
            content_type = attachment.content_type or ""
            is_audio_file = "audio" in content_type or any(attachment.filename.lower().endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"])

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

            if (es_saludo or es_intencion or es_relleno) and not message.attachments:
                await message.channel.send(
                    "📝 **Asistente Esperando Detalles.**\n\n"
                    "⚠️ No detectamos detalles del hecho en tu mensaje.\n\n"
                    "Por favor, redacta **en un único mensaje consolidado** todo lo sucedido cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas), o envíanos un audio explicativo.\n\n"
                    "*Si deseas cancelar el reporte actual, escribe **cancelar**.*"
                )
                return

            # Validar longitud mínima si no hay adjuntos
            if len(clean_text) < 15 and not message.attachments:
                await message.channel.send(
                    "ℹ️ **Descripción muy corta.** Para poder procesar y correlacionar tu caso, por favor proporciona una explicación más detallada de lo sucedido (mínimo 15 caracteres) o envía un audio explicativo."
                )
                return

        # Procesar adjuntos
        if message.attachments:
            attachment = message.attachments[0]
            url_archivo = attachment.url
            
            if is_audio_file:
                tipo_contenido = TipoContenido.AUDIO
                await message.channel.send("🎙️ *Audio recibido. Transcribiendo y ejecutando agentes de IA...*")
                
                # Transcribir usando Whisper
                stt_res = await transcribe_audio(url_archivo)
                if stt_res.get("transcripcion"):
                    contenido_raw = stt_res["transcripcion"]
                else:
                    await message.channel.send(f"❌ Error en la transcripción: {stt_res.get('error', 'desconocido')}")
                    return
            else:
                content_type = attachment.content_type or ""
                is_image = "image" in content_type or any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"])
                if is_image:
                    tipo_contenido = TipoContenido.IMAGEN
                else:
                    tipo_contenido = TipoContenido.DOCUMENTO
                
                if not contenido_raw:
                    contenido_raw = f"[Evidencia adjunta: {attachment.filename}]"
                    
        if not contenido_raw or not contenido_raw.strip():
            await message.channel.send("❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia.")
            return
            
        await message.channel.send("🔍 *Procesando denuncia formal... Guardando evidencias y analizando con agentes de IA...*")
        
        try:
            # Crear denuncia y ejecutar grafo
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.DISCORD,
                    id_externo=str(message.id),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata={
                        "discord_user_id": str(message.author.id),
                        "discord_user_name": str(message.author),
                        "channel_id": str(message.channel.id)
                    }
                )
                denuncia = await service.crear_denuncia(req)
                
                # Ejecutar grafo
                await service.ejecutar_grafo(denuncia, modo="completo")
                await db.refresh(denuncia)
                
            # Restablecer estado a IDLE al registrar con éxito
            self.user_states[message.author.id] = 'idle'
            
            # Datos de respuesta
            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"
            
            reply_msg = (
                f"✅ **Denuncia Registrada Exitosamente**\n\n"
                f"🎫 **Código de seguimiento:** `{tracking_code}`\n"
                f"⚖️ **Nivel de Riesgo Estimado:** **{nivel_riesgo_str}**\n\n"
                f"Puedes auditar el análisis de IA forense y el sellado de blockchain en:\n"
                f"http://localhost:3000/tracking?code={tracking_code}"
            )
            await message.channel.send(reply_msg)
            
        except Exception as e:
            logger.error(f"Error procesando denuncia de Discord: {e}", exc_info=True)
            await message.channel.send(f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")
