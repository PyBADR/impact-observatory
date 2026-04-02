"""API contract tests — verify response shapes and required fields.

Ensures all endpoints return the expected structure regardless of data.
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


class TestEventContracts:
    def test_events_shape(self, client):
        r = client.get("/api/v1/events")
        data = r.json()
        assert isinstance(data["count"], int)
        assert isinstance(data["events"], list)

    def test_conflicts_shape(self, client):
        r = client.get("/api/v1/conflicts")
        data = r.json()
        assert "count" in data
        assert "events" in data

    def test_incidents_shape(self, client):
        r = client.get("/api/v1/incidents")
        data = r.json()
        assert "incidents" in data
        for inc in data["incidents"]:
            assert "id" in inc
            assert "type" in inc
            assert "severity" in inc


class TestScoreContracts:
    def test_risk_response_shape(self, client):
        r = client.post("/api/v1/scores/risk", json={"event_severity": 0.5})
        data = r.json()
        assert isinstance(data["score"], float)
        assert isinstance(data["factors"], list)
        for f in data["factors"]:
            assert "factor" in f
            assert "weight" in f
            assert "contribution" in f

    def test_disruption_response_shape(self, client):
        r = client.post("/api/v1/scores/disruption", json={"risk": 0.5})
        data = r.json()
        assert isinstance(data["score"], float)


class TestInsuranceContracts:
    def test_exposure_response_shape(self, client):
        r = client.post("/api/v1/insurance/exposure", json={
            "portfolio_id": "test",
            "tiv_normalized": 0.5,
            "route_dependency": 0.5,
            "region_risk": 0.5,
            "claims_elasticity": 0.5,
        })
        data = r.json()
        required = ["exposure_score", "classification", "recommendations",
                     "tiv_contribution", "route_dependency_contribution",
                     "region_risk_contribution", "claims_elasticity_contribution"]
        for key in required:
            assert key in data, f"Missing: {key}"

    def test_claims_surge_response_shape(self, client):
        r = client.post("/api/v1/insurance/claims-surge", json={
            "entity_id": "test",
            "risk": 0.5,
            "disruption": 0.5,
            "exposure": 0.5,
            "policy_sensitivity": 0.5,
        })
        data = r.json()
        assert "surge_score" in data
        assert "classification" in data
        assert "claims_uplift_pct" in data

    def test_underwriting_response_shape(self, client):
        r = client.post("/api/v1/insurance/underwriting", json={
            "entity_ids": ["a"],
            "risk_scores": [0.8],
            "exposure_scores": [0.7],
            "surge_scores": [0.6],
        })
        data = r.json()
        assert "total_flagged" in data
        assert "items" in data
        assert "summary" in data

    def test_severity_response_shape(self, client):
        r = client.post("/api/v1/insurance/severity", json={
            "entity_id": "test",
            "current_severity": 0.5,
        })
        data = r.json()
        assert len(data["projections"]) == 4
        for p in data["projections"]:
            assert "horizon" in p
            assert "projected_severity" in p
            assert "confidence" in p
            assert "classification" in p


class TestDecisionContracts:
    def test_decision_full_shape(self, client):
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["hormuz"],
            "severity": 0.7,
        })
        data = r.json()

        # Top-level keys
        assert "decision" in data
        assert "system_state" in data
        assert "top_affected" in data
        assert "sector_impacts" in data
        assert "risk_vector" in data
        assert "metadata" in data

        # System state
        ss = data["system_state"]
        assert "total_stress" in ss
        assert "stress_classification" in ss
        assert "system_energy" in ss
        assert "confidence" in ss

        # Top affected entities
        for ent in data["top_affected"]:
            assert "node_id" in ent
            assert "label" in ent
            assert "risk_score" in ent or "risk" in ent
            assert "disruption_score" in ent or "disruption" in ent
            assert "sector" in ent

        # Risk vector length matches node count
        assert len(data["risk_vector"]) == data["metadata"]["n_nodes"]


class TestGraphContracts:
    def test_propagation_path_shape(self, client):
        r = client.get("/api/v1/graph/propagation-path", params={"start_node_id": "hormuz"})
        data = r.json()
        assert "start" in data
        assert "paths" in data
        assert isinstance(data["paths"], list)

    def test_chokepoints_shape(self, client):
        r = client.get("/api/v1/graph/chokepoints")
        data = r.json()
        assert "chokepoints" in data
        for cp in data["chokepoints"]:
            assert "node_id" in cp
            assert "in_degree" in cp
