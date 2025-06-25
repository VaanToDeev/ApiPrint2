from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from app.models import UserRole, StatusEstudante, StatusTCC, StatusTarefa, StatusConvite

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

class CursoCreate(CursoBase):
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

class TCCCreate(TCCBase):
    estudante_id: int

class TCCPublic(TCCBase):
    id: int
    status: StatusTCC
    estudante_id: int
    orientador_id: int
    class Config:
        from_attributes = True

class TCCDetailsPublic(TCCPublic):
    estudante: EstudantePublic
    orientador: ProfessorPublic
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

class ArquivoBase(BaseModel):
    nome_arquivo: str
    caminho_arquivo: str

class ArquivoCreate(ArquivoBase):
    pass

class ArquivoPublic(ArquivoBase):
    id: int
    data_upload: datetime
    tarefa_id: int
    class Config:
        from_attributes = True

# --- Schema de Login ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Schemas de Tarefa ---
class TarefaBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=255)
    descricao: Optional[str] = None
    data_entrega: Optional[date] = None

class TarefaCreate(TarefaBase):
    pass

class TarefaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=255)
    descricao: Optional[str] = None
    data_entrega: Optional[date] = None
    status: Optional[StatusTarefa] = None

class TarefaPublic(TarefaBase):
    id: int
    tcc_id: int
    status: StatusTarefa
    arquivos: List[ArquivoPublic] = []
    class Config:
        from_attributes = True

# --- NOVO: Schemas de Convite de Orientação ---
class ConviteOrientacaoBase(BaseModel):
    titulo_proposto: str = Field(..., min_length=10, max_length=255)
    descricao_proposta: Optional[str] = None

class ConviteOrientacaoCreate(ConviteOrientacaoBase):
    estudante_id: int

class ConviteOrientacaoUpdate(BaseModel):
    status: StatusConvite # O aluno só poderá mudar para ACEITO ou RECUSADO

class ConviteOrientacaoPublic(ConviteOrientacaoBase):
    id: int
    status: StatusConvite
    data_convite: datetime
    data_resposta: Optional[datetime] = None
    professor: ProfessorPublic
    estudante: EstudantePublic

    class Config:
        from_attributes = True