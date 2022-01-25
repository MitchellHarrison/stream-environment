import requests
import os
import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow

DB_API = os.environ.get("DB_API", "")
DB_API_PORT = os.environ.get("DB_API_PORT", "")
DATABASE = f"http://{DB_API}:{DB_API_PORT}"

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

API_SERVICE = "youtube"
API_VERSION = "v3"
SECRETS_FILE = "./web_secrets.json"

PORT = int(os.environ.get("YOUTUBE_BOT_PORT", 6120))
print(PORT)

def get_credentials() -> dict:
    try:
        flow = InstalledAppFlow.from_client_secrets_file(SECRETS_FILE, SCOPES)
    except:
        flow = InstalledAppFlow.from_client_secrets_file("../web_secrets.json", SCOPES)

    print("Getting credentials...")
    creds = flow.run_local_server(
        port = PORT,
        prompt = "consent"
    )
    payload = {
        "name": "yt_access",
        "token": creds.__dict__["token"]
    }
    try:
        requests.post(f"{DATABASE}/tokens/set/", data=payload)
    except:
        print("tokens 'set'")
    return creds

def get_live_chat_id(creds) -> str:
    yt = googleapiclient.discovery.build(API_SERVICE, API_VERSION, credentials=creds)
    print("Getting live access token...")
    request = yt.liveBroadcasts().list(
        part = "snippet",
        broadcastStatus = "active"
    )
    response = request.execute()

    live_chat_id = response["items"][0]["snippet"]["liveChatId"]
    payload = {
        "name": "yt_live_chat_id",
        "token": live_chat_id
    }
    try:
        requests.post(f"{DATABASE}/tokens/set/", data=payload)
    except:
        print("live id 'set'")
    return live_chat_id

def main():
    # get creds from db here
    creds = None
    live_chat_id = None
    if not creds:
        creds = get_credentials()

    if not live_chat_id:
        live_chat_id = get_live_chat_id(creds)
        

if __name__ == "__main__":
    main()
