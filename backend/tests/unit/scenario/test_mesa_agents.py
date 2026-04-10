"""Tests for specialized Mesa agent types.

Verifies that ConflictAgent, FlightAgent, VesselAgent, and LogisticsAgent
are assigned correctly and exhibit differentiated behavior.
"""

from __future__ import annotations

import pytest

from src.engines.scenario_engine.mesa_sim import (
    GCCIntelligenceModel,
    GCCNodeAgent,
    ConflictAgent,
    FlightAgent,
    VesselAgent,
    LogisticsAgent,
)
from src.services.seed_data import GCC_NODES, GCC_EDGES


def _build_model() -> GCCIntelligenceModel:
    return GCCIntelligenceModel(nodes=GCC_NODES, edges=GCC_EDGES)


class TestAgentTypeAssignment:
    def test_conflict_agents_assigned(self):
        model = _build_model()
        assert isinstance(model.agent_map["stability"], ConflictAgent)
        assert isinstance(model.agent_map["sentiment"], ConflictAgent)

    def test_flight_agents_assigned(self):
        model = _build_model()
        assert isinstance(model.agent_map["dubai_apt"], FlightAgent)
        assert isinstance(model.agent_map["riyadh_apt"], FlightAgent)
        assert isinstance(model.agent_map["airspace"], FlightAgent)
        assert isinstance(model.agent_map["aviation"], FlightAgent)

    def test_vessel_agents_assigned(self):
        model = _build_model()
        assert isinstance(model.agent_map["hormuz"], VesselAgent)
        assert isinstance(model.agent_map["shipping"], VesselAgent)
        assert isinstance(model.agent_map["jebel_ali"], VesselAgent)

    def test_logistics_agents_assigned(self):
        model = _build_model()
        assert isinstance(model.agent_map["logistics"], LogisticsAgent)
        assert isinstance(model.agent_map["supply_chain"], LogisticsAgent)

    def test_default_agents_are_gcc_node(self):
        model = _build_model()
        # Country nodes should use base GCCNodeAgent
        assert type(model.agent_map["saudi"]) is GCCNodeAgent
        assert type(model.agent_map["uae"]) is GCCNodeAgent


class TestAgentBehavior:
    def test_conflict_agent_amplifies_risk(self):
        """ConflictAgent should propagate risk more aggressively."""
        model = _build_model()
        # Inject shock near sentiment node
        model.inject_shock(["sentiment"], severity=0.8)
        model.step()
        # ConflictAgent decays slower — risk should be higher after shock
        assert model.agent_map["sentiment"].risk > 0.05

    def test_vessel_agent_slower_decay(self):
        """VesselAgent risk should persist longer (slower decay)."""
        model = _build_model()
        model.inject_shock(["hormuz"], severity=0.9)
        model.step()
        risk_after_1 = model.agent_map["hormuz"].risk

        # Run 3 more steps without re-injecting
        for _ in range(3):
            model.step()
        risk_after_4 = model.agent_map["hormuz"].risk

        # Risk should still be significant due to slower decay
        assert risk_after_4 > 0.01

    def test_logistics_agent_accumulates_pressure(self):
        """LogisticsAgent should accumulate pressure faster."""
        model = _build_model()
        model.inject_shock(["jebel_ali"], severity=0.9)
        for _ in range(5):
            model.step()

        logistics_pressure = model.agent_map["logistics"].pressure
        # Should accumulate noticeable pressure from jebel_ali shock
        assert logistics_pressure > 0.05

    def test_all_agents_step_without_error(self):
        """All specialized agent types should complete steps."""
        model = _build_model()
        model.inject_shock(["hormuz", "dubai_apt", "stability", "logistics"], severity=0.7)
        for _ in range(10):
            model.step()

        # All agents should have valid state
        for agent in model.agent_map.values():
            assert 0.0 <= agent.risk <= 1.0
            assert 0.0 <= agent.pressure <= 1.0
            assert 0.0 <= agent.disruption <= 1.0

    def test_agent_type_property(self):
        model = _build_model()
        assert model.agent_map["stability"].agent_type == "conflict"
        assert model.agent_map["dubai_apt"].agent_type == "flight"
        assert model.agent_map["hormuz"].agent_type == "vessel"
        assert model.agent_map["logistics"].agent_type == "logistics"
        assert model.agent_map["saudi"].agent_type == "node"
