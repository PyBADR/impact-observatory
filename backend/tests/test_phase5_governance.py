"""
Impact Observatory | مرصد الأثر
Phase 5 Evidence & Governance Layer — Acceptance Tests

Tests cover:
  1. Evidence Engine        → every decision has full evidence pack, no missing sections
  2. Policy Engine          → governance rules enforced, violations explained
  3. Attribution Defense    → defensible, never over-claimed, explanation present
  4. Override Engine        → overrides tracked, no override without reason
  5. Full pipeline          → all 4 outputs present, 36 stages, no regression
"""
from __future__ import annotations

import pytest

from src.engines.evidence_engine import build_decision_evidence, build_all_evidence
from src.engines.policy_engine import evaluate_policy, evaluate_all_policies
from src.engines.attribution_defense_engine import build_attribution_defense, build_all_attribution_defenses
from src.engines.override_engine import track_override, track_all_overrides


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_actions():
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
            "confidence": 0.70,
            "sector": "insurance",
            "reversibility": "MEDIUM",
            "loss_avoided_usd": 200_000_000,
            "cost_usd": 40_000_000,
        },
        {
            "id": "act_003",
            "label": "Deploy liquidity buffer for CBUAE compliance",
            "urgency": 0.80,
            "confidence": 0.90,
            "sector": "banking",
            "reversibility": "HIGH",
            "loss_avoided_usd": 500_000_000,
            "cost_usd": 25_000_000,
        },
    ]


@pytest.fixture
def sample_transmission_chain():
    return {
        "chain_length": 5,
        "total_delay": 48,
        "max_severity": 0.85,
        "breakable_points": [{"source": "a", "target": "b"}],
        "summary": "Oil → Finance → Insurance cascade",
    }


@pytest.fixture
def sample_counterfactual():
    return {
        "baseline": {"projected_loss_usd": 5_000_000_000},
        "recommended": {"projected_loss_usd": 2_000_000_000},
        "delta": {"loss_reduction_pct": 60},
        "consistency_flag": "CONSISTENT",
        "confidence_score": 0.85,
    }


@pytest.fixture
def sample_trust():
    return {
        "action_confidence": [
            {"action_id": "act_001", "confidence_score": 0.85, "confidence_label": "HIGH"},
            {"action_id": "act_002", "confidence_score": 0.70, "confidence_label": "MEDIUM"},
            {"action_id": "act_003", "confidence_score": 0.90, "confidence_label": "HIGH"},
        ],
        "model_dependency": {"data_completeness": 0.75, "signal_reliability": 0.80, "assumption_sensitivity": "LOW"},
        "validation": {"required": False, "reason": "", "validation_type": "NONE"},
        "risk_profile": {"downside_if_wrong": "MEDIUM", "reversibility": "MEDIUM", "time_sensitivity": "MEDIUM"},
    }


@pytest.fixture
def sample_ownerships():
    return [
        {"decision_id": "act_001", "owner_role": "CRO"},
        {"decision_id": "act_002", "owner_role": "CRO"},
        {"decision_id": "act_003", "owner_role": "TREASURY"},
    ]


@pytest.fixture
def sample_workflows():
    return [
        {"decision_id": "act_001", "status": "APPROVED", "approver_role": "CRO", "escalation_path": ["CRO", "CEO"]},
        {"decision_id": "act_002", "status": "PENDING", "approver_role": "CRO", "escalation_path": ["CRO"]},
        {"decision_id": "act_003", "status": "APPROVED", "approver_role": "TREASURY", "escalation_path": ["TREASURY", "CFO"]},
    ]


