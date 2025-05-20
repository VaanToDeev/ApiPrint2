from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
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
    full_name: str = Field(..., min_length=3)
    user_type: UserType

# Esquema para dados específicos de Aluno
class AlunoData(BaseModel):
    matricula: str = Field(..., max_length=20)
    curso: str
    periodo: int = Field(..., ge=1, le=10)
    turma: str

# Esquema para dados específicos de Professor
class ProfessorData(BaseModel):
    departamento: str
    disciplinas: List[str]
    titulacao: str

# Esquema para dados específicos de Coordenador
class CoordenadorData(ProfessorData):
    area_coordenacao: str
    inicio_mandato: datetime

# Esquema para criação de usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    aluno_data: Optional[AlunoData] = None
    professor_data: Optional[ProfessorData] = None
    coordenador_data: Optional[CoordenadorData] = None

    @validator('aluno_data', 'professor_data', 'coordenador_data')
    def validate_user_type_data(cls, v, values):
        user_type = values.get('user_type')
        if user_type == UserType.ALUNO and not isinstance(v, AlunoData):
            raise ValueError('Dados de aluno são obrigatórios para usuários do tipo aluno')
        elif user_type == UserType.PROFESSOR and not isinstance(v, ProfessorData):
            raise ValueError('Dados de professor são obrigatórios para usuários do tipo professor')
        elif user_type == UserType.COORDENADOR and not isinstance(v, CoordenadorData):
            raise ValueError('Dados de coordenador são obrigatórios para usuários do tipo coordenador')
        return v

# Esquema para retorno de usuário
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    aluno_data: Optional[AlunoData] = None
    professor_data: Optional[ProfessorData] = None
    coordenador_data: Optional[CoordenadorData] = None

    class Config:
        from_attributes = True

# Esquema para token de acesso
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para dados do token
class TokenData(BaseModel):
    email: Optional[str] = None

class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    
    class Config:
        from_attributes = True