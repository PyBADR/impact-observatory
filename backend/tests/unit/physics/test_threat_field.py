"""Tests for threat field model."""

import pytest

from src.engines.physics.threat_field import ThreatField, compute_threat_at_point


class TestThreatField:
    def test_empty_field_returns_zero(self):
        field = ThreatField()
        assert field.evaluate(25.0, 51.0) == 0.0

    def test_at_source_returns_severity(self):
        field = ThreatField()
        field.add_source(lat=25.0, lng=51.0, severity=0.8)
        result = field.evaluate(25.0, 51.0)
        assert result == pytest.approx(0.8, abs=0.01)

    def test_decays_with_distance(self):
        field = ThreatField()
        field.add_source(lat=25.0, lng=51.0, severity=0.8)
        at_source = field.evaluate(25.0, 51.0)
        far_away = field.evaluate(30.0, 60.0)
        assert at_source > far_away

    def test_additive_sources(self):
        field = ThreatField()
        field.add_source(lat=25.0, lng=51.0, severity=0.5)
        single = field.evaluate(25.0, 51.0)

        field.add_source(lat=25.0, lng=51.0, severity=0.3)
        double = field.evaluate(25.0, 51.0)
        assert double > single

    def test_grid_evaluation(self):
        field = ThreatField()
        field.add_source(lat=25.0, lng=51.0, severity=0.9)
        lats, lngs, grid = field.evaluate_grid((24, 26), (50, 52), resolution=10)
        assert grid.shape == (10, 10)
        assert grid.max() > 0


class TestComputeThreatAtPoint:
    def test_with_events(self):
        events = [
            {"lat": 26.5, "lng": 56.3, "severity_score": 0.8},
            {"lat": 25.0, "lng": 51.0, "severity_score": 0.6},
        ]
        threat, contributors = compute_threat_at_point(26.5, 56.3, events)
        assert threat > 0
        assert len(contributors) == 2
        assert contributors[0]["influence"] >= contributors[1]["influence"]

    def test_empty_events(self):
        threat, contributors = compute_threat_at_point(25.0, 51.0, [])
        assert threat == 0.0
        assert contributors == []
