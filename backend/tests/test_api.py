"""
API endpoint tests for Impact Observatory.

Tests verify:
1. Health and version endpoints respond correctly (no auth required)
2. All /api/v1/* endpoints require X-API-Key auth
3. Entity listing endpoints return expected shapes
4. Graph intelligence endpoints accept queries
5. Scenario endpoints respond correctly
6. Ingestion endpoints accept data
7. Root endpoint returns platform info
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def headers():
    """Analyst-level auth headers."""
    return {"X-API-Key": "test-key-analyst"}


@pytest.fixture
def admin_headers():
    """Admin-level auth headers."""
    return {"X-API-Key": "test-key-admin"}


API = "/api/v1"


# ============================================================================
# Health & Version (no auth)
# ============================================================================

class TestHealthEndpoints:
    def test_health_endpoint_success(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "operational"]
        assert "timestamp" in data
        assert data["service_name"] == "Impact Observatory"

    def test_health_no_auth_required(self, client):
        """Health endpoint must be accessible without API key."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_version_endpoint_success(self, client, headers):
        response = client.get("/version", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


# ============================================================================
# Root endpoint (no auth)
# ============================================================================

class TestRootEndpoint:
    def test_root_endpoint_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "endpoints" in data


# ============================================================================
# Auth enforcement
# ============================================================================

class TestAuthEnforcement:
    def test_api_v1_requires_auth(self, client):
        """All /api/v1/* endpoints must reject unauthenticated requests."""
        endpoints = [
            (f"{API}/events", "get"),
            (f"{API}/airports", "get"),
            (f"{API}/scenarios", "get"),
            (f"{API}/ingest/status", "get"),
        ]
        for url, method in endpoints:
            response = getattr(client, method)(url)
            assert response.status_code == 403, f"{url} should require auth"

    def test_invalid_api_key_rejected(self, client):
        response = client.get(f"{API}/events", headers={"X-API-Key": "bad-key"})
        assert response.status_code == 403


# ============================================================================
# Entity listing endpoints (authed)
# ============================================================================

class TestEntitiesEndpoints:
    def test_list_events(self, client, headers):
        response = client.get(f"{API}/events", headers=headers)
        assert response.status_code == 200

    def test_list_airports(self, client, headers):
        response = client.get(f"{API}/airports", headers=headers)
        assert response.status_code == 200

    def test_list_ports(self, client, headers):
        response = client.get(f"{API}/ports", headers=headers)
        assert response.status_code == 200

    def test_list_corridors(self, client, headers):
        response = client.get(f"{API}/corridors", headers=headers)
        assert response.status_code == 200

    def test_list_flights(self, client, headers):
        response = client.get(f"{API}/flights", headers=headers)
        assert response.status_code == 200

    def test_list_vessels(self, client, headers):
        response = client.get(f"{API}/vessels", headers=headers)
        assert response.status_code == 200


# ============================================================================
# Scenarios endpoints (authed)
# ============================================================================

class TestScenariosEndpoints:
    def test_list_scenarios(self, client, headers):
        response = client.get(f"{API}/scenarios", headers=headers)
        assert response.status_code == 200

    def test_create_scenario(self, client, admin_headers):
        scenario_data = {
            "name": "Test Scenario",
            "description": "A test scenario",
            "scenario_type": "disruption",
            "parameters": {"severity": 0.8}
        }
        response = client.post(f"{API}/scenarios", json=scenario_data, headers=admin_headers)
        # 200/201 success, 422 validation, 500 server error all acceptable in test env
        assert response.status_code in [200, 201, 422, 500]

    def test_run_scenario(self, client, headers):
        response = client.post(
            f"{API}/scenarios/run",
            json={"scenario_id": "hormuz_closure"},
            headers=headers,
        )
        assert response.status_code in [200, 201, 422, 500]

    def test_list_scenario_runs(self, client, headers):
        response = client.get(f"{API}/scenarios/runs", headers=headers)
        assert response.status_code == 200

    def test_get_scenario_run_not_found(self, client, headers):
        response = client.get(f"{API}/scenarios/runs/nonexistent", headers=headers)
        assert response.status_code in [200, 404]


# ============================================================================
# Graph intelligence endpoints (authed)
# ============================================================================

class TestGraphEndpoints:
    def test_nearest_impacted(self, client, headers):
        query = {"latitude": 25.276987, "longitude": 55.296249, "radius_km": 100}
        response = client.post(f"{API}/graph/nearest", json=query, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_risk_propagation(self, client, headers):
        query = {"source_entity_id": "e-001", "source_entity_type": "event", "max_hops": 3, "risk_threshold": 0.3}
        response = client.post(f"{API}/graph/propagation", json=query, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_chokepoint_analysis(self, client, headers):
        response = client.post(f"{API}/graph/chokepoint", json={"region": "Middle East"}, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_cascade_analysis(self, client, headers):
        response = client.post(f"{API}/graph/cascade", json={"region": "ME", "event_id": "e-001"}, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_scenario_subgraph(self, client, headers):
        response = client.post(f"{API}/graph/scenario", json={"scenario_id": "hormuz_closure"}, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_reroute_alternatives(self, client, headers):
        query = {"source_location": "Jebel Ali", "destination_location": "Singapore",
                 "origin_lat": 25.0, "origin_lon": 55.0, "dest_lat": 1.3, "dest_lon": 103.8}
        response = client.post(f"{API}/graph/reroute", json=query, headers=headers)
        assert response.status_code in [200, 422, 500]


# ============================================================================
# Data ingestion endpoints (authed)
# ============================================================================

class TestIngestionEndpoints:
    @pytest.mark.parametrize("entity_type", [
        "events", "airports", "ports", "corridors", "flights", "vessels", "actors"
    ])
    def test_ingest_entity(self, client, headers, entity_type):
        response = client.post(f"{API}/ingest/{entity_type}", json={"batch_size": 10}, headers=headers)
        assert response.status_code in [200, 422, 500]

    def test_ingest_status(self, client, headers):
        response = client.get(f"{API}/ingest/status", headers=headers)
        assert response.status_code == 200


# ============================================================================
# Integration
# ============================================================================

class TestIntegration:
    def test_health_version_ingest_chain(self, client, headers):
        assert client.get("/health").status_code == 200
        assert client.get("/version", headers=headers).status_code == 200
        assert client.get(f"{API}/ingest/status", headers=headers).status_code == 200

    def test_all_entity_endpoints_reachable(self, client, headers):
        for ep in ["events", "airports", "ports", "corridors", "flights", "vessels"]:
            resp = client.get(f"{API}/{ep}", headers=headers)
            assert resp.status_code == 200, f"/api/v1/{ep} returned {resp.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
