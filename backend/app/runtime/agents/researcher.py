"""
Researcher Agent — executes web searches and collects raw data.

Responsibilities:
- Run each search query against Tavily
- Collect and structure the results
- On subsequent iterations, incorporate critique feedback into follow-up queries
"""

import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from app.runtime.agents.base import get_worker_llm
from app.runtime.events import publish_event
from app.runtime.tools.web_search import web_search

FOLLOWUP_PROMPT = """You are a research specialist. The analyst's work was reviewed and found lacking in some areas.

Original research request: {input}
Critic's feedback: {critique}
Previous search queries used: {previous_queries}

Generate 3 NEW, targeted follow-up search queries that specifically address the gaps identified by the critic.
These must be different from the previous queries.
Return ONLY the queries as a numbered list."""


async def _run_single_search(query: str) -> dict:
    """Run one Tavily search and return structured result."""
    try:
        results = await web_search.ainvoke(query)
        # results is a list of dicts: [{"url": ..., "content": ..., "title": ...}]
        snippets = [r.get("content", "") for r in results if r.get("content")]
        return {"query": query, "results": snippets}
    except Exception as e:
        return {"query": query, "results": [f"Search failed: {str(e)}"]}


async def researcher_node(state: dict) -> dict:
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)

    # On follow-up iterations, generate new queries based on critique
    if iteration > 0 and state.get("critique"):
        await publish_event(run_id, "researcher", "start", f"Iteration {iteration + 1}: Running follow-up research based on critique")
        queries = await _generate_followup_queries(state)
    else:
        queries = state["search_queries"]
        await publish_event(run_id, "researcher", "start", f"Running {len(queries)} searches")

    # Run all searches concurrently
    tasks = [_run_single_search(q) for q in queries]
    new_results = await asyncio.gather(*tasks)

    for r in new_results:
        await publish_event(run_id, "researcher", "tool_call", f"Searched: {r['query']} → {len(r['results'])} results")

    # Accumulate results across iterations (don't overwrite previous research)
    existing = state.get("research_data", [])
    combined = existing + list(new_results)

    await publish_event(run_id, "researcher", "complete", f"Collected {len(combined)} total research items")

    return {
        "research_data": combined,
        "search_queries": queries,
    }


async def _generate_followup_queries(state: dict) -> list[str]:
    llm = get_worker_llm()
    prompt = FOLLOWUP_PROMPT.format(
        input=state["input"],
        critique=state["critique"],
        previous_queries="\n".join(state.get("search_queries", [])),
    )
    response = await llm.ainvoke([
        SystemMessage(content="You are a research specialist generating targeted follow-up search queries."),
        HumanMessage(content=prompt),
    ])
    raw = response.content.strip()
    queries = []
    for line in raw.split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            query = line.split(".", 1)[-1].split(")", 1)[-1].strip()
            if query:
                queries.append(query)
    return queries[:3] if queries else [state["input"]]
