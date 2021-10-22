import zmq
import json
from zmq.asyncio import Context

ZMQ_PUB = "chat_output"
CONTEXT = Context()
PORT = 5555
HOST = "127.0.0.1"
PROTOCOL = "tcp"
ZMQ_ADDRESS = f"{PROTOCOL}://{HOST}:{PORT}"
OUTPUT_TOPIC = "chat_output"

class Publisher:
    def __init__(self, topic:str=OUTPUT_TOPIC, context:Context=CONTEXT, pub:str=ZMQ_PUB):
        self.topic = topic
        self.context = context
        self.pub = pub
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(ZMQ_ADDRESS)


    async def publish(self, payload:str) -> None:
        message = [self.topic.encode("ascii"), payload.encode("ascii")]
        await self.socket.send_multipart(message)
