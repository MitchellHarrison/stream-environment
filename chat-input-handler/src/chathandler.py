import asyncio
import aiohttp
import re
import os
import uuid
import zmq
import zmq.asyncio
import json
from datetime import datetime
from dataclasses import dataclass
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


@dataclass
class ChatHandler:
    twitch: str = os.environ["TWITCH_IN_TOPIC"]
    context: zmq.asyncio.Context = zmq.asyncio.Context()
    twitch_address: str = TWITCH_ADDRESS
    command_responses: dict = {}

    def format_output(self, input_payload: dict, message_data: dict) -> dict:
        output = {
            "id": str(uuid.uuid4()),
            "source": "chat.handler",
            "specversion": "1.0",
            "type": "chat_message",
            "time": input_payload.get("time", str(datetime.now())),
            "data": message_data,
        }
        return output

    # wrapper around aiohttp get logic
    async def aio_get(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                response = await r.json()
                return response

    # wrapper around aiohttp post logic
    async def aio_post(self, url: str, payload: dict) -> None:
        data = json.dumps(payload).encode("ascii")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data):
                return

    async def handle_chat_message(self, payload: dict) -> dict:
        payload_data = payload.get("data", "")
        platform = payload_data.get("platform", "")
        sent_time = payload.get("time", str(datetime.now()))
        message_data = {}

        if platform == "twitch":
            message = TwitchMessage(sent_time, payload_data.get("message", ""))
            # print stylized message to terminal
            message.display()
            message_data = await self.handle_twitch_message(message)
        elif platform == "youtube":
            raise NotImplementedError

        if message_data:
            output = self.format_output(payload, message_data)
            # send data to database
            await self.aio_post(f"{DATABASE}/chat/store/", output)

            # send data to backend
            await self.aio_post(f"{BACKEND}/chat/v1.0/", output)

    async def handle_twitch_message(self, message: TwitchMessage) -> dict:
        response = ""
        if message.is_command:
            command = message.text.split()[0]
            if message.command == "!addcommand" and message.sender.is_broadcaster:
                first_word = message.text.split()[1]
                name = first_word if first_word.startswith("!") else f"!{first_word}"
                response = message.text.split(" ", 2)[-1]
                entry = {"name": name, "output": output}
                entry_url = f"{DATABASE}/commands/add/twitch/"
                await self.aio_post(entry_url, entry)
                self.command_responses[entry] = response

            elif message.command == "!delcommand" and message.sender.is_broadcaster:
                first_word = message.text.split()[1]
                name = first_word if first_word.startswith("!") else f"!{first_word}"
                payload = {"name": name}
                await self.aio_post(f"{DATABASE}/commands/delete/twitch/", payload)
                del self.command_responses[name]
            response = await self.get_command_response(command, "twitch")

        output = {  # message is / is not a command
            "platform": "twitch",
            "machine": "chat_input_handler1",
            "user_id": message.sender.user_id,
            "username": message.sender.username,
            "display_name": message.sender.display_name,
            "message": message.text,
            "is_command": message.is_command,
            "response": response,
        }
        return output

    async def refresh_commands(self, platform: str):
        url = f"{DATABASE}/commands/get-all/{platform}/"
        commands = await self.aio_get(url)
        for command in commands:
            output_url = f"{DATABASE}/commands/output/{platform}/{command}/"
            response = await self.aio_get(output_url)
            reply = response.get("output", "")
            self.command_responses[command] = reply

    async def get_command_response(self, command: str, platform: str) -> str:
        # get list of commands from db DATABASE
        default_reply = ""
        if not self.command_responses:
            await self.refresh_commands(platform)
        return self.command_responses.get(command, default_reply)

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
