"""Tests for GCC-tuned disruption scoring."""

import numpy as np
import pytest

from src.engines.math_core.disruption import (
    compute_disruption_score,
    compute_disruption_vector,
)
from src.engines.math_core.gcc_weights import DISRUPTION


class TestDisruptionScore:
    def test_zero_inputs(self):
        bd = compute_disruption_score("n1", risk=0.0)
        assert bd.disruption_score == 0.0

    def test_full_risk_only(self):
        bd = compute_disruption_score("n1", risk=1.0)
        assert bd.disruption_score == pytest.approx(DISRUPTION.risk, abs=0.01)

    def test_all_components(self):
        bd = compute_disruption_score(
            "n1", risk=0.8, congestion=0.6,
            accessibility_loss=0.5, reroute_penalty=0.7,
            boundary_restriction=0.3,
        )
        expected = (
            DISRUPTION.risk * 0.8
            + DISRUPTION.congestion * 0.6
            + DISRUPTION.accessibility_loss * 0.5
            + DISRUPTION.reroute_penalty * 0.7
            + DISRUPTION.boundary_restriction * 0.3
        )
        assert bd.disruption_score == pytest.approx(expected, abs=0.001)

    def test_capped_at_one(self):
        bd = compute_disruption_score(
            "n1", risk=1.0, congestion=1.0,
            accessibility_loss=1.0, reroute_penalty=1.0,
            boundary_restriction=1.0,
        )
        assert bd.disruption_score <= 1.0

    def test_dominant_factor(self):
        bd = compute_disruption_score("n1", risk=0.9, congestion=0.1)
        assert bd.dominant_factor == "risk"

    def test_vector_scoring(self):
        ids = ["a", "b", "c"]
        risk = np.array([0.8, 0.4, 0.1])
        vec, bds = compute_disruption_vector(ids, risk)
        assert vec.shape == (3,)
        assert len(bds) == 3
        assert vec[0] > vec[1] > vec[2]
