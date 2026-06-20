"""
Script de utilidades: Inicializar base de datos, verificar conexiones
"""
import asyncio
import sys
from app.models.db_session import async_engine, init_db
from app.memory.hybrid_memory import memory_system
from app.config.settings import settings

async def check_postgres():
    from sqlalchemy import text
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    print("✅ PostgreSQL: Conexión exitosa")

async def check_qdrant():
    collections = [c.name for c in memory_system.qdrant.get_collections().collections]
    print(f"✅ Qdrant: Conectado. Collections: {collections}")

async def init_all():
    print("🚀 Inicializando IntelExtorsión Agent System...")
    await check_postgres()
    await check_qdrant()
    await init_db()
    print("✅ Tablas creadas en PostgreSQL")
    print("✅ Colección Qdrant verificada")
    print("🎯 Sistema listo para operar")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        asyncio.run(init_all())
    else:
        print("Uso: python scripts/setup.py init")
