"""
Agente: AlertAgent
Responsabilidad: Generación y emisión de alertas oficiales ante riesgo alto/crítico.
"""
from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.tools.shared_tools import AGENT_TOOLS

class AlertAgent:
    name = "alert"
    prompt = AGENT_PROMPTS["alert"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        riesgo = state.resultado_riesgo or {}
        if riesgo.get("nivel_riesgo") not in ["alto", "critico"]:
            return {
                "resultado_alerta": {
                    "alerta_generada": False,
                    "motivo": "Riesgo no amerita alerta inmediata"
                }
            }
        
        user_msg = f"Resultado Risk Agent: {json.dumps(riesgo, ensure_ascii=False)}"
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        
        # Emitir alerta vía tool si se indica
        if result.get("alerta_generada"):
            alert_tool = AGENT_TOOLS["emitir_alerta"]
            await alert_tool._arun(
                denuncia_id=str(state.denuncia_id),
                nivel=riesgo.get("nivel_riesgo"),
                titulo=result.get("titulo", "Alerta"),
                descripcion=result.get("descripcion", ""),
                recomendacion=result.get("recomendacion", "")
            )
        
        return {"resultado_alerta": result}
