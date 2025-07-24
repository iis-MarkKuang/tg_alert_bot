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
def send_slack_webhook_message(webhook_url: str, message: str, slack_member_uids: str):
    """
    Send a message to a Slack channel using a webhook URL.
    :param slack_member_uids:
    :param webhook_url: The Slack webhook URL.
    :param message: The message to send.
    """
    message += f" 请帮忙处理 <@{'> <@'.join(slack_member_uids.split(','))}>"

    payload = {"text": message}
    
    print(f"Sending webhook message to: {webhook_url}")
    print(f"Message: {message}")
    
    response = requests.post(webhook_url, json=payload)
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    response.raise_for_status()


@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def get_slack_user_info(bot_token: str, user_email: str = None):
    """
    Get user information from Slack API.
    :param bot_token: The Slack bot token.
    :param user_email: Email to search for (optional).
    """
    url = "https://slack.com/api/users.list"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    if not data["ok"]:
        raise Exception(f"Slack API error: {data.get('error', 'Unknown error')}")
    
    users = data["members"]
    print("Available users:")
    for user in users:
        if not user.get("deleted", False):  # Skip deleted users
            user_id = user["id"]
            name = user.get("name", "Unknown")
            real_name = user.get("real_name", "Unknown")
            print(f"  {real_name} (@{name}): {user_id}")
    
    return users


if __name__ == "__main__":
    # Option 1: Using bot token (requires proper scopes and valid token)
    # send_slack_message(
    #     bot_token="xoxb-2185937878-9210919414386-ygxJV4IU4AZeRxguMUesC2tZ",
    #     channel_id="C097670USVB",
    #     message="Hello, world!"
    # )
    
    # Helper: Get user IDs (uncomment to see all users)
    # get_slack_user_info(bot_token="xoxb-2185937878-9210919414386-ygxJV4IU4AZeRxguMUesC2tZ")
    
    # Option 2: Using webhook URL (simpler and more reliable for alerts)
    # To get a webhook URL:
    # 1. Go to your Slack app settings
    # 2. Go to "Incoming Webhooks" → "Activate Incoming Webhooks"
    # 3. Click "Add New Webhook to Workspace"
    # 4. Choose your channel
    # 5. Copy the webhook URL
    
    # Example messages with mentions:
    # message = "🚨 Alert: <@U1234567890> please check this!"  # Mention specific user
    # message = "🚨 Alert: <!here> system is down!"  # Mention online users
    # message = "🚨 Alert: <!channel> urgent attention needed!"  # Mention everyone
    
    send_slack_webhook_message(
        webhook_url="https://hooks.slack.com/services/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",  # Replace with your new webhook URL
        message="Hello <@U075GVBRVHD> please check this alert!",  # Replace U1234567890 with your actual user ID (starts with U)
        slack_member_uids="U06EPUT1F0U,U05UFDH8T7B,U0435QQSTNK,U07MWLMR2LB,U04V9BBV3A5,U06UF4K9K9D,U06K0BE946T"
    )
