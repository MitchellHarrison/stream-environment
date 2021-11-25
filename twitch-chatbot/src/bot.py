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
OAUTH_TOKEN = os.environ.get("OAUTH_TOKEN", "")
BOT_NAME = os.environ.get("BOT_NAME", "")
CHANNEL = os.environ.get("CHANNEL", "")
OUTPUT_HANDLER = os.environ.get("OUTPUT_HANDLER", "chat_output_handler")

# twitch irc server parameters
SERVER = "irc.twitch.tv"
PORT = 6667

ZMQ_PORT = 5555
TOPIC = "twitch_messages"
OUTPUT_TOPIC = "twitch_output"

# zmq PUB parameters
ZMQ_HOST = "0.0.0.0"
PUB_ADDRESS = f"tcp://{ZMQ_HOST}:{ZMQ_PORT}"

# zmq SUB parameters
SUB_ADDRESS = f"tcp://{OUTPUT_HANDLER}:{ZMQ_PORT}"

@dataclass
class Bot:
    oauth_token: str = OAUTH_TOKEN
    bot_name: str = BOT_NAME
    channel: str = CHANNEL
    server: str = SERVER
    port: int = PORT
    topic: str = TOPIC
    output_topic: str = OUTPUT_TOPIC
    pub_address: str = PUB_ADDRESS
    sub_address: str = SUB_ADDRESS

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
        message = [self.topic.encode("ascii"), payload.encode("ascii")]
        await self.pub.send_multipart(message)


    async def send(self, message:str) -> None:
        self.writer.write(f"{message}\r\n".encode())
        await self.writer.drain()


    async def send_chat_message(self, message:str) -> None:
        self.writer.write(f"PRIVMSG #{self.channel} :{message}")


    async def pong(self) -> None:
        await self.send("PONG tmi.twitch.tv")


    async def connect(self) -> None:
        await self.send(f"PASS oauth:{self.oauth_token}")
        await self.send(f"NICK {self.bot_name}")
        await self.send(f"JOIN #{self.channel}")        
        await self.send(f"CAP REQ :twitch.tv/tags")
        await self.send(f"PRIVMSG #{self.channel} :I'm listening!")


    async def read(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(self.server, self.port)
        await self.connect()
        while True:
            data = await self.reader.read(1024)
            try:
                messages = data.decode()
            except UnicodeDecodeError:
                raise(UnicodeDecodeError(data))

            if len(messages) == 0:
                continue

            if messages.startswith("PING"):
                await self.pong()

            # ignore initial connection messages
            elif messages.startswith(":tmi.twitch.tv"):
                print("Connected...")

            else:
                payload = self.format_output(messages)
                await self.publish_to_zmq(payload)


    # read output messages from zmq
    async def get_outgoing_messages(self) -> None:
        # sub socket to receive chat output messages from zmq
        self.sub = self.context.socket(zmq.SUB)
        self.sub.connect(self.sub_address)
        self.sub.subscribe("")

        print("LISTENING FOR MESSAGES")
        while True:
            _, msg = await self.sub.recv_multipart()
            payload = json.loads(msg)
            print(f"CHATBOT OUTGOING MESSAGE RECEIVED {payload}")
            output_message = payload["data"]["message"]
            await self.send_chat_message(output_message)


    def run(self) -> None:
        self.context = zmq.asyncio.Context()

        # pub socket to publish incoming messages to zmq
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind(self.pub_address)

        cors = asyncio.wait([self.read(), self.get_outgoing_messages()])
        asyncio.get_event_loop().run_until_complete(cors)
