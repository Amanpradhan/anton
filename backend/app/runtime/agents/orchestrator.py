"""
Orchestrator Agent — the entry point of every workflow run.

Responsibilities:
- Understand the user's request
- Decompose it into 4-6 targeted search queries for the researcher
- Set the stage for the rest of the pipeline
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.runtime.agents.base import get_orchestrator_llm
from app.runtime.events import publish_event

SYSTEM_PROMPT = """You are the Orchestrator of Anton, an autonomous competitive intelligence platform.

Your job is to receive a research request and decompose it into precise, targeted web search queries
that will help a team of specialist agents build a comprehensive intelligence report.

Rules:
- Generate exactly 5 search queries
- Each query must target a different angle (market size, key players, recent news, trends, challenges)
- Queries must be specific enough to return useful results, not generic
- Return ONLY the queries as a numbered list, nothing else

Example output:
1. fintech payment processors LATAM market size 2024 2025
2. top payment companies Latin America Mercado Pago competitors
3. payment infrastructure regulation LATAM 2024 compliance
4. LATAM fintech funding rounds payment startups 2024
5. cross-border payments challenges Latin America merchants"""


async def orchestrator_node(state: dict) -> dict:
    run_id = state["run_id"]
    user_input = state["input"]

    await publish_event(run_id, "orchestrator", "start", f"Analyzing request: {user_input}")

    llm = get_orchestrator_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Research request: {user_input}"),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    # Parse numbered list into clean query strings
    queries = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            # Strip leading "1. " or "1) "
            query = line.split(".", 1)[-1].split(")", 1)[-1].strip()
            if query:
                queries.append(query)

    # Fallback: if parsing fails, use raw lines
    if not queries:
        queries = [line.strip() for line in raw.split("\n") if line.strip()][:5]

    tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

    await publish_event(
        run_id, "orchestrator", "complete",
        f"Generated {len(queries)} search queries",
        tokens_used=tokens,
    )

    return {
        "search_queries": queries,
        "messages": [HumanMessage(content=user_input)],
        "token_counts": {**state.get("token_counts", {}), "orchestrator": tokens},
        "iteration": 0,
    }
