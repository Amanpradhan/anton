"""
Tests for Agent CRUD endpoints.

Critical paths:
- Create agent with full config → persisted correctly
- Get, update, delete → correct responses
- Missing required fields → 422 validation error
- Delete nonexistent → 404
"""

import pytest
from httpx import AsyncClient

from tests.conftest import AGENT_PAYLOAD

pytestmark = pytest.mark.asyncio


async def test_list_agents_empty(client: AsyncClient):
    """Fresh DB has no agents."""
    resp = await client.get("/api/agents/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_agent(client: AsyncClient):
    """Creating an agent returns it with a generated ID."""
    resp = await client.post("/api/agents/", json=AGENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == AGENT_PAYLOAD["name"]
    assert data["role"] == AGENT_PAYLOAD["role"]
    assert data["tools"] == AGENT_PAYLOAD["tools"]
    assert data["channels"] == AGENT_PAYLOAD["channels"]
    assert "id" in data
    assert data["is_active"] is True


async def test_create_agent_missing_required_fields(client: AsyncClient):
    """Missing name/role/system_prompt returns 422."""
    resp = await client.post("/api/agents/", json={"name": "Incomplete"})
    assert resp.status_code == 422


async def test_get_agent(client: AsyncClient):
    """Get agent by ID returns the correct record."""
    create = await client.post("/api/agents/", json=AGENT_PAYLOAD)
    agent_id = create.json()["id"]

    resp = await client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id
    assert resp.json()["name"] == AGENT_PAYLOAD["name"]


async def test_get_agent_not_found(client: AsyncClient):
    """Non-existent ID returns 404."""
    resp = await client.get("/api/agents/does-not-exist")
    assert resp.status_code == 404


async def test_list_agents_after_create(client: AsyncClient):
    """List includes the created agent."""
    await client.post("/api/agents/", json=AGENT_PAYLOAD)
    resp = await client.get("/api/agents/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_update_agent(client: AsyncClient):
    """Patch updates only the specified fields."""
    create = await client.post("/api/agents/", json=AGENT_PAYLOAD)
    agent_id = create.json()["id"]

    resp = await client.patch(f"/api/agents/{agent_id}", json={"name": "Updated Name", "is_active": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["is_active"] is False
    # Unpatched fields stay the same
    assert data["role"] == AGENT_PAYLOAD["role"]


async def test_update_agent_not_found(client: AsyncClient):
    resp = await client.patch("/api/agents/ghost", json={"name": "X"})
    assert resp.status_code == 404


async def test_delete_agent(client: AsyncClient):
    """Deleting an agent returns 204 and removes it from list."""
    create = await client.post("/api/agents/", json=AGENT_PAYLOAD)
    agent_id = create.json()["id"]

    resp = await client.delete(f"/api/agents/{agent_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 404


async def test_delete_agent_not_found(client: AsyncClient):
    resp = await client.delete("/api/agents/ghost")
    assert resp.status_code == 404


async def test_agent_temperature_validation(client: AsyncClient):
    """Temperature above 2.0 should fail validation."""
    payload = {**AGENT_PAYLOAD, "temperature": 5.0}
    resp = await client.post("/api/agents/", json=payload)
    assert resp.status_code == 422
