"""Tests for GCC-tuned confidence scoring."""

import numpy as np
import pytest

from src.engines.math_core.confidence import (
    compute_confidence,
    compute_system_confidence,
    compute_confidence_vector,
)


class TestConfidence:
    def test_perfect_data(self):
        bd = compute_confidence("n1", 1.0, 1.0, 1.0, 1.0)
        assert bd.confidence == pytest.approx(1.0, abs=0.01)
        assert bd.uncertainty == pytest.approx(0.0, abs=0.01)
        assert bd.classification == "HIGH"

    def test_no_data(self):
        bd = compute_confidence("n1", 0.0, 0.0, 0.0, 0.0)
        assert bd.confidence == pytest.approx(0.0, abs=0.01)
        assert bd.uncertainty == pytest.approx(1.0, abs=0.01)
        assert bd.classification == "VERY_LOW"

    def test_partial(self):
        bd = compute_confidence("n1", 0.8, 0.6, 0.7, 0.5)
        assert 0.0 < bd.confidence < 1.0
        assert bd.confidence + bd.uncertainty == pytest.approx(1.0, abs=0.001)

    def test_classification_thresholds(self):
        high = compute_confidence("n", 1.0, 1.0, 0.8, 0.8)
        assert high.classification == "HIGH"

        mod = compute_confidence("n", 0.6, 0.6, 0.6, 0.6)
        assert mod.classification in ("HIGH", "MODERATE")

        low = compute_confidence("n", 0.3, 0.3, 0.3, 0.3)
        assert low.classification in ("LOW", "VERY_LOW")


class TestSystemConfidence:
    def test_uniform(self):
        risk = np.array([0.5, 0.5])
        conf = np.array([0.8, 0.8])
        assert compute_system_confidence(risk, conf) == pytest.approx(0.8, abs=0.01)

    def test_weighted_by_risk(self):
        risk = np.array([0.9, 0.1])
        conf = np.array([0.3, 0.9])
        sc = compute_system_confidence(risk, conf)
        # High-risk node has low confidence, so system confidence should be low
        assert sc < 0.5

    def test_no_risk(self):
        risk = np.zeros(3)
        conf = np.array([0.7, 0.8, 0.9])
        sc = compute_system_confidence(risk, conf)
        assert sc == pytest.approx(0.8, abs=0.01)  # mean


class TestConfidenceVector:
    def test_batch(self):
        vec, bds = compute_confidence_vector(["a", "b"], np.array([0.9, 0.5]))
        assert vec.shape == (2,)
        assert len(bds) == 2
