import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.message import Message
from app.models.run import Run, RunStatus
from app.models.workflow import Workflow
from app.runtime.runner import run_workflow
from app.schemas.run import RunCreate, RunResponse

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[RunResponse])
async def list_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run).order_by(Run.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=RunResponse, status_code=202)
async def create_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Verify workflow exists
    wf_result = await db.execute(select(Workflow).where(Workflow.id == payload.workflow_id))
    workflow = wf_result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create the run record immediately so the client gets a run_id to track
    run = Run(
        id=str(uuid.uuid4()),
        workflow_id=payload.workflow_id,
        status=RunStatus.PENDING,
        input=payload.input,
        trigger_source=payload.trigger_source,
        trigger_id=payload.trigger_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    run_id = run.id

    # Execute the pipeline in the background — API returns 202 immediately
    background_tasks.add_task(
        run_workflow,
        run_id=run_id,
        workflow_id=payload.workflow_id,
        user_input=payload.input,
        trigger_source=payload.trigger_source,
        trigger_id=payload.trigger_id,
    )

    return run


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Load messages for this run
    msg_result = await db.execute(
        select(Message).where(Message.run_id == run_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    # Attach messages to run object for serialization
    run.messages = messages
    return run
