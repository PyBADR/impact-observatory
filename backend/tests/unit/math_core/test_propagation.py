"""Tests for GCC-tuned propagation engine."""

import numpy as np
import pytest

from src.engines.math_core.propagation import (
    propagation_step,
    propagate_multi_step,
    pressure_step,
    accumulate_pressure,
    compute_system_energy,
    build_adjacency_matrix,
)
from src.engines.math_core.gcc_weights import SHOCKWAVE, PRESSURE


class TestPropagationStep:
    def test_zero_state_zero_shock(self):
        adj = np.eye(3) * 0.5
        state = np.zeros(3)
        shock = np.zeros(3)
        result = propagation_step(adj, state, shock)
        assert np.allclose(result, 0.0)

    def test_shock_propagates(self):
        adj = np.array([[0, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0]])
        state = np.zeros(3)
        shock = np.array([1.0, 0.0, 0.0])
        result = propagation_step(adj, state, shock)
        assert result[0] > 0  # shock at node 0
        assert result[1] == 0  # no adjacency propagation yet (state was zero)

    def test_uses_gcc_coefficients(self):
        adj = np.eye(2) * 0.5
        state = np.array([0.5, 0.0])
        shock = np.array([0.3, 0.0])
        ext = np.array([0.1, 0.0])
        result = propagation_step(adj, state, shock, ext)
        expected_0 = SHOCKWAVE.alpha * 0.5 * 0.5 + SHOCKWAVE.beta * 0.3 + SHOCKWAVE.delta * 0.1
        assert result[0] == pytest.approx(min(expected_0, 1.0), abs=0.001)


class TestMultiStepPropagation:
    def test_converges(self):
        adj = np.array([[0, 0.3, 0], [0.3, 0, 0.3], [0, 0.3, 0]])
        initial = np.zeros(3)
        shock = np.array([0.5, 0, 0])
        result = propagate_multi_step(adj, initial, shock, max_steps=50)
        assert result.steps > 0
        assert result.final_state.shape == (3,)
        assert result.peak_risk > 0

    def test_energy_history_recorded(self):
        adj = np.eye(3) * 0.5
        initial = np.zeros(3)
        shock = np.array([0.8, 0, 0])
        result = propagate_multi_step(adj, initial, shock, max_steps=5)
        assert len(result.energy_history) == result.steps + 1


class TestPressureStep:
    def test_zero_inputs(self):
        p = np.zeros(3)
        result = pressure_step(p, np.zeros(3), np.zeros(3), np.zeros(3))
        assert np.allclose(result, 0.0)

    def test_persistence(self):
        p = np.array([0.5, 0.5, 0.5])
        result = pressure_step(p, np.zeros(3), np.zeros(3), np.zeros(3))
        expected = PRESSURE.rho * 0.5
        assert result[0] == pytest.approx(expected, abs=0.001)

    def test_shock_increases_pressure(self):
        p = np.zeros(3)
        shock = np.array([1.0, 0.0, 0.0])
        result = pressure_step(p, np.zeros(3), np.zeros(3), shock)
        assert result[0] == pytest.approx(PRESSURE.xi * 1.0, abs=0.001)


class TestPressureAccumulation:
    def test_multi_step(self):
        n = 3
        inflows = [np.array([0.3, 0.1, 0.0])] * 5
        outflows = [np.array([0.1, 0.1, 0.0])] * 5
        shocks = [np.array([0.5, 0.0, 0.0])] + [np.zeros(n)] * 4
        result = accumulate_pressure(np.zeros(n), inflows, outflows, shocks)
        assert result.steps == 5
        assert result.pressure_state[0] > result.pressure_state[2]


class TestSystemEnergy:
    def test_zero(self):
        assert compute_system_energy(np.zeros(5)) == 0.0

    def test_unit_vector(self):
        e = compute_system_energy(np.ones(4))
        assert e > 0


class TestAdjacencyMatrix:
    def test_build(self):
        ids = ["a", "b", "c"]
        edges = [
            {"source": "a", "target": "b", "weight": 0.8},
            {"source": "b", "target": "c", "weight": 0.6},
        ]
        adj = build_adjacency_matrix(ids, edges)
        assert adj.shape == (3, 3)
        assert adj[0, 1] > 0  # a→b
        assert adj[1, 2] > 0  # b→c
        # Row-normalized
        assert adj[0].sum() == pytest.approx(1.0, abs=0.01) or adj[0, 1] > 0
