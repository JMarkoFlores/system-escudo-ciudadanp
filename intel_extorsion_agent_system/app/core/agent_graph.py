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
from app.agents.seal_agent import node_seal
from app.agents.respond_agent import node_respond
from app.nlp.ner_engine import ner_engine

# ==========================================
# LLM Configuración (Lazy) + Mock para tests
# ==========================================
_llm = None

class MockLLM:
    """LLM determinista para tests/CI sin consumir tokens de Groq."""

    _responses = {
        "intake": {
            "valido": True,
            "categoria_preliminar": "Extorsión telefónica / secuestro virtual",
            "prioridad_inicial": 5,
            "entidades_detectadas": [
                {"tipo": "telefono", "valor": "999888777", "confianza": 0.9},
                {"tipo": "monto", "valor": "5000 soles", "confianza": 0.8},
            ],
            "notas": "Caso válido para análisis forense",
        },
        "ocr": {
            "texto_extraido": "Texto de prueba extraído por OCR",
            "estructurado": True,
            "entidades": [],
        },
        "speech": {
            "transcripcion": "Llamada extorsiva pidiendo dinero",
            "estructurado": True,
            "entidades": [],
        },
        "nlp": {
            "intencion": "extorsion",
            "sentimiento": "amenaza",
            "entidades": [
                {"tipo": "telefono", "valor": "999888777", "inicio": 0, "fin": 9},
                {"tipo": "moneda", "valor": "soles", "inicio": 10, "fin": 15},
                {"tipo": "monto", "valor": "5000", "inicio": 5, "fin": 9},
            ],
            "resumen": "Denuncia de extorsión telefónica por secuestro virtual.",
            "palabras_clave": ["extorsión", "secuestro", "dinero"],
            "indicadores_extorsion": ["plazo", "monto", "amenaza"],
            "score_amenaza": 0.8,
        },
        "correlation": {
            "correlaciones": [
                {
                    "denuncia_relacionada_id": "DEN-2024-001",
                    "score_similitud": 0.82,
                    "tipo_match": "telefono",
                    "evidencia_match": "Mismo número reportado previamente",
                }
            ],
            "red_criminal_detectada": True,
            "modus_operandi_id": "MOD-001",
            "score_red": 0.75,
            "recomendacion_investigativa": "Investigar número y alertar a la población",
        },
        "osint": {
            "telefonos": [{"numero": "999888777", "reportes_previos": 3, "riesgo": "Alto", "fuentes": ["test"]}],
            "cuentas_bancarias": [],
            "redes_sociales": [],
            "dispositivos": [],
            "fuentes_consultadas": ["test"],
            "riesgo_osint": 3,
            "observaciones": "Número con reportes previos de extorsión",
        },
        "risk": {
            "nivel_riesgo": "ALTO",
            "score_numerico": 0.85,
            "factores": ["Amenaza explícita", "Monto elevado", "Recurrencia"],
            "recomendacion_operativa": "Escalar a unidad de inteligencia",
            "requiere_accion_inmediata": True,
            "tiempo_respuesta_sugerido_minutos": 30,
        },
        "alert": {
            "alerta_generada": True,
            "alerta_id": "ALERT-TEST-001",
            "nivel": "ALTO",
            "titulo": "Alerta de extorsión alta",
            "descripcion": "Caso de extorsión telefónica con alto riesgo",
            "recomendacion": "Investigar de inmediato",
            "mensaje_alerta": "Alerta test",
            "canales_notificacion": ["push"],
        },
        "respond": {
            "enviado": True,
            "tracking_code": "TRJ-TEST",
            "mensaje_ciudadano": "Denuncia registrada con código TRJ-TEST01",
        },
    }

    def _detect_agent(self, messages: List[Dict[str, Any]]) -> str:
        system = ""
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
                break
        system = system.lower()
        for agent in self._responses:
            if agent in system:
                return agent
        # Fallback por contenido de mensajes
        user = ""
        for m in messages:
            if m.get("role") == "user":
                user += m.get("content", "")
        user = user.lower()
        if "intake" in user:
            return "intake"
        if "ocr" in user or "tesseract" in user:
            return "ocr"
        if "speech" in user or "whisper" in user:
            return "speech"
        if "risk" in user or "riesgo" in user:
            return "risk"
        if "alert" in user:
            return "alert"
        if "correlation" in user or "correlaci" in user:
            return "correlation"
        if "osint" in user:
            return "osint"
        if "respond" in user or "trj" in user:
            return "respond"
        return "nlp"

    async def ainvoke(self, messages, **kwargs):
        from langchain_core.messages import AIMessage
        agent = self._detect_agent(messages)
        return AIMessage(content=json.dumps(self._responses[agent], ensure_ascii=False))


def get_llm():
    global _llm
    if _llm is None:
        if settings.MOCK_LLM or not settings.GROQ_API_KEY:
            _llm = MockLLM()
        else:
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
    
    updates = {
        "resultado_intake": result,
        "mensajes": [{"role": "assistant", "content": response.content}]
    }
    
    if not result.get("valido", True):
        updates["saltar_agentes"] = ["ocr", "speech", "nlp", "correlation", "osint", "risk", "alert"]
        updates["errores"] = [f"Intake rechazado: {result.get('notas', 'Sin justificación')}"]
    
    return updates

