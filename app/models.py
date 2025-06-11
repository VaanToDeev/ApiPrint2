from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey, DateTime, Text
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

# NOVO: Status para o TCC
class StatusTCC(str, enum.Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"

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
    # NOVO: Relacionamento com TCCs orientados
    tccs_orientados = relationship("TCC", back_populates="orientador", foreign_keys="[TCC.orientador_id]")

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
    # NOVO: Relacionamento com TCCs do estudante
    tccs = relationship("TCC", back_populates="estudante", foreign_keys="[TCC.estudante_id]")

class Curso(Base):
    __tablename__ = "cursos"

    id_curso = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_curso = Column(String(100), unique=True, nullable=False)
    coordenador_id = Column(Integer, ForeignKey("professores.id"), unique=True, nullable=True)
    coordenador = relationship("Professor", back_populates="curso_coordenado")
    estudantes = relationship("Estudante", back_populates="curso")

# NOVO: Modelo TCC
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
    
    files = relationship("TCCFile", back_populates="tcc")

# NOVO: Modelo TCCFile
class TCCFile(Base):
    __tablename__ = "tcc_files"
    
    id = Column(Integer, primary_key=True, index=True)
    tcc_id = Column(Integer, ForeignKey("tccs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    filetype = Column(String(100), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    tcc = relationship("TCC", back_populates="files")
