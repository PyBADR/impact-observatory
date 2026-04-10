"""
Tests — Decision Contract, Counterfactual, Propagation, Outcome, Value Audit
=============================================================================
Validates state machines, computation logic, and rejection of invalid data.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError

from src.banking_intelligence.schemas.decision_contract import (
    DecisionContract,
    DecisionStatus,
    VALID_TRANSITIONS,
    RollbackPlan,
    ObservationPlan,
)
from src.banking_intelligence.schemas.counterfactual import (
    CounterfactualContract,
    CounterfactualBranch,
    ConfidenceDimensions,
    DownsideRisk,
)
from src.banking_intelligence.schemas.propagation import (
    PropagationContract,
    PropagationChain,
    InterventionSpec,
    PropagationEvidence,
)
from src.banking_intelligence.schemas.outcome_review import (
    OutcomeReviewContract,
    DecisionValueAudit,
    ReviewWindow,
    AssumptionTrace,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _minimal_decision(**overrides) -> dict:
    base = {
        "decision_id": "dec:test_001",
        "scenario_id": "hormuz_chokepoint_disruption",
        "title": "Test Decision for Hormuz Scenario",
        "sector": "banking",
        "decision_type": "mitigating",
        "primary_owner_id": "authority:sa_sama",
        "approver_id": "authority:sa_sama",
        "deadline_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "trigger_condition": "URS >= 0.65",
        "escalation_threshold": 0.80,
        "legal_authority_basis": "SAMA_BCR_Art_42",
        "reversibility": "partially_reversible",
        "execution_feasibility": "ready",
        "rollback_plan": {
            "is_rollback_possible": True,
            "rollback_steps": ["Step 1"],
            "rollback_owner_id": "authority:sa_sama",
        },
        "observation_plan": {
            "primary_metric": "interbank_rate_spread",
            "observer_entity_id": "authority:sa_sama",
        },
    }
    base.update(overrides)
    return base


def _confidence(d=0.85, i=0.70, e=0.88, ds=0.75) -> dict:
    return {
        "directional_confidence": d,
        "impact_estimate_confidence": i,
        "execution_confidence": e,
        "data_sufficiency_confidence": ds,
    }


def _downside(loss=1000000, prob=0.1) -> dict:
    return {
        "worst_case_loss_usd": loss,
        "probability_of_worst_case": prob,
        "description": "Test downside",
    }


def _branch(label, loss, cost, delta, hours=72) -> dict:
    return {
        "branch_label": label,
        "description": f"Test {label} branch",
        "expected_loss_usd": loss,
        "expected_cost_usd": cost,
        "expected_time_to_stabilize_hours": hours,
        "downside_risk": _downside(),
        "confidence": _confidence(),
        "delta_vs_baseline_usd": delta,
    }


# ─── Decision Contract Tests ───────────────────────────────────────────────

class TestDecisionContract:
    def test_valid_creation(self):
        dc = DecisionContract.model_validate(_minimal_decision())
        assert dc.status == DecisionStatus.DRAFT
        assert dc.is_terminal is False

    def test_state_transition_happy_path(self):
        dc = DecisionContract.model_validate(_minimal_decision())
        dc.transition_to(DecisionStatus.PENDING_APPROVAL, "test_user")
        assert dc.status == DecisionStatus.PENDING_APPROVAL
        dc.transition_to(DecisionStatus.APPROVED, "approver")
        dc.transition_to(DecisionStatus.EXECUTING, "executor")
        dc.transition_to(DecisionStatus.EXECUTED, "executor")
        assert dc.executed_at is not None
        dc.transition_to(DecisionStatus.CLOSED, "reviewer")
        assert dc.is_terminal is True
        assert len(dc.status_history) == 5

    def test_invalid_transition_raises(self):
        dc = DecisionContract.model_validate(_minimal_decision())
        with pytest.raises(ValueError, match="Invalid transition"):
            dc.transition_to(DecisionStatus.EXECUTED, "test")

    def test_dependencies_satisfied_check(self):
        data = _minimal_decision(dependencies=[
            {"dependency_id": "bank:sa_snb", "dependency_type": "system_ready", "is_satisfied": True},
            {"dependency_id": "bank:sa_rajhi", "dependency_type": "system_ready", "is_satisfied": False},
        ])
        dc = DecisionContract.model_validate(data)
        assert dc.dependencies_satisfied is False

    def test_all_transitions_coverage(self):
        """Verify every defined transition is reachable."""
        for from_status, targets in VALID_TRANSITIONS.items():
            for target in targets:
                dc = DecisionContract.model_validate(
                    _minimal_decision(status=from_status.value)
                )
                assert dc.can_transition_to(target)


# ─── Counterfactual Tests ──────────────────────────────────────────────────

class TestCounterfactualContract:
    def test_valid_counterfactual(self):
        cf = CounterfactualContract.model_validate({
            "counterfactual_id": "cf:test_001",
            "decision_id": "dec:test_001",
            "scenario_id": "hormuz_chokepoint_disruption",
            "analysis_horizon_hours": 168,
            "do_nothing": _branch("do_nothing", 850000000, 0, 0.0, 336),
            "recommended_action": _branch("recommended_action", 200000000, 45000000, -605000000, 72),
            "delayed_action": _branch("delayed_action", 450000000, 45000000, -355000000, 144),
            "alternative_action": _branch("alternative_action", 350000000, 25000000, -475000000, 120),
        })
        assert cf.recommended_net_benefit_usd == 850000000 - 200000000 - 45000000
        assert cf.is_action_justified is True
        assert cf.delay_penalty_usd == 450000000 - 200000000

    def test_do_nothing_must_have_zero_delta(self):
        with pytest.raises(ValidationError, match="delta_vs_baseline_usd must be 0.0"):
            CounterfactualContract.model_validate({
                "counterfactual_id": "cf:bad",
                "decision_id": "dec:test",
                "scenario_id": "test",
                "analysis_horizon_hours": 168,
                "do_nothing": _branch("do_nothing", 100, 0, 50.0),  # delta != 0
                "recommended_action": _branch("recommended_action", 50, 10, -40),
                "delayed_action": _branch("delayed_action", 75, 10, -15),
                "alternative_action": _branch("alternative_action", 60, 15, -25),
            })

    def test_confidence_composite(self):
        dims = ConfidenceDimensions(
            directional_confidence=0.85,
            impact_estimate_confidence=0.70,
            execution_confidence=0.88,
            data_sufficiency_confidence=0.75,
        )
        composite = dims.composite_confidence
        assert 0.0 < composite < 1.0
        assert dims.weakest_dimension == "impact_estimate"


# ─── Propagation Tests ─────────────────────────────────────────────────────

class TestPropagationContract:
    def _evidence(self) -> dict:
        return {
            "evidence_type": "stress_test",
            "description": "2025 SAMA stress test",
            "relevance_score": 0.85,
        }

    def _intervention(self) -> dict:
        return {
            "intervention_type": "liquidity_injection",
            "description": "SAMA emergency repo facility",
            "owner_entity_id": "authority:sa_sama",
            "readiness": "ready",
            "estimated_activation_hours": 2.0,
            "effectiveness_estimate": 0.80,
        }

    def test_valid_breakable_propagation(self):
        prop = PropagationContract.model_validate({
            "propagation_id": "prop:snb_to_rajhi_liquidity",
            "scenario_id": "hormuz_chokepoint_disruption",
            "from_entity_id": "bank:sa_snb",
            "to_entity_id": "bank:sa_rajhi",
            "transfer_mechanism": "liquidity_channel",
            "delay_hours": 4.0,
            "severity_transfer": 0.35,
            "breakable_point": True,
            "interventions": [self._intervention()],
            "actionable_owner_id": "authority:sa_sama",
            "evidence_sources": [self._evidence()],
            "confidence": 0.75,
        })
        assert prop.best_intervention is not None
        assert prop.max_blockable_severity == pytest.approx(0.35 * 0.80)

    def test_breakable_without_interventions_fails(self):
        with pytest.raises(ValidationError, match="breakable_point=True but no interventions"):
            PropagationContract.model_validate({
                "propagation_id": "prop:bad",
                "scenario_id": "test",
                "from_entity_id": "bank:sa_snb",
                "to_entity_id": "bank:sa_rajhi",
                "transfer_mechanism": "liquidity_channel",
                "delay_hours": 4.0,
                "severity_transfer": 0.35,
                "breakable_point": True,
                "interventions": [],  # empty!
                "actionable_owner_id": "authority:sa_sama",
                "evidence_sources": [self._evidence()],
                "confidence": 0.75,
            })

    def test_chain_validates_continuity(self):
        link1 = PropagationContract.model_validate({
            "propagation_id": "prop:link1",
            "scenario_id": "test",
            "from_entity_id": "bank:sa_snb",
            "to_entity_id": "bank:sa_rajhi",
            "transfer_mechanism": "liquidity_channel",
            "delay_hours": 4.0,
            "severity_transfer": 0.5,
            "breakable_point": False,
            "actionable_owner_id": "authority:sa_sama",
            "evidence_sources": [self._evidence()],
            "confidence": 0.75,
        })
        link2 = PropagationContract.model_validate({
            "propagation_id": "prop:link2",
            "scenario_id": "test",
            "from_entity_id": "bank:sa_rajhi",
            "to_entity_id": "fintech:sa_stcpay",
            "transfer_mechanism": "payment_channel",
            "delay_hours": 2.0,
            "severity_transfer": 0.3,
            "breakable_point": False,
            "actionable_owner_id": "authority:sa_sama",
            "evidence_sources": [self._evidence()],
            "confidence": 0.65,
        })
        chain = PropagationChain(
            chain_id="chain:test",
            scenario_id="test",
            links=[link1, link2],
        )
        assert chain.total_delay_hours == 6.0
        assert chain.cumulative_severity_transfer == pytest.approx(0.5 * 0.3)

    def test_chain_rejects_broken_continuity(self):
        link1 = PropagationContract.model_validate({
            "propagation_id": "prop:a",
            "scenario_id": "test",
            "from_entity_id": "bank:sa_snb",
            "to_entity_id": "bank:sa_rajhi",
            "transfer_mechanism": "liquidity_channel",
            "delay_hours": 4.0,
            "severity_transfer": 0.5,
            "breakable_point": False,
            "actionable_owner_id": "authority:sa_sama",
            "evidence_sources": [self._evidence()],
            "confidence": 0.75,
        })
        link2 = PropagationContract.model_validate({
            "propagation_id": "prop:b",
            "scenario_id": "test",
            "from_entity_id": "bank:ae_fab",  # WRONG — not rajhi
            "to_entity_id": "fintech:sa_stcpay",
            "transfer_mechanism": "payment_channel",
            "delay_hours": 2.0,
            "severity_transfer": 0.3,
            "breakable_point": False,
            "actionable_owner_id": "authority:sa_sama",
            "evidence_sources": [self._evidence()],
            "confidence": 0.65,
        })
        with pytest.raises(ValidationError, match="Chain broken"):
            PropagationChain(
                chain_id="chain:broken",
                scenario_id="test",
                links=[link1, link2],
            )


# ─── Outcome Review Tests ──────────────────────────────────────────────────

class TestOutcomeReview:
    def test_standard_review_factory(self):
        review = OutcomeReviewContract.create_standard_review(
            review_id="review:test_001",
            decision_id="dec:test_001",
            scenario_id="hormuz_chokepoint_disruption",
            metric_name="interbank_rate_spread",
            expected_values={6.0: 30.0, 24.0: 25.0, 72.0: 20.0, 168.0: 15.0},
        )
        assert len(review.windows) == 4
        assert review.completion_pct == 0.0
        assert review.windows[0].window_hours == 6.0

    def test_delta_computation(self):
        w = ReviewWindow(
            window_hours=24.0,
            metric_name="test",
            expected_metric_value=100.0,
            actual_metric_value=85.0,
        )
        assert w.delta_from_expected == -15.0
        assert w.delta_pct == -15.0


# ─── Value Audit Tests ─────────────────────────────────────────────────────

class TestDecisionValueAudit:
    def _minimal_audit(self, **overrides) -> dict:
        base = {
            "audit_id": "audit:test_001",
            "decision_id": "dec:test_001",
            "outcome_review_id": "review:test_001",
            "scenario_id": "hormuz_chokepoint_disruption",
            "gross_loss_avoided_usd": 650000000,
            "implementation_cost_usd": 45000000,
            "side_effect_cost_usd": 10000000,
            "composite_confidence": 0.81,
            "assumptions_trace": [
                {
                    "assumption_id": "A001",
                    "description": "Oil price assumption",
                    "value_used": 95.0,
                    "source": "Bloomberg",
                    "sensitivity_to_outcome": 0.8,
                    "was_validated": True,
                }
            ],
        }
        base.update(overrides)
        return base

    def test_value_computation(self):
        audit = DecisionValueAudit.model_validate(self._minimal_audit())
        assert audit.net_value_usd == 650000000 - 45000000 - 10000000
        assert audit.confidence_adjusted_value_usd == pytest.approx(
            audit.net_value_usd * 0.81
        )

    def test_cfo_defensible_with_validated_assumptions(self):
        audit = DecisionValueAudit.model_validate(self._minimal_audit())
        assert audit.cfo_defensible is True
        assert len(audit.defensibility_gaps) == 0

    def test_not_defensible_with_low_confidence(self):
        audit = DecisionValueAudit.model_validate(
            self._minimal_audit(composite_confidence=0.20)
        )
        assert audit.cfo_defensible is False
        assert any("too low" in g for g in audit.defensibility_gaps)

    def test_variance_computation(self):
        audit = DecisionValueAudit.model_validate(
            self._minimal_audit(realized_value_usd=400000000)
        )
        assert audit.variance_usd is not None
        assert audit.variance_usd == 400000000 - audit.confidence_adjusted_value_usd
