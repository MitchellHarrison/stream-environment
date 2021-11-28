import os
import zmq
import json
from zmq.asyncio import Context

CONTEXT = Context()
PORT = 5555
HOST = "0.0.0.0" #os.environ.get("CHAT_OUTPUT", "127.0.0.1")
PROTOCOL = "tcp"
ZMQ_ADDRESS = f"{PROTOCOL}://{HOST}:{PORT}"
OUTPUT_TOPIC = "chat_output"

class Publisher:
    def __init__(self, topic:str=OUTPUT_TOPIC, context:Context=CONTEXT):
        self.topic = topic
        self.context = context
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(ZMQ_ADDRESS)

    async def publish(self, payload:str) -> None:
        message = [self.topic.encode("ascii"), payload.encode("ascii")]
        await self.socket.send_multipart(message)
