"""Tests for the full GCC Decision Intelligence JSON contract.

Verifies the /decision/output endpoint returns all mandatory fields
matching the platform specification.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.state import init_state


@pytest.fixture(scope="module", autouse=True)
def setup():
    init_state()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestDecisionContract:
    """Verify the full mandatory JSON contract from /decision/output."""

    def _run_decision(self, client, **overrides):
        payload = {
            "shock_node_ids": ["hormuz", "shipping"],
            "severity": 0.8,
            "include_insurance": True,
            "scenario_horizon": "72h",
        }
        payload.update(overrides)
        r = client.post("/api/v1/decision/output", json=payload)
        assert r.status_code == 200
        return r.json()

    def test_top_level_fields(self, client):
        data = self._run_decision(client)

        # All mandatory top-level fields present
        assert "event" in data
        assert "timestamp" in data
        assert "risk_score" in data
        assert "disruption_score" in data
        assert "confidence_score" in data
        assert "system_stress" in data
        assert "affected_airports" in data
        assert "affected_ports" in data
        assert "affected_corridors" in data
        assert "affected_routes" in data
        assert "economic_impact_estimate" in data
        assert "insurance_impact" in data
        assert "recommended_action" in data
        assert "scenario_horizon" in data
        assert "explanation" in data

    def test_scores_0_to_100_scale(self, client):
        data = self._run_decision(client)

        assert 0.0 <= data["risk_score"] <= 100.0
        assert 0.0 <= data["disruption_score"] <= 100.0
        assert 0.0 <= data["confidence_score"] <= 1.0
        assert 0.0 <= data["system_stress"] <= 100.0

    def test_scenario_horizon_passthrough(self, client):
        for horizon in ("24h", "72h", "7d"):
            data = self._run_decision(client, scenario_horizon=horizon)
            assert data["scenario_horizon"] == horizon

    def test_affected_airports_structure(self, client):
        data = self._run_decision(client)

        for airport in data["affected_airports"]:
            assert "node_id" in airport
            assert "label" in airport
            assert "risk_score" in airport
            assert "disruption_score" in airport

    def test_affected_corridors_present(self, client):
        """Hormuz shock should affect corridor nodes."""
        data = self._run_decision(client)
        corridor_ids = {c["node_id"] for c in data["affected_corridors"]}
        assert "hormuz" in corridor_ids or "shipping" in corridor_ids

    def test_insurance_impact_structure(self, client):
        data = self._run_decision(client)
        ins = data["insurance_impact"]

        assert ins is not None
        assert "exposure_score" in ins
        assert "claims_surge_potential" in ins
        assert "underwriting_class" in ins
        assert ins["underwriting_class"] in (
            "standard", "monitored", "restricted", "escalation"
        )
        assert "expected_claims_uplift" in ins
        assert "flagged_entities" in ins

    def test_explanation_structure(self, client):
        data = self._run_decision(client)
        expl = data["explanation"]

        assert "top_causal_factors" in expl
        assert "propagation_path" in expl
        assert "confidence_breakdown" in expl
        assert "weight_config_used" in expl
        assert expl["weight_config_used"] == "GCC_ASSET_CLASS_DEFAULTS"
        assert len(expl["top_causal_factors"]) > 0

    def test_economic_impact_estimate(self, client):
        data = self._run_decision(client)
        assert isinstance(data["economic_impact_estimate"], str)
        assert "$" in data["economic_impact_estimate"]

    def test_recommended_action_is_string(self, client):
        data = self._run_decision(client)
        assert isinstance(data["recommended_action"], str)
        assert len(data["recommended_action"]) > 10

    def test_backward_compat_decision_object(self, client):
        """The nested decision object should still be present for backward compat."""
        data = self._run_decision(client)
        d = data["decision"]

        assert "what_happened" in d
        assert "what_is_the_impact" in d
        assert "what_is_affected" in d
        assert "how_big_is_the_risk" in d
        assert "recommended_actions" in d

    def test_metadata_present(self, client):
        data = self._run_decision(client)
        meta = data["metadata"]
        assert meta["n_nodes"] == 42
        assert meta["equation"] == "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U"
