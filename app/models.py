from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime # Import datetime

class UserRole(str, enum.Enum):
    PROFESSOR = "professor"
    COORDENADOR = "coordenador"
    ADMIN = "admin"

class StatusEstudante(str, enum.Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"

class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    siape = Column(String(50), unique=True, index=True, nullable=False)
    departamento = Column(String(100))
    titulacao = Column(String(100)) # e.g., Mestre, Doutor
    telefone = Column(String(20), nullable=True) # NOVO CAMPO: Telefone
    role = Column(SAEnum(UserRole), default=UserRole.PROFESSOR, nullable=False)

    # Relationship: Professor coordena Curso (um Professor pode coordenar 0 ou 1 Curso)
    curso_coordenado = relationship("Curso", back_populates="coordenador", uselist=False)
    # Add other relationships from ERD later e.g., TCCs orientados

    def __repr__(self):
        return f"<Professor(id={self.id}, nome='{self.nome}', email='{self.email}', role='{self.role.value}')>"


class Estudante(Base):
    __tablename__ = "estudantes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False) # Added nome, essential for a user
    email = Column(String(100), unique=True, index=True, nullable=False) # Added email for login
    hashed_password = Column(String(255), nullable=False) # Added for authentication
    matricula = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(SAEnum(StatusEstudante), default=StatusEstudante.ATIVO)
    turma = Column(String(50))
    telefone = Column(String(20), nullable=True) # NOVO CAMPO: Telefone

    curso_id = Column(Integer, ForeignKey("cursos.id_curso"))
    curso = relationship("Curso", back_populates="estudantes")
    # Add other relationships from ERD later e.g., TCCs

    def __repr__(self):
        return f"<Estudante(id={self.id}, nome='{self.nome}', email='{self.email}', matricula='{self.matricula}')>"

class Curso(Base):
    __tablename__ = "cursos"

    id_curso = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_curso = Column(String(100), unique=True, nullable=False)

    coordenador_id = Column(Integer, ForeignKey("professores.id"), unique=True, nullable=True) # Um curso pode ter um coordenador
    coordenador = relationship("Professor", back_populates="curso_coordenado")

    estudantes = relationship("Estudante", back_populates="curso")

    def __repr__(self):
        return f"<Curso(id_curso={self.id_curso}, nome_curso='{self.nome_curso}')>"

# TODO: Add TCC, DocumentoApoio, ChecklistTCC models later


# Novo modelo TCC adicionado
class TCC(Base):
    __tablename__ = "tccs"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(String(1000), nullable=True)
    ano = Column(Integer, nullable=False)

    estudante_id = Column(Integer, ForeignKey("estudantes.id"), nullable=False)
    estudante = relationship("Estudante", back_populates="tccs")

    orientador_id = Column(Integer, ForeignKey("professores.id"), nullable=False)
    orientador = relationship("Professor", back_populates="orientacoes_tcc")

    files = relationship("TCCFile", back_populates="tcc", cascade="all, delete-orphan") # Relationship to TCC files

    def __repr__(self):
        return f"<TCC(id={self.id}, titulo='{self.titulo}')>"

# Novo modelo TCCFile
class TCCFile(Base):
    __tablename__ = "tcc_files"

    id = Column(Integer, primary_key=True, index=True)
    tcc_id = Column(Integer, ForeignKey("tccs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False) # Path where the file is stored
    filetype = Column(String(50), nullable=False) # e.g., 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    
    tcc = relationship("TCC", back_populates="files")

    def __repr__(self):
        return f"<TCCFile(id={self.id}, filename='{self.filename}', tcc_id={self.tcc_id})>"