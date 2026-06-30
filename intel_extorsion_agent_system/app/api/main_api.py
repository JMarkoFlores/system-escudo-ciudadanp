"""
API REST - FastAPI
Endpoints del Subsistema de Agentes Autónomos
"""
import logging
from typing import Optional, List
import uuid
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File, Request, Body
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
from app.models.db_session import get_db, init_db, AsyncSessionLocal
from app.models.database import Denuncia, ResultadoAgente, Alerta, Cluster, EstadoDenuncia, NivelRiesgo
from app.services.agent_service import AgentExecutionService
from app.memory.hybrid_memory import memory_system
from app.api.clusters_router import router as clusters_router
from app.api.heatmap_router import router as heatmap_router
from app.api.auth_router import router as auth_router, require_user

app = FastAPI(
    title="IntelExtorsión - Agent System API",
    description="Subsistema de Agentes Autónomos para análisis de denuncias de extorsión",
    version="1.0.0"
)

app.include_router(clusters_router)
app.include_router(heatmap_router)
app.include_router(auth_router)

# CORS: configurable vía variable de entorno; por defecto permite orígenes de desarrollo
import os
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:5173").split(",")
if os.getenv("CORS_ALLOW_ALL", "").lower() in ("true", "1"):
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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

    # Crear usuarios por defecto para el dashboard policial
    try:
        async with AsyncSessionLocal() as db:
            from app.services.auth_service import seed_default_users
            await seed_default_users(db)
            print("FastAPI startup: usuarios por defecto verificados", flush=True)
    except Exception as e:
        print(f"FastAPI startup: error seeding usuarios: {e}", flush=True)

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

        async def _start_discord_bot():
            global discord_bot_client
            try:
                discord_bot_client = DiscordBot(settings.DISCORD_BOT_TOKEN)
                await discord_bot_client.start(settings.DISCORD_BOT_TOKEN)
            except Exception as e:
                print(f"[Discord Bot] FATAL: {e}", flush=True)
                import logging
                logging.getLogger(__name__).error(f"Discord bot failed to start: {e}", exc_info=True)

        asyncio.create_task(_start_discord_bot())
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

    try:
        response = await service.ejecutar_grafo(denuncia, modo=modo, agentes_selectivos=agentes)
        return response
    except Exception as e:
        logger.exception(f"Error ejecutando grafo para denuncia {denuncia_id}: {e}")
        # Actualizar estado a error para que el ciudadano no vea 'en_analisis' congelado
        denuncia.estado = EstadoDenuncia.error_procesamiento
        await db.commit()
        raise HTTPException(status_code=503, detail=f"El motor de agentes no pudo procesar la denuncia: {str(e)}")

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
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user)
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
            nivel_riesgo=d.nivel_riesgo.value if d.nivel_riesgo else None,
            seal_tx_hash=d.seal_tx_hash,
            seal_block=d.seal_block,
            seal_status=d.seal_status,
            url_archivo=d.url_archivo,
            contenido_raw=d.contenido_raw,
            hash_archivo=d.hash_archivo,
            metadata_json=d.metadata_json,
            zona_detectada=d.zona_detectada,
            did_denunciante=d.did_denunciante,
        )
        for d in rows
    ]

