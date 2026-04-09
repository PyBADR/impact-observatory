"""v1 Decision Authority API — executive decision directives.

POST /api/v1/decision/authority/run  — execute simulation + narrative + decision authority
GET  /api/v1/decision/authority/{run_id}  — retrieve directive for existing run

This endpoint produces DECISIONS, not reports.
Every response forces executive action.
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.narrative.engine import NarrativeEngine
from src.narrative.decision_authority import DecisionAuthorityEngine
from src.narrative.error_translator import translate_error
from src.core.rbac import enforce_permission, get_role_from_request
from src.services.action_tracking_store import (
    seed_actions,
    list_actions_for_run,
    get_action,
    update_action,
    acknowledge_action,
    get_run_summary,
    get_action_history,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/authority", tags=["decision-authority"])

# Module-level engines — stateless, safe to share
_narrative_engine = NarrativeEngine()
_authority_engine = DecisionAuthorityEngine()

# In-memory directive cache
_directive_cache: dict[str, dict] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Request schema
# ─────────────────────────────────────────────────────────────────────────────

class AuthorityRunRequest(BaseModel):
    """Request body for POST /api/v1/decision/authority/run."""
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


# ─────────────────────────────────────────────────────────────────────────────
# Executive error wrapper — no raw HTTP errors
# ─────────────────────────────────────────────────────────────────────────────

def _executive_error(
    status_code: int,
    title: str,
    message: str,
    action_required: str,
    severity: str = "HIGH",
    trace_id: str | None = None,
) -> JSONResponse:
    """Return structured executive error. No raw HTTP errors allowed."""
    return JSONResponse(
        status_code=status_code,
        content={
            "executive_error": {
                "title": title,
                "title_ar": _translate_title(title),
                "message": message,
                "action_required": action_required,
                "severity": severity,
                "trace_id": trace_id,
            },
        },
    )


def _translate_title(title: str) -> str:
    """Quick title translation for executive errors."""
    t = {
        "Execution Blocked": "التنفيذ محظور",
        "Action Update Blocked": "تحديث الإجراء محظور",
        "Scenario Rejected": "السيناريو مرفوض",
        "Engine Failure": "فشل المحرك",
        "Pipeline Timeout": "انتهاء مهلة خط الأنابيب",
        "Access Denied": "الوصول مرفوض",
        "Validation Error": "خطأ في التحقق",
    }
    return t.get(title, "خطأ")


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/decision/authority/run
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/run", status_code=201, summary="Execute full decision authority pipeline")
async def authority_run(body: AuthorityRunRequest, request: Request):
    """Execute the complete pipeline: Simulation → Narrative → Decision Authority.

    Returns a structured executive directive that forces a decision:
    APPROVE | REJECT | ESCALATE | DELAY

    Pipeline: SimulationEngine → NarrativeEngine → DecisionAuthorityEngine → Directive

    This is a Chief Risk Officer AI. Not a dashboard. Not a report.
    """
    enforce_permission(get_role_from_request(request), "run:create")
    trace_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    # ── Validate scenario ────────────────────────────────────────────────
    try:
        from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG

        if body.scenario_id not in SCENARIO_CATALOG:
            available = sorted(SCENARIO_CATALOG.keys())
            return _executive_error(
                status_code=400,
                title="Scenario Rejected",
                message=f"Scenario '{body.scenario_id}' does not exist in the observatory catalog. {len(available)} scenarios available.",
                action_required=f"Select a valid scenario from: {', '.join(available[:5])}{'...' if len(available) > 5 else ''}",
                severity="MODERATE",
                trace_id=trace_id,
            )
    except ImportError as e:
        return _executive_error(
            status_code=500,
            title="Engine Failure",
            message=f"SimulationEngine module failed to load. Infrastructure issue detected.",
            action_required="Contact platform engineering team immediately. System integrity compromised.",
            severity="CRITICAL",
            trace_id=trace_id,
        )

    # ── Run simulation ───────────────────────────────────────────────────
    try:
        engine = SimulationEngine()
        simulation = engine.run(
            scenario_id=body.scenario_id,
            severity=body.severity,
            horizon_hours=body.horizon_hours,
        )
    except ValueError as e:
        return _executive_error(
            status_code=400,
            title="Execution Blocked",
            message=f"Simulation parameters rejected: {e}",
            action_required="Correct severity (0.0-1.0) and horizon_hours (1-8760), then resubmit.",
            severity="MODERATE",
            trace_id=trace_id,
        )
    except Exception as e:
        logger.exception(f"[{trace_id}] SimulationEngine.run() failed")
        return _executive_error(
            status_code=500,
            title="Engine Failure",
            message=f"Simulation engine encountered a critical failure during scenario execution.",
            action_required="Retry with reduced severity or horizon. If persistent, escalate to platform team.",
            severity="HIGH",
            trace_id=trace_id,
        )

    # ── Generate narrative ───────────────────────────────────────────────
    try:
        narrative = _narrative_engine.generate(simulation)
    except Exception as e:
        logger.warning(f"[{trace_id}] Narrative generation failed: {e}")
        narrative = {"executive_summary": {}, "narrative_available": False}

    # ── Generate decision authority ──────────────────────────────────────
    try:
        authority = _authority_engine.generate(simulation, narrative)
    except Exception as e:
        logger.exception(f"[{trace_id}] DecisionAuthorityEngine.generate() failed")
        return _executive_error(
            status_code=500,
            title="Engine Failure",
            message="Decision authority engine failed to produce executive directive.",
            action_required="Manual risk assessment required. Convene risk committee immediately.",
            severity="HIGH",
            trace_id=trace_id,
        )

    # ── Assemble response ────────────────────────────────────────────────
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response = {
        **authority,
        "meta": {
            "trace_id": trace_id,
            "pipeline": "SimulationEngine → NarrativeEngine → DecisionAuthorityEngine",
            "model_version": simulation.get("model_version", "2.1.0"),
            "duration_ms": duration_ms,
            "scenario_id": body.scenario_id,
            "severity": body.severity,
            "horizon_hours": body.horizon_hours,
        },
    }

    # Seed actions into tracking store
    run_id = simulation.get("run_id", trace_id)
    da_actions = authority.get("decision_authority", {}).get("recommended_actions", [])
    if da_actions:
        seed_actions(run_id, da_actions)

    # Cache
    _directive_cache[run_id] = response

    da = authority.get("decision_authority", {})
    ed = da.get("executive_directive", {})

    logger.info(
        f"[{trace_id}] Decision Authority: "
        f"decision={ed.get('decision', '?')} "
        f"urgency={ed.get('urgency_level', '?')} "
        f"pressure={da.get('decision_pressure_score', {}).get('score', 0)} "
        f"scenario={body.scenario_id} "
        f"severity={body.severity} "
        f"duration={duration_ms}ms"
    )

    return response


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/decision/authority/{run_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{run_id}", summary="Retrieve decision authority directive for existing run")
async def get_authority_directive(run_id: str, request: Request):
    """Retrieve cached decision authority directive.

    If the run exists but has no cached directive, generates on-the-fly.
    """
    enforce_permission(get_role_from_request(request), "run:read")

    if run_id in _directive_cache:
        return _directive_cache[run_id]

    try:
        from src.services import run_store
        stored = run_store.get_run(run_id)
        if stored is None:
            return _executive_error(
                status_code=404,
                title="Execution Blocked",
                message=f"Run '{run_id}' not found. No decision authority directive available.",
                action_required="Execute a new scenario run via POST /api/v1/decision/authority/run.",
                severity="LOW",
                trace_id=run_id[:8],
            )

        result = stored.get("result", stored)
        narrative = _narrative_engine.generate(result)
        authority = _authority_engine.generate(result, narrative)

        response = {
            **authority,
            "meta": {
                "trace_id": run_id[:8],
                "pipeline": "RunStore → NarrativeEngine → DecisionAuthorityEngine",
                "model_version": result.get("model_version", "2.1.0"),
                "generated_on_demand": True,
            },
        }
        _directive_cache[run_id] = response
        return response

    except Exception as e:
        logger.exception(f"Failed to retrieve/generate authority for run {run_id}")
        return _executive_error(
            status_code=500,
            title="Engine Failure",
            message=f"Failed to generate decision authority directive for run {run_id}.",
            action_required="Retry or execute a new scenario run.",
            severity="MODERATE",
            trace_id=run_id[:8],
        )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/decision/authority/actions/{run_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/actions/{run_id}", summary="List tracked actions for a decision authority run")
async def get_run_actions(run_id: str, request: Request):
    """Return all tracked actions for a run with current status and progress.

    Includes per-run summary: total, by_status, overall_progress, acknowledgment rate.
    """
    enforce_permission(get_role_from_request(request), "run:read")

    actions = list_actions_for_run(run_id)
    summary = get_run_summary(run_id)

    if not actions:
        return _executive_error(
            status_code=404,
            title="Execution Blocked",
            message=f"No tracked actions found for run '{run_id}'.",
            action_required="Execute a scenario via POST /api/v1/decision/authority/run first.",
            severity="LOW",
            trace_id=run_id[:8],
        )

    return {
        "run_id": run_id,
        "actions": actions,
        "summary": summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/decision/authority/actions/{action_id}
# ─────────────────────────────────────────────────────────────────────────────

class ActionUpdateRequest(BaseModel):
    """Request body for PATCH action updates."""
    status: str | None = Field(
        default=None,
        description="New status: ACKNOWLEDGED | IN_PROGRESS | DONE | BLOCKED",
        json_schema_extra={"example": "ACKNOWLEDGED"},
    )
    execution_progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Execution progress percentage (0-100)",
        json_schema_extra={"example": 50},
    )
    owner_acknowledged: bool | None = Field(
        default=None,
        description="Owner has seen and accepted this action",
        json_schema_extra={"example": True},
    )
    note: str | None = Field(
        default=None,
        max_length=1000,
        description="Operator note (timestamped, appended to action history)",
        json_schema_extra={"example": "Treasury team activated. Monitoring interbank rates."},
    )
    actor: str | None = Field(
        default=None,
        max_length=200,
        description="Actor identifier for audit trail (e.g. user email, role, or system name)",
        json_schema_extra={"example": "cro@deevo.ai"},
    )


@router.patch("/actions/{action_id}", summary="Update action tracking status")
async def patch_action(action_id: str, body: ActionUpdateRequest, request: Request):
    """Update an action's status, progress, acknowledgment, or add notes.

    State machine: PENDING → ACKNOWLEDGED → IN_PROGRESS → DONE | BLOCKED

    Invalid transitions are rejected with executive-grade error messages.
    All updates are timestamped and SHA-256 hashed for audit.
    """
    enforce_permission(get_role_from_request(request), "run:create")

    existing = get_action(action_id)
    if existing is None:
        return _executive_error(
            status_code=404,
            title="Execution Blocked",
            message=f"Action '{action_id}' not found in tracking system.",
            action_required="Verify action_id from GET /api/v1/decision/authority/actions/{{run_id}}.",
            severity="LOW",
            trace_id=action_id[:8],
        )

    try:
        updated = update_action(
            action_id,
            status=body.status,
            execution_progress=body.execution_progress,
            owner_acknowledged=body.owner_acknowledged,
            note=body.note,
            actor=body.actor,
        )
    except ValueError as e:
        return _executive_error(
            status_code=400,
            title="Action Update Blocked",
            message=str(e),
            action_required="Correct the status transition and resubmit.",
            severity="MODERATE",
            trace_id=action_id[:8],
        )

    if updated is None:
        return _executive_error(
            status_code=500,
            title="Engine Failure",
            message=f"Failed to update action '{action_id}'.",
            action_required="Retry the update. If persistent, escalate to platform team.",
            severity="MODERATE",
            trace_id=action_id[:8],
        )

    logger.info(
        f"Action {action_id} updated: "
        f"status={updated.get('status')} "
        f"progress={updated.get('execution_progress')}% "
        f"acknowledged={updated.get('owner_acknowledged')}"
    )

    return {
        "action": updated,
        "meta": {
            "update_hash": updated.get("last_update_hash", ""),
            "updated_at": updated.get("updated_at", ""),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/decision/authority/actions/{action_id}/acknowledge
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/actions/{action_id}/acknowledge", summary="Acknowledge an action (shorthand)")
async def acknowledge_action_endpoint(action_id: str, request: Request):
    """Quick acknowledgment: moves action to ACKNOWLEDGED, sets owner_acknowledged=True.

    Convenience endpoint — equivalent to PATCH with status=ACKNOWLEDGED.
    """
    enforce_permission(get_role_from_request(request), "run:create")

    existing = get_action(action_id)
    if existing is None:
        return _executive_error(
            status_code=404,
            title="Execution Blocked",
            message=f"Action '{action_id}' not found.",
            action_required="Verify action_id exists.",
            severity="LOW",
            trace_id=action_id[:8],
        )

    try:
        updated = acknowledge_action(action_id)
    except ValueError as e:
        return _executive_error(
            status_code=400,
            title="Execution Blocked",
            message=str(e),
            action_required="Action may already be acknowledged or completed.",
            severity="LOW",
            trace_id=action_id[:8],
        )

    return {
        "action": updated,
        "meta": {
            "acknowledged": True,
            "updated_at": updated.get("updated_at", "") if updated else "",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/decision/authority/actions/{action_id}/history
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/actions/{action_id}/history", summary="Get audit history for an action")
async def get_action_history_endpoint(action_id: str, request: Request):
    """Return the full audit history for a specific action.

    Each entry includes: timestamp, previous_status, new_status, actor, notes, audit_hash.
    """
    enforce_permission(get_role_from_request(request), "run:read")

    existing = get_action(action_id)
    if existing is None:
        return _executive_error(
            status_code=404,
            title="Execution Blocked",
            message=f"Action '{action_id}' not found in tracking system.",
            action_required="Verify action_id from GET /api/v1/decision/authority/actions/{{run_id}}.",
            severity="LOW",
            trace_id=action_id[:8],
        )

    history = get_action_history(action_id)

    return {
        "action_id": action_id,
        "action": existing.get("action", ""),
        "current_status": existing.get("status", "PENDING"),
        "history": history,
        "total_updates": len(history),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic validation error handler — catches framework errors before they leak
# ─────────────────────────────────────────────────────────────────────────────

from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI


def register_validation_handler(app: FastAPI) -> None:
    """Register a global handler that wraps Pydantic validation errors
    in executive-safe JSON. Call from main.py after app creation."""

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError):
        # Only intercept for decision authority routes
        path = request.url.path
        if "/decision/authority" not in path:
            # Let other routes use default handler
            return JSONResponse(
                status_code=422,
                content={"detail": exc.errors()},
            )

        # Build human-readable summary of validation failures
        issues = []
        for err in exc.errors():
            loc = " → ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "invalid value")
            issues.append(f"{loc}: {msg}")

        return JSONResponse(
            status_code=400,
            content={
                "executive_error": {
                    "title": "Validation Error",
                    "title_ar": "خطأ في التحقق",
                    "message": f"Request rejected: {'; '.join(issues)}",
                    "action_required": "Correct the request parameters and resubmit.",
                    "severity": "LOW",
                    "trace_id": None,
                },
            },
        )
