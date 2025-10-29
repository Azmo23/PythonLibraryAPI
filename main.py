from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import dbLite, User, Book, cargarLibros
from schemas import *
from auth import *
from datetime import timedelta
import traceback

# Función lifespan para manejar el ciclo de vida
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Conectar y crear tablas
    try:
        print("Iniciando aplicacion...")
        # Conectar a la base de datos
        if dbLite.is_closed():
            dbLite.connect()
            print("Conectado a la base de datos")
        
        # Crear tablas si no existen
        dbLite.create_tables([User, Book])
        print("Tablas creadas: users, books")
        
        # Crear usuario admin por defecto si no existe
        if not User.select().where(User.role == 'admin').exists():
            admin_user = User.create(
                fullname="Administrador Principal",
                email="admin@biblioteca.com",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            print("Usuario admin creado: admin@biblioteca.com / admin123")
        else:
            print("Usuario admin ya existe")
            
    except Exception as e:
        print(f"Error en startup: {e}")
        print(traceback.format_exc())
        raise e
    
    yield  # La aplicación se ejecuta aquí
    
    # Shutdown - Desconectar BD
    try:
        if not dbLite.is_closed():
            dbLite.close()
            print("Desconectado de la base de datos")
    except Exception as e:
        print(f"Error en shutdown: {e}")

app = FastAPI(
    title="API Biblioteca Virtual", 
    description="API para gestion de biblioteca con autenticacion JWT",
    version="1.0.0",
    lifespan=lifespan
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RUTA TEMPORAL PARA DEBUG - ELIMINAR DESPUES
@app.get("/api/v1/debug/usuarios")
async def debug_usuarios():
    try:
        usuarios = []
        for usuario in User.select():
            usuarios.append({
                "id": usuario.id,
                "fullname": usuario.fullname,
                "email": usuario.email,
                "role": usuario.role
            })
        return usuarios
    except Exception as e:
        return {"error": str(e)}

# RUTAS PUBLICAS

# Registro de usuarios
@app.post("/api/v1/register", response_model=UserResponseModel)
async def register(user_data: UserRequestModel):
    try:
        print(f"Intentando registrar usuario: {user_data.email}")
        
        # Verificar si el usuario ya existe
        if User.select().where(User.email == user_data.email).exists():
            print("Email ya registrado")
            raise HTTPException(status_code=400, detail="El email ya esta registrado")
        
        # El primer usuario sera admin, los siguientes user
        user_count = User.select().count()
        role = "admin" if user_count == 0 else "user"
        
        hashed_password = get_password_hash(user_data.password)
        
        user = User.create(
            fullname=user_data.fullname,
            email=user_data.email,
            hashed_password=hashed_password,
            role=role
        )
        
        print(f"Usuario registrado: {user.fullname} ({user.email}) con rol: {user.role}")
        return user
        
    except Exception as e:
        print(f"Error en registro: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Login de usuarios
@app.post("/api/v1/login", response_model=TokenResponseModel)
async def login(user_data: UserLoginModel):
    try:
        print(f"Intentando login con: {user_data.email}")
        
        # Buscar usuario por email
        user = get_user_by_email(user_data.email)
        
        if not user:
            print("Usuario no encontrado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not verify_password(user_data.password, user.hashed_password):
            print("Contraseña incorrecta")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        print(f"Login exitoso: {user.fullname} ({user.email}) - rol: {user.role}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise  # Re-lanzar las HTTPException
    except Exception as e:
        print(f"Error en login: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# RUTAS PROTEGIDAS - Para usuarios autenticados

# Obtener informacion del usuario actual
@app.get("/api/v1/users/me", response_model=UserResponseModel)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Listar todos los libros (acceso para usuarios autenticados)
@app.get("/api/v1/libros")
async def listar_libros(current_user: User = Depends(get_current_active_user)):
    libros = cargarLibros()
    return libros

# Obtener un libro especifico
@app.get("/api/v1/libros/{libro_id}")
async def obtener_libro(libro_id: int, current_user: User = Depends(get_current_active_user)):
    try:
        libro = Book.get(Book.id == libro_id)
        return libro
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

# RUTAS PROTEGIDAS - Solo para administradores

# Crear nuevo libro (solo admin)
@app.post("/api/v1/libros", response_model=BookResponseModel)
async def crear_libro(
    libro_data: BookRequestModel, 
    current_user: User = Depends(get_current_admin_user)
):
    try:
        # Verificar si el ISBN ya existe
        if Book.select().where(Book.isbn == libro_data.isbn).exists():
            raise HTTPException(status_code=400, detail="El ISBN ya esta registrado")
        
        libro = Book.create(
            title=libro_data.title,
            author=libro_data.author,
            description=libro_data.description,
            year=libro_data.year,
            isbn=libro_data.isbn
        )
        
        return libro
        
    except Exception as e:
        print(f"Error creando libro: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Actualizar libro (solo admin)
@app.put("/api/v1/libros/{libro_id}", response_model=BookResponseModel)
async def actualizar_libro(
    libro_id: int,
    libro_data: BookRequestModel,
    current_user: User = Depends(get_current_admin_user)
):
    try:
        libro = Book.get(Book.id == libro_id)
        
        # Verificar si el ISBN ya existe en otro libro
        if Book.select().where(
            (Book.isbn == libro_data.isbn) & 
            (Book.id != libro_id)
        ).exists():
            raise HTTPException(status_code=400, detail="El ISBN ya existe en otro libro")
        
        libro.title = libro_data.title
        libro.author = libro_data.author
        libro.description = libro_data.description
        libro.year = libro_data.year
        libro.isbn = libro_data.isbn
        
        libro.save()
        
        return libro
        
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    except Exception as e:
        print(f"Error actualizando libro: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Eliminar libro (solo admin)
@app.delete("/api/v1/libros/{libro_id}")
async def eliminar_libro(
    libro_id: int, 
    current_user: User = Depends(get_current_admin_user)
):
    try:
        libro = Book.get(Book.id == libro_id)
        libro.delete_instance()
        return {"message": "Libro eliminado correctamente"}
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    except Exception as e:
        print(f"Error eliminando libro: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")