@app.get("/v1/denuncias/{denuncia_id}", response_model=DenunciaResponse)
async def obtener_denuncia(
    denuncia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user)
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
    resultados = []
    for r in res_result.scalars().all():
        res_dict = dict(r.resultado_json) if r.resultado_json else {}
        res_dict["agente"] = r.agente
        resultados.append(res_dict)
    
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
        seal_status=denuncia.seal_status,
        url_archivo=denuncia.url_archivo,
        contenido_raw=denuncia.contenido_raw,
        hash_archivo=denuncia.hash_archivo,
        metadata_json=denuncia.metadata_json,
        zona_detectada=denuncia.zona_detectada,
        did_denunciante=denuncia.did_denunciante,
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
    resultados = []
    for r in res_result.scalars().all():
        res_dict = dict(r.resultado_json) if r.resultado_json else {}
        res_dict["agente"] = r.agente
        resultados.append(res_dict)

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
        seal_status=denuncia.seal_status,
        url_archivo=denuncia.url_archivo,
        contenido_raw=denuncia.contenido_raw,
        hash_archivo=denuncia.hash_archivo,
        metadata_json=denuncia.metadata_json,
        zona_detectada=denuncia.zona_detectada,
        did_denunciante=denuncia.did_denunciante,
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
    Si es el primer archivo, se almacena en url_archivo (principal).
    Los siguientes se guardan en metadata_json['archivos_adicionales'].
    Calcula SHA-256, almacena en disco y actualiza el registro.
    """
    from app.services.file_service import save_upload

    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")

    filepath, file_hash, file_size = await save_upload(file, str(denuncia_id))

    file_entry = {
        "path": filepath,
        "filename": file.filename,
        "tipo": tipo_evidencia or denuncia.tipo_contenido or "documento",
        "mime": file.content_type,
        "sha256": file_hash,
        "file_size": file_size,
    }

    if not denuncia.url_archivo:
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
    else:
        meta = denuncia.metadata_json or {}
        adicionales = meta.get("archivos_adicionales", [])
        adicionales.append(file_entry)
        meta["archivos_adicionales"] = adicionales
        denuncia.metadata_json = meta

    await db.commit()

    return {
        "status": "ok",
        "denuncia_id": str(denuncia_id),
        "file_hash": file_hash,
        "file_path": filepath,
        "file_size": file_size,
        "mime_type": file.content_type,
        "es_principal": denuncia.url_archivo == filepath,
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
    index: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el archivo de evidencia adjunto a la denuncia.
    index=0 -> archivo principal (url_archivo).
    index>0 -> archivo adicional desde metadata_json['archivos_adicionales'][index-1].
    """
    from fastapi.responses import FileResponse
    import os

    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")

    file_path = None
    mime_type = None

    if index == 0:
        file_path = denuncia.url_archivo
    else:
        adicionales = (denuncia.metadata_json or {}).get("archivos_adicionales", [])
        if index - 1 >= len(adicionales):
            raise HTTPException(status_code=404, detail="Índice de archivo adicional fuera de rango")
        file_path = adicionales[index - 1].get("path")
        mime_type = adicionales[index - 1].get("mime")

    if not file_path:
        raise HTTPException(status_code=404, detail="Archivo de evidencia no encontrado o no registrado")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="El archivo no existe físicamente en el servidor")

    # Determinar el content type a partir de los metadatos o dejar que FastAPI lo deduzca
    if mime_type is None and denuncia.metadata_json and "file_mime" in denuncia.metadata_json:
        mime_type = denuncia.metadata_json["file_mime"]

    return FileResponse(file_path, media_type=mime_type)

