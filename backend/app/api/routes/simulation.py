"""
Impact Observatory | مرصد الأثر — Phase 1 Simulation API Route
POST /api/v1/simulation/run-hormuz

Single route that orchestrates the full Hormuz simulation pipeline:
  1. Validate request (Pydantic gate)
  2. Run propagation engine (edge-based stress transmission)
  3. Generate decisions (rule-based, deterministic)
  4. Generate explanations (template-based, no LLM)
  5. Compute SHA-256 audit digest
  6. Return typed HormuzRunResult

No external service dependencies. Runs fully in-process.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.domain.simulation.decision_engine import generate_decisions
from app.domain.simulation.explain import generate_explanations
from app.domain.simulation.propagation_engine import propagate
from app.domain.simulation.schemas import (
    HormuzRunRequest,
    HormuzRunResult,
)

logger = logging.getLogger("observatory.simulation")

router = APIRouter(
    prefix="/simulation",
    tags=["simulation-phase1"],
)


@router.post(
    "/run-hormuz",
    response_model=HormuzRunResult,
    summary="Run Hormuz disruption simulation — Phase 1 production core",
    description=(
        "Executes the full GCC macro-financial stress propagation pipeline for a "
        "Strait of Hormuz disruption scenario. Returns country impacts, sector stress, "
        "decision recommendations, and causal explanations. "
        "All computation is deterministic — same inputs always produce same outputs."
    ),
)
async def run_hormuz(request: HormuzRunRequest) -> HormuzRunResult:
    """Execute the Hormuz simulation and return structured results."""
    logger.info(
        "Hormuz simulation requested: severity=%.2f, horizon=%dh, transit_reduction=%.2f",
        request.severity,
        request.horizon_hours,
        request.transit_reduction_pct,
    )

    try:
        # ── Step 1: Propagation ──────────────────────────────────────────
        prop_result = propagate(
            severity=request.severity,
            transit_reduction_pct=request.transit_reduction_pct,
            horizon_hours=request.horizon_hours,
        )

        # ── Step 2: Decision generation ──────────────────────────────────
        decisions = generate_decisions(prop_result)

        # ── Step 3: Explainability ───────────────────────────────────────
        explanations = generate_explanations(prop_result)

        # ── Step 4: Assemble result ──────────────────────────────────────
        result = HormuzRunResult(
            scenario_id="hormuz_chokepoint_disruption",
            model_version="3.0.0-phase1",
            timestamp=datetime.utcnow(),
            severity=request.severity,
            horizon_hours=request.horizon_hours,
            transit_reduction_pct=request.transit_reduction_pct,
            total_loss_usd=round(prop_result.total_loss_usd, 2),
            risk_level=prop_result.country_impacts[0].risk_level if prop_result.country_impacts else "NOMINAL",
            confidence=prop_result.confidence,
            countries=prop_result.country_impacts,
            sectors=prop_result.sector_impacts,
            propagation_edges=prop_result.propagation_edges,
            decisions=decisions,
            explainability=explanations,
        )

        # ── Step 5: SHA-256 audit digest ─────────────────────────────────
        payload_json = result.model_dump_json(exclude={"sha256_digest"})
        result.sha256_digest = hashlib.sha256(payload_json.encode()).hexdigest()

        logger.info(
            "Hormuz simulation complete: total_loss=%s, risk=%s, decisions=%d, sha256=%s",
            f"${prop_result.total_loss_usd:,.0f}",
            result.risk_level,
            len(decisions),
            result.sha256_digest[:16],
        )

        return result

    except Exception as e:
        logger.exception("Hormuz simulation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Simulation engine error: {str(e)}",
        )
