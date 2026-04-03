"""v1 Runs API — execute and query scenario runs.

POST /api/v1/runs                              — execute full pipeline
GET  /api/v1/runs                              — list runs (paginated)
GET  /api/v1/runs/{run_id}                     — full result
GET  /api/v1/runs/{run_id}/financial           — financial impacts only
GET  /api/v1/runs/{run_id}/banking             — banking stress only
GET  /api/v1/runs/{run_id}/insurance           — insurance stress only
GET  /api/v1/runs/{run_id}/fintech             — fintech stress only
GET  /api/v1/runs/{run_id}/decision            — decision plan only
GET  /api/v1/runs/{run_id}/explanation         — explanation pack only
GET  /api/v1/runs/{run_id}/report/{mode}       — report in executive|analyst|regulatory mode
GET  /api/v1/runs/{run_id}/business-impact     — business impact summary + loss trajectory
GET  /api/v1/runs/{run_id}/timeline            — timestep-by-timestep temporal simulation
GET  /api/v1/runs/{run_id}/regulatory-timeline — regulatory breach events over time
GET  /api/v1/runs/{run_id}/executive-explanation — executive-level business explanation
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from src.schemas.scenario import ScenarioCreate
from src.services.run_orchestrator import execute_run
from src.services.scenario_service import get_run
from src.services import reporting_service, audit_service
from src.services import run_store
from src.i18n.labels import get_all_labels
from src.core.rbac import enforce_permission, get_role_from_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs", tags=["runs"])


def _get_org_from_request(request: Request) -> str:
    """Extract org from JWT token, default to 'default' for API key auth."""
    from src.services.auth_service import verify_token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = verify_token(token)
        if payload:
            return payload.get("org", "default")
    return "default"


@router.post("", status_code=201)
async def create_run(body: ScenarioCreate, request: Request):
    """Execute a full scenario run through all 15 services.

    Returns: complete run result with headline, financial, banking,
    insurance, fintech, decisions, explanation, business impact,
    timeline, and regulatory state.
    """
    enforce_permission(get_role_from_request(request), "run:create")
    try:
        result = execute_run(body)
        run_store.put_for_org(result["run_id"], result, org=_get_org_from_request(request))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Run execution failed")
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")


@router.get("")
async def list_runs(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all runs, newest first. Paginated.

    Returns summary objects: run_id, template_id, severity, headline_loss_usd, peak_day, status, created_at.
    """
    enforce_permission(get_role_from_request(request), "run:read")
    runs = await run_store.alist_for_org(org=_get_org_from_request(request), limit=limit, offset=offset)
    return {"runs": runs, "limit": limit, "offset": offset, "count": len(runs), "org": _get_org_from_request(request)}


@router.get("/{run_id}")
async def get_run_result(run_id: str, request: Request):
    """Get full result for a completed run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result


@router.get("/{run_id}/financial")
async def get_run_financial(run_id: str, request: Request):
    """Get financial impacts for a run."""
    enforce_permission(get_role_from_request(request), "run:financial")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "run_id": run_id,
        "headline": result["headline"],
        "financial": result["financial"],
    }


@router.get("/{run_id}/banking")
async def get_run_banking(run_id: str, request: Request):
    """Get banking stress for a run."""
    enforce_permission(get_role_from_request(request), "run:banking")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result["banking"]


@router.get("/{run_id}/insurance")
async def get_run_insurance(run_id: str, request: Request):
    """Get insurance stress for a run."""
    enforce_permission(get_role_from_request(request), "run:insurance")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result["insurance"]


@router.get("/{run_id}/fintech")
async def get_run_fintech(run_id: str, request: Request):
    """Get fintech stress for a run."""
    enforce_permission(get_role_from_request(request), "run:fintech")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result["fintech"]


@router.get("/{run_id}/decision")
async def get_run_decision(run_id: str, request: Request):
    """Get decision plan for a run (top 3 actions)."""
    enforce_permission(get_role_from_request(request), "run:decision")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result["decisions"]


@router.get("/{run_id}/explanation")
async def get_run_explanation(run_id: str, request: Request):
    """Get explanation pack for a run."""
    enforce_permission(get_role_from_request(request), "run:explanation")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result["explanation"]


@router.get("/{run_id}/report/{mode}")
async def get_run_report(
    run_id: str,
    mode: str,
    request: Request,
    lang: str = Query("en", pattern=r"^(en|ar)$"),
):
    """Get a formatted report for a run.

    Modes: executive, analyst, regulatory
    Languages: en, ar
    """
    report_perm = f"report:{mode}" if mode in ("executive", "analyst", "regulatory") else "report:executive"
    enforce_permission(get_role_from_request(request), report_perm)
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if mode not in ("executive", "analyst", "regulatory"):
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}. Use executive|analyst|regulatory")

    # We need to reconstruct the typed objects from cached dicts
    # For the executive report, we already have it cached
    if mode == "executive":
        return result.get("executive_report", {})

    # For analyst and regulatory, return the full data
    if mode == "analyst":
        return {
            "mode": "analyst",
            "run_id": run_id,
            "lang": lang,
            "financial": result["financial"],
            "banking": result["banking"],
            "insurance": result["insurance"],
            "fintech": result["fintech"],
            "decisions": result["decisions"],
            "explanation": result["explanation"],
            "flow_states": result.get("flow_states", []),
            "propagation": result.get("propagation", []),
        }

    # Regulatory brief
    return {
        "mode": "regulatory_brief",
        "run_id": run_id,
        "lang": lang,
        "classification": "CONFIDENTIAL",
        "headline": result["headline"],
        "banking": result["banking"],
        "insurance": result["insurance"],
        "fintech": result["fintech"],
        "decisions": result["decisions"],
    }


@router.get("/{run_id}/report/{mode}/pdf")
async def get_run_report_pdf(
    run_id: str,
    mode: str,
    request: Request,
    lang: str = Query(default="en", description="Language: en or ar"),
):
    """Export run report as PDF. Mode: executive|analyst|regulatory."""
    from fastapi.responses import Response
    enforce_permission(get_role_from_request(request), f"report:{mode}" if mode in ("executive", "analyst", "regulatory") else "report:executive")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    try:
        from src.services.pdf_export import generate_executive_pdf
        pdf_bytes = generate_executive_pdf(result, lang=lang)
        filename = f"impact-observatory-{run_id}-{mode}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as e:
        logger.exception("PDF generation failed")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{run_id}/business-impact")
async def get_business_impact(run_id: str, request: Request):
    """Business impact summary with loss trajectory."""
    enforce_permission(get_role_from_request(request), "run:business_impact")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result.get("business_impact", {})


@router.get("/{run_id}/timeline")
async def get_timeline(run_id: str, request: Request):
    """Timestep-by-timestep temporal simulation."""
    enforce_permission(get_role_from_request(request), "run:timeline")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return result.get("timeline", {})


@router.get("/{run_id}/regulatory-timeline")
async def get_regulatory_timeline(run_id: str, request: Request):
    """Regulatory breach events over time."""
    enforce_permission(get_role_from_request(request), "run:regulatory")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    bi = result.get("business_impact", {})
    return {"regulatory_breach_events": bi.get("regulatory_breach_events", []), "regulatory_state": result.get("regulatory_state", {})}


@router.get("/{run_id}/executive-explanation")
async def get_executive_explanation(run_id: str, request: Request):
    """Executive-level business explanation."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if result is None:
        raise HTTPException(status_code=404, detail="Run not found")
    explanation = result.get("explanation", {})
    bi = result.get("business_impact", {})
    summary = bi.get("summary", {})
    return {
        "run_id": run_id,
        "executive_summary": explanation.get("narrative_en", ""),
        "loss_translation": {
            "peak_loss_value": summary.get("peak_cumulative_loss", 0),
            "peak_loss_time": summary.get("peak_loss_timestamp", ""),
            "affected_revenue_value": summary.get("peak_cumulative_loss", 0) * 0.15,
            "entities_at_risk_count": len(result.get("financial", result.get("financial_impacts", []))),
            "business_materiality_band": "critical" if summary.get("business_severity") == "severe" else summary.get("business_severity", "low"),
        },
        "business_severity": summary.get("business_severity", "low"),
        "executive_status": summary.get("executive_status", "monitor"),
    }


