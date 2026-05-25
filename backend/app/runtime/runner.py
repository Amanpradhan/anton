"""
WorkflowRunner — the bridge between the API layer and the LangGraph runtime.

Responsibilities:
- Accept a run_id (already created in DB by the API)
- Execute the compiled graph with the given input
- Persist all agent messages to the DB
- Update the Run record (status, output, token counts, cost)
- Publish events to Redis throughout
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.message import Message
from app.models.run import Run, RunStatus
from app.runtime.events import publish_event
from app.runtime.graph import AgentState, compiled_graph

# Gemini 2.0 Flash pricing (per 1K tokens, approximate)
COST_PER_1K_TOKENS_USD = 0.000075


async def run_workflow(
    run_id: str,
    workflow_id: str,
    user_input: str,
    trigger_source: str = "api",
    trigger_id: str | None = None,
) -> str:
    """
    Execute the Anton multi-agent pipeline for a given input.
    Returns the final_output (short summary for the user).
    """
    async with AsyncSessionLocal() as db:
        # Mark run as started
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.status = RunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        await db.commit()

    await publish_event(run_id, "system", "start", f"Pipeline started for: {user_input}")

    initial_state: AgentState = {
        "run_id": run_id,
        "input": user_input,
        "search_queries": [],
        "research_data": [],
        "analysis": "",
        "critique": "",
        "critique_approved": False,
        "iteration": 0,
        "report": "",
        "final_output": "",
        "messages": [],
        "token_counts": {},
    }

    try:
        final_state = await compiled_graph.ainvoke(initial_state)

        total_tokens = sum(final_state.get("token_counts", {}).values())
        estimated_cost = (total_tokens / 1000) * COST_PER_1K_TOKENS_USD

        async with AsyncSessionLocal() as db:
            # Update run record
            result = await db.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one()
            run.status = RunStatus.COMPLETED
            run.output = final_state.get("report", "")
            run.total_tokens = total_tokens
            run.estimated_cost_usd = estimated_cost
            run.completed_at = datetime.now(timezone.utc)

            # Persist agent messages
            for msg in final_state.get("messages", []):
                role = getattr(msg, "type", "unknown")
                db.add(Message(
                    run_id=run_id,
                    sender=role,
                    recipient="user" if role == "ai" else "pipeline",
                    content=msg.content,
                    message_type="final_output" if role == "ai" else "user_input",
                ))

            await db.commit()

        await publish_event(
            run_id, "system", "complete",
            f"Pipeline complete. Tokens: {total_tokens}, Cost: ${estimated_cost:.4f}",
            tokens_used=total_tokens,
        )

        return final_state.get("final_output", "Analysis complete.")

    except Exception as e:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = RunStatus.FAILED
                run.error = str(e)
                run.completed_at = datetime.now(timezone.utc)
                await db.commit()

        await publish_event(run_id, "system", "error", f"Pipeline failed: {str(e)}")
        raise
