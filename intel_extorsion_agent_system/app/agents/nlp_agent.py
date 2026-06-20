"""
Agente: NLPAgent
Responsabilidad: Análisis lingüístico profundo, extracción de entidades y score de amenaza.
"""
from typing import Dict, Any
import json
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.memory.hybrid_memory import memory_system

class NLPAgent:
    name = "nlp"
    prompt = AGENT_PROMPTS["nlp"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        textos = []
        if state.contenido_raw:
            textos.append(f"[TEXTO ORIGINAL] {state.contenido_raw}")
        if state.resultado_ocr:
            textos.append(f"[OCR] {state.resultado_ocr.get('texto_extraido', '')}")
        if state.resultado_speech:
            textos.append(f"[TRANSCRIPCIÓN] {state.resultado_speech.get('transcripcion', '')}")
        
        user_msg = "\n\n---\n\n".join(textos) if textos else "Sin texto disponible"
        
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        
        # Guardar memoria semántica (fire-and-forget en contexto async)
        resumen = result.get("resumen", "")
        keywords = " ".join(result.get("palabras_clave", []))
        await memory_system.save_semantic_memory(
            denuncia_id=str(state.denuncia_id),
            text=f"{resumen} {keywords}",
            metadata={"canal": state.canal, "score": result.get("score_amenaza", 0)}
        )
        
        return {"resultado_nlp": result}
