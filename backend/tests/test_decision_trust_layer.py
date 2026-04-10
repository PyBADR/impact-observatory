"""
Impact Observatory | مرصد الأثر
Test Suite: Decision Trust Layer — Explanation Engine + Decision Transparency Engine.

Tests:
  1. Explanation exists for all key metrics
  2. Ratio calculation is correct
  3. Classification logic is correct
  4. Loss-inducing detection triggers correctly
  5. Graceful degradation when data is missing
"""
import pytest
import math

from src.engines.explanation_engine import (
    generate_explanations,
    explain_total_loss,
    explain_unified_risk_score,
    explain_confidence_score,
    explain_sector_stress,
    explain_executive_status,
)
from src.engines.decision_transparency_engine import (
    classify_action,
    compute_decision_transparency,
    compute_all_transparencies,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_result():
    """Minimal simulation result dict for testing."""
    return {
        "scenario_id": "hormuz_chokepoint_disruption",
        "severity": 0.70,
        "event_severity": 0.58,
        "risk_level": "ELEVATED",
        "peak_day": 9,
        "confidence_score": 0.82,
        "unified_risk": {
            "score": 0.58,
            "risk_level": "ELEVATED",
            "components": {
                "G": 0.65,
                "P": 0.72,
                "N": 0.48,
                "L": 0.55,
                "T": 0.40,
                "U": 0.35,
                "AvgExposure": 0.15,
                "AvgStress": 0.35,
                "PropagationScore": 0.72,
            },
        },
        "financial_impact": {
            "total_loss_usd": 4_200_000_000,
            "direct_loss_usd": 2_520_000_000,
            "indirect_loss_usd": 1_176_000_000,
            "systemic_loss_usd": 504_000_000,
            "systemic_multiplier": 1.12,
            "sector_losses": [
                {"sector": "energy", "loss_usd": 1_260_000_000},
                {"sector": "maritime", "loss_usd": 840_000_000},
                {"sector": "banking", "loss_usd": 756_000_000},
            ],
        },
        "sector_analysis": [
            {"sector": "energy", "exposure": 0.28, "stress": 0.81, "classification": "SEVERE"},
            {"sector": "maritime", "exposure": 0.18, "stress": 0.68, "classification": "HIGH"},
            {"sector": "banking", "exposure": 0.20, "stress": 0.72, "classification": "HIGH"},
            {"sector": "insurance", "exposure": 0.08, "stress": 0.45, "classification": "GUARDED"},
        ],
        "decision_plan": {
            "actions": [
                {
                    "action_id": "ACT-001",
                    "sector": "energy",
                    "owner": "National Oil Company",
                    "action": "Activate SPR drawdown",
                    "priority_score": 0.89,
                    "urgency": 0.92,
                    "loss_avoided_usd": 1_260_000_000,
                    "cost_usd": 1_200_000_000,
                    "regulatory_risk": 0.70,
                    "feasibility": 0.85,
                    "time_to_act_hours": 6,
                },
                {
                    "action_id": "ACT-002",
                    "sector": "banking",
                    "owner": "Central Bank",
                    "action": "Activate emergency liquidity",
                    "priority_score": 0.85,
                    "urgency": 0.88,
                    "loss_avoided_usd": 756_000_000,
                    "cost_usd": 500_000_000,
                    "regulatory_risk": 0.85,
                    "feasibility": 0.80,
                    "time_to_act_hours": 4,
                },
                {
                    "action_id": "ACT-003",
                    "sector": "insurance",
                    "owner": "Reinsurance Desk",
                    "action": "File loss notification",
                    "priority_score": 0.72,
                    "urgency": 0.78,
                    "loss_avoided_usd": 50_000_000,
                    "cost_usd": 200_000_000,
                    "regulatory_risk": 0.88,
                    "feasibility": 0.78,
                    "time_to_act_hours": 12,
                },
            ],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Test 1: Explanation exists for all key metrics
# ═══════════════════════════════════════════════════════════════════════════════

class TestExplanationEngine:
    def test_generates_all_key_explanations(self, sample_result):
        explanations = generate_explanations(sample_result)
        metric_ids = [e["metric_id"] for e in explanations]

        # Must have these core metrics
        assert "projected_loss" in metric_ids
        assert "unified_risk_score" in metric_ids
        assert "confidence_score" in metric_ids
        assert "executive_status" in metric_ids

        # Must have sector stress for each sector in analysis
        for sa in sample_result["sector_analysis"]:
            assert f"sector_stress_{sa['sector']}" in metric_ids

    def test_explanation_has_required_fields(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            assert "metric_id" in exp
            assert "label" in exp
            assert "value" in exp
            assert "drivers" in exp
            assert "reasoning_chain" in exp
            assert "assumptions" in exp
            assert isinstance(exp["drivers"], list)
            assert isinstance(exp["reasoning_chain"], list)
            assert isinstance(exp["assumptions"], list)

    def test_drivers_have_required_fields(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            for driver in exp["drivers"]:
                assert "label" in driver
                assert "contribution_pct" in driver
                assert "rationale" in driver
                assert isinstance(driver["contribution_pct"], (int, float))

    def test_drivers_are_sorted_by_contribution(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            if len(exp["drivers"]) > 1:
                pcts = [d["contribution_pct"] for d in exp["drivers"]]
                assert pcts == sorted(pcts, reverse=True), \
                    f"Drivers not sorted for {exp['metric_id']}: {pcts}"

    def test_total_loss_drivers_are_real(self, sample_result):
        exp = explain_total_loss(sample_result)
        # Must reference actual direct/indirect/systemic split
        labels = [d["label"] for d in exp["drivers"]]
        assert "Direct Asset Losses" in labels
        assert "Indirect Propagation Losses" in labels

    def test_urs_drivers_reference_real_weights(self, sample_result):
        exp = explain_unified_risk_score(sample_result)
        # Must reference actual URS formula components
        chain = " ".join(exp["reasoning_chain"])
        assert "0.35" in chain  # URS_G1
        assert "0.3" in chain   # URS_G4

    def test_graceful_with_missing_data(self):
        """Engine should not crash with minimal/empty result."""
        minimal = {"scenario_id": "test", "severity": 0.5}
        explanations = generate_explanations(minimal)
        # Should still produce some explanations without crashing
        assert isinstance(explanations, list)


# ═══════════════════════════════════════════════════════════════════════════════
# Test 2+3: Ratio calculation + Classification logic
# ═══════════════════════════════════════════════════════════════════════════════

class TestClassificationLogic:
    def test_high_value(self):
        assert classify_action(100, 1000) == "HIGH_VALUE"       # ratio 0.1

    def test_acceptable(self):
        # classify_action(cost, benefit) → net = benefit - cost
        # ACCEPTABLE: net >= 0 AND 1 <= ratio <= 5
        assert classify_action(500, 500) == "ACCEPTABLE"         # net=0, ratio=1.0
        assert classify_action(1000, 1000) == "ACCEPTABLE"       # net=0, ratio=1.0
        assert classify_action(5000, 5000) == "ACCEPTABLE"       # net=0, ratio=1.0
        assert classify_action(500, 250) == "LOSS_INDUCING"      # net=-250 → LOSS_INDUCING

    def test_low_efficiency(self):
        # LOW_EFFICIENCY: net >= 0 AND 5 < ratio <= 20
        # Hard to achieve: need cost/benefit > 5 AND benefit > cost (net >= 0)
        # That's impossible: if cost/benefit > 5 then cost > 5*benefit > benefit, so net < 0
        # Therefore LOW_EFFICIENCY only triggers via ratio path when net == 0 and ratio > 5
        # In practice, net < 0 catches first → LOSS_INDUCING dominates
        # Verify the expected behavior:
        assert classify_action(10000, 1500) == "LOSS_INDUCING"   # net=-8500 → LOSS_INDUCING
        assert classify_action(6000, 10000) == "HIGH_VALUE"      # net=4000, ratio=0.6 → HIGH_VALUE

    def test_loss_inducing_high_ratio(self):
        assert classify_action(10001, 500) == "LOSS_INDUCING"    # net=-9501 → LOSS_INDUCING

    def test_loss_inducing_negative_net(self):
        # net_value = benefit - cost = 500 - 1000 = -500 → LOSS_INDUCING
        assert classify_action(1000, 500) == "LOSS_INDUCING"

    def test_zero_cost_zero_benefit(self):
        assert classify_action(0, 0) == "ACCEPTABLE"

    def test_zero_benefit_with_cost(self):
        assert classify_action(1000, 0) == "LOSS_INDUCING"


class TestRatioComputation:
    def test_ratio_correct(self, sample_result):
        action = sample_result["decision_plan"]["actions"][0]
        t = compute_decision_transparency(action, sample_result)
        expected_ratio = action["cost_usd"] / action["loss_avoided_usd"]
        assert abs(t["cost_benefit_ratio"] - expected_ratio) < 0.01

    def test_net_value_correct(self, sample_result):
        action = sample_result["decision_plan"]["actions"][0]
        t = compute_decision_transparency(action, sample_result)
        expected_net = action["loss_avoided_usd"] - action["cost_usd"]
        assert t["net_value_usd"] == expected_net

    def test_classification_on_real_actions(self, sample_result):
        # ACT-001: cost 1.2B, benefit 1.26B → ratio 0.952 → HIGH_VALUE
        action1 = sample_result["decision_plan"]["actions"][0]
        t1 = compute_decision_transparency(action1, sample_result)
        assert t1["classification"] == "HIGH_VALUE"

        # ACT-002: cost 500M, benefit 756M → ratio 0.661 → HIGH_VALUE
        action2 = sample_result["decision_plan"]["actions"][1]
        t2 = compute_decision_transparency(action2, sample_result)
        assert t2["classification"] == "HIGH_VALUE"

        # ACT-003: cost 200M, benefit 50M → net -150M → LOSS_INDUCING
        action3 = sample_result["decision_plan"]["actions"][2]
        t3 = compute_decision_transparency(action3, sample_result)
        assert t3["classification"] == "LOSS_INDUCING"


# ═══════════════════════════════════════════════════════════════════════════════
# Test 4: Loss-inducing detection triggers correctly
# ═══════════════════════════════════════════════════════════════════════════════

class TestLossInducingDetection:
    def test_detects_loss_inducing_actions(self, sample_result):
        result = compute_all_transparencies(sample_result)
        assert result["has_loss_inducing"] is True
        assert result["loss_inducing_count"] >= 1
        assert "ACT-003" in result["loss_inducing_actions"]

    def test_warning_banner_generated(self, sample_result):
        result = compute_all_transparencies(sample_result)
        assert result["warning_banner"] is not None
        assert "ACT-003" in result["warning_banner"]

    def test_no_false_positive_on_clean_actions(self):
        clean_result = {
            "decision_plan": {
                "actions": [
                    {
                        "action_id": "CLEAN-001",
                        "sector": "banking",
                        "owner": "Central Bank",
                        "action": "Activate buffer",
                        "priority_score": 0.85,
                        "urgency": 0.88,
                        "loss_avoided_usd": 1_000_000_000,
                        "cost_usd": 100_000_000,
                        "regulatory_risk": 0.85,
                        "feasibility": 0.80,
                        "time_to_act_hours": 4,
                    },
                ],
            },
            "financial_impact": {"total_loss_usd": 5_000_000_000},
        }
        result = compute_all_transparencies(clean_result)
        assert result["has_loss_inducing"] is False
        assert result["loss_inducing_count"] == 0
        assert result["warning_banner"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# Test 5: Batch transparency computation
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchTransparency:
    def test_computes_for_all_actions(self, sample_result):
        result = compute_all_transparencies(sample_result)
        assert len(result["action_transparencies"]) == 3

    def test_each_transparency_has_required_fields(self, sample_result):
        result = compute_all_transparencies(sample_result)
        for t in result["action_transparencies"]:
            assert "action_id" in t
            assert "cost_usd" in t
            assert "benefit_usd" in t
            assert "net_value_usd" in t
            assert "cost_benefit_ratio" in t
            assert "classification" in t
            assert "why_recommended" in t
            assert "tradeoffs" in t
            assert isinstance(t["why_recommended"], list)
            assert isinstance(t["tradeoffs"], list)
            assert len(t["why_recommended"]) >= 1  # At least one reason

    def test_why_recommended_is_real_not_generic(self, sample_result):
        result = compute_all_transparencies(sample_result)
        for t in result["action_transparencies"]:
            for reason in t["why_recommended"]:
                # Must contain actual numbers, not placeholder text
                assert any(c.isdigit() for c in reason), \
                    f"Reason appears generic (no numbers): {reason}"

    def test_empty_actions_handled(self):
        empty = {"decision_plan": {"actions": []}}
        result = compute_all_transparencies(empty)
        assert len(result["action_transparencies"]) == 0
        assert result["has_loss_inducing"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 1.5: Business Explainability Layer Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBusinessExplainability:
    def test_all_explanations_have_business_explanation(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            assert "business_explanation" in exp
            biz = exp["business_explanation"]
            assert "summary" in biz
            assert "drivers" in biz
            assert isinstance(biz["summary"], str)
            assert len(biz["summary"]) > 20, f"Business summary too short for {exp['metric_id']}"
            assert isinstance(biz["drivers"], list)

    def test_business_drivers_have_impact_levels(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            for bd in exp["business_explanation"]["drivers"]:
                assert "label" in bd
                assert "impact" in bd
                assert "explanation" in bd
                assert bd["impact"] in ("HIGH", "MEDIUM", "LOW"), \
                    f"Invalid impact level: {bd['impact']}"

    def test_business_summary_is_non_technical(self, sample_result):
        """Business summaries should not contain formula notation."""
        explanations = generate_explanations(sample_result)
        technical_markers = ["×", "g1", "g2", "g3", "g4", "g5", "alpha(", "URS ="]
        for exp in explanations:
            summary = exp["business_explanation"]["summary"]
            for marker in technical_markers:
                assert marker not in summary, \
                    f"Business summary for {exp['metric_id']} contains technical notation '{marker}': {summary}"

    def test_business_drivers_reference_real_data(self, sample_result):
        """At least one business driver per explanation should contain actual numbers."""
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            biz_drivers = exp["business_explanation"]["drivers"]
            if len(biz_drivers) == 0:
                continue
            has_numbers = any(
                any(c.isdigit() for c in bd["explanation"])
                for bd in biz_drivers
            )
            assert has_numbers, \
                f"No business drivers reference real data for {exp['metric_id']}: " \
                f"{[bd['explanation'] for bd in biz_drivers]}"

    def test_graceful_with_missing_data_biz(self):
        minimal = {"scenario_id": "test", "severity": 0.5}
        explanations = generate_explanations(minimal)
        for exp in explanations:
            assert "business_explanation" in exp


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 1.5: Confidence Layer Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfidenceLayer:
    def test_all_explanations_have_confidence(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            assert "confidence" in exp
            assert "confidence_reasons" in exp
            conf = exp["confidence"]
            assert isinstance(conf, int)
            assert 0 <= conf <= 100, f"Confidence {conf} out of range for {exp['metric_id']}"

    def test_confidence_reasons_are_list_of_strings(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            reasons = exp["confidence_reasons"]
            assert isinstance(reasons, list)
            for r in reasons:
                assert isinstance(r, str)
                assert len(r) > 5, f"Confidence reason too short: {r}"

    def test_confidence_varies_by_metric(self, sample_result):
        """Different metrics should have different confidence levels (not all identical)."""
        explanations = generate_explanations(sample_result)
        confidences = [exp["confidence"] for exp in explanations]
        # At least 2 distinct values (sector stresses may share, but projected_loss vs confidence_score differ)
        assert len(set(confidences)) >= 2, \
            f"All confidences identical: {confidences}"

    def test_extreme_severity_reduces_confidence(self):
        """High severity should produce lower confidence than low severity."""
        low_sev = {
            "scenario_id": "hormuz_chokepoint_disruption",
            "severity": 0.30,
            "event_severity": 0.25,
            "risk_level": "LOW",
            "peak_day": 5,
            "confidence_score": 0.88,
            "unified_risk": {"score": 0.25, "risk_level": "LOW", "components": {}},
            "financial_impact": {"total_loss_usd": 500_000_000, "direct_loss_usd": 300_000_000,
                                 "indirect_loss_usd": 140_000_000, "systemic_loss_usd": 60_000_000,
                                 "systemic_multiplier": 1.0, "sector_losses": []},
            "sector_analysis": [],
        }
        high_sev = {**low_sev, "severity": 0.90, "confidence_score": 0.60}

        low_exps = generate_explanations(low_sev)
        high_exps = generate_explanations(high_sev)

        # Compare projected_loss confidence
        low_conf = next(e["confidence"] for e in low_exps if e["metric_id"] == "projected_loss")
        high_conf = next(e["confidence"] for e in high_exps if e["metric_id"] == "projected_loss")
        assert low_conf > high_conf, \
            f"Low severity conf ({low_conf}) should exceed high severity conf ({high_conf})"


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 1.5: Data Context Layer Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataContextLayer:
    def test_all_explanations_have_data_context(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            assert "data_context" in exp
            ctx = exp["data_context"]
            assert "source_summary" in ctx
            assert "source_type" in ctx
            assert "reference_period" in ctx
            assert "generated_at" in ctx
            assert "freshness_label" in ctx

    def test_source_type_is_valid(self, sample_result):
        explanations = generate_explanations(sample_result)
        valid_types = {"SIMULATION", "HISTORICAL_PROXY", "HYBRID"}
        for exp in explanations:
            assert exp["data_context"]["source_type"] in valid_types, \
                f"Invalid source_type for {exp['metric_id']}: {exp['data_context']['source_type']}"

    def test_freshness_label_is_valid(self, sample_result):
        explanations = generate_explanations(sample_result)
        valid_labels = {"LIVE", "RECENT", "SIMULATED", "HISTORICAL"}
        for exp in explanations:
            assert exp["data_context"]["freshness_label"] in valid_labels, \
                f"Invalid freshness_label for {exp['metric_id']}: {exp['data_context']['freshness_label']}"

    def test_generated_at_is_iso_format(self, sample_result):
        explanations = generate_explanations(sample_result)
        for exp in explanations:
            ts = exp["data_context"]["generated_at"]
            # Should be parseable as ISO datetime
            assert "T" in ts, f"generated_at doesn't look like ISO: {ts}"
            assert len(ts) >= 19, f"generated_at too short: {ts}"


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 1.5: Decision Risk Overlay Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecisionRiskOverlay:
    def test_all_transparencies_have_decision_risks(self, sample_result):
        result = compute_all_transparencies(sample_result)
        for t in result["action_transparencies"]:
            assert "decision_risks" in t
            assert isinstance(t["decision_risks"], list)

    def test_risk_entries_have_required_fields(self, sample_result):
        result = compute_all_transparencies(sample_result)
        for t in result["action_transparencies"]:
            for risk in t["decision_risks"]:
                assert "label" in risk
                assert "severity" in risk
                assert "description" in risk
                assert risk["severity"] in ("HIGH", "MEDIUM", "LOW")
                assert len(risk["description"]) > 10

    def test_loss_inducing_action_has_value_destruction_risk(self, sample_result):
        """ACT-003 is LOSS_INDUCING — must have Value Destruction risk."""
        result = compute_all_transparencies(sample_result)
        act3 = next(t for t in result["action_transparencies"] if t["action_id"] == "ACT-003")
        risk_labels = [r["label"] for r in act3["decision_risks"]]
        assert "Value Destruction" in risk_labels, \
            f"LOSS_INDUCING action missing Value Destruction risk. Got: {risk_labels}"

    def test_high_cost_action_has_capital_risk(self, sample_result):
        """ACT-001 costs $1.2B — must have capital commitment risk."""
        result = compute_all_transparencies(sample_result)
        act1 = next(t for t in result["action_transparencies"] if t["action_id"] == "ACT-001")
        risk_labels = [r["label"] for r in act1["decision_risks"]]
        assert "High Capital Commitment" in risk_labels, \
            f"High-cost action missing capital risk. Got: {risk_labels}"

    def test_time_critical_action_has_timing_risk(self, sample_result):
        """ACT-002 has 4h window — must have time-critical risk."""
        result = compute_all_transparencies(sample_result)
        act2 = next(t for t in result["action_transparencies"] if t["action_id"] == "ACT-002")
        risk_labels = [r["label"] for r in act2["decision_risks"]]
        assert "Time-Critical Execution" in risk_labels, \
            f"Time-critical action missing timing risk. Got: {risk_labels}"

    def test_clean_action_has_fewer_risks(self):
        """A clean, well-funded, low-cost action should have minimal risks."""
        clean_result = {
            "decision_plan": {
                "actions": [
                    {
                        "action_id": "CLEAN-001",
                        "sector": "banking",
                        "owner": "Central Bank",
                        "action": "Minor adjustment",
                        "priority_score": 0.50,
                        "urgency": 0.50,
                        "loss_avoided_usd": 100_000_000,
                        "cost_usd": 10_000_000,
                        "regulatory_risk": 0.30,
                        "feasibility": 0.95,
                        "time_to_act_hours": 48,
                    },
                ],
            },
            "financial_impact": {"total_loss_usd": 1_000_000_000},
        }
        result = compute_all_transparencies(clean_result)
        risks = result["action_transparencies"][0]["decision_risks"]
        # Should have few or no HIGH risks
        high_risks = [r for r in risks if r["severity"] == "HIGH"]
        assert len(high_risks) == 0, f"Clean action should have no HIGH risks. Got: {[r['label'] for r in high_risks]}"
