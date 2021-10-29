import asyncio
import os
import uuid
import json
import zmq
import zmq.asyncio
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv

# try to get creds from Docker image
try:
    OAUTH_TOKEN = os.environ["OAUTH_TOKEN"]
    BOT_NAME = os.environ["BOT_NAME"]
    CHANNEL = os.environ["CHANNEL"]

# get creds from local file (if running outside of Docker)
except KeyError:
    load_dotenv("../credentials.env")
    OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")
    BOT_NAME = os.getenv("BOT_NAME")
    CHANNEL = os.getenv("CHANNEL")

# twitch irc server parameters
SERVER = "irc.twitch.tv"
PORT = 6667

# zmq-specific things
ZMQ_PORT = 5555
ZMQ_HOST = "*"
ZMQ_ADDRESS = f"tcp://{ZMQ_HOST}:{ZMQ_PORT}"
TOPIC = "twitch_messages"

@dataclass
class Listener:
    oauth_token: str = OAUTH_TOKEN
    bot_name: str = BOT_NAME
    channel: str = CHANNEL
    server: str = SERVER
    port: int = PORT
    topic: str = TOPIC
    zmq_address: str = ZMQ_ADDRESS

    def format_output(self, message:str) -> str:
        id_ = str(uuid.uuid4())
        output = {
            "id": id_,
            "source": "chat.twitch.reader",
            "specversion": "1.0",
            "type": "chat_message",
            "time": str(datetime.now()),
            "data": {
                "platform": "twitch",
                "machine": "twitch_chat_monitor1",
                "message": message
                }
            }
        return json.dumps(output)
        

    async def publish_to_zmq(self, payload:str) -> None:
        print("Listener found a message")
        message = [self.topic.encode("ascii"), payload.encode("ascii")]
        await self.pub.send_multipart(message)


    async def send(self, message:str) -> None:
        self.writer.write(f"{message}\r\n".encode())
        await self.writer.drain()


    async def pong(self) -> None:
        await self.send("PONG tmi.twitch.tv")


    async def connect(self) -> None:
        await self.send(f"PASS oauth:{self.oauth_token}")
        await self.send(f"NICK {self.bot_name}")
        await self.send(f"JOIN #{self.channel}")        
        await self.send(f"CAP REQ :twitch.tv/tags")
        await self.send(f"PRIVMSG #{self.channel} :I'm listening!")


    async def read(self) -> None:
        self.context = zmq.asyncio.Context()
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind(self.zmq_address)

        while True:
            data = await self.reader.read(1024)
            messages = data.decode()

            if messages.startswith("PING"):
                await self.pong()

            # ignore initial connection messages
            elif messages.startswith(":tmi.twitch.tv"):
                print("Connected...")

            else:
                payload = self.format_output(messages)
                await self.publish_to_zmq(payload)


    async def run(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(self.server, self.port)
        await self.connect()
        await self.read()
