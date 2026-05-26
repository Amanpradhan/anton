from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    graph: dict = {}
    trigger_channel: str | None = None
    is_template: bool = False


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    graph: dict | None = None
    trigger_channel: str | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None
    graph: dict
    trigger_channel: str | None
    is_template: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
