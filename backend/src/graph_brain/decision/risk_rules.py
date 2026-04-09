"""Risk Business Rules — Deterministic classification and recommendation logic.

Uses the exact URS thresholds from config.py and the cross-sector dependency
map from risk_models.py. No LLM calls — pure deterministic rules.

Architecture Layer: Models (Layer 3)
Owner: Decision Layer
Consumers: RiskEngine

Key formulas (from config.py):
  URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropagationScore + g5*LossNorm
  Es  = w1*I + w2*D + w3*U + w4*G
"""

import math
from typing import Optional

from src.graph_brain.decision.risk_models import (
    RiskLevel,
    RiskFactor,
    RiskFactorSource,
)


# ═══════════════════════════════════════════════════════════════════════════════
# URS Thresholds — imported from config.py spec
# ═══════════════════════════════════════════════════════════════════════════════

URS_THRESHOLDS: dict[RiskLevel, tuple[float, float]] = {
    RiskLevel.NOMINAL:  (0.00, 0.20),
    RiskLevel.LOW:      (0.20, 0.35),
    RiskLevel.GUARDED:  (0.35, 0.50),
    RiskLevel.ELEVATED: (0.50, 0.65),
    RiskLevel.HIGH:     (0.65, 0.80),
    RiskLevel.SEVERE:   (0.80, 1.01),
}


def classify_risk_level(score: float) -> RiskLevel:
    """Map a [0.0, 1.0] risk score to a URS risk level.

    Uses the exact thresholds from config.py RISK_THRESHOLDS.
    """
    score = max(0.0, min(1.0, score))
    for level, (lo, hi) in URS_THRESHOLDS.items():
        if lo <= score < hi:
            return level
    return RiskLevel.SEVERE  # fallback for score == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Sector Sensitivity Coefficients — from config.py SECTOR_ALPHA
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_SENSITIVITY: dict[str, float] = {
    "energy":         0.28,
    "maritime":       0.18,
    "banking":        0.20,
    "insurance":      0.08,
    "fintech":        0.06,
    "logistics":      0.10,
    "infrastructure": 0.05,
    "government":     0.03,
    "healthcare":     0.02,
}

# Cross-sector dependency chains (from risk_models.py _CROSS_SECTOR_DEPS)
CROSS_SECTOR_DEPS: dict[str, list[str]] = {
    "energy":         ["banking", "maritime", "logistics", "fintech"],
    "maritime":       ["energy", "logistics", "banking"],
    "banking":        ["fintech", "insurance", "government"],
    "insurance":      ["banking", "fintech"],
    "fintech":        ["banking", "insurance"],
    "logistics":      ["maritime", "energy"],
    "infrastructure": ["energy", "banking"],
    "government":     ["banking", "fintech"],
    "healthcare":     ["banking", "logistics"],
}

# Vulnerability by hop distance (from config.py)
VULNERABILITY_BY_HOP: dict[int, float] = {
    0: 1.00,   # direct
    1: 0.70,   # first-hop
    2: 0.35,   # second-hop
}
VULNERABILITY_DEFAULT: float = 0.10


def get_vulnerability_weight(hop_distance: int) -> float:
    """Get vulnerability decay weight by graph hop distance."""
    return VULNERABILITY_BY_HOP.get(hop_distance, VULNERABILITY_DEFAULT)


def get_sector_sensitivity(sector: str) -> float:
    """Get sector sensitivity coefficient (alpha_j from config.py)."""
    return SECTOR_SENSITIVITY.get(sector.lower(), 0.05)


def get_dependent_sectors(sector: str) -> list[str]:
    """Get sectors that depend on a given sector."""
    return CROSS_SECTOR_DEPS.get(sector.lower(), [])


# ═══════════════════════════════════════════════════════════════════════════════
# Temporal Decay — signals lose relevance over time
# ═══════════════════════════════════════════════════════════════════════════════

def compute_temporal_decay(
    signal_age_hours: float,
    half_life_hours: float = 168.0,  # 7 days default
) -> float:
    """Exponential temporal decay: decay = 2^(-age/half_life).

    Args:
        signal_age_hours: Hours since signal was emitted
        half_life_hours: Half-life in hours (168 = 7 days)

    Returns:
        Decay factor [0.0, 1.0] — 1.0 means fresh, 0.0 means fully decayed
    """
    if signal_age_hours <= 0:
        return 1.0
    return math.pow(2.0, -signal_age_hours / half_life_hours)


# ═══════════════════════════════════════════════════════════════════════════════
# Composite Risk Score — matches URS formula structure
# ═══════════════════════════════════════════════════════════════════════════════

# Weights from config.py URS formula
URS_WEIGHTS = {
    "severity": 0.35,       # g1 — event severity
    "exposure": 0.10,       # g2 — peak sector exposure
    "stress": 0.15,         # g3 — peak stress index
    "propagation": 0.30,    # g4 — propagation score
    "loss": 0.10,           # g5 — normalized loss
}


