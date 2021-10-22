import os
import urllib
import webbrowser
import requests
from dotenv import load_dotenv
from sanic import Sanic, Request
from sanic.response import text
load_dotenv("../credentials.env")

# credential imports
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
OAUTH_TOKEN = os.getenv("OAUTH_TOKEN")
CALLBACK = os.getenv("CALLBACK")

# eventsub callback creds
HOST = "127.0.0.1"
PORT = 5000
LOCAL_ADDRESS = f"https://{HOST}:{PORT}"
SCOPES = [
    "bits:read",
    "channel:read:subscriptions",
    "channel:moderate",
    "channel:read:redemptions",
]

# database API creds
DB_URL = "http://127.0.0.1:1337"

# ssl things
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")
ssl = {"cert": CERT_PATH, "key": KEY_PATH}

app = Sanic("twitch_eventsub")

def get_user_auth(client_id:str = CLIENT_ID, scopes:list = SCOPES):
    url = "https://id.twitch.tv/oauth2/authorize"

    # create appropriate url for authorizing permissions
    params = {
        "client_id": client_id, 
        "redirect_uri": "https://127.0.0.1:5000/authorize",
        "response_type": "code",
        "scope": " ".join(scopes),
        "force_verify": "true"
    }
    get_url = url + "?" + urllib.parse.urlencode(params)

    # open browser window for user to accept required permissions
    webbrowser.open(get_url)


async def aio_get(url:str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            response = await r.json()
            print(response)
            return response
     

async def aio_post(url:str, payload:dict, **kwargs) -> None:
    data = json.dumps(payload).encode("ascii")
    async with aiohttp.ClientSession() as session:
        await session.post(url, data=data) 


@app.get("/") 
async def root(request):
    get_user_auth()
    return text("Hey, it worked!")


@app.route("/authorize")
async def authorize(request):
    code = request.args["code"][0]
     
    # get user access token using the above code
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{LOCAL_ADDRESS}/authorize"
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            url=url,
            client_id = CLIENT_ID,
            client_secret = CLIENT_SECRET,
            code = code,
            grant_type = "authorization_code",
            redirect_uri = f"{LOCAL_ADDRESS}/authorize"
        )
        data = response.json()
    #response = requests.post(url=url, params=params)
    #data = response.json()

    app_access = data["access_token"]
    app_access_payload = {"name":"app_access", "token":app_access}
    aio_post(f"{DB_URL}/tokens/set/", app_access_payload)

    refresh = data["refresh_token"]
    refresh_payload = {"name":"refresh", "token":refresh}
    aio_post(f"{DB_URL}/tokens/set/", refresh_payload)
    #write_token("refresh", refresh_token)

    return text("boom, it worked")


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, ssl=ssl)

