"""Macro Intelligence Layer — Pack 1 API Route Tests.

Covers:
  1. POST /api/v1/macro/signals — valid signal → 201
  2. POST with invalid fields → 422
  3. POST with invalid enum values → 422
  4. POST with out-of-range severity → 422
  5. POST with extended fields (signal_type, country_scope, sector_scope, raw_payload)
  6. GET /api/v1/macro/signals — list route (empty, after insert)
  7. GET /api/v1/macro/signals/{id} — by id route
  8. GET with unknown id → 404
  9. Deduplication (same content → same registry entry)
  10. Filter query parameters
"""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.macro import router as macro_router
from src.macro.macro_signal_service import (
    MacroSignalService,
    SignalRegistry,
    get_signal_service,
)


# ── App factory ───────────────────────────────────────────────────────────────

def _make_app(service: MacroSignalService) -> TestClient:
    """Build isolated FastAPI app with fresh service per test."""
    app = FastAPI()
    app.include_router(macro_router)
    app.dependency_overrides[get_signal_service] = lambda: service
    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    svc = MacroSignalService(registry=SignalRegistry())
    return _make_app(svc)


@pytest.fixture
def client_with_service():
    """Returns (client, service) for tests that need direct service access."""
    svc = MacroSignalService(registry=SignalRegistry())
    return _make_app(svc), svc


# ── Payload helper ────────────────────────────────────────────────────────────

