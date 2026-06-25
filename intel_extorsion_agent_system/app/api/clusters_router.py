"""
Router API para Clusters (NLP Forense + Clustering)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models.db_session import get_db
from app.models.database import Cluster, Denuncia, EstadoCluster, NivelAlertaCluster

router = APIRouter(prefix="/v1/clusters", tags=["clusters"])


@router.get("", response_model=List[dict])
async def listar_clusters(
    estado: Optional[str] = Query(None, description="activo, inactivo, resuelto"),
    zona: Optional[str] = Query(None, description="Filtrar por zona principal"),
    nivel_alerta: Optional[str] = Query(None, description="bajo, medio, alto, critico"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los clústeres activos con perfiles resumidos.
    """
    query = select(Cluster).order_by(desc(Cluster.updated_at))
    if estado:
        query = query.where(Cluster.estado == estado)
    if zona:
        query = query.where(Cluster.zona_principal.ilike(f"%{zona}%"))
    if nivel_alerta:
        query = query.where(Cluster.nivel_alerta == nivel_alerta)
    
    result = await db.execute(query.limit(limit).offset(offset))
    rows = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "codigo": c.codigo,
            "zona_principal": c.zona_principal,
            "estado": c.estado.value if c.estado else None,
            "nivel_alerta": c.nivel_alerta.value if c.nivel_alerta else None,
            "total_denuncias": c.total_denuncias,
            "monto_min": c.monto_min,
            "monto_max": c.monto_max,
            "cuentas_detectadas": c.cuentas_detectadas or [],
            "jerga_frecuente": c.jerga_frecuente or [],
            "metodos_violencia": c.metodos_violencia or [],
            "primera_denuncia": c.primera_denuncia.isoformat() if c.primera_denuncia else None,
            "ultima_denuncia": c.ultima_denuncia.isoformat() if c.ultima_denuncia else None,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]


@router.get("/{cluster_id}", response_model=dict)
async def obtener_cluster(
    cluster_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Perfil completo de un clúster (banda criminal).
    """
    result = await db.execute(select(Cluster).where(Cluster.id == cluster_id))
    cluster = result.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Clúster no encontrado")
    
    return {
        "id": cluster.id,
        "codigo": cluster.codigo,
        "zona_principal": cluster.zona_principal,
        "estado": cluster.estado.value if cluster.estado else None,
        "nivel_alerta": cluster.nivel_alerta.value if cluster.nivel_alerta else None,
        "total_denuncias": cluster.total_denuncias,
        "monto_min": cluster.monto_min,
        "monto_max": cluster.monto_max,
        "cuentas_detectadas": cluster.cuentas_detectadas or [],
        "telefonos_detectados": cluster.telefonos_detectados or [],
        "jerga_frecuente": cluster.jerga_frecuente or [],
        "metodos_violencia": cluster.metodos_violencia or [],
        "primera_denuncia": cluster.primera_denuncia.isoformat() if cluster.primera_denuncia else None,
        "ultima_denuncia": cluster.ultima_denuncia.isoformat() if cluster.ultima_denuncia else None,
        "created_at": cluster.created_at.isoformat(),
        "updated_at": cluster.updated_at.isoformat(),
    }


@router.get("/{cluster_id}/denuncias", response_model=List[dict])
async def obtener_denuncias_cluster(
    cluster_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Denuncias anónimas asociadas a un clúster (sin PII del denunciante).
    """
    result = await db.execute(
        select(Denuncia).where(Denuncia.cluster_id == cluster_id)
        .order_by(desc(Denuncia.created_at))
        .limit(limit)
    )
    rows = result.scalars().all()
    
    return [
        {
            "id": str(d.id),
            "canal": d.canal,
            "estado": d.estado.value if d.estado else None,
            "nivel_riesgo": d.nivel_riesgo.value if d.nivel_riesgo else None,
            "zona_detectada": d.zona_detectada,
            "tracking_code": d.tracking_code,
            "nlp_entities": d.nlp_entities_json,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]


@router.post("/recalculate", response_model=dict)
async def recalcular_clusters(
    db: AsyncSession = Depends(get_db)
):
    """
    Fuerza el recálculo completo de todos los clústeres.
    Útil para mantenimiento o después de cargar seed data.
    """
    from app.nlp.clustering import clustering_engine
    
    result = await db.execute(
        select(Denuncia).where(Denuncia.nlp_entities_json.isnot(None))
    )
    denuncias = result.scalars().all()
    
    if len(denuncias) < 3:
        return {"status": "insufficient_data", "clusters_found": 0, "denuncias_analizadas": len(denuncias)}
    
    clustering_engine.build_graph(denuncias)
    active = clustering_engine.find_active_clusters()
    
    # Limpiar clusters antiguos
    await db.execute(select(Cluster))  # placeholder para lógica de limpieza si es necesaria
    
    return {
        "status": "ok",
        "clusters_found": len(active),
        "denuncias_analizadas": len(denuncias),
        "clusters": [len(c) for c in active],
    }