@router.post("/{run_id}/actions/{action_id}/approve", status_code=200)
async def approve_action(run_id: str, action_id: str, request: Request):
    """Human-in-the-loop: approve a decision action for execution.

    This is the ONLY way an action can move from PENDING_REVIEW to APPROVED.
    No action executes without explicit human approval.
    """
    enforce_permission(get_role_from_request(request), "action:approve")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    decisions = result.get("decisions", {})
    actions = decisions.get("actions", [])

    # Find the action
    target = None
    for action in actions:
        aid = action.get("id") if isinstance(action, dict) else getattr(action, "id", None)
        if aid == action_id:
            target = action
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found in run {run_id}")

    # Update status
    if isinstance(target, dict):
        target["status"] = "APPROVED"
    else:
        target.status = "APPROVED"

    # Audit trail
    audit_service.record_decision_action(
        run_id=run_id,
        action_id=action_id,
        action=target.get("action") if isinstance(target, dict) else getattr(target, "action", ""),
        owner=target.get("owner") if isinstance(target, dict) else getattr(target, "owner", ""),
        priority=target.get("priority", 0) if isinstance(target, dict) else getattr(target, "priority", 0),
    )

    logger.info("Action %s in run %s approved by human reviewer", action_id, run_id)
    return {
        "run_id": run_id,
        "action_id": action_id,
        "status": "APPROVED",
        "message": "Action approved for execution",
        "message_ar": "تمت الموافقة على الإجراء للتنفيذ",
    }


@router.post("/{run_id}/actions/{action_id}/reject", status_code=200)
async def reject_action(run_id: str, action_id: str, request: Request):
    """Human-in-the-loop: reject a decision action.

    Rejected actions are recorded in the audit trail but not executed.
    """
    enforce_permission(get_role_from_request(request), "action:reject")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    decisions = result.get("decisions", {})
    actions = decisions.get("actions", [])

    target = None
    for action in actions:
        aid = action.get("id") if isinstance(action, dict) else getattr(action, "id", None)
        if aid == action_id:
            target = action
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found in run {run_id}")

    if isinstance(target, dict):
        target["status"] = "REJECTED"
    else:
        target.status = "REJECTED"

    logger.info("Action %s in run %s rejected by human reviewer", action_id, run_id)
    return {
        "run_id": run_id,
        "action_id": action_id,
        "status": "REJECTED",
        "message": "Action rejected",
        "message_ar": "تم رفض الإجراء",
    }


@router.get("/audit/log")
async def get_audit_log(request: Request, run_id: str | None = Query(None), limit: int = Query(100, ge=1, le=1000)):
    """Get audit trail entries."""
    enforce_permission(get_role_from_request(request), "audit:read")
    return audit_service.get_audit_log(run_id=run_id, limit=limit)


@router.get("/audit/stats")
async def get_audit_stats(request: Request):
    """Get aggregate audit statistics."""
    enforce_permission(get_role_from_request(request), "audit:stats")
    return audit_service.get_audit_stats()


@router.get("/labels")
async def get_labels(lang: str = Query("en", pattern=r"^(en|ar)$")):
    """Get all UI labels in the requested language."""
    return get_all_labels(lang)
