"""
Agente: CorrelationAgent
Responsabilidad: Correlacionar con casos históricos y detectar redes criminales.
"""
from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.memory.hybrid_memory import memory_system

class CorrelationAgent:
    name = "correlation"
    prompt = AGENT_PROMPTS["correlation"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        nlp_res = state.resultado_nlp or {}
        query_parts = [nlp_res.get("resumen", "")]
        query_parts.extend([e.get("valor", "") for e in nlp_res.get("entidades", [])])
        query = " | ".join(filter(None, query_parts))
        
        # Traer casos similares para enriquecer prompt
        similares = await memory_system.search_similar_cases(
            query=query,
            denuncia_id_excluir=str(state.denuncia_id),
            limit=5
        )
        
        user_msg = (
            f"Query de búsqueda: {query}\n"
            f"Entidades clave: {json.dumps(nlp_res.get('entidades', []), ensure_ascii=False)}\n"
            f"Casos similares encontrados: {json.dumps(similares, ensure_ascii=False)}"
        )
        
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        return {"resultado_correlacion": result}
