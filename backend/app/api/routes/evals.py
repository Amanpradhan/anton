"""
Eval routes — batch evaluation against fixed test cases.

POST /api/evals/run      — run all test cases through the full pipeline and score each
GET  /api/evals/results  — list all eval results
GET  /api/evals/results/{run_id} — get eval for a specific run

The 5 test cases cover different domains and complexity levels,
giving a reliable signal on pipeline quality across scenarios.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.eval_result import EvalResult
from app.models.run import Run, RunStatus
from app.models.workflow import Workflow
from app.runtime.runner import run_workflow

router = APIRouter(prefix="/evals", tags=["evals"])

# ── Fixed test cases ──────────────────────────────────────────────────────────
# Diverse prompts that exercise different aspects of the pipeline:
# market sizing, competitor analysis, trend spotting, regulatory context, niche markets

EVAL_TEST_CASES = [
    {
        "id": "tc_latam_payments",
        "prompt": "Analyze the competitive landscape of payment processors in Latin America in 2024-2025",
        "description": "Core use case: LATAM fintech competitive analysis",
    },
    {
        "id": "tc_ai_agents_market",
        "prompt": "What is the current state of the AI agent platform market and who are the key players?",
        "description": "Trend analysis: emerging AI tooling market",
    },
    {
        "id": "tc_b2b_saas_latam",
        "prompt": "Identify the top B2B SaaS companies targeting SMBs in Latin America and their growth strategies",
        "description": "Niche market: B2B SaaS + specific region",
    },
    {
        "id": "tc_open_banking",
        "prompt": "What are the open banking regulations and opportunities in Brazil and Mexico?",
        "description": "Regulatory context: open banking in specific markets",
    },
    {
        "id": "tc_crypto_latam",
        "prompt": "How are cryptocurrency and stablecoin adoption trends evolving in Latin America?",
        "description": "Emerging trend: crypto adoption in LATAM",
    },
]


@router.post("/run")
async def run_batch_eval(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger all 5 test cases through the full Anton pipeline.
    Returns immediately with run IDs to track progress.
    Evaluation scores are stored in the DB as each run completes.
    """
    # Get or create the default workflow
    wf_result = await db.execute(
        select(Workflow).where(Workflow.is_active == True).limit(1)
    )
    workflow = wf_result.scalar_one_or_none()
    if not workflow:
        return {"error": "No active workflow found. Create one first."}

    run_ids = {}
    for tc in EVAL_TEST_CASES:
        run = Run(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            status=RunStatus.PENDING,
            input=tc["prompt"],
            trigger_source="eval",
            created_at=datetime.now(timezone.utc),
        )
        db.add(run)
        await db.flush()
        run_ids[tc["id"]] = run.id

        background_tasks.add_task(
            run_workflow,
            run_id=run.id,
            workflow_id=workflow.id,
            user_input=tc["prompt"],
            trigger_source="eval",
        )

    await db.commit()
    return {
        "message": f"Started {len(EVAL_TEST_CASES)} eval runs",
        "run_ids": run_ids,
        "note": "Use GET /api/evals/results to see scores as they complete",
    }


@router.get("/results")
async def list_eval_results(db: AsyncSession = Depends(get_db)):
    """All eval results ordered by most recent, with aggregate stats."""
    result = await db.execute(
        select(EvalResult).order_by(EvalResult.created_at.desc())
    )
    results = result.scalars().all()

    if not results:
        return {"results": [], "aggregate": None}

    avg_overall = sum(r.overall_score for r in results) / len(results)
    pass_rate = sum(1 for r in results if r.passed) / len(results) * 100

    return {
        "results": [
            {
                "run_id": r.run_id,
                "overall_score": r.overall_score,
                "specificity_score": r.specificity_score,
                "completeness_score": r.completeness_score,
                "accuracy_risk_score": r.accuracy_risk_score,
                "usefulness_score": r.usefulness_score,
                "passed": r.passed,
                "feedback": r.feedback,
                "created_at": r.created_at,
            }
            for r in results
        ],
        "aggregate": {
            "total_runs": len(results),
            "avg_overall_score": round(avg_overall, 2),
            "pass_rate_pct": round(pass_rate, 1),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
        },
    }


@router.get("/results/{run_id}")
async def get_eval_result(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EvalResult).where(EvalResult.run_id == run_id)
    )
    eval_result = result.scalar_one_or_none()
    if not eval_result:
        return {"message": "Eval not yet complete or run not found"}
    return eval_result