async def node_ocr(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 2: OCR Agent
    Procesa imágenes/documentos usando Tesseract OCR + LLM para estructuración.
    """
    if "ocr" in state.saltar_agentes or state.tipo_contenido not in ["imagen", "documento", "mixto"]:
        return {"resultado_ocr": None}
    
    from app.services.ocr_service import extract_text_from_image

    ocr_result = {}
    if state.url_archivo:
        ocr_result = await extract_text_from_image(state.url_archivo, idioma="spa")
    
    prompt = AGENT_PROMPTS["ocr"]
    user_msg = (
        f"URL del archivo: {state.url_archivo}\n"
        f"Hash: {state.hash_archivo}\n"
        f"Texto extraído por Tesseract OCR:\n{ocr_result.get('texto_extraido', 'Sin texto extraído')}\n"
        f"Confianza OCR: {ocr_result.get('confianza', 0)}"
    )
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    result["tesseract_raw"] = ocr_result
    
    return {"resultado_ocr": result}

async def node_speech(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 3: Speech Agent
    Transcribe audio usando Groq Whisper + LLM para análisis forense.
    """
    if "speech" in state.saltar_agentes or state.tipo_contenido not in ["audio", "video", "mixto"]:
        return {"resultado_speech": None}
    
    from app.services.stt_service import transcribe_audio

    stt_result = {}
    if state.url_archivo:
        stt_result = await transcribe_audio(state.url_archivo, idioma="es")
    
    prompt = AGENT_PROMPTS["speech"]
    user_msg = (
        f"URL del audio: {state.url_archivo}\n"
        f"Duración estimada: {state.metadata.get('duracion_seg', stt_result.get('duracion_segundos', 'desconocida'))}\n"
        f"Transcripción Groq Whisper:\n{stt_result.get('transcripcion', 'Sin transcripción')}\n"
        f"Confianza STT: {stt_result.get('confianza', 0)}"
    )
    
    messages = _build_messages(prompt, user_msg, state)
    response = await get_llm().ainvoke(messages)
    result = _parse_llm_json(response.content)
    result["whisper_raw"] = stt_result
    
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

async def node_cluster(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 5.5: Cluster / NLP Forense Agent
    Extrae entidades forenses y detecta zonas usando NER especializado.
    Se ejecuta entre correlation y osint.
    """
    if "cluster" in state.saltar_agentes:
        return {"resultado_cluster": None}
    
    # Consolidar texto de todas las fuentes
    textos = []
    if state.contenido_raw:
        textos.append(state.contenido_raw)
    if state.resultado_ocr:
        textos.append(state.resultado_ocr.get("texto_extraido", ""))
    if state.resultado_speech:
        textos.append(state.resultado_speech.get("transcripcion", ""))
    
    texto_completo = "\n".join(textos) if textos else ""
    
    # Ejecutar NER forense
    ner_result = ner_engine.extract_entities(texto_completo)
    
    return {
        "resultado_cluster": ner_result,
        "zona_detectada": ner_result.get("zona_detectada"),
    }

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
    
    nivel = result.get("nivel_riesgo", "bajo")
    if isinstance(nivel, str):
        nivel = nivel.lower().strip()
    
    return {
        "resultado_riesgo": result,
        "nivel_riesgo": NivelRiesgo(nivel),
        "requiere_escalamiento": nivel in ["alto", "critico"]
    }

async def node_alert(state: AgenteState) -> Dict[str, Any]:
    """
    NODO 8: Alert Agent
    Emite alertas si el riesgo es alto/crítico y hace push SSE al dashboard.
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
    
    # Push SSE al dashboard
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"http://{settings.API_HOST}:{settings.API_PORT}/v1/dashboard/push",
                json={
                    "tipo": "alerta",
                    "denuncia_id": str(state.denuncia_id),
                    "nivel": nivel,
                    "zona": state.zona_detectada or riesgo.get("zona_detectada"),
                    "tracking_code": state.tracking_code,
                    "seal_tx_hash": state.seal_tx_hash,
                    "mensaje": result.get("descripcion", ""),
                },
                timeout=2.0
            )
    except Exception:
        pass
    
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
    if state.tipo_contenido in ["imagen", "documento", "mixto"]:
        return "ocr"
    elif state.tipo_contenido in ["audio", "video"]:
        return "speech"
    else:
        return "nlp"

def router_post_risk(state: AgenteState) -> str:
    """Después de risk, sella TODAS las evidencias en blockchain para preservar cadena de custodia"""
    return "seal"

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
workflow.add_node("cluster", node_cluster)
workflow.add_node("osint", node_osint)
workflow.add_node("risk", node_risk)
workflow.add_node("seal", node_seal)
workflow.add_node("alert", node_alert)
workflow.add_node("respond", node_respond)

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

# Desde Correlation -> Cluster -> OSINT
workflow.add_edge("correlation", "cluster")
workflow.add_edge("cluster", "osint")

# Desde OSINT -> Risk
workflow.add_edge("osint", "risk")

# Desde Risk -> [seal | respond] según nivel de riesgo
workflow.add_conditional_edges(
    "risk",
    router_post_risk,
    {
        "seal": "seal",
        "respond": "respond"
    }
)

# Desde Seal -> Alert (solo si riesgo ALTO/CRÍTICO)
workflow.add_edge("seal", "alert")

# Desde Alert -> Respond
workflow.add_edge("alert", "respond")

# Fin
workflow.add_edge("respond", END)

# Checkpoint en memoria (puede persistirse en PostgreSQL con LangGraph checkpointer)
memory_saver = MemorySaver()
agent_graph = workflow.compile(checkpointer=memory_saver)
