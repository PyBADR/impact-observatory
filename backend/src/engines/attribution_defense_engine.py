"""
Phase 5 — Attribution Defensibility Model

Makes value attribution auditable and explainable.
Generates human-readable explanations for why value was attributed
at a given confidence level, with external factor disclosure.

Layer ownership: Governance Layer (Stage 35)
Data flow: Value Attribution + Context → Attribution Defense
"""
from __future__ import annotations


# ── External Factor Detection ─────────────────────────────────────────

_VOLATILITY_SCENARIOS = {
    "energy_market_volatility_shock",
    "saudi_oil_shock",
    "qatar_lng_disruption",
}

_GEOPOLITICAL_SCENARIOS = {
    "iran_regional_escalation",
    "hormuz_chokepoint_disruption",
    "hormuz_full_closure",
    "red_sea_trade_corridor_instability",
}

_SYSTEMIC_SCENARIOS = {
    "uae_banking_crisis",
    "regional_liquidity_stress_event",
    "financial_infrastructure_cyber_disruption",
}


def _detect_external_factors(
    scenario_id: str,
    severity: float,
    total_actions: int,
) -> list[str]:
    """Detect external factors that could influence value attribution."""
    factors = []

    if scenario_id in _VOLATILITY_SCENARIOS:
        factors.append("energy market volatility")
    if scenario_id in _GEOPOLITICAL_SCENARIOS:
        factors.append("geopolitical instability")
    if scenario_id in _SYSTEMIC_SCENARIOS:
        factors.append("systemic contagion effects")
    if severity >= 0.80:
        factors.append("extreme severity conditions")
    if total_actions > 5:
        factors.append("multi-action interaction effects")

    return factors


def _compute_confidence_band(
    attribution_confidence: float,
    external_factors_count: int,
    data_completeness: float,
) -> float:
    """Compute adjusted confidence band accounting for external factors.

    Lower confidence when many external factors or low data completeness.
    """
    base = attribution_confidence
    # Each external factor reduces confidence by 5%
    factor_penalty = external_factors_count * 0.05
    # Low data completeness further penalizes
    completeness_penalty = max(0, (0.70 - data_completeness) * 0.2)
    adjusted = max(0.10, min(1.0, base - factor_penalty - completeness_penalty))
    return round(adjusted, 3)


def _determine_attribution_type(
    original_type: str,
    external_factors_count: int,
    total_actions: int,
) -> str:
    """Re-evaluate attribution type considering external factors.

    If multiple external drivers, downgrade from DIRECT → ASSISTED.
    Never upgrade — only maintain or downgrade.
    """
    if original_type == "DIRECT" and (external_factors_count >= 2 or total_actions > 3):
        return "ASSISTED"
    if original_type == "PARTIAL" and external_factors_count >= 3:
        return "LOW_CONFIDENCE"
    # Map DIRECT → DIRECT, PARTIAL → PARTIAL or ASSISTED
    if original_type == "DIRECT":
        return "DIRECT"
    if original_type == "PARTIAL":
        return "ASSISTED" if external_factors_count >= 1 else "PARTIAL"
    return "LOW_CONFIDENCE"


def _generate_explanation(
    decision_label: str,
    attribution_type: str,
    confidence_band: float,
    external_factors: list[str],
    value_created: float,
) -> str:
    """Generate human-readable attribution explanation."""
    value_desc = f"${abs(value_created):,.0f}" if abs(value_created) >= 1000 else f"${value_created:.0f}"
    direction = "created" if value_created >= 0 else "lost"

    if attribution_type == "DIRECT":
        base = f"Value of {value_desc} {direction} is directly attributable to '{decision_label}' with high confidence ({confidence_band:.0%})."
    elif attribution_type == "ASSISTED":
        base = f"Value of {value_desc} {direction} is partially attributable to '{decision_label}' ({confidence_band:.0%} confidence). Multiple contributing factors detected."
    else:
        base = f"Value of {value_desc} {direction} has low-confidence attribution to '{decision_label}' ({confidence_band:.0%}). Insufficient data for definitive attribution."

    if external_factors:
        factors_str = ", ".join(external_factors)
        base += f" External factors influencing outcome: {factors_str}."

    return base


def build_attribution_defense(
    value_attribution: dict,
    *,
    action: dict | None = None,
    scenario_id: str = "",
    severity: float = 0.5,
    total_actions: int = 1,
    data_completeness: float = 0.70,
) -> dict:
    """Build attribution defensibility model for a single decision.

    Returns a human-readable, auditable explanation of value attribution.
    """
    decision_id = value_attribution.get("decision_id", "")
    original_type = value_attribution.get("attribution_type", "LOW_CONFIDENCE")
    attribution_confidence = value_attribution.get("attribution_confidence", 0.5)
    value_created = value_attribution.get("value_created", 0)
    decision_label = (action or {}).get(
        "label",
        (action or {}).get("action", (action or {}).get("action_en", decision_id)),
    )

    external_factors = _detect_external_factors(scenario_id, severity, total_actions)
    confidence_band = _compute_confidence_band(
        attribution_confidence, len(external_factors), data_completeness
    )
    attribution_type = _determine_attribution_type(
        original_type, len(external_factors), total_actions
    )
    explanation = _generate_explanation(
        decision_label, attribution_type, confidence_band, external_factors, value_created
    )

    return {
        "decision_id": decision_id,
        "attribution_type": attribution_type,
        "confidence_band": confidence_band,
        "external_factors": external_factors,
        "explanation": explanation,
        "original_attribution_type": original_type,
        "original_confidence": attribution_confidence,
    }


def build_all_attribution_defenses(
    value_attributions: list[dict],
    *,
    actions: list[dict] | None = None,
    scenario_id: str = "",
    severity: float = 0.5,
    data_completeness: float = 0.70,
) -> list[dict]:
    """Build attribution defensibility for all decisions."""
    _actions = actions or []
    total_actions = len(_actions)
    results = []

    for va in value_attributions:
        did = va.get("decision_id", "")
        action = None
        for a in _actions:
            if a.get("id", a.get("action_id", "")) == did:
                action = a
                break

        results.append(build_attribution_defense(
            va,
            action=action,
            scenario_id=scenario_id,
            severity=severity,
            total_actions=total_actions,
            data_completeness=data_completeness,
        ))

    return results
