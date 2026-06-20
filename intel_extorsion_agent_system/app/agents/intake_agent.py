"""
Agente: IntakeAgent
Responsabilidad: Validación y clasificación inicial de denuncias.
"""
from typing import Dict, Any
from app.schemas.agent_schemas import AgenteState, IntakeResult
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages

class IntakeAgent:
    """
    Intake Agent: Primera línea de recepción.
    Determina si el contenido es una denuncia válida de extorsión,
    asigna prioridad y extrae entidades iniciales.
    """
    
    name = "intake"
    prompt = AGENT_PROMPTS["intake"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        formatted_prompt = self.prompt.format(
            canal=state.canal,
            tipo_contenido=state.tipo_contenido
        )
        user_msg = (
            f"Contenido recibido:\n{state.contenido_raw or '[Sin texto - archivo adjunto]'}\n\n"
            f"Metadata: {state.metadata}"
        )
        
        messages = _build_messages(formatted_prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        
        # Decisiones de enrutamiento
        saltar = []
        if not result.get("valido", True):
            saltar = ["ocr", "speech", "nlp", "correlation", "osint", "risk", "alert"]
        
        return {
            "resultado_intake": result,
            "saltar_agentes": saltar,
            "mensajes": [{"role": "assistant", "content": response.content}]
        }
