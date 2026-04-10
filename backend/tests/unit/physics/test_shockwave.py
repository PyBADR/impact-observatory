"""Tests for shockwave propagation model."""

import numpy as np
import pytest

from src.engines.physics.shockwave import ShockwaveConfig, ShockwaveModel, propagate_shockwave


@pytest.fixture
def linear_network():
    """3-node linear: 0 → 1 → 2."""
    adj = np.array([
        [0, 0.8, 0],
        [0, 0, 0.6],
        [0, 0, 0],
    ], dtype=np.float64)
    return adj


class TestShockwave:
    def test_origin_starts_with_full_amplitude(self, linear_network):
        model = ShockwaveModel()
        history = model.propagate(linear_network, origin_indices=[0], n_steps=5)
        assert history[0][0] == pytest.approx(1.0)

    def test_wave_reaches_downstream(self, linear_network):
        model = ShockwaveModel()
        history = model.propagate(linear_network, origin_indices=[0], n_steps=10)
        peak = model.peak_impact(history)
        assert peak[1] > 0  # node 1 affected
        assert peak[2] > 0  # node 2 affected

    def test_attenuation(self, linear_network):
        model = ShockwaveModel()
        history = model.propagate(linear_network, origin_indices=[0], n_steps=10)
        peak = model.peak_impact(history)
        # Downstream nodes should have lower peak than origin
        assert peak[0] >= peak[1]
        assert peak[1] >= peak[2]

    def test_convenience_function(self, linear_network):
        peak, history = propagate_shockwave(linear_network, [0], n_steps=5)
        assert peak.shape == (3,)
        assert len(history) == 6  # initial + 5 steps
