"""Pilot Scope Definition Engine — Phase 6, Stage 37.

Narrows the system into a deployable slice by defining which scenarios,
decision types, and ownership roles are in-scope for the pilot.

Only scoped scenarios are allowed. Out-of-scope runs are rejected.
Execution mode constrains behavior: SHADOW (observe only), ADVISORY
(recommend but don't act), or CONTROLLED (limited real execution).
"""

from __future__ import annotations

from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════════════════════════
# Default pilot scope — banking / liquidity management
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_PILOT_SCOPE = {
    "sector": "banking",
    "decision_type": "liquidity_management",
    "scenarios": [
        "regional_liquidity_stress_event",
        "uae_banking_crisis",
    ],
    "decision_owners": ["TREASURY", "CRO"],
    "approval_flow": ["TREASURY", "CRO"],
    "execution_mode": "SHADOW",
}


def get_pilot_scope() -> dict:
    """Return the active pilot scope configuration."""
    return {**DEFAULT_PILOT_SCOPE}


def validate_pilot_scope(scenario_id: str, *, scope: dict | None = None) -> dict:
    """Check whether a scenario falls within the active pilot scope.

    Returns:
        {
            "in_scope": bool,
            "scenario_id": str,
            "scope_sector": str,
            "execution_mode": str,
            "reason": str,
            "validated_at": str (ISO 8601),
        }
    """
    active = scope or get_pilot_scope()
    allowed_scenarios = active.get("scenarios", [])
    in_scope = scenario_id in allowed_scenarios

    return {
        "in_scope": in_scope,
        "scenario_id": scenario_id,
        "scope_sector": active.get("sector", ""),
        "execution_mode": active.get("execution_mode", "SHADOW"),
        "decision_owners": active.get("decision_owners", []),
        "approval_flow": active.get("approval_flow", []),
        "reason": (
            f"Scenario '{scenario_id}' is within pilot scope ({active.get('sector', '')} / {active.get('decision_type', '')})"
            if in_scope
            else f"Scenario '{scenario_id}' is outside pilot scope. Allowed: {allowed_scenarios}"
        ),
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
