from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

# Importações principais que não causam ciclos
from app import models
from app.core.security import decode_access_token, verify_password
from app.database import get_db

# O import de 'crud' foi removido do topo para evitar importações circulares

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[models.Professor | models.Estudante]:
    """
    Autentica um usuário (professor ou estudante) e retorna o objeto do modelo se for bem-sucedido.
    """
    # Importação local para quebrar o ciclo de dependência
    from app import crud

    # Tenta encontrar um professor com o email fornecido
    professor = await crud.get_professor_by_email(db, email=email)
    if professor and verify_password(password, professor.hashed_password):
        return professor

    # Se não for um professor, tenta encontrar um estudante
    estudante = await crud.get_estudante_by_email(db, email=email)
    if estudante and verify_password(password, estudante.hashed_password):
        return estudante
    
    # Retorna None se a autenticação falhar
    return None

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.Professor | models.Estudante:
    """
    Decodifica o token JWT e retorna o usuário atual do banco de dados.
    """
    # Importação local para quebrar o ciclo de dependência
    from app import crud

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: Optional[str] = payload.get("sub")
    user_type: Optional[str] = payload.get("user_type")

    if email is None or user_type is None:
        raise credentials_exception
    
    user: Optional[models.Professor | models.Estudante] = None
    if user_type == "professor":
        user = await crud.get_professor_by_email(db, email=email)
    elif user_type == "estudante":
        user = await crud.get_estudante_by_email(db, email=email)
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.Professor | models.Estudante = Depends(get_current_user_from_token)):
    """
    Um dependente que verifica se o usuário atual está ativo.
    """
    if isinstance(current_user, models.Estudante) and current_user.status == models.StatusEstudante.INATIVO:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Estudante inativo.")
    return current_user

async def get_current_admin_user(current_user: models.Professor = Depends(get_current_active_user)):
    """
    Um dependente que verifica se o usuário atual é um Administrador.
    """
    if not isinstance(current_user, models.Professor) or current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (admin required)"
        )
    return current_user

async def get_current_coordenador_or_admin_user(current_user: models.Professor = Depends(get_current_active_user)):
    """
    Um dependente que verifica se o usuário atual é um Coordenador ou Administrador.
    """
    if not isinstance(current_user, models.Professor) or current_user.role not in [models.UserRole.ADMIN, models.UserRole.COORDENADOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (coordenador or admin required)"
        )
    return current_user
