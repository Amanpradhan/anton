"""
Tests for Workflow CRUD and template endpoints.

Critical paths:
- Create workflow → persisted with graph structure
- List templates → returns both pre-built templates
- Create from template → instantiates a real workflow record
- Unknown template → 404
"""

import pytest
from httpx import AsyncClient

from tests.conftest import WORKFLOW_PAYLOAD

pytestmark = pytest.mark.asyncio


async def test_list_workflows_empty(client: AsyncClient):
    resp = await client.get("/api/workflows/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_workflow(client: AsyncClient):
    resp = await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == WORKFLOW_PAYLOAD["name"]
    assert data["trigger_channel"] == "telegram"
    assert len(data["graph"]["nodes"]) == 2
    assert len(data["graph"]["edges"]) == 1
    assert "id" in data


async def test_get_workflow(client: AsyncClient):
    create = await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)
    wf_id = create.json()["id"]

    resp = await client.get(f"/api/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id


async def test_get_workflow_not_found(client: AsyncClient):
    resp = await client.get("/api/workflows/does-not-exist")
    assert resp.status_code == 404


async def test_update_workflow(client: AsyncClient):
    create = await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)
    wf_id = create.json()["id"]

    resp = await client.patch(f"/api/workflows/{wf_id}", json={"name": "Renamed", "is_active": False})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["is_active"] is False


async def test_delete_workflow(client: AsyncClient):
    create = await client.post("/api/workflows/", json=WORKFLOW_PAYLOAD)
    wf_id = create.json()["id"]

    resp = await client.delete(f"/api/workflows/{wf_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/workflows/{wf_id}")
    assert resp.status_code == 404


async def test_list_templates(client: AsyncClient):
    """Should always return 2 pre-built templates."""
    resp = await client.get("/api/workflows/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) == 2
    ids = {t["id"] for t in templates}
    assert "competitive_intel" in ids
    assert "market_digest" in ids


async def test_template_has_graph(client: AsyncClient):
    """Each template must have nodes and edges defined."""
    resp = await client.get("/api/workflows/templates")
    for template in resp.json():
        assert len(template["graph"]["nodes"]) > 0
        assert len(template["graph"]["edges"]) > 0


async def test_create_from_template_competitive_intel(client: AsyncClient):
    """Creating from a template instantiates a real workflow record."""
    resp = await client.post("/api/workflows/from-template/competitive_intel")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Competitor Deep Dive"
    assert data["trigger_channel"] == "telegram"
    assert data["is_active"] is True
    assert len(data["graph"]["nodes"]) > 0


async def test_create_from_template_market_digest(client: AsyncClient):
    resp = await client.post("/api/workflows/from-template/market_digest")
    assert resp.status_code == 201
    assert resp.json()["name"] == "Market Trend Weekly Digest"


async def test_create_from_invalid_template(client: AsyncClient):
    """Unknown template ID returns 404."""
    resp = await client.post("/api/workflows/from-template/does_not_exist")
    assert resp.status_code == 404
