import hashlib
import uuid
import io
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


def _strip_image_metadata(content: bytes, mime_type: str) -> bytes:
    """
    Elimina metadatos EXIF/ICC/XMP de imágenes para cumplir RF-06.
    Preserva la integridad visual; solo elimina metadata que expose
    información del dispositivo, GPS, serial, etc.
    """
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(content))

        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)

        buf = io.BytesIO()
        fmt_map = {
            "image/jpeg": ("JPEG", {"quality": 95, "optimize": True}),
            "image/png": ("PNG", {"optimize": True}),
            "image/webp": ("WEBP", {"quality": 95}),
        }
        fmt, save_kwargs = fmt_map.get(mime_type, ("PNG", {}))
        clean_img.save(buf, format=fmt, **save_kwargs)
        return buf.getvalue()
    except Exception:
        return content


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def save_upload(file: UploadFile, denuncia_id: str) -> Tuple[str, str, int]:
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"Tipo de archivo no permitido: {file.content_type}")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.UPLOAD_MAX_SIZE_MB:
        raise HTTPException(400, f"Archivo excede el límite de {settings.UPLOAD_MAX_SIZE_MB}MB")

    if file.content_type.startswith("image/"):
        content = _strip_image_metadata(content, file.content_type)

    file_hash = _compute_hash(content)
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
    import aiofiles
    # Soporte para rutas de archivo locales
    if url.startswith("/") or url.startswith("C:") or url.startswith("D:") or url.startswith("file://"):
        file_path = url.replace("file://", "")
        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        ext = Path(file_path).suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".webp": "image/webp", ".pdf": "application/pdf",
                    ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav",
                    ".mp4": "video/mp4", ".txt": "text/plain"}
        mime = mime_map.get(ext, "application/octet-stream")
        if mime.startswith("image/"):
            content = _strip_image_metadata(content, mime)
        return content, mime
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content = resp.read()
        mime = resp.headers.get("content-type", "application/octet-stream")
        if mime.startswith("image/"):
            content = _strip_image_metadata(content, mime)
        return content, mime
