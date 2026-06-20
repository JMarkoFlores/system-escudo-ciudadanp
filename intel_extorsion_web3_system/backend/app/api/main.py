"""
Web3 Backend API - FastAPI
Endpoints para integración blockchain, DApp y Agent System
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import hashlib
import httpx

from app.config.settings import settings
from app.services.web3_service import web3_service

app = FastAPI(
    title="IntelExtorsión Web3 Backend API",
    description="API de integración Web3 para custodia blockchain, DID y evidencias",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Schemas
# ==========================================

class HealthResponse(BaseModel):
    status: str
    blockchain_connected: bool
    block_number: int
    backend_address: Optional[str]

class StoreEvidenceRequest(BaseModel):
    did_denunciante: Optional[str] = Field(None, description="DID del denunciante")
    tipo_evidencia: int = Field(..., ge=1, le=5, description="1=texto,2=imagen,3=audio,4=video,5=documento")
    metadata_uri: Optional[str] = Field("", description="URI a metadatos JSON")
    ipfs_cid: Optional[str] = Field(None, description="CID si ya está en IPFS")

class StoreEvidenceResponse(BaseModel):
    success: bool
    evidence_id: Optional[int]
    evidence_hash: str
    tx_hash: str
    block_number: int
    ipfs_cid: str
    timestamp: str

class VerifyEvidenceRequest(BaseModel):
    evidence_id: int

class VerifyEvidenceResponse(BaseModel):
    evidence_id: int
    valid: bool
    mensaje: str
    on_chain_hash: str
    provided_hash: str
    custodian: str
    timestamp: int
    active: bool
    blockchain: str
    block_number_at_verify: int

class CreateCaseRequest(BaseModel):
    did_denunciante: str
    nivel_riesgo: int = Field(..., ge=0, le=3, description="0=BAJO,1=MEDIO,2=ALTO,3=CRITICO")
    resumen: str
    metadata_uri: Optional[str] = ""

class CreateCaseResponse(BaseModel):
    success: bool
    case_id: Optional[int]
    tx_hash: str
    block_number: int

class ResolveDIDResponse(BaseModel):
    did: str
    exists: bool
    document: Optional[Dict[str, Any]]

class CustodyHistoryResponse(BaseModel):
    evidence_id: int
    history: List[Dict[str, Any]]

class LinkEvidenceRequest(BaseModel):
    case_id: int
    evidence_id: int

class SealEvidenceRequest(BaseModel):
    content_hash: str = Field(..., description="SHA-256 hash del contenido a sellar")
    case_id: int = Field(..., description="ID del caso asociado")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SealEvidenceResponse(BaseModel):
    success: bool
    evidence_hash: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    evidence_id: Optional[int] = None
    case_id: Optional[int] = None
    message: Optional[str] = None

# ==========================================
# Endpoints
# ==========================================

@app.get("/health", response_model=HealthResponse)
async def health():
    connected = web3_service.is_connected()
    block = web3_service.get_block_number() if connected else 0
    return HealthResponse(
        status="ok",
        blockchain_connected=connected,
        block_number=block,
        backend_address=web3_service.backend_address
    )

# --------- Evidencias ---------

@app.post("/v1/evidencias", response_model=StoreEvidenceResponse)
async def store_evidence(
    tipo_evidencia: int = Form(...),
    did_denunciante: Optional[str] = Form(None),
    metadata_uri: Optional[str] = Form(""),
    file: UploadFile = File(...)
):
    """
    Registra una evidencia en blockchain:
    1. Recibe archivo
    2. Sube a IPFS (o recibe CID)
    3. Calcula SHA-256
    4. Registra en EvidenceRegistry (Rollux L2)
    """
    content = await file.read()
    
    # Subir a IPFS via Pinata (o servicio configurado)
    ipfs_cid = await _upload_to_ipfs(content, file.filename)
    
    result = web3_service.store_evidence(
        file_bytes=content,
        ipfs_cid=ipfs_cid,
        did_denunciante=did_denunciante or "",
        tipo_evidencia=tipo_evidencia,
        metadata_uri=metadata_uri or ""
    )
    
    return StoreEvidenceResponse(
        success=result["status"] == 1,
        evidence_id=result.get("evidence_id"),
        evidence_hash=result["evidence_hash"],
        tx_hash=result["tx_hash"],
        block_number=result["block_number"],
        ipfs_cid=ipfs_cid,
        timestamp=""
    )

@app.post("/v1/evidencias/seal", response_model=SealEvidenceResponse)
async def seal_evidence(req: SealEvidenceRequest):
    """
    Sella un hash de evidencia en blockchain (usado por agentes autónomos).
    Acepta JSON: content_hash + case_id.
    """
    try:
        result = web3_service.seal_evidence_by_hash(
            evidence_hash=req.content_hash,
            case_id=req.case_id,
            metadata=req.metadata
        )
        return SealEvidenceResponse(
            success=result.get("success", False),
            evidence_hash=result.get("evidence_hash", ""),
            tx_hash=result.get("tx_hash"),
            block_number=result.get("block_number"),
            evidence_id=result.get("evidence_id"),
            case_id=result.get("case_id"),
            message=result.get("message")
        )
    except Exception as e:
        return SealEvidenceResponse(
            success=False,
            evidence_hash=req.content_hash,
            message=f"Error al sellar evidencia: {str(e)}"
        )

@app.post("/v1/evidencias/verify", response_model=VerifyEvidenceResponse)
async def verify_evidence(
    evidence_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Verifica integridad de evidencia comparando hash SHA-256 on-chain."""
    content = await file.read()
    result = web3_service.verify_evidence_integrity(evidence_id, content)
    return VerifyEvidenceResponse(**result)

