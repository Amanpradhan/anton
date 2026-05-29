"""
WebSocket endpoint for real-time run monitoring.

Flow:
  Frontend connects → ws://localhost:8000/ws/runs/{run_id}
  1. Subscribe to Redis pubsub FIRST (no event gap)
  2. Replay buffered events from Redis list (catch-up)
  3. Forward live pubsub messages as they arrive
  4. Send heartbeat ping every 15s of silence to keep connection alive
  Connection closes when the run completes or client disconnects
"""

import json
import time

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_events(websocket: WebSocket, run_id: str):
    await websocket.accept()

    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()

    # Subscribe FIRST — no events can be missed after this point
    await pubsub.subscribe(f"run:{run_id}")

    # Replay buffered events (published before this WebSocket connected)
    buffered = await r.lrange(f"run:events:{run_id}", 0, -1)
    already_done = False
    for data in buffered:
        await websocket.send_text(data)
        try:
            parsed = json.loads(data)
            if parsed.get("event_type") in ("complete", "error"):
                already_done = True
        except (json.JSONDecodeError, AttributeError):
            pass

    if already_done:
        await pubsub.unsubscribe(f"run:{run_id}")
        await pubsub.aclose()
        await r.aclose()
        return

    # Forward live events with a time-based heartbeat every 15s
    last_heartbeat = time.monotonic()

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            now = time.monotonic()
            if now - last_heartbeat >= 15:
                await websocket.send_text(json.dumps({"event_type": "ping"}))
                last_heartbeat = now

            if message is None:
                continue

            data = message["data"]
            await websocket.send_text(data)
            last_heartbeat = now  # reset heartbeat on any real message

            try:
                parsed = json.loads(data)
                if parsed.get("event_type") in ("complete", "error"):
                    break
            except (json.JSONDecodeError, AttributeError):
                pass

    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"run:{run_id}")
        await pubsub.aclose()
        await r.aclose()
