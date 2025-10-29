from peewee import *

dbLite = SqliteDatabase('biblioteca.db')

class User(Model):
    fullname = CharField(max_length=100)
    email = CharField(max_length=100, unique=True)
    hashed_password = CharField(max_length=255)
    is_active = BooleanField(default=True)
    role = CharField(default='user')  # 'user' o 'admin'

    class Meta:
        database = dbLite
        table_name = 'users'

class Book(Model):
    title = CharField(max_length=200)
    author = CharField(max_length=100)
    description = TextField(null=True)
    year = IntegerField(null=True)
    isbn = CharField(max_length=20, unique=True)
    available = BooleanField(default=True)

    class Meta:
        database = dbLite
        table_name = 'books'

dbLite.connect()

def cargarLibros():
    libros = []
    for libro in Book.select().dicts():
        libros.append(libro)
    return libros

def cargarUsuarios():
    usuarios = []
    for usuario in User.select().dicts():
        usuarios.append(usuario)
    return usuarios