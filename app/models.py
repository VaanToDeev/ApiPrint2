from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, CheckConstraint
from sqlalchemy.sql import func, case
import enum
from .database import Base

class UserType(str, enum.Enum):
    ALUNO = "aluno"
    PROFESSOR = "professor"
    COORDENADOR = "coordenador"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(200))
    hashed_password = Column(String(255))
    user_type = Column(Enum(UserType), nullable=False)
    matricula = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Adiciona uma constraint que garante que matrícula seja preenchida apenas para alunos
    __table_args__ = (
        CheckConstraint(
            "(user_type != 'aluno' AND matricula IS NULL) OR "
            "(user_type = 'aluno' AND matricula IS NOT NULL)",
            name='check_matricula_aluno'
        ),
    )