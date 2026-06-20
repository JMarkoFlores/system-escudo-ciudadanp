"""
Agente: SpeechAgent
Responsabilidad: Transcripción y análisis forense de audio.
"""
from typing import Dict, Any
from app.schemas.agent_schemas import AgenteState
from app.prompts.system_prompts import AGENT_PROMPTS
from app.core.agent_graph import llm, _parse_llm_json, _build_messages
from app.tools.shared_tools import AGENT_TOOLS

class SpeechAgent:
    name = "speech"
    prompt = AGENT_PROMPTS["speech"]
    
    async def run(self, state: AgenteState) -> Dict[str, Any]:
        if state.tipo_contenido not in ["audio", "video", "mixto"]:
            return {"resultado_speech": None}
        
        stt_tool = AGENT_TOOLS["transcribir_audio"]
        tool_result = {}
        if state.url_archivo:
            tool_result = await stt_tool._arun(audio_url=state.url_archivo, idioma="es")
        
        user_msg = (
            f"URL del audio: {state.url_archivo}\n"
            f"Resultado preliminar STT engine: {tool_result}"
        )
        
        messages = _build_messages(self.prompt, user_msg, state)
        response = await llm.ainvoke(messages)
        result = _parse_llm_json(response.content)
        return {"resultado_speech": result}
