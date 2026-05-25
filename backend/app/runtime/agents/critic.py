"""
Critic Agent — quality gate that enforces rigorous standards.

Responsibilities:
- Review the analyst's work critically
- Flag vague claims, missing data, unverified numbers
- Decide: approve (move to reporter) or reject (send back to researcher)

This is what makes the pipeline genuinely multi-agent and not just a single LLM call.
The feedback loop between Critic → Researcher creates iterative quality improvement.
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.runtime.agents.base import get_worker_llm
from app.runtime.events import publish_event

SYSTEM_PROMPT = """You are a rigorous fact-checker and critical reviewer at an intelligence firm.

Your job is to review an analyst's report and decide if it meets publication standards.

Evaluate on:
1. **Specificity** — Are claims backed by specific data, companies, or dates? Or is it vague?
2. **Completeness** — Are all 6 required sections present and substantive?
3. **Accuracy risk** — Are there claims that seem unverified or speculative?
4. **Data gaps** — Did the analyst flag real gaps, or did they paper over missing information?

Respond in this exact JSON format:
{
  "approved": true or false,
  "score": 1-10,
  "critique": "Your detailed feedback here. Be specific about what's missing or wrong.",
  "must_research": ["specific topic 1", "specific topic 2"]
}

Approve (true) if score >= 7. Reject (false) if score < 7.
Be honest — a rejected analysis that gets improved is better than a weak approved one."""


async def critic_node(state: dict) -> dict:
    run_id = state["run_id"]
    iteration = state.get("iteration", 0)

    await publish_event(run_id, "critic", "start", f"Reviewing analysis (iteration {iteration + 1})")

    llm = get_worker_llm()
    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Original request: {state['input']}\n\nAnalysis to review:\n{state['analysis']}"),
    ])

    raw = response.content.strip()
    tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

    # Parse JSON response
    try:
        # Strip markdown code fences if present
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        approved = result.get("approved", False)
        critique = result.get("critique", raw)
        score = result.get("score", 0)
    except json.JSONDecodeError:
        # If JSON parsing fails, default to rejected with raw content as critique
        approved = False
        critique = raw
        score = 0

    status = "APPROVED" if approved else f"REJECTED (score: {score}/10)"
    await publish_event(run_id, "critic", "complete", f"{status} — {critique[:200]}", tokens_used=tokens)

    return {
        "critique": critique,
        "critique_approved": approved,
        "iteration": iteration + 1,
        "token_counts": {**state.get("token_counts", {}), "critic": tokens},
    }
