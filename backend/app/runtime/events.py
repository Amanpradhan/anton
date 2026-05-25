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
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await r.publish(f"run:{run_id}", json.dumps(event))
    finally:
        await r.aclose()
