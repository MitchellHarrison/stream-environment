import asyncio
import os 
import uuid
import json
import zmq
from zmq.asyncio import Context

BACKEND = "0.0.0.0" #os.environ.get("BACKEND", "127.0.0.1")
TWITCH_QUEUE = "0.0.0.0"
CONTEXT = Context()

PORT = 5555
PROTOCOL = "tcp"

# zmq SUB socket address
CHAT_SUB_ADDRESS = f"{PROTOCOL}://{BACKEND}:{PORT}"

# zmq PUB socket address
TWITCH_ADDRESS = f"{PROTOCOL}://{TWITCH_QUEUE}:{PORT}"

class OutputHandler:
    def __init__(self, context:Context=CONTEXT, chat_address:str=CHAT_SUB_ADDRESS,
                twitch_address:str=TWITCH_ADDRESS, backend:str=BACKEND, 
                twitch_queue:str=TWITCH_QUEUE):
        self.context = context
        self.chat_address = chat_address
        self.twitch_address = twitch_address

        self.backend = backend
        self.twitch_queue = twitch_queue

        # zmq SUB socket
        self.sub_socket = self.context.socket(zmq.SUB)
        print(self.chat_address)
        self.sub_socket.bind(self.chat_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.backend, "ascii"))

        # zmq PUB socket
        self.twitch_socket = self.context.socket(zmq.PUB)
        self.twitch_socket.connect(self.twitch_address)


    def format_output(self, payload:dict) -> str:
        message = payload["data"]["message"]
        time = payload["time"]
        output = {
            "id": str(uuid.uuid4()),
            "source": "output.handler",
            "type": "chat_message",
            "time": time,
            "data": {
                "message": message
            }
        }
        return json.dumps(output)
        

    async def route(self, platform:str, payload:str) -> None:
        message = [self.twitch_queue.encode("ascii"), payload.encode("ascii")]
        if platform == "twitch":
            print(payload)
            await self.twitch_socket.send_multipart(message)
        else:
            # this is where another streaming platform output would be
            pass
        

    async def run(self) -> None:
        print("RUNNING")
        while True:
            # receive message from chat output queue
            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)
            print("MESSAGE RECEIVED")

            platform = payload["data"]["platform"]
            output = self.format_output(payload)
            await self.route(platform, output)
