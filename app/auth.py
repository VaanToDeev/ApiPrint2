from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional # ADICIONADO: Importar Optional
from app import crud, models, schemas
from app.core.security import decode_access_token, verify_password, create_access_token
from app.database import get_db
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Matches the login route

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[models.Professor | models.Estudante]:
    # Try professor first
    professor = await crud.get_professor_by_email(db, email=email)
    if professor and verify_password(password, professor.hashed_password):
        return professor

    # Try estudante if professor not found or password mismatch
    estudante = await crud.get_estudante_by_email(db, email=email)
    if estudante and verify_password(password, estudante.hashed_password):
        return estudante
    
    return None

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.Professor | models.Estudante:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: Optional[str] = payload.get("sub") # Optional já estava sendo usado aqui
    user_type: Optional[str] = payload.get("user_type") # e aqui

    if email is None or user_type is None:
        raise credentials_exception
    
    user: Optional[models.Professor | models.Estudante] = None # E aqui
    if user_type == "professor":
        user = await crud.get_professor_by_email(db, email=email)
    elif user_type == "estudante":
        user = await crud.get_estudante_by_email(db, email=email)
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.Professor | models.Estudante = Depends(get_current_user_from_token)):
    # Add logic here if users can be "deactivated" in a way not covered by Estudante.status
    # For now, if they can log in, they are "active" in terms of authentication.
    # if hasattr(current_user, 'is_active') and not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    if isinstance(current_user, models.Estudante) and current_user.status == models.StatusEstudante.INATIVO:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Estudante inativo.")
    return current_user

async def get_current_admin_user(current_user: models.Professor = Depends(get_current_active_user)):
    if not isinstance(current_user, models.Professor) or current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (admin required)"
        )
    return current_user

async def get_current_coordenador_or_admin_user(current_user: models.Professor = Depends(get_current_active_user)):
    if not isinstance(current_user, models.Professor) or current_user.role not in [models.UserRole.ADMIN, models.UserRole.COORDENADOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (coordenador or admin required)"
        )
    return current_user
