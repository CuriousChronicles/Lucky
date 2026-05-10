import os
from dotenv import load_dotenv
import requests

load_dotenv()

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
if not NTFY_TOPIC:
    raise RuntimeError("NTFY_TOPIC not set. Copy .env.example to .env and fill it in.")

NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

requests.post(NTFY_URL,
    data="This is a test message",
    headers={
        "Title": "Test Message",
    })