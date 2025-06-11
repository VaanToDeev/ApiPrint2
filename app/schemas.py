from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.models import UserRole, StatusEstudante # Import enums from models
import enum

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
    nome: str
    email: str
    matricula: str
    status: str  # Mantém como string, mas garanta que no endpoint converte para string
    turma: Optional[str]
    telefone: Optional[str]
    curso_id: int
    orientador_id: Optional[int]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # Garante que status Enum vira string
        data = super().from_orm(obj)
        if hasattr(data, "status") and isinstance(data.status, enum.Enum):
            data.status = data.status.value
        return data # For SQLAlchemy model conversion (formerly orm_mode)

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


# TCC Schemas adicionado
class TCCBase(BaseModel):
    titulo: str = Field(..., min_length=5, max_length=255)
    descricao: Optional[str] = Field(None, max_length=1000)
    ano: int = Field(..., gt=1900, lt=2100) # Assuming a reasonable range for year

class TCCCreate(TCCBase):
    estudante_id: int
    orientador_id: int

class TCCPublic(TCCBase):
    id: int
    estudante_id: int
    orientador_id: int
    # Optionally include full student/orientador objects for more detail
    # estudante: EstudantePublic
    # orientador: ProfessorPublic

    class Config:
        from_attributes = True

# TCC File Schemas
class TCCFilePublic(BaseModel):
    id: int
    tcc_id: int
    filename: str
    filepath: str
    filetype: str
    upload_date: datetime

    class Config:
        from_attributes = True

class TCCFileUpload(BaseModel):
    # This schema is mainly for documentation, actual file comes as UploadFile
    pass