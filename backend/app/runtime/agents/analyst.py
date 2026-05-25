"""
Analyst Agent — synthesizes raw research into structured intelligence.

Responsibilities:
- Read all collected research data
- Identify patterns, trends, key players, gaps
- Produce a structured analysis with clear sections
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.runtime.agents.base import get_worker_llm
from app.runtime.events import publish_event

SYSTEM_PROMPT = """You are a senior market intelligence analyst at a top strategy firm.

You receive raw web research data and synthesize it into a structured, insightful analysis.

Your analysis must always include these sections:
1. **Executive Summary** (2-3 sentences, the most important finding)
2. **Key Players** (main companies/actors and their positioning)
3. **Market Dynamics** (size, growth, trends)
4. **Opportunities** (underserved areas, emerging niches)
5. **Risks & Challenges** (regulatory, competitive, structural)
6. **Data Gaps** (what's unclear or missing from the research)

Be specific. Cite specific companies, numbers, and dates when available.
Flag anything that seems uncertain or that needs verification."""


async def analyst_node(state: dict) -> dict:
    run_id = state["run_id"]
    research_data = state.get("research_data", [])

    await publish_event(run_id, "analyst", "start", f"Analyzing {len(research_data)} research items")

    # Flatten all research into a readable block
    research_text = ""
    for item in research_data:
        research_text += f"\n\n## Search: {item['query']}\n"
        for i, result in enumerate(item["results"], 1):
            research_text += f"{i}. {result[:500]}\n"  # Cap per result to avoid token explosion

    llm = get_worker_llm()
    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Original request: {state['input']}\n\nResearch data:\n{research_text}"),
    ])

    analysis = response.content.strip()
    tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

    await publish_event(run_id, "analyst", "complete", "Analysis complete", tokens_used=tokens)

    return {
        "analysis": analysis,
        "token_counts": {**state.get("token_counts", {}), "analyst": tokens},
    }
