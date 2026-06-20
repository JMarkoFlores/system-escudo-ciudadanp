import httpx
import hashlib
import json
from typing import Optional
from app.config.settings import settings

WEB3_BACKEND_URL = settings.WEB3_BACKEND_URL

async def seal_evidence(
    content_hash: str,
    case_id: int
) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{WEB3_BACKEND_URL}/v1/evidencias/seal",
                json={
                    "content_hash": content_hash,
                    "case_id": case_id
                }
            )
            if response.status_code == 200:
                return response.json()
            return {
                "success": False,
                "tx_hash": None,
                "block_number": None,
                "error": f"Web3 backend responded {response.status_code}"
            }
        except httpx.RequestError as e:
            return {
                "success": False,
                "tx_hash": None,
                "block_number": None,
                "error": str(e)
            }

async def verify_evidence(content_hash: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{WEB3_BACKEND_URL}/v1/evidencias/{content_hash}/verificar"
            )
            if response.status_code == 200:
                return response.json()
            return {"exists": False}
        except httpx.RequestError:
            return {"exists": False}

def compute_content_hash(text: str, metadata: Optional[dict] = None) -> str:
    content = text or ""
    if metadata:
        content += json.dumps(metadata, sort_keys=True)
    return "0x" + hashlib.sha256(content.encode()).hexdigest()
