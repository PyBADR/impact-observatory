"""
Execution Trigger Layer — Phase 3 Engine 3

Bridges decisions → action execution by determining execution mode,
target system, and trigger readiness for each action.

Pure function. Never throws. Returns safe defaults.
"""
from __future__ import annotations


# ═══════════════════════════════════════════════════════════════════════════════
# System target mapping
# ═══════════════════════════════════════════════════════════════════════════════

_SECTOR_SYSTEM: dict[str, str] = {
    "banking": "banking_core",
    "insurance": "claims_management",
    "energy": "energy_trading_desk",
    "maritime": "port_operations",
    "fintech": "payment_gateway",
    "logistics": "logistics_platform",
    "infrastructure": "asset_management",
    "government": "regulatory_portal",
    "healthcare": "health_systems",
}

# Keywords → execution mode override
_AUTO_KEYWORDS: list[str] = [
    "activate", "trigger", "execute", "enforce", "deploy", "switch",
]
_API_KEYWORDS: list[str] = [
    "notify", "alert", "report", "escalate", "send", "transmit",
]


def _safe_str(v, fb: str = "") -> str:
    if v is None:
        return fb
    s = str(v).strip()
    return s if s else fb


def build_execution_trigger(
    action: dict,
    *,
    workflow: dict | None = None,
    action_type: str = "STRATEGIC",
) -> dict:
    """Build execution trigger for a single action.

    Args:
        action: The action dict.
        workflow: DecisionWorkflow from workflow_engine.
        action_type: IMMEDIATE | CONDITIONAL | STRATEGIC.

    Returns:
        {action_id, execution_mode, system_target, trigger_ready}
    """
    action_id = _safe_str(
        action.get("id") or action.get("action_id") or action.get("rank"),
        f"exec_{id(action)}",
    )
    label = _safe_str(action.get("label") or action.get("action"), "").lower()
    sector = _safe_str(action.get("sector"), "cross-sector").lower()

    # ── Determine execution mode ──
    if action_type == "STRATEGIC":
        execution_mode = "MANUAL"
    elif action_type == "IMMEDIATE":
        # Check for auto-executable keywords
        if any(kw in label for kw in _AUTO_KEYWORDS):
            execution_mode = "AUTO"
        elif any(kw in label for kw in _API_KEYWORDS):
            execution_mode = "API"
        else:
            execution_mode = "MANUAL"
    elif action_type == "CONDITIONAL":
        if any(kw in label for kw in _API_KEYWORDS):
            execution_mode = "API"
        else:
            execution_mode = "MANUAL"
    else:
        execution_mode = "MANUAL"

    # ── System target ──
    system_target = _SECTOR_SYSTEM.get(sector, "enterprise_risk_platform")

    # ── Trigger readiness ──
    trigger_ready = False

    wf_status = "PENDING"
    wf_approved = False
    if workflow:
        wf_status = _safe_str(workflow.get("status"), "PENDING")
        wf_approved = wf_status == "APPROVED"

    if action_type == "IMMEDIATE":
        # Immediate: ready if workflow approved OR no approval needed
        if not workflow:
            trigger_ready = True
        elif wf_approved:
            trigger_ready = True
        elif not workflow.get("approval_required", True):
            trigger_ready = True
    elif action_type == "CONDITIONAL":
        # Conditional: ready only if explicitly approved
        trigger_ready = wf_approved
    else:
        # Strategic: always manual, never auto-ready
        trigger_ready = False

    # Override: rejected workflows are never ready
    if wf_status == "REJECTED":
        trigger_ready = False

    return {
        "action_id": action_id,
        "execution_mode": execution_mode,
        "system_target": system_target,
        "trigger_ready": trigger_ready,
    }


def build_all_triggers(
    actions: list[dict],
    *,
    workflows: list[dict] | None = None,
    action_pathways: dict | None = None,
) -> list[dict]:
    """Build execution triggers for all actions.

    Uses action_pathways to determine action_type (IMMEDIATE/CONDITIONAL/STRATEGIC).
    """
    wf_list = workflows or []

    # Build action_id → type lookup from pathways
    type_lookup: dict[str, str] = {}
    if action_pathways and isinstance(action_pathways, dict):
        for atype in ("immediate", "conditional", "strategic"):
            for a in (action_pathways.get(atype) or []):
                if isinstance(a, dict):
                    aid = _safe_str(a.get("id") or a.get("action_id"), "")
                    if aid:
                        type_lookup[aid] = atype.upper()

    results = []
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        aid = _safe_str(
            action.get("id") or action.get("action_id") or action.get("rank"), ""
        )
        action_type = type_lookup.get(aid, "STRATEGIC")
        wf = wf_list[i] if i < len(wf_list) else None

        trigger = build_execution_trigger(
            action, workflow=wf, action_type=action_type,
        )
        results.append(trigger)
    return results
