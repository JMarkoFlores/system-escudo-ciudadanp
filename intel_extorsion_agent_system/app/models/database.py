import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class EstadoDenuncia(str, enum.Enum):
    en_ingesta = "en_ingesta"
    en_analisis = "en_analisis"
    procesado = "procesado"
    correlacionado = "correlacionado"
    riesgo_evaluado = "riesgo_evaluado"
    alerta_generada = "alerta_generada"
    archivado = "archivado"

class NivelRiesgo(str, enum.Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"
    critico = "critico"

class Denuncia(Base):
    __tablename__ = "denuncias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canal = Column(String(50), nullable=False)
    id_externo = Column(String(100), nullable=True)
    did_denunciante = Column(String(100), nullable=True)
    tipo_contenido = Column(Enum(EstadoDenuncia), nullable=False, default=EstadoDenuncia.en_ingesta) # Wait, tipo_contenido is image/audio/text, wait. In main_api, tipo_contenido is enum or string? In agent_service line 36: tipo_contenido=req.tipo_contenido.value.
    # Ah! In main_api, tipo_contenido.value is returned.
    # Let's see: req.tipo_contenido in agent_schemas.py. Let's look at agent_schemas.py to see TipoContenido values.
    # We can just define tipo_contenido as String(50) or Enum, but String is safer in case of unexpected types. Let's use String(50) for tipo_contenido.
    tipo_contenido = Column(String(50), nullable=False)
    contenido_raw = Column(String, nullable=True)
    url_archivo = Column(String, nullable=True)
    hash_archivo = Column(String, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    tracking_code = Column(String(20), nullable=True, index=True)
    seal_tx_hash = Column(String(100), nullable=True)
    seal_block = Column(Integer, nullable=True)
    seal_status = Column(String(50), nullable=True)
    nivel_riesgo = Column(Enum(NivelRiesgo), nullable=True)
    estado = Column(Enum(EstadoDenuncia), nullable=False, default=EstadoDenuncia.en_ingesta)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    procesado_at = Column(DateTime, nullable=True)

    resultados = relationship("ResultadoAgente", back_populates="denuncia", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="denuncia", cascade="all, delete-orphan")

class ResultadoAgente(Base):
    __tablename__ = "resultados_agentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    denuncia_id = Column(UUID(as_uuid=True), ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False)
    agente = Column(String(50), nullable=False)
    resultado_json = Column(JSONB, nullable=False)
    exitoso = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    denuncia = relationship("Denuncia", back_populates="resultados")

class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    denuncia_id = Column(UUID(as_uuid=True), ForeignKey("denuncias.id", ondelete="CASCADE"), nullable=False)
    nivel = Column(Enum(NivelRiesgo), nullable=False)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(String, nullable=True)
    recomendacion = Column(String, nullable=True)
    zona = Column(String(100), nullable=True)
    tx_hash = Column(String(100), nullable=True)
    leida = Column(Boolean, default=False, nullable=False)
    atendida = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    denuncia = relationship("Denuncia", back_populates="alertas")

class MemoriaConversacional(Base):
    __tablename__ = "memoria_conversacional"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    content = Column(String, nullable=False)
    tool_calls = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
