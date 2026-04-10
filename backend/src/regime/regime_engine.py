"""
Regime Engine — classifies system state from pipeline signals.

Pure function. No side effects. No external dependencies beyond config.

Input signals:
  - Banking sector stress (aggregate_stress, lcr_ratio, car_ratio)
  - Insurance sector stress (aggregate_stress, combined_ratio)
  - Fintech sector stress (aggregate_stress, payment_volume_impact)
  - Event severity (0-1)
  - Propagation depth (number of hops)
  - System stress score (unified_risk_score)
  - Scenario type (MARITIME/ENERGY/LIQUIDITY/CYBER/REGULATORY)

Output:
  RegimeState with classification, confidence, transition risk, and trigger flags.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from src.regime.regime_types import (
    RegimeType,
    ALL_REGIMES,
    REGIME_DEFINITIONS,
    TRANSITION_MATRIX,
)
from src.utils import clamp


# ── Regime Input Schema ─────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RegimeInputs:
    """
    Signals that feed regime classification.

    Constructed from pipeline result. Every field has a safe default
    so the engine never crashes on missing data.
    """

    # Macro signals
    event_severity: float = 0.0       # 0-1 scenario severity
    system_stress: float = 0.0        # unified_risk_score (0-1)
    scenario_type: str = ""           # MARITIME/ENERGY/LIQUIDITY/CYBER/REGULATORY

    # Liquidity signals
    banking_stress: float = 0.0       # banking aggregate_stress (0-1)
    lcr_ratio: float = 1.20           # liquidity coverage ratio (>1.0 = compliant)
    car_ratio: float = 0.12           # capital adequacy ratio (>0.105 = compliant)

    # Volatility / stress signals
    insurance_stress: float = 0.0     # insurance aggregate_stress (0-1)
    combined_ratio: float = 0.95      # insurance combined ratio (<1.10 = solvent)
    fintech_stress: float = 0.0       # fintech aggregate_stress (0-1)

    # Payment / settlement stress
    payment_volume_impact_pct: float = 0.0  # % reduction in payment throughput
    api_availability_pct: float = 100.0     # fintech API uptime

    # Propagation indicators
    propagation_depth: int = 0        # hops from origin
    nodes_affected: int = 0           # count of impacted nodes
    bottleneck_count: int = 0         # critical bottlenecks identified

    # Sector pressure (count of sectors with stress > 0.35)
    sectors_under_pressure: int = 0


# ── Regime Output Contract ──────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RegimeState:
    """
    Output of regime classification. Single source of truth for system state.

    Consumed by:
      - Graph/Propagation engine (modifiers)
      - Decision Trigger engine (trigger conditions)
      - Map Payload engine (overlay coloring)
      - Executive Dashboard (status display)
    """

    regime_id: RegimeType
    regime_label: str
    regime_label_ar: str
    confidence: float                         # 0-1 classification confidence
    transition_risk: float                    # 0-1 probability of moving to a worse regime
    persistence_score: float                  # 0-1 likelihood of staying in current regime
    stress_level: float                       # 0-1 aggregate stress driving this classification
    trigger_flags: list[str] = field(default_factory=list)
    reasoning_summary: str = ""
    reasoning_summary_ar: str = ""

    # Transition forecast
    likely_next_regime: RegimeType = "STABLE"
    transition_probability: float = 0.0

    # Graph modifiers (consumed by regime_graph_adapter)
    propagation_amplifier: float = 1.0
    delay_compression: float = 1.0
    failure_threshold_shift: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime_id": self.regime_id,
            "regime_label": self.regime_label,
            "regime_label_ar": self.regime_label_ar,
            "confidence": round(self.confidence, 4),
            "transition_risk": round(self.transition_risk, 4),
            "persistence_score": round(self.persistence_score, 4),
            "stress_level": round(self.stress_level, 4),
            "trigger_flags": self.trigger_flags,
            "reasoning_summary": self.reasoning_summary,
            "reasoning_summary_ar": self.reasoning_summary_ar,
            "likely_next_regime": self.likely_next_regime,
            "transition_probability": round(self.transition_probability, 4),
            "propagation_amplifier": round(self.propagation_amplifier, 4),
            "delay_compression": round(self.delay_compression, 4),
            "failure_threshold_shift": round(self.failure_threshold_shift, 4),
        }


# ── Classification Engine ───────────────────────────────────────────────────

# Signal weights for composite stress computation
_SIGNAL_WEIGHTS = {
    "event_severity":    0.20,
    "system_stress":     0.20,
    "banking_stress":    0.18,
    "insurance_stress":  0.10,
    "fintech_stress":    0.08,
    "lcr_breach":        0.08,   # binary: 1 if LCR < 1.0
    "car_breach":        0.06,   # binary: 1 if CAR < 0.105
    "combined_breach":   0.05,   # binary: 1 if combined_ratio > 1.10
    "payment_impact":    0.05,   # payment_volume_impact / 100
}


def _compute_composite_stress(inputs: RegimeInputs) -> tuple[float, list[str]]:
    """
    Compute weighted composite stress and collect trigger flags.

    Returns (stress, flags) where stress ∈ [0, 1].
    """
    flags: list[str] = []

    # Normalize all signals to [0, 1]
    signals: dict[str, float] = {
        "event_severity": clamp(inputs.event_severity, 0, 1),
        "system_stress": clamp(inputs.system_stress, 0, 1),
        "banking_stress": clamp(inputs.banking_stress, 0, 1),
        "insurance_stress": clamp(inputs.insurance_stress, 0, 1),
        "fintech_stress": clamp(inputs.fintech_stress, 0, 1),
        "lcr_breach": 1.0 if inputs.lcr_ratio < 1.0 else 0.0,
        "car_breach": 1.0 if inputs.car_ratio < 0.105 else 0.0,
        "combined_breach": 1.0 if inputs.combined_ratio > 1.10 else 0.0,
        "payment_impact": clamp(inputs.payment_volume_impact_pct / 100.0, 0, 1),
    }

    # Collect trigger flags
    if signals["lcr_breach"]:
        flags.append("LCR_BREACH")
    if signals["car_breach"]:
        flags.append("CAR_BREACH")
    if signals["combined_breach"]:
        flags.append("INSURANCE_COMBINED_RATIO_BREACH")
    if inputs.banking_stress >= 0.50:
        flags.append("BANKING_HIGH_STRESS")
    if inputs.fintech_stress >= 0.50:
        flags.append("FINTECH_HIGH_STRESS")
    if inputs.payment_volume_impact_pct >= 30:
        flags.append("PAYMENT_DISRUPTION")
    if inputs.bottleneck_count >= 3:
        flags.append("MULTI_BOTTLENECK")
    if inputs.sectors_under_pressure >= 3:
        flags.append("MULTI_SECTOR_PRESSURE")
    if inputs.propagation_depth >= 10:
        flags.append("DEEP_PROPAGATION")

    # Weighted sum
    composite = sum(
        signals[k] * _SIGNAL_WEIGHTS[k]
        for k in _SIGNAL_WEIGHTS
    )

    # Sector pressure bonus: multi-sector stress amplifies regime
    if inputs.sectors_under_pressure >= 3:
        composite = min(1.0, composite * 1.15)
    if inputs.sectors_under_pressure >= 4:
        composite = min(1.0, composite * 1.10)

    return clamp(composite, 0, 1), flags


def _classify_from_stress(stress: float) -> RegimeType:
    """Map composite stress to regime type using REGIME_DEFINITIONS thresholds."""
    # Walk from most severe to least
    for regime in reversed(ALL_REGIMES):
        lo, _hi = REGIME_DEFINITIONS[regime]["severity_range"]
        if stress >= lo:
            return regime
    return "STABLE"


def _compute_confidence(stress: float, regime: RegimeType) -> float:
    """
    Confidence that the classification is correct.

    Higher when stress is deep inside the regime band (not near boundary).
    Lower when stress is near a transition boundary.
    """
    lo, hi = REGIME_DEFINITIONS[regime]["severity_range"]
    band_width = hi - lo
    if band_width <= 0:
        return 0.5
    center = (lo + hi) / 2.0
    distance_from_center = abs(stress - center)
    # Confidence = 1.0 at center, drops toward edges
    return clamp(1.0 - (distance_from_center / (band_width / 2.0)) * 0.4, 0.5, 1.0)


def _compute_transitions(
    current: RegimeType,
    stress: float,
) -> tuple[RegimeType, float, float]:
    """
    Compute transition forecast.

    Returns (likely_next, transition_probability, persistence).
    """
    row = TRANSITION_MATRIX[current]
    persistence = row[current]

    # Find most likely next regime (excluding current)
    likely_next = current
    max_prob = 0.0
    for target, base_prob in row.items():
        if target == current:
            continue
        # Adjust by proximity to regime boundary
        target_lo, _target_hi = REGIME_DEFINITIONS[target]["severity_range"]
        distance_to_target = abs(stress - target_lo)
        proximity_boost = max(0, 1.0 - distance_to_target * 2.0) * 0.15
        adjusted_prob = base_prob + proximity_boost
        if adjusted_prob > max_prob:
            max_prob = adjusted_prob
            likely_next = target

    # Transition risk = probability of moving to ANY worse regime
    transition_risk = 0.0
    current_idx = ALL_REGIMES.index(current)
    for target, prob in row.items():
        target_idx = ALL_REGIMES.index(target)
        if target_idx > current_idx:
            transition_risk += prob

    return likely_next, clamp(max_prob, 0, 1), clamp(transition_risk, 0, 1)


def _build_reasoning(
    regime: RegimeType,
    stress: float,
    flags: list[str],
    inputs: RegimeInputs,
) -> tuple[str, str]:
    """Build human-readable reasoning summary (EN + AR)."""
    defn = REGIME_DEFINITIONS[regime]

    if not flags:
        en = f"System classified as {defn['label']} (stress={stress:.2f}). No trigger flags."
        ar = f"تصنيف النظام: {defn['label_ar']} (ضغط={stress:.2f}). لا توجد إشارات تحذيرية."
    else:
        flag_str = ", ".join(flags[:4])
        en = (
            f"System classified as {defn['label']} (stress={stress:.2f}). "
            f"Active triggers: {flag_str}. "
            f"{defn['decision_relevance']}"
        )
        ar = (
            f"تصنيف النظام: {defn['label_ar']} (ضغط={stress:.2f}). "
            f"إشارات نشطة: {flag_str}. "
        )

    return en, ar


# ── Public API ──────────────────────────────────────────────────────────────

def build_regime_inputs(result: dict[str, Any]) -> RegimeInputs:
    """
    Factory: build RegimeInputs from a pipeline result dict.

    Extracts all signals from banking_stress, insurance_stress, fintech_stress,
    headline, propagation, and bottleneck data.
    """
    banking = result.get("banking_stress") or result.get("banking", {}) or {}
    insurance = result.get("insurance_stress") or result.get("insurance", {}) or {}
    fintech = result.get("fintech_stress") or result.get("fintech", {}) or {}
    headline = result.get("headline", {}) or {}

    # Count sectors under pressure (stress > 0.35)
    sector_stresses = [
        float(banking.get("aggregate_stress", 0) if isinstance(banking, dict) else 0),
        float(insurance.get("aggregate_stress", insurance.get("severity_index", 0)) if isinstance(insurance, dict) else 0),
        float(fintech.get("aggregate_stress", 0) if isinstance(fintech, dict) else 0),
    ]
    sectors_under_pressure = sum(1 for s in sector_stresses if s > 0.35)

    return RegimeInputs(
        event_severity=float(result.get("event_severity", result.get("severity", 0))),
        system_stress=float(result.get("unified_risk_score", result.get("system_stress_score", 0))),
        scenario_type=str(result.get("scenario_type", "")),
        banking_stress=sector_stresses[0],
        lcr_ratio=float(banking.get("lcr_ratio", 1.20) if isinstance(banking, dict) else 1.20),
        car_ratio=float(banking.get("car_ratio", 0.12) if isinstance(banking, dict) else 0.12),
        insurance_stress=sector_stresses[1],
        combined_ratio=float(insurance.get("combined_ratio", 0.95) if isinstance(insurance, dict) else 0.95),
        fintech_stress=sector_stresses[2],
        payment_volume_impact_pct=float(fintech.get("payment_volume_impact_pct", 0) if isinstance(fintech, dict) else 0),
        api_availability_pct=float(fintech.get("api_availability_pct", 100) if isinstance(fintech, dict) else 100),
        propagation_depth=int(headline.get("propagation_depth", len(result.get("propagation_chain", result.get("propagation", []))))),
        nodes_affected=int(headline.get("affected_entities", headline.get("total_nodes_impacted", 0))),
        bottleneck_count=len(result.get("bottlenecks", [])),
        sectors_under_pressure=sectors_under_pressure,
    )


def classify_regime(inputs: RegimeInputs) -> RegimeState:
    """
    Classify system regime from input signals.

    Pure function. No side effects. Returns full RegimeState.
    """
    stress, flags = _compute_composite_stress(inputs)
    regime = _classify_from_stress(stress)
    confidence = _compute_confidence(stress, regime)
    likely_next, transition_prob, transition_risk = _compute_transitions(regime, stress)
    defn = REGIME_DEFINITIONS[regime]
    reasoning_en, reasoning_ar = _build_reasoning(regime, stress, flags, inputs)

    return RegimeState(
        regime_id=regime,
        regime_label=defn["label"],
        regime_label_ar=defn["label_ar"],
        confidence=confidence,
        transition_risk=transition_risk,
        persistence_score=defn["persistence"],
        stress_level=stress,
        trigger_flags=flags,
        reasoning_summary=reasoning_en,
        reasoning_summary_ar=reasoning_ar,
        likely_next_regime=likely_next,
        transition_probability=transition_prob,
        propagation_amplifier=defn["propagation_amplifier"],
        delay_compression=defn["delay_compression"],
        failure_threshold_shift=defn["failure_threshold_shift"],
    )


def classify_regime_from_result(result: dict[str, Any]) -> RegimeState:
    """Convenience: classify regime directly from pipeline result dict."""
    inputs = build_regime_inputs(result)
    return classify_regime(inputs)
