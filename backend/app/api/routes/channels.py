"""
Channel webhook routes.

POST /api/channels/telegram/webhook  — receives messages from Telegram
POST /api/channels/telegram/setup    — registers our URL with Telegram
GET  /api/channels/telegram/info     — check current webhook status
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.telegram import get_webhook_info, register_webhook, telegram
from app.config import settings
from app.db.database import get_db
from app.models.run import Run, RunStatus
from app.models.workflow import Workflow
from app.runtime.runner import run_workflow

router = APIRouter(prefix="/channels", tags=["channels"])


# ── Telegram ──────────────────────────────────────────────────────────────────

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()
    user_message, chat_id = await telegram.parse_incoming(payload)

    if not user_message or not chat_id:
        return {"ok": True}  # Ignore non-text updates (stickers, joins, etc.)

    # Find the active workflow connected to Telegram
    result = await db.execute(
        select(Workflow)
        .where(Workflow.trigger_channel == "telegram", Workflow.is_active == True)
        .limit(1)
    )
    workflow = result.scalar_one_or_none()

    if not workflow:
        await telegram.send_message(
            chat_id,
            "No active workflow is connected to Telegram yet.\n"
            "Set one up at the Anton dashboard.",
        )
        return {"ok": True}

    # Acknowledge immediately — pipeline takes 30–60s
    await telegram.send_message(
        chat_id,
        f"Got it. Running the analysis pipeline...\n"
        f"I'll send you the results as soon as it's ready.",
    )

    # Create the run record
    run = Run(
        id=str(uuid.uuid4()),
        workflow_id=workflow.id,
        status=RunStatus.PENDING,
        input=user_message,
        trigger_source="telegram",
        trigger_id=chat_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()
    run_id = run.id

    # Execute pipeline + send reply in the background
    background_tasks.add_task(
        _run_and_reply,
        run_id=run_id,
        workflow_id=workflow.id,
        user_input=user_message,
        chat_id=chat_id,
    )

    return {"ok": True}


async def _run_and_reply(run_id: str, workflow_id: str, user_input: str, chat_id: str) -> None:
    """Run the pipeline and send the result back to the Telegram user."""
    try:
        final_output = await run_workflow(
            run_id=run_id,
            workflow_id=workflow_id,
            user_input=user_input,
            trigger_source="telegram",
            trigger_id=chat_id,
        )
        await telegram.send_message(chat_id, final_output)
    except Exception as e:
        await telegram.send_message(
            chat_id,
            f"The pipeline encountered an error: {str(e)[:300]}\n"
            "Please try again or check the Anton dashboard.",
        )


@router.post("/telegram/setup")
async def setup_telegram_webhook():
    """Register our webhook URL with Telegram. Run this once after ngrok is started."""
    if not settings.telegram_webhook_url:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_WEBHOOK_URL is not set in .env. Start ngrok and update the URL first.",
        )
    result = await register_webhook(settings.telegram_webhook_url)
    return result


@router.get("/telegram/info")
async def telegram_webhook_info():
    """Check the current webhook status registered with Telegram."""
    return await get_webhook_info()
