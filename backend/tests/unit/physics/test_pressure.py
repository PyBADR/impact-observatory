"""Tests for pressure accumulation model."""

import pytest

from src.engines.physics.pressure import NodePressure, PressureModel, congestion_pressure


class TestNodePressure:
    def test_zero_flow_zero_pressure(self):
        np = NodePressure(node_id="test", flow=0, vulnerability=0.5, threat_intensity=0.8)
        assert np.pressure == pytest.approx(0.0)

    def test_high_all_high_pressure(self):
        np = NodePressure(node_id="test", flow=1.0, vulnerability=1.0, threat_intensity=1.0)
        assert np.pressure == pytest.approx(1.0)

    def test_stress_includes_congestion(self):
        n1 = NodePressure(node_id="a", flow=0.5, vulnerability=0.5, threat_intensity=0.5, congestion=0.0)
        n2 = NodePressure(node_id="b", flow=0.5, vulnerability=0.5, threat_intensity=0.5, congestion=1.0)
        assert n2.stress > n1.stress


class TestPressureModel:
    def test_system_stress_zero_for_empty(self):
        model = PressureModel()
        assert model.system_stress() == 0.0

    def test_system_stress_aggregates(self):
        model = PressureModel()
        model.add_node("a", flow=0.5, vulnerability=0.5, threat_intensity=0.5)
        model.add_node("b", flow=0.8, vulnerability=0.8, threat_intensity=0.8)
        assert model.system_stress() > 0


class TestCongestionPressure:
    def test_zero_traffic(self):
        pressure, explanation = congestion_pressure(0, 100)
        assert pressure == pytest.approx(0.0, abs=0.05)

    def test_at_capacity(self):
        pressure, explanation = congestion_pressure(100, 100)
        assert pressure > 0.2

    def test_over_capacity(self):
        at_cap, _ = congestion_pressure(100, 100)
        over_cap, _ = congestion_pressure(200, 100)
        assert over_cap > at_cap

    def test_threat_amplifies(self):
        without_threat, _ = congestion_pressure(50, 100, threat_level=0.0)
        with_threat, _ = congestion_pressure(50, 100, threat_level=0.8)
        assert with_threat > without_threat
