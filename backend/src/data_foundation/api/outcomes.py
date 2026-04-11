"""Outcome tracking routes.

POST /outcomes/expected  — record an expected outcome
POST /outcomes/actual    — record an actual observed outcome
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from src.data_foundation.schemas.outcome_schemas import (
    CreateActualOutcomeRequest,
    CreateExpectedOutcomeRequest,
    DecisionActualOutcome,
    DecisionExpectedOutcome,
)
from src.data_foundation.services.outcome_tracking_service import OutcomeTrackingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outcomes", tags=["outcomes"])


# In-memory fallback for when no database session is available.
# Production would inject AsyncSession via dependency.
_expected_store: dict[str, dict] = {}
_actual_store: dict[str, dict] = {}


@router.post("/expected", status_code=201, response_model=DecisionExpectedOutcome)
async def create_expected_outcome(body: CreateExpectedOutcomeRequest):
    """Record an expected outcome from a decision rule trigger."""
    from uuid import uuid4
    outcome_id = f"EO-{str(uuid4())[:12]}"
    record = body.model_dump()
    record["expected_outcome_id"] = outcome_id
    _expected_store[outcome_id] = record
    logger.info("Expected outcome created: %s for decision_log=%s", outcome_id, body.decision_log_id)
    return DecisionExpectedOutcome(**record)


@router.post("/actual", status_code=201, response_model=DecisionActualOutcome)
async def create_actual_outcome(body: CreateActualOutcomeRequest):
    """Record an actual observed outcome."""
    from uuid import uuid4
    outcome_id = f"AO-{str(uuid4())[:12]}"
    record = body.model_dump()
    record["actual_outcome_id"] = outcome_id
    _actual_store[outcome_id] = record
    logger.info(
        "Actual outcome created: %s for expected=%s",
        outcome_id, body.expected_outcome_id,
    )
    return DecisionActualOutcome(**record)
