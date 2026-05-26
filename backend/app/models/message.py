import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Who sent it: agent name or "user" or "system"
    sender: Mapped[str] = mapped_column(String(100), nullable=False)
    # Who it's addressed to: agent name or "user"
    recipient: Mapped[str] = mapped_column(String(100), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Message type: "task", "result", "critique", "user_input", "final_output"
    message_type: Mapped[str] = mapped_column(String(50), default="task")

    # Token usage for this specific message
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
