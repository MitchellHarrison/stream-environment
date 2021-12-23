import aiohttp
import os
import json
from abc import ABC, abstractmethod
from user import TwitchUser

MAX_MESSAGE_LENGTH = 500
DB_API = os.environ["DB_API"]
DB_API_PORT = os.environ["DB_API_PORT"]
DATABASE = f"http://{DB_API}:{DB_API_PORT}"
TRIGGER = os.environ["COMMAND_TRIGGER"]

class Command(ABC):
    @property
    @abstractmethod
    def command_name(self) -> str:
        raise NotImplementedError
    
    # restricted commands are only useable by streamer and mods
    @property
    def restricted(self) -> bool:
        return False

    @abstractmethod
    async def execute(self, user=TwitchUser(), message=""):
        raise NotImplementedError

    async def aio_get(self, url:str, headers={}) -> dict:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as r:
                response = await r.json()
                return response

    async def aio_post(self, url:str, payload:dict) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(payload).encode()) as r:
                return


class AddCommand(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}addcommand"

    @property
    def restricted(self) -> bool:
        return True

    async def execute(self, user:TwitchUser, message:str):
        command = message.split()[1]
        if command.startswith(TRIGGER):
           command = command.lstrip(TRIGGER)
        output = message.split(maxsplit=2)[-1]

        # add entry to text_command table
        url = f"{DATABASE}/commands/add/twitch/" 
        payload = {"command":command, "output":output}
        await self.aio_post(url, payload)


class EditCommand(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}editcommand"

    @property
    def restricted(self) -> bool:
        return True

    async def execute(self, user=TwitchUser(), message=""):
        name = message.split()[1].lstrip(TRIGGER)
        new_output = message.split(maxsplit=2)[-1]
        url = f"{DATABASE}/commands/edit/twitch/"
        payload = {
            "name": name,
            "output": new_output
        }
        print(payload)
        await self.aio_post(url, payload)


class DelCommand(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}delcommand"

    @property
    def restricted(self) -> bool:
        return True

    async def execute(self, user=TwitchUser(), message=""):
        command = message.split()[1]
        if command.startswith(TRIGGER):
            command = command.lstrip(TRIGGER)

        # remove text command from database
        payload = {"name": command}
        url = f"{DATABASE}/commands/delete/twitch/"
        await self.aio_post(url, payload)
        

class Commands(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}commands"

    async def execute(self, user=TwitchUser(), message=""):
        hard_commands = [c.command_name for c in (s() for s in Command.__subclasses__())]
        url = f"{DATABASE}/commands/get-all/twitch/"
        text_commands = await self.aio_get(url)
        all_commands = hard_commands + [f"{TRIGGER}{c}" for c in text_commands]
        return ", ".join(sorted(all_commands))


class Joke(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}joke"

    async def execute(self, user=TwitchUser(), message=""):
        error_message = "I couldn't find a short enough joke. Sorry!"
        url = "https://icanhazdadjoke.com/"
        headers = {"accept": "application/json"}
        num_attempts = 10

        # try to get a short enough joke to fit in chat
        for _ in range(num_attempts):
            result = await self.aio_get(url, headers)
            joke = result["joke"]
            if len(joke) <= MAX_MESSAGE_LENGTH:
                return joke
        return error_message


class Poem(Command):
    @property
    def command_name(self) -> str:
        return f"{TRIGGER}poem"

    async def execute(self, user=TwitchUser(), message=""):
        num_lines = 4
        num_attempts = 5
        url = f"https://poetrydb.org/linecount/{num_lines}/lines"
        error_message = "I couldn't find a short enough poem. Sorry!"
        poems = await self.aio_get(url)

        for i,_ in enumerate(poems):
            # stop parsing poem list after number of attempts
            if i >= num_attempts:
                break

            lines = poems[i]["lines"]
            poem = "; ".join(lines)
            if len(poem) > MAX_MESSAGE_LENGTH:
                continue
            return poem

        # on failure to find a poem, return error_message
        return error_message
