import asyncio
import aiohttp
import re
import os
import uuid
import zmq
import zmq.asyncio
import json
from datetime import datetime
from message import TwitchMessage

TWITCH = "twitch_messages"
YOUTUBE = "youtube_messages"
CONTEXT = zmq.asyncio.Context()

DB_API = os.environ.get("DB_API", "127.0.0.1")
DATABASE = f"http://{DB_API}:1337"

BACKEND_NAME = os.environ.get("BACKEND_NAME", "127.0.0.1")
BACKEND_PORT = os.environ.get("BACKEND_PORT", "1336")
BACKEND = f"http://{BACKEND_NAME}:{BACKEND_PORT}"

TWITCH_BOT = os.environ.get("TWITCH_BOT", "127.0.0.1")
PROTOCOL = "tcp"
ZMQ_PORT = 5555
TWITCH_ADDRESS = f"{PROTOCOL}://{TWITCH_BOT}:{ZMQ_PORT}"

class ChatHandler:
    def __init__(self, twitch:str = TWITCH, context:zmq.asyncio.Context = CONTEXT,
                twitch_address:str = TWITCH_ADDRESS):
        self.twitch = twitch
        self.context = context
        self.twitch_address = twitch_address

        # zmq SUB socket
        self.twitch_sock = self.context.socket(zmq.SUB)
        self.twitch_sock.connect(self.twitch_address)
        self.twitch_sock.setsockopt(zmq.SUBSCRIBE, bytes(self.twitch, "ascii"))

        self.twitch_pattern = re.compile(
            fr"badges=(?P<badges>[^;]*).*display-name=(?P<display_name>[^;]*).*emotes=(?P<emotes>[^;]*);.+user-id=(?P<user_id>[\d]+).+:(?P<username>[\d\w]+)![^:]+:(?P<text>.*)\r",
            flags=re.IGNORECASE
        )


    def format_output(self, input_payload:dict, message_data:dict) -> dict:
        output = {
            "id": str(uuid.uuid4()),
            "source": "chat.handler", 
            "specversion": "1.0",
            "type": "chat_message",
            "time": input_payload.get("time", str(datetime.now())),
            "data": message_data
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


    async def handle_twitch_message(self, message:TwitchMessage) -> dict:
        response = ""
        if message.is_command:
            command = message.text.split()[0]
            if message.command == "!addcommand" and message.sender.is_broadcaster:
                first_word = message.text.split()[1]
                name = first_word if first_word.startswith("!") else f"!{first_word}"
                entry = {
                    "name": name, 
                    "output": message.text.split(" ", 2)[-1]
                }
                entry_url = f"{DATABASE}/commands/add/twitch/"
                await self.aio_post(entry_url, entry)

            elif message.command == "!delcommand" and message.sender.is_broadcaster:
                first_word = message.text.split()[1]
                name = first_word if first_word.startswith("!") else f"!{first_word}"
                
                payload = {"name": name}
                await self.aio_post(f"{DATABASE}/commands/delete/twitch/", payload)

            response = await self.get_command_response(command, "twitch")

        output = {
            "platform": "twitch",
            "machine": "chat_input_handler1",
            "user_id": message.sender.user_id,
            "username": message.sender.username,
            "display_name": message.sender.display_name,
            "message": message.text,
            "is_command": message.is_command,
            "response": response
        }
        return output


    async def get_command_response(self, command:str, platform:str) -> str:
        # get list of commands from db DATABASE
        url = f"{DATABASE}/commands/get-all/{platform}/" 
        commands = await self.aio_get(url)

        default_reply = "That's not a command, sorry!"
        if command in commands:
            output_url = f"{DATABASE}/commands/output/{platform}/{command}/"
            response = await self.aio_get(output_url)
            reply = response.get("output", default_reply)
        else:
            reply = default_reply

        return reply


    async def run(self) -> None:
        print("THE INPUT HANDLER IS RUNNING")
        while True:
            _, msg = await self.twitch_sock.recv_multipart()
            payload = json.loads(msg)
            payload_data = payload.get("data", "")
            platform = payload_data.get("platform", "")
            sent_time = payload.get("time", str(datetime.now()))
            message_data = {}

            if platform == "twitch":
                message = TwitchMessage(sent_time, payload_data.get("message", ""))
                message_data = await self.handle_twitch_message(message)

            if not message_data:
                continue

            output = self.format_output(payload, message_data)
            output_url = f"{BACKEND}/chat/v1.0/"
            await self.aio_post(output_url, output)
