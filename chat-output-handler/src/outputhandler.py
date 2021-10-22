import asyncio
import uuid
import json
import zmq
from zmq.asyncio import Context

HOST = "127.0.0.1"
PORT = 5555
PROTOCOL = "tcp"
ZMQ_ADDRESS = f"{PROTOCOL}://{HOST}:{PORT}"
CHAT_OUT_QUEUE = "chat_output"
TWITCH_QUEUE = "twitch_output" 
CONTEXT = Context()

class OutputHandler:
    def __init__(self, context:Context=CONTEXT, address:str=ZMQ_ADDRESS, 
                sub_queue:str=CHAT_OUT_QUEUE, twitch_queue:str=TWITCH_QUEUE):
        self.context = context
        self.address = address
        self.sub_queue = sub_queue
        self.twitch_queue = twitch_queue

        # subscribe to chat_output message queue
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.bind(self.address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.sub_queue, "ascii"))

        self.twitch_socket = self.context.socket(zmq.PUB)
        self.twitch_socket.connect(self.address)


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
            await self.twitch_socket.send_multipart(message)
        

    async def run(self) -> None:
        while True:
            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)
            platform = payload["data"]["platform"]
            output = self.format_output(payload)
            await self.route(platform, output)
