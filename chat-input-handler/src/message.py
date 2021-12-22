import aiohttp
import os
import re
import json
from command import Command
from datetime import datetime
from user import TwitchUser

COMMAND_TRIGGER = "!"
HARD_COMMANDS = {s.command_name: s for s in (c() for c in Command.__subclasses__())}

DB_API = os.environ["DB_API"]
DB_API_PORT = os.environ["DB_API_PORT"]
DATABASE = f"http://{DB_API}:{DB_API_PORT}"

class TwitchMessage:
    def __init__(self, sent_time:str, message:str) -> None:
        self.platform = "twitch"
        self.sent_time = sent_time
        self.message = message

        self.message_data = self.parse(self.message)
        self.text = self.message_data.get("message", "")
        self.sender = TwitchUser(
            self.message_data.get("user-id", ""),
            self.message_data.get("display-name", ""),
            self.message_data.get("badges", []),
            self.message_data.get("color", "")
        )

        self.is_command = False
        self.command_name = ""
        if self.text.startswith(COMMAND_TRIGGER):
            self.is_command = True
            self.command_name = self.text.split()[0]
        self.reply = None

        self.display()


    def parse(self, message:str) -> dict:
        if "PRIVMSG" in message:
            all_tags = message.split()[0]
            text = message.split("PRIVMSG")[1].split(":", maxsplit=1)[-1]
            output = {"message":text}

            tag_strings = all_tags.split(";") 
            required_tags = ["user-id", "display-name", "badges", "color"]
            for t in tag_strings:
                k,v = t.split("=")
                if k in required_tags:
                    if k == "badges":
                        v = [b[0] for b in (e.split("/") for e in v.split(","))]
                    output[k] = v
            return output


    def display(self) -> None:
        r,g,b = self.sender.color
        print(f"\033[38;2;{r};{g};{b}m" + self.sender.display_name + 
                "\033[38;2;255;255;255m", f"{self.text}\n")


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


    async def update_reply(self) -> None:
        if self.is_command:
            # update reply from command object
            if self.command_name in HARD_COMMANDS:
                command = HARD_COMMANDS[self.command_name]
                user_is_priv = (self.sender.is_mod or self.sender.is_broadcaster)
                if command.restricted and not user_is_priv:
                    sender_name = self.sender.display_name
                    self.reply = f"You need to be a mod to use that command, {sender_name}."
                else:
                    self.reply = await command.execute(self.sender, self.text)

            # command is not a hard_command
            else:
                # get command output from DB/cache
                text_commands = await self.aio_get(f"{DATABASE}/commands/get-all/twitch/")
                if self.command_name in text_commands:
                    response_url = f"{DATABASE}/commands/output/twitch/{self.command_name}/"
                    response = await self.aio_get(response_url)
                    self.reply = response["output"]
                
            # delcommand logic
            # if message.command == "!delcommand" and message.sender.is_broadcaster:
            #     first_word = message.text.split()[1]
            #     name = first_word if first_word.startswith("!") else f"!{first_word}"
            #     
            #     payload = {"name": name}
            #     await self.aio_post(f"{DATABASE}/commands/delete/twitch/", payload)
