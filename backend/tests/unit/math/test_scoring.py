"""Tests for scoring functions."""

import pytest

from src.engines.math_core.scoring import (
    composite_risk_score,
    confidence_score,
    disruption_score,
    exposure_score,
)


class TestCompositeRiskScore:
    def test_all_zeros_returns_near_zero(self):
        score, factors = composite_risk_score(0, 0, 0, 0, 0, 0, 0, 0)
        assert score == pytest.approx(0.0, abs=0.01)
        assert len(factors) == 8

    def test_all_ones_returns_one(self):
        score, factors = composite_risk_score(1, 1, 1, 1, 1, 1, 1, 1)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_high_severity_dominates(self):
        score_high, _ = composite_risk_score(1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        score_low, _ = composite_risk_score(0.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        assert score_high > score_low

    def test_factors_have_explanations(self):
        _, factors = composite_risk_score(0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1)
        for f in factors:
            assert f.factor
            assert f.weight > 0
            assert f.detail


class TestDisruptionScore:
    def test_zero_inputs(self):
        score, factors = disruption_score(0, 0, 0, 0, 0)
        assert score == pytest.approx(0.0, abs=0.01)

    def test_clamped_to_unit(self):
        score, _ = disruption_score(1, 1, 1, 1, 1)
        assert 0 <= score <= 1.0


class TestExposureScore:
    def test_high_value_high_exposure(self):
        score, factors = exposure_score(1.0, 1.0, 1.0)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_low_value_low_exposure(self):
        score, _ = exposure_score(0.0, 0.0, 0.0)
        assert score == pytest.approx(0.0, abs=0.01)


class TestConfidenceScore:
    def test_high_quality_high_confidence(self):
        score, factors = confidence_score(
            source_quality=1.0,
            corroboration_count=10,
            data_freshness=1.0,
            signal_agreement=1.0,
        )
        assert score > 0.8

    def test_no_corroboration_lower_confidence(self):
        score_with, _ = confidence_score(0.7, 5, 0.8, 0.7)
        score_without, _ = confidence_score(0.7, 0, 0.8, 0.7)
        assert score_with > score_without

    def test_factors_explained(self):
        _, factors = confidence_score(0.8, 3, 0.9, 0.7)
        assert len(factors) == 4
        assert any("corroboration" in f.factor for f in factors)
