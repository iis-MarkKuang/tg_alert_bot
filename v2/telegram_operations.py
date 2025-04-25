import requests
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def send_telegram_message(bot_token: str, chat_id: str, message: str):
    """
    Send a message to a Telegram chat.
    :param bot_token: The Telegram bot token.
    :param chat_id: The ID of the chat to send the message to.
    :param message: The message to send.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    data = response.json()
    assert data["ok"]
