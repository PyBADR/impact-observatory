"""
Truth Validation Engine
========================

Validates data records against TruthValidationPolicy definitions.
All functions are pure — no DB access, no side effects.

Validation checks (in order):
  1. Freshness — is the record newer than freshness_max_hours?
  2. Completeness — does the record have ≥ completeness_min_fields non-null?
  3. Corroboration — do multiple sources agree (if required)?
  4. Field-level — per-field checks: range, not_null, regex, enum_member

Each check produces a pass/fail. Overall is_valid = all checks pass.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    TruthValidationPolicy,
    TruthValidationResult,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Individual check functions — pure, deterministic
# ═══════════════════════════════════════════════════════════════════════════════


def check_freshness(
    record_timestamp: Optional[datetime],
    max_hours: float,
    now: Optional[datetime] = None,
) -> bool:
    """Check if the record is fresher than max_hours.

    Returns True if record_timestamp is None (no timestamp = no freshness
    requirement can be checked, so we defer to completeness).
    """
    if record_timestamp is None:
        return True
    reference = now or datetime.now(timezone.utc)
    age = reference - record_timestamp
    return age <= timedelta(hours=max_hours)


def check_completeness(
    record: Dict[str, Any],
    min_fields: int,
) -> bool:
    """Check if the record has at least min_fields non-null values."""
    non_null = sum(1 for v in record.values() if v is not None)
    return non_null >= min_fields


def check_corroboration(
    source_values: List[Tuple[str, float]],
    min_sources: int,
    deviation_max_pct: Optional[float],
) -> bool:
    """Check if multiple sources agree on a numeric value.

    Args:
        source_values: List of (source_id, value) pairs.
        min_sources: Minimum number of sources required.
        deviation_max_pct: Max allowed deviation (%) between any two sources.

    Returns:
        True if corroboration passes.
    """
    if len(source_values) < min_sources:
        return False

    if deviation_max_pct is None:
        return True  # No deviation check required, count-only

    values = [v for _, v in source_values]
    if not values:
        return False

    mean = sum(values) / len(values)
    if mean == 0:
        # All must be exactly 0 for 0-mean corroboration
        return all(v == 0 for v in values)

    for v in values:
        deviation_pct = abs(v - mean) / abs(mean) * 100.0
        if deviation_pct > deviation_max_pct:
            return False

    return True


def check_field(
    field_name: str,
    value: Any,
    check_type: str,
    params: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """Run a single field-level check.

    Returns (passed, failure_reason).
    """
    if check_type == "not_null":
        if value is None:
            return False, f"Field '{field_name}' is null."
        return True, None

    if check_type == "range":
        if value is None:
            return False, f"Field '{field_name}' is null (range check requires value)."
        min_val = params.get("min")
        max_val = params.get("max")
        if min_val is not None and value < min_val:
            return False, f"Field '{field_name}' = {value} < min {min_val}."
        if max_val is not None and value > max_val:
            return False, f"Field '{field_name}' = {value} > max {max_val}."
        return True, None

    if check_type == "regex":
        if value is None:
            return False, f"Field '{field_name}' is null (regex check)."
        pattern = params.get("pattern", "")
        if not re.match(pattern, str(value)):
            return False, f"Field '{field_name}' = '{value}' does not match /{pattern}/."
        return True, None

    if check_type == "enum_member":
        allowed = params.get("values", [])
        if value not in allowed:
            return False, f"Field '{field_name}' = '{value}' not in {allowed}."
        return True, None

    if check_type == "freshness":
        # Field-level freshness (for per-field timestamps)
        if value is None:
            return True, None  # No timestamp = skip
        max_age_hours = params.get("max_age_hours", 24.0)
        if isinstance(value, datetime):
            age = datetime.now(timezone.utc) - value
            if age > timedelta(hours=max_age_hours):
                return False, f"Field '{field_name}' is {age.total_seconds() / 3600:.1f}h old (max: {max_age_hours}h)."
        return True, None

    return True, None  # Unknown check type = pass (forward compatible)


# ═══════════════════════════════════════════════════════════════════════════════
# Main validation function
# ═══════════════════════════════════════════════════════════════════════════════


def validate_record(
    policy: TruthValidationPolicy,
    record_id: str,
    record: Dict[str, Any],
    record_timestamp: Optional[datetime] = None,
    source_values: Optional[List[Tuple[str, float]]] = None,
    now: Optional[datetime] = None,
) -> TruthValidationResult:
    """Validate a data record against a TruthValidationPolicy.

    Pure function. No side effects. Returns a TruthValidationResult.

    Args:
        policy: The validation policy to apply.
        record_id: Identifier for the record being validated.
        record: Dict of field_name → value for the record.
        record_timestamp: When the record was produced/fetched.
        source_values: For corroboration: [(source_id, numeric_value), ...].
        now: Override for current time (for deterministic testing).

    Returns:
        TruthValidationResult with all check outcomes.
    """
    failure_details: List[Dict[str, Any]] = []

    # 1. Freshness
    freshness_ok = check_freshness(record_timestamp, policy.freshness_max_hours, now=now)
    if not freshness_ok:
        failure_details.append({
            "check": "freshness",
            "max_hours": policy.freshness_max_hours,
            "record_timestamp": record_timestamp.isoformat() if record_timestamp else None,
        })

    # 2. Completeness
    completeness_ok = check_completeness(record, policy.completeness_min_fields)
    if not completeness_ok:
        non_null = sum(1 for v in record.values() if v is not None)
        failure_details.append({
            "check": "completeness",
            "non_null_fields": non_null,
            "required": policy.completeness_min_fields,
        })

    # 3. Corroboration
    corroboration_ok: Optional[bool] = None
    if policy.corroboration_required:
        src_vals = source_values or []
        corroboration_ok = check_corroboration(
            src_vals,
            policy.corroboration_min_sources,
            policy.deviation_max_pct,
        )
        if not corroboration_ok:
            failure_details.append({
                "check": "corroboration",
                "sources_provided": len(src_vals),
                "min_required": policy.corroboration_min_sources,
            })

    # 4. Field-level checks
    field_passed = 0
    field_failed = 0
    for rule in policy.validation_rules:
        field_name = rule.get("field", "")
        check_type = rule.get("check", "")
        params = {k: v for k, v in rule.items() if k not in ("field", "check")}
        value = record.get(field_name)
        ok, reason = check_field(field_name, value, check_type, params)
        if ok:
            field_passed += 1
        else:
            field_failed += 1
            failure_details.append({
                "check": "field",
                "field": field_name,
                "check_type": check_type,
                "reason": reason,
            })

    # Overall validity
    is_valid = (
        freshness_ok
        and completeness_ok
        and (corroboration_ok is None or corroboration_ok)
        and field_failed == 0
    )

    result = TruthValidationResult(
        policy_id=policy.policy_id,
        target_dataset=policy.target_dataset,
        record_id=record_id,
        is_valid=is_valid,
        freshness_passed=freshness_ok,
        completeness_passed=completeness_ok,
        corroboration_passed=corroboration_ok,
        field_checks_passed=field_passed,
        field_checks_failed=field_failed,
        failure_details=failure_details,
    )
    result.compute_hash()
    return result


def resolve_source_priority(
    policy: TruthValidationPolicy,
    available_sources: List[str],
) -> Optional[str]:
    """Given a policy's source priority order, return the highest-ranked
    source that is available.

    Returns None if no available source matches the priority list.
    """
    available_set = set(available_sources)
    for source in policy.source_priority_order:
        if source in available_set:
            return source
    return None
