import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

import pytesseract
from PIL import Image

from app.services.file_service import download_from_url

async def extract_text_from_image(image_url: str, idioma: str = "spa") -> Dict[str, Any]:
    try:
        content, mime = await download_from_url(image_url)

        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            img = Image.open(tmp_path)
            texto = pytesseract.image_to_string(img, lang=idioma)

            # Get word-level confidence data
            conf_data = pytesseract.image_to_data(img, lang=idioma, output_type=pytesseract.Output.DICT)
            confidences = [c for c in conf_data["conf"] if c != "-1"]
            avg_conf = sum(int(c) for c in confidences) / len(confidences) / 100.0 if confidences else 0.0

            return {
                "texto_extraido": texto.strip(),
                "confianza": round(avg_conf, 2),
                "idioma": idioma,
                "largo_texto": len(texto.strip()),
                "palabras": len(texto.split()),
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        return {"texto_extraido": "", "confianza": 0.0, "error": str(e), "idioma": idioma}
