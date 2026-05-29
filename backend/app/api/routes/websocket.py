"""
WebSocket endpoint for real-time run monitoring.

Flow:
  Frontend connects → ws://localhost:8000/ws/runs/{run_id}
  Backend subscribes to Redis channel `run:{run_id}`
  Each agent event published to Redis is forwarded to the WebSocket client
  Connection closes when the run completes or client disconnects
"""

import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_events(websocket: WebSocket, run_id: str):
    await websocket.accept()

    r = aioredis.from_url(settings.redis_url, decode_responses=True)

    # Replay any events that were published before this WebSocket connected
    # (fixes the race condition where the pipeline starts before the browser opens the run page)
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
        await r.aclose()
        return

    pubsub = r.pubsub()
    await pubsub.subscribe(f"run:{run_id}")

    try:
        while True:
            # Poll for a message with a 15s timeout, then send a heartbeat to keep the connection alive
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1),
                    timeout=15,
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event_type": "ping"}))
                continue

            if message is None:
                continue

            data = message["data"]
            await websocket.send_text(data)

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
