"""Evaluation Layer API routes.

Exposes expected/actual outcomes, decision evaluations, analyst feedback,
replay runs, and rule performance snapshots.

Read-heavy — write operations come from evaluation service and replay engine.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.evaluation.converters import (
    expected_outcome_from_orm,
    actual_outcome_from_orm,
    evaluation_from_orm,
    feedback_from_orm,
    replay_run_from_orm,
    replay_result_from_orm,
    performance_from_orm,
)
from src.data_foundation.evaluation.repositories import (
    ExpectedOutcomeRepo,
    ActualOutcomeRepo,
    DecisionEvaluationRepo,
    AnalystFeedbackRepo,
    ReplayRunRepo,
    ReplayRunResultRepo,
    RulePerformanceRepo,
)

router = APIRouter(
    prefix="/foundation/evaluation",
    tags=["Data Foundation — Evaluation"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Expected Outcomes
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/expected-outcomes", response_model=list[dict])
async def list_expected_outcomes(
    rule_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = ExpectedOutcomeRepo(session)
    if rule_id:
        rows = await repo.get_by_rule(rule_id, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [expected_outcome_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/expected-outcomes/{outcome_id}")
async def get_expected_outcome(outcome_id: str, session: AsyncSession = Depends(get_session)):
    repo = ExpectedOutcomeRepo(session)
    row = await repo.get_by_pk(outcome_id)
    if not row:
        raise HTTPException(404, f"Expected outcome '{outcome_id}' not found")
    return expected_outcome_from_orm(row).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Actual Outcomes
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/actual-outcomes", response_model=list[dict])
async def list_actual_outcomes(
    expected_outcome_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = ActualOutcomeRepo(session)
    if expected_outcome_id:
        rows = await repo.get_by_expected(expected_outcome_id)
    else:
        rows = await repo.list_all(limit=limit)
    return [actual_outcome_from_orm(r).model_dump(mode="json") for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Evaluations
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/evaluations", response_model=list[dict])
async def list_evaluations(
    rule_id: Optional[str] = Query(None),
    verdict: Optional[str] = Query(None, description="Filter by analyst_verdict"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = DecisionEvaluationRepo(session)
    if rule_id:
        rows = await repo.get_by_rule(rule_id, limit=limit)
    elif verdict:
        rows = await repo.get_by_verdict(verdict, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [evaluation_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str, session: AsyncSession = Depends(get_session)):
    repo = DecisionEvaluationRepo(session)
    row = await repo.get_by_pk(evaluation_id)
    if not row:
        raise HTTPException(404, f"Evaluation '{evaluation_id}' not found")
    return evaluation_from_orm(row).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Analyst Feedback
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/feedback", response_model=list[dict])
async def list_feedback(
    evaluation_id: Optional[str] = Query(None),
    analyst_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = AnalystFeedbackRepo(session)
    if evaluation_id:
        rows = await repo.get_by_evaluation(evaluation_id)
    elif analyst_id:
        rows = await repo.get_by_analyst(analyst_id, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [feedback_from_orm(r).model_dump(mode="json") for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Replay Runs
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/replays", response_model=list[dict])
async def list_replay_runs(
    status: Optional[str] = Query(None, description="Filter by status (COMPLETED, RUNNING, etc.)"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = ReplayRunRepo(session)
    if status:
        rows = await repo.get_by_status(status)
    else:
        rows = await repo.list_all(limit=limit)
    return [replay_run_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/replays/{replay_run_id}")
async def get_replay_run(replay_run_id: str, session: AsyncSession = Depends(get_session)):
    repo = ReplayRunRepo(session)
    row = await repo.get_by_pk(replay_run_id)
    if not row:
        raise HTTPException(404, f"Replay run '{replay_run_id}' not found")
    return replay_run_from_orm(row).model_dump(mode="json")


@router.get("/replays/{replay_run_id}/results", response_model=list[dict])
async def get_replay_results(
    replay_run_id: str,
    triggered_only: bool = Query(False),
    session: AsyncSession = Depends(get_session),
):
    repo = ReplayRunResultRepo(session)
    if triggered_only:
        rows = await repo.get_triggered_by_run(replay_run_id)
    else:
        rows = await repo.get_by_run(replay_run_id)
    return [replay_result_from_orm(r).model_dump(mode="json") for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Rule Performance Snapshots
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/rule-performance", response_model=list[dict])
async def list_rule_performance(
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = RulePerformanceRepo(session)
    rows = await repo.list_all(limit=limit)
    return [performance_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/rule-performance/{rule_id}")
async def get_rule_performance(rule_id: str, session: AsyncSession = Depends(get_session)):
    """Get latest performance snapshot for a rule."""
    repo = RulePerformanceRepo(session)
    row = await repo.get_latest_for_rule(rule_id)
    if not row:
        raise HTTPException(404, f"No performance snapshot for rule '{rule_id}'")
    return performance_from_orm(row).model_dump(mode="json")


@router.get("/rule-performance/{rule_id}/history", response_model=list[dict])
async def get_rule_performance_history(
    rule_id: str,
    limit: int = Query(12, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Get performance snapshot history for a rule (most recent first)."""
    repo = RulePerformanceRepo(session)
    rows = await repo.get_history(rule_id, limit=limit)
    return [performance_from_orm(r).model_dump(mode="json") for r in rows]
