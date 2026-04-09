"""v1 Narrative API — unified simulation + executive narrative endpoint.

POST /api/v1/narrative/run   — execute simulation + generate narrative
GET  /api/v1/narrative/{run_id}  — retrieve narrative for an existing run
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.narrative.engine import NarrativeEngine
from src.narrative.error_translator import translate_error
from src.core.rbac import enforce_permission, get_role_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/narrative", tags=["narrative"])

# Module-level engine — stateless, safe to share
_engine = NarrativeEngine()

# In-memory narrative cache (keyed by run_id)
_narrative_cache: dict[str, dict] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class NarrativeRunRequest(BaseModel):
    """Request body for POST /api/v1/narrative/run."""
    scenario_id: str = Field(
        ...,
        description="Scenario identifier from the catalog",
        json_schema_extra={"example": "hormuz_chokepoint_disruption"},
    )
    severity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Event severity (0.0 = nominal, 1.0 = catastrophic)",
        json_schema_extra={"example": 0.7},
    )
    horizon_hours: int = Field(
        default=336,
        ge=1,
        le=8760,
        description="Simulation time horizon in hours",
        json_schema_extra={"example": 336},
    )
    language: str = Field(
        default="en",
        description="Primary language for narrative: 'en' or 'ar' (both always included)",
        json_schema_extra={"example": "en"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/narrative/run
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/run", status_code=201, summary="Execute simulation + generate executive narrative")
async def narrative_run(body: NarrativeRunRequest, request: Request):
    """Execute the full simulation pipeline and wrap output in executive narrative.

    Returns the complete SimulateResponse enriched with:
    - executive_summary (bilingual headline, exposure, urgency)
    - causal_chain_story (root cause → propagation path → effects)
    - sector_stories (per-sector impact narrative with metrics)
    - decision_rationale (enriched actions with ROI + consequence analysis)
    - governance (audit trail, model certainty, methodology transparency)

    Pipeline: SimulationEngine.run() → NarrativeEngine.generate() → Response
    """
    enforce_permission(get_role_from_request(request), "run:create")
    trace_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    # ── Validate scenario ────────────────────────────────────────────────
    try:
        from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG

        if body.scenario_id not in SCENARIO_CATALOG:
            available = sorted(SCENARIO_CATALOG.keys())
            error_brief = translate_error(
                status_code=400,
                error_type="invalid_scenario",
                raw_detail=f"Scenario '{body.scenario_id}' not in catalog. Available: {available}",
                trace_id=trace_id,
                scenario_id=body.scenario_id,
            )
            return JSONResponse(status_code=400, content=error_brief)
    except ImportError as e:
        error_brief = translate_error(
            status_code=500,
            error_type="engine_error",
            raw_detail=f"SimulationEngine import failed: {e}",
            trace_id=trace_id,
        )
        return JSONResponse(status_code=500, content=error_brief)

    # ── Run simulation ───────────────────────────────────────────────────
    try:
        engine = SimulationEngine()
        result = engine.run(
            scenario_id=body.scenario_id,
            severity=body.severity,
            horizon_hours=body.horizon_hours,
        )
    except ValueError as e:
        error_brief = translate_error(
            status_code=400,
            error_type="validation_error",
            raw_detail=str(e),
            trace_id=trace_id,
            scenario_id=body.scenario_id,
        )
        return JSONResponse(status_code=400, content=error_brief)
    except TimeoutError as e:
        error_brief = translate_error(
            status_code=504,
            error_type="timeout",
            raw_detail=str(e),
            trace_id=trace_id,
            scenario_id=body.scenario_id,
        )
        return JSONResponse(status_code=504, content=error_brief)
    except Exception as e:
        logger.exception(f"[{trace_id}] SimulationEngine.run() failed")
        error_brief = translate_error(
            status_code=500,
            error_type="engine_error",
            raw_detail=str(e),
            trace_id=trace_id,
            scenario_id=body.scenario_id,
        )
        return JSONResponse(status_code=500, content=error_brief)

    # ── Generate narrative ───────────────────────────────────────────────
    try:
        narrative = _engine.generate(result)
    except Exception as e:
        logger.exception(f"[{trace_id}] NarrativeEngine.generate() failed")
        # Return raw simulation result with error note rather than failing
        narrative = {
            "narrative_error": str(e),
            "narrative_available": False,
        }

    # ── Assemble unified response ────────────────────────────────────────
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response = {
        # Core simulation output (all 16+ fields)
        "simulation": result,
        # Executive narrative layer
        "narrative": narrative,
        # Meta
        "meta": {
            "trace_id": trace_id,
            "pipeline": "SimulationEngine → NarrativeEngine",
            "model_version": result.get("model_version", "2.1.0"),
            "duration_ms": duration_ms,
            "language_primary": body.language,
            "narrative_available": narrative.get("narrative_available", True),
        },
    }

    # Cache for GET retrieval
    run_id = result.get("run_id", trace_id)
    _narrative_cache[run_id] = response

    logger.info(
        f"[{trace_id}] Narrative run complete: "
        f"scenario={body.scenario_id} severity={body.severity} "
        f"risk_level={result.get('risk_level', '?')} "
        f"duration={duration_ms}ms"
    )

    return response


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/narrative/{run_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{run_id}", summary="Retrieve narrative for an existing run")
async def get_narrative(run_id: str, request: Request):
    """Retrieve the cached narrative for a previously executed run.

    If the run exists in the run store but has no cached narrative,
    generates the narrative on-the-fly.
    """
    enforce_permission(get_role_from_request(request), "run:read")

    # Check narrative cache first
    if run_id in _narrative_cache:
        return _narrative_cache[run_id]

    # Try to find the run in the run store and generate narrative
    try:
        from src.services import run_store
        stored = run_store.get_run(run_id)
        if stored is None:
            error_brief = translate_error(
                status_code=404,
                error_type="run_not_found",
                raw_detail=f"Run ID '{run_id}' not found in store or narrative cache.",
                trace_id=run_id[:8],
            )
            return JSONResponse(status_code=404, content=error_brief)

        # Generate narrative from stored result
        result = stored.get("result", stored)
        narrative = _engine.generate(result)

        response = {
            "simulation": result,
            "narrative": narrative,
            "meta": {
                "trace_id": run_id[:8],
                "pipeline": "RunStore → NarrativeEngine",
                "model_version": result.get("model_version", "2.1.0"),
                "narrative_available": True,
                "generated_on_demand": True,
            },
        }
        _narrative_cache[run_id] = response
        return response

    except Exception as e:
        logger.exception(f"Failed to retrieve/generate narrative for run {run_id}")
        error_brief = translate_error(
            status_code=500,
            error_type="engine_error",
            raw_detail=str(e),
            trace_id=run_id[:8],
        )
        return JSONResponse(status_code=500, content=error_brief)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/narrative/scenarios — list scenarios with narrative context
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/scenarios", summary="List scenarios with narrative context metadata")
async def list_narrative_scenarios():
    """Return all scenarios with their narrative context (signal, root cause, strategic context).

    Useful for UI dropdowns that want to show executives what each scenario means
    before they run it.
    """
    from src.narrative.engine import NarrativeEngine

    contexts = NarrativeEngine._SCENARIO_CONTEXT if hasattr(NarrativeEngine, '_SCENARIO_CONTEXT') else {}

    scenarios = []
    for sid, ctx in contexts.items():
        scenarios.append({
            "scenario_id": sid,
            "signal": ctx.get("signal", ""),
            "signal_ar": ctx.get("signal_ar", ""),
            "root_cause": ctx.get("root_cause", ""),
            "root_cause_ar": ctx.get("root_cause_ar", ""),
            "strategic_context": ctx.get("strategic_context", ""),
            "strategic_context_ar": ctx.get("strategic_context_ar", ""),
        })

    return {
        "count": len(scenarios),
        "scenarios": scenarios,
    }
