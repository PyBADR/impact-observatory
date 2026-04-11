"""Evaluation routes.

POST /evaluations/run    — run deterministic evaluation
GET  /evaluations/{id}   — retrieve evaluation result
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from src.data_foundation.schemas.outcome_schemas import (
    DecisionEvaluation,
    RunEvaluationRequest,
)
from src.data_foundation.services.decision_evaluation_service import (
    compute_correctness,
    compute_confidence_gap,
    compute_direction_alignment,
    compute_entity_alignment,
    compute_explainability_completeness,
    compute_severity_alignment,
    compute_timing_alignment,
)
from src.data_foundation.api.outcomes import _expected_store, _actual_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluations", tags=["evaluations"])

_evaluation_store: dict[str, dict] = {}


@router.post("/run", status_code=201, response_model=DecisionEvaluation)
async def run_evaluation(body: RunEvaluationRequest):
    """Run deterministic evaluation comparing expected vs actual outcome."""
    from uuid import uuid4
    from datetime import datetime, timezone

    expected = _expected_store.get(body.expected_outcome_id)
    if expected is None:
        raise HTTPException(status_code=404, detail=f"Expected outcome not found: {body.expected_outcome_id}")

    actual = _actual_store.get(body.actual_outcome_id)
    if actual is None:
        raise HTTPException(status_code=404, detail=f"Actual outcome not found: {body.actual_outcome_id}")

    severity_score = compute_severity_alignment(
        expected["expected_severity"],
        actual["observed_severity"],
    )
    entity_score = compute_entity_alignment(
        expected.get("expected_entities", []),
        actual.get("observed_entities", []),
    )
    timing_score = compute_timing_alignment(
        expected.get("expected_time_horizon_hours"),
        actual.get("observed_time_to_materialization_hours"),
    )
    direction_score = compute_direction_alignment(
        expected["expected_direction"],
        actual["observed_direction"],
    )
    correctness = compute_correctness(severity_score, entity_score, timing_score, direction_score)
    gap = compute_confidence_gap(expected.get("confidence_at_decision_time", 0.5), correctness)
    explainability = compute_explainability_completeness(None)

    eval_id = f"EVAL-{str(uuid4())[:12]}"
    now = datetime.now(timezone.utc)

    result = {
        "evaluation_id": eval_id,
        "decision_log_id": body.decision_log_id,
        "expected_outcome_id": body.expected_outcome_id,
        "actual_outcome_id": body.actual_outcome_id,
        "correctness_score": round(correctness, 4),
        "severity_alignment_score": round(severity_score, 4),
        "entity_alignment_score": round(entity_score, 4),
        "timing_alignment_score": round(timing_score, 4),
        "confidence_gap": round(gap, 4),
        "explainability_completeness_score": round(explainability, 4),
        "evaluation_status": "COMPLETED",
        "evaluated_at": now,
    }
    _evaluation_store[eval_id] = result
    logger.info("Evaluation completed: %s, correctness=%.4f", eval_id, correctness)
    return DecisionEvaluation(**result)


@router.get("/{evaluation_id}", response_model=DecisionEvaluation)
async def get_evaluation(evaluation_id: str):
    """Retrieve a previously computed evaluation."""
    result = _evaluation_store.get(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Evaluation not found: {evaluation_id}")
    return DecisionEvaluation(**result)
