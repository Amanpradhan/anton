from datetime import datetime

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    workflow_id: str
    input: str = Field(..., min_length=1)
    trigger_source: str = "api"
    trigger_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    run_id: str
    sender: str
    recipient: str
    content: str
    message_type: str
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    input: str | None
    trigger_source: str
    trigger_id: str | None
    output: str | None
    error: str | None
    total_tokens: int
    estimated_cost_usd: float
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}
