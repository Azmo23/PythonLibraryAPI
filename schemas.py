from pydantic import *
from typing import Optional

#Esquemas para usuarios
class UserRequestModel(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    
class UserLoginModel(BaseModel):
    email: EmailStr
    password: str
    
class UserResponseModel(UserRequestModel):
    id: int
    fullname: str
    email: EmailStr
    is_active: bool
    role: str
    
#Esquemas para libros
class BookRequestModel(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    published_year: int
    isbn: str
    available_copies: int 
    
class BookResponseModel(BookRequestModel):
    id: int
    available: bool
    
#Esquemas para los tokens
class TokenModel(BaseModel):
    access_token: str
    token_type: str
    

