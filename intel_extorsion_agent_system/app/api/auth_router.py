"""
Router de autenticación para el dashboard policial.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models.db_session import get_db
from app.models.database import Usuario, RolUsuario
from app.services.auth_service import (
    authenticate_user, create_access_token, decode_token, get_user_by_username,
    list_users, create_user, update_user, delete_user
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre_completo: Optional[str] = None


class UserResponse(BaseModel):
    username: str
    rol: str
    nombre_completo: Optional[str] = None
    activo: bool = True

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    nombre_completo: Optional[str] = Field(None, max_length=100)
    rol: str = Field(..., pattern="^(admin|supervisor|analista)$")


class UserUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=100)
    rol: Optional[str] = Field(None, pattern="^(admin|supervisor|analista)$")
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    access_token = create_access_token(data={"sub": user.username, "rol": user.rol.value})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": user.rol.value,
        "nombre_completo": user.nombre_completo,
    }


@router.get("/me", response_model=UserResponse)
async def me(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = await get_user_by_username(db, payload["sub"])
    if not user or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    return {
        "username": user.username,
        "rol": user.rol.value,
        "nombre_completo": user.nombre_completo,
    }


async def get_current_user_optional(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        return None
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    return await get_user_by_username(db, payload["sub"])


async def require_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = await get_user_by_username(db, payload["sub"])
    if not user or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    return user


async def require_admin(current_user: Usuario = Depends(require_user)):
    """Solo administradores pueden realizar acciones de gestión de usuarios."""
    if current_user.rol != RolUsuario.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores pueden realizar esta acción")
    return current_user


# CRUD Endpoints for Users (Admin only)

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Listar todos los usuarios (solo admin)."""
    users = await list_users(db, skip=skip, limit=limit)
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_data: UserCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Crear un nuevo usuario (solo admin)."""
    try:
        user = await create_user(
            db,
            username=user_data.username,
            password=user_data.password,
            nombre_completo=user_data.nombre_completo,
            rol=user_data.rol
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/users/{username}", response_model=UserResponse)
async def update_user_endpoint(
    username: str,
    user_data: UserUpdate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar un usuario existente (solo admin)."""
    user = await update_user(
        db,
        username=username,
        nombre_completo=user_data.nombre_completo,
        rol=user_data.rol,
        activo=user_data.activo,
        password=user_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    username: str,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un usuario (solo admin)."""
    success = await delete_user(db, username)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return None
