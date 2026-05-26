"""
Evaluator Agent — LLM-as-Judge for output quality.

This is NOT part of the main pipeline graph.
It runs after the Reporter completes and scores the final report
on 4 dimensions. Scores are stored in the DB and shown in the UI.

Why LLM-as-judge?
- Human evaluation doesn't scale
- Rule-based checks miss nuance
- Using the same LLM family (Gemini) as judge is a known technique
  at AI labs — it correlates well with human judgment at scale
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.runtime.agents.base import get_worker_llm

SYSTEM_PROMPT = """You are an expert evaluator for competitive intelligence reports.

Score the following report on 4 dimensions, each from 1 to 10:

1. **Specificity** (1-10)
   - 10: Every claim has specific companies, numbers, dates
   - 5: Mix of specific and vague claims
   - 1: Entirely generic, no real data

2. **Completeness** (1-10)
   - 10: All sections are substantive and thorough
   - 5: Most sections present but some are thin
   - 1: Major sections missing or trivially short

3. **Accuracy Risk** (1-10)
   - 10: All claims are clearly grounded, uncertainty flagged appropriately
   - 5: Some unverified claims but flagged
   - 1: Many unverified or likely wrong claims presented as fact

4. **Usefulness** (1-10)
   - 10: A strategy professional could immediately act on this
   - 5: Useful context but lacks actionable direction
   - 1: Generic filler that adds no real value

Respond ONLY in this exact JSON format:
{
  "specificity_score": <1-10>,
  "completeness_score": <1-10>,
  "accuracy_risk_score": <1-10>,
  "usefulness_score": <1-10>,
  "overall_score": <average of the four>,
  "feedback": "2-3 sentences of specific, actionable feedback"
}"""


async def evaluate_report(request: str, report: str) -> dict:
    """
    Score a report using Gemini as judge.
    Returns a dict with all scores and feedback.
    """
    llm = get_worker_llm()

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Original request: {request}\n\nReport to evaluate:\n{report}"),
    ])

    raw = response.content.strip()

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        scores = json.loads(clean)
        # Recalculate overall as average to prevent hallucinated values
        dims = ["specificity_score", "completeness_score", "accuracy_risk_score", "usefulness_score"]
        scores["overall_score"] = round(sum(scores[d] for d in dims) / len(dims), 2)
        scores["passed"] = scores["overall_score"] >= 7.0
        return scores
    except (json.JSONDecodeError, KeyError):
        return {
            "specificity_score": 0.0,
            "completeness_score": 0.0,
            "accuracy_risk_score": 0.0,
            "usefulness_score": 0.0,
            "overall_score": 0.0,
            "feedback": f"Evaluator failed to parse scores. Raw: {raw[:200]}",
            "passed": False,
        }
