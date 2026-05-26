"""
Tests for the Telegram channel integration.

Critical paths:
- parse_incoming: correctly extracts text + chat_id from valid update
- parse_incoming: returns (None, None) for non-text updates
- Webhook with no active workflow → sends fallback message
- Webhook with valid message + active workflow → creates run and acknowledges
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.channels.telegram import TelegramChannel
from tests.conftest import WORKFLOW_PAYLOAD

pytestmark = pytest.mark.asyncio


# ── Unit tests for TelegramChannel ───────────────────────────────────────────

async def test_parse_incoming_valid_message():
    """Valid Telegram message payload is parsed correctly."""
    channel = TelegramChannel()
    payload = {
        "message": {
            "text": "Analyze fintech in LATAM",
            "chat": {"id": 987654321},
        }
    }
    text, chat_id = await channel.parse_incoming(payload)
    assert text == "Analyze fintech in LATAM"
    assert chat_id == "987654321"


async def test_parse_incoming_no_message():
    """Payload without message field returns (None, None)."""
    channel = TelegramChannel()
    text, chat_id = await channel.parse_incoming({})
    assert text is None
    assert chat_id is None


async def test_parse_incoming_no_text():
    """Non-text update (sticker, photo, etc.) returns (None, None)."""
    channel = TelegramChannel()
    payload = {"message": {"sticker": {}, "chat": {"id": 123}}}
    text, chat_id = await channel.parse_incoming(payload)
    assert text is None
    assert chat_id is None


async def test_parse_incoming_edited_message():
    """Edited messages are also parsed correctly."""
    channel = TelegramChannel()
    payload = {
        "edited_message": {
            "text": "Updated request",
            "chat": {"id": 111222333},
        }
    }
    text, chat_id = await channel.parse_incoming(payload)
    assert text == "Updated request"
    assert chat_id == "111222333"


# ── Webhook endpoint tests ────────────────────────────────────────────────────

TELEGRAM_UPDATE = {
    "message": {
        "text": "Analyze payment processors in Brazil",
        "chat": {"id": 42424242},
    }
}


async def test_webhook_no_active_workflow(client: AsyncClient):
    """
    When no Telegram-connected workflow exists, the bot sends a
    fallback message and returns 200 OK.
    """
    with patch("app.api.routes.channels.telegram.send_message", new_callable=AsyncMock) as mock_send:
        resp = await client.post("/api/channels/telegram/webhook", json=TELEGRAM_UPDATE)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    # Bot should have sent a "no workflow" message
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0]
    assert "42424242" == call_args[0]
    assert "workflow" in call_args[1].lower()


async def test_webhook_with_active_workflow(client: AsyncClient):
    """
    With an active Telegram workflow, the webhook acknowledges the user
    and triggers the pipeline in the background.
    """
    # Create an active Telegram workflow
    await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)

    with patch("app.api.routes.channels.telegram.send_message", new_callable=AsyncMock) as mock_send, \
         patch("app.api.routes.channels._run_and_reply", new_callable=AsyncMock):

        resp = await client.post("/api/channels/telegram/webhook", json=TELEGRAM_UPDATE)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    # Bot sent the acknowledgment message
    mock_send.assert_called_once()
    ack_message = mock_send.call_args[0][1]
    assert "pipeline" in ack_message.lower() or "analysis" in ack_message.lower() or "it" in ack_message.lower()


async def test_webhook_ignores_non_text_update(client: AsyncClient):
    """Non-text updates (joins, stickers) are silently ignored."""
    with patch("app.api.routes.channels.telegram.send_message", new_callable=AsyncMock) as mock_send:
        resp = await client.post("/api/channels/telegram/webhook", json={
            "message": {"sticker": {}, "chat": {"id": 999}}
        })

    assert resp.status_code == 200
    mock_send.assert_not_called()


async def test_webhook_info_endpoint(client: AsyncClient):
    """Info endpoint calls Telegram API and returns webhook data."""
    mock_response = {"ok": True, "result": {"url": "", "has_custom_certificate": False}}
    with patch("app.api.routes.channels.get_webhook_info", new_callable=AsyncMock, return_value=mock_response):
        resp = await client.get("/api/channels/telegram/info")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
