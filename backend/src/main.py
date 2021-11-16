import os
import uuid
import uvicorn
import json
from datetime import datetime
from fastapi import FastAPI, Request
from publisher import Publisher

DB_API_NAME = os.environ.get("DB_API_NAME", "127.0.0.1")
DB_API_PORT = os.environ.get("DB_API_PORT", 1337)
DATABASE = f"http://{DB_API_NAME}:{DB_API_PORT}/"

ZMQ_PUB = "chat_output"
app = FastAPI()
publisher = Publisher()

def format_message_response(message:dict, platform:str, chat_response:str) -> dict:
    output = {
        "id": str(uuid.uuid4()),
        "source":  "stream.backend",
        "specversion": "1.0",
        "type": "chat_message",
        "time": str(datetime.now()),
        "data": {
            "platform": platform,
            "machine": "backend1",
            "message": chat_response
        }
    }
    return json.dumps(output)


@app.post("/chat/v1.0/")
async def handle_message(payload:Request):
    message = await payload.json()
    data = message["data"]
    print(data)
    platform = data["platform"]

    if data["is_command"]:
        default_response = f"I don't know what to say, {data['display_name']}."
        response = data.get("response", default_response)

        output = format_message_response(message, platform, response)
        await publisher.publish(output)

    return {
        "status": "SUCCESS",
        "data": message
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1336)

