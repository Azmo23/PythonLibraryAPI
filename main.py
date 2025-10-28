from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import dbLite, User, Book, cargarLibros
from schemas import *
from auth import *
from datetime import timedelta

app = FastAPI(title="API Biblioteca",
              description="API para la gestión de libros",
              version="1.0.0")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def lifespan(app: FastAPI):
    # Conectarse a la base de datos al iniciar la aplicación
    dbLite.connect()
    dbLite.create_tables([User, Book])
    cargarLibros()

    #Crear usuario admin por defecto si no existe
    if not User.select().where(User.email == "admin@admin.com").exists():
        user = User.create(full_name="Admin",
                            email="admin@admin.com", 
                            password=get_password_hash("admin123"), 
                            role="admin", 
                            is_active=True)
        print ("Usuario admin creado: Admin/admin123")

    yield

    # Desconectarse de la base de datos al cerrar la aplicación
    if not dbLite.is_closed():
        dbLite.close()


#Rutas Públicas

@app.post("/api/v1/register", response_model=UserResponseModel)
async def register(user: UserRequestModel):
    #Verificar si el usuario si existe
    if User.select().where(User.email == user.email).exists():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    #El primer usuario será admin los demás solo User

    user_count = User.select().count()

    if user_count == 0:
        role = "admin"
    else:
        role = "user"

    password = get_password_hash(user.password)

    user = User.create(full_name=user.full_name,
                        email=user.email, 
                        password=password, 
                        role=role, 
                        is_active=True)

    return user


#Login de usuarios
@app.post("/api/v1/login", response_model=TokenModel)
async def login(user: UserLoginModel):
    user = authenticate_user(user.email, user.password)

    #Verificar si el usuario existe
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


#Rutas protegidas - para usuarios autenticados

#Obtener informacion del usuario actual
@app.get("/api/v1/users/me", response_model=UserResponseModel)
async def get_me(current_user: UserResponseModel = Depends(get_current_user)):
    return current_user

#Listar todos los libros (acceso para usuarios autenticados)
@app.get("/api/v1/books/")
async def get_books(current_user: UserResponseModel = Depends(get_current_user)):
    libros = cargarLibros()
    return libros

#Obtener un libro especifico
@app.get("/api/v1/books/{libro_id}")
async def get_book(id: int, current_user: UserResponseModel = Depends(get_current_user)):
    try:
        libro = Book.get(Book.id == libro_id)
        return libro
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

#Rutas protegidas - Solo administradores

#Crear un libro
@app.post("/api/v1/createBook", response_model=BookResponseModel)
async def create_book(
    libro_data: BookRequestModel,
    current_user: UserResponseModel = Depends(get_current_admin_user)
):
    #Verificar si el ISBN ya está registrado
    if Book.select().where(Book.isbn == libro_data.isbn).exists():
        raise HTTPException(status_code=400, detail="ISBN ya registrado")
    
    #Crear el libro
    libro = Book.create(
        title = libro_data.title,
        author = libro_data.author,
        description = libro_data.description,
        isbn = libro_data.isbn,
        publication_date = libro_data.publication_date,
    )
    return libro

#Actualizar un libro
@app.put("/api/v1/updateBook/{libro_id}", response_model=BookResponseModel)
async def update_book(
    libro_id: int,
    libro_data: BookRequestModel,
    current_user: UserResponseModel = Depends(get_current_admin_user)
):
    try:
        libro = Book.get(Book.id == libro_id)

        #Verificar si el ISBN ya está o existe en otro libro
        if Book.select().where(
            (Book.isbn == libro_data.isbn) &
            (Book.id != libro_id)
        ).exists():
            raise HTTPException(status_code=400, detail="ISBN ya registrado")
        
        libro.title = libro_data.title
        libro.author = libro_data.author
        libro.isbn = libro_data.isbn
        libro.description = libro_data.description
        libro.publication_date = libro_data.publication_date

        libro.save()

        return libro
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    
#Eliminar un libro
@app.delete("/api/v1/deleteBook/{libro_id}", response_model=BookResponseModel)
async def delete_book(
    libro_id: int,
    current_user: UserResponseModel = Depends(get_current_admin_user)
):
    try:
        libro = Book.get(Book.id == libro_id)
        libro.delete_instance()
        return {"message": "Libro eliminado correctamente"}
    except Book.DoesNotExist:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)




    





            
