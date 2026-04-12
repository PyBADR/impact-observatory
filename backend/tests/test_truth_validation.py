"""
Truth Validation Engine — Tests
=================================

Validates:
  1. Freshness check with stale and fresh data
  2. Completeness check with varying non-null field counts
  3. Corroboration check with agreement and divergence
  4. Field-level checks: range, not_null, regex, enum_member
  5. Full validate_record round-trip
  6. Source priority resolution
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from src.data_foundation.governance.schemas import TruthValidationPolicy
from src.data_foundation.governance.truth_validation import (
    check_freshness,
    check_completeness,
    check_corroboration,
    check_field,
    validate_record,
    resolve_source_priority,
)


NOW = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)


def _make_policy(**kwargs):
    defaults = dict(
        target_dataset="p1_oil_energy_signals",
        policy_name="Test Policy",
        source_priority_order=["IEA", "OPEC", "Reuters"],
        authored_by="admin",
    )
    defaults.update(kwargs)
    return TruthValidationPolicy(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Freshness
# ═══════════════════════════════════════════════════════════════════════════════


class TestFreshness:

    def test_fresh_record_passes(self):
        ts = NOW - timedelta(hours=2)
        assert check_freshness(ts, max_hours=24.0, now=NOW) is True

    def test_stale_record_fails(self):
        ts = NOW - timedelta(hours=48)
        assert check_freshness(ts, max_hours=24.0, now=NOW) is False

    def test_exact_boundary_passes(self):
        ts = NOW - timedelta(hours=24)
        assert check_freshness(ts, max_hours=24.0, now=NOW) is True

    def test_none_timestamp_passes(self):
        assert check_freshness(None, max_hours=24.0, now=NOW) is True


# ═══════════════════════════════════════════════════════════════════════════════
# Completeness
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompleteness:

    def test_sufficient_fields(self):
        record = {"a": 1, "b": 2, "c": 3}
        assert check_completeness(record, min_fields=3) is True

    def test_insufficient_fields(self):
        record = {"a": 1, "b": None, "c": None}
        assert check_completeness(record, min_fields=2) is False

    def test_empty_record_fails(self):
        assert check_completeness({}, min_fields=1) is False

    def test_all_none_fails(self):
        record = {"a": None, "b": None}
        assert check_completeness(record, min_fields=1) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Corroboration
# ═══════════════════════════════════════════════════════════════════════════════


class TestCorroboration:

    def test_sufficient_agreeing_sources(self):
        sources = [("IEA", 75.0), ("OPEC", 76.0), ("Reuters", 74.5)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=5.0) is True

    def test_insufficient_sources(self):
        sources = [("IEA", 75.0)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=5.0) is False

    def test_excessive_deviation(self):
        sources = [("IEA", 75.0), ("OPEC", 100.0)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=5.0) is False

    def test_no_deviation_check(self):
        sources = [("A", 100.0), ("B", 200.0)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=None) is True

    def test_zero_mean_all_zero(self):
        sources = [("A", 0.0), ("B", 0.0)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=5.0) is True

    def test_zero_mean_not_all_zero(self):
        sources = [("A", 0.0), ("B", 1.0)]
        assert check_corroboration(sources, min_sources=2, deviation_max_pct=5.0) is False


# ═══════════════════════════════════════════════════════════════════════════════
# Field-level checks
# ═══════════════════════════════════════════════════════════════════════════════


class TestFieldChecks:

    def test_not_null_passes(self):
        ok, reason = check_field("x", 42, "not_null", {})
        assert ok is True

    def test_not_null_fails(self):
        ok, reason = check_field("x", None, "not_null", {})
        assert ok is False

    def test_range_passes(self):
        ok, _ = check_field("price", 75.0, "range", {"min": 0, "max": 200})
        assert ok is True

    def test_range_below_min(self):
        ok, reason = check_field("price", -5, "range", {"min": 0, "max": 200})
        assert ok is False
        assert "min" in reason.lower()

    def test_range_above_max(self):
        ok, reason = check_field("price", 300, "range", {"min": 0, "max": 200})
        assert ok is False
        assert "max" in reason.lower()

    def test_regex_passes(self):
        ok, _ = check_field("code", "KW-001", "regex", {"pattern": r"^[A-Z]{2}-\d{3}$"})
        assert ok is True

    def test_regex_fails(self):
        ok, reason = check_field("code", "invalid", "regex", {"pattern": r"^[A-Z]{2}-\d{3}$"})
        assert ok is False

    def test_enum_member_passes(self):
        ok, _ = check_field("status", "ACTIVE", "enum_member", {"values": ["ACTIVE", "RETIRED"]})
        assert ok is True

    def test_enum_member_fails(self):
        ok, reason = check_field("status", "UNKNOWN", "enum_member", {"values": ["ACTIVE", "RETIRED"]})
        assert ok is False

    def test_unknown_check_type_passes(self):
        """Forward compatibility: unknown checks don't fail."""
        ok, _ = check_field("x", 1, "future_check_type", {})
        assert ok is True


