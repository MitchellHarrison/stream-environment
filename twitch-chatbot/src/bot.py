import asyncio
import os
import uuid
import json
import zmq
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv
from zmq.asyncio import Context

# try to get creds from Docker image
OAUTH_TOKEN = os.environ["OAUTH_TOKEN"]
BOT_NAME = os.environ["BOT_NAME"]
CHANNEL = os.environ["CHANNEL"]
OUTPUT_HANDLER = os.environ.get("OUTPUT_HANDLER", "chat_output_handler")

# twitch irc server parameters
SERVER = "irc.twitch.tv"
PORT = 6667

TOPIC = "twitch_messages"
OUTGOING_TOPIC = "twitch_output"
ZMQ_PORT = 5555

# zmq PUB address
PUB_ADDRESS = f"tcp://0.0.0.0:{ZMQ_PORT}"

# zmq SUB address
SUB_ADDRESS = f"tcp://{OUTPUT_HANDLER}:{ZMQ_PORT}"

@dataclass
class Bot:
    oauth_token: str = OAUTH_TOKEN
    bot_name: str = BOT_NAME
    channel: str = CHANNEL
    server: str = SERVER
    port: int = PORT
    topic: str = TOPIC
    outgoing_topic: str = OUTGOING_TOPIC
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
        await self.send(f"PRIVMSG #{self.channel} :{message}")


    async def pong(self) -> None:
        await self.send("PONG tmi.twitch.tv")


    async def connect(self) -> None:
        await self.send(f"PASS oauth:{self.oauth_token}")
        await self.send(f"NICK {self.bot_name}")
        await self.send(f"JOIN #{self.channel}")        
        await self.send(f"CAP REQ :twitch.tv/tags")
        await self.send(f"PRIVMSG #{self.channel} :I'm listening!")


    async def read_chat(self) -> None:
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
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.sub_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.outgoing_topic, "ascii"))

        while True:
            # sleep to allow read_chat to create self.writer first
            await asyncio.sleep(1)

            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)
            print(f"MESSAGE RECEIVED: {payload}")
            output_message = payload["data"]["message"]
            
            # ignore blank output messages for incorrect commands
            if output_message:
                await self.send_chat_message(output_message)


    def run(self) -> None:
        self.context = Context()

        # pub socket to publish incoming messages to zmq
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind(self.pub_address)

        cors = asyncio.wait([self.read_chat(), self.get_outgoing_messages()])
        asyncio.get_event_loop().run_until_complete(cors)
