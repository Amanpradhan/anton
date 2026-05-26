from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    model: str = "gemini-2.0-flash"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    tools: list[str] = []
    channels: list[str] = []
    memory_enabled: bool = True
    memory_window: int = Field(10, ge=1, le=100)
    max_tokens: int = Field(2048, ge=256, le=32768)
    max_iterations: int = Field(10, ge=1, le=50)
    schedule: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = None
    tools: list[str] | None = None
    channels: list[str] | None = None
    memory_enabled: bool | None = None
    memory_window: int | None = None
    max_tokens: int | None = None
    max_iterations: int | None = None
    schedule: str | None = None
    is_active: bool | None = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: str
    model: str
    temperature: float
    tools: list[str]
    channels: list[str]
    memory_enabled: bool
    memory_window: int
    max_tokens: int
    max_iterations: int
    schedule: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
