"""
Servicio de Ejecución del Grafo de Agentes
"""
import uuid
import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.core.agent_graph import agent_graph
from app.schemas.agent_schemas import (
    AgenteState, DenunciaIngestaRequest, ProcesarDenunciaRequest,
    EjecucionGrafoResponse
)
from app.models.database import Denuncia, ResultadoAgente, Alerta, Cluster, EstadoDenuncia, NivelRiesgo as NivelRiesgoDB, EstadoCluster, NivelAlertaCluster
from app.memory.hybrid_memory import memory_system
from app.config.settings import settings
from app.nlp.ner_engine import ner_engine
from app.nlp.clustering import clustering_engine

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
            all_agents = ["intake", "ocr", "speech", "nlp", "correlation", "osint", "risk", "seal", "alert", "respond"]
            initial_state.saltar_agentes = [a for a in all_agents if a not in agentes_selectivos]
        
        # Ejecutar grafo
        final_state = None
        try:
            config = {"configurable": {"thread_id": str(denuncia.id)}}
            result = await agent_graph.ainvoke(initial_state, config=config)
            final_state = AgenteState(**result)

            # Limpiar resultados previos para evitar duplicados en reprocesamientos
            await self.db.execute(
                delete(ResultadoAgente).where(ResultadoAgente.denuncia_id == denuncia.id)
            )
        except Exception as e:
            logger.exception(f"Error ejecutando agent_graph para denuncia {denuncia.id}: {e}")
            denuncia.estado = EstadoDenuncia.error_procesamiento
            await self.db.commit()
            return EjecucionGrafoResponse(
                denuncia_id=denuncia.id,
                estado_final=denuncia.estado.value,
                resultados={},
                tiempo_total_ms=int((time.time() - start_time) * 1000),
                alertas_generadas=0,
                errores=[str(e)]
            )
        
        # Persistir resultados de cada agente
        agent_results_map = {
            "intake": final_state.resultado_intake,
            "ocr": final_state.resultado_ocr,
            "speech": final_state.resultado_speech,
            "nlp": final_state.resultado_nlp,
            "correlation": final_state.resultado_correlacion,
            "cluster": final_state.resultado_cluster,
            "osint": final_state.resultado_osint,
            "risk": final_state.resultado_riesgo,
            "seal": final_state.resultado_seal,
            "alert": final_state.resultado_alerta,
            "respond": final_state.resultado_respond,
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
        
        # Guardar tracking_code
        if final_state.tracking_code:
            denuncia.tracking_code = final_state.tracking_code
        
        # Guardar datos de sellado blockchain
        if final_state.seal_tx_hash:
            denuncia.seal_tx_hash = final_state.seal_tx_hash
        if final_state.seal_block:
            denuncia.seal_block = final_state.seal_block
        if final_state.seal_status:
            denuncia.seal_status = final_state.seal_status
        
        # Guardar nivel de riesgo
        if final_state.nivel_riesgo:
            denuncia.nivel_riesgo = NivelRiesgoDB(final_state.nivel_riesgo.value)
        
        # Guardar entidades NER y zona detectada
        if final_state.resultado_cluster:
            denuncia.nlp_entities_json = final_state.resultado_cluster
            if final_state.zona_detectada:
                denuncia.zona_detectada = final_state.zona_detectada
        
        # Asignar a clúster (post-grafo)
        await self._asignar_cluster(denuncia)
        
        # Actualizar estado denuncia
        denuncia.estado = self._mapear_estado_final(final_state)
        denuncia.procesado_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # Generar alerta en DB si aplica
        alertas_generadas = 0
        if final_state.resultado_alerta and final_state.resultado_alerta.get("alerta_generada"):
            nivel_real = final_state.nivel_riesgo.value if final_state.nivel_riesgo else None
            alertas_generadas = await self._persistir_alerta(denuncia.id, final_state.resultado_alerta, nivel_real)
        
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
    
    async def _persistir_alerta(self, denuncia_id: uuid.UUID, alerta_data: Dict[str, Any], nivel_riesgo_real: Optional[str] = None) -> int:
        """Persiste alerta oficial usando el nivel de riesgo real y dispara notificaciones push."""
        nivel_str = alerta_data.get("nivel") or nivel_riesgo_real or "medio"
        nivel_str = str(nivel_str).lower().strip()
        alerta = Alerta(
            denuncia_id=denuncia_id,
            nivel=NivelRiesgoDB(nivel_str),
            titulo=alerta_data.get("titulo", "Alerta sin título"),
            descripcion=alerta_data.get("descripcion", ""),
            recomendacion=alerta_data.get("recomendacion", ""),
            zona=alerta_data.get("zona"),
            tx_hash=alerta_data.get("tx_hash") or alerta_data.get("seal_tx_hash")
        )
        self.db.add(alerta)
        await self.db.commit()

        # Enviar notificaciones push (no bloquea si fallan)
        try:
            from sqlalchemy import select
            result = await self.db.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
            denuncia = result.scalar_one_or_none()
            from app.services.notification_service import send_alert_notifications
            await send_alert_notifications(
                denuncia_id=str(denuncia_id),
                nivel=nivel_str,
                titulo=alerta.titulo,
                descripcion=alerta.descripcion,
                recomendacion=alerta.recomendacion or None,
                tracking_code=denuncia.tracking_code if denuncia else None,
                tx_hash=denuncia.seal_tx_hash if denuncia else None,
            )
        except Exception as exc:
            logger.warning(f"No se pudieron enviar notificaciones push para alerta {denuncia_id}: {exc}")

        return 1
    
    async def _asignar_cluster(self, denuncia: Denuncia):
        """
        Busca si la denuncia encaja en un clúster existente.
        Si no, crea uno nuevo si hay suficientes denuncias similares.
        """
        from sqlalchemy import select
        
        # Obtener todas las denuncias con entidades NER
        result = await self.db.execute(
            select(Denuncia).where(Denuncia.nlp_entities_json.isnot(None))
        )
        todas_denuncias = result.scalars().all()
        
        if len(todas_denuncias) < 3:
            return
        
        # Construir grafo y encontrar clusters
        clustering_engine.build_graph(todas_denuncias)
        active_clusters = clustering_engine.find_active_clusters()
        
        # Para cada componente conectada, asegurar que existe un Cluster en DB
        for component in active_clusters:
            if len(component) < 3:
                continue
            
            # Buscar si ya existe un cluster con estas denuncias
            denuncia_ids = set(component)
            existing_cluster = None
            for d_id in component:
                d_obj = await self.db.execute(select(Denuncia).where(Denuncia.id == d_id))
                d_row = d_obj.scalar_one_or_none()
                if d_row and d_row.cluster_id:
                    existing_cluster = d_row.cluster_id
                    break
            
            if existing_cluster:
                # Actualizar cluster existente
                cluster_obj = await self.db.execute(select(Cluster).where(Cluster.id == existing_cluster))
                cluster = cluster_obj.scalar_one_or_none()
                if cluster:
                    profile = clustering_engine.calculate_cluster_profile(component)
                    cluster.total_denuncias = profile.get("total_denuncias", 0)
                    cluster.zona_principal = profile.get("zona_principal")
                    cluster.monto_min = str(profile.get("monto_min")) if profile.get("monto_min") else None
                    cluster.monto_max = str(profile.get("monto_max")) if profile.get("monto_max") else None
                    cluster.cuentas_detectadas = profile.get("cuentas_detectadas")
                    cluster.jerga_frecuente = profile.get("jerga_frecuente")
                    cluster.metodos_violencia = profile.get("metodos_violencia")
                    cluster.nivel_alerta = NivelAlertaCluster(profile.get("nivel_alerta", "bajo"))
                    # Asignar cluster_id a denuncias sin cluster
                    for d_id in component:
                        d_obj = await self.db.execute(select(Denuncia).where(Denuncia.id == d_id))
                        d_row = d_obj.scalar_one_or_none()
                        if d_row and not d_row.cluster_id:
                            d_row.cluster_id = cluster.id
            else:
                # Crear nuevo cluster
                profile = clustering_engine.calculate_cluster_profile(component)
                codigo = clustering_engine.generar_codigo_cluster()
                nuevo_cluster = Cluster(
                    codigo=codigo,
                    zona_principal=profile.get("zona_principal"),
                    estado=EstadoCluster.activo,
                    nivel_alerta=NivelAlertaCluster(profile.get("nivel_alerta", "bajo")),
                    total_denuncias=profile.get("total_denuncias", 0),
                    monto_min=str(profile.get("monto_min")) if profile.get("monto_min") else None,
                    monto_max=str(profile.get("monto_max")) if profile.get("monto_max") else None,
                    cuentas_detectadas=profile.get("cuentas_detectadas"),
                    jerga_frecuente=profile.get("jerga_frecuente"),
                    metodos_violencia=profile.get("metodos_violencia"),
                    primera_denuncia=profile.get("primera_denuncia"),
                    ultima_denuncia=profile.get("ultima_denuncia"),
                )
                self.db.add(nuevo_cluster)
                await self.db.flush()  # Para obtener el ID
                for d_id in component:
                    d_obj = await self.db.execute(select(Denuncia).where(Denuncia.id == d_id))
                    d_row = d_obj.scalar_one_or_none()
                    if d_row:
                        d_row.cluster_id = nuevo_cluster.id
        
        await self.db.commit()

    def _mapear_estado_final(self, state: AgenteState) -> EstadoDenuncia:
        if state.resultado_alerta and state.resultado_alerta.get("alerta_generada"):
            return EstadoDenuncia.alerta_generada
        if state.resultado_riesgo:
            return EstadoDenuncia.riesgo_evaluado
        if state.resultado_correlacion:
            return EstadoDenuncia.correlacionado
        if state.resultado_nlp:
            return EstadoDenuncia.procesado
        if state.resultado_intake:
            # Si el intake rechazó la denuncia, se archiva para no dejarla congelada
            if not state.resultado_intake.get("valido", True):
                return EstadoDenuncia.archivado
            return EstadoDenuncia.procesado
        return EstadoDenuncia.en_analisis
