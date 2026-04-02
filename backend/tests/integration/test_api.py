"""Integration tests for the FastAPI application.

Tests all API endpoints end-to-end using TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.state import init_state


@pytest.fixture(scope="module", autouse=True)
def setup_state():
    init_state()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---- Health ----

class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("ok", "healthy")


# ---- Events ----

class TestEvents:
    def test_list_events(self, client):
        r = client.get("/api/v1/events")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert "events" in data

    def test_threat_field(self, client):
        r = client.get("/api/v1/events/threat-field", params={"lat": 25.0, "lng": 55.0})
        assert r.status_code == 200
        data = r.json()
        assert "threat_intensity" in data


# ---- Conflicts ----

class TestConflicts:
    def test_list_conflicts(self, client):
        r = client.get("/api/v1/conflicts")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data

    def test_event_multipliers(self, client):
        r = client.get("/api/v1/conflicts/event-multipliers")
        assert r.status_code == 200
        data = r.json()
        assert "multipliers" in data
        assert data["multipliers"]["missile_strike"] == 1.40

    def test_threat_field_post(self, client):
        r = client.post("/api/v1/conflicts/threat-field", json={"lat": 25.0, "lng": 55.0})
        assert r.status_code == 200
        data = r.json()
        assert "threat_intensity" in data
        assert "equation" in data


# ---- Incidents ----

class TestIncidents:
    def test_list_incidents(self, client):
        r = client.get("/api/v1/incidents")
        assert r.status_code == 200
        data = r.json()
        assert "incidents" in data

    def test_incident_summary(self, client):
        r = client.get("/api/v1/incidents/summary")
        assert r.status_code == 200
        data = r.json()
        assert "total_incidents" in data
        assert "layers_active" in data


# ---- Flights ----

class TestFlights:
    def test_list_flights(self, client):
        r = client.get("/api/v1/flights")
        assert r.status_code == 200


# ---- Vessels ----

class TestVessels:
    def test_list_vessels(self, client):
        r = client.get("/api/v1/vessels")
        assert r.status_code == 200


# ---- Scores ----

class TestScores:
    def test_risk_score(self, client):
        r = client.post("/api/v1/scores/risk", json={
            "event_severity": 0.7,
            "source_confidence": 0.8,
            "spatial_proximity": 0.6,
        })
        assert r.status_code == 200
        data = r.json()
        assert "score" in data
        assert "factors" in data

    def test_disruption_score(self, client):
        r = client.post("/api/v1/scores/disruption", json={"risk": 0.6})
        assert r.status_code == 200
        data = r.json()
        assert "score" in data

    def test_confidence_score(self, client):
        r = client.get("/api/v1/scores/confidence", params={"source_quality": 0.8})
        assert r.status_code == 200
        data = r.json()
        assert "score" in data


# ---- Scenarios ----

class TestScenarios:
    def test_list_templates(self, client):
        r = client.get("/api/v1/scenario/templates")
        assert r.status_code == 200
        data = r.json()
        assert len(data["templates"]) >= 10

    def test_run_scenario(self, client):
        r = client.post("/api/v1/scenario/run", json={
            "scenario_id": "hormuz_disruption",
            "severity_override": 0.7,
        })
        assert r.status_code == 200
        data = r.json()
        assert "system_stress" in data
        assert "narrative" in data


# ---- Graph ----

class TestGraph:
    def test_propagation_path(self, client):
        r = client.get("/api/v1/graph/propagation-path", params={
            "start_node_id": "hormuz",
        })
        assert r.status_code == 200

    def test_chokepoints(self, client):
        r = client.get("/api/v1/graph/chokepoints")
        assert r.status_code == 200


# ---- Insurance ----

class TestInsurance:
    def test_exposure(self, client):
        r = client.post("/api/v1/insurance/exposure", json={
            "portfolio_id": "p1",
            "tiv_normalized": 0.8,
            "route_dependency": 0.6,
            "region_risk": 0.7,
            "claims_elasticity": 0.5,
        })
        assert r.status_code == 200
        data = r.json()
        assert "exposure_score" in data
        assert "classification" in data

    def test_claims_surge(self, client):
        r = client.post("/api/v1/insurance/claims-surge", json={
            "entity_id": "e1",
            "risk": 0.7,
            "disruption": 0.6,
            "exposure": 0.5,
            "policy_sensitivity": 0.4,
            "base_claims_usd": 1000000,
        })
        assert r.status_code == 200
        data = r.json()
        assert "surge_score" in data
        assert "claims_uplift_pct" in data

    def test_underwriting(self, client):
        r = client.post("/api/v1/insurance/underwriting", json={
            "entity_ids": ["a", "b"],
            "risk_scores": [0.9, 0.3],
            "exposure_scores": [0.8, 0.2],
            "surge_scores": [0.7, 0.1],
        })
        assert r.status_code == 200
        data = r.json()
        assert "total_flagged" in data

    def test_severity_projection(self, client):
        r = client.post("/api/v1/insurance/severity", json={
            "entity_id": "e1",
            "current_severity": 0.5,
            "trend_factor": 0.002,
        })
        assert r.status_code == 200
        data = r.json()
        assert "projections" in data
        assert len(data["projections"]) == 4


# ---- Decision ----

class TestDecision:
    def test_decision_output(self, client):
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["hormuz"],
            "severity": 0.7,
        })
        assert r.status_code == 200
        data = r.json()

        # Must answer all 5 domain questions
        assert "decision" in data
        d = data["decision"]
        assert "what_happened" in d
        assert "what_is_the_impact" in d
        assert "what_is_affected" in d
        assert "how_big_is_the_risk" in d
        assert "recommended_actions" in d

        # Must include system state
        assert "system_state" in data
        assert "total_stress" in data["system_state"]

        # Must include affected nodes
        assert "top_affected" in data
        assert len(data["top_affected"]) > 0

        # Must include metadata
        assert "metadata" in data
        assert data["metadata"]["equation"] == "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U"

    def test_decision_with_insurance(self, client):
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["hormuz", "shipping"],
            "severity": 0.8,
            "include_insurance": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["insurance_impact"] is not None

    def test_decision_no_shock(self, client):
        r = client.post("/api/v1/decision/output", json={})
        assert r.status_code == 200
        data = r.json()
        assert "decision" in data
