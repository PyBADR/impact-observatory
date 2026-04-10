"""
Impact Observatory | مرصد الأثر
Phase 2 Decision Trust System — Acceptance Tests

Tests cover:
  1. Action-Level Confidence Engine  → every action gets a score + label
  2. Model Dependency Engine         → completeness, reliability, sensitivity
  3. Validation Requirement Engine   → triggers when thresholds breached
  4. Confidence Breakdown Layer      → minimum 2 human-readable drivers
  5. Decision Risk Envelope          → downside, reversibility, time sensitivity
  6. Unified orchestrator            → all 5 outputs present and consistent
"""
from __future__ import annotations

import pytest

from src.engines.trust_engine import (
    compute_action_confidence,
    compute_model_dependency,
    compute_validation,
    build_confidence_breakdown,
    compute_risk_envelope,
    compute_decision_trust,
)
from src import config


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_actions():
    """Representative action list from SimulationEngine output."""
    return [
        {
            "id": "act_001",
            "label": "Activate force majeure clause on marine policies",
            "urgency": 0.90,
            "confidence": 0.85,
            "sector": "insurance",
            "reversibility": "LOW",
            "loss_avoided_usd": 350_000_000,
            "cost_usd": 15_000_000,
        },
        {
            "id": "act_002",
            "label": "Increase reinsurance reserves by 20%",
            "urgency": 0.60,
            "confidence": 0.78,
            "sector": "insurance",
            "reversibility": "HIGH",
            "loss_avoided_usd": 200_000_000,
            "cost_usd": 40_000_000,
        },
        {
            "id": "act_003",
            "label": "Halt new trade finance origination in Gulf corridor",
            "urgency": 0.75,
            "confidence": 0.70,
            "sector": "banking",
            "reversibility": "LOW",
            "loss_avoided_usd": 500_000_000,
            "cost_usd": 80_000_000,
        },
    ]


