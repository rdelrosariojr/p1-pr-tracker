import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")


def send_message(text):
    if not SLACK_WEBHOOK:
        raise ValueError("Missing SLACK_WEBHOOK")

    resp = requests.post(SLACK_WEBHOOK, json={
        "text": text
    })

    resp.raise_for_status()