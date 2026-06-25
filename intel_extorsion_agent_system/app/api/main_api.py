"""
API REST - FastAPI
Endpoints del Subsistema de Agentes Autónomos
"""
import logging
from typing import Optional, List
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File, Request
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

bot_client = None
discord_bot_client = None
whatsapp_bot_client = None

@app.on_event("startup")
async def startup():
    print("FastAPI startup: inicializando base de datos...", flush=True)
    await init_db()
    
    # Telegram Bot
    global bot_client
    if settings.TELEGRAM_BOT_TOKEN:
        print(f"FastAPI startup: detectado TELEGRAM_BOT_TOKEN, iniciando bot...", flush=True)
        from app.channels.telegram_bot import TelegramBot
        bot_client = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
        bot_client.start_background()
    else:
        print("FastAPI startup: NO se detectó TELEGRAM_BOT_TOKEN en settings", flush=True)
        
    # Discord Bot
    global discord_bot_client
    if settings.DISCORD_BOT_TOKEN:
        print(f"FastAPI startup: detectado DISCORD_BOT_TOKEN, iniciando bot de Discord...", flush=True)
        import asyncio
        from app.channels.discord_bot import DiscordBot
        discord_bot_client = DiscordBot(settings.DISCORD_BOT_TOKEN)
        asyncio.create_task(discord_bot_client.start(settings.DISCORD_BOT_TOKEN))
    else:
        print("FastAPI startup: NO se detectó DISCORD_BOT_TOKEN en settings", flush=True)
        
    # WhatsApp Bot
    global whatsapp_bot_client
    if settings.WHATSAPP_API_TOKEN:
        print(f"FastAPI startup: detectado WHATSAPP_API_TOKEN, iniciando bot de WhatsApp...", flush=True)
        from app.channels.whatsapp_bot import WhatsAppBot
        whatsapp_bot_client = WhatsAppBot(settings.WHATSAPP_API_TOKEN)
    else:
        print("FastAPI startup: NO se detectó WHATSAPP_API_TOKEN en settings", flush=True)

@app.on_event("shutdown")
async def shutdown():
    global bot_client
    if bot_client:
        await bot_client.stop()
        
    global discord_bot_client
    if discord_bot_client:
        print("FastAPI shutdown: deteniendo bot de Discord...", flush=True)
        await discord_bot_client.close()
        
    global whatsapp_bot_client
    if whatsapp_bot_client:
        print("FastAPI shutdown: deteniendo bot de WhatsApp...", flush=True)
        await whatsapp_bot_client.close()

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

# Webhook de WhatsApp (Whapi.cloud)
@app.post("/v1/channels/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Recibe actualizaciones de mensajes de Whapi.cloud y las procesa en background.
    """
    global whatsapp_bot_client
    if not whatsapp_bot_client:
        raise HTTPException(status_code=503, detail="Canal de WhatsApp no inicializado")
        
    try:
        payload = await request.json()
        logger.info(f"Webhook de WhatsApp recibido: {payload}")
        
        # Procesar de forma asíncrona en segundo plano para responder de inmediato
        background_tasks.add_task(whatsapp_bot_client.process_webhook, payload)
        
        return {"status": "accepted"}
    except Exception as e:
        logger.error(f"Error procesando webhook de WhatsApp: {e}")
        raise HTTPException(status_code=400, detail=str(e))

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
        tipo_contenido=denuncia.tipo_contenido,
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

@app.get("/v1/denuncias")
async def listar_denuncias(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    canal: Optional[str] = Query(None, description="Filtrar por canal"),
    did_denunciante: Optional[str] = Query(None, description="Filtrar por DID del denunciante"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista denuncias registradas en el sistema, ordenadas por fecha descendente.
    """
    query = select(Denuncia).order_by(desc(Denuncia.created_at))
    if estado:
        query = query.where(Denuncia.estado == estado)
    if canal:
        query = query.where(Denuncia.canal == canal)
    if did_denunciante:
        query = query.where(Denuncia.did_denunciante == did_denunciante)
    
    result = await db.execute(query.limit(limit).offset(offset))
    rows = result.scalars().all()
    
    def get_estado_val(est):
        if est is None:
            return "creado"
        return est.value if hasattr(est, "value") else str(est)
    
    return [
        DenunciaResponse(
            id=d.id,
            canal=d.canal,
            estado=get_estado_val(d.estado),
            tipo_contenido=d.tipo_contenido,
            created_at=d.created_at,
            resultados=[],
            tracking_code=d.tracking_code,
            nivel_riesgo=d.nivel_riesgo,
            seal_tx_hash=d.seal_tx_hash,
            seal_block=d.seal_block,
            seal_status=d.seal_status
        )
        for d in rows
    ]

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
        tipo_contenido=denuncia.tipo_contenido,
        created_at=denuncia.created_at,
        resultados=resultados
    )

