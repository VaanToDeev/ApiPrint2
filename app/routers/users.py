from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

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
    """Obter token de acesso"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.User)
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