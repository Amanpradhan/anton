"""
Redis event publisher for real-time agent monitoring.

Every time an agent does something meaningful, it publishes an event to
Redis channel `run:{run_id}`. The WebSocket endpoint subscribes to this
channel and streams events to the frontend.
"""

import json
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.config import settings


async def publish_event(
    run_id: str,
    agent: str,
    event_type: str,  # "start" | "thinking" | "tool_call" | "message" | "complete" | "error"
    content: str,
    tokens_used: int = 0,
) -> None:
    event = {
        "run_id": run_id,
        "agent": agent,
        "event_type": event_type,
        "content": content,
        "tokens_used": tokens_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload = json.dumps(event)
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        # Buffer event in a list so late WebSocket connections can replay missed events
        buf_key = f"run:events:{run_id}"
        await r.rpush(buf_key, payload)
        await r.expire(buf_key, 3600)  # keep for 1 hour then auto-clean
        # Also publish for any already-connected WebSocket subscribers
        await r.publish(f"run:{run_id}", payload)
    finally:
        await r.aclose()
