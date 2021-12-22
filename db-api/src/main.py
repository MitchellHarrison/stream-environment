import uvicorn
from models import database, Tokens, TextCommands, ChatMessages
from fastapi import FastAPI, Request

SUCCESS = {"status": "success"}
FAILURE = {"status": "failure"}
PLATFORMS = ["twitch"]

app = FastAPI()
database.create_tables([Tokens, TextCommands, ChatMessages])

@app.get("/")
async def main():
    return "Running!"


@app.post("/chat/write/")
async def store_chat(payload:Request):
    pass


@app.post("/commands/add/{platform}/")
async def add_command(platform:str, payload:Request):
    data = await payload.json()
    print(data)
    command = data["command"]
    output = data["output"]

    try:
        # only add to a single platform
        if platform.strip():
            statement = TextCommands.insert(
                    command=command, 
                    output=output,
                    platform=platform
                )

        # add to all platforms
        else:
            entries = []
            for platform in PLATFORMS:
                entry = {"command":command, "output":output, "platform":platform}
                entries.append(entry)

            statement = TextCommands.insert(entries)

        statement.execute()
        return SUCCESS

    except Exception as e:
        return FAILURE


@app.post("/commands/edit/{platform}/")
async def edit_command(platform:str, payload:Request):
    data = await payload.json()
    command = data["name"]
    output = data["output"]

    try:
        if platform.strip():
            statement = (TextCommands
                        .update({TextCommands.output: output})
                        .where(
                            TextCommands.command == command, 
                            TextCommands.platform==platform
                            )
                        )
        else:
            statement = (TextCommands
                        .update({TextCommands.output: output})
                        .where(TextCommands.command == command)
                        )
        statement.execute()
        return SUCCESS

    except Exception as e:
        print(e)
        return FAILURE


@app.post("/commands/delete/{platform}/")
async def delete_command(platform:str, payload:Request):
    data = await payload.json()
    print(data)
    command = data["name"]

    try:
        if platform.strip():
            statement = (TextCommands
                        .delete()
                        .where(
                            TextCommands.command == command, 
                            TextCommands.platform == platform
                            )
                        )
        else:
            statement = TextCommands.delete().where(TextCommands.command == command)
        statement.execute()
        return SUCCESS

    except Exception as e:
        print(e)
        return FAILURE


@app.get("/commands/get-all/{platform}/")
async def get_commands(platform:str):
    try:
        result = (TextCommands
                .select()
                .where(TextCommands.platform == platform)
                ).execute()
        commands = [c.command for c in result]
        return commands

    except Exception as e:
        print(e)
        return FAILURE


@app.get("/commands/output/{platform}/{command}/")
async def get_command_output(platform:str, command:str) -> dict:
    try:
        output = TextCommands.get(
                TextCommands.platform == platform,
                TextCommands.command == command
                ).output
        response = {"output": output}
        return response

    except Exception as e:
        print(e)
        return FAILURE


@app.post("/tokens/set/")
async def set_token(payload:Request):
    data = await payload.json()
    name = data.get("name", "")
    token = data.get("token", "")
    statement = (Tokens
            .insert(name=name, token=token)
            .on_conflict(
                conflict_target = Tokens.name,
                preserve = Tokens.token
                )
            )
    statement.execute()
    return f"Token {name} set!"


@app.get("/tokens/get/")
async def get_token(payload:Request):
    data = await payload.json()
    name = data.get("name", "")
    token = Tokens.select().where(Tokens.name == name).get()
    return token


# time, username, user_id, message, platform
@app.post("/chat/store/")
async def store_chat_message(payload:Request):
    data = await payload.json()
    dt = data["time"] 
    username = data["data"]["username"]
    user_id = data["data"]["user_id"]
    message = data["data"]["message"]
    platform = data["data"]["platform"]
    
    statement = ChatMessages.insert(
            time = dt,
            username = username,
            user_id = user_id, 
            message = message,
            platform = platform
        )
    statement.execute()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1337)
