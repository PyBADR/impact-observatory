"""Tests for graph propagation engine."""

import numpy as np
import pytest

from src.engines.math.propagation import (
    build_adjacency_matrix,
    compute_gdp_loss,
    compute_sector_impacts,
    compute_system_confidence,
    compute_system_energy,
    propagate_multi_step,
    propagation_step,
)


@pytest.fixture
def simple_graph():
    """3-node linear graph: A → B → C."""
    node_ids = ["a", "b", "c"]
    edges = [
        {"source": "a", "target": "b", "weight": 0.8, "polarity": 1},
        {"source": "b", "target": "c", "weight": 0.6, "polarity": 1},
    ]
    adj = build_adjacency_matrix(node_ids, edges)
    return node_ids, adj


class TestBuildAdjacency:
    def test_shape(self, simple_graph):
        _, adj = simple_graph
        assert adj.shape == (3, 3)

    def test_edge_values(self, simple_graph):
        _, adj = simple_graph
        assert adj[0, 1] == pytest.approx(0.8)  # a→b
        assert adj[1, 2] == pytest.approx(0.6)  # b→c
        assert adj[2, 0] == pytest.approx(0.0)  # no c→a

    def test_polarity(self):
        adj = build_adjacency_matrix(
            ["x", "y"],
            [{"source": "x", "target": "y", "weight": 0.5, "polarity": -1}],
        )
        assert adj[0, 1] == pytest.approx(-0.5)


class TestPropagationStep:
    def test_shock_propagates(self, simple_graph):
        _, adj = simple_graph
        risk = np.array([0.0, 0.0, 0.0])
        shock = np.array([1.0, 0.0, 0.0])
        result = propagation_step(adj, risk, shock)
        # Shock at a should propagate partially to b
        assert result[0] > 0  # from shock
        assert 0 <= result[1] <= 1
        assert 0 <= result[2] <= 1


class TestMultiStepPropagation:
    def test_converges(self, simple_graph):
        _, adj = simple_graph
        risk = np.zeros(3)
        shock = np.array([0.8, 0.0, 0.0])
        final, steps, history = propagate_multi_step(adj, risk, shock)
        assert steps > 0
        assert len(history) > 1
        assert all(0 <= v <= 1 for v in final)

    def test_shock_reaches_downstream(self, simple_graph):
        _, adj = simple_graph
        risk = np.zeros(3)
        shock = np.array([1.0, 0.0, 0.0])
        final, _, _ = propagate_multi_step(adj, risk, shock)
        # Node c should have some impact from a→b→c
        assert final[2] > 0


class TestSystemMetrics:
    def test_energy_zero_for_zero_risk(self):
        assert compute_system_energy(np.zeros(5)) == pytest.approx(0.0)

    def test_energy_positive_for_nonzero(self):
        assert compute_system_energy(np.array([0.5, 0.3, 0.7])) > 0

    def test_confidence_high_for_uniform(self):
        # Uniform risk = low variance = high confidence
        c = compute_system_confidence(np.full(10, 0.5))
        assert c > 0.8

    def test_confidence_lower_for_varied(self):
        uniform_c = compute_system_confidence(np.full(10, 0.5))
        varied_c = compute_system_confidence(np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1]))
        assert uniform_c > varied_c


class TestSectorImpacts:
    def test_correct_grouping(self):
        risk = np.array([0.8, 0.6, 0.4, 0.2])
        sectors = ["infra", "infra", "economy", "economy"]
        result = compute_sector_impacts(risk, sectors)
        assert result["infra"] == pytest.approx(0.7)
        assert result["economy"] == pytest.approx(0.3)


class TestGDPLoss:
    def test_weighted_sum(self):
        sector_impacts = {"infra": 0.5, "economy": 0.8}
        weights = {"infra": 0.3, "economy": 0.7}
        loss = compute_gdp_loss(sector_impacts, weights)
        expected = 0.5 * 0.3 + 0.8 * 0.7
        assert loss == pytest.approx(expected)
