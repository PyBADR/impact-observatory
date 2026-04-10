"""
Decision Lifecycle Tracker — Phase 3 Engine 4

Tracks the full lifecycle of each decision from issuance through
approval to execution, with timestamps and status transitions.

Pure function. Never throws. Returns safe defaults.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _safe_str(v, fb: str = "") -> str:
    if v is None:
        return fb
    s = str(v).strip()
    return s if s else fb


def _now_iso() -> str:
    """UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def track_decision_lifecycle(
    decision: dict,
    *,
    workflow: dict | None = None,
    execution: dict | None = None,
) -> dict:
    """Track lifecycle state for a single decision.

    Status transitions:
      ISSUED → APPROVED → EXECUTED → COMPLETED

    Returns:
        {decision_id, status, issued_at, approved_at, executed_at, outcome}
    """
    decision_id = _safe_str(
        decision.get("id") or decision.get("action_id") or decision.get("rank"),
        f"lc_{id(decision)}",
    )

    # Always issued at pipeline run time
    issued_at = _now_iso()

    # Determine lifecycle status from workflow + execution
    approved_at = None
    executed_at = None
    outcome = None
    status = "ISSUED"

    if workflow:
        wf_status = _safe_str(workflow.get("status"), "PENDING")

        if wf_status == "APPROVED":
            status = "APPROVED"
            approved_at = _now_iso()

            # Check execution
            if execution:
                trigger_ready = execution.get("trigger_ready", False)
                exec_mode = _safe_str(execution.get("execution_mode"), "MANUAL")

                if trigger_ready and exec_mode == "AUTO":
                    status = "EXECUTED"
                    executed_at = _now_iso()
                    outcome = "auto_executed"
                elif trigger_ready:
                    outcome = "ready_for_manual_execution"

        elif wf_status == "ESCALATED":
            status = "ISSUED"  # still issued, pending escalation review
            outcome = "escalated_to_" + "_".join(
                workflow.get("escalation_path", ["leadership"])
            ).lower()

        elif wf_status == "REJECTED":
            status = "ISSUED"
            outcome = "rejected_requires_review"

    return {
        "decision_id": decision_id,
        "status": status,
        "issued_at": issued_at,
        "approved_at": approved_at,
        "executed_at": executed_at,
        "outcome": outcome,
    }


def track_all_lifecycles(
    actions: list[dict],
    *,
    workflows: list[dict] | None = None,
    executions: list[dict] | None = None,
) -> list[dict]:
    """Track lifecycle for all actions."""
    wf_list = workflows or []
    ex_list = executions or []
    results = []
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        wf = wf_list[i] if i < len(wf_list) else None
        ex = ex_list[i] if i < len(ex_list) else None
        lc = track_decision_lifecycle(action, workflow=wf, execution=ex)
        results.append(lc)
    return results