@pytest.fixture
def sample_action_pathways():
    return {
        "immediate": [
            {"id": "ap_1", "label": "Emergency action", "urgency": 0.95, "reversibility": "LOW"},
        ],
        "conditional": [
            {"id": "ap_2", "label": "Conditional step", "urgency": 0.55, "reversibility": "MEDIUM"},
        ],
        "strategic": [],
        "total_actions": 2,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Action-Level Confidence Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestActionConfidence:
    """AT-1: Every action has confidence."""

    def test_every_action_gets_confidence(self, sample_actions):
        result = compute_action_confidence(
            actions=sample_actions,
            global_confidence=0.85,
            propagation_score=0.72,
            counterfactual_consistency="CONSISTENT",
        )
        assert len(result) == len(sample_actions)
        for entry in result:
            assert "action_id" in entry
            assert "confidence_score" in entry
            assert "confidence_label" in entry
            assert 0.0 <= entry["confidence_score"] <= 1.0
            assert entry["confidence_label"] in ("HIGH", "MEDIUM", "LOW")

    def test_scores_bounded_zero_to_one(self, sample_actions):
        result = compute_action_confidence(
            actions=sample_actions,
            global_confidence=1.0,
            propagation_score=1.0,
        )
        for entry in result:
            assert 0.0 <= entry["confidence_score"] <= 1.0

    def test_severity_penalty_reduces_confidence(self, sample_actions):
        normal = compute_action_confidence(
            actions=sample_actions, severity=0.5, global_confidence=0.85,
        )
        extreme = compute_action_confidence(
            actions=sample_actions, severity=0.90, global_confidence=0.85,
        )
        for n, e in zip(normal, extreme):
            assert e["confidence_score"] <= n["confidence_score"]

    def test_empty_actions_returns_empty(self):
        result = compute_action_confidence(actions=[], global_confidence=0.85)
        assert result == []

    def test_malformed_actions_skipped(self):
        result = compute_action_confidence(
            actions=[None, "bad", 42, {"id": "ok", "urgency": 0.5}],
            global_confidence=0.85,
        )
        assert len(result) == 1
        assert result[0]["action_id"] == "ok"

    def test_counterfactual_inconsistency_lowers_score(self, sample_actions):
        consistent = compute_action_confidence(
            actions=sample_actions, counterfactual_consistency="CONSISTENT",
        )
        inconsistent = compute_action_confidence(
            actions=sample_actions, counterfactual_consistency="CORRECTED_INCONSISTENCY",
        )
        for c, i in zip(consistent, inconsistent):
            assert i["confidence_score"] <= c["confidence_score"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Model Dependency Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestModelDependency:
    """AT-2: Model dependency metrics are complete."""

    def test_returns_all_fields(self):
        result = compute_model_dependency(
            sectors_affected=["energy", "banking"],
            severity=0.65,
            propagation_score=0.70,
            global_confidence=0.85,
        )
        assert "data_completeness" in result
        assert "signal_reliability" in result
        assert "assumption_sensitivity" in result

    def test_data_completeness_bounded(self):
        result = compute_model_dependency(
            sectors_affected=["energy"],
            severity=0.95,
            global_confidence=0.85,
        )
        assert 0.0 <= result["data_completeness"] <= 1.0

    def test_signal_reliability_bounded(self):
        result = compute_model_dependency(
            propagation_score=0.8,
            global_confidence=0.9,
        )
        assert 0.0 <= result["signal_reliability"] <= 1.0

    def test_sensitivity_high_for_extreme_severity(self):
        result = compute_model_dependency(severity=0.80, sectors_affected=["energy", "banking", "insurance", "fintech", "maritime"])
        assert result["assumption_sensitivity"] == "HIGH"

    def test_sensitivity_low_for_mild(self):
        result = compute_model_dependency(severity=0.20, sectors_affected=["energy"])
        assert result["assumption_sensitivity"] == "LOW"

    def test_high_severity_degrades_completeness(self):
        mild = compute_model_dependency(sectors_affected=["energy"], severity=0.30)
        extreme = compute_model_dependency(sectors_affected=["energy"], severity=0.90)
        assert extreme["data_completeness"] < mild["data_completeness"]

    def test_no_sectors_fallback(self):
        result = compute_model_dependency(sectors_affected=[])
        assert result["data_completeness"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Validation Requirement Engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidation:
    """AT-3: Validation returned with correct triggers."""

    def test_returns_all_fields(self):
        result = compute_validation(global_confidence=0.85, total_loss_usd=100_000)
        assert "required" in result
        assert "reason" in result
        assert "validation_type" in result

    def test_not_required_for_safe_scenario(self):
        result = compute_validation(
            global_confidence=0.90,
            total_loss_usd=10_000,
            data_completeness=0.85,
            risk_level="LOW",
            severity=0.20,
        )
        assert result["required"] is False
        assert result["validation_type"] == "NONE"

    def test_low_confidence_triggers_validation(self):
        result = compute_validation(
            global_confidence=0.30,
            total_loss_usd=100_000,
        )
        assert result["required"] is True
        assert "confidence" in result["reason"].lower()

    def test_high_loss_triggers_validation(self):
        result = compute_validation(
            global_confidence=0.85,
            total_loss_usd=2_000_000_000,
        )
        assert result["required"] is True

    def test_high_risk_triggers_regulatory(self):
        result = compute_validation(
            global_confidence=0.85,
            risk_level="SEVERE",
        )
        assert result["required"] is True
        assert result["validation_type"] == "REGULATORY"

    def test_extreme_severity_triggers_board_validation(self):
        result = compute_validation(
            global_confidence=0.85,
            severity=0.90,
        )
        assert result["required"] is True
        assert "board" in result["reason"].lower()

    def test_low_data_triggers_validation(self):
        result = compute_validation(
            global_confidence=0.85,
            data_completeness=0.40,
        )
        assert result["required"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Confidence Breakdown Layer
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceBreakdown:
    """AT-4: Confidence explained — minimum 2 drivers."""

    def test_minimum_two_drivers(self):
        result = build_confidence_breakdown(
            global_confidence=0.85,
            data_completeness=0.80,
            signal_reliability=0.85,
        )
        assert "drivers" in result
        assert len(result["drivers"]) >= 2

    def test_drivers_are_strings(self):
        result = build_confidence_breakdown(global_confidence=0.85)
        for d in result["drivers"]:
            assert isinstance(d, str)
            assert len(d) > 10  # meaningful sentences, not empty

    def test_extreme_severity_adds_driver(self):
        mild = build_confidence_breakdown(severity=0.30)
        extreme = build_confidence_breakdown(severity=0.85)
        assert len(extreme["drivers"]) >= len(mild["drivers"])

    def test_high_risk_adds_driver(self):
        low_risk = build_confidence_breakdown(risk_level="LOW")
        high_risk = build_confidence_breakdown(risk_level="SEVERE")
        assert len(high_risk["drivers"]) >= len(low_risk["drivers"])

    def test_weak_sectors_mentioned(self):
        result = build_confidence_breakdown(
            global_confidence=0.85,
            data_completeness=0.62,
            sectors_affected=["fintech", "healthcare"],
        )
        drivers_text = " ".join(result["drivers"]).lower()
        # fintech and healthcare have low completeness in config
        assert "fintech" in drivers_text or "healthcare" in drivers_text or "limited" in drivers_text


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Decision Risk Envelope
# ═══════════════════════════════════════════════════════════════════════════════


class TestRiskEnvelope:
    """AT-5: Risk profile complete."""

    def test_returns_all_fields(self):
        result = compute_risk_envelope(total_loss_usd=100_000, severity=0.5)
        assert "downside_if_wrong" in result
        assert "reversibility" in result
        assert "time_sensitivity" in result

    def test_downside_high_for_large_loss(self):
        result = compute_risk_envelope(total_loss_usd=2_000_000_000)
        assert result["downside_if_wrong"] == "HIGH"

    def test_downside_low_for_small_loss(self):
        result = compute_risk_envelope(total_loss_usd=50_000, risk_level="LOW")
        assert result["downside_if_wrong"] == "LOW"

    def test_reversibility_low_with_irreversible_actions(self, sample_actions):
        result = compute_risk_envelope(
            actions=sample_actions,  # has 2 LOW-rev actions + "halt" keyword
            severity=0.75,
        )
        assert result["reversibility"] == "LOW"

    def test_time_critical_for_short_delay(self):
        result = compute_risk_envelope(total_delay_hours=6.0, severity=0.90)
        assert result["time_sensitivity"] == "CRITICAL"

    def test_time_low_for_long_delay_mild_severity(self):
        result = compute_risk_envelope(total_delay_hours=120.0, severity=0.30)
        assert result["time_sensitivity"] == "LOW"

    def test_valid_enum_values(self, sample_actions):
        result = compute_risk_envelope(
            total_loss_usd=500_000_000,
            actions=sample_actions,
            severity=0.65,
        )
        assert result["downside_if_wrong"] in ("LOW", "MEDIUM", "HIGH")
        assert result["reversibility"] in ("HIGH", "MEDIUM", "LOW")
        assert result["time_sensitivity"] in ("LOW", "MEDIUM", "CRITICAL")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Unified Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════


class TestDecisionTrustUnified:
    """AT-6: No contradiction between confidence and logic."""

    def test_all_five_outputs_present(self, sample_actions, sample_action_pathways):
        result = compute_decision_trust(
            actions=sample_actions,
            scenario_id="hormuz_chokepoint_disruption",
            severity=0.72,
            total_loss_usd=2_800_000_000,
            global_confidence=0.85,
            propagation_score=0.72,
            risk_level="HIGH",
            sectors_affected=["energy", "maritime", "banking", "insurance"],
            counterfactual_consistency="CONSISTENT",
            transmission_total_delay=18.0,
            action_pathways=sample_action_pathways,
        )
        assert "action_confidence" in result
        assert "model_dependency" in result
        assert "validation" in result
        assert "confidence_breakdown" in result
        assert "risk_profile" in result

    def test_action_confidence_count_matches(self, sample_actions):
        result = compute_decision_trust(
            actions=sample_actions,
            severity=0.50,
        )
        assert len(result["action_confidence"]) == len(sample_actions)

    def test_high_loss_triggers_both_validation_and_high_downside(self, sample_actions):
        result = compute_decision_trust(
            actions=sample_actions,
            total_loss_usd=5_000_000_000,
            risk_level="SEVERE",
            severity=0.90,
        )
        assert result["validation"]["required"] is True
        assert result["risk_profile"]["downside_if_wrong"] == "HIGH"

    def test_confidence_and_validation_consistent(self, sample_actions):
        """When confidence is low, validation must be required."""
        result = compute_decision_trust(
            actions=sample_actions,
            global_confidence=0.30,
            severity=0.85,
        )
        assert result["validation"]["required"] is True
        # All actions should have reduced confidence
        for ac in result["action_confidence"]:
            assert ac["confidence_score"] < 0.80

    def test_breakdown_has_minimum_drivers(self, sample_actions):
        result = compute_decision_trust(
            actions=sample_actions,
            severity=0.50,
        )
        assert len(result["confidence_breakdown"]["drivers"]) >= 2

    def test_empty_actions_still_produces_valid_trust(self):
        result = compute_decision_trust(
            actions=[],
            severity=0.50,
            total_loss_usd=100_000,
        )
        assert result["action_confidence"] == []
        assert result["model_dependency"]["data_completeness"] > 0
        assert result["confidence_breakdown"]["drivers"]
        assert result["risk_profile"]["downside_if_wrong"] in ("LOW", "MEDIUM", "HIGH")

    def test_safe_with_none_inputs(self):
        """Engine must not throw on None/missing optional inputs."""
        result = compute_decision_trust(
            actions=[{"id": "test_1"}],
            sectors_affected=None,
            counterfactual_consistency="UNKNOWN",
            action_pathways=None,
        )
        assert len(result["action_confidence"]) == 1
        assert result["model_dependency"] is not None
        assert result["risk_profile"] is not None
