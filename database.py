from peewee import *

dbLite = SqliteDatabase('library.db')

class User(Model):
    fullname = CharField(max_length=150)
    email = CharField(max_length=100, unique=True)
    password = CharField(max_length=100)
    is_active = BooleanField(default=True)
    role = CharField(max_length=50, default='user') # roles: user o admin. (Por defecto es user)

    class Meta:
        database = dbLite
        table_name = 'users'

class Book(Model):
    title = CharField(max_length=200)
    author = CharField(max_length=100)
    published_year = IntegerField()
    description = TextField(null=True)
    isbn = CharField(max_length=13, unique=True)
    available_copies = IntegerField(default=1)

    class Meta:
        database = dbLite
        table_name = 'books'
        
dbLite.connect()

def cargarUsuarios():
    usuarios = []
    for user in User.select().dicts():
        usuarios.append(user)
    return usuarios

def cargarLibros():
    libros = []
    for book in Book.select().dicts():
        libros.append(book)
    return libros

