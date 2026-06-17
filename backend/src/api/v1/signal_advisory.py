"""
Impact Observatory | مرصد الأثر
Signal Advisory Endpoint — v5 advisory-only signal context.

GET /internal/signal-advisory/evaluate

Returns advisory interpretations for sample signals against a scenario.
Gated by ENABLE_SIGNAL_ADVISORY_V5 feature flag.

When flag is false (default, production):
  -> Returns 404 with explanation.

When flag is true (dev/advisory):
  -> Returns advisory interpretations from sample signals.
  -> ZERO scoring impact.
  -> metric_after == metric_before (always).
  -> scoring_applied == False (always).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from src.signal_ingestion.feature_flags import is_signal_advisory_v5_enabled
from src.signal_ingestion.ingestion_service import (
    ingest_signals,
    SAMPLE_RAW_SIGNALS,
)
from src.signal_ingestion.advisory_service import evaluate_advisories
from src.signal_ingestion.audit_log import SignalAuditLog


router = APIRouter(prefix="/internal/signal-advisory", tags=["internal"])


@router.get("/evaluate")
async def signal_advisory_evaluate(
    scenario_id: str = Query(
        default="hormuz_chokepoint_disruption",
        description="Scenario to evaluate advisory signals against.",
    ),
):
    """Evaluate sample signals and return advisory interpretations.

    Returns 404 when ENABLE_SIGNAL_ADVISORY_V5 is not true.
    Returns advisory interpretations when enabled.
    metric_after == metric_before. scoring_applied == False.
    """
    if not is_signal_advisory_v5_enabled():
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Signal advisory v5 is not enabled.",
                "hint": "Set ENABLE_SIGNAL_ADVISORY_V5=true in your environment.",
                "production_safe": True,
            },
        )

    audit_log = SignalAuditLog()

    # Ingest sample signals (static fixture data)
    snapshots = ingest_signals(
        raw_inputs=SAMPLE_RAW_SIGNALS,
        source_id="sig_sample_static",
        audit_log=audit_log,
    )

    # Generate advisory interpretations (read-only, no scoring)
    advisories = evaluate_advisories(
        snapshots,
        scenario_id,
        audit_log=audit_log,
    )

    return JSONResponse(content={
        "enabled": True,
        "scenario_id": scenario_id,
        "advisory_count": len(advisories),
        "advisories": [a.to_dict() for a in advisories],
        "audit_summary": audit_log.summary(),
        "scoring_impact": "none",
        "notice": "Advisory only — metrics unchanged. "
                  "Scoring not applied. "
                  "Signal explains context, not outcome.",
    })
