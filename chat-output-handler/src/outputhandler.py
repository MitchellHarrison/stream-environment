import asyncio
import os 
import uuid
import json
import zmq
from zmq.asyncio import Context

BACKEND = os.environ.get("BACKEND", "127.0.0.1")
TWITCH_QUEUE = os.environ.get("TWITCH_QUEUE", "")
CONTEXT = Context()
PORT = 5555

# zmq SUB socket address
CHAT_ADDRESS = f"tcp://{BACKEND}:{PORT}"
CHAT_SUB_TOPIC = "chat_output"

# zmq PUB socket address
TWITCH_ADDRESS = f"tcp://0.0.0.0:{PORT}"

class OutputHandler:
    def __init__(self, context:Context=CONTEXT, chat_address:str=CHAT_ADDRESS,
                twitch_address:str=TWITCH_ADDRESS, chat_sub_topic:str=CHAT_SUB_TOPIC,
                twitch_queue:str=TWITCH_QUEUE):
        self.context = context
        self.chat_address = chat_address
        self.twitch_address = twitch_address
        self.chat_sub_topic = chat_sub_topic
        self.twitch_queue = twitch_queue

        # zmq SUB socket
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.chat_address)
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, bytes(self.chat_sub_topic, "ascii"))

        # zmq PUB socket
        self.twitch_socket = self.context.socket(zmq.PUB)
        self.twitch_socket.bind(self.twitch_address)


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
        while True:
            # receive message from chat output queue
            _, msg = await self.sub_socket.recv_multipart()
            payload = json.loads(msg)

            platform = payload["data"]["platform"]
            output = self.format_output(payload)
            await self.route(platform, output)
