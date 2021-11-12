import os
from dotenv import load_dotenv
from datetime import datetime
from peewee import PostgresqlDatabase, Model, TextField, DateTimeField, IntegerField
load_dotenv("../credentials.env")

DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "password")
DB_NAME = os.environ.get("DB_NAME", "livestream")
HOST = "database"
PORT = 5432

database = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASS, port=PORT, 
                              host=HOST, autorollback=True)

class BaseModel(Model):
    class Meta:
        database = database


class Tokens(BaseModel):
    name = TextField(unique=True)
    token = TextField()


class TextCommands(BaseModel):
    name = TextField(unique=True)
    platform = TextField()
    output = TextField()

