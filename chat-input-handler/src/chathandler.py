import asyncio
import aiohttp
import command
import re
import os
import uuid
import zmq
import zmq.asyncio
import json
from datetime import datetime
from message import TwitchMessage

DB_API = os.environ["DB_API"]
DB_API_PORT = os.environ["DB_API_PORT"]
DATABASE = f"http://{DB_API}:{DB_API_PORT}"

BACKEND_NAME = os.environ["BACKEND"]
BACKEND_PORT = os.environ["BACKEND_PORT"]
BACKEND = f"http://{BACKEND_NAME}:{BACKEND_PORT}"

# zmq sub parameters
TWITCH_BOT = os.environ["TWITCH_BOT"]
ZMQ_PORT = os.environ["ZMQ_PORT"]
TWITCH_ADDRESS = f"tcp://{TWITCH_BOT}:{ZMQ_PORT}"

# all command objects 
COMMANDS = (c() for c in command.Command.__subclasses__())

class ChatHandler:
    def __init__(self):
        self.twitch = os.environ["TWITCH_IN_TOPIC"]
        self.context = zmq.asyncio.Context()
        self.twitch_address = TWITCH_ADDRESS
        self.hard_commands = {s.command_name: s for s in COMMANDS}


    def format_output(self, message:TwitchMessage) -> dict:
        output = {
            "id": str(uuid.uuid4()),
            "source": "chat.handler", 
            "specversion": "1.0",
            "type": "chat_message",
            "time": message.sent_time,
            "data": {
                "platform": message.platform,
                "machine": "chat_input_handler1",
                "user_id": message.sender.user_id,
                "username": message.sender.username,
                "display_name": message.sender.display_name,
                "message": message.text,
                "is_command": message.is_command,
                "response": message.reply
            }
        }
        return output


    # wrapper around aiohttp get logic
    async def aio_get(self, url:str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                response = await r.json()
                return response


    # wrapper around aiohttp post logic
    async def aio_post(self, url:str, payload:dict) -> None:
        data = json.dumps(payload).encode("ascii")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data): 
                return


    async def handle_chat_message(self, payload:dict) -> dict:
        payload_data = payload.get("data", "")
        platform = payload_data.get("platform", "")
        sent_time = payload.get("time", str(datetime.now()))
        message = False

        if platform == "twitch":
            message = TwitchMessage(sent_time, payload_data.get("message", ""))
            await message.update_reply()

        elif platform == "youtube":
            # youtube messages will be handled here
            pass

        if message:
            output = self.format_output(message)
            await self.aio_post(f"{DATABASE}/chat/store/", output)
            await self.aio_post(f"{BACKEND}/chat/v1.0/", output)


    async def get_command_response(self, command:str, platform:str) -> str:
        # get list of commands from db DATABASE
        url = f"{DATABASE}/commands/get-all/{platform}/" 
        commands = await self.aio_get(url)

        default_reply = ""
        if command in commands:
            output_url = f"{DATABASE}/commands/output/{platform}/{command}/"
            response = await self.aio_get(output_url)
            reply = response.get("output", default_reply)
        else:
            reply = default_reply
        return reply


    async def run(self) -> None:
        # zmq SUB socket
        self.twitch_sock = self.context.socket(zmq.SUB)
        self.twitch_sock.connect(self.twitch_address)
        self.twitch_sock.setsockopt(zmq.SUBSCRIBE, bytes(self.twitch, "ascii"))

        while True:
            # recieve message from twitch chat via zmq
            _, msg = await self.twitch_sock.recv_multipart()
            payload = json.loads(msg)
            await self.handle_chat_message(payload)
