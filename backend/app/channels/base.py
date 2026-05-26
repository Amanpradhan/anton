"""
Base channel interface — every messaging channel must implement this.
Adding a new channel = create a new file that implements BaseChannel.
"""

from abc import ABC, abstractmethod


class BaseChannel(ABC):
    @abstractmethod
    async def send_message(self, recipient_id: str, text: str) -> None:
        """Send a text message to a recipient."""

    @abstractmethod
    async def parse_incoming(self, payload: dict) -> tuple[str | None, str | None]:
        """
        Parse an incoming webhook payload.
        Returns (user_message, sender_id) or (None, None) if not a text message.
        """
