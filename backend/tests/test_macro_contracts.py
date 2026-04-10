"""Macro Intelligence Layer — Pack 1 Contract Tests.

Tests cover:
  1. Enum completeness and values
  2. Schema validation (MacroSignalInput, MacroSignal, NormalizedSignal)
  3. Validator correctness (field-level, cross-field, fail-closed)
  4. Normalization pipeline (severity mapping, domain inference, TTL, hashing)
  5. Signal service (ingest, dedup, query, expiration, rejections)
  6. API endpoint contracts (POST, GET, 422, 404)

Total: 45+ contract tests. All must pass for Pack 1 to be green.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalStatus,
)
from src.macro.macro_normalizer import SOURCE_DOMAIN_MAP, normalize_signal
from src.macro.macro_schemas import (
    MacroSignal,
    MacroSignalInput,
    NormalizedSignal,
    SignalIntakeResponse,
    SignalRegistryEntry,
    SignalRejection,
)
from src.macro.macro_signal_service import (
    MacroSignalService,
    SignalRegistry,
)
from src.macro.macro_validators import (
    severity_from_score,
    validate_direction_severity_coherence,
    validate_event_time,
    validate_regions,
    validate_severity_score,
    validate_signal_input,
    validate_title,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

def _valid_input(**overrides) -> MacroSignalInput:
    """Factory for valid MacroSignalInput with sensible defaults."""
    defaults = {
        "title": "Hormuz Strait Partial Blockage Detected",
        "description": "Satellite imagery confirms partial obstruction",
        "source": SignalSource.GEOPOLITICAL,
        "severity_score": 0.72,
        "direction": SignalDirection.NEGATIVE,
        "confidence": SignalConfidence.HIGH,
        "regions": [GCCRegion.UAE, GCCRegion.OMAN],
        "impact_domains": [ImpactDomain.OIL_GAS, ImpactDomain.MARITIME],
        "ttl_hours": 48,
        "tags": ["hormuz", "maritime", "chokepoint"],
    }
    defaults.update(overrides)
    return MacroSignalInput(**defaults)


@pytest.fixture
def valid_input() -> MacroSignalInput:
    return _valid_input()


@pytest.fixture
def service() -> MacroSignalService:
    """Fresh service with empty registry per test."""
    return MacroSignalService(registry=SignalRegistry())


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ENUM TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnums:
    def test_signal_source_has_10_members(self):
        assert len(SignalSource) == 10

    def test_signal_severity_has_6_levels(self):
        assert len(SignalSeverity) == 6

    def test_gcc_region_has_7_members(self):
        """6 GCC states + GCC_WIDE"""
        assert len(GCCRegion) == 7

    def test_signal_status_lifecycle(self):
        """Status enum covers the full signal lifecycle."""
        expected = {"received", "validated", "normalized", "registered",
                    "rejected", "superseded", "expired"}
        actual = {s.value for s in SignalStatus}
        assert actual == expected

    def test_impact_domain_has_12_domains(self):
        assert len(ImpactDomain) == 12


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SCHEMA VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMacroSignalInput:
    def test_valid_input_passes(self, valid_input):
        assert valid_input.title == "Hormuz Strait Partial Blockage Detected"
        assert valid_input.severity_score == 0.72

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            _valid_input(title="Hi")

    def test_severity_score_bounds(self):
        with pytest.raises(ValidationError):
            _valid_input(severity_score=1.5)
        with pytest.raises(ValidationError):
            _valid_input(severity_score=-0.1)

    def test_regions_required(self):
        with pytest.raises(ValidationError):
            _valid_input(regions=[])

    def test_tags_cleaned(self):
        inp = _valid_input(tags=["  Hormuz  ", "HORMUZ", "maritime", "Maritime"])
        assert inp.tags == ["hormuz", "maritime"]

    def test_default_confidence_is_unverified(self):
        inp = MacroSignalInput(
            title="Test signal default confidence",
            source=SignalSource.ECONOMIC,
            severity_score=0.3,
            direction=SignalDirection.NEGATIVE,
            regions=[GCCRegion.SAUDI_ARABIA],
        )
        assert inp.confidence == SignalConfidence.UNVERIFIED

    def test_default_ttl_is_72(self):
        inp = MacroSignalInput(
            title="Test signal default TTL value",
            source=SignalSource.ECONOMIC,
            severity_score=0.3,
            direction=SignalDirection.NEGATIVE,
            regions=[GCCRegion.SAUDI_ARABIA],
        )
        assert inp.ttl_hours == 72


class TestMacroSignal:
    def test_content_hash_computed(self, valid_input):
        normalized = normalize_signal(valid_input)
        assert len(normalized.content_hash) == 64  # SHA-256 hex

    def test_content_hash_deterministic(self, valid_input):
        """Same logical input → same content hash (ignoring timestamps)."""
        sig1 = MacroSignal(
            title="Test", source=SignalSource.ECONOMIC,
            severity_score=0.5, severity_level=SignalSeverity.GUARDED,
            direction=SignalDirection.NEGATIVE,
            confidence=SignalConfidence.HIGH,
            regions=[GCCRegion.UAE],
            impact_domains=[ImpactDomain.BANKING],
            event_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        sig2 = MacroSignal(
            title="Test", source=SignalSource.ECONOMIC,
            severity_score=0.5, severity_level=SignalSeverity.GUARDED,
            direction=SignalDirection.NEGATIVE,
            confidence=SignalConfidence.HIGH,
            regions=[GCCRegion.UAE],
            impact_domains=[ImpactDomain.BANKING],
            event_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        assert sig1.content_hash == sig2.content_hash


class TestSignalRegistryEntry:
    def test_audit_hash_populated(self, valid_input):
        normalized = normalize_signal(valid_input)
        entry = SignalRegistryEntry(signal=normalized)
        assert len(entry.audit_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# 3. VALIDATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidators:
    def test_severity_from_score_nominal(self):
        assert severity_from_score(0.0) == SignalSeverity.NOMINAL
        assert severity_from_score(0.19) == SignalSeverity.NOMINAL

    def test_severity_from_score_low(self):
        assert severity_from_score(0.20) == SignalSeverity.LOW
        assert severity_from_score(0.34) == SignalSeverity.LOW

    def test_severity_from_score_guarded(self):
        assert severity_from_score(0.35) == SignalSeverity.GUARDED
        assert severity_from_score(0.49) == SignalSeverity.GUARDED

    def test_severity_from_score_elevated(self):
        assert severity_from_score(0.50) == SignalSeverity.ELEVATED
        assert severity_from_score(0.64) == SignalSeverity.ELEVATED

    def test_severity_from_score_high(self):
        assert severity_from_score(0.65) == SignalSeverity.HIGH
        assert severity_from_score(0.79) == SignalSeverity.HIGH

    def test_severity_from_score_severe(self):
        assert severity_from_score(0.80) == SignalSeverity.SEVERE
        assert severity_from_score(1.0) == SignalSeverity.SEVERE

    def test_validate_title_empty(self):
        errors = validate_title("   ")
        assert len(errors) > 0

    def test_validate_title_too_short(self):
        errors = validate_title("Hi")
        assert any("too short" in e for e in errors)

    def test_validate_severity_out_of_range(self):
        errors = validate_severity_score(1.5)
        assert len(errors) == 1

    def test_validate_regions_empty(self):
        errors = validate_regions([])
        assert len(errors) == 1

    def test_validate_regions_duplicates(self):
        errors = validate_regions([GCCRegion.UAE, GCCRegion.UAE])
        assert any("duplicate" in e for e in errors)

    def test_validate_event_time_future_rejected(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        errors = validate_event_time(future)
        assert len(errors) == 1

    def test_validate_event_time_past_accepted(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        errors = validate_event_time(past)
        assert len(errors) == 0

    def test_neutral_direction_high_severity_rejected(self):
        errors = validate_direction_severity_coherence(
            SignalDirection.NEUTRAL, 0.75
        )
        assert len(errors) == 1

    def test_negative_direction_high_severity_accepted(self):
        errors = validate_direction_severity_coherence(
            SignalDirection.NEGATIVE, 0.75
        )
        assert len(errors) == 0

    def test_master_validator_valid_input(self, valid_input):
        is_valid, errors, warnings = validate_signal_input(valid_input)
        assert is_valid is True
        assert len(errors) == 0

    def test_master_validator_invalid_fails_closed(self):
        inp = _valid_input(
            direction=SignalDirection.NEUTRAL,
            severity_score=0.85,
        )
        is_valid, errors, warnings = validate_signal_input(inp)
        assert is_valid is False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. NORMALIZATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNormalization:
    def test_normalize_produces_normalized_signal(self, valid_input):
        result = normalize_signal(valid_input)
        assert isinstance(result, NormalizedSignal)
        assert result.status == SignalStatus.NORMALIZED

    def test_severity_level_matches_score(self, valid_input):
        result = normalize_signal(valid_input)
        assert result.severity_level == severity_from_score(valid_input.severity_score)

    def test_event_time_defaults_to_now(self):
        inp = _valid_input(event_time=None)
        before = datetime.now(timezone.utc)
        result = normalize_signal(inp)
        after = datetime.now(timezone.utc)
        assert before <= result.event_time <= after

    def test_expires_at_computed(self, valid_input):
        result = normalize_signal(valid_input)
        expected_delta = timedelta(hours=valid_input.ttl_hours)
        actual_delta = result.expires_at - result.intake_time
        # Allow 1 second tolerance
        assert abs((actual_delta - expected_delta).total_seconds()) < 1

    def test_impact_domains_inferred_when_empty(self):
        inp = _valid_input(impact_domains=[])
        result = normalize_signal(inp)
        expected = SOURCE_DOMAIN_MAP[inp.source]
        assert result.impact_domains == expected

    def test_impact_domains_preserved_when_provided(self):
        domains = [ImpactDomain.AVIATION, ImpactDomain.BANKING]
        inp = _valid_input(impact_domains=domains)
        result = normalize_signal(inp)
        assert result.impact_domains == domains

    def test_content_hash_is_sha256(self, valid_input):
        result = normalize_signal(valid_input)
        assert len(result.content_hash) == 64
        # Verify it's valid hex
        int(result.content_hash, 16)

    def test_normalization_version_set(self, valid_input):
        result = normalize_signal(valid_input)
        assert result.normalization_version == "1.0.0"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SIGNAL SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSignalService:
    def test_ingest_valid_signal(self, service, valid_input):
        entry, rejection, warnings = service.ingest_signal(valid_input)
        assert entry is not None
        assert rejection is None
        assert entry.status == SignalStatus.REGISTERED
        assert service.registry.size == 1

    def test_ingest_invalid_signal_rejected(self, service):
        inp = _valid_input(
            direction=SignalDirection.NEUTRAL,
            severity_score=0.85,
        )
        entry, rejection, warnings = service.ingest_signal(inp)
        assert entry is None
        assert rejection is not None
        assert len(rejection.errors) > 0
        assert service.registry.size == 0

    def test_dedup_returns_existing(self, service):
        """Dedup requires identical content hash — fix event_time for determinism."""
        fixed_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        inp = _valid_input(event_time=fixed_time)
        entry1, _, _ = service.ingest_signal(inp)
        entry2, _, warnings = service.ingest_signal(inp)
        assert entry1.registry_id == entry2.registry_id
        assert any("dedup" in w for w in warnings)
        assert service.registry.size == 1

    def test_get_by_registry_id(self, service, valid_input):
        entry, _, _ = service.ingest_signal(valid_input)
        found = service.get_by_registry_id(entry.registry_id)
        assert found is not None
        assert found.registry_id == entry.registry_id

    def test_get_by_signal_id(self, service, valid_input):
        entry, _, _ = service.ingest_signal(valid_input)
        found = service.get_by_signal_id(entry.signal.signal_id)
        assert found is not None

    def test_get_nonexistent_returns_none(self, service):
        assert service.get_by_registry_id(uuid4()) is None

    def test_list_signals_pagination(self, service):
        for i in range(5):
            inp = _valid_input(
                title=f"Signal number {i} for pagination test",
                severity_score=0.1 * (i + 1),
            )
            service.ingest_signal(inp)
        entries, total = service.list_signals(offset=0, limit=3)
        assert total == 5
        assert len(entries) == 3

    def test_list_signals_filter_by_source(self, service):
        service.ingest_signal(_valid_input(source=SignalSource.GEOPOLITICAL))
        service.ingest_signal(_valid_input(
            title="UAE Banking Sector Stress Indicator",
            source=SignalSource.ECONOMIC,
            severity_score=0.45,
        ))
        entries, total = service.list_signals(source=SignalSource.ECONOMIC)
        assert total == 1
        assert entries[0].signal.source == SignalSource.ECONOMIC

    def test_list_signals_filter_by_region(self, service):
        service.ingest_signal(_valid_input(regions=[GCCRegion.UAE]))
        service.ingest_signal(_valid_input(
            title="Saudi Oil Production Disruption Warning",
            regions=[GCCRegion.SAUDI_ARABIA],
            severity_score=0.55,
        ))
        entries, total = service.list_signals(region=GCCRegion.SAUDI_ARABIA)
        assert total == 1

    def test_get_rejections(self, service):
        inp = _valid_input(
            direction=SignalDirection.NEUTRAL,
            severity_score=0.85,
        )
        service.ingest_signal(inp)
        rejections = service.get_rejections()
        assert len(rejections) == 1

    def test_expire_stale_signals(self, service):
        inp = _valid_input(ttl_hours=1)
        entry, _, _ = service.ingest_signal(inp)
        # Manually backdate intake and expiry
        entry.signal.intake_time = datetime.now(timezone.utc) - timedelta(hours=2)
        entry.signal.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        count = service.expire_stale_signals()
        assert count == 1
        assert entry.status == SignalStatus.EXPIRED

    def test_stats(self, service, valid_input):
        service.ingest_signal(valid_input)
        stats = service.get_stats()
        assert stats["total_entries"] == 1
        assert "by_status" in stats
        assert "by_severity" in stats
        assert "by_source" in stats


# ═══════════════════════════════════════════════════════════════════════════════
# 6. API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_macro_app():
    """Build a minimal FastAPI app with only the macro router.

    Avoids importing src.main which pulls in the full app with Python 3.11+
    dependencies (StrEnum) that may not be available in the test environment.
    """
    from fastapi import FastAPI
    from src.api.v1.macro import router as macro_router

    app = FastAPI()
    app.include_router(macro_router)
    return app


class TestMacroAPI:
    """Integration tests against the macro router only."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Fresh test client with clean registry per test."""
        from src.macro.macro_signal_service import get_signal_service, SignalRegistry, MacroSignalService

        app = _make_macro_app()

        fresh_registry = SignalRegistry()
        fresh_service = MacroSignalService(registry=fresh_registry)

        def override_service():
            return fresh_service

        app.dependency_overrides[get_signal_service] = override_service
        self.client = TestClient(app)
        self.service = fresh_service
        yield
        app.dependency_overrides.clear()

    def _post_signal(self, **overrides):
        payload = {
            "title": "API Test Signal: Hormuz Disruption",
            "source": "geopolitical",
            "severity_score": 0.72,
            "direction": "negative",
            "confidence": "high",
            "regions": ["AE", "OM"],
            "impact_domains": ["oil_gas", "maritime"],
            "ttl_hours": 48,
            "tags": ["test"],
        }
        payload.update(overrides)
        return self.client.post("/api/v1/macro/signals", json=payload)

    def test_post_signal_201(self):
        resp = self._post_signal()
        assert resp.status_code == 201
        data = resp.json()
        assert "signal_id" in data
        assert "registry_id" in data
        assert data["severity_level"] == "high"

    def test_post_invalid_signal_422(self):
        resp = self._post_signal(
            direction="neutral",
            severity_score=0.85,
        )
        assert resp.status_code == 422

    def test_post_missing_title_422(self):
        resp = self.client.post("/api/v1/macro/signals", json={
            "source": "economic",
            "severity_score": 0.3,
            "direction": "negative",
            "regions": ["SA"],
        })
        assert resp.status_code == 422

    def test_get_signals_empty(self):
        resp = self.client.get("/api/v1/macro/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["entries"] == []

    def test_get_signals_after_post(self):
        self._post_signal()
        resp = self.client.get("/api/v1/macro/signals")
        data = resp.json()
        assert data["total"] == 1

    def test_get_signal_by_id(self):
        post_resp = self._post_signal()
        registry_id = post_resp.json()["registry_id"]
        resp = self.client.get(f"/api/v1/macro/signals/{registry_id}")
        assert resp.status_code == 200

    def test_get_signal_404(self):
        fake_id = str(uuid4())
        resp = self.client.get(f"/api/v1/macro/signals/{fake_id}")
        assert resp.status_code == 404

    def test_get_stats(self):
        self._post_signal()
        resp = self.client.get("/api/v1/macro/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_entries"] == 1

    def test_get_rejections(self):
        self._post_signal(direction="neutral", severity_score=0.85)
        resp = self.client.get("/api/v1/macro/rejections")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_post_expire(self):
        resp = self.client.post("/api/v1/macro/expire")
        assert resp.status_code == 200
        assert "expired_count" in resp.json()

    def test_filter_by_source(self):
        self._post_signal(source="geopolitical")
        self._post_signal(
            title="Economic signal for filter test scenario",
            source="economic",
            severity_score=0.45,
        )
        resp = self.client.get("/api/v1/macro/signals?source=economic")
        data = resp.json()
        assert data["total"] == 1

    def test_content_hash_in_response(self):
        resp = self._post_signal()
        data = resp.json()
        assert "content_hash" in data
        assert len(data["content_hash"]) == 64
