"""Analyst Feedback routes.

POST /feedback  — submit analyst verdict on a decision
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.data_foundation.schemas.outcome_schemas import (
    AnalystFeedbackRecord,
    CreateFeedbackRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])

_feedback_store: dict[str, dict] = {}


@router.post("", status_code=201, response_model=AnalystFeedbackRecord)
async def create_feedback(body: CreateFeedbackRequest):
    """Submit analyst feedback on a decision/evaluation."""
    from uuid import uuid4
    feedback_id = f"FB-{str(uuid4())[:12]}"
    record = body.model_dump()
    record["feedback_id"] = feedback_id
    _feedback_store[feedback_id] = record
    logger.info(
        "Analyst feedback recorded: %s by %s, verdict=%s",
        feedback_id, body.analyst_name, body.verdict,
    )
    return AnalystFeedbackRecord(**record)
