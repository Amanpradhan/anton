import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # LLM config
    model: Mapped[str] = mapped_column(String(100), default="gemini-2.5-flash")
    temperature: Mapped[float] = mapped_column(default=0.7)

    # Tools the agent can use (list of tool names)
    tools: Mapped[list] = mapped_column(JSON, default=list)

    # Connected messaging channels (e.g. ["telegram"])
    channels: Mapped[list] = mapped_column(JSON, default=list)

    # Memory config
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    memory_window: Mapped[int] = mapped_column(default=10)  # last N messages

    # Guardrails
    max_tokens: Mapped[int] = mapped_column(default=2048)
    max_iterations: Mapped[int] = mapped_column(default=10)

    # Schedule (cron expression, null = no schedule)
    schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
