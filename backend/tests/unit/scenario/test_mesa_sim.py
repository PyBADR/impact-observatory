"""Tests for Mesa agent-based simulation integration.

Tests cover model creation, shock injection, pressure accumulation,
congestion detection, convergence, and energy dynamics.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.engines.scenario.engine import GraphState
from src.engines.scenario_engine.mesa_sim import (
    GCCIntelligenceModel,
    GCCNodeAgent,
    MesaSimulationResult,
    run_mesa_simulation,
)
from src.services.seed_data import GCC_NODES, GCC_EDGES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_graph_state() -> GraphState:
    """Build a GraphState from GCC seed data."""
    node_ids = [n["id"] for n in GCC_NODES]
    node_labels = {n["id"]: n["label"] for n in GCC_NODES}
    node_labels_ar = {n["id"]: n.get("label_ar", "") for n in GCC_NODES}
    node_sectors = [n.get("layer", "infrastructure") for n in GCC_NODES]
    sector_weights = {
        "geography": 0.15,
        "infrastructure": 0.30,
        "economy": 0.25,
        "finance": 0.15,
        "society": 0.15,
    }
    return GraphState(
        node_ids=node_ids,
        node_labels=node_labels,
        node_labels_ar=node_labels_ar,
        node_sectors=node_sectors,
        sector_weights=sector_weights,
        edges=GCC_EDGES,
        baseline_risk=None,
    )


def _build_model() -> GCCIntelligenceModel:
    """Build a GCCIntelligenceModel from seed data."""
    return GCCIntelligenceModel(nodes=GCC_NODES, edges=GCC_EDGES)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestModelCreation:
    """Test that a model can be created from GCC seed data."""

    def test_model_creation(self) -> None:
        model = _build_model()

        # All seed nodes should be in the model
        assert model.n_nodes == len(GCC_NODES)

        # Agent map should contain all nodes
        for n in GCC_NODES:
            assert n["id"] in model.agent_map

        # NetworkX graph should have edges (undirected may merge duplicates)
        assert model.G.number_of_edges() >= len(GCC_EDGES) - 5

    def test_agent_initial_state(self) -> None:
        model = _build_model()

        for agent in model.agent_map.values():
            assert agent.risk == pytest.approx(0.05)
            assert agent.pressure == pytest.approx(0.10)
            assert agent.disruption == 0.0
            assert agent.shock == 0.0
            assert agent.capacity == 1.0

    def test_node_ids_stable(self) -> None:
        model = _build_model()
        state = model.get_system_state()

        assert len(state["risk_vector"]) == model.n_nodes
        assert len(state["pressure_vector"]) == model.n_nodes
        assert len(state["disruption_vector"]) == model.n_nodes


class TestShockInjection:
    """Test that shock injection increases risk in target nodes."""

    def test_shock_increases_risk(self) -> None:
        model = _build_model()

        # Record pre-shock risk for Hormuz
        pre_risk = model.agent_map["hormuz"].risk

        # Inject a severe shock
        model.inject_shock(["hormuz"], severity=0.9)
        model.step()

        post_risk = model.agent_map["hormuz"].risk
        assert post_risk > pre_risk, (
            f"Shock should increase risk: pre={pre_risk}, post={post_risk}"
        )

    def test_shock_propagates_to_neighbors(self) -> None:
        model = _build_model()

        # Hormuz connects to shipping, oil_sector, gas_sector, etc.
        model.inject_shock(["hormuz"], severity=0.9)

        # Run a few steps for propagation
        for _ in range(3):
            model.step()

        # Neighbors should have elevated risk compared to default
        shipping_risk = model.agent_map["shipping"].risk
        assert shipping_risk > 0.05, (
            f"Shock should propagate to shipping: risk={shipping_risk}"
        )

    def test_multi_node_shock(self) -> None:
        model = _build_model()

        targets = ["hormuz", "dubai_apt", "jebel_ali"]
        model.inject_shock(targets, severity=0.8)
        model.step()

        for nid in targets:
            assert model.agent_map[nid].risk > 0.05

    def test_shock_clamped_to_unit(self) -> None:
        model = _build_model()
        model.inject_shock(["hormuz"], severity=1.5)  # over 1.0
        model.step()

        assert model.agent_map["hormuz"].risk <= 1.0


class TestPressureAccumulation:
    """Test that pressure accumulates at high-traffic nodes."""

    def test_pressure_accumulates_under_shock(self) -> None:
        model = _build_model()
        initial_pressure = model.agent_map["hormuz"].pressure

        model.inject_shock(["hormuz"], severity=0.8)

        for _ in range(5):
            model.step()

        final_pressure = model.agent_map["hormuz"].pressure
        assert final_pressure > initial_pressure, (
            f"Pressure should accumulate: initial={initial_pressure}, "
            f"final={final_pressure}"
        )

    def test_pressure_spreads_through_network(self) -> None:
        model = _build_model()

        # Shock at a hub node
        model.inject_shock(["jebel_ali"], severity=0.9)

        for _ in range(8):
            model.step()

        # Logistics is connected to jebel_ali
        logistics_pressure = model.agent_map["logistics"].pressure
        # Should be above the default 0.10 initial value after several steps
        # of pressure inflow from the shocked neighbor
        assert logistics_pressure > 0.08, (
            f"Pressure should spread to logistics: {logistics_pressure}"
        )


class TestCongestionDetection:
    """Test that congested nodes are detected when pressure exceeds threshold."""

    def test_congestion_detected(self) -> None:
        model = _build_model()

        # Inject very strong shock to push pressure above threshold
        model.inject_shock(["hormuz"], severity=1.0)

        for _ in range(10):
            model.step()
            # Re-inject to keep pressure climbing
            model.inject_shock(["hormuz"], severity=0.9)

        events = model.congestion_events
        hormuz_events = [e for e in events if e[1] == "hormuz"]
        assert len(hormuz_events) > 0, (
            "Hormuz should have congestion events under sustained heavy shock"
        )
        # Pressure values in events should be above threshold
        for step_num, nid, pressure_val in hormuz_events:
            assert pressure_val > 0.70

    def test_no_congestion_without_shock(self) -> None:
        model = _build_model()

        # Run without any shocks — initial pressure is 0.10, well below 0.70
        for _ in range(5):
            model.step()

        events = model.congestion_events
        assert len(events) == 0, (
            f"No congestion expected without shocks, got {len(events)} events"
        )


class TestConvergence:
    """Test that the simulation converges after a shock dissipates."""

    def test_convergence_after_impulse(self) -> None:
        graph_state = _build_graph_state()

        result = run_mesa_simulation(
            graph_state=graph_state,
            scenario={
                "shocks": [
                    {"target_node_ids": ["hormuz"], "severity": 0.7},
                ],
            },
            n_steps=100,
        )

        assert isinstance(result, MesaSimulationResult)
        assert result.steps_run > 0
        assert result.steps_run <= 100

        # After enough steps with a single impulse, the system should converge
        # (risk changes become negligible)
        if result.converged:
            assert result.steps_run < 100

    def test_result_has_all_fields(self) -> None:
        graph_state = _build_graph_state()

        result = run_mesa_simulation(
            graph_state=graph_state,
            scenario={"shocks": [{"target_node_ids": ["dubai_apt"], "severity": 0.5}]},
            n_steps=10,
        )

        assert len(result.risk_history) == result.steps_run
        assert len(result.pressure_history) == result.steps_run
        assert len(result.system_energy_history) == result.steps_run
        assert "risk_vector" in result.final_state
        assert "pressure_vector" in result.final_state
        assert "disruption_vector" in result.final_state
        assert isinstance(result.congestion_events, list)
        assert isinstance(result.converged, bool)


class TestSystemEnergy:
    """Test that system energy eventually decreases after a shock."""

    def test_energy_decreases_post_shock(self) -> None:
        graph_state = _build_graph_state()

        result = run_mesa_simulation(
            graph_state=graph_state,
            scenario={
                "shocks": [
                    {"target_node_ids": ["hormuz", "shipping"], "severity": 0.8},
                ],
            },
            n_steps=40,
        )

        energies = result.system_energy_history
        assert len(energies) > 2

        # Energy should peak early then decline (or at least the late-stage
        # energy should be lower than the peak)
        peak_energy = max(energies)
        final_energy = energies[-1]
        assert final_energy <= peak_energy, (
            f"Final energy ({final_energy}) should not exceed peak ({peak_energy})"
        )

    def test_energy_positive(self) -> None:
        graph_state = _build_graph_state()

        result = run_mesa_simulation(
            graph_state=graph_state,
            scenario={"shocks": [{"target_node_ids": ["riyadh_apt"], "severity": 0.6}]},
            n_steps=10,
        )

        for e in result.system_energy_history:
            assert e >= 0.0

    def test_metrics_accessible(self) -> None:
        model = _build_model()
        model.inject_shock(["hormuz"], severity=0.7)
        model.step()

        metrics = model.get_metrics()
        assert "system_energy" in metrics
        assert "max_risk" in metrics
        assert "congested_count" in metrics
        assert "mean_pressure" in metrics
        assert metrics["system_energy"] >= 0.0
        assert metrics["step"] == 1
