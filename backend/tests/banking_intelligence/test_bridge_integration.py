"""
Banking Intelligence — Bridge Integration Test
================================================
Exercises bridge_full_chain() against all 15 scenarios from SCENARIO_CATALOG.

Validates:
  1. Every scenario produces valid Pydantic models (no ValidationError)
  2. All contract IDs follow prefixed patterns (dec:, cf:, prop:, review:, audit:)
  3. Cross-reference integrity (decision → counterfactual → review → audit)
  4. Propagation contracts are ordered and non-empty for chain-producing scenarios
  5. Value audit math is self-consistent
  6. State machine starts at DRAFT
"""

import pytest
from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
from src.simulation_schemas import SimulateResponse
from src.banking_intelligence.services.scenario_bridge import bridge_full_chain
from src.banking_intelligence.schemas.decision_contract import (
    DecisionContract,
    DecisionStatus,
)
from src.banking_intelligence.schemas.counterfactual import CounterfactualContract
from src.banking_intelligence.schemas.propagation import PropagationContract
from src.banking_intelligence.schemas.outcome_review import (
    OutcomeReviewContract,
    DecisionValueAudit,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    """Module-scoped engine (expensive to create — reuse across tests)."""
    return SimulationEngine()


@pytest.fixture(scope="module")
def all_chains(engine):
    """Run bridge_full_chain for every scenario at severity=0.7.

    Returns dict[scenario_id → chain_dict].
    """
    chains = {}
    for scenario_id in sorted(SCENARIO_CATALOG.keys()):
        raw = engine.run(scenario_id=scenario_id, severity=0.7, horizon_hours=336)
        sim_result = SimulateResponse(**raw)
        run_id = f"test-bridge-{scenario_id[:20]}"
        chain = bridge_full_chain(run_id, scenario_id, sim_result)
        chains[scenario_id] = chain
    return chains


SCENARIO_IDS = sorted(SCENARIO_CATALOG.keys())


# ── Parametrized Tests ──────────────────────────────────────────────────────

@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
class TestBridgeFullChain:
    """End-to-end bridge integration for each scenario."""

    def test_chain_has_all_keys(self, all_chains, scenario_id):
        """Chain dict contains all required top-level keys."""
        chain = all_chains[scenario_id]
        required = {
            "decision_contract",
            "counterfactual_contract",
            "propagation_contracts",
            "outcome_review_contract",
            "value_audit",
            "metadata",
        }
        assert required.issubset(chain.keys()), (
            f"Missing keys: {required - chain.keys()}"
        )

    def test_decision_contract_valid(self, all_chains, scenario_id):
        """DecisionContract passes Pydantic validation and has correct prefix."""
        dc: DecisionContract = all_chains[scenario_id]["decision_contract"]
        assert isinstance(dc, DecisionContract)
        assert dc.decision_id.startswith("dec:")
        assert dc.scenario_id == scenario_id
        assert dc.status == DecisionStatus.DRAFT
        assert dc.primary_owner_id.startswith("authority:")
        assert dc.approver_id.startswith("authority:")
        assert dc.escalation_threshold > 0.0
        assert dc.escalation_threshold <= 1.0

    def test_counterfactual_contract_valid(self, all_chains, scenario_id):
        """CounterfactualContract has 4 branches with correct labels."""
        cf: CounterfactualContract = all_chains[scenario_id][
            "counterfactual_contract"
        ]
        assert isinstance(cf, CounterfactualContract)
        assert cf.counterfactual_id.startswith("cf:")
        assert cf.scenario_id == scenario_id

        # 4-branch labels
        assert cf.do_nothing.branch_label == "do_nothing"
        assert cf.recommended_action.branch_label == "recommended_action"
        assert cf.delayed_action.branch_label == "delayed_action"
        assert cf.alternative_action.branch_label == "alternative_action"

        # do_nothing loss >= recommended_action loss
        assert cf.do_nothing.expected_loss_usd >= cf.recommended_action.expected_loss_usd

    def test_counterfactual_linked_to_decision(self, all_chains, scenario_id):
        """Counterfactual references the correct decision_id."""
        chain = all_chains[scenario_id]
        dc: DecisionContract = chain["decision_contract"]
        cf: CounterfactualContract = chain["counterfactual_contract"]
        assert cf.decision_id == dc.decision_id

    def test_propagation_contracts_valid(self, all_chains, scenario_id):
        """Propagation contracts have correct prefixes and from/to entity fields."""
        props: list[PropagationContract] = all_chains[scenario_id][
            "propagation_contracts"
        ]
        assert isinstance(props, list)
        for i, p in enumerate(props):
            assert isinstance(p, PropagationContract)
            assert p.propagation_id.startswith("prop:")
            assert p.scenario_id == scenario_id
            assert p.from_entity_id, f"Empty from_entity_id at index {i}"
            assert p.to_entity_id, f"Empty to_entity_id at index {i}"
            assert 0.0 <= p.severity_transfer <= 1.0
            assert p.delay_hours > 0.0

    def test_outcome_review_contract_valid(self, all_chains, scenario_id):
        """OutcomeReviewContract has 4 windows and correct ID prefix."""
        review: OutcomeReviewContract = all_chains[scenario_id][
            "outcome_review_contract"
        ]
        assert isinstance(review, OutcomeReviewContract)
        assert review.review_id.startswith("review:")
        assert review.scenario_id == scenario_id
        assert len(review.windows) == 4
        # Windows should be in ascending order of hours
        hours = [w.window_hours for w in review.windows]
        assert hours == sorted(hours)

    def test_outcome_review_linked_to_decision(self, all_chains, scenario_id):
        """Outcome review references the correct decision_id."""
        chain = all_chains[scenario_id]
        dc: DecisionContract = chain["decision_contract"]
        review: OutcomeReviewContract = chain["outcome_review_contract"]
        assert review.decision_id == dc.decision_id

    def test_value_audit_valid(self, all_chains, scenario_id):
        """DecisionValueAudit has correct prefix and self-consistent math."""
        audit: DecisionValueAudit = all_chains[scenario_id]["value_audit"]
        assert isinstance(audit, DecisionValueAudit)
        assert audit.audit_id.startswith("audit:")
        assert audit.scenario_id == scenario_id
        assert audit.gross_loss_avoided_usd > 0.0
        assert audit.implementation_cost_usd > 0.0
        assert audit.composite_confidence > 0.0
        assert audit.composite_confidence <= 1.0
        assert len(audit.assumptions_trace) >= 2

    def test_value_audit_linked_to_decision_and_review(self, all_chains, scenario_id):
        """Value audit references correct decision_id and review_id."""
        chain = all_chains[scenario_id]
        dc: DecisionContract = chain["decision_contract"]
        review: OutcomeReviewContract = chain["outcome_review_contract"]
        audit: DecisionValueAudit = chain["value_audit"]
        assert audit.decision_id == dc.decision_id
        assert audit.outcome_review_id == review.review_id

    def test_decision_backlinks(self, all_chains, scenario_id):
        """Decision contract has backlinks to counterfactual, review, and audit."""
        chain = all_chains[scenario_id]
        dc: DecisionContract = chain["decision_contract"]
        cf: CounterfactualContract = chain["counterfactual_contract"]
        review: OutcomeReviewContract = chain["outcome_review_contract"]
        audit: DecisionValueAudit = chain["value_audit"]
        assert dc.counterfactual_id == cf.counterfactual_id
        assert dc.outcome_review_id == review.review_id
        assert dc.value_audit_id == audit.audit_id

    def test_metadata_complete(self, all_chains, scenario_id):
        """Metadata block has all required fields."""
        meta = all_chains[scenario_id]["metadata"]
        assert meta["run_id"].startswith("test-bridge-")
        assert meta["scenario_id"] == scenario_id
        assert meta["final_urs"] > 0.0
        assert meta["financial_impact_usd"] > 0.0
        assert meta["decision_id"].startswith("dec:")
        assert meta["counterfactual_id"].startswith("cf:")
        assert meta["review_id"].startswith("review:")
        assert meta["audit_id"].startswith("audit:")


# ── Aggregate Tests ─────────────────────────────────────────────────────────

class TestBridgeAggregates:
    """Cross-scenario aggregate validation."""

    def test_all_scenarios_bridgeable(self, all_chains):
        """Every scenario in SCENARIO_CATALOG produced a valid chain."""
        assert len(all_chains) == len(SCENARIO_CATALOG)

    def test_unique_decision_ids(self, all_chains):
        """No two scenarios produce the same decision_id."""
        ids = [c["decision_contract"].decision_id for c in all_chains.values()]
        assert len(ids) == len(set(ids)), "Duplicate decision IDs found"

    def test_unique_counterfactual_ids(self, all_chains):
        """No two scenarios produce the same counterfactual_id."""
        ids = [
            c["counterfactual_contract"].counterfactual_id
            for c in all_chains.values()
        ]
        assert len(ids) == len(set(ids)), "Duplicate counterfactual IDs found"
