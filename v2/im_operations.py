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



@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def send_slack_message(bot_token: str, channel_id: str, message: str):
    """
    Send a message to a Slack channel.
    :param bot_token: The Slack bot token (starts with 'xoxb-').
    :param channel_id: The ID of the channel to send the message to (e.g., '#general' or 'C1234567890').
    :param message: The message to send.
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel_id,
        "text": message,
    }
    
    print(f"Sending message to channel: {channel_id}")
    print(f"Message: {message}")
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    
    print(f"Slack API response: {data}")
    
    if not data["ok"]:
        raise Exception(f"Slack API error: {data.get('error', 'Unknown error')}")
    else:
        print("Message sent successfully!")


@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def send_slack_webhook_message(webhook_url: str, message: str):
    """
    Send a message to a Slack channel using a webhook URL.
    :param webhook_url: The Slack webhook URL.
    :param message: The message to send.
    """
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()


if __name__ == "__main__":
    send_slack_message(
        bot_token="xoxb-2185937878-9210919414386-ygxJV4IU4AZeRxguMUesC2tZ",
        channel_id="C097670USVB",
        message="Hello, world!"
    )