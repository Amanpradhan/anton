"""
Reporter Agent — final stage, produces the polished deliverable.

Responsibilities:
- Transform the analyst's work into a professional report
- Generate a short executive summary for the user (sent via Telegram)
- The full report is stored in the DB; the summary goes to the messaging channel
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.runtime.agents.base import get_worker_llm
from app.runtime.events import publish_event

REPORT_PROMPT = """You are a senior intelligence report writer.

Transform the analyst's findings into a polished, professional intelligence report.

Format the report in clean Markdown with:
- A title
- Date (today)
- Executive Summary (3-4 sentences)
- Full sections with headers
- Key Takeaways (3 bullet points at the end)
- Confidence level: High / Medium / Low with explanation

Make it look like something a strategy consultant would be proud to send to a client."""

SUMMARY_PROMPT = """Based on this intelligence report, write a SHORT Telegram message summary.

Rules:
- Maximum 5 sentences
- Start with the single most important finding
- Include 2-3 key data points
- End with "Full report available on Anton dashboard."
- Use simple language, no jargon
- No markdown, just plain text"""


async def reporter_node(state: dict) -> dict:
    run_id = state["run_id"]

    await publish_event(run_id, "reporter", "start", "Generating final report")

    llm = get_worker_llm()

    # Generate full report
    report_response = await llm.ainvoke([
        SystemMessage(content=REPORT_PROMPT),
        HumanMessage(content=f"Request: {state['input']}\n\nAnalysis:\n{state['analysis']}"),
    ])
    report = report_response.content.strip()
    report_tokens = report_response.usage_metadata.get("total_tokens", 0) if report_response.usage_metadata else 0

    await publish_event(run_id, "reporter", "message", "Full report generated, creating summary")

    # Generate short summary for messaging channel
    summary_response = await llm.ainvoke([
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=report),
    ])
    summary = summary_response.content.strip()
    summary_tokens = summary_response.usage_metadata.get("total_tokens", 0) if summary_response.usage_metadata else 0

    total_tokens = report_tokens + summary_tokens
    await publish_event(run_id, "reporter", "complete", "Report and summary ready", tokens_used=total_tokens)

    return {
        "report": report,
        "final_output": summary,
        "messages": [AIMessage(content=summary)],
        "token_counts": {**state.get("token_counts", {}), "reporter": total_tokens},
    }
