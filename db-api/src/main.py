import uvicorn
from models import database, Tokens, TextCommands
from fastapi import FastAPI, Request

SUCCESS = {"status": "success"}
FAILURE = {"status": "failure"}
PLATFORMS = ["twitch", "youtube"]

app = FastAPI()
database.create_tables([Tokens, TextCommands])

@app.get("/")
async def main():
    return "Running!"


@app.post("/chat/write/")
async def store_chat(payload:Request):
    pass


@app.post("/commands/add/{platform}/")
async def add_command(platform:str, payload:Request):
    data = await payload.json()
    name = data["name"]
    output = data["output"]

    try:
        if platform.strip():
            statement = TextCommands.insert(
                    name=name, 
                    output=output,
                    platform=platform
                )

        else:
            entries = []
            for platform in PLATFORMS:
                entry = {"name":name, "output":output, "platform":platform}
                entries.append(entry)

            statement = TextCommands.insert(entries)

        statement.execute()
        return SUCCESS

    except Exception as e:
        return FAILURE


@app.post("/commands/edit/{platform}/")
async def edit_command(platform:str, payload:Request):
    data = await payload.json()
    name = data["name"]
    output = data["output"]

    try:
        if platform.strip():
            statement = (TextCommands
                        .update({TextCommands.output: output})
                        .where(
                            TextCommands.name == name, 
                            TextCommands.platform==platform
                            )
                        )
        else:
            statement = (TextCommands
                        .update({TextCommands.output: output})
                        .where(TextCommands.name == name)
                        )
        statement.execute()
        return SUCCESS

    except Exception as e:
        print(e)
        return FAILURE


@app.post("/commands/delete/{platform}/")
async def delete_command(platform:str, payload:Request):
    data = await payload.json()
    name = data["name"]

    try:
        if platform.strip():
            statement = (TextCommands
                        .delete()
                        .where(
                            TextCommands.name == name, 
                            TextCommands.platform == platform
                            )
                        )
        else:
            statement = TextCommands.delete().where(TextCommands.name == name)
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
        commands = [c.name for c in result]
        return commands

    except Exception as e:
        print(e)
        return FAILURE


@app.get("/commands/output/{platform}/{name}/")
async def get_command_output(platform:str, name:str) -> dict:
    try:
        output = TextCommands.get(
                TextCommands.platform == platform,
                TextCommands.name == name
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1337)

