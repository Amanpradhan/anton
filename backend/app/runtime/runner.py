"""
WorkflowRunner — the bridge between the API layer and the LangGraph runtime.

Responsibilities:
- Accept a run_id (already created in DB by the API)
- Execute the compiled graph with the given input
- Persist all agent messages to the DB
- Update the Run record (status, output, token counts, cost)
- Trigger the EvaluatorAgent after completion
- Publish events to Redis throughout
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.eval_result import EvalResult
from app.models.message import Message
from app.models.run import Run, RunStatus
from app.runtime.agents.evaluator import evaluate_report
from app.runtime.events import publish_event
from app.runtime.graph import AgentState, compiled_graph

# Blended Gemini 2.5 Flash pricing (input $0.30/1M + output $2.50/1M, ~65/35 split ≈ $1.07/1M)
# Report-generating pipelines are output-heavy: analyst + reporter produce long completions
# Orchestrator uses 2.5 Pro ($1.25/$10 per 1M) but is a small fraction of total tokens
COST_PER_1K_TOKENS_USD = 0.00107


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
        # 5-minute hard timeout — prevents silent hangs on Gemini/Tavily API issues
        final_state = await asyncio.wait_for(
            compiled_graph.ainvoke(initial_state),
            timeout=300,
        )

        total_tokens = sum(final_state.get("token_counts", {}).values())
        estimated_cost = (total_tokens / 1000) * COST_PER_1K_TOKENS_USD
        report = final_state.get("report", "")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one()
            run.status = RunStatus.COMPLETED
            run.output = report
            run.total_tokens = total_tokens
            run.estimated_cost_usd = estimated_cost
            run.completed_at = datetime.now(timezone.utc)

            # Save per-agent summary messages so the Monitor tab works for completed runs
            tc = final_state.get("token_counts", {})
            queries = final_state.get("search_queries", [])
            research = final_state.get("research_data", [])
            critique = final_state.get("critique", "")
            iteration = final_state.get("iteration", 0)
            approved = final_state.get("critique_approved", False)

            agent_msgs = [
                Message(run_id=run_id, sender="orchestrator", recipient="pipeline",
                        content=f"Generated {len(queries)} search queries:\n" + "\n".join(f"• {q}" for q in queries),
                        message_type="task", tokens_used=tc.get("orchestrator", 0)),
                Message(run_id=run_id, sender="researcher", recipient="pipeline",
                        content=f"Completed {len(research)} searches and accumulated research data.",
                        message_type="task", tokens_used=tc.get("researcher", 0)),
                Message(run_id=run_id, sender="analyst", recipient="pipeline",
                        content="Synthesized research into a structured 6-section analysis.",
                        message_type="task", tokens_used=tc.get("analyst", 0)),
                Message(run_id=run_id, sender="critic", recipient="pipeline",
                        content=f"Quality review (iteration {iteration}): {'✓ Approved' if approved else '✗ Sent back for revision'}\n{critique[:400]}",
                        message_type="task", tokens_used=tc.get("critic", 0)),
                Message(run_id=run_id, sender="reporter", recipient="pipeline",
                        content="Generated final intelligence report and Telegram summary.",
                        message_type="final_output", tokens_used=tc.get("reporter", 0)),
            ]
            for m in agent_msgs:
                db.add(m)

            await db.commit()

        await publish_event(
            run_id, "system", "complete",
            f"Pipeline complete. Tokens: {total_tokens}, Cost: ${estimated_cost:.4f}",
            tokens_used=total_tokens,
        )

        # Run evaluation in the background (non-blocking — don't await)
        await _run_evaluation(run_id, user_input, report)

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


async def _run_evaluation(run_id: str, user_input: str, report: str) -> None:
    """Score the report using LLM-as-judge and persist the result."""
    try:
        await publish_event(run_id, "evaluator", "start", "Scoring report quality...")
        scores = await evaluate_report(user_input, report)

        async with AsyncSessionLocal() as db:
            db.add(EvalResult(
                run_id=run_id,
                specificity_score=scores["specificity_score"],
                completeness_score=scores["completeness_score"],
                accuracy_risk_score=scores["accuracy_risk_score"],
                usefulness_score=scores["usefulness_score"],
                overall_score=scores["overall_score"],
                feedback=scores["feedback"],
                passed=scores["passed"],
            ))
            await db.commit()

        status = "PASSED" if scores["passed"] else "FAILED"
        await publish_event(
            run_id, "evaluator", "complete",
            f"Eval {status} — Overall: {scores['overall_score']}/10",
        )
    except Exception as e:
        await publish_event(run_id, "evaluator", "error", f"Eval failed: {str(e)}")
