import os
from datetime import datetime
from peewee import PostgresqlDatabase
from peewee import Model 
from peewee import TextField
from peewee import DateTimeField
from peewee import IntegerField
from peewee import CharField

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
    name = CharField(unique=True)
    token = CharField()


class TextCommands(BaseModel):
    command = CharField()
    platform = CharField()
    output = CharField()
    class Meta:
        table_name = "text_commands"


class ChatMessages(BaseModel):
    time = DateTimeField()
    username = CharField()
    user_id = CharField()
    message = CharField()
    platform = CharField()
    class Meta:
        table_name = "chat_messages"
