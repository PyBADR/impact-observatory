"""Tests for friction / resistance model."""

import pytest

from src.engines.physics.friction import FrictionModel, corridor_resistance


class TestFrictionModel:
    def test_base_only(self):
        fm = FrictionModel(base_resistance=0.1)
        assert fm.total_resistance == pytest.approx(0.1)

    def test_all_factors(self):
        fm = FrictionModel(
            base_resistance=0.1,
            political_factor=0.2,
            chokepoint_factor=0.15,
            security_factor=0.1,
        )
        assert fm.total_resistance == pytest.approx(0.55)

    def test_clamped_to_one(self):
        fm = FrictionModel(
            base_resistance=0.5,
            political_factor=0.5,
            chokepoint_factor=0.5,
            security_factor=0.5,
        )
        assert fm.total_resistance <= 1.0

    def test_effective_flow_reduces(self):
        fm = FrictionModel(base_resistance=0.3)
        assert fm.effective_flow(100) == pytest.approx(70.0)

    def test_blocked_delay(self):
        fm = FrictionModel(base_resistance=0.99)
        assert fm.transit_delay_factor() == 100.0


class TestCorridorResistance:
    def test_base_corridor(self):
        resistance, explanation = corridor_resistance(0.1, 0.0, False)
        assert resistance == pytest.approx(0.1)

    def test_chokepoint_adds_penalty(self):
        normal, _ = corridor_resistance(0.1, 0.0, False)
        chokepoint, _ = corridor_resistance(0.1, 0.0, True)
        assert chokepoint > normal

    def test_threat_increases_resistance(self):
        low_threat, _ = corridor_resistance(0.1, 0.2, False)
        high_threat, _ = corridor_resistance(0.1, 0.8, False)
        assert high_threat > low_threat

    def test_explanation_keys(self):
        _, explanation = corridor_resistance(0.1, 0.5, True, 0.3)
        assert "base_resistance" in explanation
        assert "chokepoint_penalty" in explanation
        assert "security_penalty" in explanation
        assert "total_resistance" in explanation
