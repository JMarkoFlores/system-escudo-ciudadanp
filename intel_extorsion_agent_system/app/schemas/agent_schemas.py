"""
Esquemas Pydantic para APIs y comunicación entre agentes
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid

class CanalEntrada(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEB = "web"
    API = "api"

class TipoContenido(str, Enum):
    TEXTO = "texto"
    IMAGEN = "imagen"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENTO = "documento"
    MIXTO = "mixto"

class NivelRiesgo(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"

# ==========================================
# Entradas / Payloads
# ==========================================

class DenunciaIngestaRequest(BaseModel):
    canal: CanalEntrada = Field(..., description="Canal por el que ingresó la denuncia")
    id_externo: Optional[str] = Field(None, description="ID del mensaje en el canal externo")
    did_denunciante: Optional[str] = Field(None, description="DID del denunciante si está autenticado")
    tipo_contenido: TipoContenido
    contenido_raw: Optional[str] = Field(None, description="Texto plano o transcripción preliminar")
    url_archivo: Optional[str] = Field(None, description="URL al archivo en almacenamiento")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProcesarDenunciaRequest(BaseModel):
    denuncia_id: uuid.UUID
    modo: Literal["completo", "selectivo"] = "completo"
    agentes: Optional[List[str]] = Field(None, description="Lista de agentes a ejecutar si modo=selectivo")

# ==========================================
# Estado del Grafo (LangGraph State)
# ==========================================

class AgenteState(BaseModel):
    """Estado compartido del grafo de agentes"""
    denuncia_id: uuid.UUID
    canal: CanalEntrada
    tipo_contenido: TipoContenido
    contenido_raw: Optional[str] = None
    url_archivo: Optional[str] = None
    hash_archivo: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Resultados parciales por agente
    resultado_intake: Optional[Dict[str, Any]] = None
    resultado_ocr: Optional[Dict[str, Any]] = None
    resultado_speech: Optional[Dict[str, Any]] = None
    resultado_nlp: Optional[Dict[str, Any]] = None
    resultado_correlacion: Optional[Dict[str, Any]] = None
    resultado_osint: Optional[Dict[str, Any]] = None
    resultado_riesgo: Optional[Dict[str, Any]] = None
    resultado_alerta: Optional[Dict[str, Any]] = None
    
    # Control de flujo
    errores: List[str] = Field(default_factory=list)
    saltar_agentes: List[str] = Field(default_factory=list)
    requiere_escalamiento: bool = False
    nivel_riesgo: Optional[NivelRiesgo] = None
    
    # Memoria conversacional (checkpoint)
    mensajes: List[Dict[str, Any]] = Field(default_factory=list)

# ==========================================
# Salidas por Agente
# ==========================================

class IntakeResult(BaseModel):
    agente: Literal["intake"] = "intake"
    valido: bool
    categoria_preliminar: Optional[str] = None
    prioridad_inicial: int = Field(1, ge=1, le=5)
    entidades_detectadas: List[Dict[str, Any]] = Field(default_factory=list)
    notas: Optional[str] = None

class OCRResult(BaseModel):
    agente: Literal["ocr"] = "ocr"
    texto_extraido: str
    idioma_detectado: Optional[str] = None
    confianza: float = Field(..., ge=0.0, le=1.0)
    entidades: List[Dict[str, Any]] = Field(default_factory=list)

class SpeechResult(BaseModel):
    agente: Literal["speech"] = "speech"
    transcripcion: str
    idioma_detectado: Optional[str] = None
    duracion_segundos: Optional[float] = None
    confianza: float = Field(..., ge=0.0, le=1.0)
    emocion_detectada: Optional[str] = None

class NLPResult(BaseModel):
    agente: Literal["nlp"] = "nlp"
    intencion: str
    sentimiento: str  # positivo, negativo, neutro, miedo, amenaza
    entidades: List[Dict[str, Any]] = Field(default_factory=list)
    resumen: str
    palabras_clave: List[str] = Field(default_factory=list)
    indicadores_extorsion: List[str] = Field(default_factory=list)
    score_amenaza: float = Field(..., ge=0.0, le=1.0)

class OSINTResult(BaseModel):
    agente: Literal["osint"] = "osint"
    telefonos: List[Dict[str, Any]] = Field(default_factory=list)
    cuentas_bancarias: List[Dict[str, Any]] = Field(default_factory=list)
    redes_sociales: List[Dict[str, Any]] = Field(default_factory=list)
    dispositivos: List[Dict[str, Any]] = Field(default_factory=list)
    fuentes_consultadas: List[str] = Field(default_factory=list)
    riesgo_osint: int = Field(1, ge=1, le=5)

class CorrelacionResult(BaseModel):
    agente: Literal["correlation"] = "correlation"
    correlaciones: List[Dict[str, Any]] = Field(default_factory=list)
    red_criminal_detectada: bool = False
    modus_operandi_id: Optional[str] = None
    score_red: float = Field(0.0, ge=0.0, le=1.0)

class RiskResult(BaseModel):
    agente: Literal["risk"] = "risk"
    nivel_riesgo: NivelRiesgo
    score_numerico: float = Field(..., ge=0.0, le=1.0)
    factores: List[str] = Field(default_factory=list)
    recomendacion_operativa: str
    requiere_accion_inmediata: bool = False

class AlertResult(BaseModel):
    agente: Literal["alert"] = "alert"
    alerta_generada: bool
    alerta_id: Optional[uuid.UUID] = None
    canales_notificacion: List[str] = Field(default_factory=list)
    mensaje_alerta: Optional[str] = None

# ==========================================
# Respuestas API
# ==========================================

class DenunciaResponse(BaseModel):
    id: uuid.UUID
    canal: str
    estado: str
    tipo_contenido: str
    created_at: datetime
    resultados: List[Dict[str, Any]] = Field(default_factory=list)

class EjecucionGrafoResponse(BaseModel):
    denuncia_id: uuid.UUID
    estado_final: str
    resultados: Dict[str, Any]
    tiempo_total_ms: int
    alertas_generadas: int
    errores: List[str]

class HealthCheckResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    componentes: Dict[str, str]
