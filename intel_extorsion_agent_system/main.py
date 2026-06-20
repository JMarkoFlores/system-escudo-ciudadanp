"""
Entry point - Servidor Uvicorn
"""
import uvicorn
from app.api.main_api import app
from app.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main_api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
