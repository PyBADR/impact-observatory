"""Integration tests for flights CRUD + risk + proximity endpoints."""

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


class TestFlightsList:
    def test_list_all(self, client):
        r = client.get("/api/v1/flights")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert "flights" in data
        assert "total" in data

    def test_filter_by_status(self, client):
        r = client.get("/api/v1/flights", params={"status": "en_route"})
        data = r.json()
        for f in data["flights"]:
            assert f["status"] == "en_route"

    def test_filter_by_origin(self, client):
        r = client.get("/api/v1/flights", params={"origin": "dubai_apt"})
        data = r.json()
        for f in data["flights"]:
            assert f["origin_airport_id"] == "dubai_apt"

    def test_pagination(self, client):
        r = client.get("/api/v1/flights", params={"limit": 1, "offset": 0})
        data = r.json()
        assert data["count"] <= 1


class TestFlightCRUD:
    def test_create_flight(self, client):
        r = client.post("/api/v1/flights", json={
            "flight_number": "GF100",
            "origin_airport_id": "bahrain_apt",
            "destination_airport_id": "doha_apt",
            "latitude": 25.5,
            "longitude": 51.0,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["flight_number"] == "GF100"
        assert data["id"].startswith("flt-")
        return data["id"]

    def test_get_flight(self, client):
        r = client.get("/api/v1/flights/flt-001")
        assert r.status_code == 200
        assert r.json()["flight_number"] == "EK501"

    def test_get_flight_not_found(self, client):
        r = client.get("/api/v1/flights/nonexistent")
        assert r.status_code == 404

    def test_update_flight(self, client):
        r = client.put("/api/v1/flights/flt-001", json={"status": "landed"})
        assert r.status_code == 200
        assert r.json()["status"] == "landed"

    def test_delete_flight(self, client):
        # Create then delete
        r = client.post("/api/v1/flights", json={
            "flight_number": "DEL01",
            "origin_airport_id": "riyadh_apt",
            "destination_airport_id": "muscat_apt",
        })
        fid = r.json()["id"]
        r2 = client.delete(f"/api/v1/flights/{fid}")
        assert r2.status_code == 204
        r3 = client.get(f"/api/v1/flights/{fid}")
        assert r3.status_code == 404


class TestFlightRisk:
    def test_single_flight_risk(self, client):
        r = client.get("/api/v1/flights/flt-001/risk")
        assert r.status_code == 200
        data = r.json()
        assert "risk_score" in data
        assert "classification" in data
        assert "factors" in data
        assert data["classification"] in (
            "NOMINAL", "LOW", "MODERATE", "ELEVATED", "CRITICAL"
        )

    def test_batch_flight_risk(self, client):
        r = client.post("/api/v1/flights/risk/batch")
        assert r.status_code == 200
        data = r.json()
        assert "assessments" in data
        assert data["count"] >= 1
        # Should be sorted by risk descending
        scores = [a["risk_score"] for a in data["assessments"]]
        assert scores == sorted(scores, reverse=True)


class TestFlightNearby:
    def test_nearby_search(self, client):
        # Search near Dubai
        r = client.get("/api/v1/flights/nearby/search", params={
            "lat": 25.0, "lng": 55.0, "radius_km": 1000,
        })
        assert r.status_code == 200
        data = r.json()
        assert "flights" in data
        # All returned flights should have distance
        for f in data["flights"]:
            assert "distance_km" in f
            assert f["distance_km"] <= 1000
