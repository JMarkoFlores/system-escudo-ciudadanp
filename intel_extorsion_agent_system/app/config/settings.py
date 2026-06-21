"""
IntelExtorsión Agent System - Configuración Centralizada
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Aplicación
    APP_NAME: str = "IntelExtorsion-Agent-System"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # GroqCloud
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.2
    GROQ_MAX_TOKENS: int = 4096
    
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "intel_extorsion"
    POSTGRES_USER: str = "agent_user"
    POSTGRES_PASSWORD: str = "agent_pass"
    DATABASE_URL: Optional[str] = None
    
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def sync_database_url(self) -> str:
        return self.async_database_url.replace("+asyncpg", "+psycopg2")
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_DENUNCIAS: str = "denuncias_embeddings_v2"
    QDRANT_DIMENSION: int = 384  # sentence-transformers/all-MiniLM-L6-v2
    
    # LangGraph / Memory
    REDIS_URL: str = "redis://localhost:6379/0"
    MEMORY_MAX_TOKENS: int = 8000
    
    # Agent Configuration
    AGENT_MAX_RETRIES: int = 3
    AGENT_TIMEOUT_SECONDS: int = 120
    
    # OSINT
    OSINT_ENABLED: bool = True
    OSINT_MAX_REQUESTS_PER_MINUTE: int = 30
    
    # Web3 Backend
    WEB3_BACKEND_URL: str = "http://web3-backend:8001"
    
    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    UPLOAD_MAX_SIZE_MB: int = 50
    ALLOWED_MIME_TYPES: list = ["image/jpeg", "image/png", "image/webp", "application/pdf", "audio/mpeg", "audio/ogg", "audio/wav", "video/mp4", "text/plain"]

    # Alertas
    ALERT_WEBHOOK_URL: Optional[str] = None
    ALERT_EMAIL_SMTP_HOST: Optional[str] = None
    ALERT_EMAIL_FROM: Optional[str] = None
    
    # Canales
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    DISCORD_BOT_TOKEN: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
