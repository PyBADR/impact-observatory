"""
Executive Policy — dynamic executive classification with scenario-type awareness.

Absorbs classify_executive_status() from utils.py and extends it with:
  1. Scenario-type escalation rules (e.g., CYBER scenarios escalate faster)
  2. Breach-window compression (imminent breaches tighten thresholds)
  3. Loss-ratio sensitivity per scenario type

The original function in utils.py remains as a backwards-compatible alias.
This module is the authoritative implementation.

Pure function. No side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import (
    EXEC_CLASS_WEIGHTS,
    EXEC_BREACH_TIMING_MAX_HOURS,
    EXEC_LOSS_RATIO_CAP,
)
from src.policies.scenario_policy import PolicyContext
from src.utils import clamp, weighted_average


# ── Scenario-type escalation modifiers ──────────────────────────────────────
# These shift the composite score upward for scenario types that historically
# escalate faster. Applied as additive bonus AFTER weighted average.
_TYPE_ESCALATION_BONUS: dict[str, float] = {
    "CYBER":       0.08,   # Cyber events escalate fastest (speed of propagation)
    "LIQUIDITY":   0.05,   # Banking crises cascade through interbank channels
    "ENERGY":      0.03,   # Energy shocks have delayed but severe impact
    "MARITIME":    0.02,   # Maritime disruptions are slower to escalate
    "REGULATORY":  0.00,   # Regulatory events escalate through policy, not speed
}

# Breach-window compression: if breach is within this many hours,
# lower the SEVERE → CRITICAL threshold by this amount.
_BREACH_COMPRESSION_WINDOW_HOURS = 12.0
_BREACH_COMPRESSION_FACTOR = 0.05  # lowers CRITICAL threshold from 0.75 → 0.70


@dataclass(frozen=True, slots=True)
class ExecutivePolicyResult:
    """
    Executive classification result with full audit trail.

    status:          "STABLE" | "ELEVATED" | "SEVERE" | "CRITICAL"
    composite_score: Raw weighted composite (before type escalation).
    adjusted_score:  Score after scenario-type bonus.
    thresholds:      The threshold set used (may be compressed for imminent breaches).
    factors:         Individual normalized factor values for explainability.
    warnings:        Non-blocking advisories.
    """

    status: str
    composite_score: float
    adjusted_score: float
    thresholds: dict[str, float] = field(default_factory=dict)
    factors: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def evaluate_executive_policy(context: PolicyContext) -> ExecutivePolicyResult:
    """
    Evaluate executive classification from PolicyContext.

    Extends the original classify_executive_status() with:
      - Scenario-type escalation bonuses
      - Breach-window threshold compression
      - Full factor decomposition for audit

    Args:
        context: PolicyContext with severity, breach timing, loss ratio,
                 propagation speed, and scenario type.

    Returns:
        ExecutivePolicyResult with status, scores, thresholds, and factors.
    """
    warnings: list[str] = []

    # ── Normalize inputs to [0, 1] ──────────────────────────────────────────
    norm_severity = clamp(context.severity, 0.0, 1.0)

    if context.time_to_first_breach_hours is None:
        norm_breach_timing = 0.0
    else:
        norm_breach_timing = 1.0 - clamp(
            context.time_to_first_breach_hours / EXEC_BREACH_TIMING_MAX_HOURS,
            0.0,
            1.0,
        )

    norm_loss_ratio = clamp(context.loss_ratio / EXEC_LOSS_RATIO_CAP, 0.0, 1.0)
    norm_propagation_speed = clamp(context.propagation_speed, 0.0, 1.0)

    factors = {
        "severity": round(norm_severity, 4),
        "breach_timing": round(norm_breach_timing, 4),
        "loss_ratio": round(norm_loss_ratio, 4),
        "propagation_speed": round(norm_propagation_speed, 4),
    }

    # ── Weighted composite ──────────────────────────────────────────────────
    composite = weighted_average(
        values=[norm_severity, norm_breach_timing, norm_loss_ratio, norm_propagation_speed],
        weights=[
            EXEC_CLASS_WEIGHTS["severity"],
            EXEC_CLASS_WEIGHTS["breach_timing"],
            EXEC_CLASS_WEIGHTS["loss_ratio"],
            EXEC_CLASS_WEIGHTS["propagation_speed"],
        ],
    )

    # ── Scenario-type escalation bonus ──────────────────────────────────────
    type_bonus = _TYPE_ESCALATION_BONUS.get(context.scenario_type, 0.0)
    adjusted = composite + type_bonus
    if type_bonus > 0:
        warnings.append(
            f"Scenario type '{context.scenario_type}' adds +{type_bonus:.2f} "
            f"escalation bonus"
        )

    # ── Breach-window threshold compression ─────────────────────────────────
    thresholds = {
        "STABLE": 0.0,
        "ELEVATED": 0.25,
        "SEVERE": 0.50,
        "CRITICAL": 0.75,
    }

    breach_hours = context.time_to_first_breach_hours
    if breach_hours is not None and breach_hours <= _BREACH_COMPRESSION_WINDOW_HOURS:
        thresholds["CRITICAL"] -= _BREACH_COMPRESSION_FACTOR
        warnings.append(
            f"Breach imminent ({breach_hours:.1f}h) — CRITICAL threshold "
            f"compressed to {thresholds['CRITICAL']:.2f}"
        )

    # ── Classify ────────────────────────────────────────────────────────────
    if adjusted >= thresholds["CRITICAL"]:
        status = "CRITICAL"
    elif adjusted >= thresholds["SEVERE"]:
        status = "SEVERE"
    elif adjusted >= thresholds["ELEVATED"]:
        status = "ELEVATED"
    else:
        status = "STABLE"

    return ExecutivePolicyResult(
        status=status,
        composite_score=round(composite, 4),
        adjusted_score=round(adjusted, 4),
        thresholds=thresholds,
        factors=factors,
        warnings=warnings,
    )


def classify_executive_status_v2(
    severity: float,
    time_to_first_breach_hours: float | None,
    loss_ratio: float,
    propagation_speed: float,
    scenario_type: str = "",
) -> str:
    """
    Drop-in replacement for utils.classify_executive_status() with scenario-type awareness.

    Returns just the status string for backwards compatibility.
    Use evaluate_executive_policy() for full audit result.
    """
    ctx = PolicyContext(
        scenario_id="",
        scenario_type=scenario_type,
        severity=severity,
        time_to_first_breach_hours=time_to_first_breach_hours,
        loss_ratio=loss_ratio,
        propagation_speed=propagation_speed,
    )
    result = evaluate_executive_policy(ctx)
    return result.status