# ═══════════════════════════════════════════════════════════════════════════════
# Full validate_record
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateRecord:

    def test_fully_valid_record(self):
        policy = _make_policy(
            freshness_max_hours=24.0,
            completeness_min_fields=2,
            validation_rules=[
                {"field": "price", "check": "range", "min": 0, "max": 200},
            ],
        )
        result = validate_record(
            policy=policy,
            record_id="REC-1",
            record={"price": 75.0, "source": "IEA"},
            record_timestamp=NOW - timedelta(hours=1),
            now=NOW,
        )
        assert result.is_valid is True
        assert result.freshness_passed is True
        assert result.completeness_passed is True
        assert result.field_checks_passed == 1
        assert result.field_checks_failed == 0
        assert result.provenance_hash != ""

    def test_stale_record_invalid(self):
        policy = _make_policy(freshness_max_hours=6.0)
        result = validate_record(
            policy=policy,
            record_id="REC-2",
            record={"price": 75.0},
            record_timestamp=NOW - timedelta(hours=12),
            now=NOW,
        )
        assert result.is_valid is False
        assert result.freshness_passed is False

    def test_incomplete_record_invalid(self):
        policy = _make_policy(completeness_min_fields=3)
        result = validate_record(
            policy=policy,
            record_id="REC-3",
            record={"price": 75.0, "source": None},
            now=NOW,
        )
        assert result.is_valid is False
        assert result.completeness_passed is False

    def test_corroboration_failure(self):
        policy = _make_policy(
            corroboration_required=True,
            corroboration_min_sources=2,
            deviation_max_pct=5.0,
        )
        result = validate_record(
            policy=policy,
            record_id="REC-4",
            record={"price": 75.0},
            source_values=[("IEA", 75.0)],  # Only 1 source
            now=NOW,
        )
        assert result.is_valid is False
        assert result.corroboration_passed is False

    def test_field_check_failure(self):
        policy = _make_policy(
            validation_rules=[
                {"field": "price", "check": "range", "min": 0, "max": 100},
            ],
        )
        result = validate_record(
            policy=policy,
            record_id="REC-5",
            record={"price": 150.0},
            now=NOW,
        )
        assert result.is_valid is False
        assert result.field_checks_failed == 1
        assert len(result.failure_details) > 0

    def test_multiple_failures_all_reported(self):
        policy = _make_policy(
            freshness_max_hours=1.0,
            completeness_min_fields=5,
            validation_rules=[
                {"field": "country", "check": "not_null"},
            ],
        )
        result = validate_record(
            policy=policy,
            record_id="REC-6",
            record={"price": 75.0, "country": None},
            record_timestamp=NOW - timedelta(hours=10),
            now=NOW,
        )
        assert result.is_valid is False
        # Should have freshness, completeness, and field check failures
        assert len(result.failure_details) >= 3


# ═══════════════════════════════════════════════════════════════════════════════
# Source priority resolution
# ═══════════════════════════════════════════════════════════════════════════════


class TestResolveSourcePriority:

    def test_returns_highest_available(self):
        policy = _make_policy(source_priority_order=["IEA", "OPEC", "Reuters"])
        assert resolve_source_priority(policy, ["Reuters", "OPEC"]) == "OPEC"

    def test_returns_first_when_all_available(self):
        policy = _make_policy(source_priority_order=["IEA", "OPEC"])
        assert resolve_source_priority(policy, ["IEA", "OPEC"]) == "IEA"

    def test_returns_none_when_none_available(self):
        policy = _make_policy(source_priority_order=["IEA", "OPEC"])
        assert resolve_source_priority(policy, ["Bloomberg"]) is None

    def test_returns_none_for_empty_available(self):
        policy = _make_policy(source_priority_order=["IEA"])
        assert resolve_source_priority(policy, []) is None
