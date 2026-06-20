"""
Agente: OSINTAgent
Responsabilidad: Enriquecimiento con fuentes abiertas (teléfonos, cuentas, redes).
"""
from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.tools.shared_tools import AGENT_TOOLS

class OSINTAgent:
    name = "osint"
    prompt = AGENT_PROMPTS["osint"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        entidades = []
        if state.resultado_intake:
            entidades.extend(state.resultado_intake.get("entidades_detectadas", []))
        if state.resultado_nlp:
            entidades.extend(state.resultado_nlp.get("entidades", []))
        
        # Ejecutar tool OSINT para cada entidad relevante
        osint_tool = AGENT_TOOLS["consultar_osint"]
        tool_results = []
        for e in entidades:
            if e.get("tipo") in ["telefono", "cuenta_bancaria"]:
                tr = await osint_tool._arun(
                    telefono=e.get("valor") if e.get("tipo") == "telefono" else None,
                    cuenta_bancaria=e.get("valor") if e.get("tipo") == "cuenta_bancaria" else None
                )
                tool_results.append(tr)
        
        user_msg = (
            f"Entidades a investigar: {json.dumps(entidades, ensure_ascii=False)}\n"
            f"Resultados preliminares OSINT: {json.dumps(tool_results, ensure_ascii=False)}"
        )
        
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        return {"resultado_osint": result}
