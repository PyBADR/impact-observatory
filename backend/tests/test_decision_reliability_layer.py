"""
Impact Observatory | مرصد الأثر
Sprint 2: Decision Reliability Layer — Validation Tests

Test suites:
  1. TestRangeEngine — low ≤ base ≤ high, confidence 0-100, method valid
  2. TestSensitivityEngine — points reflect input changes, baseline correct
  3. TestOutcomeTracking — store, update, deviation correct
  4. TestTrustMemory — success/failure counting, trust score formula
  5. TestConfidenceAdjustment — adjustment based on trust, scaling
  6. TestIntegration — full pipeline reliability payload
"""

import pytest

from src.engines.range_engine import (
    generate_ranges,
    range_total_loss,
    range_unified_risk_score,
    range_sector_stress,
)
from src.engines.sensitivity_engine import (
    generate_sensitivities,
    sensitivity_total_loss,
    sensitivity_urs,
    sensitivity_sector_stress,
)
from src.engines.outcome_engine import (
    store_prediction,
    update_outcome,
    get_outcome,
    build_outcome_records,
    build_trust_memories_for_run,
    build_confidence_adjustments,
    adjust_confidence,
    clear_stores,
    get_all_trust_memories,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_result():
    """Full simulation result for testing."""
    return {
        "scenario_id": "hormuz_chokepoint_disruption",
        "severity": 0.70,
        "event_severity": 0.58,
        "risk_level": "HIGH",
        "peak_day": 3,
        "confidence_score": 0.78,
        "unified_risk": {
            "score": 0.72,
            "risk_level": "HIGH",
            "components": {
                "AvgExposure": 0.18,
                "AvgStress": 0.35,
                "P": 0.88,
            },
        },
        "financial_impact": {
            "total_loss_usd": 9_300_000_000,
            "direct_loss_usd": 5_580_000_000,
            "indirect_loss_usd": 2_604_000_000,
            "systemic_loss_usd": 1_116_000_000,
            "systemic_multiplier": 1.12,
            "sector_losses": [
                {"sector": "energy", "loss_usd": 2_790_000_000},
                {"sector": "maritime", "loss_usd": 1_860_000_000},
                {"sector": "banking", "loss_usd": 1_674_000_000},
                {"sector": "insurance", "loss_usd": 930_000_000},
                {"sector": "logistics", "loss_usd": 744_000_000},
                {"sector": "fintech", "loss_usd": 558_000_000},
            ],
            "confidence_interval": {
                "lower": 8_277_000_000,
                "upper": 10_323_000_000,
                "confidence": 0.78,
            },
        },
        "sector_analysis": [
            {"sector": "energy", "exposure": 0.28, "stress": 0.62, "classification": "HIGH"},
            {"sector": "maritime", "exposure": 0.20, "stress": 0.48, "classification": "ELEVATED"},
            {"sector": "banking", "exposure": 0.18, "stress": 0.42, "classification": "ELEVATED"},
            {"sector": "insurance", "exposure": 0.08, "stress": 0.25, "classification": "LOW"},
        ],
        "decision_plan": {
            "actions": [
                {
                    "action_id": "ACT-001",
                    "sector": "energy",
                    "owner": "Energy Minister",
                    "action": "Strategic reserve release",
                    "priority_score": 0.89,
                    "urgency": 0.92,
                    "loss_avoided_usd": 3_500_000_000,
                    "cost_usd": 1_200_000_000,
                    "regulatory_risk": 0.75,
                    "feasibility": 0.88,
                    "time_to_act_hours": 6,
                },
                {
                    "action_id": "ACT-002",
                    "sector": "maritime",
                    "owner": "Port Authority",
                    "action": "Port rerouting protocols",
                    "priority_score": 0.82,
                    "urgency": 0.85,
                    "loss_avoided_usd": 1_200_000_000,
                    "cost_usd": 250_000_000,
                    "regulatory_risk": 0.60,
                    "feasibility": 0.92,
                    "time_to_act_hours": 4,
                },
                {
                    "action_id": "ACT-003",
                    "sector": "banking",
                    "owner": "Central Bank",
                    "action": "Interbank lending facility",
                    "priority_score": 0.75,
                    "urgency": 0.70,
                    "loss_avoided_usd": 800_000_000,
                    "cost_usd": 2_000_000_000,
                    "regulatory_risk": 0.85,
                    "feasibility": 0.75,
                    "time_to_act_hours": 12,
                },
            ],
        },
    }


@pytest.fixture(autouse=True)
def _clean_stores():
    """Clear outcome/trust stores before each test."""
    clear_stores()
    yield
    clear_stores()


# ═══════════════════════════════════════════════════════════════════════════════
# Test 1: Range Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestRangeEngine:
    def test_generates_ranges_for_all_metrics(self, sample_result):
        ranges = generate_ranges(sample_result)
        # Should have: projected_loss, unified_risk_score, confidence_score, + 4 sectors
        assert len(ranges) >= 7
        metric_ids = [r["metric_id"] for r in ranges]
        assert "projected_loss" in metric_ids
        assert "unified_risk_score" in metric_ids
        assert "confidence_score" in metric_ids

    def test_low_leq_base_leq_high(self, sample_result):
        """Critical invariant: low ≤ base ≤ high for all ranges."""
        ranges = generate_ranges(sample_result)
        for r in ranges:
            assert r["low"] <= r["base"], \
                f"{r['metric_id']}: low ({r['low']}) > base ({r['base']})"
            assert r["base"] <= r["high"], \
                f"{r['metric_id']}: base ({r['base']}) > high ({r['high']})"

    def test_confidence_0_to_100(self, sample_result):
        ranges = generate_ranges(sample_result)
        for r in ranges:
            assert 0 <= r["confidence"] <= 100, \
                f"{r['metric_id']}: confidence {r['confidence']} out of range"

    def test_method_is_valid(self, sample_result):
        ranges = generate_ranges(sample_result)
        valid = {"SENSITIVITY_SWEEP", "SCENARIO_BAND", "HYBRID"}
        for r in ranges:
            assert r["method"] in valid, \
                f"{r['metric_id']}: invalid method {r['method']}"

    def test_range_band_is_nonzero(self, sample_result):
        """Range must have some width (low < high) for non-zero base."""
        ranges = generate_ranges(sample_result)
        for r in ranges:
            if r["base"] > 0:
                assert r["high"] > r["low"], \
                    f"{r['metric_id']}: zero-width range for base {r['base']}"

    def test_loss_range_has_notes(self, sample_result):
        r = range_total_loss(sample_result)
        assert r["notes"] is not None
        assert len(r["notes"]) >= 2
        # Notes should reference actual numbers
        assert any("severity" in n.lower() for n in r["notes"])

    def test_higher_severity_widens_range(self):
        """Higher severity should produce wider bands."""
        low_sev = {
            "severity": 0.30,
            "confidence_score": 0.85,
            "scenario_id": "hormuz_chokepoint_disruption",
            "financial_impact": {"total_loss_usd": 2_000_000_000},
            "unified_risk": {"score": 0.30, "risk_level": "LOW", "components": {}},
            "sector_analysis": [],
        }
        high_sev = {**low_sev, "severity": 0.90, "confidence_score": 0.60,
                     "financial_impact": {"total_loss_usd": 15_000_000_000}}

        r_low = range_total_loss(low_sev)
        r_high = range_total_loss(high_sev)

        width_low = r_low["high"] - r_low["low"]
        width_high = r_high["high"] - r_high["low"]
        # Higher severity should produce wider absolute band
        assert width_high > width_low

    def test_graceful_with_empty_result(self):
        ranges = generate_ranges({})
        assert isinstance(ranges, list)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2: Sensitivity Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestSensitivityEngine:
    def test_generates_sensitivity_for_key_metrics(self, sample_result):
        analyses = generate_sensitivities(sample_result)
        metric_ids = [a["metric_id"] for a in analyses]
        assert "projected_loss" in metric_ids
        assert "unified_risk_score" in metric_ids

    def test_points_reflect_input_changes(self, sample_result):
        """Higher severity input → higher output."""
        analysis = sensitivity_total_loss(sample_result)
        points = analysis["points"]
        assert len(points) >= 5

        # Monotonically increasing: higher severity → higher loss
        for i in range(1, len(points)):
            assert points[i]["input_value"] >= points[i - 1]["input_value"]
            assert points[i]["output_value"] >= points[i - 1]["output_value"], \
                f"Loss should increase with severity: {points[i-1]} → {points[i]}"

    def test_baseline_value_is_correct(self, sample_result):
        analysis = sensitivity_total_loss(sample_result)
        expected = sample_result["financial_impact"]["total_loss_usd"]
        assert analysis["baseline_value"] == expected

    def test_variable_tested_is_severity(self, sample_result):
        analysis = sensitivity_urs(sample_result)
        assert analysis["variable_tested"] == "severity"

    def test_trend_is_set(self, sample_result):
        analysis = sensitivity_total_loss(sample_result)
        assert analysis["trend"] is not None
        assert "nonlinear" in analysis["trend"]

    def test_sector_sensitivity_exists(self, sample_result):
        analysis = sensitivity_sector_stress(sample_result, "energy")
        assert analysis["metric_id"] == "sector_stress_energy"
        assert len(analysis["points"]) >= 5

    def test_urs_capped_at_one(self, sample_result):
        analysis = sensitivity_urs(sample_result)
        for pt in analysis["points"]:
            assert pt["output_value"] <= 1.0, \
                f"URS should be ≤ 1.0: {pt}"

    def test_graceful_with_empty_result(self):
        analyses = generate_sensitivities({})
        assert isinstance(analyses, list)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 3: Outcome Tracking
# ═══════════════════════════════════════════════════════════════════════════════

class TestOutcomeTracking:
    def test_store_prediction(self):
        record = store_prediction("run-1", "ACT-001", "hormuz", 3_500_000_000)
        assert record["action_id"] == "ACT-001"
        assert record["predicted_value"] == 3_500_000_000
        assert record["status"] == "PENDING"
        assert record["actual_value"] is None
        assert record["deviation"] is None

    def test_update_outcome_computes_deviation(self):
        store_prediction("run-1", "ACT-001", "hormuz", 3_500_000_000)
        updated = update_outcome("run-1", "ACT-001", 3_200_000_000)
        assert updated is not None
        assert updated["actual_value"] == 3_200_000_000
        assert updated["deviation"] == -300_000_000  # actual - predicted
        assert updated["status"] == "CONFIRMED"

    def test_deviation_pct_correct(self):
        store_prediction("run-1", "ACT-001", "hormuz", 1_000_000_000)
        updated = update_outcome("run-1", "ACT-001", 800_000_000)
        assert updated is not None
        assert updated["deviation_pct"] == -20.0  # (800M - 1B) / 1B * 100

    def test_update_nonexistent_returns_none(self):
        result = update_outcome("run-999", "ACT-999", 100)
        assert result is None

    def test_get_outcome(self):
        store_prediction("run-1", "ACT-001", "hormuz", 100)
        record = get_outcome("run-1", "ACT-001")
        assert record is not None
        assert record["predicted_value"] == 100

    def test_build_outcome_records_from_result(self, sample_result):
        records = build_outcome_records("run-test", sample_result)
        assert len(records) == 3  # 3 actions in sample
        for r in records:
            assert r["status"] == "PENDING"
            assert r["predicted_value"] > 0

    def test_outcome_record_has_timestamp(self):
        record = store_prediction("run-1", "ACT-001", "hormuz", 100)
        assert "timestamp" in record
        assert "T" in record["timestamp"]  # ISO format


# ═══════════════════════════════════════════════════════════════════════════════
# Test 4: Trust Memory
# ═══════════════════════════════════════════════════════════════════════════════

class TestTrustMemory:
    def test_trust_memory_updates_after_confirmed_outcome(self):
        store_prediction("run-1", "ACT-001", "hormuz", 1_000_000_000)
        update_outcome("run-1", "ACT-001", 950_000_000, "CONFIRMED")

        memories = get_all_trust_memories()
        assert len(memories) == 1
        mem = list(memories.values())[0]
        assert mem["total_runs"] == 1
        assert mem["success_count"] == 1  # deviation 5% < 25% threshold

    def test_failed_outcome_counts_as_failure(self):
        store_prediction("run-1", "ACT-001", "hormuz", 1_000_000_000)
        update_outcome("run-1", "ACT-001", 400_000_000, "CONFIRMED")

        memories = get_all_trust_memories()
        mem = list(memories.values())[0]
        assert mem["failure_count"] == 1  # deviation 60% > 25% threshold

    def test_trust_score_perfect_history(self):
        """Perfect predictions → high trust score."""
        for i in range(5):
            store_prediction(f"run-{i}", f"ACT-00{i}", "hormuz", 1_000_000_000)
            update_outcome(f"run-{i}", f"ACT-00{i}", 1_000_000_000, "CONFIRMED")

        memories = get_all_trust_memories()
        mem = list(memories.values())[0]
        assert mem["trust_score"] >= 90  # 60% success + 40% accuracy

    def test_trust_score_poor_history(self):
        """All failures → low trust score."""
        for i in range(5):
            store_prediction(f"run-{i}", f"ACT-00{i}", "hormuz", 1_000_000_000)
            update_outcome(f"run-{i}", f"ACT-00{i}", 200_000_000, "CONFIRMED")

        memories = get_all_trust_memories()
        mem = list(memories.values())[0]
        assert mem["trust_score"] <= 30

    def test_build_trust_memories_returns_defaults_for_new_actions(self, sample_result):
        memories = build_trust_memories_for_run(sample_result)
        assert len(memories) == 3
        for m in memories:
            assert m["total_runs"] == 0
            assert m["trust_score"] == 50  # neutral default

    def test_trust_memory_accumulates_across_runs(self):
        """Multiple runs update the same template key."""
        store_prediction("run-1", "ACT-001", "hormuz", 1000)
        update_outcome("run-1", "ACT-001", 1000, "CONFIRMED")

        store_prediction("run-2", "ACT-002", "hormuz", 1000)
        update_outcome("run-2", "ACT-002", 500, "CONFIRMED")

        memories = get_all_trust_memories()
        # Both ACT-001 and ACT-002 share prefix "ACT" + scenario
        mem = list(memories.values())[0]
        assert mem["total_runs"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5: Confidence Adjustment
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceAdjustment:
    def test_no_history_returns_base(self):
        adj, reason = adjust_confidence(75, 50, 0)
        assert adj == 75
        assert "base confidence unchanged" in reason.lower()

    def test_good_trust_boosts(self):
        adj, reason = adjust_confidence(75, 85, 5)
        assert adj > 75
        assert "boost" in reason.lower()

    def test_poor_trust_reduces(self):
        adj, reason = adjust_confidence(75, 30, 5)
        assert adj < 75
        assert "reduced" in reason.lower()

    def test_limited_history_half_weight(self):
        """< 3 runs → half-weight adjustment."""
        adj_few, _ = adjust_confidence(75, 30, 2)
        adj_many, _ = adjust_confidence(75, 30, 5)
        # Few runs should have smaller penalty
        assert adj_few > adj_many

    def test_confidence_clamped_5_to_99(self):
        adj_low, _ = adjust_confidence(5, 10, 10)
        assert adj_low >= 5
        adj_high, _ = adjust_confidence(99, 90, 10)
        assert adj_high <= 99

    def test_build_adjustments_from_explanations(self, sample_result):
        from src.engines.explanation_engine import generate_explanations
        explanations = generate_explanations(sample_result)
        memories = build_trust_memories_for_run(sample_result)
        adjustments = build_confidence_adjustments(explanations, memories)
        assert len(adjustments) == len(explanations)
        for adj in adjustments:
            assert "metric_id" in adj
            assert "original_confidence" in adj
            assert "adjusted_confidence" in adj
            assert "adjustment_reason" in adj

    def test_confidence_adjusts_after_bad_history(self, sample_result):
        """After storing bad outcomes, confidence should adjust down."""
        from src.engines.explanation_engine import generate_explanations

        # Build bad history
        for i in range(4):
            store_prediction(f"run-{i}", f"ACT-00{i}", "hormuz_chokepoint_disruption", 1_000_000_000)
            update_outcome(f"run-{i}", f"ACT-00{i}", 200_000_000, "CONFIRMED")

        explanations = generate_explanations(sample_result)
        memories = build_trust_memories_for_run(sample_result)
        adjustments = build_confidence_adjustments(explanations, memories)

        # At least some adjustments should be lower
        reduced = [a for a in adjustments if a["adjusted_confidence"] < a["original_confidence"]]
        assert len(reduced) > 0, "Bad history should reduce at least some confidences"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 6: Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestReliabilityIntegration:
    def test_all_range_ids_match_sensitivity_ids(self, sample_result):
        """Ranges and sensitivities should overlap on key metrics."""
        ranges = generate_ranges(sample_result)
        sensitivities = generate_sensitivities(sample_result)

        range_ids = {r["metric_id"] for r in ranges}
        sens_ids = {s["metric_id"] for s in sensitivities}

        # projected_loss and unified_risk_score must be in both
        assert "projected_loss" in range_ids & sens_ids
        assert "unified_risk_score" in range_ids & sens_ids

    def test_outcome_records_match_actions(self, sample_result):
        records = build_outcome_records("run-int", sample_result)
        action_ids = [a["action_id"] for a in sample_result["decision_plan"]["actions"]]
        record_ids = [r["action_id"] for r in records]
        assert set(record_ids) == set(action_ids)

    def test_full_pipeline_produces_complete_payload(self, sample_result):
        """Simulate the full pipeline: explanations → ranges → sensitivities → outcomes → trust → adjustment."""
        from src.engines.explanation_engine import generate_explanations
        from src.engines.decision_transparency_engine import compute_all_transparencies

        # Sprint 1
        explanations = generate_explanations(sample_result)
        transparency = compute_all_transparencies(sample_result)

        # Sprint 2
        ranges = generate_ranges(sample_result)
        sensitivities = generate_sensitivities(sample_result)
        outcomes = build_outcome_records("run-full", sample_result)
        trust_memories = build_trust_memories_for_run(sample_result)
        adjustments = build_confidence_adjustments(explanations, trust_memories)

        # Assemble payload
        payload = {
            "ranges": ranges,
            "sensitivities": sensitivities,
            "outcome_records": outcomes,
            "trust_memories": trust_memories,
            "confidence_adjustments": adjustments,
        }

        assert len(payload["ranges"]) >= 7
        assert len(payload["sensitivities"]) >= 5
        assert len(payload["outcome_records"]) == 3
        assert len(payload["trust_memories"]) == 3
        assert len(payload["confidence_adjustments"]) == len(explanations)

    def test_graceful_with_minimal_result(self):
        minimal = {"scenario_id": "test", "severity": 0.5}
        ranges = generate_ranges(minimal)
        sensitivities = generate_sensitivities(minimal)
        outcomes = build_outcome_records("run-min", minimal)
        assert isinstance(ranges, list)
        assert isinstance(sensitivities, list)
        assert isinstance(outcomes, list)
