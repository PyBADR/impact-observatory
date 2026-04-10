"""
Data Sanity Guard — prevents invalid values from reaching the UI.

Catches and replaces:
  - Percentages > 100% or < 0%
  - Sentinel values like 9999h (time_to_breach with no actual breach)
  - NaN / Infinity / negative losses
  - ROI ratios > 100x (contamination indicator)
  - Stress scores outside [0, 1]

Pure function. Applied as the LAST stage before API response.
Logs every mutation for audit trail integrity.
"""
from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# Module-level mutation collector — reset per sanitize call
_mutations: list[dict[str, Any]] = []


def _record_mutation(field: str, original: Any, clamped: Any, rule: str) -> None:
    """Record a sanity guard mutation for audit trail."""
    _mutations.append({
        "field": field,
        "original": _safe_repr(original),
        "clamped": _safe_repr(clamped),
        "rule": rule,
    })


def _safe_repr(v: Any) -> Any:
    """Safe repr for logging — convert NaN/Infinity to strings."""
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f):
            return "NaN"
        if math.isinf(f):
            return "Infinity" if f > 0 else "-Infinity"
        return f
    except (TypeError, ValueError):
        return str(v)


# ── Constants ────────────────────────────────────────────────────────────────

# Sentinel values used internally — replace for UI display
SENTINEL_HOURS = 9999.0
SENTINEL_REPLACEMENT_HOURS = None  # null in JSON = "not applicable"

# Maximum sane values
MAX_PERCENTAGE = 100.0
MAX_LOSS_USD = 500_000_000_000  # $500B — no GCC scenario exceeds this
MAX_HOURS = 8760.0  # 1 year
MAX_ROI_RATIO = 50.0  # 50x ROI is the upper sanity bound
MAX_STRESS = 1.0
MAX_CONFIDENCE = 1.0


def _safe_float(v: Any, fallback: float = 0.0) -> float:
    """Coerce to float, replacing NaN/Infinity with fallback."""
    if v is None:
        return fallback
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return fallback
        return f
    except (TypeError, ValueError):
        return fallback


def _clamp(v: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, v))


def _sanitize_hours(v: Any) -> float | None:
    """Sanitize hours — replace 9999 sentinel with None."""
    f = _safe_float(v, 0.0)
    if f >= SENTINEL_HOURS:
        return SENTINEL_REPLACEMENT_HOURS
    if f < 0:
        return 0.0
    return round(min(f, MAX_HOURS), 1)


def _sanitize_percentage(v: Any) -> float:
    """Ensure percentage is in [0, 100]."""
    f = _safe_float(v, 0.0)
    return round(_clamp(f, 0.0, MAX_PERCENTAGE), 2)


def _sanitize_score(v: Any) -> float:
    """Ensure 0-1 score is in [0.0, 1.0]."""
    f = _safe_float(v, 0.0)
    return round(_clamp(f, 0.0, MAX_STRESS), 4)


def _sanitize_usd(v: Any) -> float:
    """Ensure USD value is non-negative and bounded."""
    f = _safe_float(v, 0.0)
    if f < 0:
        return 0.0
    return round(min(f, MAX_LOSS_USD), 2)


# ── Main Sanitizer ──────────────────────────────────────────────────────────


def _tracked_score(field: str, v: Any) -> float:
    """Sanitize score with mutation tracking."""
    original = v
    sanitized = _sanitize_score(v)
    if _safe_float(original) != sanitized and original is not None:
        _record_mutation(field, original, sanitized, "score_clamp_0_1")
    return sanitized


def _tracked_hours(field: str, v: Any) -> float | None:
    """Sanitize hours with mutation tracking."""
    original = v
    sanitized = _sanitize_hours(v)
    if _safe_float(original) != (sanitized or 0.0):
        _record_mutation(field, original, sanitized, "hours_sentinel_or_clamp")
    return sanitized


def _tracked_usd(field: str, v: Any) -> float:
    """Sanitize USD with mutation tracking."""
    original = v
    sanitized = _sanitize_usd(v)
    if _safe_float(original) != sanitized and original is not None:
        _record_mutation(field, original, sanitized, "usd_non_negative_bounded")
    return sanitized


def _tracked_pct(field: str, v: Any) -> float:
    """Sanitize percentage with mutation tracking."""
    original = v
    sanitized = _sanitize_percentage(v)
    if _safe_float(original) != sanitized and original is not None:
        _record_mutation(field, original, sanitized, "percentage_clamp_0_100")
    return sanitized


