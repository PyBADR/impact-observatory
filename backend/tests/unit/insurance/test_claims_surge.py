"""Tests for insurance claims surge prediction."""

import numpy as np
import pytest

from src.engines.insurance_intelligence.claims_surge import (
    compute_claims_surge,
    compute_claims_surge_batch,
)
from src.engines.math_core.gcc_weights import CLAIMS_SURGE, CLAIMS_UPLIFT


class TestClaimsSurge:
    def test_zero_inputs(self):
        r = compute_claims_surge("e1", 0, 0, 0, 0)
        assert r.surge_score == 0.0
        assert r.classification == "LOW"

    def test_max_inputs(self):
        r = compute_claims_surge("e1", 1, 1, 1, 1)
        assert r.surge_score == pytest.approx(1.0, abs=0.01)
        assert r.classification == "SEVERE"

    def test_claims_uplift(self):
        r = compute_claims_surge(
            "e1", risk=0.8, disruption=0.7, exposure=0.6, policy_sensitivity=0.5,
            base_claims_usd=1_000_000, system_stress=0.5, uncertainty=0.3,
        )
        assert r.claims_uplift_pct > 0
        assert r.estimated_claims_delta_usd > 0

    def test_uplift_formula(self):
        r = compute_claims_surge(
            "e1", risk=0.5, disruption=0.5, exposure=0.5, policy_sensitivity=0.5,
            base_claims_usd=100_000, system_stress=0.4, uncertainty=0.2,
        )
        surge = (CLAIMS_SURGE.risk * 0.5 + CLAIMS_SURGE.disruption * 0.5
                 + CLAIMS_SURGE.exposure * 0.5 + CLAIMS_SURGE.policy_sensitivity * 0.5)
        expected_factor = 1 + CLAIMS_UPLIFT.chi1 * surge + CLAIMS_UPLIFT.chi2 * 0.4 + CLAIMS_UPLIFT.chi3 * 0.2
        expected_delta = 100_000 * (expected_factor - 1)
        assert r.estimated_claims_delta_usd == pytest.approx(expected_delta, rel=0.01)

    def test_batch(self):
        ids = ["e1", "e2"]
        scores, results = compute_claims_surge_batch(
            ids,
            np.array([0.8, 0.2]),
            np.array([0.7, 0.1]),
            np.array([0.6, 0.2]),
            np.array([0.5, 0.1]),
            np.array([500_000, 100_000]),
            system_stress=0.3,
        )
        assert scores.shape == (2,)
        assert scores[0] > scores[1]
