"""
LangGraph state definition and graph builder.

The competitive intelligence pipeline runs in this order:

  START → orchestrator → researcher → analyst → critic
                                          ↑          ↓ (if issues found)
                                          └──────────┘
                                               ↓ (if approved OR max iterations)
                                           reporter → END

Key design: the critic creates a feedback loop. If it finds gaps,
the researcher runs again with targeted follow-up queries.
Max 3 iterations prevents infinite loops.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from app.runtime.agents.analyst import analyst_node
from app.runtime.agents.critic import critic_node
from app.runtime.agents.orchestrator import orchestrator_node
from app.runtime.agents.reporter import reporter_node
from app.runtime.agents.researcher import researcher_node

MAX_ITERATIONS = 3


class AgentState(TypedDict):
    # ── Core input ────────────────────────────────────────────────────────────
    run_id: str
    input: str

    # ── Research phase ────────────────────────────────────────────────────────
    search_queries: list[str]
    research_data: list[dict]  # [{"query": str, "results": list[str]}]

    # ── Analysis & critique loop ──────────────────────────────────────────────
    analysis: str
    critique: str
    critique_approved: bool
    iteration: int  # how many research→analyst→critic cycles have run

    # ── Output ────────────────────────────────────────────────────────────────
    report: str
    final_output: str  # short summary returned to user (e.g. via Telegram)

    # ── Conversation history (add_messages reducer appends, never overwrites) ─
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Cost tracking ─────────────────────────────────────────────────────────
    token_counts: dict[str, int]  # {"researcher": 412, "analyst": 890, ...}


def route_after_critic(state: AgentState) -> str:
    """
    Conditional edge: decides what happens after the critic reviews.

    - If critique is approved OR we've hit the max iterations → reporter
    - Otherwise → researcher (with the critique as feedback for better searches)
    """
    if state.get("critique_approved") or state.get("iteration", 0) >= MAX_ITERATIONS:
        return "reporter"
    return "researcher"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("critic", critic_node)
    graph.add_node("reporter", reporter_node)

    # Linear edges
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "critic")
    graph.add_edge("reporter", END)

    # Conditional edge: critic decides next step
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "researcher": "researcher",
            "reporter": "reporter",
        },
    )

    return graph.compile()


# Singleton — compiled once at import, reused for every run
compiled_graph = build_graph()
