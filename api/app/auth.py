from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .database import get_db
from . import models, schemas

# Carregar variáveis de ambiente
load_dotenv()

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "SUBSTITUA_POR_UMA_CHAVE_SECRETA_COMPLEXA")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para criptografia de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Endpoint para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

# Funções de utilidade para autenticação
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, login: str, password: str):
    """
    Autentica um usuário pelo email ou username e senha
    
    Args:
        db: Sessão do banco de dados
        login: Email ou username do usuário
        password: Senha do usuário
        
    Returns:
        User: O objeto usuário se autenticado ou False se não autenticado
    """
    # Tenta encontrar o usuário pelo email
    user = db.query(models.User).filter(models.User.email == login).first()
    
    # Se não encontrar pelo email, tenta pelo username
    if not user:
        user = db.query(models.User).filter(models.User.username == login).first()
    
    # Se não encontrar o usuário ou a senha estiver incorreta, retorna False
    if not user or not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        identifier: str = payload.get("sub")
        if identifier is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=identifier)
    except JWTError:
        raise credentials_exception
    
    # Verifica se o identificador é um email (contém @)
    if "@" in identifier:
        user = db.query(models.User).filter(models.User.email == identifier).first()
    else:
        user = db.query(models.User).filter(models.User.username == identifier).first()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user