import asyncio
import logging
import httpx
from typing import Optional, List, Dict, Any

from app.config.settings import settings
from app.schemas.agent_schemas import DenunciaIngestaRequest, CanalEntrada, TipoContenido
from app.services.agent_service import AgentExecutionService
from app.models.db_session import AsyncSessionLocal
from app.services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.is_running = False
        self._task = None
        self.user_states = {}  # chat_id -> 'idle' | 'waiting_for_denuncia'

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
        except Exception as e:
            logger.debug(f"Error al obtener actualizaciones de Telegram: {e}")
        return []

    async def process_update(self, update: dict):
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
                "🛡️ *Bienvenido al bot oficial de IntelExtorsión*\n\n"
                "Puedes registrar una denuncia de extorsión de forma 100% confidencial.\n\n"
                "✍️ *¿Cómo denunciar?*\n"
                "• Escribe detalladamente tu denuncia en un mensaje de texto.\n"
                "• O envía una nota de voz explicando la situación (la transcribiremos automáticamente).\n\n"
                "🔍 *¿Cómo consultar?*\n"
                "• Envía el código en formato `TRJ-XXXX` para consultar su estado en tiempo real.\n\n"
                "Tu reporte será analizado de inmediato por nuestros agentes de inteligencia artificial y recibirás un código de seguimiento."
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
                    "El asistente de ingesta ha sido desactivado y tu sesión se encuentra limpia. ¿Qué deseas hacer hoy? Puedes volver a iniciar escribiendo 'denunciar'."
                )
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
                                    f"http://localhost:3000/tracking?code={tracking_code}"
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
                        "👋 *¡Hola!* Estoy aquí para ayudarte a registrar denuncias de extorsión de forma segura y confidencial.\n\n"
                        "Para iniciar una denuncia, por favor escribe *denunciar* o presiona el comando /denunciar."
                    )
                    return

                # 3. Activar asistente de denuncia
                intencion_nueva = ["quiero denunciar", "hacer una denuncia", "hacer otra denuncia", "otra denuncia", "nueva denuncia", "registrar otra", "denunciar", "/denunciar"]
                if any(i in clean_text for i in intencion_nueva):
                    self.user_states[chat_id] = 'waiting_for_denuncia'
                    await self.send_message(
                        chat_id,
                        "📝 *Asistente de Ingesta Activado.*\n\n"
                        "Por favor, describa detalladamente lo sucedido **en su siguiente mensaje** (puede incluir números de teléfono extorsionadores, cuentas bancarias, montos exigidos, etc.) o envíe una nota de voz.\n\n"
                        "⚠️ *Asegúrese de consolidar toda la información en un único mensaje.* Si desea abortar el proceso, escriba *cancelar*."
                    )
                    return

                # Fallback en IDLE
                await self.send_message(
                    chat_id,
                    "🤖 *Hola. Para poder registrar una denuncia formal de extorsión, primero debemos activar el asistente de ingesta.*\n\n"
                    "Por favor, escribe la palabra **denunciar** para comenzar."
                )
                return
            else:
                # Si envían audios/archivos en IDLE, pedir que activen el asistente
                await self.send_message(
                    chat_id,
                    "🤖 *Detecté un archivo, pero el asistente de ingesta no está activo.*\n\n"
                    "Por favor, escribe la palabra **denunciar** primero para poder registrar tu caso correctamente."
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
                    "📝 *Asistente Esperando Detalles.*\n\n"
                    "⚠️ No detectamos detalles del hecho en tu mensaje.\n\n"
                    "Por favor, redacta **en un único mensaje consolidado** todo lo sucedido cuando estés listo (incluyendo teléfonos, cuentas bancarias, amenazas), o envíanos una nota de voz explicativa.\n\n"
                    "*Si deseas cancelar el reporte actual, escribe **cancelar**.*"
                )
                return

            # Evitar registrar textos demasiado cortos que no aporten detalles
            if len(clean_text) < 15 and not voice_or_audio:
                await self.send_message(
                    chat_id,
                    "ℹ️ *Tu mensaje es muy corto.* Para poder iniciar una denuncia válida y que los agentes de IA puedan analizarla, por favor escribe una descripción más detallada de los hechos o envía una nota de voz."
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
            await self.send_message(chat_id, "❌ Por favor, escribe un mensaje o envía una nota de voz explicativa para registrar la denuncia.")
            return

        await self.send_message(chat_id, "🔍 _Registrando denuncia y ejecutando análisis de inteligencia..._")

        try:
            # Crear denuncia y ejecutar grafo
            async with AsyncSessionLocal() as db:
                service = AgentExecutionService(db)
                req = DenunciaIngestaRequest(
                    canal=CanalEntrada.TELEGRAM,
                    id_externo=str(message["message_id"]),
                    tipo_contenido=tipo_contenido,
                    contenido_raw=contenido_raw,
                    url_archivo=url_archivo,
                    metadata={
                        "telegram_user": message.get("from", {}),
                        "chat_id": chat_id
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
                f"✅ *Denuncia Registrada Exitosamente*\n\n"
                f"🎫 *Código de seguimiento:* `{tracking_code}`\n"
                f"⚖️ *Nivel de Riesgo Inicial:* *{nivel_riesgo_str}*\n\n"
                f"Puedes consultar el análisis completo de los agentes de IA y blockchain en el siguiente enlace:\n"
                f"http://localhost:3000/tracking?code={tracking_code}"
            )
            await self.send_message(chat_id, msg_reply)
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

    async def send_message(self, chat_id: int, text: str):
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            await self.http_client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error al enviar mensaje a Telegram: {e}")