def sanitize_run_result(result: dict) -> dict:
    """
    Apply sanity guards to a full run result dict.

    Mutates in place and returns the same dict.
    Applied as the last pipeline stage before API response.
    Tracks all mutations for audit trail — stored in result["sanity_mutations"].
    """
    # Reset mutation collector
    _mutations.clear()
    # ── Banking stress ───────────────────────────────────────────────────
    banking = result.get("banking_stress") or result.get("banking", {})
    if banking and isinstance(banking, dict):
        banking["aggregate_stress"] = _tracked_score("banking_stress.aggregate_stress", banking.get("aggregate_stress"))
        banking["time_to_liquidity_breach_hours"] = _tracked_hours("banking_stress.time_to_liquidity_breach_hours", banking.get("time_to_liquidity_breach_hours"))
        if "lcr_ratio" in banking:
            banking["lcr_ratio"] = round(_safe_float(banking["lcr_ratio"], 1.0), 4)

    # ── Insurance stress ─────────────────────────────────────────────────
    insurance = result.get("insurance_stress") or result.get("insurance", {})
    if insurance and isinstance(insurance, dict):
        insurance["severity_index"] = _tracked_score("insurance_stress.severity_index", insurance.get("severity_index"))
        insurance["aggregate_stress"] = _tracked_score("insurance_stress.aggregate_stress", insurance.get("aggregate_stress"))
        insurance["time_to_insolvency_hours"] = _tracked_hours("insurance_stress.time_to_insolvency_hours", insurance.get("time_to_insolvency_hours"))
        if "combined_ratio" in insurance:
            cr = _safe_float(insurance["combined_ratio"], 1.0)
            insurance["combined_ratio"] = round(_clamp(cr, 0.0, 5.0), 4)

    # ── Fintech stress ───────────────────────────────────────────────────
    fintech = result.get("fintech_stress") or result.get("fintech", {})
    if fintech and isinstance(fintech, dict):
        fintech["aggregate_stress"] = _tracked_score("fintech_stress.aggregate_stress", fintech.get("aggregate_stress"))
        fintech["time_to_payment_failure_hours"] = _tracked_hours("fintech_stress.time_to_payment_failure_hours", fintech.get("time_to_payment_failure_hours"))
        if "payment_volume_impact_pct" in fintech:
            fintech["payment_volume_impact_pct"] = _tracked_pct("fintech_stress.payment_volume_impact_pct", fintech["payment_volume_impact_pct"])
        if "api_availability_pct" in fintech:
            fintech["api_availability_pct"] = _tracked_pct("fintech_stress.api_availability_pct", fintech["api_availability_pct"])

    # ── Financial impact ─────────────────────────────────────────────────
    fi = result.get("financial_impact", {})
    if fi and isinstance(fi, dict):
        fi["total_loss_usd"] = _tracked_usd("financial_impact.total_loss_usd", fi.get("total_loss_usd"))

    # ── Headline ─────────────────────────────────────────────────────────
    headline = result.get("headline", {})
    if headline and isinstance(headline, dict):
        headline["total_loss_usd"] = _tracked_usd("headline.total_loss_usd", headline.get("total_loss_usd"))

    # ── Decision plan ────────────────────────────────────────────────────
    dp = result.get("decision_plan", {})
    if dp and isinstance(dp, dict):
        dp["time_to_first_failure_hours"] = _tracked_hours("decision_plan.time_to_first_failure_hours", dp.get("time_to_first_failure_hours"))

        # Sanitize each action
        for i, action in enumerate(dp.get("actions", [])):
            if isinstance(action, dict):
                pfx = f"decision_plan.actions[{i}]"
                action["loss_avoided_usd"] = _tracked_usd(f"{pfx}.loss_avoided_usd", action.get("loss_avoided_usd"))
                action["cost_usd"] = _tracked_usd(f"{pfx}.cost_usd", action.get("cost_usd"))
                action["priority_score"] = _tracked_score(f"{pfx}.priority_score", action.get("priority_score"))
                action["urgency"] = _tracked_score(f"{pfx}.urgency", action.get("urgency"))
                action["regulatory_risk"] = _tracked_score(f"{pfx}.regulatory_risk", action.get("regulatory_risk"))
                action["feasibility"] = _tracked_score(f"{pfx}.feasibility", action.get("feasibility"))

    # ── Portfolio value (ROI) ────────────────────────────────────────────
    pv = result.get("portfolio_value", {})
    if pv and isinstance(pv, dict):
        roi = _safe_float(pv.get("roi_ratio"), 0.0)
        clamped_roi = round(_clamp(roi, -MAX_ROI_RATIO, MAX_ROI_RATIO), 4)
        if roi != clamped_roi:
            _record_mutation("portfolio_value.roi_ratio", roi, clamped_roi, "roi_clamp")
        pv["roi_ratio"] = clamped_roi
        tvc = _safe_float(pv.get("total_value_created"))
        clamped_tvc = round(_clamp(tvc, -MAX_LOSS_USD, MAX_LOSS_USD), 2)
        if tvc != clamped_tvc:
            _record_mutation("portfolio_value.total_value_created", tvc, clamped_tvc, "usd_clamp")
        pv["total_value_created"] = clamped_tvc

    # ── Unified risk score ───────────────────────────────────────────────
    if "unified_risk_score" in result:
        result["unified_risk_score"] = _tracked_score("unified_risk_score", result["unified_risk_score"])

    # ── Confidence score ─────────────────────────────────────────────────
    if "confidence_score" in result:
        result["confidence_score"] = _tracked_score("confidence_score", result["confidence_score"])

    expl = result.get("explainability", {})
    if expl and isinstance(expl, dict) and "confidence_score" in expl:
        expl["confidence_score"] = _tracked_score("explainability.confidence_score", expl["confidence_score"])

    # ── Attach mutations to result for audit trail ──────────────────────
    if _mutations:
        result["sanity_mutations"] = list(_mutations)
        logger.info("Sanity guard applied %d mutations", len(_mutations))
    else:
        result["sanity_mutations"] = []

    return result