def _payload(**overrides) -> dict:
    base = {
        "title": "Route test: Strait of Hormuz partial blockage",
        "source": "geopolitical",
        "severity_score": 0.72,
        "direction": "negative",
        "confidence": "high",
        "regions": ["AE", "OM"],
        "impact_domains": ["oil_gas", "maritime"],
        "ttl_hours": 48,
        "tags": ["hormuz", "blockage"],
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VALID POST → 201
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostSignal:
    def test_valid_post_returns_201(self, client):
        resp = client.post("/api/v1/macro/signals", json=_payload())
        assert resp.status_code == 201

    def test_201_response_contains_signal_id(self, client):
        data = client.post("/api/v1/macro/signals", json=_payload()).json()
        assert "signal_id" in data
        # Must be a valid UUID
        from uuid import UUID
        UUID(data["signal_id"])

    def test_201_response_contains_registry_id(self, client):
        data = client.post("/api/v1/macro/signals", json=_payload()).json()
        assert "registry_id" in data
        from uuid import UUID
        UUID(data["registry_id"])

    def test_201_severity_level_correct(self, client):
        """severity_score 0.72 → HIGH."""
        data = client.post("/api/v1/macro/signals", json=_payload()).json()
        assert data["severity_level"] == "high"

    def test_201_content_hash_is_64_chars(self, client):
        data = client.post("/api/v1/macro/signals", json=_payload()).json()
        assert "content_hash" in data
        assert len(data["content_hash"]) == 64

    def test_201_status_is_registered(self, client):
        data = client.post("/api/v1/macro/signals", json=_payload()).json()
        assert data["status"] == "registered"

    def test_post_with_minimal_fields(self, client):
        minimal = {
            "title": "Minimal route test signal input",
            "source": "market",
            "severity_score": 0.3,
            "direction": "negative",
            "regions": ["SA"],
        }
        resp = client.post("/api/v1/macro/signals", json=minimal)
        assert resp.status_code == 201

    def test_post_with_mixed_direction(self, client):
        data = client.post(
            "/api/v1/macro/signals",
            json=_payload(direction="mixed", severity_score=0.7),
        ).json()
        assert data["status"] == "registered"

    def test_post_with_uncertain_direction_low_severity(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(direction="uncertain", severity_score=0.3),
        )
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# 2. INVALID FIELDS → 422
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostInvalidFields:
    def test_missing_title_422(self, client):
        payload = _payload()
        del payload["title"]
        assert client.post("/api/v1/macro/signals", json=payload).status_code == 422

    def test_missing_source_422(self, client):
        payload = _payload()
        del payload["source"]
        assert client.post("/api/v1/macro/signals", json=payload).status_code == 422

    def test_missing_direction_422(self, client):
        payload = _payload()
        del payload["direction"]
        assert client.post("/api/v1/macro/signals", json=payload).status_code == 422

    def test_missing_regions_422(self, client):
        payload = _payload()
        del payload["regions"]
        assert client.post("/api/v1/macro/signals", json=payload).status_code == 422

    def test_empty_regions_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(regions=[])
        ).status_code == 422

    def test_title_too_short_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(title="Hi")
        ).status_code == 422

    def test_neutral_direction_high_severity_422(self, client):
        """Cross-field: NEUTRAL + severity >= 0.65 is contradictory."""
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(direction="neutral", severity_score=0.85),
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "errors" in detail
        assert any("contradictory" in e for e in detail["errors"])

    def test_uncertain_direction_high_severity_422(self, client):
        """Cross-field: UNCERTAIN + severity >= 0.65 is also contradictory."""
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(direction="uncertain", severity_score=0.80),
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INVALID ENUM VALUES → 422
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostInvalidEnums:
    def test_invalid_source_enum_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(source="unknown_source")
        ).status_code == 422

    def test_invalid_direction_enum_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(direction="sideways")
        ).status_code == 422

    def test_invalid_confidence_enum_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(confidence="maybe")
        ).status_code == 422

    def test_invalid_region_code_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(regions=["XX"])
        ).status_code == 422

    def test_invalid_signal_type_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(signal_type="not_a_type")
        ).status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# 4. OUT-OF-RANGE SEVERITY → 422
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostSeverityRange:
    def test_severity_above_1_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(severity_score=1.01)
        ).status_code == 422

    def test_severity_below_0_422(self, client):
        assert client.post(
            "/api/v1/macro/signals", json=_payload(severity_score=-0.1)
        ).status_code == 422

    def test_severity_exactly_0_201(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(severity_score=0.0, direction="positive"),
        )
        assert resp.status_code == 201

    def test_severity_exactly_1_201(self, client):
        resp = client.post(
            "/api/v1/macro/signals", json=_payload(severity_score=1.0)
        )
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXTENDED FIELDS IN POST
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostExtendedFields:
    def test_signal_type_accepted(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(signal_type="commodity"),
        )
        assert resp.status_code == 201

    def test_country_scope_accepted(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(country_scope=["Kuwait", "Iraq"]),
        )
        assert resp.status_code == 201

    def test_sector_scope_accepted(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(sector_scope=["oil", "banking"]),
        )
        assert resp.status_code == 201

    def test_raw_payload_accepted(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(raw_payload={"ref": "bloomberg-001", "score": 0.85}),
        )
        assert resp.status_code == 201

    def test_all_signal_types_accepted(self, client):
        """All 8 SignalType values must be accepted by the API."""
        for idx, signal_type in enumerate([
            "geopolitical", "policy", "market", "commodity",
            "regulatory", "logistics", "sentiment", "systemic",
        ]):
            resp = client.post(
                "/api/v1/macro/signals",
                json=_payload(
                    title=f"Type test signal for {signal_type} classification",
                    signal_type=signal_type,
                    severity_score=round(0.2 + 0.08 * idx, 2),  # 0.20…0.76
                ),
            )
            assert resp.status_code == 201, f"signal_type={signal_type} failed: {resp.text}"

    def test_country_scope_deduped_in_registry(self, client_with_service):
        client, svc = client_with_service
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(country_scope=["UAE", " UAE ", "Oman"]),
        )
        assert resp.status_code == 201
        registry_id = resp.json()["registry_id"]
        entry = svc.get_by_registry_id(__import__("uuid").UUID(registry_id))
        assert entry.signal.country_scope == ["Oman", "UAE"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. GET /api/v1/macro/signals — LIST ROUTE
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetSignalsList:
    def test_empty_list_returns_200(self, client):
        resp = client.get("/api/v1/macro/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["entries"] == []

    def test_list_after_post_returns_entry(self, client):
        client.post("/api/v1/macro/signals", json=_payload())
        resp = client.get("/api/v1/macro/signals")
        data = resp.json()
        assert data["total"] == 1
        assert len(data["entries"]) == 1

    def test_list_pagination_limit(self, client):
        for i in range(5):
            client.post(
                "/api/v1/macro/signals",
                json=_payload(
                    title=f"Pagination test signal number {i} in sequence",
                    severity_score=0.2 + 0.1 * i,
                ),
            )
        resp = client.get("/api/v1/macro/signals?limit=3")
        data = resp.json()
        assert data["total"] == 5
        assert len(data["entries"]) == 3

    def test_list_pagination_offset(self, client):
        for i in range(5):
            client.post(
                "/api/v1/macro/signals",
                json=_payload(
                    title=f"Offset test signal entry number {i} in sequence",
                    severity_score=0.2 + 0.1 * i,
                ),
            )
        resp = client.get("/api/v1/macro/signals?limit=10&offset=3")
        data = resp.json()
        assert len(data["entries"]) == 2  # 5 total, skip 3

    def test_list_response_has_required_keys(self, client):
        client.post("/api/v1/macro/signals", json=_payload())
        data = client.get("/api/v1/macro/signals").json()
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert "entries" in data

    def test_list_filter_by_source(self, client):
        client.post("/api/v1/macro/signals", json=_payload(source="geopolitical"))
        client.post(
            "/api/v1/macro/signals",
            json=_payload(
                title="Economic filter test signal for source filtering",
                source="economic",
                severity_score=0.45,
            ),
        )
        data = client.get("/api/v1/macro/signals?source=economic").json()
        assert data["total"] == 1
        assert data["entries"][0]["signal"]["source"] == "economic"

    def test_list_entries_sorted_newest_first(self, client):
        for i in range(3):
            client.post(
                "/api/v1/macro/signals",
                json=_payload(
                    title=f"Sort order test signal entry number {i}",
                    severity_score=0.3 + 0.1 * i,
                ),
            )
        data = client.get("/api/v1/macro/signals").json()
        entries = data["entries"]
        times = [e["registered_at"] for e in entries]
        assert times == sorted(times, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GET /api/v1/macro/signals/{id} — BY ID ROUTE
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetSignalById:
    def test_get_by_id_returns_200(self, client):
        registry_id = client.post(
            "/api/v1/macro/signals", json=_payload()
        ).json()["registry_id"]
        resp = client.get(f"/api/v1/macro/signals/{registry_id}")
        assert resp.status_code == 200

    def test_get_by_id_contains_entry(self, client):
        registry_id = client.post(
            "/api/v1/macro/signals", json=_payload()
        ).json()["registry_id"]
        data = client.get(f"/api/v1/macro/signals/{registry_id}").json()
        assert "entry" in data
        assert data["entry"]["registry_id"] == registry_id

    def test_get_by_id_signal_fields_present(self, client):
        registry_id = client.post(
            "/api/v1/macro/signals", json=_payload()
        ).json()["registry_id"]
        entry = client.get(f"/api/v1/macro/signals/{registry_id}").json()["entry"]
        signal = entry["signal"]
        assert "signal_id" in signal
        assert "title" in signal
        assert "severity_level" in signal
        assert "content_hash" in signal
        assert "normalization_version" in signal

    def test_get_by_id_extended_fields_present(self, client):
        resp = client.post(
            "/api/v1/macro/signals",
            json=_payload(
                signal_type="logistics",
                country_scope=["Kuwait"],
                sector_scope=["shipping"],
                raw_payload={"ref": "test-001"},
            ),
        )
        registry_id = resp.json()["registry_id"]
        entry = client.get(f"/api/v1/macro/signals/{registry_id}").json()["entry"]
        signal = entry["signal"]
        assert signal["signal_type"] == "logistics"
        assert "Kuwait" in signal["country_scope"]
        assert "shipping" in signal["sector_scope"]
        assert signal["raw_payload"] == {"ref": "test-001"}


# ═══════════════════════════════════════════════════════════════════════════════
# 8. 404 ON MISSING ID
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotFound:
    def test_unknown_registry_id_returns_404(self, client):
        fake_id = str(uuid4())
        resp = client.get(f"/api/v1/macro/signals/{fake_id}")
        assert resp.status_code == 404

    def test_404_response_has_detail(self, client):
        fake_id = str(uuid4())
        data = client.get(f"/api/v1/macro/signals/{fake_id}").json()
        assert "detail" in data

    def test_404_after_delete_not_applicable(self, client):
        """Registry is append-only in Pack 1 — no delete endpoint exists."""
        resp = client.delete(f"/api/v1/macro/signals/{uuid4()}")
        assert resp.status_code == 405  # Method Not Allowed


# ═══════════════════════════════════════════════════════════════════════════════
# 9. DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeduplication:
    def test_identical_content_returns_same_registry_entry(self, client):
        fixed_time = "2026-03-01T12:00:00+00:00"
        p = _payload(event_time=fixed_time)
        id1 = client.post("/api/v1/macro/signals", json=p).json()["registry_id"]
        id2 = client.post("/api/v1/macro/signals", json=p).json()["registry_id"]
        assert id1 == id2

    def test_dedup_does_not_increase_registry_size(self, client):
        fixed_time = "2026-03-02T12:00:00+00:00"
        p = _payload(event_time=fixed_time)
        client.post("/api/v1/macro/signals", json=p)
        client.post("/api/v1/macro/signals", json=p)
        data = client.get("/api/v1/macro/signals").json()
        assert data["total"] == 1

    def test_different_severity_not_deduped(self, client):
        fixed_time = "2026-03-03T12:00:00+00:00"
        client.post("/api/v1/macro/signals", json=_payload(
            severity_score=0.3, event_time=fixed_time
        ))
        client.post("/api/v1/macro/signals", json=_payload(
            severity_score=0.8, event_time=fixed_time
        ))
        data = client.get("/api/v1/macro/signals").json()
        assert data["total"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 10. AUXILIARY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuxiliaryEndpoints:
    def test_stats_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/macro/stats")
        assert resp.status_code == 200

    def test_stats_counts_registered_signals(self, client):
        client.post("/api/v1/macro/signals", json=_payload())
        data = client.get("/api/v1/macro/stats").json()
        assert data["total_entries"] == 1

    def test_rejections_endpoint_returns_200(self, client):
        resp = client.get("/api/v1/macro/rejections")
        assert resp.status_code == 200

    def test_rejections_contains_rejected_signal(self, client):
        client.post(
            "/api/v1/macro/signals",
            json=_payload(direction="neutral", severity_score=0.85),
        )
        data = client.get("/api/v1/macro/rejections").json()
        assert len(data) == 1
        assert "errors" in data[0]

    def test_expire_endpoint_returns_200(self, client):
        resp = client.post("/api/v1/macro/expire")
        assert resp.status_code == 200
        assert "expired_count" in resp.json()
