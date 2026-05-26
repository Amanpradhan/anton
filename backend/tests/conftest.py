"""
Test configuration and shared fixtures.

Strategy:
- SQLite in-memory DB per test session — no Docker, no PostgreSQL needed
- Each test gets a clean transaction that rolls back after the test
- Redis and LLM calls are mocked — tests are fast and offline-safe
- FastAPI's dependency injection is overridden to use the test DB
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, patch

from app.db.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create the test engine and tables once per session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """
    Per-test transactional session.
    Rolls back after every test so tests are fully isolated.
    """
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """
    FastAPI test client with:
    - DB overridden to use the test SQLite session
    - Redis publish calls mocked (no Redis needed)
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.runtime.events.publish_event", new_callable=AsyncMock):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c

    app.dependency_overrides.clear()


# ── Shared test data ──────────────────────────────────────────────────────────

AGENT_PAYLOAD = {
    "name": "Test Researcher",
    "role": "Web Research Specialist",
    "system_prompt": "You are a helpful research agent.",
    "model": "gemini-2.0-flash",
    "temperature": 0.7,
    "tools": ["web_search"],
    "channels": ["telegram"],
    "memory_enabled": True,
    "memory_window": 10,
    "max_tokens": 2048,
    "max_iterations": 10,
    "schedule": None,
}

WORKFLOW_PAYLOAD = {
    "name": "Test CI Pipeline",
    "description": "Competitive intelligence workflow for testing",
    "graph": {
        "nodes": [
            {"id": "orchestrator", "label": "Orchestrator", "role": "Plans the research"},
            {"id": "researcher",   "label": "Researcher",   "role": "Runs searches"},
        ],
        "edges": [
            {"source": "orchestrator", "target": "researcher", "label": ""},
        ],
    },
    "trigger_channel": "telegram",
    "is_template": False,
}
