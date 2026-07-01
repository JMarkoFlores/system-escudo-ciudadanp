import asyncio
import logging
import discord
import os
from typing import Optional, Dict, List, Any
from datetime import datetime

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads/evidencias"

# Configuración personalizada del bot
BOT_CONFIG = {
    "BOT_NAME": "IntelExtorsión Bot",
    "BOT_COLOR": 0x00BFFF,  # Sky blue
    "BOT_EMOJI": "🛡️",
    "WELCOME_CHANNEL": "welcome",
    "REPORT_CHANNEL": "reports",
    "STATS_CHANNEL": "statistics",
    "ADMIN_ROLE": "Administrator",
    "ANALYST_ROLE": "Analyst",
    "CITIZEN_ROLE": "Citizen",
}


class DiscordBot(discord.Client):
    """
    Custom Discord client for IntelExtorsión.
    
    Features:
    - Extortion report reception
    - Automatic audio transcription
    - AI agent graph execution
    - Personalized welcome messages
    - Styled embeds
    - System statistics
    - Multi-file support (batching)
    """

    def __init__(self, token: str):
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.guilds = True
        intents.members = True  # For on_member_join event (Server Members Intent must be enabled in Discord Developer Portal)
        # intents.presences = True  # Requires privileged intent (not currently used)
        super().__init__(intents=intents)
        self.token = token
        self.user_states: Dict[int, str] = {}  # user_id -> 'idle' | 'waiting_for_denuncia'
        self.pending_batches: Dict[int, Dict[str, Any]] = {}  # user_id -> {messages: [], timer: asyncio.Task | None}
        self.start_time = datetime.now()

    async def on_ready(self):
        print(f"Bot de Discord conectado exitosamente como {self.user} (ID: {self.user.id})", flush=True)
        logger.info(f"Bot de Discord conectado exitosamente como {self.user} (ID: {self.user.id})")
        print(f"[Discord Bot] Guilds conectados: {len(self.guilds)}", flush=True)
        
        # Set custom bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="extortion reports | !help"
            )
        )
        
        # Log connected servers
        for guild in self.guilds:
            print(f"[Discord Bot] Server: {guild.name} (ID: {guild.id}) - {guild.member_count} members", flush=True)

    async def on_disconnect(self):
        print("[Discord Bot] *** BOT DESCONECTADO de Discord ***", flush=True)
        logger.warning("Bot de Discord desconectado")

    async def on_resumed(self):
        print("[Discord Bot] Conexión reanudada", flush=True)
        logger.info("Bot de Discord reanudó conexión")

    async def on_error(self, event_method, error):
        print(f"[Discord Bot] ERROR en {event_method}: {error}", flush=True)
        logger.error(f"Error en Discord bot ({event_method}): {error}", exc_info=True)
    
    async def on_member_join(self, member):
        """Event when a new member joins the server."""
        # Find welcome channel
        welcome_channel = discord.utils.get(
            member.guild.text_channels,
            name=BOT_CONFIG["WELCOME_CHANNEL"]
        )
        
        if welcome_channel:
            welcome_embed = discord.Embed(
                title=f"{BOT_CONFIG['BOT_EMOJI']} Welcome to IntelExtorsión",
                description=f"Hello {member.mention}! Thank you for joining the Citizen Intelligence community.",
                color=BOT_CONFIG["BOT_COLOR"]
            )
            welcome_embed.add_field(
                name="📋 What is this server?",
                value="This is a space to report extortion cases safely and anonymously. Reports are analyzed by forensic AI and delivered to competent authorities.",
                inline=False
            )
            welcome_embed.add_field(
                name="✍️ How to report?",
                value="Send me a private message (DM) with `!help` to get started, or use the `!report` command in the #reports channel.",
                inline=False
            )
            welcome_embed.add_field(
                name="⚠️ Important",
                value="This system is NOT a direct police complaint channel. For formal complaints, use the 111 hotline.",
                inline=False
            )
            welcome_embed.set_footer(text=f"Member #{member.guild.member_count} | {datetime.now().strftime('%d/%m/%Y')}")
            
            await welcome_channel.send(embed=welcome_embed)
            
            # Assign default role
            citizen_role = discord.utils.get(member.guild.roles, name=BOT_CONFIG["CITIZEN_ROLE"])
            if citizen_role:
                await member.add_roles(citizen_role)
                logger.info(f"Role {BOT_CONFIG['CITIZEN_ROLE']} assigned to {member.name}")

    # -----------------------------------------
    # Descarga de archivos desde Discord CDN
    # -----------------------------------------

    async def download_attachment(self, attachment: discord.Attachment, dest_path: str) -> bool:
        """Descarga un archivo adjunto de Discord y lo guarda localmente."""
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            data = await attachment.read()
            with open(dest_path, "wb") as f:
                f.write(data)
            logger.info(f"[Discord] Archivo descargado: {dest_path} ({len(data)} bytes)")
            return True
        except Exception as e:
            logger.error(f"[Discord] Error descargando archivo {attachment.filename}: {e}")
            return False

    # -----------------------------------------
    # Eventos de Discord
    # -----------------------------------------

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

        # 1. Help or welcome commands (always available)
        if clean_text in ["!start", "!help", "help", "ayuda", "info", "/start", "/help"]:
            help_embed = discord.Embed(
                title=f"{BOT_CONFIG['BOT_EMOJI']} IntelExtorsión - Citizen Intelligence",
                description="Extortion case reporting and analysis system with forensic AI",
                color=BOT_CONFIG["BOT_COLOR"]
            )
            help_embed.add_field(
                name="⚠️ IMPORTANT",
                value="This system is NOT a direct police complaint channel. It is a **CITIZEN INTELLIGENCE** platform that receives reports, analyzes them with forensic AI, and delivers processed intelligence to competent authorities (DIVINCRI La Libertad).",
                inline=False
            )
            help_embed.add_field(
                name="📋 What does this system do?",
                value="• Receives reports 100% anonymously\n• Analyzes with 10 specialized AI agents\n• Correlates similar cases\n• Delivers intelligence to authorities\n• Seals evidence on blockchain",
                inline=False
            )
            help_embed.add_field(
                name="✍️ Available commands",
                value="`!report` - Start a new report\n`!stats` - View system statistics\n`!info` - Bot information\n`!cancel` - Cancel current report",
                inline=False
            )
            help_embed.add_field(
                name="🔍 Check report status",
                value="Send the code in format `TRJ-XXXX` to check its status",
                inline=False
            )
            help_embed.add_field(
                name="📞 Formal complaints",
                value="For formal complaints to the Prosecutor's Office or Police, use the 111 hotline or go to the nearest police station.",
                inline=False
            )
            help_embed.set_footer(text=f"Bot active since: {self.start_time.strftime('%d/%m/%Y %H:%M')}")
            
            await message.channel.send(embed=help_embed)
            return
        
        # Statistics command
        if clean_text in ["!stats", "!estadisticas", "stats", "estadisticas"]:
            await self._send_stats(message.channel)
            return
        
        # Bot information command
        if clean_text in ["!info", "!botinfo", "info", "botinfo"]:
            info_embed = discord.Embed(
                title=f"🤖 {BOT_CONFIG['BOT_NAME']} Information",
                color=BOT_CONFIG["BOT_COLOR"]
            )
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            info_embed.add_field(name="🟢 Status", value="Online", inline=True)
            info_embed.add_field(name="⏱️ Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
            info_embed.add_field(name="🌐 Servers", value=str(len(self.guilds)), inline=True)
            info_embed.add_field(name="👥 Active users", value=str(sum(g.member_count for g in self.guilds)), inline=True)
            info_embed.add_field(name="📊 Reports processed", value="See !stats", inline=True)
            info_embed.set_footer(text="IntelExtorsión v1.0.0 | Citizen Intelligence")
            
            await message.channel.send(embed=info_embed)
            return

        # 2. Cancel command (always available)
        if clean_text in ["cancelar", "salir", "cancel", "/cancel"]:
            self.user_states[message.author.id] = 'idle'
            # Clear pending batch
            if message.author.id in self.pending_batches:
                batch = self.pending_batches.pop(message.author.id)
                if batch.get("timer"):
                    batch["timer"].cancel()
            
            cancel_embed = discord.Embed(
                title="❌ Report Cancelled",
                description="The intake assistant has been deactivated and your session is now clean.",
                color=0xFF0000
            )
            cancel_embed.add_field(
                name="What would you like to do now?",
                value="Type `!report` to start a new report or `!help` to see available commands.",
                inline=False
            )
            await message.channel.send(embed=cancel_embed)
            return

        # Recuperar estado de sesión
        chat_state = self.user_states.get(message.author.id, 'idle')

        # --- FLUJO ESTADO: IDLE ---
        if chat_state == 'idle':
            if clean_text:
                # A. Búsqueda y Tracking de Denuncias
                if clean_text.startswith("trj-") or (len(clean_text) == 8 and clean_text.startswith("trj")):
                    tracking_code = clean_text.upper()
                    await message.channel.send(f"🔍 *Searching for report status {tracking_code}...*")
                    try:
                        async with AsyncSessionLocal() as db:
                            from sqlalchemy import select
                            from app.models.database import Denuncia
                            result = await db.execute(
                                select(Denuncia).where(Denuncia.tracking_code == tracking_code)
                            )
                            denuncia = result.scalar_one_or_none()
                            if denuncia:
                                nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDING"
                                msg = (
                                    f"🎫 **Report Found:** `{tracking_code}`\n"
                                    f"⚖️ **Risk Level:** **{nivel_riesgo_str}**\n"
                                    f"📋 **Case Status:** `{denuncia.estado.value.upper()}`\n\n"
                                    f"You can audit the complete AI and blockchain history in our Tracking Portal:\n"
                                    f"{settings.TRACKING_URL}?code={tracking_code}"
                                )
                                await message.channel.send(msg)
                            else:
                                await message.channel.send(f"❌ I couldn't find any report with code `{tracking_code}`. Please verify it's spelled correctly.")
                    except Exception as e:
                        logger.error(f"Error tracking report {tracking_code}: {e}")
                        await message.channel.send(f"❌ An error occurred while searching for the report: {str(e)}")
                    return

                # B. Respuestas conversacionales (Saludos)
                saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "que tal", "buen dia", "hello", "hi", "saludos"]
                if clean_text in saludos or any(s == clean_text for s in saludos) or clean_text in ["hola!", "hola.", "hello!", "hi!", "hey!"]:
                    await message.channel.send(
                        "👋 **Hello!** I'm the IntelExtorsión Citizen Intelligence assistant.\n\n"
                        "This system receives extortion reports, analyzes them with forensic AI, and delivers processed information to competent authorities to combat organized crime.\n\n"
                        "To report information, type **report** to activate the intake assistant.\n\n"
                        "⚠️ Remember: This is NOT a direct formal police complaint channel. For official complaints, use the 111 hotline or go to the police station."
                    )
                    return

                # C. Report intention -> classification menu RF-01
                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "quiero reportar", "reportar", "aportar informacion", "aportar información", "!reportar", "!report", "report", "i want to report", "make a report", "new report"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[message.author.id] = 'classifying'
                    menu_embed = discord.Embed(
                        title="🛡️ Report Classification Menu",
                        description="Does the threat come from:\n\n1️⃣ **Individual / Criminal gang**\n2️⃣ **Public official / Police**\n\nReply with `1` or `2`.",
                        color=BOT_CONFIG["BOT_COLOR"]
                    )
                    await message.channel.send(embed=menu_embed)
                    return

            # Fallback in IDLE
            fallback_embed = discord.Embed(
                title=f"{BOT_CONFIG['BOT_EMOJI']} Hello, I'm {BOT_CONFIG['BOT_NAME']}",
                description="This system receives extortion reports for forensic AI analysis and delivers intelligence to competent authorities.",
                color=BOT_CONFIG["BOT_COLOR"]
            )
            fallback_embed.add_field(
                name="✍️ To report information",
                value="Type `!report` or `report` to activate the intake assistant.",
                inline=False
            )
            fallback_embed.add_field(
                name="📞 For formal complaints",
                value="Use the 111 hotline or go to the nearest police station.",
                inline=False
            )
            await message.channel.send(embed=fallback_embed)
            return

        # --- FLUJO ESTADO: CLASSIFYING (RF-01) ---
        if chat_state == 'classifying':
            if clean_text in ["1", "one", "particular", "banda", "criminal", "gang", "delincuente"]:
                self.user_states[message.author.id] = 'waiting_for_denuncia'
                ingest_embed = discord.Embed(
                    title="📝 Intake Assistant Activated",
                    description="Please describe the facts in detail in your next message.",
                    color=BOT_CONFIG["BOT_COLOR"]
                )
                ingest_embed.add_field(
                    name="📋 Required information",
                    value="• Phone numbers that contacted you\n• Names or bank accounts for payment\n• Type of threat or money demands\n• Area or location where the events occurred",
                    inline=False
                )
                ingest_embed.add_field(
                    name="📎 Evidence",
                    value="You can attach images, audio files, or documents as evidence.",
                    inline=False
                )
                ingest_embed.add_field(
                    name="⚠️ Important",
                    value="Your information will be analyzed by forensic AI and delivered to competent authorities for operational intelligence. To abort, type `cancel`.",
                    inline=False
                )
                await message.channel.send(embed=ingest_embed)
                return
            elif clean_text in ["2", "two", "funcionario", "policía", "policia", "autoridad", "pnp", "official", "police"]:
                self.user_states[message.author.id] = 'idle'
                redirect_embed = discord.Embed(
                    title="🛡️ Report against Public Official / Police",
                    description="This channel is intended for extortion reports by *individuals or criminal gangs*. "
                                "If the threat comes from a public official or police officer, we recommend specialized channels:",
                    color=0xFF9900
                )
                redirect_embed.add_field(
                    name="📞 Canales recomendados",
                    value="• **Inspectoría General PNP:** Línea 1818 (Central de denuncias Mininter) | lineas1818@mininter.gob.pe\n• **Fiscalía Anticorrupción:** Línea 0800-00-205 (Línea de Integridad) | denunciascorrupcion@mpfn.gob.pe",
                    inline=False
                )
                redirect_embed.add_field(
                    name="🚫 Not registered",
                    value="Your report will **NOT** be registered in the DIVINCRI dashboard for institutional protection.",
                    inline=False
                )
                await message.channel.send(embed=redirect_embed)
                return
            else:
                await message.channel.send("⚠️ Please reply with `1` (individual/gang) or `2` (official/police).")
                return

        # --- FLUJO ESTADO: WAITING_FOR_DENUNCIA ---
        # Delegar al handler de batching
        await self._handle_incoming_message(message)

    # -----------------------------------------
    # Batching temporal
    # -----------------------------------------

    async def _handle_incoming_message(self, message: discord.Message):
        """
        Decide si procesar inmediatamente o agregar a un batch temporal.
        Mensajes con adjuntos se agrupan por usuario durante 3 segundos.
        """
        user_id = message.author.id
        has_attachments = len(message.attachments) > 0

        # Si es texto puro sin adjunto → procesar inmediatamente
        if not has_attachments and message.content.strip():
            await self._process_single_message(message)
            return

        # Si tiene adjunto → agregar al batch
        batch = self.pending_batches.get(user_id)
        if batch is None:
            batch = {"messages": [], "timer": None}
            self.pending_batches[user_id] = batch

        batch["messages"].append(message)

        # Cancelar timer anterior si existe
        if batch["timer"]:
            batch["timer"].cancel()

        # Programar procesamiento del batch en 3 segundos
        async def _trigger():
            await asyncio.sleep(3.0)
            await self._flush_batch(user_id)

        batch["timer"] = asyncio.create_task(_trigger())
        n_adjuntos = len(message.attachments)
        logger.info(f"[Discord] Mensaje con {n_adjuntos} adjunto(s) agregado a batch de {user_id}. Total en batch: {len(batch['messages'])}")

    async def _flush_batch(self, user_id: int):
        """Procesa el batch acumulado para un usuario y lo limpia."""
        batch = self.pending_batches.pop(user_id, None)
        if not batch or not batch["messages"]:
            return

        messages = batch["messages"]
        logger.info(f"[Discord] Procesando batch de {user_id} con {len(messages)} mensaje(s)")

        try:
            await self._process_message_batch(user_id, messages)
        except Exception as e:
            logger.exception(f"Error procesando batch de {user_id}")
            # Buscar canal para enviar error
            if messages:
                try:
                    await messages[0].channel.send(f"❌ Ocurrió un error inesperado al procesar tu denuncia: {str(e)}")
                except:
                    pass

    # -----------------------------------------
    # Procesamiento de mensaje único (texto)
    # -----------------------------------------

    async def _process_single_message(self, message: discord.Message):
        """Procesa un mensaje de texto individual (sin adjuntos)."""
        user_id = message.author.id
        text = message.content.strip()
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

        if es_saludo or es_intencion or es_relleno:
            await message.channel.send(
                "📝 **Asistente Esperando Detalles del Reporte.**\n\n"
                "⚠️ No detectamos detalles del hecho en tu mensaje.\n\n"
                "Por favor, redacta **en un único mensaje consolidado** toda la información relevante cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas, zona), o envíanos un audio explicativo.\n\n"
                "*Si deseas cancelar el reporte actual, escribe **cancelar**.*"
            )
            return

        # Validar longitud mínima
        if len(clean_text) < 15:
            await message.channel.send(
                "ℹ️ **Descripción muy corta.** Para poder procesar tu reporte y generar inteligencia útil para las autoridades, por favor proporciona más detalles (mínimo 15 caracteres) o envía un audio explicativo."
            )
            return

        # Procesar como denuncia de texto puro
        await self._create_denuncia_from_batch(message.channel, [message], user_id)

    # -----------------------------------------
    # Procesamiento de batch (múltiples mensajes/archivos)
    # -----------------------------------------

    async def _process_message_batch(self, user_id: int, messages: List[discord.Message]):
        """Procesa un grupo de mensajes (imágenes, audios, etc.) como una sola denuncia."""
        # Si hay archivos adjuntos, activar asistente implícitamente
        canal = messages[0].channel
        await self._create_denuncia_from_batch(canal, messages, user_id)

    async def _create_denuncia_from_batch(self, canal, messages: List[discord.Message], user_id: int):
        """
        Crea una sola denuncia a partir de uno o más mensajes.
        Combina textos/captions y descarga todos los archivos adjuntos.
        """
        textos: List[str] = []
        archivos_descargados: List[Dict[str, Any]] = []
        msg_id_principal = None
        sender_name = None

        for msg in messages:
            # Tomar el primer msg_id como ID principal de la denuncia
            if msg_id_principal is None:
                msg_id_principal = msg.id
                sender_name = str(msg.author)

            # Extraer texto del mensaje
            texto_msg = msg.content.strip()
            if texto_msg:
                # Limpiar menciones
                texto_msg = texto_msg.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()
                if texto_msg:
                    textos.append(texto_msg)

            # Descargar adjuntos
            for attachment in msg.attachments:
                content_type = attachment.content_type or ""
                filename = attachment.filename.lower()

                # Determinar tipo
                is_audio = "audio" in content_type or any(filename.endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"])
                is_image = "image" in content_type or any(filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"])
                is_video = "video" in content_type or any(filename.endswith(ext) for ext in [".mp4", ".webm", ".mov"])

                if is_audio:
                    tipo = "audio"
                elif is_image:
                    tipo = "imagen"
                elif is_video:
                    tipo = "video"
                else:
                    tipo = "documento"

                # Generar nombre seguro para archivo local
                ext = os.path.splitext(attachment.filename)[1] or ".bin"
                safe_name = f"{msg.id}_{attachment.id}_{tipo}{ext}"
                dest_path = os.path.join(UPLOAD_DIR, safe_name)

                # Descargar archivo
                downloaded = await self.download_attachment(attachment, dest_path)
                if downloaded:
                    archivos_descargados.append({
                        "path": dest_path,
                        "tipo": tipo,
                        "mime": content_type or f"{tipo}/{ext.lstrip('.')}",
                        "filename": attachment.filename,
                    })

                    # Si es audio, transcribir
                    if is_audio:
                        await canal.send("🎙️ *Audio detectado. Transcribiendo...*")
                        stt_res = await transcribe_audio(dest_path)
                        if stt_res.get("transcripcion"):
                            textos.append(f"[Transcripción de audio]: {stt_res['transcripcion']}")
                        else:
                            logger.warning(f"[Discord] No se pudo transcribir audio: {stt_res.get('error')}")

        # Determinar tipo de contenido
        tiene_texto = bool(textos)
        tiene_adjuntos = bool(archivos_descargados)

        if tiene_texto and tiene_adjuntos:
            tipo_contenido = TipoContenido.MIXTO
        elif tiene_adjuntos:
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
            "canal_origen": "discord",
            "session_id": hashlib.sha256(str(user_id).encode()).hexdigest()[:16],
            "batch_size": len(messages),
            "total_archivos": len(archivos_descargados),
        }
        if len(archivos_descargados) > 1:
            metadata["archivos_adicionales"] = archivos_descargados[1:]

        # Validaciones de contenido
        clean_text = contenido_raw.lower().strip()
        if not contenido_raw.strip() or contenido_raw == "[Sin texto descriptivo]":
            if not archivos_descargados:
                await canal.send("❌ Mensaje vacío. Por favor, descríbenos los hechos o adjunta tu evidencia para que podamos generar inteligencia útil.")
                return

        # Filtros de relleno solo si no hay adjuntos
        if not archivos_descargados and len(clean_text) < 15:
            await canal.send("ℹ️ *Descripción muy corta.* Por favor proporciona más detalles para generar inteligencia útil (mínimo 15 caracteres) o envía un audio.")
            return

        n_archivos = len(archivos_descargados)
        archivos_msg = f" ({n_archivos} archivos adjuntos)" if n_archivos > 1 else ""
        await canal.send(f"🔍 *Procesando tu reporte{archivos_msg}... Guardando evidencias y analizando con agentes de IA forense...*")

        try:
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.DISCORD,
                    id_externo=str(msg_id_principal),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata=metadata
                )
                denuncia = await service.crear_denuncia(req)
                await service.ejecutar_grafo(denuncia, modo="completo")
                await db.refresh(denuncia)

            # Restablecer estado a IDLE al registrar con éxito
            self.user_states[user_id] = 'idle'

            # Datos de respuesta
            tracking_code = denuncia.tracking_code or "TRJ-PENDIENTE"
            nivel_riesgo_str = denuncia.nivel_riesgo.value.upper() if denuncia.nivel_riesgo else "PENDIENTE"

            reply_msg = (
                f"✅ **Report Successfully Registered**{archivos_msg}\n\n"
                f"🎫 **Tracking code:** `{tracking_code}`\n"
                f"⚖️ **Estimated Risk Level:** **{nivel_riesgo_str}**\n\n"
                f"Your information will be analyzed by forensic AI and delivered to competent authorities for operational intelligence.\n\n"
                f"You can check the analysis status of your report at:\n"
                f"{settings.TRACKING_URL}?code={tracking_code}\n\n"
                f"⚠️ Remember: This is a citizen intelligence system. For formal complaints to the Prosecutor's Office or Police, use the 111 hotline or go to the police station."
            )
            await canal.send(reply_msg)

        except Exception as e:
            logger.error(f"Error processing Discord report: {e}", exc_info=True)
            await canal.send(f"❌ An unexpected error occurred while processing your report: {str(e)}")
    
    async def _send_stats(self, channel):
        """Envía estadísticas del sistema al canal especificado."""
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, func
                from app.models.database import Denuncia
                
                # Consultar estadísticas
                total_denuncias = await db.execute(select(func.count()).select_from(Denuncia))
                total_count = total_denuncias.scalar() or 0
                
                # Por nivel de riesgo
                riesgo_query = await db.execute(
                    select(Denuncia.nivel_riesgo, func.count(Denuncia.id))
                    .group_by(Denuncia.nivel_riesgo)
                )
                riesgo_counts = {str(r[0]): r[1] for r in riesgo_query.all()}
                
                # Por canal
                canal_query = await db.execute(
                    select(Denuncia.canal, func.count(Denuncia.id))
                    .group_by(Denuncia.canal)
                )
                canal_counts = {str(c[0]): c[1] for c in canal_query.all()}
                
                # Hoy
                from datetime import date
                hoy = date.today()
                hoy_query = await db.execute(
                    select(func.count()).select_from(Denuncia).where(
                        func.date(Denuncia.created_at) == hoy
                    )
                )
                hoy_count = hoy_query.scalar() or 0
            
            # Create statistics embed
            stats_embed = discord.Embed(
                title=f"📊 IntelExtorsión Statistics",
                description=f"Data updated at {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                color=BOT_CONFIG["BOT_COLOR"]
            )
            
            stats_embed.add_field(name="📋 Total reports", value=str(total_count), inline=True)
            stats_embed.add_field(name="📅 Reports today", value=str(hoy_count), inline=True)
            stats_embed.add_field(name="🌐 Active servers", value=str(len(self.guilds)), inline=True)
            
            # By risk level
            riesgo_text = "\n".join([f"• {r}: {c}" for r, c in riesgo_counts.items()])
            stats_embed.add_field(name="⚖️ By risk level", value=riesgo_text or "No data", inline=False)
            
            # By channel
            canal_text = "\n".join([f"• {c}: {v}" for c, v in canal_counts.items()])
            stats_embed.add_field(name="📡 By channel", value=canal_text or "No data", inline=False)
            
            stats_embed.set_footer(text="IntelExtorsión - Citizen Intelligence")
            
            await channel.send(embed=stats_embed)
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            await channel.send(f"❌ Error getting statistics: {str(e)}")
