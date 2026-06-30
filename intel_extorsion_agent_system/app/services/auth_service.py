"""
Servicio de autenticación JWT para el dashboard policial.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import settings
from app.models.database import Usuario, RolUsuario


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
    return bcrypt.checkpw(plain_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except PyJWTError:
        return None


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[Usuario]:
    result = await db.execute(select(Usuario).where(Usuario.username == username, Usuario.activo == True))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[Usuario]:
    result = await db.execute(select(Usuario).where(Usuario.username == username))
    return result.scalar_one_or_none()


async def seed_default_users(db: AsyncSession):
    """Crea usuarios por defecto si la tabla está vacía."""
    result = await db.execute(select(Usuario))
    if result.scalars().first():
        return

    defaults = [
        ("admin", settings.SEED_ADMIN_PASSWORD, "Administrador", RolUsuario.admin),
        ("supervisor", settings.SEED_SUPERVISOR_PASSWORD, "Supervisor", RolUsuario.supervisor),
        ("analista", settings.SEED_ANALISTA_PASSWORD, "Analista", RolUsuario.analista),
    ]
    for username, password, nombre, rol in defaults:
        db.add(Usuario(
            username=username,
            hashed_password=get_password_hash(password),
            nombre_completo=nombre,
            rol=rol,
            activo=True
        ))
    await db.commit()


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Usuario).offset(skip).limit(limit))
    return result.scalars().all()


async def create_user(db: AsyncSession, username: str, password: str, nombre_completo: Optional[str], rol: str) -> Usuario:
    existing = await get_user_by_username(db, username)
    if existing:
        raise ValueError(f"El usuario '{username}' ya existe")

    rol_enum = RolUsuario(rol.lower().strip())
    user = Usuario(
        username=username,
        hashed_password=get_password_hash(password),
        nombre_completo=nombre_completo,
        rol=rol_enum,
        activo=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    username: str,
    nombre_completo: Optional[str] = None,
    rol: Optional[str] = None,
    activo: Optional[bool] = None,
    password: Optional[str] = None
) -> Optional[Usuario]:
    user = await get_user_by_username(db, username)
    if not user:
        return None

    if nombre_completo is not None:
        user.nombre_completo = nombre_completo
    if rol is not None:
        user.rol = RolUsuario(rol.lower().strip())
    if activo is not None:
        user.activo = activo
    if password is not None:
        user.hashed_password = get_password_hash(password)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, username: str) -> bool:
    user = await get_user_by_username(db, username)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
