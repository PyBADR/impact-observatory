"""
Impact Observatory | مرصد الأثر — Phase 2 Scenarios API Route

GET  /api/v1/scenarios/list       → List all registered scenarios
POST /api/v1/scenarios/run/{slug} → Run any registered scenario

The {slug} path parameter selects the scenario from the registry.
Same response contract as Phase 1 HormuzRunResult — extended with
pathway_headlines in the explainability layer.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.domain.simulation.decision_engine import generate_decisions
from app.domain.simulation.explain import generate_explanations
from app.domain.simulation.runner import SimulationRunner, build_run_result
from app.domain.simulation.scenario_registry import get_scenario, list_scenarios
from app.domain.simulation.schemas import HormuzRunResult

logger = logging.getLogger("observatory.scenarios")

router = APIRouter(
    prefix="/scenarios",
    tags=["scenarios-phase2"],
)

_runner = SimulationRunner()


# ═══════════════════════════════════════════════════════════════════════════════
# Request Schema
# ═══════════════════════════════════════════════════════════════════════════════

class ScenarioRunRequest(BaseModel):
    """Generic input for any scenario run."""
    severity: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Override default severity (0.0–1.0). None uses scenario default.",
    )
    horizon_hours: Optional[int] = Field(
        default=None,
        ge=1, le=8760,
        description="Override default horizon. None uses scenario default.",
    )
    extra_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Scenario-specific parameters (e.g. transit_reduction_pct, interbank_freeze_pct)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Extended Response (adds pathway_headlines to the base HormuzRunResult)
# ═══════════════════════════════════════════════════════════════════════════════

class ScenarioRunResult(HormuzRunResult):
    """Extends base result with Phase 2 pathway headlines."""
    pathway_headlines: list[str] = Field(
        default_factory=list,
        description="Executive-readable transmission pathway headlines",
    )
    scenario_name: str = ""
    scenario_type: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/list",
    summary="List all registered simulation scenarios",
    description="Returns metadata for every scenario in the registry.",
)
async def list_all_scenarios():
    return {"scenarios": list_scenarios()}


@router.post(
    "/run/{slug}",
    response_model=ScenarioRunResult,
    summary="Run a scenario simulation by slug",
    description=(
        "Execute the full GCC macro-financial stress propagation pipeline "
        "for the specified scenario. Supports: hormuz, liquidity_stress."
    ),
)
async def run_scenario(slug: str, request: ScenarioRunRequest) -> ScenarioRunResult:
    """Execute a scenario by slug and return structured results."""

    # ── Validate slug ────────────────────────────────────────────────────
    try:
        spec = get_scenario(slug)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    sev = request.severity if request.severity is not None else spec.default_severity
    hrs = request.horizon_hours if request.horizon_hours is not None else spec.default_horizon_hours

    logger.info("Scenario run: slug=%s, severity=%.2f, horizon=%dh", slug, sev, hrs)

    try:
        # ── Run propagation ──────────────────────────────────────────────
        prop = _runner.run(slug, severity=sev, horizon_hours=hrs, **request.extra_params)

        # ── Decisions ────────────────────────────────────────────────────
        decisions = generate_decisions(prop)

        # ── Explainability (Phase 1 module — scenario-aware via prop) ────
        explanations = generate_explanations(prop)

        # ── Build base result ────────────────────────────────────────────
        base = build_run_result(
            prop=prop,
            severity=sev,
            horizon_hours=hrs,
            extra_params=request.extra_params,
            decisions=decisions,
            explainability=explanations,
        )

        # ── Extend with Phase 2 fields ───────────────────────────────────
        result = ScenarioRunResult(
            **base.model_dump(),
            pathway_headlines=prop.pathway_headlines,
            scenario_name=spec.name,
            scenario_type=spec.scenario_type,
        )

        logger.info(
            "Scenario '%s' complete: loss=%s, risk=%s, headlines=%d",
            slug,
            f"${prop.total_loss_usd:,.0f}",
            result.risk_level,
            len(prop.pathway_headlines),
        )

        return result

    except Exception as e:
        logger.exception("Scenario '%s' failed: %s", slug, str(e))
        raise HTTPException(status_code=500, detail=f"Simulation engine error: {str(e)}")
