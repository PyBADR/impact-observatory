"""
Decision Ownership Layer — Phase 3 Engine 1

Assigns every decision to a real organizational role based on
scenario domain, action sector, and risk characteristics.

Pure function. Never throws. Returns safe defaults.
Constants come from config.py.
"""
from __future__ import annotations

from src import config


# ═══════════════════════════════════════════════════════════════════════════════
# Role assignment rules — keyword → role mapping
# ═══════════════════════════════════════════════════════════════════════════════

# Sector → default owner role
_SECTOR_ROLE: dict[str, str] = {
    "energy": "COO",
    "maritime": "COO",
    "banking": "TREASURY",
    "insurance": "CRO",
    "fintech": "CRO",
    "logistics": "COO",
    "infrastructure": "COO",
    "government": "REGULATOR",
    "healthcare": "COO",
}

# Scenario domain → override role
_DOMAIN_ROLE: dict[str, str] = {
    "geopolitical": "CRO",
    "financial": "CFO",
    "operational": "COO",
    "regulatory": "REGULATOR",
    "cyber": "CRO",
    "environmental": "COO",
}

# Role → organization unit
_ROLE_ORG_UNIT: dict[str, str] = {
    "CRO": "Enterprise Risk Management",
    "CFO": "Finance & Treasury",
    "COO": "Operations",
    "TREASURY": "Treasury & Liquidity",
    "RISK": "Risk Analytics",
    "REGULATOR": "Regulatory Affairs",
}

# Role → default execution channel
_ROLE_EXEC_CHANNEL: dict[str, str] = {
    "CRO": "Risk Operations Desk",
    "CFO": "Finance War Room",
    "COO": "Operations Command",
    "TREASURY": "Treasury Desk",
    "RISK": "Risk Analytics Hub",
    "REGULATOR": "Regulatory Liaison",
}

# Action-label keywords that force specific roles
_KEYWORD_ROLE: list[tuple[list[str], str]] = [
    (["liquidity", "reserve", "capital adequacy", "lcr", "car"], "TREASURY"),
    (["regulatory", "compliance", "regulator", "central bank", "CBUAE", "SAMA"], "REGULATOR"),
    (["reinsurance", "claims", "solvency", "underwriting", "IFRS"], "CRO"),
    (["budget", "fiscal", "revenue", "cost", "dividend"], "CFO"),
    (["systemic", "contagion", "counterparty", "stress test"], "CRO"),
    (["port closure", "port operation", "shipping", "logistics", "supply chain", "cargo"], "COO"),
    (["cyber", "security", "breach", "infrastructure"], "CRO"),
]


def _safe_str(v, fallback: str = "") -> str:
    if v is None:
        return fallback
    s = str(v).strip()
    return s if s else fallback


def assign_decision_owner(
    decision: dict,
    *,
    scenario_id: str = "",
    scenario_domain: str = "",
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> dict:
    """Assign ownership to a single decision/action.

    Returns:
      {decision_id, owner_role, organization_unit, execution_channel}
    """
    decision_id = _safe_str(
        decision.get("id") or decision.get("action_id") or decision.get("rank"),
        f"decision_{id(decision)}",
    )
    label = _safe_str(decision.get("label") or decision.get("action"), "").lower()
    sector = _safe_str(decision.get("sector"), "cross-sector").lower()

    # Step 1: Start with sector-based default
    role = _SECTOR_ROLE.get(sector, "CRO")

    # Step 2: Keyword override (most specific)
    for keywords, keyword_role in _KEYWORD_ROLE:
        if any(kw in label for kw in keywords):
            role = keyword_role
            break

    # Step 3: Domain override (if scenario domain strongly implies a role)
    if scenario_domain:
        domain_role = _DOMAIN_ROLE.get(scenario_domain.lower())
        if domain_role:
            # Only override if no keyword match found, or if risk is SEVERE
            if risk_level in ("HIGH", "SEVERE"):
                role = domain_role

    # Step 4: Systemic risk always goes to CRO
    if risk_level == "SEVERE" and severity >= 0.85:
        role = "CRO"

    # Step 5: Regulatory scenarios override to REGULATOR
    if "regulatory" in scenario_id.lower() or "compliance" in scenario_id.lower():
        if role not in ("CRO", "REGULATOR"):
            role = "REGULATOR"

    return {
        "decision_id": decision_id,
        "owner_role": role,
        "organization_unit": _ROLE_ORG_UNIT.get(role, "Enterprise Risk Management"),
        "execution_channel": _ROLE_EXEC_CHANNEL.get(role, "Risk Operations Desk"),
    }


def assign_all_owners(
    actions: list[dict],
    *,
    scenario_id: str = "",
    scenario_domain: str = "",
    risk_level: str = "MODERATE",
    severity: float = 0.5,
) -> list[dict]:
    """Assign ownership to all actions.

    Returns list of DecisionOwnership dicts.
    """
    results = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        ownership = assign_decision_owner(
            action,
            scenario_id=scenario_id,
            scenario_domain=scenario_domain,
            risk_level=risk_level,
            severity=severity,
        )
        results.append(ownership)
    return results
