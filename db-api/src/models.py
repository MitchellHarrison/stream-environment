import os
from dotenv import load_dotenv
from datetime import datetime
from peewee import PostgresqlDatabase, Model, TextField, DateTimeField, IntegerField
load_dotenv("../credentials.env")

DB_USER = os.environ["PSQL_USER"]
DB_PASS = os.environ["PSQL_PASS"]
DB_NAME = os.environ["DB_NAME"]
HOST = os.environ["DATABASE"]
PORT = os.environ["PSQL_PORT"]

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