@app.get("/v1/evidencias/{evidence_id}/custodia", response_model=CustodyHistoryResponse)
async def get_custody_history(evidence_id: int):
    history = web3_service.get_custody_history(evidence_id)
    return CustodyHistoryResponse(evidence_id=evidence_id, history=history)

@app.post("/v1/evidencias/{evidence_id}/transferir")
async def transfer_custody(
    evidence_id: int,
    new_custodian: str = Form(...),
    motivo: str = Form(...)
):
    result = web3_service.transfer_custody(evidence_id, new_custodian, motivo)
    return {"success": result["status"] == 1, **result}

# --------- Casos ---------

@app.post("/v1/casos", response_model=CreateCaseResponse)
async def create_case(req: CreateCaseRequest):
    result = web3_service.create_case(
        did_denunciante=req.did_denunciante,
        nivel_riesgo=req.nivel_riesgo,
        resumen=req.resumen,
        metadata_uri=req.metadata_uri or ""
    )
    return CreateCaseResponse(
        success=result["status"] == 1,
        case_id=result.get("case_id"),
        tx_hash=result["tx_hash"],
        block_number=result["block_number"]
    )

@app.post("/v1/casos/vincular")
async def link_evidence_to_case(req: LinkEvidenceRequest):
    result = web3_service.link_evidence_to_case(req.case_id, req.evidence_id)
    return {"success": result["status"] == 1, **result}

@app.get("/v1/casos/{case_id}")
async def get_case(case_id: int):
    caso = web3_service.get_case(case_id)
    if not caso or caso.get("id") == 0:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return caso

# --------- DID ---------

@app.get("/v1/did/{did}", response_model=ResolveDIDResponse)
async def resolve_did(did: str):
    doc = web3_service.resolve_did(did)
    return ResolveDIDResponse(
        did=did,
        exists=doc is not None,
        document=doc
    )

@app.get("/v1/did/credential/{credential_hash}/verify")
async def verify_credential(credential_hash: str):
    result = web3_service.verify_credential(credential_hash)
    return result

# ==========================================
# Helpers
# ==========================================

async def _upload_to_ipfs(content: bytes, filename: str) -> str:
    """Sube archivo a IPFS via Pinata."""
    if not settings.IPFS_JWT:
        # Fallback: calcular hash como CID simulado para desarrollo
        return f"QmDev{hashlib.sha256(content).hexdigest()[:16]}"
    
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {settings.IPFS_JWT}"}
    
    async with httpx.AsyncClient() as client:
        files = {"file": (filename, content)}
        response = await client.post(url, headers=headers, files=files, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        return data["IpfsHash"]
