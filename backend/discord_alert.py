import requests
import json
import os

# To use this, replace this URL with your actual Discord Webhook URL.
# You can get this by going to Discord -> Channel Settings -> Integrations -> Webhooks -> New Webhook
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN")

def send_discord_alert(message: str, title: str = "🤖 AI System Alert", color: int = 0x00ff00):
    """
    Sends a rich embed message to a Discord Webhook.
    color: Hex color code (e.g. 0xff0000 for red, 0x00ff00 for green)
    """
    if "YOUR_WEBHOOK_ID" in DISCORD_WEBHOOK_URL:
        # Silently fail if the user hasn't set up the webhook yet to prevent spamming errors
        return
        
    data = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color
            }
        ]
    }
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL, 
            data=json.dumps(data), 
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

if __name__ == "__main__":
    send_discord_alert("This is a test message from the AI Trading System.", "Test Alert", 0x0000ff)
