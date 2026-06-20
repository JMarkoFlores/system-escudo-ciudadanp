"""
Core LangGraph: Definición del grafo de estados y nodos de agentes
"""
from typing import Dict, Any, List, Optional, Literal
import uuid
import json
from datetime import datetime

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.config.settings import settings
from app.schemas.agent_schemas import AgenteState, NivelRiesgo
from app.prompts.system_prompts import AGENT_PROMPTS
from app.tools.shared_tools import AGENT_TOOLS

# ==========================================
# LLM Configuración (Lazy)
# ==========================================
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            api_key=settings.GROQ_API_KEY,
        )
    return _llm

# Variable de conveniencia para imports directos en agentes individuales
llm = get_llm()

# ==========================================
# Funciones utilitarias para nodos
# ==========================================

def _parse_llm_json(content: str) -> Dict[str, Any]:
    """Parsea la respuesta JSON del LLM de forma robusta"""
    try:
        if isinstance(content, str):
            return json.loads(content)
        return content
    except json.JSONDecodeError:
        # Fallback: extraer bloque JSON
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                # Intentar encontrar el primer objeto JSON válido (non-greedy)
                for m in re.finditer(r'\{.*?\}', content, re.DOTALL):
                    try:
                        return json.loads(m.group())
                    except json.JSONDecodeError:
                        continue
        return {"error": "No se pudo parsear JSON", "raw": content}

def _build_messages(system_prompt: str, user_content: str, state: AgenteState) -> List[Dict[str, Any]]:
    """Construye mensajes para el LLM"""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

# ==========================================
# Nodos del Grafo (cada agente es un nodo)
# ==========================================

