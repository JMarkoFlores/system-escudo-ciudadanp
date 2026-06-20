"""
Tools compartidas para los agentes (LangChain Tools)
"""
from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import httpx
from app.config.settings import settings

# ==========================================
# Tool: Guardar Resultado en PostgreSQL
# ==========================================

class GuardarResultadoInput(BaseModel):
    denuncia_id: str = Field(..., description="UUID de la denuncia")
    agente: str = Field(..., description="Nombre del agente")
    resultado_json: dict = Field(..., description="Resultado estructurado")
    tokens_consumidos: Optional[int] = Field(None)
    tiempo_ms: Optional[int] = Field(None)
    exitoso: bool = Field(True)
    error_msg: Optional[str] = Field(None)

class GuardarResultadoTool(BaseTool):
    name: str = "guardar_resultado_db"
    description: str = "Guarda el resultado del procesamiento de un agente en PostgreSQL"
    args_schema: Type[BaseModel] = GuardarResultadoInput
    
    async def _arun(self, **kwargs):
        # Inyección de sesión DB real se hace desde el servicio
        return {"status": "ok", "saved": True}
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: Buscar Casos Similares (Qdrant)
# ==========================================

class BuscarSimilaresInput(BaseModel):
    query: str = Field(..., description="Texto de búsqueda semántica")
    denuncia_id_excluir: Optional[str] = Field(None)
    limit: int = Field(5, ge=1, le=20)

class BuscarSimilaresTool(BaseTool):
    name: str = "buscar_casos_similares"
    description: str = "Busca casos históricos similares usando embeddings vectoriales en Qdrant"
    args_schema: Type[BaseModel] = BuscarSimilaresInput
    
    async def _arun(self, query: str, denuncia_id_excluir: Optional[str] = None, limit: int = 5):
        from app.memory.hybrid_memory import memory_system
        results = await memory_system.search_similar_cases(query, denuncia_id_excluir, limit)
        return {"resultados": results}
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: Consultar OSINT Externo
# ==========================================

class OSINTLookupInput(BaseModel):
    telefono: Optional[str] = Field(None)
    cuenta_bancaria: Optional[str] = Field(None)
    alias: Optional[str] = Field(None)
    email: Optional[str] = Field(None)

class OSINTLookupTool(BaseTool):
    name: str = "consultar_osint"
    description: str = "Consulta fuentes OSINT para enriquecer información de un sujeto (teléfono, cuenta, alias)"
    args_schema: Type[BaseModel] = OSINTLookupInput
    
    async def _arun(self, telefono: Optional[str] = None, cuenta_bancaria: Optional[str] = None, alias: Optional[str] = None, email: Optional[str] = None):
        # Implementación real integraría APIs externas (HaveIBeenPwned, etc.)
        # Aquí simulamos respuesta estructurada
        resultados = {}
        if telefono:
            resultados["telefono"] = {"reportes": 3, "primer_reporte": "2024-01-15", "riesgo": "alto"}
        if cuenta_bancaria:
            resultados["cuenta_bancaria"] = {"entidad": "Banco X", "reportes": 1, "riesgo": "medio"}
        if alias:
            resultados["alias"] = {"redes": ["instagram", "telegram"], "riesgo": "alto"}
        return resultados
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: OCR Remoto
# ==========================================

class OCRInput(BaseModel):
    image_url: str = Field(..., description="URL de la imagen a procesar")
    idioma: Optional[str] = Field("spa", description="Código ISO del idioma")

class OCRTool(BaseTool):
    name: str = "extraer_texto_ocr"
    description: str = "Extrae texto de una imagen usando OCR (Tesseract)"
    args_schema: Type[BaseModel] = OCRInput
    
    async def _arun(self, image_url: str, idioma: str = "spa"):
        from app.services.ocr_service import extract_text_from_image
        return await extract_text_from_image(image_url, idioma=idioma)
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: Transcripción de Audio
# ==========================================

class TranscribirAudioInput(BaseModel):
    audio_url: str = Field(..., description="URL del archivo de audio")
    idioma: Optional[str] = Field("es", description="Idioma esperado")

class TranscribirAudioTool(BaseTool):
    name: str = "transcribir_audio"
    description: str = "Transcribe un archivo de audio a texto usando Groq Whisper"
    args_schema: Type[BaseModel] = TranscribirAudioInput
    
    async def _arun(self, audio_url: str, idioma: str = "es"):
        from app.services.stt_service import transcribe_audio
        return await transcribe_audio(audio_url, idioma=idioma)
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: Emitir Alerta
# ==========================================

class EmitirAlertaInput(BaseModel):
    denuncia_id: str = Field(...)
    nivel: str = Field(..., description="bajo, medio, alto, critico")
    titulo: str = Field(...)
    descripcion: str = Field(...)
    recomendacion: Optional[str] = Field(None)

class EmitirAlertaTool(BaseTool):
    name: str = "emitir_alerta"
    description: str = "Emite una alerta oficial al sistema de inteligencia policial"
    args_schema: Type[BaseModel] = EmitirAlertaInput
    
    async def _arun(self, denuncia_id: str, nivel: str, titulo: str, descripcion: str, recomendacion: Optional[str] = None):
        # Persistir en DB y enviar a webhook/email
        return {
            "alerta_id": "alert-uuid-123",
            "emitida": True,
            "canales": ["dashboard", "webhook"]
        }
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# ==========================================
# Tool: Consultar Denuncia Existente
# ==========================================

class ConsultarDenunciaInput(BaseModel):
    denuncia_id: str = Field(...)

class ConsultarDenunciaTool(BaseTool):
    name: str = "consultar_denuncia_db"
    description: str = "Consulta los datos completos de una denuncia y sus resultados previos"
    args_schema: Type[BaseModel] = ConsultarDenunciaInput
    
    async def _arun(self, denuncia_id: str):
        # Se inyecta DB real desde el servicio
        return {"denuncia_id": denuncia_id, "datos": "..."}
    
    def _run(self, **kwargs):
        raise NotImplementedError("Usar versión async")

# Registry de tools compartidas
AGENT_TOOLS = {
    "guardar_resultado": GuardarResultadoTool(),
    "buscar_similares": BuscarSimilaresTool(),
    "consultar_osint": OSINTLookupTool(),
    "extraer_ocr": OCRTool(),
    "transcribir_audio": TranscribirAudioTool(),
    "emitir_alerta": EmitirAlertaTool(),
    "consultar_denuncia": ConsultarDenunciaTool(),
}
