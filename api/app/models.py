from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy import Enum
from .schemas import UserType

# ...existing code...

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, index=True)  # Defina um tamanho, ex: 50
    full_name = Column(String(100))  # Defina um tamanho, ex: 100
    matricula = Column(String(20))
    user_type = Column(Enum(UserType), nullable=False)
    hashed_password = Column(String(255))  # Defina um tamanho, ex: 255
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
# ...existing code...