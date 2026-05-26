"""
WebSocket endpoint for real-time run monitoring.

Flow:
  Frontend connects → ws://localhost:8000/ws/runs/{run_id}
  Backend subscribes to Redis channel `run:{run_id}`
  Each agent event published to Redis is forwarded to the WebSocket client
  Connection closes when the run completes or client disconnects
"""

import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_events(websocket: WebSocket, run_id: str):
    await websocket.accept()

    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe(f"run:{run_id}")

    try:
        async for message in pubsub.listen():
            # pubsub.listen() yields control/subscribe confirmation messages too
            if message["type"] != "message":
                continue

            data = message["data"]
            await websocket.send_text(data)

            # Auto-close WebSocket when run finishes or errors
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
