"""
Tests for Run creation and retrieval.

Critical paths:
- Create run with valid workflow → 202 + run record created
- Create run with unknown workflow → 404
- Get run → correct status and fields
- Run is created with PENDING status initially

Note: We do NOT test the full pipeline execution here (that would
require real LLM + Redis). The runner itself is tested in test_runtime.py.
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from tests.conftest import WORKFLOW_PAYLOAD

pytestmark = pytest.mark.asyncio


async def _create_workflow(client: AsyncClient) -> str:
    resp = await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)
    return resp.json()["id"]


async def test_create_run_no_workflow(client: AsyncClient):
    """Run creation with non-existent workflow returns 404."""
    resp = await client.post("/api/runs/", json={
        "workflow_id": "does-not-exist",
        "input": "Analyze the fintech market",
    })
    assert resp.status_code == 404


async def test_create_run_returns_202(client: AsyncClient):
    """
    Run creation returns 202 Accepted immediately.
    The pipeline runs in the background — API doesn't block.
    """
    wf_id = await _create_workflow(client)

    with patch("app.api.routes.runs.run_workflow", new_callable=AsyncMock):
        resp = await client.post("/api/runs/", json={
            "workflow_id": wf_id,
            "input": "Analyze payment processors in LATAM",
        })

    assert resp.status_code == 202
    data = resp.json()
    assert data["workflow_id"] == wf_id
    assert data["status"] == "pending"
    assert data["input"] == "Analyze payment processors in LATAM"
    assert "id" in data


async def test_create_run_persists_trigger_source(client: AsyncClient):
    """Trigger source is stored correctly."""
    wf_id = await _create_workflow(client)

    with patch("app.api.routes.runs.run_workflow", new_callable=AsyncMock):
        resp = await client.post("/api/runs/", json={
            "workflow_id": wf_id,
            "input": "Test",
            "trigger_source": "telegram",
            "trigger_id": "12345678",
        })

    assert resp.status_code == 202
    data = resp.json()
    assert data["trigger_source"] == "telegram"
    assert data["trigger_id"] == "12345678"


async def test_get_run(client: AsyncClient):
    """Get run by ID returns the correct record with messages list."""
    wf_id = await _create_workflow(client)

    with patch("app.api.routes.runs.run_workflow", new_callable=AsyncMock):
        create = await client.post("/api/runs/", json={
            "workflow_id": wf_id,
            "input": "Test analysis",
        })

    run_id = create.json()["id"]
    resp = await client.get(f"/api/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == run_id
    assert data["messages"] == []  # No messages yet (pipeline mocked)
    assert data["total_tokens"] == 0
    assert data["estimated_cost_usd"] == 0.0


async def test_get_run_not_found(client: AsyncClient):
    resp = await client.get("/api/runs/does-not-exist")
    assert resp.status_code == 404


async def test_list_runs(client: AsyncClient):
    """List runs returns all created runs."""
    wf_id = await _create_workflow(client)

    with patch("app.api.routes.runs.run_workflow", new_callable=AsyncMock):
        await client.post("/api/runs/", json={"workflow_id": wf_id, "input": "First"})
        await client.post("/api/runs/", json={"workflow_id": wf_id, "input": "Second"})

    resp = await client.get("/api/runs/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
