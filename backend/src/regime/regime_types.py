"""
Regime Types — canonical system-state definitions for Decision Intelligence.

Five regimes, ordered by severity. Each regime:
  - Has a decision-relevance description (why it matters)
  - Modifies propagation behavior (transfer amplifier, delay compression)
  - Specifies which decisions it should influence
  - Defines persistence characteristics (stickiness)

These are NOT market regimes. They are operational system-state classifications
that serve the decision pipeline.
"""
from __future__ import annotations

from typing import Literal


# ── Canonical regime types (ordered by severity) ────────────────────────────

RegimeType = Literal[
    "STABLE",
    "ELEVATED_STRESS",
    "LIQUIDITY_STRESS",
    "SYSTEMIC_STRESS",
    "CRISIS_ESCALATION",
]

# All valid regime types as a tuple for iteration
ALL_REGIMES: tuple[RegimeType, ...] = (
    "STABLE",
    "ELEVATED_STRESS",
    "LIQUIDITY_STRESS",
    "SYSTEMIC_STRESS",
    "CRISIS_ESCALATION",
)


# ── Regime definitions with decision-relevance mapping ──────────────────────

REGIME_DEFINITIONS: dict[RegimeType, dict] = {
    "STABLE": {
        "severity_range": (0.0, 0.20),
        "label": "Stable Operations",
        "label_ar": "عمليات مستقرة",
        "description": "System operating within normal parameters. No elevated risk.",
        "decision_relevance": "Monitoring mode only. No escalation required.",
        "affected_decisions": [],
        "propagation_amplifier": 1.0,    # no amplification
        "delay_compression": 1.0,        # no compression
        "failure_threshold_shift": 0.0,  # no shift
        "persistence": 0.90,             # high stickiness — stays stable
    },
    "ELEVATED_STRESS": {
        "severity_range": (0.20, 0.40),
        "label": "Elevated Stress",
        "label_ar": "ضغط مرتفع",
        "description": "One or more sectors showing above-normal stress. Watchlist activated.",
        "decision_relevance": "Preparatory decisions should be staged. Monitoring cadence increases.",
        "affected_decisions": ["MONITOR", "STAGE_RESERVES"],
        "propagation_amplifier": 1.10,   # 10% faster propagation
        "delay_compression": 0.90,       # 10% faster transmission
        "failure_threshold_shift": -0.03, # thresholds tighten slightly
        "persistence": 0.75,             # moderate stickiness
    },
    "LIQUIDITY_STRESS": {
        "severity_range": (0.40, 0.60),
        "label": "Liquidity Stress",
        "label_ar": "ضغط السيولة",
        "description": "Banking/payment systems under liquidity pressure. Interbank channels strained.",
        "decision_relevance": "Liquidity actions become urgent. Central bank intervention likely needed.",
        "affected_decisions": ["EMERGENCY_LIQUIDITY", "REPO_LIMIT_INCREASE", "RESERVE_REQUIREMENT_CUT"],
        "propagation_amplifier": 1.25,   # 25% faster in banking channels
        "delay_compression": 0.75,       # 25% faster transmission
        "failure_threshold_shift": -0.08, # thresholds compress significantly
        "persistence": 0.65,             # moderate — can escalate or recover
    },
    "SYSTEMIC_STRESS": {
        "severity_range": (0.60, 0.80),
        "label": "Systemic Stress",
        "label_ar": "ضغط نظامي",
        "description": "Multiple sectors under simultaneous stress. Cross-sector contagion active.",
        "decision_relevance": "Multi-sector response required. Regulatory coordination mandatory.",
        "affected_decisions": [
            "EMERGENCY_LIQUIDITY", "REGULATORY_FORBEARANCE", "CAPITAL_CONTROLS",
            "CROSS_BORDER_COORDINATION", "PAYMENT_CONTINGENCY",
        ],
        "propagation_amplifier": 1.50,   # 50% amplification across all channels
        "delay_compression": 0.60,       # 40% faster transmission
        "failure_threshold_shift": -0.12, # thresholds compress aggressively
        "persistence": 0.55,             # unstable — tends to escalate
    },
    "CRISIS_ESCALATION": {
        "severity_range": (0.80, 1.00),
        "label": "Crisis Escalation",
        "label_ar": "تصعيد أزمة",
        "description": "Active system failure. Multiple nodes breached or failing. Emergency protocols required.",
        "decision_relevance": "All decisions become IMMEDIATE. Escalation is mandatory. Human-in-the-loop approval required.",
        "affected_decisions": [
            "EMERGENCY_LIQUIDITY", "PAYMENT_CONTINGENCY", "CYBER_DEFENSE",
            "PORT_REROUTING", "OIL_RESERVES_RELEASE", "CAPITAL_CONTROLS",
            "REGULATORY_FORBEARANCE", "CROSS_BORDER_COORDINATION",
        ],
        "propagation_amplifier": 2.00,   # 2x propagation speed
        "delay_compression": 0.40,       # 60% faster transmission
        "failure_threshold_shift": -0.20, # thresholds collapse
        "persistence": 0.80,             # very sticky — hard to recover from
    },
}


# ── Transition probability matrix ───────────────────────────────────────────
# TRANSITION_MATRIX[current][next] = base probability of transitioning
# These are base rates; actual transition probability is modified by:
#   - current stress level relative to regime boundary
#   - rate of stress change (acceleration)
#   - number of sectors under simultaneous stress

TRANSITION_MATRIX: dict[RegimeType, dict[RegimeType, float]] = {
    "STABLE": {
        "STABLE": 0.85,
        "ELEVATED_STRESS": 0.12,
        "LIQUIDITY_STRESS": 0.02,
        "SYSTEMIC_STRESS": 0.005,
        "CRISIS_ESCALATION": 0.005,
    },
    "ELEVATED_STRESS": {
        "STABLE": 0.25,
        "ELEVATED_STRESS": 0.50,
        "LIQUIDITY_STRESS": 0.15,
        "SYSTEMIC_STRESS": 0.08,
        "CRISIS_ESCALATION": 0.02,
    },
    "LIQUIDITY_STRESS": {
        "STABLE": 0.05,
        "ELEVATED_STRESS": 0.20,
        "LIQUIDITY_STRESS": 0.45,
        "SYSTEMIC_STRESS": 0.22,
        "CRISIS_ESCALATION": 0.08,
    },
    "SYSTEMIC_STRESS": {
        "STABLE": 0.01,
        "ELEVATED_STRESS": 0.05,
        "LIQUIDITY_STRESS": 0.15,
        "SYSTEMIC_STRESS": 0.44,
        "CRISIS_ESCALATION": 0.35,
    },
    "CRISIS_ESCALATION": {
        "STABLE": 0.00,
        "ELEVATED_STRESS": 0.02,
        "LIQUIDITY_STRESS": 0.08,
        "SYSTEMIC_STRESS": 0.25,
        "CRISIS_ESCALATION": 0.65,
    },
}