@app.get("/v1/denuncias/{denuncia_id}/archivos")
async def listar_archivos_denuncia(
    denuncia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los archivos de evidencia adjuntos a la denuncia
    (archivo principal + archivos adicionales del batch).
    """
    result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denuncia no encontrada")

    archivos = []

    # Archivo principal
    if denuncia.url_archivo:
        import os
        archivos.append({
            "index": 0,
            "path": denuncia.url_archivo,
            "filename": os.path.basename(denuncia.url_archivo),
            "tipo": denuncia.tipo_contenido,
            "principal": True,
            "existe": os.path.exists(denuncia.url_archivo),
        })

    # Archivos adicionales desde metadata
    adicionales = (denuncia.metadata_json or {}).get("archivos_adicionales", [])
    for i, adj in enumerate(adicionales, start=1):
        archivos.append({
            "index": i,
            "path": adj.get("path"),
            "filename": adj.get("filename") or os.path.basename(adj.get("path", "")),
            "tipo": adj.get("tipo", "documento"),
            "mime": adj.get("mime"),
            "principal": False,
            "existe": os.path.exists(adj.get("path", "")) if adj.get("path") else False,
        })

    return {
        "denuncia_id": str(denuncia_id),
        "total_archivos": len(archivos),
        "archivos": archivos,
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
                "recomendacion": a.recomendacion,
                "leida": a.leida,
                "atendida": a.atendida,
                "metadata_json": a.metadata_json,
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
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user)
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
            "metadata_json": a.metadata_json,
            "created_at": a.created_at.isoformat()
        }
        for a in rows
    ]

@app.patch("/v1/alertas/{alerta_id}")
async def actualizar_alerta(
    alerta_id: uuid.UUID,
    leida: Optional[bool] = None,
    atendida: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user)
):
    """
    Actualiza el estado de lectura o atención de una alerta.
    Body opcional:
      - mensaje_resolucion: str  (mensaje del oficial sobre lo descubierto)
      - estado_denuncia: str     (nuevo estado de la denuncia relacionada, ej: "archivado")
    """
    result = await db.execute(select(Alerta).where(Alerta.id == alerta_id))
    alerta = result.scalar_one_or_none()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    if leida is not None:
        alerta.leida = leida
    if atendida is not None:
        alerta.atendida = atendida

    # Procesar body JSON
    mensaje_resolucion = data.get("mensaje_resolucion")
    estado_denuncia = data.get("estado_denuncia")

    if mensaje_resolucion is not None:
        meta = alerta.metadata_json or {}
        meta["mensaje_resolucion"] = mensaje_resolucion
        meta["atendida_por"] = "oficial"
        meta["atendida_en"] = datetime.now(timezone.utc).isoformat()
        alerta.metadata_json = meta

    await db.commit()
    await db.refresh(alerta)

    # Actualizar estado de la denuncia relacionada si se solicitó
    if estado_denuncia:
        den_result = await db.execute(select(Denuncia).where(Denuncia.id == alerta.denuncia_id))
        denuncia = den_result.scalar_one_or_none()
        if denuncia:
            try:
                denuncia.estado = EstadoDenuncia(estado_denuncia)
            except ValueError:
                pass  # estado inválido, ignorar silenciosamente
            await db.commit()

    return {
        "id": str(alerta.id),
        "denuncia_id": str(alerta.denuncia_id),
        "nivel": alerta.nivel.value,
        "titulo": alerta.titulo,
        "descripcion": alerta.descripcion,
        "recomendacion": alerta.recomendacion,
        "leida": alerta.leida,
        "atendida": alerta.atendida,
        "metadata_json": alerta.metadata_json,
        "created_at": alerta.created_at.isoformat()
    }

# ==========================================
# Dashboard - Métricas
# ==========================================

@app.get("/v1/dashboard/metricas")
async def obtener_metricas(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user)
):
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

    # Alertas críticas = denuncias con nivel de riesgo alto o critico
    alertas_result = await db.execute(
        select(func.count(Denuncia.id)).where(
            Denuncia.nivel_riesgo.in_([NivelRiesgo.alto, NivelRiesgo.critico])
        )
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


# ==========================================
# Grafos Criminales (Clusters)
# ==========================================

@app.get("/v1/grafos/criminal")
async def obtener_grafo_criminal(
    denuncia_id: Optional[uuid.UUID] = Query(None, description="Centrar grafo en una denuncia específica"),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve el grafo de red criminal basado en clusters reales.
    Nodos: clústeres (grandes) y denuncias (pequeñas).
    Aristas: pertenencia de denuncia a clúster.
    """
    from app.nlp.clustering import clustering_engine
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(select(Cluster).options(selectinload(Cluster.denuncias)))
    clusters = result.scalars().all()
    
    nodes = []
    links = []
    
    for cluster in clusters:
        # Nodo cluster (grande)
        nodes.append({
            "id": f"cluster-{cluster.id}",
            "label": cluster.codigo,
            "group": "caso",
            "val": max(6, cluster.total_denuncias * 2),
            "metadata": {
                "zona_principal": cluster.zona_principal,
                "nivel_alerta": cluster.nivel_alerta.value if cluster.nivel_alerta else None,
                "total_denuncias": cluster.total_denuncias,
                "monto_min": cluster.monto_min,
                "monto_max": cluster.monto_max,
            }
        })
        
        for d in cluster.denuncias:
            node_id = f"denuncia-{d.id}"
            # Evitar duplicados de denuncias
            if not any(n["id"] == node_id for n in nodes):
                nodes.append({
                    "id": node_id,
                    "label": f"Denuncia {d.tracking_code or str(d.id)[:8]}",
                    "group": "denunciante",
                    "val": 3,
                    "metadata": {
                        "canal": d.canal,
                        "nivel_riesgo": d.nivel_riesgo.value if d.nivel_riesgo else None,
                        "zona": d.zona_detectada,
                    }
                })
            
            links.append({
                "source": node_id,
                "target": f"cluster-{cluster.id}",
                "label": "pertenece"
            })
    
    # Si no hay clusters, devolver datos mínimos para que el frontend no rompa
    if not nodes:
        nodes = [{"id": "empty", "label": "Sin datos", "group": "caso", "val": 1}]
    
    return {"nodes": nodes, "links": links}


# Background Task Wrapper
# ==========================================

async def _run_grafo_background(denuncia_id: uuid.UUID, modo: str, agentes: Optional[List[str]]):
    """Wrapper para ejecución en background tasks de FastAPI"""
    from app.models.db_session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        service = AgentExecutionService(db)
        result = await db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
        denuncia = result.scalar_one_or_none()
        if not denuncia:
            logger.warning(f"_run_grafo_background: denuncia {denuncia_id} no encontrada")
            return
        try:
            await service.ejecutar_grafo(denuncia, modo=modo, agentes_selectivos=agentes)
        except Exception as e:
            logger.exception(f"Error en background ejecutando grafo para denuncia {denuncia_id}: {e}")
            try:
                denuncia.estado = EstadoDenuncia.error_procesamiento
                await db.commit()
            except Exception as inner:
                logger.exception(f"No se pudo actualizar estado de error para denuncia {denuncia_id}: {inner}")
