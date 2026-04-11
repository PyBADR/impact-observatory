"""Tests for truth validation engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.data_foundation.governance.schemas import TruthValidationPolicy
from src.data_foundation.governance.truth_validation import (
    check_completeness,
    check_corroboration,
    check_field_rules,
    check_freshness,
    resolve_source_priority,
    validate_record,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hours_ago(hours: float) -> datetime:
    return _utcnow() - timedelta(hours=hours)


def _make_policy(**overrides) -> TruthValidationPolicy:
    defaults = {
        "policy_id": "TVP-TEST",
        "target_dataset": "test_dataset",
        "policy_name": "Test policy",
        "freshness_max_hours": 24.0,
        "completeness_min_fields": 3,
        "authored_by": "admin",
    }
    defaults.update(overrides)
    return TruthValidationPolicy(**defaults)


class TestFreshness:
    def test_fresh_record(self):
        assert check_freshness(_hours_ago(1), max_hours=24.0) is True

    def test_stale_record(self):
        assert check_freshness(_hours_ago(48), max_hours=24.0) is False

    def test_exact_boundary(self):
        # Use explicit reference_time to avoid timing flakiness
        now = _utcnow()
        from datetime import timedelta
        ts = now - timedelta(hours=24)
        assert check_freshness(ts, max_hours=24.0, reference_time=now) is True

    def test_just_over_boundary(self):
        now = _utcnow()
        from datetime import timedelta
        ts = now - timedelta(hours=24, seconds=36)  # 24.01 hours
        assert check_freshness(ts, max_hours=24.0, reference_time=now) is False

    def test_zero_max_hours(self):
        # 0 hours = must be exactly now
        assert check_freshness(_hours_ago(0.01), max_hours=0.0) is False

    def test_naive_timestamp_handled(self):
        naive = datetime(2026, 4, 12, 12, 0, 0)
        # Should not raise — treated as UTC
        check_freshness(naive, max_hours=999999)


class TestCompleteness:
    def test_sufficient_fields(self):
        assert check_completeness({"a": 1, "b": 2, "c": 3}, min_fields=3) is True

    def test_insufficient_fields(self):
        assert check_completeness({"a": 1, "b": None}, min_fields=2) is False

    def test_all_null(self):
        assert check_completeness({"a": None, "b": None}, min_fields=1) is False

    def test_zero_min(self):
        assert check_completeness({}, min_fields=0) is True

    def test_empty_record(self):
        assert check_completeness({}, min_fields=1) is False


class TestCorroboration:
    def test_sufficient_sources_agree(self):
        passed, failures = check_corroboration([100, 101, 99], min_sources=2)
        assert passed is True

    def test_insufficient_sources(self):
        passed, failures = check_corroboration([100], min_sources=2)
        assert passed is False
        assert any("corroboration_count" in f.get("check", "") for f in failures)

    def test_deviation_within_limit(self):
        passed, failures = check_corroboration(
            [100, 102], min_sources=2, deviation_max_pct=5.0,
        )
        assert passed is True

    def test_deviation_exceeds_limit(self):
        passed, failures = check_corroboration(
            [100, 200], min_sources=2, deviation_max_pct=5.0,
        )
        assert passed is False
        assert any("deviation" in f.get("check", "") for f in failures)

    def test_no_deviation_check(self):
        passed, _ = check_corroboration([100, 200], min_sources=2, deviation_max_pct=None)
        assert passed is True

    def test_identical_values(self):
        passed, _ = check_corroboration([50, 50, 50], min_sources=2, deviation_max_pct=1.0)
        assert passed is True


class TestFieldRules:
    def test_range_pass(self):
        p, f, failures = check_field_rules(
            {"rate": 3.5},
            [{"field": "rate", "check": "range", "min": 0, "max": 10}],
        )
        assert p == 1 and f == 0

    def test_range_fail(self):
        p, f, failures = check_field_rules(
            {"rate": 15},
            [{"field": "rate", "check": "range", "min": 0, "max": 10}],
        )
        assert f == 1
        assert failures[0]["field"] == "rate"

    def test_not_null_pass(self):
        p, f, _ = check_field_rules(
            {"name": "test"},
            [{"field": "name", "check": "not_null"}],
        )
        assert p == 1

    def test_not_null_fail(self):
        p, f, _ = check_field_rules(
            {"name": None},
            [{"field": "name", "check": "not_null"}],
        )
        assert f == 1

    def test_regex_pass(self):
        p, f, _ = check_field_rules(
            {"code": "KW"},
            [{"field": "code", "check": "regex", "pattern": "^[A-Z]{2}$"}],
        )
        assert p == 1

    def test_regex_fail(self):
        p, f, _ = check_field_rules(
            {"code": "kw123"},
            [{"field": "code", "check": "regex", "pattern": "^[A-Z]{2}$"}],
        )
        assert f == 1

    def test_enum_member_pass(self):
        p, f, _ = check_field_rules(
            {"severity": "HIGH"},
            [{"field": "severity", "check": "enum_member", "values": ["LOW", "HIGH", "SEVERE"]}],
        )
        assert p == 1

    def test_enum_member_fail(self):
        p, f, _ = check_field_rules(
            {"severity": "MEGA"},
            [{"field": "severity", "check": "enum_member", "values": ["LOW", "HIGH", "SEVERE"]}],
        )
        assert f == 1

    def test_multiple_rules(self):
        p, f, _ = check_field_rules(
            {"rate": 3.5, "code": "KW", "name": None},
            [
                {"field": "rate", "check": "range", "min": 0, "max": 10},
                {"field": "code", "check": "regex", "pattern": "^[A-Z]{2}$"},
                {"field": "name", "check": "not_null"},
            ],
        )
        assert p == 2 and f == 1

    def test_missing_field_range(self):
        p, f, _ = check_field_rules(
            {},
            [{"field": "rate", "check": "range", "min": 0, "max": 10}],
        )
        assert f == 1


class TestValidateRecord:
    def test_valid_record(self):
        policy = _make_policy()
        result = validate_record(
            policy, "REC-001",
            {"a": 1, "b": 2, "c": 3},
            _hours_ago(1),
        )
        assert result.is_valid is True
        assert result.freshness_passed is True
        assert result.completeness_passed is True

    def test_stale_record(self):
        policy = _make_policy(freshness_max_hours=1.0)
        result = validate_record(
            policy, "REC-002",
            {"a": 1, "b": 2, "c": 3},
            _hours_ago(2),
        )
        assert result.is_valid is False
        assert result.freshness_passed is False

    def test_incomplete_record(self):
        policy = _make_policy(completeness_min_fields=5)
        result = validate_record(
            policy, "REC-003",
            {"a": 1, "b": 2},
            _hours_ago(1),
        )
        assert result.is_valid is False
        assert result.completeness_passed is False

    def test_corroboration_required_and_fails(self):
        policy = _make_policy(
            corroboration_required=True,
            corroboration_min_sources=3,
        )
        result = validate_record(
            policy, "REC-004",
            {"a": 1, "b": 2, "c": 3},
            _hours_ago(1),
            corroboration_values=[100],
        )
        assert result.is_valid is False
        assert result.corroboration_passed is False

    def test_corroboration_not_required(self):
        policy = _make_policy(corroboration_required=False)
        result = validate_record(
            policy, "REC-005",
            {"a": 1, "b": 2, "c": 3},
            _hours_ago(1),
        )
        assert result.corroboration_passed is None

    def test_field_rules_fail(self):
        policy = _make_policy(
            validation_rules=[{"field": "rate", "check": "range", "min": 0, "max": 10}],
        )
        result = validate_record(
            policy, "REC-006",
            {"a": 1, "b": 2, "c": 3, "rate": 999},
            _hours_ago(1),
        )
        assert result.is_valid is False
        assert result.field_checks_failed == 1

    def test_result_has_correct_ids(self):
        policy = _make_policy()
        result = validate_record(policy, "REC-007", {"a": 1, "b": 2, "c": 3}, _hours_ago(1))
        assert result.result_id.startswith("TVR-")
        assert result.policy_id == "TVP-TEST"
        assert result.target_dataset == "test_dataset"
        assert result.record_id == "REC-007"


class TestSourcePriority:
    def test_first_match_wins(self):
        policy = _make_policy(source_priority_order=["src-cbk", "src-eia", "src-imf"])
        source_id, value = resolve_source_priority(
            policy, {"src-eia": 95.0, "src-cbk": 100.0},
        )
        assert source_id == "src-cbk"
        assert value == 100.0

    def test_fallback_to_second(self):
        policy = _make_policy(source_priority_order=["src-cbk", "src-eia"])
        source_id, value = resolve_source_priority(
            policy, {"src-eia": 95.0},
        )
        assert source_id == "src-eia"

    def test_no_match(self):
        policy = _make_policy(source_priority_order=["src-cbk"])
        source_id, value = resolve_source_priority(
            policy, {"src-other": 50.0},
        )
        assert source_id is None
        assert value is None

    def test_empty_priority(self):
        policy = _make_policy(source_priority_order=[])
        source_id, value = resolve_source_priority(
            policy, {"src-cbk": 100.0},
        )
        assert source_id is None
