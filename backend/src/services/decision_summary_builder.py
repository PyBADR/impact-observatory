"""Decision Summary Builder — normalized bridge between engine internals and frontend.

Takes the raw run result dict (which already contains ``decision_calibration``
and ``decision_trust`` sub-dicts) and produces a flat, frontend-consumable
summary per decision.

Called by the ``/api/v1/runs/{run_id}/decision-summary`` endpoint.
"""

from __future__ import annotations

import logging
from typing import Any

from src.services.institutional_audit import get_audit_entry_count

logger = logging.getLogger(__name__)


def build_decision_summary(run_result: dict) -> dict:
    """Build the DecisionSummaryResponse payload from a cached run result.

    Returns a dict matching the ``DecisionSummaryResponse`` Pydantic model.
    """
    run_id = run_result.get("run_id", "")
    scenario_id = run_result.get("scenario_id", "")

    cal = run_result.get("decision_calibration", {})
    trust = run_result.get("decision_trust", {})

    # Index calibration outputs by decision_id
    ranked_by_id: dict[str, dict] = {}
    for r in cal.get("ranked_decisions", []):
        ranked_by_id[r.get("decision_id", "")] = r

    cal_by_id: dict[str, dict] = {}
    for c in cal.get("calibration_results", []):
        cal_by_id[c.get("decision_id", "")] = c

    auth_by_id: dict[str, dict] = {}
    for a in cal.get("authority_assignments", []):
        auth_by_id[a.get("decision_id", "")] = a

    # Index trust outputs by decision_id
    override_by_id: dict[str, dict] = {}
    for o in trust.get("override_results", []):
        override_by_id[o.get("decision_id", "")] = o

    expl_ids: set[str] = {
        e.get("decision_id", "")
        for e in trust.get("explanations", [])
    }

    # Scenario type from trust layer
    sv = trust.get("scenario_validation", {})
    scenario_type = sv.get("scenario_type", "")

    # Build summary items
    decisions: list[dict] = []
    exec_breakdown: dict[str, int] = {
        "BLOCKED": 0, "HUMAN_REQUIRED": 0, "CONDITIONAL": 0, "AUTO_EXECUTABLE": 0,
    }
    trust_breakdown: dict[str, int] = {
        "HIGH": 0, "MEDIUM": 0, "LOW": 0,
    }

    # Use override_results as the canonical decision list (every decision processed)
    for override in trust.get("override_results", []):
        did = override.get("decision_id", "")
        aid = override.get("action_id", "")

        ranked = ranked_by_id.get(did, {})
        calibrated = cal_by_id.get(did, {})
        authority = auth_by_id.get(did, {})

        exec_mode = override.get("final_status", "HUMAN_REQUIRED")
        t_level = override.get("trust_level", "MEDIUM")

        # Count breakdowns
        if exec_mode in exec_breakdown:
            exec_breakdown[exec_mode] += 1
        if t_level in trust_breakdown:
            trust_breakdown[t_level] += 1

        # Audit entries for this decision
        audit_count = 0
        try:
            trail = _get_decision_audit_count(run_id, did)
            audit_count = trail
        except Exception:
            pass

        decisions.append({
            "decision_id": did,
            "action_id": aid,
            "action_en": _extract_action_text(run_result, aid, "en"),
            "action_ar": _extract_action_text(run_result, aid, "ar"),
            "sector": _extract_sector(run_result, aid),
            "decision_owner_en": authority.get("primary_authority_en", ""),
            "decision_owner_ar": authority.get("primary_authority_ar", ""),
            "deadline_hours": _extract_deadline(run_result, aid),
            "trust_level": t_level,
            "trust_score": override.get("trust_score", 0.0),
            "execution_mode": exec_mode,
            "execution_mode_ar": override.get("final_status_ar", ""),
            "ranking_score": ranked.get("ranking_score", 0.0),
            "calibrated_rank": ranked.get("calibrated_rank", 0),
            "calibration_grade": calibrated.get("calibration_grade", ""),
            "calibration_confidence": calibrated.get("calibration_confidence", 0.0),
            "explainability_available": did in expl_ids,
            "override_rule": override.get("override_rule", ""),
            "override_reason_en": override.get("override_reason_en", ""),
            "override_reason_ar": override.get("override_reason_ar", ""),
            "audit_entries_count": audit_count,
        })

    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "pipeline_stages_completed": run_result.get("pipeline_stages_completed", 80),
        "decisions": decisions,
        "total_decisions": len(decisions),
        "execution_breakdown": exec_breakdown,
        "trust_breakdown": trust_breakdown,
    }


def _get_decision_audit_count(run_id: str, decision_id: str) -> int:
    """Get audit entry count for a specific decision."""
    from src.services.institutional_audit import get_audit_trail_for_decision
    return len(get_audit_trail_for_decision(run_id, decision_id))


def _extract_action_text(run_result: dict, action_id: str, lang: str) -> str:
    """Extract action text from the DQ executive decisions embedded in the run."""
    dq = run_result.get("decision_quality", {})
    for dec in dq.get("executive_decisions", []):
        if dec.get("action_id") == action_id:
            if lang == "ar":
                return dec.get("action_ar", dec.get("action", ""))
            return dec.get("action_en", dec.get("action", ""))
    # Fallback to raw decision_plan actions
    for a in run_result.get("decision_plan", {}).get("actions", []):
        if isinstance(a, dict) and a.get("action_id") == action_id:
            key = "action_ar" if lang == "ar" else "action"
            return a.get(key, a.get("action_en", ""))
    return ""


def _extract_sector(run_result: dict, action_id: str) -> str:
    """Extract sector from DQ or raw action registry."""
    dq = run_result.get("decision_quality", {})
    for dec in dq.get("executive_decisions", []):
        if dec.get("action_id") == action_id:
            return dec.get("sector", "")
    return ""


def _extract_deadline(run_result: dict, action_id: str) -> float:
    """Extract time_to_act_hours from DQ executive decisions."""
    dq = run_result.get("decision_quality", {})
    for dec in dq.get("executive_decisions", []):
        if dec.get("action_id") == action_id:
            return float(dec.get("time_to_act_hours", dec.get("deadline_hours", 0)))
    return 0.0
