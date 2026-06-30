from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.models.database import Base

async_engine = create_async_engine(settings.async_database_url, echo=settings.DEBUG)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with async_engine.begin() as conn:
        # Sincronizar valores del enum EstadoDenuncia sin depender de recrear la BD
        await conn.exec_driver_sql(
            """
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estadodenuncia') THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_enum e
                        JOIN pg_type t ON e.enumtypid = t.oid
                        WHERE t.typname = 'estadodenuncia'
                          AND e.enumlabel = 'error_procesamiento'
                    ) THEN
                        ALTER TYPE estadodenuncia ADD VALUE IF NOT EXISTS 'error_procesamiento';
                    END IF;
                END IF;
            END $$;
            """
        )
        await conn.run_sync(Base.metadata.create_all)
