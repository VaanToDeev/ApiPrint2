from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Esquema base para usuário
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

# Esquema para criação de usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Esquema para atualização de usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)

# Esquema para retorno de usuário
class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Esquema para token de acesso
class Token(BaseModel):
    access_token: str
    token_type: str

# Esquema para dados do token
class TokenData(BaseModel):
    username: Optional[str] = None