from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
from pydantic import BaseModel, EmailStr, Field

from .. import crud, models, schemas, auth
from ..database import get_db, engine
from ..schemas import UserType

# Criar o router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Criar tabelas no banco de dados
models.Base.metadata.create_all(bind=engine)

# Schemas para atualizações específicas
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class EmailUpdate(BaseModel):
    new_email: EmailStr
    password: str

class UsernameUpdate(BaseModel):
    new_username: str = Field(..., min_length=3, max_length=50)
    password: str

# Schema customizado para login com email
class EmailPasswordRequestForm(BaseModel):
    email: EmailStr
    password: str

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Cadastrar um novo usuário"""
    return crud.create_user(db=db, user=user)

@router.get("/alunos", response_model=List[schemas.User])
def read_alunos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Listar todos os alunos"""
    if current_user.user_type not in [UserType.PROFESSOR, UserType.COORDENADOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas professores e coordenadores podem listar alunos"
        )
    return crud.get_users_by_type(db, UserType.ALUNO, skip=skip, limit=limit)

@router.get("/professores", response_model=List[schemas.User])
def read_professores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Listar todos os professores"""
    if current_user.user_type != UserType.COORDENADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas coordenadores podem listar professores"
        )
    return crud.get_users_by_type(db, UserType.PROFESSOR, skip=skip, limit=limit)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Obter token de acesso usando o formulário OAuth2 padrão.
    
    O campo username pode conter um email ou nome de usuário.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Usar o email para o token, garantindo consistência
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
async def login_with_email(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Fazer login usando campos separados para email e senha"""
    user = auth.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/current_user", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Obter dados do usuário autenticado"""
    return current_user

@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Listar todos os usuários (apenas coordenador)"""
    if current_user.user_type != UserType.COORDENADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas coordenadores podem listar todos os usuários"
        )
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Obter um usuário específico pelo ID"""
    # Se não for coordenador, só pode ver seus próprios dados
    if current_user.user_type != UserType.COORDENADOR and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode ver seus próprios dados"
        )
    
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return db_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Atualizar um usuário"""
    # Se não for coordenador, só pode editar seus próprios dados
    if current_user.user_type != UserType.COORDENADOR and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode editar seus próprios dados"
        )
    
    # Não permitir alteração do tipo de usuário, exceto pelo coordenador
    if user.user_type is not None and current_user.user_type != UserType.COORDENADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas coordenadores podem alterar o tipo de usuário"
        )
    
    return crud.update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Remover um usuário (apenas coordenador)"""
    if current_user.user_type != UserType.COORDENADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas coordenadores podem remover usuários"
        )
    
    return crud.delete_user(db=db, user_id=user_id)

@router.put("/me/password", response_model=schemas.User)
async def update_password(
    password_update: PasswordUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualizar senha do usuário"""
    # Verificar senha atual
    if not auth.verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Atualizar senha
    return crud.update_user(
        db=db,
        user_id=current_user.id,
        user=schemas.UserUpdate(password=password_update.new_password)
    )

@router.put("/me/email", response_model=schemas.User)
async def update_email(
    email_update: EmailUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualizar email do usuário"""
    # Verificar senha
    if not auth.verify_password(email_update.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha incorreta"
        )
    
    # Verificar se o novo email já está em uso
    if crud.get_user_by_email(db, email=email_update.new_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Atualizar email
    return crud.update_user(
        db=db,
        user_id=current_user.id,
        user=schemas.UserUpdate(email=email_update.new_email)
    )

@router.put("/me/username", response_model=schemas.User)
async def update_username(
    username_update: UsernameUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Atualizar nome de usuário"""
    # Verificar senha
    if not auth.verify_password(username_update.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha incorreta"
        )
    
    # Verificar se o novo username já está em uso
    if crud.get_user_by_username(db, username=username_update.new_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já está em uso"
        )
    
    # Atualizar username
    return crud.update_user(
        db=db,
        user_id=current_user.id,
        user=schemas.UserUpdate(username=username_update.new_username)
    )