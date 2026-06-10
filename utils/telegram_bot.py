import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "Token atau Chat ID Telegram belum diatur di file .env. Silakan buat file .env dengan TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID."
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, "Pesan berhasil dikirim ke Telegram!"
        else:
            return False, f"Gagal mengirim pesan: {response.text}"
    except Exception as e:
        return False, f"Error: {e}"
