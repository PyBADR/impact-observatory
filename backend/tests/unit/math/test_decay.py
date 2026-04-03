"""Tests for spatial and temporal decay functions."""

import numpy as np
import pytest

from src.engines.math_core.decay import haversine_km, spatial_decay, temporal_decay


class TestSpatialDecay:
    def test_zero_distance_returns_one(self):
        assert spatial_decay(0.0) == pytest.approx(1.0)

    def test_large_distance_approaches_zero(self):
        result = spatial_decay(10000.0)
        assert result < 0.01

    def test_decay_is_monotonically_decreasing(self):
        distances = [0, 50, 100, 500, 1000, 5000]
        values = [float(spatial_decay(d)) for d in distances]
        for i in range(1, len(values)):
            assert values[i] < values[i - 1]

    def test_array_input(self):
        distances = np.array([0, 100, 500])
        result = spatial_decay(distances)
        assert result.shape == (3,)
        assert result[0] == pytest.approx(1.0)
        assert result[1] < result[0]
        assert result[2] < result[1]

    def test_custom_lambda(self):
        # Higher lambda = faster decay
        fast = spatial_decay(100, lam=0.05)
        slow = spatial_decay(100, lam=0.001)
        assert fast < slow


class TestTemporalDecay:
    def test_zero_time_returns_one(self):
        assert temporal_decay(0.0) == pytest.approx(1.0)

    def test_large_time_approaches_zero(self):
        result = temporal_decay(10000.0)
        assert result < 0.01

    def test_24_hours_reasonable_freshness(self):
        result = temporal_decay(24.0)
        assert 0.5 < result < 1.0  # still fairly fresh at 24h


class TestHaversine:
    def test_same_point_zero_distance(self):
        assert haversine_km(25.0, 51.0, 25.0, 51.0) == pytest.approx(0.0, abs=0.01)

    def test_known_distance_dubai_riyadh(self):
        # Dubai (25.25, 55.36) to Riyadh (24.96, 46.70) ≈ 870 km
        d = haversine_km(25.25, 55.36, 24.96, 46.70)
        assert 800 < d < 950

    def test_symmetry(self):
        d1 = haversine_km(25.0, 51.0, 26.0, 56.0)
        d2 = haversine_km(26.0, 56.0, 25.0, 51.0)
        assert d1 == pytest.approx(d2, abs=0.01)