@app.get("/v1/denuncias/tracking/{tracking_code}")
async def obtener_denuncia_por_tracking(
    tracking_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca una denuncia por su código de seguimiento TRJ-XXXX.
    """
    from sqlalchemy import select
    result = await db.execute(
        select(Denuncia).where(Denuncia.tracking_code == tracking_code)
    )
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Código de seguimiento no encontrado")

    # Cargar resultados de agentes
    res_result = await db.execute(
        select(ResultadoAgente)
        .where(ResultadoAgente.denuncia_id == denuncia.id)
        .order_by(ResultadoAgente.created_at)
    )
    resultados = [r.resultado_json for r in res_result.scalars().all()]

    return DenunciaResponse(
        id=denuncia.id,
        canal=denuncia.canal,
        estado=denuncia.estado.value,
        tipo_contenido=denuncia.tipo_contenido,
        created_at=denuncia.created_at,
        resultados=resultados,
        tracking_code=denuncia.tracking_code,
        nivel_riesgo=denuncia.nivel_riesgo.value if denuncia.nivel_riesgo else None,
        seal_tx_hash=denuncia.seal_tx_hash,
        seal_block=denuncia.seal_block,
        seal_status=denuncia.seal_status
    )

@app.post("/v1/denuncias/{denuncia_id}/adjuntar", status_code=201)
async def adjuntar_archivo(
    denuncia_id: uuid.UUID,
    file: UploadFile = File(...),
    tipo_evidencia: Optional[str] = Query(None, description="Tipo de evidencia (imagen/audio/documento)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Adjunta un archivo de evidencia a una denuncia existente.
    Calcula SHA-256, almacena en disco y actualiza el registro.
    """
    from app.services.file_service import save_upload

    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")

    filepath, file_hash, file_size = await save_upload(file, str(denuncia_id))

    denuncia.url_archivo = filepath
    denuncia.hash_archivo = file_hash
    if tipo_evidencia:
        denuncia.tipo_contenido = tipo_evidencia
    denuncia.metadata_json = {
        **(denuncia.metadata_json or {}),
        "file_size": file_size,
        "file_mime": file.content_type,
        "file_name": file.filename,
    }
    await db.commit()

    return {
        "status": "ok",
        "denuncia_id": str(denuncia_id),
        "file_hash": file_hash,
        "file_path": filepath,
        "file_size": file_size,
        "mime_type": file.content_type,
    }

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

@app.get("/v1/denuncias/{denuncia_id}/archivo")
async def obtener_archivo_denuncia(
    denuncia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el archivo de evidencia adjunto a la denuncia.
    """
    from fastapi.responses import FileResponse
    import os

    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia or not denuncia.url_archivo:
        raise HTTPException(status_code=404, detail="Archivo de evidencia no encontrado o no registrado")
    
    if not os.path.exists(denuncia.url_archivo):
        raise HTTPException(status_code=404, detail="El archivo no existe físicamente en el servidor")
    
    # Determinar el content type a partir de los metadatos o dejar que FastAPI lo deduzca
    mime_type = None
    if denuncia.metadata_json and "file_mime" in denuncia.metadata_json:
        mime_type = denuncia.metadata_json["file_mime"]
        
    return FileResponse(denuncia.url_archivo, media_type=mime_type)

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
# Alertas Globales
# ==========================================

@app.get("/v1/alertas")
async def listar_alertas(
    nivel: Optional[str] = Query(None, description="Filtrar por nivel de riesgo"),
    leida: Optional[bool] = Query(None, description="Filtrar por estado de lectura"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas las alertas generadas por el sistema.
    """
    query = select(Alerta).order_by(desc(Alerta.created_at))
    if nivel:
        query = query.where(Alerta.nivel == nivel)
    if leida is not None:
        query = query.where(Alerta.leida == leida)
    
    result = await db.execute(query.limit(limit))
    rows = result.scalars().all()
    
    return [
        {
            "id": str(a.id),
            "denuncia_id": str(a.denuncia_id),
            "nivel": a.nivel.value,
            "titulo": a.titulo,
            "descripcion": a.descripcion,
            "recomendacion": a.recomendacion,
            "leida": a.leida,
            "atendida": a.atendida,
            "created_at": a.created_at.isoformat()
        }
        for a in rows
    ]

# ==========================================
# Dashboard - Métricas
# ==========================================

@app.get("/v1/dashboard/metricas")
async def obtener_metricas(db: AsyncSession = Depends(get_db)):
    """
    Devuelve métricas agregadas para el dashboard policial.
    """
    from sqlalchemy import func, cast, Date
    from datetime import datetime, timedelta, timezone

    # Total denuncias
    total_result = await db.execute(select(func.count(Denuncia.id)))
    total_denuncias = total_result.scalar() or 0

    # Denuncias hoy
    hoy = datetime.now(timezone.utc).date()
    hoy_result = await db.execute(
        select(func.count(Denuncia.id)).where(
            cast(Denuncia.created_at, Date) == hoy
        )
    )
    denuncias_hoy = hoy_result.scalar() or 0

    # Alertas críticas (alto + critico)
    alertas_result = await db.execute(
        select(func.count(Alerta.id)).where(Alerta.nivel.in_(["alto", "critico"]))
    )
    alertas_criticas = alertas_result.scalar() or 0

    # Casos resueltos / archivados
    resueltos_result = await db.execute(
        select(func.count(Denuncia.id)).where(Denuncia.estado == "archivado")
    )
    casos_resueltos = resueltos_result.scalar() or 0

    # Evidencias registradas = denuncias con url_archivo no nulo
    evidencias_result = await db.execute(
        select(func.count(Denuncia.id)).where(Denuncia.url_archivo.isnot(None))
    )
    evidencias_registradas = evidencias_result.scalar() or 0

    return {
        "total_denuncias": total_denuncias,
        "denuncias_hoy": denuncias_hoy,
        "alertas_criticas": alertas_criticas,
        "casos_resueltos": casos_resueltos,
        "tiempo_promedio_respuesta_min": 12,  # Placeholder hasta tener métricas reales
        "evidencias_registradas": evidencias_registradas,
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
# ==========================================
# SSE Push para Dashboard
# ==========================================

from fastapi.responses import JSONResponse

@app.post("/v1/dashboard/push")
async def dashboard_push(payload: dict):
    """
    Endpoint interno para que los agentes envíen push al dashboard.
    Los clientes SSE pueden suscribirse a /v1/dashboard/stream.
    """
    # En producción: reenviar via SSE o WebSocket a clientes conectados
    return JSONResponse({"status": "received", "tipo": payload.get("tipo")})


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
