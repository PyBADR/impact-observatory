"""Tests for severity projection."""

import pytest

from src.engines.insurance_intelligence.severity_projection import (
    project_severity,
    HORIZONS,
)


class TestSeverityProjection:
    def test_stable_severity(self):
        report = project_severity("e1", current_severity=0.3)
        assert report.trend_direction == "STABLE"
        assert len(report.projections) == len(HORIZONS)

    def test_escalating(self):
        report = project_severity("e1", current_severity=0.3, trend_factor=0.005)
        assert report.trend_direction == "ESCALATING"
        # Later horizons should have higher severity
        sev_24h = report.projections[0].projected_severity
        sev_90d = report.projections[-1].projected_severity
        assert sev_90d > sev_24h

    def test_declining(self):
        report = project_severity("e1", current_severity=0.5, trend_factor=-0.003)
        assert report.trend_direction == "DECLINING"

    def test_scenario_uplift(self):
        report_no = project_severity("e1", current_severity=0.3)
        report_with = project_severity(
            "e1", current_severity=0.3,
            scenario_uplift=0.4, scenario_probability=0.8,
        )
        assert report_with.worst_case_severity > report_no.worst_case_severity

    def test_stress_acceleration(self):
        report = project_severity(
            "e1", current_severity=0.3,
            stress_current=0.7, stress_previous=0.3,
        )
        # Stress delta = 0.4 should accelerate severity
        assert report.projections[0].stress_component > 0

    def test_confidence_decays(self):
        report = project_severity("e1", current_severity=0.5)
        conf_24h = report.projections[0].confidence
        conf_90d = report.projections[-1].confidence
        assert conf_24h > conf_90d

    def test_capped_at_one(self):
        report = project_severity(
            "e1", current_severity=0.9, trend_factor=0.01,
            scenario_uplift=0.5, scenario_probability=1.0,
            stress_current=0.9, stress_previous=0.1,
        )
        for p in report.projections:
            assert p.projected_severity <= 1.0

    def test_recommendations(self):
        report = project_severity(
            "e1", current_severity=0.8, trend_factor=0.005,
            stress_current=0.7, stress_previous=0.5,
        )
        assert len(report.recommendations) > 0
