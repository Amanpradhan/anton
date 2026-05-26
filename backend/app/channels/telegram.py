"""
Telegram channel adapter.

Implements BaseChannel for the Telegram Bot API.
Handles incoming webhook updates and outgoing messages.
"""

import httpx

from app.channels.base import BaseChannel
from app.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


class TelegramChannel(BaseChannel):
    async def send_message(self, recipient_id: str, text: str) -> None:
        """Send a message to a Telegram chat. Splits long messages automatically."""
        # Telegram max message length is 4096 chars
        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
        async with httpx.AsyncClient() as client:
            for chunk in chunks:
                await client.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={"chat_id": recipient_id, "text": chunk},
                    timeout=10,
                )

    async def parse_incoming(self, payload: dict) -> tuple[str | None, str | None]:
        """Extract (user_message, chat_id) from a Telegram update payload."""
        message = payload.get("message") or payload.get("edited_message")
        if not message:
            return None, None
        text = message.get("text")
        chat_id = str(message.get("chat", {}).get("id"))
        if not text or not chat_id:
            return None, None
        return text, chat_id


async def register_webhook(webhook_url: str) -> dict:
    """Register our webhook URL with Telegram. Called from the setup endpoint."""
    url = f"{webhook_url}/api/channels/telegram/webhook"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={"url": url, "allowed_updates": ["message", "edited_message"]},
            timeout=10,
        )
        return response.json()


async def get_webhook_info() -> dict:
    """Get current webhook status from Telegram."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TELEGRAM_API}/getWebhookInfo", timeout=10)
        return response.json()


# Singleton used by route handlers
telegram = TelegramChannel()
