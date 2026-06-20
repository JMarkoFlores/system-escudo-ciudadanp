"""
Agente: OCRAgent
Responsabilidad: Extracción y estructuración de texto desde imágenes/documentos.
"""
from typing import Dict, Any, Optional
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.tools.shared_tools import AGENT_TOOLS

class OCRAgent:
    name = "ocr"
    prompt = AGENT_PROMPTS["ocr"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        if state.tipo_contenido not in ["imagen", "documento", "mixto"]:
            return {"resultado_ocr": None}
        
        # Ejecutar tool OCR real si hay URL
        ocr_tool = AGENT_TOOLS["extraer_ocr"]
        tool_result = {}
        if state.url_archivo:
            tool_result = await ocr_tool._arun(image_url=state.url_archivo, idioma="spa")
        
        user_msg = (
            f"URL del archivo: {state.url_archivo}\n"
            f"Hash: {state.hash_archivo}\n"
            f"Resultado preliminar OCR engine: {tool_result}"
        )
        
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        return {"resultado_ocr": result}