@pytest.fixture
def sample_value_attributions():
    return [
        {"decision_id": "act_001", "value_created": 500_000, "attribution_confidence": 0.85, "attribution_type": "DIRECT"},
        {"decision_id": "act_002", "value_created": 200_000, "attribution_confidence": 0.60, "attribution_type": "PARTIAL"},
        {"decision_id": "act_003", "value_created": 800_000, "attribution_confidence": 0.90, "attribution_type": "DIRECT"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Evidence Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvidenceEngine:
    """Every decision must have a full evidence pack with no missing sections."""

    def test_single_evidence_has_all_layers(self, sample_actions, sample_transmission_chain, sample_counterfactual, sample_trust):
        result = build_decision_evidence(
            sample_actions[0],
            transmission_chain=sample_transmission_chain,
            counterfactual=sample_counterfactual,
            trust=sample_trust,
            scenario_id="hormuz_chokepoint_disruption",
            severity=0.75,
            run_id="run_001",
        )
        assert "decision_id" in result
        assert "signal_snapshot" in result
        assert "transmission_evidence" in result
        assert "counterfactual_basis" in result
        assert "trust_basis" in result
        assert "execution_evidence" in result
        assert "outcome_evidence" in result
        assert "completeness" in result

    def test_evidence_decision_id_matches(self, sample_actions, sample_transmission_chain, sample_counterfactual, sample_trust):
        result = build_decision_evidence(
            sample_actions[0],
            transmission_chain=sample_transmission_chain,
            counterfactual=sample_counterfactual,
            trust=sample_trust,
        )
        assert result["decision_id"] == "act_001"

    def test_evidence_has_immutable_timestamp(self, sample_actions):
        result = build_decision_evidence(sample_actions[0], run_id="run_test")
        assert result["assembled_at"] != ""
        assert "T" in result["assembled_at"]  # ISO 8601

    def test_signal_snapshot_contains_scenario(self, sample_actions):
        result = build_decision_evidence(
            sample_actions[0],
            scenario_id="hormuz_full_closure",
            severity=0.9,
        )
        assert result["signal_snapshot"]["scenario_id"] == "hormuz_full_closure"
        assert result["signal_snapshot"]["severity"] == 0.9

    def test_completeness_flags_accurate(self, sample_actions, sample_transmission_chain, sample_counterfactual, sample_trust):
        result = build_decision_evidence(
            sample_actions[0],
            transmission_chain=sample_transmission_chain,
            counterfactual=sample_counterfactual,
            trust=sample_trust,
        )
        comp = result["completeness"]
        assert comp["has_signal"] is True
        assert comp["has_transmission"] is True
        assert comp["has_counterfactual"] is True
        assert comp["has_trust"] is True

    def test_missing_layers_flagged(self, sample_actions):
        result = build_decision_evidence(sample_actions[0])
        comp = result["completeness"]
        assert comp["has_transmission"] is False
        assert comp["has_counterfactual"] is False
        assert comp["complete"] is False

    def test_batch_returns_one_per_action(self, sample_actions, sample_transmission_chain, sample_counterfactual, sample_trust):
        results = build_all_evidence(
            sample_actions,
            transmission_chain=sample_transmission_chain,
            counterfactual=sample_counterfactual,
            trust=sample_trust,
        )
        assert len(results) == 3
        ids = {r["decision_id"] for r in results}
        assert ids == {"act_001", "act_002", "act_003"}

    def test_empty_actions_returns_empty(self):
        results = build_all_evidence([])
        assert results == []


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Policy Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolicyEngine:
    """Every decision must be evaluated, violations always explained."""

    def test_single_policy_returns_all_fields(self, sample_actions, sample_trust):
        result = evaluate_policy(
            sample_actions[0],
            trust=sample_trust,
            scenario_id="hormuz_chokepoint_disruption",
        )
        assert "decision_id" in result
        assert "allowed" in result
        assert "violations" in result
        assert "required_approvals" in result
        assert "rules_evaluated" in result
        assert "rules_passed" in result

    def test_regulatory_scenario_requires_approval(self, sample_actions, sample_trust):
        result = evaluate_policy(
            sample_actions[0],
            trust=sample_trust,
            scenario_id="uae_banking_crisis",
        )
        assert result["allowed"] is False
        assert any("regulator" in v.lower() for v in result["violations"])
        assert "REGULATOR" in result["required_approvals"]

    def test_non_regulatory_scenario_allowed(self, sample_actions, sample_trust):
        result = evaluate_policy(
            sample_actions[2],  # HIGH reversibility, banking, good confidence
            trust=sample_trust,
            scenario_id="hormuz_chokepoint_disruption",
            risk_level="MODERATE",
        )
        assert result["allowed"] is True
        assert len(result["violations"]) == 0

    def test_irreversible_action_needs_multi_approval(self, sample_actions, sample_trust, sample_ownerships):
        result = evaluate_policy(
            sample_actions[0],  # reversibility=LOW
            trust=sample_trust,
            ownership=sample_ownerships[0],
            scenario_id="hormuz_chokepoint_disruption",
        )
        assert any("irreversible" in v.lower() for v in result["violations"])
        assert "CRO" in result["required_approvals"]

    def test_severe_risk_requires_board(self, sample_actions, sample_trust):
        result = evaluate_policy(
            sample_actions[0],
            trust=sample_trust,
            scenario_id="hormuz_chokepoint_disruption",
            risk_level="SEVERE",
        )
        assert any("board" in v.lower() or "severe" in v.lower() for v in result["violations"])
        assert "CEO" in result["required_approvals"]

    def test_rules_evaluated_is_positive(self, sample_actions, sample_trust):
        result = evaluate_policy(sample_actions[0], trust=sample_trust)
        assert result["rules_evaluated"] >= 5

    def test_batch_returns_one_per_action(self, sample_actions, sample_trust, sample_ownerships):
        results = evaluate_all_policies(
            sample_actions,
            trust=sample_trust,
            ownerships=sample_ownerships,
            scenario_id="hormuz_chokepoint_disruption",
        )
        assert len(results) == 3

    def test_no_silent_failures(self, sample_actions, sample_trust):
        """Every decision must have a definitive allowed/blocked status."""
        results = evaluate_all_policies(sample_actions, trust=sample_trust)
        for r in results:
            assert isinstance(r["allowed"], bool)
            if not r["allowed"]:
                assert len(r["violations"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Attribution Defense Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestAttributionDefenseEngine:
    """Attribution defensible, never over-claimed, explanation always present."""

    def test_single_defense_returns_all_fields(self, sample_value_attributions, sample_actions):
        result = build_attribution_defense(
            sample_value_attributions[0],
            action=sample_actions[0],
            scenario_id="hormuz_chokepoint_disruption",
        )
        assert "decision_id" in result
        assert "attribution_type" in result
        assert "confidence_band" in result
        assert "external_factors" in result
        assert "explanation" in result

    def test_explanation_always_present(self, sample_value_attributions, sample_actions):
        result = build_attribution_defense(
            sample_value_attributions[0],
            action=sample_actions[0],
        )
        assert len(result["explanation"]) > 10  # non-trivial explanation

    def test_attribution_type_valid(self, sample_value_attributions):
        result = build_attribution_defense(sample_value_attributions[0])
        assert result["attribution_type"] in ("DIRECT", "ASSISTED", "LOW_CONFIDENCE")

    def test_confidence_band_bounded(self, sample_value_attributions):
        result = build_attribution_defense(sample_value_attributions[0])
        assert 0 <= result["confidence_band"] <= 1.0

    def test_geopolitical_scenario_adds_external_factor(self, sample_value_attributions, sample_actions):
        result = build_attribution_defense(
            sample_value_attributions[0],
            action=sample_actions[0],
            scenario_id="hormuz_chokepoint_disruption",
        )
        assert "geopolitical instability" in result["external_factors"]

    def test_volatility_scenario_adds_external_factor(self, sample_value_attributions, sample_actions):
        result = build_attribution_defense(
            sample_value_attributions[0],
            action=sample_actions[0],
            scenario_id="energy_market_volatility_shock",
        )
        assert "energy market volatility" in result["external_factors"]

    def test_never_over_claims_direct(self, sample_value_attributions, sample_actions):
        """With many actions + external factors, DIRECT should downgrade to ASSISTED."""
        result = build_attribution_defense(
            sample_value_attributions[0],  # originally DIRECT
            action=sample_actions[0],
            scenario_id="hormuz_chokepoint_disruption",
            severity=0.85,
            total_actions=6,  # many actions
        )
        # With geopolitical factor + 6 actions, DIRECT should become ASSISTED
        assert result["attribution_type"] in ("ASSISTED", "LOW_CONFIDENCE")

    def test_extreme_severity_adds_factor(self, sample_value_attributions, sample_actions):
        result = build_attribution_defense(
            sample_value_attributions[0],
            action=sample_actions[0],
            severity=0.90,
        )
        assert "extreme severity conditions" in result["external_factors"]

    def test_batch_returns_one_per_action(self, sample_value_attributions, sample_actions):
        results = build_all_attribution_defenses(
            sample_value_attributions,
            actions=sample_actions,
        )
        assert len(results) == 3

    def test_matches_original_attribution(self, sample_value_attributions):
        result = build_attribution_defense(sample_value_attributions[0])
        assert result["original_attribution_type"] == "DIRECT"
        assert result["original_confidence"] == 0.85


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Override Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestOverrideEngine:
    """Overrides tracked, no override without reason, traceable per decision."""

    def test_no_override_when_policy_allowed(self, sample_actions):
        result = track_override(
            sample_actions[0],
            policy={"allowed": True, "violations": []},
            workflow={"status": "APPROVED", "approver_role": "CRO"},
        )
        assert result["overridden"] is False
        assert result["reason"] is None
        assert result["override_type"] == "NONE"

    def test_policy_override_when_blocked_but_approved(self, sample_actions):
        result = track_override(
            sample_actions[0],
            policy={"allowed": False, "violations": ["test violation"]},
            workflow={"status": "APPROVED", "approver_role": "CRO"},
        )
        assert result["overridden"] is True
        assert result["overridden_by"] == "CRO"
        assert result["reason"] is not None
        assert result["override_type"] == "POLICY_OVERRIDE"
        assert result["timestamp"] is not None

    def test_no_override_without_reason(self, sample_actions):
        result = track_override(
            sample_actions[0],
            policy={"allowed": False, "violations": ["blocked"]},
            workflow={"status": "APPROVED", "approver_role": "CRO"},
        )
        if result["overridden"]:
            assert result["reason"] is not None
            assert len(result["reason"]) > 0

    def test_escalation_override(self, sample_actions):
        result = track_override(
            sample_actions[0],
            policy={"allowed": True, "violations": []},
            workflow={"status": "ESCALATED", "escalation_path": ["CRO", "CEO", "Board"]},
        )
        assert result["overridden"] is True
        assert result["override_type"] == "ESCALATION_RESOLUTION"
        assert result["overridden_by"] == "Board"

    def test_override_records_policy_violations(self, sample_actions):
        violations = ["regulatory scenario requires approval", "irreversible action"]
        result = track_override(
            sample_actions[0],
            policy={"allowed": False, "violations": violations},
            workflow={"status": "APPROVED", "approver_role": "CRO"},
        )
        assert result["policy_violations_at_override"] == violations

    def test_batch_returns_one_per_action(self, sample_actions):
        results = track_all_overrides(sample_actions)
        assert len(results) == 3
        ids = {r["decision_id"] for r in results}
        assert ids == {"act_001", "act_002", "act_003"}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Full Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    """End-to-end: all Phase 5 outputs present, decision reproducible from evidence."""

    def test_full_pipeline_produces_all_phase5_outputs(self):
        """Orchestrator response must include all 4 Phase 5 fields."""
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(
            scenario_id="hormuz_chokepoint_disruption",
            severity=0.75,
        )
        result = execute_run(params)

        # Phase 5 fields present
        assert "decision_evidence" in result
        assert "policy" in result
        assert "attribution_defense" in result
        assert "overrides" in result

        # Non-empty (pipeline produces actions)
        assert len(result["decision_evidence"]) > 0
        assert len(result["policy"]) > 0
        assert len(result["attribution_defense"]) > 0
        assert len(result["overrides"]) > 0

    def test_evidence_has_all_layers_for_every_decision(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.75)
        result = execute_run(params)

        for ev in result["decision_evidence"]:
            assert "signal_snapshot" in ev
            assert "transmission_evidence" in ev
            assert "counterfactual_basis" in ev
            assert "trust_basis" in ev
            assert "execution_evidence" in ev
            assert "outcome_evidence" in ev
            assert "completeness" in ev

    def test_policy_no_silent_failures(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.75)
        result = execute_run(params)

        for pol in result["policy"]:
            assert isinstance(pol["allowed"], bool)
            if not pol["allowed"]:
                assert len(pol["violations"]) > 0

    def test_attribution_defense_explanation_present(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.75)
        result = execute_run(params)

        for ad in result["attribution_defense"]:
            assert len(ad["explanation"]) > 0
            assert ad["attribution_type"] in ("DIRECT", "ASSISTED", "LOW_CONFIDENCE")

    def test_override_no_override_without_reason(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.75)
        result = execute_run(params)

        for ov in result["overrides"]:
            if ov["overridden"]:
                assert ov["reason"] is not None
                assert len(ov["reason"]) > 0
                assert ov["timestamp"] is not None

    def test_pipeline_stage_count_is_36(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.5)
        result = execute_run(params)
        assert result["pipeline_stages_completed"] == 41

    def test_regulatory_scenario_blocks_decisions(self):
        """Banking crisis scenario should trigger regulatory policy violations."""
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="uae_banking_crisis", severity=0.75)
        result = execute_run(params)

        blocked_count = sum(1 for p in result["policy"] if not p["allowed"])
        assert blocked_count > 0  # At least some decisions blocked by regulatory policy

    def test_evidence_consistent_with_prior_outputs(self):
        """Evidence pack data must match actual pipeline outputs."""
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(scenario_id="hormuz_chokepoint_disruption", severity=0.75)
        result = execute_run(params)

        # Evidence count matches decision count (all actions, not just top 3)
        actions = result.get("decision_plan", {}).get("actions", [])
        assert len(result["decision_evidence"]) == len(actions)
        assert len(result["policy"]) == len(actions)
        assert len(result["attribution_defense"]) == len(result["value_attribution"])
        assert len(result["overrides"]) == len(actions)
