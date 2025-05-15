from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from . import models, schemas, auth
from .schemas import UserType

def is_coordenador(user: models.User) -> bool:
    return user.user_type == models.UserType.COORDENADOR

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_users_by_type(db: Session, user_type: UserType, skip: int = 0, limit: int = 100):
    return db.query(models.User).filter(models.User.user_type == user_type).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # Verificar se o e-mail já está em uso
    db_user_email = get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado"
        )
    
    # Verificar se o nome de usuário já está em uso
    db_user_username = get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já registrado"
        )
    
    # Verificar se já existe um coordenador (só pode haver um)
    if user.user_type == UserType.COORDENADOR:
        existing_coord = db.query(models.User).filter(
            models.User.user_type == models.UserType.COORDENADOR
        ).first()
        if existing_coord:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um coordenador registrado no sistema"
        )
    
    # Criar novo usuário
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        user_type=user.user_type,
        hashed_password=hashed_password
    )
    
    # Salvar no banco de dados
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Atualizar campos se fornecidos
    update_data = user.dict(exclude_unset=True)
    
    # Se a senha for atualizada, hash ela
    if "password" in update_data:
        update_data["hashed_password"] = auth.get_password_hash(update_data.pop("password"))
    
    # Se o email for atualizado, verificar se já existe
    if "email" in update_data and update_data["email"] != db_user.email:
        if get_user_by_email(db, update_data["email"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já registrado"
            )
    
    # Se o username for atualizado, verificar se já existe
    if "username" in update_data and update_data["username"] != db_user.username:
        if get_user_by_username(db, update_data["username"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de usuário já registrado"
            )
    
    # Atualizar o usuário
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    db.delete(db_user)
    db.commit()
    return {"message": "Usuário removido com sucesso"}