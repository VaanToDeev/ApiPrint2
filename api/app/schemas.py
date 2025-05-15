from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"
    COORDENADOR = "coordenador"

# Esquema base para usuário
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    user_type: UserType
    matricula: Optional[str] = Field(None, max_length=20)

    @validator('matricula')
    def validate_matricula(cls, v, values):
        if 'user_type' in values and values['user_type'] == UserType.ALUNO and not v:
            raise ValueError('Matrícula é obrigatória para alunos')
        if 'user_type' in values and values['user_type'] != UserType.ALUNO and v:
            raise ValueError('Matrícula só pode ser preenchida para alunos')
        return v

# Esquema para criação de usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Esquema para atualização de usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    user_type: Optional[UserType] = None
    matricula: Optional[str] = Field(None, max_length=20)

    @validator('matricula')
    def validate_matricula(cls, v, values):
        if 'user_type' in values and values['user_type'] == UserType.ALUNO and v is None:
            raise ValueError('Matrícula é obrigatória para alunos')
        if 'user_type' in values and values['user_type'] != UserType.ALUNO and v is not None:
            raise ValueError('Matrícula só pode ser preenchida para alunos')
        return v

# Esquema para retorno de usuário
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Esquema para token de acesso
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para dados do token
class TokenData(BaseModel):
    username: Optional[str] = None