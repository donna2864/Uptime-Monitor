import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def send_webhook(message:str):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("[ALERT] WEBHOOK_URL is not configured")
        return False
    try:
        response = httpx.post(
            webhook_url,
            json={"content":message},
            timeout=10.0
        )
        response.raise_for_status()
        print("[ALERT] Webhook notification sent")
        return True
    except httpx.HTTPError as error:
        print(f"[ALERT] Failed to send webhook: {error}")
        return False