async def node_intake(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 1: Intake Agent
    Valida y clasifica la denuncia entrante.
    """
    prompt = AGENT_PROMPTS["intake"].format(
        canal=state.canal,
        tipo_contenido=state.tipo_contenido
    )
    user_msg = f"Contenido recibido:\n{state.contenido_raw or '[Sin texto - archivo adjunto]'}\n\nMetadata: {json.dumps(state.metadata, ensure_ascii=False)}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    # Decisión de flujo
    if not result.get("valido", True):
        state.saltar_agentes = ["ocr", "speech", "nlp", "correlation", "osint", "risk", "alert"]
        state.errores.append(f"Intake rechazado: {result.get('notas', 'Sin justificación')}")
    
    return {
        "resultado_intake": result,
        "mensajes": [{"role": "assistant", "content": response.content}]
    }

async def node_ocr(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 2: OCR Agent
    Procesa imágenes/documentos si aplica.
    """
    if "ocr" in state.saltar_agentes or state.tipo_contenido not in ["imagen", "documento", "mixto"]:
        return {"resultado_ocr": None}
    
    prompt = AGENT_PROMPTS["ocr"]
    user_msg = f"URL del archivo: {state.url_archivo}\nHash: {state.hash_archivo}\nTexto pre-extraído por OCR engine: [PENDIENTE - ingesta raw]"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_ocr": result}

async def node_speech(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 3: Speech Agent
    Transcribe y analiza audio.
    """
    if "speech" in state.saltar_agentes or state.tipo_contenido not in ["audio", "video", "mixto"]:
        return {"resultado_speech": None}
    
    prompt = AGENT_PROMPTS["speech"]
    user_msg = f"URL del audio: {state.url_archivo}\nDuración estimada: {state.metadata.get('duracion_seg', 'desconocida')}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_speech": result}

async def node_nlp(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 4: NLP Agent
    Analiza texto completo (raw + OCR + Speech).
    """
    if "nlp" in state.saltar_agentes:
        return {"resultado_nlp": None}
    
    # Consolidar texto de todas las fuentes
    textos = []
    if state.contenido_raw:
        textos.append(f"[TEXTO ORIGINAL] {state.contenido_raw}")
    if state.resultado_ocr:
        textos.append(f"[OCR] {state.resultado_ocr.get('texto_extraido', '')}")
    if state.resultado_speech:
        textos.append(f"[TRANSCRIPCIÓN] {state.resultado_speech.get('transcripcion', '')}")
    
    prompt = AGENT_PROMPTS["nlp"]
    user_msg = "\n\n---\n\n".join(textos) if textos else "Sin texto disponible"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_nlp": result}

async def node_correlation(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 5: Correlation Agent
    Busca casos similares y detecta redes.
    """
    if "correlation" in state.saltar_agentes:
        return {"resultado_correlacion": None}
    
    # Preparar query de búsqueda a partir de NLP
    nlp_res = state.resultado_nlp or {}
    query_parts = [nlp_res.get("resumen", "")]
    query_parts.extend([e.get("valor", "") for e in nlp_res.get("entidades", [])])
    query = " | ".join(filter(None, query_parts))
    
    prompt = AGENT_PROMPTS["correlation"]
    user_msg = f"Query de búsqueda: {query}\nEntidades clave: {json.dumps(nlp_res.get('entidades', []), ensure_ascii=False)}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_correlacion": result}

async def node_osint(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 6: OSINT Agent
    Enriquece con inteligencia de fuentes abiertas.
    """
    if "osint" in state.saltar_agentes:
        return {"resultado_osint": None}
    
    # Extraer teléfonos y cuentas de NLP + Intake
    entidades = []
    if state.resultado_intake:
        entidades.extend(state.resultado_intake.get("entidades_detectadas", []))
    if state.resultado_nlp:
        entidades.extend(state.resultado_nlp.get("entidades", []))
    
    prompt = AGENT_PROMPTS["osint"]
    user_msg = f"Entidades a investigar: {json.dumps(entidades, ensure_ascii=False)}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_osint": result}

async def node_risk(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 7: Risk Agent
    Evalúa riesgo consolidado.
    """
    if "risk" in state.saltar_agentes:
        return {"resultado_riesgo": None}
    
    # Compilar todos los resultados previos como contexto
    contexto = {
        "intake": state.resultado_intake,
        "nlp": state.resultado_nlp,
        "correlation": state.resultado_correlacion,
        "osint": state.resultado_osint,
    }
    
    prompt = AGENT_PROMPTS["risk"]
    user_msg = f"Contexto completo del caso:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    # Actualizar estado de riesgo
    nivel = result.get("nivel_riesgo", "bajo")
    if isinstance(nivel, str):
        nivel = nivel.lower().strip()
    if nivel in ["alto", "critico"]:
        state.requiere_escalamiento = True
    state.nivel_riesgo = NivelRiesgo(nivel)
    
    return {"resultado_riesgo": result}

async def node_alert(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 8: Alert Agent
    Emite alertas si el riesgo es alto/crítico.
    """
    if "alert" in state.saltar_agentes:
        return {"resultado_alerta": None}
    
    riesgo = state.resultado_riesgo or {}
    nivel = riesgo.get("nivel_riesgo", "")
    if isinstance(nivel, str):
        nivel = nivel.lower().strip()
    if nivel not in ["alto", "critico"]:
        return {
            "resultado_alerta": {
                "alerta_generada": False,
                "motivo": "Riesgo no amerita alerta inmediata"
            }
        }
    
    prompt = AGENT_PROMPTS["alert"]
    user_msg = f"Resultado Risk Agent: {json.dumps(riesgo, ensure_ascii=False)}"
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    
    return {"resultado_alerta": result}

# ==========================================
# Routing / Condicional edges
# ==========================================

def router_continue(state: AgenteState) -> str:
    """Decide si continuar o saltar según errores acumulados"""
    if len(state.errores) >= 3:
        return "end"
    return "continue"

def router_post_intake(state: AgenteState) -> str:
    """Después del intake, decide qué agentes ejecutar"""
    if not state.resultado_intake or not state.resultado_intake.get("valido", True):
        return "end"
    
    # Dependiendo del tipo de contenido, enrutar
    if state.tipo_contenido in ["imagen", "documento"]:
        return "ocr"
    elif state.tipo_contenido in ["audio", "video"]:
        return "speech"
    else:
        return "nlp"

# ==========================================
# Construcción del Grafo
# ==========================================

workflow = StateGraph(AgenteState)

# Nodos
workflow.add_node("intake", node_intake)
workflow.add_node("ocr", node_ocr)
workflow.add_node("speech", node_speech)
workflow.add_node("nlp", node_nlp)
workflow.add_node("correlation", node_correlation)
workflow.add_node("osint", node_osint)
workflow.add_node("risk", node_risk)
workflow.add_node("alert", node_alert)

# Entry point
workflow.set_entry_point("intake")

# Edges condicionales post-intake
workflow.add_conditional_edges(
    "intake",
    router_post_intake,
    {
        "ocr": "ocr",
        "speech": "speech",
        "nlp": "nlp",
        "end": END
    }
)

# Desde OCR -> NLP
workflow.add_edge("ocr", "nlp")

# Desde Speech -> NLP
workflow.add_edge("speech", "nlp")

# Desde NLP -> Correlation
workflow.add_edge("nlp", "correlation")

# Desde Correlation -> OSINT
workflow.add_edge("correlation", "osint")

# Desde OSINT -> Risk
workflow.add_edge("osint", "risk")

# Desde Risk -> Alert
workflow.add_edge("risk", "alert")

# Fin
workflow.add_edge("alert", END)

# Checkpoint en memoria (puede persistirse en PostgreSQL con LangGraph checkpointer)
memory_saver = MemorySaver()
agent_graph = workflow.compile(checkpointer=memory_saver)
