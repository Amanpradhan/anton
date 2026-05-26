from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.workflow import Workflow
from app.runtime.templates import TEMPLATES
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(payload: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = Workflow(**payload.model_dump())
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return workflow


@router.get("/templates", tags=["templates"])
async def list_templates():
    """Return the pre-built workflow templates."""
    return list(TEMPLATES.values())


@router.post("/from-template/{template_id}", response_model=WorkflowResponse, status_code=201)
async def create_from_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Instantiate a new workflow from a pre-built template."""
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    tmpl = TEMPLATES[template_id]
    workflow = Workflow(
        name=tmpl["name"],
        description=tmpl["description"],
        graph=tmpl["graph"],
        trigger_channel="telegram",
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(workflow, field, value)
    await db.flush()
    await db.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(workflow)
