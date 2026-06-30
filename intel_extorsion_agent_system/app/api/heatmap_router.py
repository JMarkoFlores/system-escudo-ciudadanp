"""
Router API para Mapa de Calor (Heatmap)
Devuelve datos GeoJSON para visualización de zonas de extorsión
integrado con el Plan Cuadrante PNP de La Libertad.
"""
import json
import os
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.models.db_session import get_db
from app.models.database import Denuncia
from app.api.auth_router import require_user

router = APIRouter(prefix="/v1/heatmap", tags=["heatmap"], dependencies=[Depends(require_user)])


def _load_cuadrantes_geojson():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "plan_cuadrante_la_libertad.geojson")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"type": "FeatureCollection", "features": []}


def _build_cuadrante_index(geojson: dict) -> dict:
    """Construye un índice de cuadrantes por distrito para búsqueda rápida."""
    index = {}
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        # Soporta múltiples campos de zona: distrito, provincia, cuadrante
        keys = []
        if props.get("distrito"):
            keys.append(props["distrito"].lower().strip())
        if props.get("provincia"):
            keys.append(props["provincia"].lower().strip())
        if props.get("cuadrante"):
            keys.append(props["cuadrante"].lower().strip())
        
        for key in keys:
            if key:
                index.setdefault(key, []).append(feature)
    return index


@router.get("/cuadrantes", response_model=dict)
async def obtener_cuadrantes():
    """Devuelve el GeoJSON base del Plan Cuadrante PNP (La Libertad)."""
    return _load_cuadrantes_geojson()


@router.get("", response_model=dict)
async def obtener_heatmap(
    zona: Optional[str] = Query(None, description="Filtrar por distrito/zona"),
    periodo: int = Query(30, ge=1, le=365, description="Días hacia atrás"),
    db: AsyncSession = Depends(get_db)
):
    """
    Devuelve puntos de calor y polígonos de cuadrantes con métricas
    agregadas de denuncias en el período.
    """
    desde = datetime.now(timezone.utc) - timedelta(days=periodo)

    query = select(Denuncia).where(Denuncia.created_at >= desde)
    if zona:
        query = query.where(Denuncia.zona_detectada.ilike(f"%{zona}%"))

    result = await db.execute(query)
    denuncias = result.scalars().all()

    # Agregar por distrito/zona detectada
    zona_counts = {}
    for d in denuncias:
        z = d.zona_detectada or "Desconocida"
        if z not in zona_counts:
            zona_counts[z] = {"count": 0, "niveles": []}
        zona_counts[z]["count"] += 1
        if d.nivel_riesgo:
            zona_counts[z]["niveles"].append(d.nivel_riesgo.value)

    # Cargar cuadrantes oficiales
    geojson = _load_cuadrantes_geojson()
    features = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {}).copy()
        distrito = props.get("distrito", "").lower().strip()
        datos = zona_counts.get(distrito, {"count": 0, "niveles": []})

        niveles = datos["niveles"]
        nivel_dominante = max(set(niveles), key=niveles.count) if niveles else props.get("riesgo_base", "bajo")
        intensidad = min(1.0, datos["count"] / 10.0)

        props.update({
            "total_denuncias_periodo": datos["count"],
            "nivel_alerta_dominante": nivel_dominante,
            "intensidad": round(intensidad, 2),
            "periodo_dias": periodo,
        })
        features.append({**feature, "properties": props})

    # Puntos de calor independientes para zonas no cubiertas por cuadrantes
    puntos = []
    for nombre, datos in zona_counts.items():
        if any(f["properties"].get("distrito", "").lower().strip() == nombre.lower().strip() for f in features):
            continue
        niveles = datos["niveles"]
        nivel_dominante = max(set(niveles), key=niveles.count) if niveles else "bajo"
        puntos.append({
            "zona": nombre,
            "lat": None,
            "lng": None,
            "total_denuncias": datos["count"],
            "nivel_alerta_dominante": nivel_dominante,
            "intensidad": round(min(1.0, datos["count"] / 10.0), 2),
        })

    return {
        "periodo_dias": periodo,
        "total_cuadrantes": len(features),
        "total_puntos_adicionales": len(puntos),
        "cuadrantes": {"type": "FeatureCollection", "features": features},
        "puntos": puntos,
    }
