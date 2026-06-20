"""
API REST - FastAPI
Endpoints del Subsistema de Agentes Autónomos
"""
from typing import Optional, List
import uuid

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.config.settings import settings
from app.schemas.agent_schemas import (
    DenunciaIngestaRequest,
    ProcesarDenunciaRequest,
    DenunciaResponse,
    EjecucionGrafoResponse,
    HealthCheckResponse
)
from app.models.db_session import get_db, init_db
from app.models.database import Denuncia, ResultadoAgente, Alerta
from app.services.agent_service import AgentExecutionService
from app.memory.hybrid_memory import memory_system

app = FastAPI(
    title="IntelExtorsión - Agent System API",
    description="Subsistema de Agentes Autónomos para análisis de denuncias de extorsión",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Health & Startup
# ==========================================

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(
        status="ok",
        version="1.0.0",
        componentes={
            "api": "ok",
            "postgres": "ok",
            "qdrant": "ok",
            "groq": "ok",
            "langgraph": "ok"
        }
    )

# ==========================================
# Denuncias - Ingesta y Procesamiento
# ==========================================

@app.post("/v1/denuncias", response_model=DenunciaResponse, status_code=201)
async def crear_denuncia(
    req: DenunciaIngestaRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe una nueva denuncia, la persiste y ejecuta el grafo de agentes en background.
    """
    service = AgentExecutionService(db)
    denuncia = await service.crear_denuncia(req)
    
    # Ejecutar grafo asíncrono en background
    background_tasks.add_task(
        _run_grafo_background,
        denuncia_id=denuncia.id,
        modo="completo",
        agentes=None
    )
    
    return DenunciaResponse(
        id=denuncia.id,
        canal=denuncia.canal,
        estado=denuncia.estado.value,
        tipo_contenido=denuncia.tipo_contenido.value,
        created_at=denuncia.created_at,
        resultados=[]
    )

@app.post("/v1/denuncias/{denuncia_id}/procesar", response_model=EjecucionGrafoResponse)
async def procesar_denuncia(
    denuncia_id: uuid.UUID,
    req: Optional[ProcesarDenunciaRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecuta manualmente (síncrono) el grafo de agentes sobre una denuncia existente.
    Útil para re-procesamiento o ejecución selectiva.
    """
    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")
    
    service = AgentExecutionService(db)
    modo = req.modo if req else "completo"
    agentes = req.agentes if req else None
    
    response = await service.ejecutar_grafo(denuncia, modo=modo, agentes_selectivos=agentes)
    return response

# ==========================================
# Consultas
# ==========================================

@app.get("/v1/denuncias/{denuncia_id}", response_model=DenunciaResponse)
async def obtener_denuncia(
    denuncia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")
    
    # Cargar resultados de agentes
    res_result = await db.execute(
        select(ResultadoAgente)
        .where(ResultadoAgente.denuncia_id == denuncia_id)
        .order_by(ResultadoAgente.created_at)
    )
    resultados = [r.resultado_json for r in res_result.scalars().all()]
    
    return DenunciaResponse(
        id=denuncia.id,
        canal=denuncia.canal,
        estado=denuncia.estado.value,
        tipo_contenido=denuncia.tipo_contenido.value,
        created_at=denuncia.created_at,
        resultados=resultados
    )

@app.get("/v1/denuncias/{denuncia_id}/resultados")
async def obtener_resultados_agentes(
    denuncia_id: uuid.UUID,
    agente: Optional[str] = Query(None, description="Filtrar por nombre de agente"),
    db: AsyncSession = Depends(get_db)
):
    query = select(ResultadoAgente).where(ResultadoAgente.denuncia_id == denuncia_id)
    if agente:
        query = query.where(ResultadoAgente.agente == agente)
    query = query.order_by(desc(ResultadoAgente.created_at))
    
    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "denuncia_id": str(denuncia_id),
        "total": len(rows),
        "resultados": [
            {
                "agente": r.agente,
                "exitoso": r.exitoso,
                "resultado": r.resultado_json,
                "created_at": r.created_at.isoformat()
            }
            for r in rows
        ]
    }

@app.get("/v1/denuncias/{denuncia_id}/alertas")
async def obtener_alertas(
    denuncia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Alerta).where(Alerta.denuncia_id == denuncia_id).order_by(desc(Alerta.created_at))
    )
    rows = result.scalars().all()
    return {
        "denuncia_id": str(denuncia_id),
        "alertas": [
            {
                "id": str(a.id),
                "nivel": a.nivel.value,
                "titulo": a.titulo,
                "descripcion": a.descripcion,
                "leida": a.leida,
                "created_at": a.created_at.isoformat()
            }
            for a in rows
        ]
    }

# ==========================================
# Búsqueda Semántica (Qdrant)
# ==========================================

@app.get("/v1/busqueda/semantica")
async def busqueda_semantica(
    q: str = Query(..., min_length=3, description="Consulta en lenguaje natural"),
    limit: int = Query(5, ge=1, le=20),
    excluir_denuncia_id: Optional[uuid.UUID] = None
):
    """
    Busca denuncias similares usando embeddings vectoriales (Qdrant).
    """
    results = await memory_system.search_similar_cases(
        query=q,
        denuncia_id_excluir=str(excluir_denuncia_id) if excluir_denuncia_id else None,
        limit=limit
    )
    return {"query": q, "resultados": results}

# ==========================================
# Background Task Wrapper
# ==========================================

async def _run_grafo_background(denuncia_id: uuid.UUID, modo: str, agentes: Optional[List[str]]):
    """Wrapper para ejecución en background tasks de FastAPI"""
    from app.models.db_session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        service = AgentExecutionService(db)
        result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
        denuncia = result.scalar_one_or_none()
        if denuncia:
            await service.ejecutar_grafo(denuncia, modo=modo, agentes_selectivos=agentes)
