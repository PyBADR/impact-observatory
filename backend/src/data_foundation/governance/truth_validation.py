"""Source Truth Validation Engine — deterministic data quality checks.

Four-check validation pipeline:
  1. Freshness — is the data recent enough?
  2. Completeness — does it have enough non-null fields?
  3. Corroboration — do multiple sources agree?
  4. Field-level — range, not_null, regex, enum_member checks

Plus source priority resolution for conflict arbitration.
All functions are pure — no I/O, fully testable.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.data_foundation.governance.schemas import (
    TruthValidationPolicy,
    TruthValidationResult,
)

__all__ = [
    "check_freshness",
    "check_completeness",
    "check_corroboration",
    "check_field_rules",
    "validate_record",
    "resolve_source_priority",
]


def _gen_id() -> str:
    return f"TVR-{str(uuid4())[:12]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Individual Checks
# ═══════════════════════════════════════════════════════════════════════════════

def check_freshness(
    record_timestamp: datetime,
    max_hours: float,
    reference_time: datetime | None = None,
) -> bool:
    """Check if a record is fresh enough.

    Args:
        record_timestamp: When the record was observed/fetched.
        max_hours: Maximum age in hours.
        reference_time: Compare against this (default: now UTC).

    Returns:
        True if the record is within the freshness window.
    """
    ref = reference_time or datetime.now(timezone.utc)
    # Ensure both are timezone-aware
    if record_timestamp.tzinfo is None:
        record_timestamp = record_timestamp.replace(tzinfo=timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)

    age_hours = (ref - record_timestamp).total_seconds() / 3600.0
    return age_hours <= max_hours


def check_completeness(
    record: Dict[str, Any],
    min_fields: int,
) -> bool:
    """Check if a record has enough non-null fields.

    Args:
        record: The data record as a dict.
        min_fields: Minimum number of non-null fields required.

    Returns:
        True if the record has enough non-null fields.
    """
    non_null_count = sum(1 for v in record.values() if v is not None)
    return non_null_count >= min_fields


def check_corroboration(
    values: List[float],
    min_sources: int,
    deviation_max_pct: float | None = None,
) -> tuple[bool, List[Dict[str, Any]]]:
    """Check if multiple sources agree on a value.

    Args:
        values: List of numeric values from different sources.
        min_sources: Minimum number of sources required.
        deviation_max_pct: Maximum percentage deviation allowed between values.

    Returns:
        (passed, failure_details)
    """
    failures: List[Dict[str, Any]] = []

    if len(values) < min_sources:
        failures.append({
            "check": "corroboration_count",
            "required": min_sources,
            "actual": len(values),
            "message": f"Need {min_sources} sources, got {len(values)}",
        })
        return False, failures

    if deviation_max_pct is not None and len(values) >= 2:
        mean_val = sum(values) / len(values)
        if mean_val != 0:
            for i, v in enumerate(values):
                deviation_pct = abs(v - mean_val) / abs(mean_val) * 100.0
                if deviation_pct > deviation_max_pct:
                    failures.append({
                        "check": "corroboration_deviation",
                        "source_index": i,
                        "value": v,
                        "mean": mean_val,
                        "deviation_pct": round(deviation_pct, 2),
                        "max_pct": deviation_max_pct,
                    })

    return len(failures) == 0, failures


def check_field_rules(
    record: Dict[str, Any],
    rules: List[Dict[str, Any]],
) -> tuple[int, int, List[Dict[str, Any]]]:
    """Run field-level validation rules against a record.

    Supported rule types:
      - range: {"field": "x", "check": "range", "min": 0, "max": 100}
      - not_null: {"field": "x", "check": "not_null"}
      - regex: {"field": "x", "check": "regex", "pattern": "^[A-Z]+$"}
      - enum_member: {"field": "x", "check": "enum_member", "values": ["A", "B"]}

    Returns:
        (passed_count, failed_count, failure_details)
    """
    passed = 0
    failed = 0
    failures: List[Dict[str, Any]] = []

    for rule in rules:
        field = rule.get("field", "")
        check = rule.get("check", "")
        value = record.get(field)

        if check == "not_null":
            if value is not None:
                passed += 1
            else:
                failed += 1
                failures.append({"field": field, "check": check, "message": f"{field} is null"})

        elif check == "range":
            if value is None:
                failed += 1
                failures.append({"field": field, "check": check, "message": f"{field} is null"})
            else:
                try:
                    fval = float(value)
                    min_val = rule.get("min", float("-inf"))
                    max_val = rule.get("max", float("inf"))
                    if min_val <= fval <= max_val:
                        passed += 1
                    else:
                        failed += 1
                        failures.append({
                            "field": field, "check": check,
                            "value": fval, "min": min_val, "max": max_val,
                            "message": f"{field}={fval} outside [{min_val}, {max_val}]",
                        })
                except (TypeError, ValueError):
                    failed += 1
                    failures.append({"field": field, "check": check, "message": f"{field} not numeric"})

        elif check == "regex":
            pattern = rule.get("pattern", "")
            if value is None:
                failed += 1
                failures.append({"field": field, "check": check, "message": f"{field} is null"})
            elif re.match(pattern, str(value)):
                passed += 1
            else:
                failed += 1
                failures.append({
                    "field": field, "check": check, "value": str(value),
                    "pattern": pattern, "message": f"{field} does not match {pattern}",
                })

        elif check == "enum_member":
            allowed = rule.get("values", [])
            if value in allowed:
                passed += 1
            else:
                failed += 1
                failures.append({
                    "field": field, "check": check, "value": value,
                    "allowed": allowed, "message": f"{field}={value} not in {allowed}",
                })

        elif check == "freshness":
            # Freshness check on a datetime field
            max_age = rule.get("max_age_hours", 24)
            if value is None:
                failed += 1
                failures.append({"field": field, "check": check, "message": f"{field} is null"})
            else:
                ts = value if isinstance(value, datetime) else None
                if ts and check_freshness(ts, max_age):
                    passed += 1
                else:
                    failed += 1
                    failures.append({"field": field, "check": check, "message": f"{field} stale or invalid"})

    return passed, failed, failures


# ═══════════════════════════════════════════════════════════════════════════════
# Full Validation Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def validate_record(
    policy: TruthValidationPolicy,
    record_id: str,
    record: Dict[str, Any],
    record_timestamp: datetime,
    corroboration_values: List[float] | None = None,
    reference_time: datetime | None = None,
) -> TruthValidationResult:
    """Run the full validation pipeline against a record.

    Args:
        policy: The TruthValidationPolicy to evaluate against.
        record_id: ID of the record being validated.
        record: The data record as a dict.
        record_timestamp: When the record was observed.
        corroboration_values: Values from multiple sources (if corroboration required).
        reference_time: Time to compare freshness against.

    Returns:
        TruthValidationResult with all check results.
    """
    now = reference_time or datetime.now(timezone.utc)
    all_failures: List[Dict[str, Any]] = []

    # 1. Freshness
    freshness_passed = check_freshness(record_timestamp, policy.freshness_max_hours, now)
    if not freshness_passed:
        all_failures.append({
            "check": "freshness",
            "max_hours": policy.freshness_max_hours,
            "message": "Record exceeds freshness window.",
        })

    # 2. Completeness
    completeness_passed = check_completeness(record, policy.completeness_min_fields)
    if not completeness_passed:
        non_null = sum(1 for v in record.values() if v is not None)
        all_failures.append({
            "check": "completeness",
            "required": policy.completeness_min_fields,
            "actual": non_null,
            "message": f"Record has {non_null} non-null fields, need {policy.completeness_min_fields}.",
        })

    # 3. Corroboration (only if required by policy)
    corroboration_passed: bool | None = None
    if policy.corroboration_required:
        vals = corroboration_values or []
        corroboration_passed, corr_failures = check_corroboration(
            vals, policy.corroboration_min_sources, policy.deviation_max_pct,
        )
        all_failures.extend(corr_failures)

    # 4. Field-level rules
    field_passed, field_failed, field_failures = check_field_rules(
        record, policy.validation_rules,
    )
    all_failures.extend(field_failures)

    # Overall validity
    is_valid = (
        freshness_passed
        and completeness_passed
        and (corroboration_passed is not False)
        and field_failed == 0
    )

    return TruthValidationResult(
        result_id=_gen_id(),
        policy_id=policy.policy_id,
        target_dataset=policy.target_dataset,
        record_id=record_id,
        is_valid=is_valid,
        freshness_passed=freshness_passed,
        completeness_passed=completeness_passed,
        corroboration_passed=corroboration_passed,
        field_checks_passed=field_passed,
        field_checks_failed=field_failed,
        failure_details=all_failures,
        validated_at=now,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Source Priority Resolution
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_source_priority(
    policy: TruthValidationPolicy,
    source_records: Dict[str, Any],
) -> tuple[str | None, Any]:
    """Resolve which source is authoritative using priority order.

    Args:
        policy: Policy with source_priority_order.
        source_records: {source_id: record_value} map.

    Returns:
        (winning_source_id, winning_value) or (None, None) if no match.
    """
    for source_id in policy.source_priority_order:
        if source_id in source_records:
            return source_id, source_records[source_id]
    return None, None
