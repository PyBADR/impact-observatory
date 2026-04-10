"""
Validation Contracts — detect and flag suspect values in pipeline output.

Unlike the sanity guard (which clamps silently), this module:
  1. DETECTS violations against data contracts
  2. Returns structured ValidationFlag records
  3. Does NOT mutate the data — flagging only

Enforcement rules:
  V1. Percentages must be in [0, 100]
  V2. Hours must be in [0, scenario_window] (default 8760)
  V3. ROI ratio must be in [-50, 50] (realistic cap)
  V4. Cost and mitigation values must be ≥ 0
  V5. Scores must be in [0, 1]
  V6. Extreme ratios: flag if loss_avoided / cost > 100x
  V7. NaN / Infinity / None in numeric fields

Pure function. No side effects. No mutations.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationFlag:
    """
    A single validation violation.

    field:    Dot-path to the offending field (e.g., "banking_stress.aggregate_stress").
    issue:    Human-readable description of the violation.
    value:    The actual value found.
    rule:     Which validation rule was violated (V1-V7).
    severity: "warning" (suspicious but passable) or "error" (contract violation).
    """

    field: str
    issue: str
    value: Any = None
    rule: str = ""
    severity: str = "warning"  # "warning" | "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "issue": self.issue,
            "value": self.value,
            "rule": self.rule,
            "severity": self.severity,
        }


# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_bad_number(v: Any) -> bool:
    """True if value is NaN, Infinity, or not a number when it should be."""
    if v is None:
        return False  # None is valid (sentinel replacement)
    try:
        f = float(v)
        return math.isnan(f) or math.isinf(f)
    except (TypeError, ValueError):
        return True


def _check_range(
    flags: list[ValidationFlag],
    data: dict,
    field: str,
    lo: float,
    hi: float,
    rule: str,
    prefix: str = "",
) -> None:
    """Check if a field is within [lo, hi]. Adds flag if not."""
    v = data.get(field)
    if v is None:
        return
    full_field = f"{prefix}.{field}" if prefix else field

    if _is_bad_number(v):
        flags.append(ValidationFlag(
            field=full_field,
            issue=f"NaN/Infinity detected",
            value=v,
            rule="V7",
            severity="error",
        ))
        return

    fv = float(v)
    if fv < lo or fv > hi:
        flags.append(ValidationFlag(
            field=full_field,
            issue=f"Value {fv} outside allowed range [{lo}, {hi}]",
            value=fv,
            rule=rule,
            severity="error" if abs(fv - (lo + hi) / 2) > (hi - lo) else "warning",
        ))


def _check_non_negative(
    flags: list[ValidationFlag],
    data: dict,
    field: str,
    rule: str,
    prefix: str = "",
) -> None:
    """Check if a field is ≥ 0."""
    v = data.get(field)
    if v is None:
        return
    full_field = f"{prefix}.{field}" if prefix else field

    if _is_bad_number(v):
        flags.append(ValidationFlag(
            field=full_field, issue="NaN/Infinity detected",
            value=v, rule="V7", severity="error",
        ))
        return

    if float(v) < 0:
        flags.append(ValidationFlag(
            field=full_field, issue=f"Negative value {v} (expected ≥ 0)",
            value=v, rule=rule, severity="error",
        ))


# ── Main Validator ──────────────────────────────────────────────────────────

def validate_metrics(
    result: dict,
    scenario_window_hours: float = 8760.0,
) -> list[ValidationFlag]:
    """
    Validate a full run result dict against data contracts.

    Returns a list of ValidationFlag objects. Empty list = all clean.
    Does NOT mutate the input dict.

    Args:
        result:                 Run result dict from the pipeline.
        scenario_window_hours:  Maximum allowed hours for time-to-X fields.
    """
    flags: list[ValidationFlag] = []

    # ── V5: Score fields (0-1) ──────────────────────────────────────────────
    _check_range(flags, result, "unified_risk_score", 0.0, 1.0, "V5")
    _check_range(flags, result, "confidence_score", 0.0, 1.0, "V5")

    # ── Banking stress ──────────────────────────────────────────────────────
    banking = result.get("banking_stress") or result.get("banking", {})
    if banking and isinstance(banking, dict):
        _check_range(flags, banking, "aggregate_stress", 0.0, 1.0, "V5", "banking_stress")
        _check_range(
            flags, banking, "time_to_liquidity_breach_hours",
            0.0, scenario_window_hours, "V2", "banking_stress",
        )

    # ── Insurance stress ────────────────────────────────────────────────────
    insurance = result.get("insurance_stress") or result.get("insurance", {})
    if insurance and isinstance(insurance, dict):
        _check_range(flags, insurance, "severity_index", 0.0, 1.0, "V5", "insurance_stress")
        _check_range(flags, insurance, "aggregate_stress", 0.0, 1.0, "V5", "insurance_stress")
        _check_range(
            flags, insurance, "time_to_insolvency_hours",
            0.0, scenario_window_hours, "V2", "insurance_stress",
        )

    # ── Fintech stress ──────────────────────────────────────────────────────
    fintech = result.get("fintech_stress") or result.get("fintech", {})
    if fintech and isinstance(fintech, dict):
        _check_range(flags, fintech, "aggregate_stress", 0.0, 1.0, "V5", "fintech_stress")
        _check_range(
            flags, fintech, "payment_volume_impact_pct",
            0.0, 100.0, "V1", "fintech_stress",
        )
        _check_range(
            flags, fintech, "api_availability_pct",
            0.0, 100.0, "V1", "fintech_stress",
        )

    # ── Financial impact ────────────────────────────────────────────────────
    fi = result.get("financial_impact", {})
    if fi and isinstance(fi, dict):
        _check_non_negative(flags, fi, "total_loss_usd", "V4", "financial_impact")

    # ── Headline ────────────────────────────────────────────────────────────
    headline = result.get("headline", {})
    if headline and isinstance(headline, dict):
        _check_non_negative(flags, headline, "total_loss_usd", "V4", "headline")

    # ── Decision plan actions ───────────────────────────────────────────────
    dp = result.get("decision_plan", {})
    if dp and isinstance(dp, dict):
        _check_range(
            flags, dp, "time_to_first_failure_hours",
            0.0, scenario_window_hours, "V2", "decision_plan",
        )
        for i, action in enumerate(dp.get("actions", [])):
            if not isinstance(action, dict):
                continue
            prefix = f"decision_plan.actions[{i}]"
            _check_non_negative(flags, action, "loss_avoided_usd", "V4", prefix)
            _check_non_negative(flags, action, "cost_usd", "V4", prefix)
            _check_range(flags, action, "priority_score", 0.0, 1.0, "V5", prefix)
            _check_range(flags, action, "urgency", 0.0, 1.0, "V5", prefix)
            _check_range(flags, action, "feasibility", 0.0, 1.0, "V5", prefix)
            _check_range(flags, action, "regulatory_risk", 0.0, 1.0, "V5", prefix)

            # V6: Extreme ratio check
            loss_avoided = float(action.get("loss_avoided_usd", 0) or 0)
            cost = float(action.get("cost_usd", 0) or 0)
            if cost > 0 and loss_avoided / cost > 100:
                flags.append(ValidationFlag(
                    field=f"{prefix}.loss_avoided/cost ratio",
                    issue=f"Extreme ratio: {loss_avoided/cost:.1f}x (loss_avoided/cost > 100x)",
                    value=round(loss_avoided / cost, 2),
                    rule="V6",
                    severity="warning",
                ))

    # ── Portfolio value (ROI) ───────────────────────────────────────────────
    pv = result.get("portfolio_value", {})
    if pv and isinstance(pv, dict):
        _check_range(flags, pv, "roi_ratio", -50.0, 50.0, "V3", "portfolio_value")

    return flags
