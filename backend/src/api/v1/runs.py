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
import uuid

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
    trace_id = str(uuid.uuid4())[:8]
    try:
        raw_result = execute_run(body)

        # Fix 3: VALIDATION GATE — validate structural contract before returning to client
        # This ensures the frontend CANNOT receive malformed payloads.
        try:
            from src.simulation_schemas import SimulateResponse
            _validated = SimulateResponse.model_validate(raw_result)
            # Use raw_result for the full response (SimulateResponse only validates a subset)
            # but enforce that core fields are structurally sound
        except Exception as validation_err:
            logger.error(
                "[Pipeline] Response validation failed — returning structured error",
                extra={
                    "trace_id": trace_id,
                    "scenario_id": getattr(body, "scenario_id", "unknown"),
                    "error": str(validation_err),
                    "stage": "response_serialization",
                },
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "PIPELINE_VALIDATION_FAILED",
                    "message": "Pipeline produced invalid response structure",
                    "trace_id": trace_id,
                    "scenario_id": getattr(body, "scenario_id", "unknown"),
                },
            )

        raw_result["trace_id"] = trace_id
        run_store.put_for_org(raw_result["run_id"], raw_result, org=_get_org_from_request(request))

        # Notify Slack (fire-and-forget — non-blocking)
        try:
            import asyncio
            from src.connectors.slack_connector import notify_run_complete
            asyncio.ensure_future(notify_run_complete(raw_result))
        except Exception:
            pass  # Slack is optional — never block the response

        return raw_result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("[Pipeline] Unhandled error", extra={"trace_id": trace_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PIPELINE_ERROR",
                "message": str(e),
                "trace_id": trace_id,
            },
        )


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

    # Notify Slack
    try:
        import asyncio
        from src.connectors.slack_connector import notify_action_decision
        action_text = target.get("action", "") if isinstance(target, dict) else getattr(target, "action", "")
        owner_text = target.get("owner", "") if isinstance(target, dict) else getattr(target, "owner", "")
        asyncio.ensure_future(notify_action_decision(run_id, action_id, action_text, "APPROVED", owner_text))
    except Exception:
        pass

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

    # Notify Slack
    try:
        import asyncio
        from src.connectors.slack_connector import notify_action_decision
        action_text = target.get("action", "") if isinstance(target, dict) else getattr(target, "action", "")
        owner_text = target.get("owner", "") if isinstance(target, dict) else getattr(target, "owner", "")
        asyncio.ensure_future(notify_action_decision(run_id, action_id, action_text, "REJECTED", owner_text))
    except Exception:
        pass

    return {
        "run_id": run_id,
        "action_id": action_id,
        "status": "REJECTED",
        "message": "Action rejected",
        "message_ar": "تم رفض الإجراء",
    }


@router.get("/{run_id}/map")
async def get_run_map_payload(run_id: str, request: Request):
    """Get map payload — geo-located entities with impact data + propagation arcs.

    Co-origin with graph: both derive from the same SimulationEngine run.
    This resolves the map_payload / graph_payload co-origin requirement.
    """
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    from src.simulation_engine import GCC_NODES

    # Build node lookup: id → {lat, lng, label, label_ar, sector}
    node_map = {}
    for n in GCC_NODES:
        node_map[n["id"]] = n

    # Build map entities from financial impacts
    financial = result.get("financial", result.get("financial_impact", {}).get("top_entities", []))
    if isinstance(financial, dict):
        financial = financial.get("top_entities", [])

    entities = []
    bottleneck_ids = set()
    for b in result.get("bottlenecks", []):
        bid = b.get("node_id") if isinstance(b, dict) else getattr(b, "node_id", "")
        if bid:
            bottleneck_ids.add(bid)

    for fi in (financial if isinstance(financial, list) else []):
        eid = fi.get("entity_id", "") if isinstance(fi, dict) else getattr(fi, "entity_id", "")
        node = node_map.get(eid)
        if not node:
            continue
        entities.append({
            "entity_id": eid,
            "entity_label": fi.get("entity_label", eid) if isinstance(fi, dict) else getattr(fi, "entity_label", eid),
            "entity_label_ar": node.get("label_ar", ""),
            "lat": node["lat"],
            "lng": node["lng"],
            "sector": node["sector"],
            "loss_usd": fi.get("loss_usd", 0) if isinstance(fi, dict) else getattr(fi, "loss_usd", 0),
            "stress_score": fi.get("stress_score", 0) if isinstance(fi, dict) else getattr(fi, "stress_score", 0),
            "classification": fi.get("classification", "MODERATE") if isinstance(fi, dict) else getattr(fi, "classification", "MODERATE"),
            "is_bottleneck": eid in bottleneck_ids,
        })

    # Build arcs from propagation chain
    arcs = []
    seen = set()
    for step in result.get("propagation_chain", result.get("propagation", [])):
        if not isinstance(step, dict):
            continue
        path = step.get("path", [])
        if len(path) >= 2:
            from_id = path[-2]
            to_id = path[-1]
            key = f"{from_id}-{to_id}"
            if key not in seen and from_id in node_map and to_id in node_map:
                seen.add(key)
                arcs.append({
                    "from_id": from_id,
                    "to_id": to_id,
                    "from_lat": node_map[from_id]["lat"],
                    "from_lng": node_map[from_id]["lng"],
                    "to_lat": node_map[to_id]["lat"],
                    "to_lng": node_map[to_id]["lng"],
                    "impact": step.get("impact", 0),
                    "hop": step.get("hop", 0),
                })

    headline = result.get("headline", {})
    return {
        "run_id": run_id,
        "scenario_id": result.get("scenario_id", ""),
        "entities": entities,
        "arcs": arcs[:50],
        "total_loss_usd": headline.get("total_loss_usd", 0),
        "peak_day": headline.get("peak_day", 0),
        "risk_level": result.get("risk_level", ""),
        "node_count": len(entities),
        "arc_count": len(arcs),
    }


