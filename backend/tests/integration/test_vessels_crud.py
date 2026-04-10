"""Integration tests for vessels CRUD + risk + proximity endpoints."""

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


class TestVesselsList:
    def test_list_all(self, client):
        r = client.get("/api/v1/vessels")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert "vessels" in data
        assert "total" in data

    def test_filter_by_type(self, client):
        r = client.get("/api/v1/vessels", params={"vessel_type": "tanker"})
        data = r.json()
        for v in data["vessels"]:
            assert v["vessel_type"] == "tanker"

    def test_filter_by_destination(self, client):
        r = client.get("/api/v1/vessels", params={"destination": "jebel_ali"})
        data = r.json()
        for v in data["vessels"]:
            assert v["destination_port_id"] == "jebel_ali"

    def test_speed_filter(self, client):
        r = client.get("/api/v1/vessels", params={"min_speed": 10.0, "max_speed": 13.0})
        data = r.json()
        for v in data["vessels"]:
            assert 10.0 <= v["speed_knots"] <= 13.0


class TestVesselCRUD:
    def test_create_vessel(self, client):
        r = client.post("/api/v1/vessels", json={
            "name": "Test Runner",
            "mmsi": "999000001",
            "vessel_type": "container",
            "latitude": 26.0,
            "longitude": 53.0,
            "speed_knots": 11.0,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test Runner"
        assert data["mmsi"] == "999000001"

    def test_create_duplicate_mmsi(self, client):
        # First create
        client.post("/api/v1/vessels", json={
            "name": "Dup Test",
            "mmsi": "888000001",
            "vessel_type": "cargo",
        })
        # Duplicate
        r = client.post("/api/v1/vessels", json={
            "name": "Dup Test 2",
            "mmsi": "888000001",
            "vessel_type": "cargo",
        })
        assert r.status_code == 409

    def test_get_vessel(self, client):
        r = client.get("/api/v1/vessels/vsl-001")
        assert r.status_code == 200
        assert r.json()["name"] == "Gulf Voyager"

    def test_get_vessel_not_found(self, client):
        r = client.get("/api/v1/vessels/nonexistent")
        assert r.status_code == 404

    def test_update_vessel(self, client):
        r = client.put("/api/v1/vessels/vsl-001", json={"speed_knots": 8.0})
        assert r.status_code == 200
        assert r.json()["speed_knots"] == 8.0

    def test_delete_vessel(self, client):
        r = client.post("/api/v1/vessels", json={
            "name": "Delete Me",
            "mmsi": "777000001",
            "vessel_type": "bulk",
        })
        vid = r.json()["id"]
        r2 = client.delete(f"/api/v1/vessels/{vid}")
        assert r2.status_code == 204
        r3 = client.get(f"/api/v1/vessels/{vid}")
        assert r3.status_code == 404


class TestVesselRisk:
    def test_single_vessel_risk(self, client):
        r = client.get("/api/v1/vessels/vsl-001/risk")
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert "classification" in data
        assert "factors" in data
        assert data["classification"] in (
            "NOMINAL", "LOW", "MODERATE", "ELEVATED", "CRITICAL"
        )
        # Gulf Voyager is near Hormuz — should have some risk
        assert data["risk_score"] > 0.0

    def test_batch_vessel_risk(self, client):
        r = client.post("/api/v1/vessels/risk/batch")
        assert r.status_code == 200
        data = r.json()
        assert "assessments" in data
        assert data["count"] >= 1
        scores = [a["risk_score"] for a in data["assessments"]]
        assert scores == sorted(scores, reverse=True)


class TestVesselNearby:
    def test_nearby_search(self, client):
        # Search near Hormuz
        r = client.get("/api/v1/vessels/nearby/search", params={
            "lat": 26.5, "lng": 56.0, "radius_km": 500,
        })
        assert r.status_code == 200
        data = r.json()
        assert "vessels" in data
        for v in data["vessels"]:
            assert "distance_km" in v
            assert v["distance_km"] <= 500

    def test_nearby_no_results(self, client):
        # Far from all vessels
        r = client.get("/api/v1/vessels/nearby/search", params={
            "lat": -30.0, "lng": 0.0, "radius_km": 10,
        })
        data = r.json()
        assert data["count"] == 0
