import os
from dotenv import load_dotenv
from datetime import datetime
from peewee import PostgresqlDatabase, Model, TextField, DateTimeField, IntegerField
load_dotenv("../credentials.env")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
HOST = "localhost"
PORT = 5432

database = PostgresqlDatabase("livestream", user=DB_USER, password=DB_PASS, port=PORT, 
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

