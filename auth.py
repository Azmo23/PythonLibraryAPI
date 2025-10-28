from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from schemas import UserResponseModel
from database import User, dbLite

# Configuración para JWT
SECRET_KEY = "97e5f3932a3b71f9c8b412a34739b9606b37d0ee393b28a9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Funciones para la funcionalidad de la contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)  

def get_password_hash(password):
    return pwd_context.hash(password)

#Funciones para usuarios

def get_user(email: str) -> Optional[UserResponseModel]:
    try:
        return User.get(User.email == email)        
    except User.DoesNotExist:
        return None
    
def authenticate_user(email: str, password: str) -> Optional[UserResponseModel]:
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

# Funciones para tokens
def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, 
                            SECRET_KEY, 
                            algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponseModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,
                            SECRET_KEY, 
                            algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserResponseModel = Depends(get_current_user)) -> UserResponseModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400,
                            detail="Usuario Inactivo")
    return current_user

async def get_current_admin_user(current_user: UserResponseModel = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No tiene permisos suficientes.")
    return current_user