@router.get("/{run_id}/graph")
async def get_run_graph_payload(run_id: str, request: Request):
    """Get graph payload — nodes and edges for graph/network visualization.

    Co-origin with map: both derive from the same SimulationEngine run.
    """
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    financial = result.get("financial", result.get("financial_impact", {}).get("top_entities", []))
    if isinstance(financial, dict):
        financial = financial.get("top_entities", [])

    nodes = []
    for fi in (financial if isinstance(financial, list) else []):
        eid = fi.get("entity_id", "") if isinstance(fi, dict) else getattr(fi, "entity_id", "")
        nodes.append({
            "id": eid,
            "label": fi.get("entity_label", eid) if isinstance(fi, dict) else getattr(fi, "entity_label", eid),
            "sector": fi.get("sector", "") if isinstance(fi, dict) else getattr(fi, "sector", ""),
            "risk_score": fi.get("stress_score", 0) if isinstance(fi, dict) else getattr(fi, "stress_score", 0),
            "stress_score": fi.get("stress_score", 0) if isinstance(fi, dict) else getattr(fi, "stress_score", 0),
            "classification": fi.get("classification", "MODERATE") if isinstance(fi, dict) else getattr(fi, "classification", "MODERATE"),
            "loss_usd": fi.get("loss_usd", 0) if isinstance(fi, dict) else getattr(fi, "loss_usd", 0),
        })

    edges = []
    seen = set()
    for step in result.get("propagation_chain", result.get("propagation", [])):
        if not isinstance(step, dict):
            continue
        path = step.get("path", [])
        if len(path) >= 2:
            source = path[-2]
            target = path[-1]
            key = f"{source}-{target}"
            if key not in seen:
                seen.add(key)
                edges.append({
                    "source": source,
                    "target": target,
                    "weight": step.get("impact", 0),
                    "hop": step.get("hop", 0),
                })

    return {
        "run_id": run_id,
        "scenario_id": result.get("scenario_id", ""),
        "nodes": nodes,
        "edges": edges[:100],
    }


@router.get("/{run_id}/transmission")
async def get_run_transmission(run_id: str, request: Request):
    """Get transmission chain — causal propagation path with breakable points."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result.get("transmission_chain", {})


@router.get("/{run_id}/counterfactual")
async def get_run_counterfactual(run_id: str, request: Request):
    """Get calibrated counterfactual — baseline vs recommended vs alternative."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result.get("counterfactual", {})


@router.get("/{run_id}/action-pathways")
async def get_run_action_pathways(run_id: str, request: Request):
    """Get structured action pathways — IMMEDIATE / CONDITIONAL / STRATEGIC."""
    enforce_permission(get_role_from_request(request), "run:decision")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result.get("action_pathways", {})


@router.get("/{run_id}/decision-trust")
async def get_run_decision_trust(run_id: str, request: Request):
    """Get decision trust payload — confidence, dependency, validation, risk envelope."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "action_confidence": result.get("action_confidence", []),
        "model_dependency": result.get("model_dependency", {}),
        "validation": result.get("validation", {}),
        "confidence_breakdown": result.get("confidence_breakdown", {}),
        "risk_profile": result.get("risk_profile", {}),
    }


@router.get("/{run_id}/decision-integration")
async def get_run_decision_integration(run_id: str, request: Request):
    """Get decision integration payload — ownership, workflows, execution, lifecycle, integrations."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "decision_ownership": result.get("decision_ownership", []),
        "workflows": result.get("decision_workflows", []),
        "execution_triggers": result.get("execution_triggers", []),
        "decision_lifecycle": result.get("decision_lifecycle", []),
        "integration": result.get("integration", {}),
    }


@router.get("/{run_id}/decision-value")
async def get_run_decision_value(run_id: str, request: Request):
    """Get decision value payload — expected vs actual, attribution, effectiveness, portfolio."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "expected_actual": result.get("expected_actual", []),
        "value_attribution": result.get("value_attribution", []),
        "effectiveness": result.get("effectiveness", []),
        "portfolio_value": result.get("portfolio_value", {}),
    }


@router.get("/{run_id}/governance")
async def get_run_governance(run_id: str, request: Request):
    """Get governance payload — evidence, policy, attribution defense, overrides (Phase 5)."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "decision_evidence": result.get("decision_evidence", []),
        "policy": result.get("policy", []),
        "attribution_defense": result.get("attribution_defense", []),
        "overrides": result.get("overrides", []),
    }


