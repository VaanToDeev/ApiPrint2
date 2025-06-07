from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.models import UserRole, StatusEstudante # Import enums from models

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None # 'professor' or 'estudante'
    role: Optional[UserRole] = None # For professors: 'professor', 'coordenador', 'admin'

# Base User Schemas

class UserPublic(BaseModel):
    id: int
    nome: str
    email: str
    role: str | None = None  # Para professor/admin
    user_type: str           # "estudante" ou "professor"

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: EmailStr
    nome: str = Field(..., min_length=3, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20) # NOVO CAMPO: Telefone (opcional na base)

class UserCreateBase(UserBase):
    password: str = Field(..., min_length=8)

# Estudante Schemas
class EstudanteCreate(UserCreateBase):
    matricula: str = Field(..., min_length=5, max_length=20)
    turma: Optional[str] = None
    curso_id: Optional[int] = None # Will be FK
    # telefone já está em UserCreateBase

class EstudanteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    matricula: Optional[str] = None
    turma: Optional[str] = None
    status: Optional[StatusEstudante] = None
    curso_id: Optional[int] = None
    telefone: Optional[str] = Field(None, max_length=20) # NOVO CAMPO: Telefone

class EstudantePublic(UserBase):
    id: int
    matricula: str
    status: StatusEstudante
    turma: Optional[str] = None
    curso_id: Optional[int] = None
    # telefone já está em UserBase

    class Config:
        from_attributes = True # For SQLAlchemy model conversion (formerly orm_mode)

# Professor Schemas
class ProfessorCreate(UserCreateBase):
    siape: str = Field(..., min_length=6, max_length=20)
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: UserRole = UserRole.PROFESSOR # Default role
    # telefone já está em UserCreateBase

class ProfessorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    siape: Optional[str] = None
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: Optional[UserRole] = None
    telefone: Optional[str] = Field(None, max_length=20) # NOVO CAMPO: Telefone

class ProfessorPublic(UserBase):
    id: int
    siape: str
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: UserRole
    # telefone já está em UserBase

    class Config:
        from_attributes = True

# Curso Schemas
class CursoBase(BaseModel):
    nome_curso: str = Field(..., min_length=3, max_length=100)

class CursoCreate(CursoBase):
    pass

class CursoPublic(BaseModel):
    id_curso: int
    nome_curso: str
    coordenador: Optional[ProfessorPublic] = None  # Adicione esta linha

    class Config:
        orm_mode = True

class CursoUpdate(BaseModel):
    nome_curso: Optional[str] = None
    coordenador_id: Optional[int] = None


# Login Schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