def compute_composite_score(
    severity_component: float = 0.0,
    exposure_component: float = 0.0,
    stress_component: float = 0.0,
    propagation_component: float = 0.0,
    loss_component: float = 0.0,
) -> float:
    """Compute composite risk score using URS weights.

    URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropScore + g5*LossNorm

    All inputs should be [0.0, 1.0]. Output is clamped to [0.0, 1.0].
    """
    raw = (
        URS_WEIGHTS["severity"] * max(0.0, min(1.0, severity_component))
        + URS_WEIGHTS["exposure"] * max(0.0, min(1.0, exposure_component))
        + URS_WEIGHTS["stress"] * max(0.0, min(1.0, stress_component))
        + URS_WEIGHTS["propagation"] * max(0.0, min(1.0, propagation_component))
        + URS_WEIGHTS["loss"] * max(0.0, min(1.0, loss_component))
    )
    return max(0.0, min(1.0, raw))


# ═══════════════════════════════════════════════════════════════════════════════
# Recommendation Engine — context-aware, severity-driven
# ═══════════════════════════════════════════════════════════════════════════════

# Scenario-specific recommendation catalogs
SCENARIO_RECOMMENDATIONS: dict[str, list[str]] = {
    "hormuz": [
        "Activate Hormuz contingency pricing for marine cargo and energy LOBs",
        "Pre-position strategic petroleum reserve drawdown triggers",
        "Review alternative shipping route cost models (Cape of Good Hope)",
    ],
    "oil": [
        "Stress-test portfolio sensitivity to >$100/bbl Brent scenario",
        "Review energy sector counterparty credit exposure",
        "Update actuarial tables for business interruption coverage",
    ],
    "banking": [
        "Monitor interbank lending rate spreads for liquidity stress",
        "Review credit insurance sublimits for banking sector exposure",
        "Assess IFRS 9 expected credit loss model adequacy",
    ],
    "cyber": [
        "Review cyber insurance aggregation limits across tenant portfolios",
        "Map shared infrastructure dependencies (SWIFT, payment gateways)",
        "Assess systemic risk exclusion clause adequacy",
    ],
    "insurance": [
        "Monitor combined ratio trajectory against reinsurance treaty thresholds",
        "Review catastrophe bond trigger proximity",
        "Pre-position facultative reinsurance capacity for Q3 renewals",
    ],
    "maritime": [
        "Review marine cargo war risk premium adequacy",
        "Assess port congestion impact on hull & machinery claims pipeline",
        "Update supply chain business interruption exposure models",
    ],
}


def generate_recommendations(
    risk_level: RiskLevel,
    entity_type: str = "",
    exposed_sectors: Optional[list[str]] = None,
    active_scenarios: Optional[list[str]] = None,
) -> list[str]:
    """Generate context-aware recommendations based on risk level and context.

    Combines:
      1. Universal severity-based recommendations
      2. Sector-specific recommendations (from exposed_sectors)
      3. Scenario-specific recommendations (from active_scenarios)
    """
    recs: list[str] = []

    # Severity-based universals
    if risk_level in (RiskLevel.SEVERE, RiskLevel.HIGH):
        recs.extend([
            "Escalate to CRO for immediate review — risk score exceeds operational threshold",
            "Activate cross-sector contagion monitoring dashboard",
            "Review and reduce concentrated exposure positions across affected sectors",
            "Initiate regulatory reporting per IFRS 17 disclosure requirements",
        ])
    elif risk_level == RiskLevel.ELEVATED:
        recs.extend([
            "Schedule risk committee review within 48 hours",
            "Increase monitoring frequency for affected entities",
            "Review hedging adequacy for primary exposure channels",
        ])
    elif risk_level == RiskLevel.GUARDED:
        recs.extend([
            "Monitor risk trajectory — upgrade to elevated if score increases >5% within 24h",
            "Review pricing model assumptions for sensitivity to current risk drivers",
        ])
    elif risk_level == RiskLevel.LOW:
        recs.append("Continue routine monitoring — no immediate action required")
    else:
        recs.append("Risk within nominal operating parameters")

    # Sector-specific
    if exposed_sectors:
        for sector in exposed_sectors[:3]:
            sector_lower = sector.lower()
            for key, sector_recs in SCENARIO_RECOMMENDATIONS.items():
                if key in sector_lower:
                    recs.extend(sector_recs[:2])
                    break

    # Scenario-specific
    if active_scenarios:
        for scenario in active_scenarios[:3]:
            scenario_lower = scenario.lower()
            for key, scenario_recs in SCENARIO_RECOMMENDATIONS.items():
                if key in scenario_lower:
                    recs.extend(scenario_recs[:2])
                    break

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_recs: list[str] = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique_recs.append(r)

    return unique_recs[:10]  # cap at 10
