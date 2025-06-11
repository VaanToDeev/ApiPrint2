from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, StatusEstudante, StatusTCC

# --- Schemas de Autenticação e Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[str] = None
    role: Optional[UserRole] = None

# --- Schemas Base de Usuário ---
class UserBase(BaseModel):
    email: EmailStr
    nome: str = Field(..., min_length=3, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)

class UserCreateBase(UserBase):
    password: str = Field(..., min_length=8)

# --- Schemas de Estudante ---
class EstudanteCreate(UserCreateBase):
    matricula: str = Field(..., min_length=5, max_length=20)
    turma: Optional[str] = None
    curso_id: Optional[int] = None

class EstudanteUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    turma: Optional[str] = None
    status: Optional[StatusEstudante] = None
    telefone: Optional[str] = Field(None, max_length=20)

class EstudantePublic(UserBase):
    id: int
    matricula: str
    status: StatusEstudante
    turma: Optional[str] = None
    curso_id: Optional[int] = None
    class Config:
        from_attributes = True

# --- Schemas de Professor ---
class ProfessorCreate(UserCreateBase):
    siape: str = Field(..., min_length=6, max_length=20)
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: UserRole = UserRole.PROFESSOR

class ProfessorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    siape: Optional[str] = None
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: Optional[UserRole] = None
    telefone: Optional[str] = Field(None, max_length=20)

class ProfessorPublic(UserBase):
    id: int
    siape: str
    departamento: Optional[str] = None
    titulacao: Optional[str] = None
    role: UserRole
    class Config:
        from_attributes = True

# --- Schemas de Curso ---
class CursoBase(BaseModel):
    nome_curso: str = Field(..., min_length=3, max_length=100)

class CursoCreate(CursoBase): # Garantindo que este schema existe
    pass

class CursoUpdate(CursoBase):
    coordenador_id: Optional[int] = None

class CursoPublic(CursoBase):
    id_curso: int
    coordenador_id: Optional[int] = None
    class Config:
        from_attributes = True

# --- Schemas de TCC ---
class TCCBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    estudante_id: int
    orientador_id: int

class TCCCreate(TCCBase):
    pass

class TCCPublic(TCCBase):
    id: int
    status: StatusTCC
    class Config:
        from_attributes = True

# --- Schemas de Arquivo de TCC ---
class TCCFileBase(BaseModel):
    tcc_id: int
    filename: str
    filepath: str
    filetype: str

class TCCFileCreate(TCCFileBase):
    pass

class TCCFilePublic(TCCFileBase):
    id: int
    upload_date: datetime
    class Config:
        from_attributes = True

# --- Schema de Login ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