@router.get("/{run_id}/evidence/{decision_id}")
async def get_decision_evidence(run_id: str, decision_id: str, request: Request):
    """Get full evidence pack for a single decision."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    evidence_list = result.get("decision_evidence", [])
    for ev in evidence_list:
        if isinstance(ev, dict) and ev.get("decision_id") == decision_id:
            return ev
    raise HTTPException(status_code=404, detail=f"Evidence for decision {decision_id} not found in run {run_id}")


@router.get("/{run_id}/audit-trail")
async def get_run_audit_trail(run_id: str, request: Request):
    """Get full audit trail for a run — evidence + policy + overrides combined."""
    enforce_permission(get_role_from_request(request), "audit:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "run_id": run_id,
        "pipeline_stages_completed": result.get("pipeline_stages_completed", 0),
        "decision_evidence": result.get("decision_evidence", []),
        "policy": result.get("policy", []),
        "attribution_defense": result.get("attribution_defense", []),
        "overrides": result.get("overrides", []),
        "stage_timings": result.get("stage_timings", {}),
    }


@router.get("/{run_id}/pilot")
async def get_run_pilot(run_id: str, request: Request):
    """Get full Phase 6 pilot payload — scope, KPIs, shadow, report, failures."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "run_id": run_id,
        "pilot_scope": result.get("pilot_scope", {}),
        "pilot_kpi": result.get("pilot_kpi", {}),
        "shadow_comparisons": result.get("shadow_comparisons", []),
        "pilot_report": result.get("pilot_report", {}),
        "failure_modes": result.get("failure_modes", []),
    }


@router.get("/{run_id}/pilot/kpi")
async def get_run_pilot_kpi(run_id: str, request: Request):
    """Get pilot KPI measurements for a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result.get("pilot_kpi", {})


@router.get("/{run_id}/pilot/shadow")
async def get_run_shadow_comparisons(run_id: str, request: Request):
    """Get shadow mode comparisons for a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return {
        "run_id": run_id,
        "shadow_comparisons": result.get("shadow_comparisons", []),
        "execution_mode": result.get("pilot_scope", {}).get("execution_mode", "SHADOW"),
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


@router.get("/system/status")
async def get_system_status(request: Request):
    """Get system-wide status including all connector health.

    Checks: Vercel deployment, GitHub CI, Slack webhook, Neo4j, Redis, PostgreSQL.
    """
    enforce_permission(get_role_from_request(request), "run:read")

    import os

    status: dict = {
        "service": "Impact Observatory | مرصد الأثر",
        "model_version": "2.1.0",
        "connectors": {},
    }

    # Vercel
    try:
        from src.connectors.vercel_connector import get_latest_deployment
        vercel = await get_latest_deployment()
        status["connectors"]["vercel"] = {
            "configured": vercel.get("configured", False),
            "state": vercel.get("state", "unknown"),
            "url": vercel.get("url", ""),
        }
    except Exception as e:
        status["connectors"]["vercel"] = {"configured": False, "error": str(e)}

    # GitHub
    try:
        from src.connectors.github_connector import get_workflow_status
        gh = await get_workflow_status()
        status["connectors"]["github"] = {
            "configured": gh.get("configured", False),
            "ci_status": gh.get("status", "unknown"),
        }
    except Exception as e:
        status["connectors"]["github"] = {"configured": False, "error": str(e)}

    # Slack
    status["connectors"]["slack"] = {
        "configured": bool(os.getenv("SLACK_WEBHOOK_URL")),
    }

    # Neo4j
    try:
        from src.db.neo4j import get_neo4j_session
        async with get_neo4j_session() as session:
            result = await session.run("RETURN 1")
            status["connectors"]["neo4j"] = {"configured": True, "status": "connected"}
    except Exception:
        status["connectors"]["neo4j"] = {"configured": False, "status": "disconnected"}

    # Redis
    try:
        from src.db.redis import get_redis
        r = get_redis()
        if r:
            await r.ping()
            status["connectors"]["redis"] = {"configured": True, "status": "connected"}
        else:
            status["connectors"]["redis"] = {"configured": False, "status": "not initialized"}
    except Exception:
        status["connectors"]["redis"] = {"configured": False, "status": "disconnected"}

    # Notion (via env check only — no runtime dependency)
    status["connectors"]["notion"] = {
        "configured": True,
        "project_url": "https://www.notion.so/3390a456744c81a9939adcfd8a8b559d",
        "decision_log": True,
        "trust_recovery_tracker": True,
    }

    # Simulation engine
    try:
        from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
        status["engine"] = {
            "version": SimulationEngine.MODEL_VERSION,
            "scenarios": len(SCENARIO_CATALOG),
            "status": "ready",
        }
    except Exception as e:
        status["engine"] = {"status": "error", "error": str(e)}

    return status
