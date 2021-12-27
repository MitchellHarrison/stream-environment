import asyncio
import os
import json
import time
import uuid
import zmq
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from zmq.asyncio import Context

OAUTH_TOKEN = os.environ["OAUTH_TOKEN"]
BOT_NAME = os.environ["BOT_NAME"]
CHANNEL = os.environ["CHANNEL"]
OUTPUT_HANDLER = os.environ["OUTPUT_HANDLER"]

ZMQ_PORT = os.environ["ZMQ_PORT"]

# zmq PUB address
PUB_ADDRESS = f"tcp://0.0.0.0:{ZMQ_PORT}"

# zmq SUB address
SUB_ADDRESS = f"tcp://{OUTPUT_HANDLER}:{ZMQ_PORT}"

@dataclass
class Bot:
    oauth_token: str = os.environ["OAUTH_TOKEN"]
    bot_name: str = os.environ["BOT_NAME"]
    channel: str = CHANNEL
    server: str = "irc.twitch.tv"
    port: int = os.environ["IRC_PORT"]
    topic: str = os.environ["TWITCH_IN_TOPIC"]
    outgoing_topic: str = os.environ["TWITCH_OUT_TOPIC"]
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
        exp = 0
        connected = False
        while not connected:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.server, self.port)
                connected = True
                print("Connected to Twitch IRC")

            # retry connection at increasing intervals
            except ConnectionResetError as e:
                print(e)
                print(f"Connection to Twitch failed. Retrying in {2**exp} second(s)...")
                time.sleep(2**exp)
                exp += 1

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
                pass

            else:
                payload = self.format_output(messages)
                await self.publish_to_zmq(payload)


    # read output messages from zmq
    async def get_outgoing_messages(self) -> None:
        # sleep to allow self.read_chat() to create self.writer first
        await asyncio.sleep(1)

        # sub socket to receive chat output messages from zmq
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.sub_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.outgoing_topic, "ascii"))

        while True:
            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)
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
