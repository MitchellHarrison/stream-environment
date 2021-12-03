import asyncio
import os 
import uuid
import json
import zmq
import zmq.asyncio
from dataclasses import dataclass

BACKEND = os.environ.get("BACKEND", "127.0.0.1")
PORT = 5555

# zmq SUB socket address
CHAT_ADDRESS = f"tcp://{BACKEND}:{PORT}"

# zmq PUB socket address
TWITCH_ADDRESS = f"tcp://0.0.0.0:{PORT}"

@dataclass
class OutputHandler:
    context: zmq.asyncio.Context = zmq.asyncio.Context()
    chat_sub_topic: str = "chat_output"
    chat_address: str = CHAT_ADDRESS
    twitch_address: str = TWITCH_ADDRESS
    twitch_queue: str = os.environ.get("TWITCH_QUEUE", "")

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
        print(f"topic = {self.twitch_queue}")
        message = [self.twitch_queue.encode("ascii"), payload.encode("ascii")]
        try:
            if platform == "twitch":
                await self.twitch_socket.send_multipart(message)
                print(f"OUTGOING {payload}")
            else:
                # this is where another streaming platform output would be
                pass
        except Exception as e:
            print(e)

    async def run(self) -> None:
        # zmq SUB socket
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.chat_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.chat_sub_topic, "ascii"))

        # zmq PUB socket
        self.twitch_socket = self.context.socket(zmq.PUB)
        self.twitch_socket.bind(self.twitch_address)

        while True:
            # receive message from chat output queue
            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)

            platform = payload["data"]["platform"]
            output = self.format_output(payload)
            await self.route(platform, output)
