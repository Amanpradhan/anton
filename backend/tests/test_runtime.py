"""
Tests for the LangGraph runtime.

Critical paths:
- Graph compiles without errors
- Conditional routing logic (route_after_critic) works correctly
- Individual agent nodes produce correct state updates (with mocked LLM)
- Evaluator returns valid score structure
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.runtime.graph import AgentState, compiled_graph, route_after_critic

pytestmark = pytest.mark.asyncio


# ── Graph compilation ─────────────────────────────────────────────────────────

def test_graph_compiles():
    """The compiled LangGraph graph is not None and is callable."""
    assert compiled_graph is not None
    assert hasattr(compiled_graph, "ainvoke")


def test_graph_has_correct_nodes():
    """Graph contains all 5 required agent nodes."""
    graph_def = compiled_graph.get_graph()
    node_ids = set(graph_def.nodes.keys())
    expected = {"orchestrator", "researcher", "analyst", "critic", "reporter"}
    assert expected.issubset(node_ids)


# ── Routing logic ─────────────────────────────────────────────────────────────

def test_route_after_critic_approved():
    """Approved critique routes to reporter."""
    state = {"critique_approved": True, "iteration": 1}
    assert route_after_critic(state) == "reporter"


def test_route_after_critic_rejected_within_limit():
    """Rejected critique within iteration limit routes back to researcher."""
    state = {"critique_approved": False, "iteration": 1}
    assert route_after_critic(state) == "researcher"


def test_route_after_critic_max_iterations_reached():
    """
    Even if critique is rejected, hitting max iterations (3) forces
    the pipeline to move to reporter to avoid infinite loops.
    """
    state = {"critique_approved": False, "iteration": 3}
    assert route_after_critic(state) == "reporter"


def test_route_after_critic_iteration_above_max():
    """Iteration above max also routes to reporter."""
    state = {"critique_approved": False, "iteration": 10}
    assert route_after_critic(state) == "reporter"


def test_route_after_critic_empty_state():
    """Missing keys default to not approved, iteration 0 → researcher."""
    state = {}
    assert route_after_critic(state) == "researcher"


# ── Agent node unit tests (mocked LLM) ───────────────────────────────────────

def _mock_llm_response(content: str, tokens: int = 100) -> MagicMock:
    """Build a mock LLM response object."""
    resp = MagicMock()
    resp.content = content
    resp.usage_metadata = {"total_tokens": tokens}
    return resp


async def test_orchestrator_node_generates_queries():
    """Orchestrator parses numbered list into search queries."""
    from app.runtime.agents.orchestrator import orchestrator_node

    mock_response = _mock_llm_response(
        "1. fintech LATAM market size 2024\n"
        "2. payment processors Latin America\n"
        "3. LATAM fintech funding rounds\n"
        "4. mobile payments Brazil Mexico\n"
        "5. cross-border payments LATAM challenges"
    )

    with patch("app.runtime.agents.orchestrator.get_orchestrator_llm") as mock_llm_fn, \
         patch("app.runtime.agents.orchestrator.publish_event", new_callable=AsyncMock):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        state = {"run_id": "test-run", "input": "Analyze fintech in LATAM", "token_counts": {}}
        result = await orchestrator_node(state)

    assert "search_queries" in result
    assert len(result["search_queries"]) == 5
    assert result["iteration"] == 0
    assert result["token_counts"]["orchestrator"] == 100


async def test_analyst_node_produces_analysis():
    """Analyst node returns analysis string from research data."""
    from app.runtime.agents.analyst import analyst_node

    mock_response = _mock_llm_response("## Executive Summary\nLATAM fintech is growing rapidly.", 250)

    with patch("app.runtime.agents.analyst.get_worker_llm") as mock_llm_fn, \
         patch("app.runtime.agents.analyst.publish_event", new_callable=AsyncMock):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        state = {
            "run_id": "test-run",
            "input": "Analyze fintech",
            "research_data": [{"query": "fintech LATAM", "results": ["Mercado Pago leads the market"]}],
            "token_counts": {},
        }
        result = await analyst_node(state)

    assert "analysis" in result
    assert "Executive Summary" in result["analysis"]
    assert result["token_counts"]["analyst"] == 250


async def test_critic_node_parses_approval():
    """Critic node correctly parses JSON approval response."""
    from app.runtime.agents.critic import critic_node

    mock_response = _mock_llm_response(
        '{"approved": true, "score": 8, "critique": "Strong analysis with specific data.", "must_research": []}',
        150
    )

    with patch("app.runtime.agents.critic.get_worker_llm") as mock_llm_fn, \
         patch("app.runtime.agents.critic.publish_event", new_callable=AsyncMock):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        state = {
            "run_id": "test-run",
            "input": "Analyze fintech",
            "analysis": "## Executive Summary\nStrong findings here.",
            "iteration": 0,
            "token_counts": {},
        }
        result = await critic_node(state)

    assert result["critique_approved"] is True
    assert result["iteration"] == 1
    assert "Strong analysis" in result["critique"]


async def test_critic_node_rejection():
    """Critic node marks as rejected when score is below threshold."""
    from app.runtime.agents.critic import critic_node

    mock_response = _mock_llm_response(
        '{"approved": false, "score": 4, "critique": "Too vague, needs specific company names.", "must_research": ["key players"]}',
        120
    )

    with patch("app.runtime.agents.critic.get_worker_llm") as mock_llm_fn, \
         patch("app.runtime.agents.critic.publish_event", new_callable=AsyncMock):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        state = {"run_id": "test-run", "input": "Analyze", "analysis": "Short.", "iteration": 1, "token_counts": {}}
        result = await critic_node(state)

    assert result["critique_approved"] is False
    assert result["iteration"] == 2


# ── Evaluator unit tests ──────────────────────────────────────────────────────

async def test_evaluator_returns_valid_scores():
    """Evaluator parses JSON scores and calculates overall correctly."""
    from app.runtime.agents.evaluator import evaluate_report

    mock_response = _mock_llm_response(
        '{"specificity_score": 8, "completeness_score": 7, "accuracy_risk_score": 9, "usefulness_score": 8, "overall_score": 8.0, "feedback": "Solid report."}',
        100
    )

    with patch("app.runtime.agents.evaluator.get_worker_llm") as mock_llm_fn:
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        scores = await evaluate_report("Test request", "Test report content")

    assert scores["overall_score"] == pytest.approx(8.0, abs=0.1)
    assert scores["passed"] is True
    assert scores["specificity_score"] == 8
    assert "feedback" in scores


async def test_evaluator_fails_gracefully_on_bad_json():
    """Evaluator returns zero scores if LLM returns unparseable output."""
    from app.runtime.agents.evaluator import evaluate_report

    mock_response = _mock_llm_response("This is not JSON at all.", 50)

    with patch("app.runtime.agents.evaluator.get_worker_llm") as mock_llm_fn:
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_fn.return_value = mock_llm

        scores = await evaluate_report("Request", "Report")

    assert scores["overall_score"] == 0.0
    assert scores["passed"] is False
    assert "feedback" in scores
