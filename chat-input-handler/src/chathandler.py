import asyncio
import aiohttp
import re
import uuid
import zmq
import zmq.asyncio
import json
from datetime import datetime
from message import TwitchMessage

TWITCH = "twitch_messages"
YOUTUBE = "youtube_messages"
CONTEXT = zmq.asyncio.Context()

API = "http://127.0.0.1:1337"

ZMQ_HOST = "twitchreader"
ZMQ_PORT = 5555
ZMQ_PROTOCOL = "tcp"
ZMQ_ADDRESS = f"{ZMQ_PROTOCOL}://{ZMQ_HOST}:{ZMQ_PORT}"

class ChatHandler:
    def __init__(self, twitch:str = TWITCH, context:zmq.asyncio.Context = CONTEXT,
                zmq_address:str = ZMQ_ADDRESS):
        self.twitch = twitch
        self.context = context
        self.zmq_address = zmq_address

        self.twitch_sock = self.context.socket(zmq.SUB)
        self.twitch_sock.connect(self.zmq_address)
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


    async def aio_get(self, url:str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                response = await r.json()
                return response


    async def aio_post(self, url:str, payload:dict) -> None:
        data = json.dumps(payload).encode("ascii")
        async with aiohttp.ClientSession() as session:
            await session.post(url, data=data)


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
                entry_url = f"{API}/commands/add/twitch/"
                await self.aio_post(entry_url, entry)

            if message.command == "!delcommand" and message.sender.is_broadcaster:
                first_word = message.text.split()[1]
                name = first_word if first_word.startswith("!") else f"!{first_word}"
                
                payload = {"name": name}
                await self.aio_post(f"{API}/commands/delete/twitch/", payload)

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
        # get list of commands from db API
        url = f"{API}/commands/get-all/{platform}/" 
        commands = await self.aio_get(url)

        default_reply = "That's not a command, sorry!"
        if command in commands:
            output_url = f"{API}/commands/output/{platform}/{command}/"
            response = await self.aio_get(output_url)
            reply = response.get("output", default_reply)
        else:
            reply = default_reply

        return reply


    async def run(self) -> None:
        while True:
            _, msg = await self.twitch_sock.recv_multipart()
            payload = json.loads(msg)
            print("Payload:", payload)
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
            output_url = "http://127.0.0.1:8000/chat/v1.0/"
            #await self.aio_post(output_url, output)