import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from app.services.file_service import download_from_url
from app.config.settings import settings

async def transcribe_audio(audio_url: str, idioma: str = "es") -> Dict[str, Any]:
    if not settings.GROQ_API_KEY:
        return {
            "transcripcion": "",
            "error": "GROQ_API_KEY no configurada",
            "idioma": idioma,
        }

    try:
        from groq import Groq

        content, mime = await download_from_url(audio_url)

        ext = ".ogg"
        if "mpeg" in mime or "mp3" in mime:
            ext = ".mp3"
        elif "wav" in mime:
            ext = ".wav"
        elif "ogg" in mime:
            ext = ".ogg"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            with open(tmp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file,
                    language=idioma,
                    response_format="verbose_json",
                )

            return {
                "transcripcion": transcription.text.strip(),
                "idioma": transcription.language or idioma,
                "duracion_segundos": getattr(transcription, "duration", 0),
                "confianza": getattr(transcription, "segments", [{}])[0].get("confidence", 0.0) if getattr(transcription, "segments", None) else 0.0,
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        return {"transcripcion": "", "error": str(e), "idioma": idioma}
