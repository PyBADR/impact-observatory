"""Tests for insurance portfolio exposure."""

import numpy as np
import pytest

from src.engines.insurance_intelligence.portfolio_exposure import (
    compute_portfolio_exposure,
    compute_portfolio_exposure_batch,
)
from src.engines.math_core.gcc_weights import INSURANCE_EXPOSURE


class TestPortfolioExposure:
    def test_zero_inputs(self):
        r = compute_portfolio_exposure("p1", 0, 0, 0, 0)
        assert r.exposure_score == 0.0
        assert r.classification == "LOW"

    def test_max_inputs(self):
        r = compute_portfolio_exposure("p1", 1, 1, 1, 1)
        assert r.exposure_score == pytest.approx(1.0, abs=0.01)
        assert r.classification == "CRITICAL"

    def test_partial_inputs(self):
        r = compute_portfolio_exposure("p1", 0.8, 0.6, 0.7, 0.5)
        expected = (
            INSURANCE_EXPOSURE.tiv * 0.8
            + INSURANCE_EXPOSURE.route_dependency * 0.6
            + INSURANCE_EXPOSURE.region_risk * 0.7
            + INSURANCE_EXPOSURE.claims_elasticity * 0.5
        )
        assert r.exposure_score == pytest.approx(expected, abs=0.01)

    def test_recommendations_generated(self):
        r = compute_portfolio_exposure("p1", 0.9, 0.8, 0.7, 0.5)
        assert len(r.recommendations) > 0

    def test_batch(self):
        ids = ["p1", "p2"]
        scores, results = compute_portfolio_exposure_batch(
            ids,
            np.array([0.8, 0.2]),
            np.array([0.6, 0.1]),
            np.array([0.7, 0.3]),
            np.array([0.5, 0.2]),
        )
        assert scores.shape == (2,)
        assert scores[0] > scores[1]
