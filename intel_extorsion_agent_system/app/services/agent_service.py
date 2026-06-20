"""
Servicio de Ejecución del Grafo de Agentes
"""
import uuid
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_graph import agent_graph
from app.schemas.agent_schemas import (
    AgenteState, DenunciaIngestaRequest, ProcesarDenunciaRequest,
    EjecucionGrafoResponse
)
from app.models.database import Denuncia, ResultadoAgente, Alerta, EstadoProcesamiento, NivelRiesgo as NivelRiesgoDB
from app.memory.hybrid_memory import memory_system
from app.config.settings import settings

class AgentExecutionService:
    """
    Servicio principal que ejecuta el grafo LangGraph para una denuncia,
    persiste resultados y gestiona memoria.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def crear_denuncia(self, req: DenunciaIngestaRequest) -> Denuncia:
        """Crea el registro inicial de denuncia en PostgreSQL"""
        denuncia = Denuncia(
            canal=req.canal.value,
            id_externo=req.id_externo,
            did_denunciante=req.did_denunciante,
            tipo_contenido=req.tipo_contenido.value,
            contenido_raw=req.contenido_raw,
            url_archivo=req.url_archivo,
            metadata_json=req.metadata
        )
        self.db.add(denuncia)
        await self.db.commit()
        await self.db.refresh(denuncia)
        return denuncia
    
    async def ejecutar_grafo(
        self,
        denuncia: Denuncia,
        modo: str = "completo",
        agentes_selectivos: Optional[list] = None
    ) -> EjecucionGrafoResponse:
        """
        Ejecuta el grafo de agentes sobre una denuncia.
        """
        start_time = time.time()
        
        # Construir estado inicial
        initial_state = AgenteState(
            denuncia_id=denuncia.id,
            canal=denuncia.canal,
            tipo_contenido=denuncia.tipo_contenido,
            contenido_raw=denuncia.contenido_raw,
            url_archivo=denuncia.url_archivo,
            hash_archivo=denuncia.hash_archivo,
            metadata=denuncia.metadata_json or {}
        )
        
        # Si modo selectivo, marcar agentes a saltar
        if modo == "selectivo" and agentes_selectivos:
            all_agents = ["intake", "ocr", "speech", "nlp", "correlation", "osint", "risk", "alert"]
            initial_state.saltar_agentes = [a for a in all_agents if a not in agentes_selectivos]
        
        # Ejecutar grafo
        config = {"configurable": {"thread_id": str(denuncia.id)}}
        result = await agent_graph.ainvoke(initial_state, config=config)
        final_state = AgenteState(**result)
        
        # Persistir resultados de cada agente
        agent_results_map = {
            "intake": final_state.resultado_intake,
            "ocr": final_state.resultado_ocr,
            "speech": final_state.resultado_speech,
            "nlp": final_state.resultado_nlp,
            "correlation": final_state.resultado_correlacion,
            "osint": final_state.resultado_osint,
            "risk": final_state.resultado_riesgo,
            "alert": final_state.resultado_alerta,
        }
        
        for agent_name, res in agent_results_map.items():
            if res:
                await self._persistir_resultado(denuncia.id, agent_name, res)
        
        # Guardar en memoria semántica (Qdrant) el resumen NLP
        if final_state.resultado_nlp:
            await memory_system.save_semantic_memory(
                denuncia_id=str(denuncia.id),
                text=final_state.resultado_nlp.get("resumen", "") + " " + " ".join(final_state.resultado_nlp.get("palabras_clave", [])),
                metadata={
                    "canal": denuncia.canal,
                    "score_amenaza": final_state.resultado_nlp.get("score_amenaza", 0),
                    "nivel_riesgo": final_state.nivel_riesgo.value if final_state.nivel_riesgo else None
                }
            )
        
        # Actualizar estado denuncia
        denuncia.estado = self._mapear_estado_final(final_state)
        denuncia.procesado_at = datetime.utcnow()
        await self.db.commit()
        
        # Generar alerta en DB si aplica
        alertas_generadas = 0
        if final_state.resultado_alerta and final_state.resultado_alerta.get("alerta_generada"):
            alertas_generadas = await self._persistir_alerta(denuncia.id, final_state.resultado_alerta)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return EjecucionGrafoResponse(
            denuncia_id=denuncia.id,
            estado_final=denuncia.estado.value,
            resultados={k: v for k, v in agent_results_map.items() if v},
            tiempo_total_ms=elapsed_ms,
            alertas_generadas=alertas_generadas,
            errores=final_state.errores
        )
    
    async def _persistir_resultado(self, denuncia_id: uuid.UUID, agente: str, resultado: Dict[str, Any]):
        """Guarda resultado individual de agente"""
        reg = ResultadoAgente(
            denuncia_id=denuncia_id,
            agente=agente,
            resultado_json=resultado,
            exitoso="error" not in resultado
        )
        self.db.add(reg)
    
    async def _persistir_alerta(self, denuncia_id: uuid.UUID, alerta_data: Dict[str, Any]) -> int:
        """Persiste alerta oficial"""
        nivel_str = alerta_data.get("nivel", "medio")
        alerta = Alerta(
            denuncia_id=denuncia_id,
            nivel=NivelRiesgoDB(nivel_str),
            titulo=alerta_data.get("titulo", "Alerta sin título"),
            descripcion=alerta_data.get("descripcion", ""),
            recomendacion=alerta_data.get("recomendacion", "")
        )
        self.db.add(alerta)
        await self.db.commit()
        return 1
    
    def _mapear_estado_final(self, state: AgenteState) -> EstadoProcesamiento:
        if state.resultado_alerta and state.resultado_alerta.get("alerta_generada"):
            return EstadoProcesamiento.ALERTA_GENERADA
        if state.resultado_riesgo:
            return EstadoProcesamiento.RIESGO_EVALUADO
        if state.resultado_correlacion:
            return EstadoProcesamiento.CORRELACIONADO
        if state.resultado_nlp:
            return EstadoProcesamiento.PROCESADO
        return EstadoProcesamiento.EN_ANALISIS
