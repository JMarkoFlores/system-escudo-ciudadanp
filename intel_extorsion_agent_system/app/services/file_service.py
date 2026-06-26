import hashlib
import uuid
import aiofiles
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from app.config.settings import settings

ALLOWED_EXTENSIONS = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "application/pdf": ".pdf",
    "audio/mpeg": ".mp3", "audio/ogg": ".ogg", "audio/wav": ".wav",
    "video/mp4": ".mp4",
    "text/plain": ".txt",
}

async def save_upload(file: UploadFile, denuncia_id: str) -> Tuple[str, str, int]:
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"Tipo de archivo no permitido: {file.content_type}")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.UPLOAD_MAX_SIZE_MB:
        raise HTTPException(400, f"Archivo excede el límite de {settings.UPLOAD_MAX_SIZE_MB}MB")

    file_hash = hashlib.sha256(content).hexdigest()
    ext = ALLOWED_EXTENSIONS.get(file.content_type, ".bin")
    filename = f"{denuncia_id}_{file_hash[:16]}_{uuid.uuid4().hex[:8]}{ext}"

    upload_path = Path(settings.UPLOAD_DIR) / "evidencias"
    upload_path.mkdir(parents=True, exist_ok=True)
    dest = upload_path / filename

    async with aiofiles.open(str(dest), "wb") as f:
        await f.write(content)

    return str(dest), file_hash, len(content)

async def download_from_url(url: str) -> Tuple[bytes, str]:
    import httpx
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.read()
        mime = resp.headers.get("content-type", "application/octet-stream")
        return content, mime
