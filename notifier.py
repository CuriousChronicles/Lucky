import os
from dotenv import load_dotenv
import requests

load_dotenv()

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
if not NTFY_TOPIC:
    raise RuntimeError("NTFY_TOPIC not set. Copy .env.example to .env and fill it in.")

NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

def send_notification(title, message, priority="default", tags=None):
    headers = {
        "Title": title,
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = ",".join(tags)

    response = requests.post(NTFY_URL, data=message.encode("utf-8"), headers=headers)
    response.raise_for_status()
