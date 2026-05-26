import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import update

from app.api.routes import agents, channels, evals, runs, websocket, workflows
from app.config import settings
from app.db.database import AsyncSessionLocal, create_tables
from app.models.run import Run, RunStatus


def _configure_langsmith() -> None:
    """Enable LangSmith tracing if API key is provided."""
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


async def _cleanup_orphaned_runs() -> None:
    """Mark any runs still in RUNNING/PENDING state as FAILED on startup.
    These are runs that were killed when the server was last restarted."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Run)
            .where(Run.status.in_([RunStatus.RUNNING, RunStatus.PENDING]))
            .values(
                status=RunStatus.FAILED,
                error="Server restarted while run was in progress.",
                completed_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_langsmith()
    await create_tables()
    await _cleanup_orphaned_runs()
    yield


app = FastAPI(
    title="Anton",
    description="Autonomous multi-agent competitive intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST routes
app.include_router(agents.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(channels.router, prefix="/api")
app.include_router(evals.router, prefix="/api")

# WebSocket
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "anton"}
