from pydantic import BaseModel, EmailStr
from typing import Optional

# Esquemas para Usuarios
class UserRequestModel(BaseModel):
    fullname: str
    email: EmailStr
    password: str

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str

class UserResponseModel(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    is_active: bool
    role: str

# Esquemas para Libros
class BookRequestModel(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    year: Optional[int] = None
    isbn: str

class BookResponseModel(BookRequestModel):
    id: int
    available: bool

# Esquemas para Tokens
class TokenResponseModel(BaseModel):
    access_token: str
    token_type: str