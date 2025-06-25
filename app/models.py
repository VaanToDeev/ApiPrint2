# models.py

from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    PROFESSOR = "professor"
    COORDENADOR = "coordenador"
    ADMIN = "admin"

class StatusEstudante(str, enum.Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"

class StatusTCC(str, enum.Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"

class StatusTarefa(str, enum.Enum):
    A_FAZER = "a_fazer"
    FAZENDO = "fazendo"
    REVISAR = "revisar"
    FEITA = "feita"
    CONCLUIDA = "concluida"

# NOVO: Enum para o status do Convite de Orientação
class StatusConvite(str, enum.Enum):
    PENDENTE = "pendente"
    ACEITO = "aceito"
    RECUSADO = "recusado"

class Professor(Base):
    __tablename__ = "professores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    siape = Column(String(50), unique=True, index=True, nullable=False)
    departamento = Column(String(100))
    titulacao = Column(String(100))
    telefone = Column(String(20), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.PROFESSOR, nullable=False)
    curso_coordenado = relationship("Curso", back_populates="coordenador", uselist=False)
    tccs_orientados = relationship("TCC", back_populates="orientador", foreign_keys="[TCC.orientador_id]")
    # NOVO: Relacionamento com convites enviados
    convites_enviados = relationship("OrientacaoConvite", back_populates="professor", foreign_keys="[OrientacaoConvite.professor_id]")


class Estudante(Base):
    __tablename__ = "estudantes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    matricula = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(SAEnum(StatusEstudante), default=StatusEstudante.ATIVO)
    turma = Column(String(50))
    telefone = Column(String(20), nullable=True)
    curso_id = Column(Integer, ForeignKey("cursos.id_curso"))
    curso = relationship("Curso", back_populates="estudantes")
    tccs = relationship("TCC", back_populates="estudante", foreign_keys="[TCC.estudante_id]")
    # NOVO: Relacionamento com convites recebidos
    convites_recebidos = relationship("OrientacaoConvite", back_populates="estudante", foreign_keys="[OrientacaoConvite.estudante_id]")

# NOVO: Modelo para armazenar convites de orientação
class OrientacaoConvite(Base):
    __tablename__ = "orientacao_convites"
    id = Column(Integer, primary_key=True, index=True)
    
    # Proposta de TCC
    titulo_proposto = Column(String(255), nullable=False)
    descricao_proposta = Column(Text, nullable=True)

    # Status e Timestamps
    status = Column(SAEnum(StatusConvite), default=StatusConvite.PENDENTE, nullable=False)
    data_convite = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_resposta = Column(DateTime, nullable=True)

    # Foreign Keys e Relacionamentos
    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    estudante_id = Column(Integer, ForeignKey("estudantes.id"), nullable=False)

    professor = relationship("Professor", back_populates="convites_enviados")
    estudante = relationship("Estudante", back_populates="convites_recebidos")


class Curso(Base):
    __tablename__ = "cursos"
    id_curso = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_curso = Column(String(100), unique=True, nullable=False)
    coordenador_id = Column(Integer, ForeignKey("professores.id"), unique=True, nullable=True)
    coordenador = relationship("Professor", back_populates="curso_coordenado")
    estudantes = relationship("Estudante", back_populates="curso")

class TCC(Base):
    __tablename__ = "tccs"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(SAEnum(StatusTCC), default=StatusTCC.EM_ANDAMENTO, nullable=False)
    estudante_id = Column(Integer, ForeignKey("estudantes.id"), nullable=False)
    orientador_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    estudante = relationship("Estudante", back_populates="tccs", foreign_keys=[estudante_id])
    orientador = relationship("Professor", back_populates="tccs_orientados", foreign_keys=[orientador_id])
    files = relationship("TCCFile", back_populates="tcc", cascade="all, delete-orphan")
    tarefas = relationship("Tarefa", back_populates="tcc", cascade="all, delete-orphan")

class Tarefa(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    data_entrega = Column(Date, nullable=True)
    status = Column(SAEnum(StatusTarefa), default=StatusTarefa.A_FAZER, nullable=False)
    tcc_id = Column(Integer, ForeignKey("tccs.id"), nullable=False)
    tcc = relationship("TCC", back_populates="tarefas")
    arquivos = relationship("Arquivo", back_populates="tarefa", cascade="all, delete-orphan")

class Arquivo(Base):
    __tablename__ = "arquivos"
    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(512), nullable=False)
    data_upload = Column(DateTime, default=datetime.utcnow, nullable=False)
    tarefa_id = Column(Integer, ForeignKey("tarefas.id"), nullable=False)
    tarefa = relationship("Tarefa", back_populates="arquivos")

class TCCFile(Base):
    __tablename__ = "tcc_files"
    id = Column(Integer, primary_key=True, index=True)
    tcc_id = Column(Integer, ForeignKey("tccs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    filetype = Column(String(100), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    tcc = relationship("TCC", back_populates="files")