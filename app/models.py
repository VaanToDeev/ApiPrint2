from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy import Enum
from .schemas import UserType

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(255))
    user_type = Column(Enum(UserType), nullable=False)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    aluno = relationship("Aluno", back_populates="user", uselist=False)
    professor = relationship("Professor", back_populates="user", uselist=False)
    coordenador = relationship("Coordenador", back_populates="user", uselist=False)

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    matricula = Column(String(20), unique=True, index=True)
    curso = Column(String(100))
    periodo = Column(Integer)
    turma = Column(String(50))

    user = relationship("User", back_populates="aluno")

class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    departamento = Column(String(100))
    disciplinas = Column(JSON)  # Lista de disciplinas como JSON
    titulacao = Column(String(100))

    user = relationship("User", back_populates="professor")

class Coordenador(Base):
    __tablename__ = "coordenadores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    professor_id = Column(Integer, ForeignKey('professores.id'), unique=True)
    area_coordenacao = Column(String(100))
    inicio_mandato = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="coordenador")
    professor = relationship("Professor")