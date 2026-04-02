"""Auto-trigger underwriting review based on risk thresholds.
Evaluates portfolio and scenario metrics to determine watch level and recommendations.
"""

WATCH_THRESHOLDS = {
    "exposure_pct": 0.15,  # 15% of total insured
    "claims_surge_multiplier": 2.0,
    "risk_score": 0.7,
    "concentration_pct": 0.30,  # 30% concentration threshold
    "duration_days": 14,
}


def evaluate_underwriting_watch(
    portfolio_exposure: float,
    total_insured: float,
    claims_surge_mult: float,
    risk_score: float,
    concentration: float,
) -> dict:
    """
    Evaluate underwriting watch level based on multiple risk triggers.

    Args:
        portfolio_exposure: Total portfolio exposure value
        total_insured: Total insured amount
        claims_surge_mult: Claims surge multiplier
        risk_score: Risk score (0.0 to 1.0)
        concentration: Concentration ratio (0.0 to 1.0)

    Returns:
        Dictionary with:
        - watch_level: "critical", "elevated", or "normal"
        - triggers: List of triggered thresholds
        - trigger_count: Number of triggers
        - recommendation: Action recommendation
    """
    triggers = []

    # Check exposure breach
    if total_insured > 0:
        exposure_ratio = portfolio_exposure / total_insured
        if exposure_ratio > WATCH_THRESHOLDS["exposure_pct"]:
            triggers.append(
                {
                    "trigger": "exposure_breach",
                    "value": exposure_ratio,
                    "threshold": WATCH_THRESHOLDS["exposure_pct"],
                }
            )

    # Check claims surge multiplier
    if claims_surge_mult > WATCH_THRESHOLDS["claims_surge_multiplier"]:
        triggers.append(
            {
                "trigger": "claims_surge",
                "value": claims_surge_mult,
                "threshold": WATCH_THRESHOLDS["claims_surge_multiplier"],
            }
        )

    # Check risk score
    if risk_score > WATCH_THRESHOLDS["risk_score"]:
        triggers.append(
            {
                "trigger": "risk_score",
                "value": risk_score,
                "threshold": WATCH_THRESHOLDS["risk_score"],
            }
        )

    # Check concentration
    if concentration > WATCH_THRESHOLDS["concentration_pct"]:
        triggers.append(
            {
                "trigger": "concentration",
                "value": concentration,
                "threshold": WATCH_THRESHOLDS["concentration_pct"],
            }
        )

    # Determine watch level
    trigger_count = len(triggers)
    if trigger_count >= 3:
        watch_level = "critical"
        recommendation = "Immediate underwriting review required"
    elif trigger_count >= 1:
        watch_level = "elevated"
        recommendation = "Enhanced monitoring recommended"
    else:
        watch_level = "normal"
        recommendation = "Standard monitoring"

    return {
        "watch_level": watch_level,
        "triggers": triggers,
        "trigger_count": trigger_count,
        "recommendation": recommendation,
    }
