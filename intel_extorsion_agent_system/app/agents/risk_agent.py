"""
Agente: RiskAgent
Responsabilidad: Evaluación de riesgo criminal consolidada.
"""
from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState, NivelRiesgo
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages

class RiskAgent:
    name = "risk"
    prompt = AGENT_PROMPTS["risk"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        contexto = {
            "intake": state.resultado_intake,
            "nlp": state.resultado_nlp,
            "correlation": state.resultado_correlacion,
            "osint": state.resultado_osint,
        }
        
        user_msg = f"Contexto completo del caso:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        
        nivel = result.get("nivel_riesgo", "bajo")
        return {
            "resultado_riesgo": result,
            "nivel_riesgo": NivelRiesgo(nivel),
            "requiere_escalamiento": nivel in ["alto", "critico"]
        }
