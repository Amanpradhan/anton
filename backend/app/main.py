import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, channels, evals, runs, websocket, workflows
from app.config import settings
from app.db.database import create_tables


def _configure_langsmith() -> None:
    """Enable LangSmith tracing if API key is provided."""
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_langsmith()
    await create_tables()
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
