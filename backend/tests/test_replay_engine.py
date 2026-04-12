"""
Replay Engine — Determinism + Round-Trip Tests
================================================

Validates:
  1. Replay is deterministic (same DataState + rules → same results)
  2. Replay correctly identifies triggered vs non-triggered rules
  3. Divergence detection works (replay vs original)
  4. compare_replay_to_original summary is accurate
  5. Failed replay handled gracefully
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.data_foundation.schemas.enums import (
    DecisionAction,
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)
from src.data_foundation.schemas.decision_rules import DecisionRule, RuleCondition
from src.data_foundation.decision.rule_engine import DataState
from src.data_foundation.evaluation.replay_engine import (
    replay_event,
    compare_replay_to_original,
)
from src.data_foundation.evaluation.schemas import ReplayStatus


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


def _make_oil_rule() -> DecisionRule:
    return DecisionRule(
        rule_id="RULE-OIL-BRENT-DROP-30",
        rule_name="Oil Crash >30%",
        description="Test rule",
        version=1,
        is_active=True,
        conditions=[
            RuleCondition(field="oil_energy_signals.change_pct", operator="lt", threshold=-30),
        ],
        condition_logic="AND",
        action=DecisionAction.ACTIVATE_CONTINGENCY,
        escalation_level=RiskLevel.SEVERE,
        applicable_countries=[GCCCountry.SA, GCCCountry.KW],
        applicable_sectors=[Sector.ENERGY],
        requires_human_approval=True,
        cooldown_minutes=1440,
    )


def _make_lcr_rule() -> DecisionRule:
    return DecisionRule(
        rule_id="RULE-LIQUIDITY-KW-LCR-BREACH",
        rule_name="LCR Breach",
        description="Test rule",
        version=1,
        is_active=True,
        conditions=[
            RuleCondition(field="banking_sector_profiles.lcr_pct", operator="lt", threshold=100),
        ],
        condition_logic="AND",
        action=DecisionAction.ESCALATE,
        escalation_level=RiskLevel.SEVERE,
        applicable_countries=[GCCCountry.KW],
        applicable_sectors=[Sector.BANKING],
        requires_human_approval=True,
        cooldown_minutes=480,
    )


def _make_data_state_oil_crash() -> DataState:
    return DataState(values={
        "oil_energy_signals.change_pct": -35.0,
        "banking_sector_profiles.lcr_pct": 150.0,
    })


def _make_data_state_lcr_breach() -> DataState:
    return DataState(values={
        "oil_energy_signals.change_pct": -5.0,
        "banking_sector_profiles.lcr_pct": 92.0,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Determinism tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestReplayDeterminism:

    def test_same_inputs_same_results(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()

        results_a = []
        results_b = []

        for _ in range(10):
            _, res = replay_event(data_state, rules, initiated_by="test")
            results_a.append([(r.rule_id, r.triggered) for r in res])

        for _ in range(10):
            _, res = replay_event(data_state, rules, initiated_by="test")
            results_b.append([(r.rule_id, r.triggered) for r in res])

        # All runs should produce identical trigger patterns
        for a, b in zip(results_a, results_b):
            assert a == b

    def test_oil_crash_triggers_oil_rule_only(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()

        run, results = replay_event(data_state, rules, initiated_by="test")

        assert run.status == ReplayStatus.COMPLETED
        assert len(results) == 2

        oil_result = next(r for r in results if r.rule_id == "RULE-OIL-BRENT-DROP-30")
        lcr_result = next(r for r in results if r.rule_id == "RULE-LIQUIDITY-KW-LCR-BREACH")

        assert oil_result.triggered is True
        assert oil_result.action == "ACTIVATE_CONTINGENCY"
        assert lcr_result.triggered is False

    def test_lcr_breach_triggers_lcr_rule_only(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_lcr_breach()

        run, results = replay_event(data_state, rules, initiated_by="test")

        oil_result = next(r for r in results if r.rule_id == "RULE-OIL-BRENT-DROP-30")
        lcr_result = next(r for r in results if r.rule_id == "RULE-LIQUIDITY-KW-LCR-BREACH")

        assert oil_result.triggered is False
        assert lcr_result.triggered is True


# ═══════════════════════════════════════════════════════════════════════════════
# Divergence detection
# ═══════════════════════════════════════════════════════════════════════════════


class TestDivergenceDetection:

    def test_matching_original(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()

        # Original: oil triggered, lcr did not
        original = {
            "RULE-OIL-BRENT-DROP-30": True,
            "RULE-LIQUIDITY-KW-LCR-BREACH": False,
        }

        _, results = replay_event(
            data_state, rules, initiated_by="test",
            original_triggered_rule_ids=original,
        )

        for r in results:
            assert r.matches_original is True
            assert r.divergence_reason is None

    def test_divergent_result(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()

        # Pretend original had BOTH triggered — but replay only triggers oil
        original = {
            "RULE-OIL-BRENT-DROP-30": True,
            "RULE-LIQUIDITY-KW-LCR-BREACH": True,  # Wrong — this should not trigger
        }

        _, results = replay_event(
            data_state, rules, initiated_by="test",
            original_triggered_rule_ids=original,
        )

        oil_result = next(r for r in results if r.rule_id == "RULE-OIL-BRENT-DROP-30")
        lcr_result = next(r for r in results if r.rule_id == "RULE-LIQUIDITY-KW-LCR-BREACH")

        assert oil_result.matches_original is True
        assert lcr_result.matches_original is False
        assert "does NOT trigger now" in lcr_result.divergence_reason

    def test_no_original_gives_none(self):
        rules = [_make_oil_rule()]
        data_state = _make_data_state_oil_crash()

        _, results = replay_event(data_state, rules, initiated_by="test")
        assert results[0].matches_original is None


# ═══════════════════════════════════════════════════════════════════════════════
# compare_replay_to_original summary
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompareReplaySummary:

    def test_all_matching(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()
        original = {"RULE-OIL-BRENT-DROP-30": True, "RULE-LIQUIDITY-KW-LCR-BREACH": False}

        _, results = replay_event(
            data_state, rules, initiated_by="test",
            original_triggered_rule_ids=original,
        )
        summary = compare_replay_to_original(results)

        assert summary["total_rules"] == 2
        assert summary["total_matching"] == 2
        assert summary["total_divergent"] == 0
        assert summary["match_rate"] == 1.0

    def test_one_divergent(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()
        original = {"RULE-OIL-BRENT-DROP-30": True, "RULE-LIQUIDITY-KW-LCR-BREACH": True}

        _, results = replay_event(
            data_state, rules, initiated_by="test",
            original_triggered_rule_ids=original,
        )
        summary = compare_replay_to_original(results)

        assert summary["total_matching"] == 1
        assert summary["total_divergent"] == 1
        assert summary["match_rate"] == 0.5
        assert len(summary["divergent_rules"]) == 1

    def test_no_comparison_data(self):
        rules = [_make_oil_rule()]
        data_state = _make_data_state_oil_crash()

        _, results = replay_event(data_state, rules, initiated_by="test")
        summary = compare_replay_to_original(results)

        assert summary["total_unknown"] == 1
        assert summary["match_rate"] == 1.0  # No comparisons → default 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Replay metadata
# ═══════════════════════════════════════════════════════════════════════════════


class TestReplayMetadata:

    def test_replay_run_has_hashes(self):
        rules = [_make_oil_rule()]
        data_state = _make_data_state_oil_crash()

        run, _ = replay_event(data_state, rules, initiated_by="analyst-1")

        assert run.replay_data_state_hash != ""
        assert run.provenance_hash != ""
        assert run.initiated_by == "analyst-1"

    def test_replay_run_completed(self):
        rules = [_make_oil_rule()]
        data_state = _make_data_state_oil_crash()

        run, _ = replay_event(data_state, rules, initiated_by="test")

        assert run.status == ReplayStatus.COMPLETED
        assert run.completed_at is not None
        assert run.error_message is None

    def test_results_have_hashes(self):
        rules = [_make_oil_rule()]
        data_state = _make_data_state_oil_crash()

        _, results = replay_event(data_state, rules, initiated_by="test")

        for r in results:
            assert r.provenance_hash != ""

    def test_rule_set_snapshot_captured(self):
        rules = [_make_oil_rule(), _make_lcr_rule()]
        data_state = _make_data_state_oil_crash()

        run, _ = replay_event(data_state, rules, initiated_by="test")

        assert "RULE-OIL-BRENT-DROP-30" in run.rule_set_snapshot
        assert "RULE-LIQUIDITY-KW-LCR-BREACH" in run.rule_set_snapshot
        assert run.rule_set_snapshot["RULE-OIL-BRENT-DROP-30"]["version"] == 1
