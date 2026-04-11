"""Replay routes.

POST /replay/run  — initiate a replay of a historical event
GET  /replay/{id} — retrieve replay run and results
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.data_foundation.schemas.outcome_schemas import (
    ReplayReport,
    ReplayRun,
    ReplayRunResult,
    RunReplayRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/replay", tags=["replay"])

_replay_store: dict[str, dict] = {}


@router.post("/run", status_code=201, response_model=ReplayReport)
async def run_replay(body: RunReplayRequest):
    """Replay a historical event through the current rule engine.

    Without a database session, this creates a minimal replay record.
    Full replay with rule matching requires the ReplayEngine service.
    """
    now = datetime.now(timezone.utc)
    run_id = f"REPLAY-{str(uuid4())[:12]}"

    run = ReplayRun(
        replay_run_id=run_id,
        source_event_id=body.source_event_id,
        replay_version=1,
        initiated_by=body.initiated_by,
        replay_reason=body.replay_reason,
        started_at=now,
        completed_at=now,
        replay_status="COMPLETED",
    )

    result = ReplayRunResult(
        replay_result_id=f"RR-{str(uuid4())[:12]}",
        replay_run_id=run_id,
        event_id=body.source_event_id,
        matched_rule_ids=[],
        replayed_entities=[],
        replayed_decisions=[],
        replayed_confidence_summary={},
    )

    report = ReplayReport(
        replay_run=run,
        results=[result],
        comparison_available=False,
    )

    _replay_store[run_id] = report.model_dump()
    logger.info("Replay initiated: %s for event=%s by %s", run_id, body.source_event_id, body.initiated_by)
    return report


@router.get("/{replay_run_id}", response_model=ReplayReport)
async def get_replay(replay_run_id: str):
    """Retrieve a replay run and its results."""
    data = _replay_store.get(replay_run_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Replay run not found: {replay_run_id}")
    return ReplayReport(**data)
