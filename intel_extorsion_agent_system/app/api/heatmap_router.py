"""
Router API para Mapa de Calor (Heatmap)
Devuelve datos GeoJSON para visualización de zonas de extorsión.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from datetime import datetime, timedelta, timezone

from app.models.db_session import get_db
from app.models.database import Denuncia, Cluster
from app.nlp.ontology import get_all_toponimos_for_heatmap

router = APIRouter(prefix="/v1/heatmap", tags=["heatmap"])


@router.get("", response_model=dict)
async def obtener_heatmap(
    zona: Optional[str] = Query(None, description="Filtrar por nombre de zona"),
    periodo: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve puntos de calor con coordenadas GPS para el mapa de extorsión.
    """
    desde = datetime.now(timezone.utc) - timedelta(days=periodo)
    
    # Obtener denuncias con entidades NER en el período
    query = select(Denuncia).where(
        Denuncia.nlp_entities_json.isnot(None),
        Denuncia.created_at >= desde
    )
    if zona:
        query = query.where(Denuncia.zona_detectada.ilike(f"%{zona}%"))
    
    result = await db.execute(query)
    denuncias = result.scalars().all()
    
    # Agregar por zona
    zona_counts = {}
    for d in denuncias:
        z = d.zona_detectada or "Desconocida"
        if z not in zona_counts:
            zona_counts[z] = {"count": 0, "niveles": []}
        zona_counts[z]["count"] += 1
        if d.nivel_riesgo:
            zona_counts[z]["niveles"].append(d.nivel_riesgo.value)
    
    # Construir puntos GeoJSON-like
    puntos = []
    toponimos_base = {t["nombre"]: t for t in get_all_toponimos_for_heatmap()}
    
    for nombre, datos in zona_counts.items():
        info = toponimos_base.get(nombre, {})
        lat = info.get("lat")
        lng = info.get("lng")
        if lat is None or lng is None:
            continue
        
        # Nivel de alerta dominante
        niveles = datos["niveles"]
        nivel_dominante = max(set(niveles), key=niveles.count) if niveles else "bajo"
        
        # Intensidad 0-1 basada en cantidad
        intensidad = min(1.0, datos["count"] / 10.0)
        
        puntos.append({
            "zona": nombre,
            "lat": lat,
            "lng": lng,
            "total_denuncias": datos["count"],
            "nivel_alerta_dominante": nivel_dominante,
            "intensidad": round(intensidad, 2),
            "tipo_zona": info.get("tipo", "desconocido"),
            "riesgo_base": info.get("riesgo_base", "bajo"),
        })
    
    return {
        "periodo_dias": periodo,
        "total_puntos": len(puntos),
        "puntos": puntos,
    }
