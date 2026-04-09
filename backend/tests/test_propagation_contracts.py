"""Macro Intelligence Layer — Pack 2 Contract Tests.

Tests cover:
  1. Causal schemas (CausalEntryPoint, CausalChannel, CausalMapping)
  2. Propagation schemas (Node, Edge, Hit, Path, Result)
  3. Causal graph integrity (no self-loops, coverage, adjacency)
  4. Causal mapper (signal → entry point → activated channels)
  5. Propagation engine (BFS traversal, severity decay, path construction)
  6. Propagation service (orchestration, store, queries)
  7. API endpoints (propagate, inline, causal, list, stats)

Total: 55+ contract tests. All must pass for Pack 2 to be green.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
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
from src.macro.macro_schemas import MacroSignalInput, NormalizedSignal
from src.macro.macro_normalizer import normalize_signal
from src.macro.macro_validators import severity_from_score

from src.macro.causal.causal_schemas import (
    CausalChannel,
    CausalEntryPoint,
    CausalMapping,
    RelationshipType,
)
from src.macro.causal.causal_mapper import (
    CONFIDENCE_WEIGHTS,
    compute_entry_strength,
)
from src.macro.causal.causal_graph import (
    ADJACENCY,
    GCC_CAUSAL_CHANNELS,
    get_all_domains,
    get_outgoing_channels,
)
from src.macro.causal.causal_mapper import (
    discover_activated_channels,
    map_signal_to_causal,
    map_signal_to_causal_entry,
    # compute_entry_strength already imported above
)

from src.macro.propagation.propagation_schemas import (
    NodeState,
    PropagationEdge,
    PropagationHit,
    PropagationNode,
    PropagationPath,
    PropagationResult,
    _state_from_severity,
)
from src.macro.propagation.propagation_engine import (
    MAX_PROPAGATION_DEPTH,
    MIN_SEVERITY_THRESHOLD,
    propagate,
)
from src.macro.propagation.propagation_service import (
    PropagationResultStore,
    PropagationService,
)
from src.macro.macro_signal_service import (
    MacroSignalService,
    SignalRegistry,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

def _make_input(**overrides) -> MacroSignalInput:
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
        "tags": ["hormuz", "maritime"],
    }
    defaults.update(overrides)
    return MacroSignalInput(**defaults)


def _make_normalized(**overrides) -> NormalizedSignal:
    return normalize_signal(_make_input(**overrides))


@pytest.fixture
def normalized_signal() -> NormalizedSignal:
    return _make_normalized()


@pytest.fixture
def prop_service() -> PropagationService:
    return PropagationService(store=PropagationResultStore())


@pytest.fixture
def signal_service() -> MacroSignalService:
    return MacroSignalService(registry=SignalRegistry())


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CAUSAL SCHEMA TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalSchemas:
    def test_causal_entry_point_valid(self, normalized_signal):
        ep = CausalEntryPoint(
            signal_id=normalized_signal.signal_id,
            signal_title=normalized_signal.title,
            source=normalized_signal.source,
            entry_domains=[ImpactDomain.OIL_GAS],
            direction=normalized_signal.direction,
            inherited_severity=normalized_signal.severity_score,
            severity_level=normalized_signal.severity_level,
            confidence=normalized_signal.confidence,
            entry_strength=compute_entry_strength(
                normalized_signal.severity_score, normalized_signal.confidence
            ),
            regions=normalized_signal.regions,
            reasoning="Oil & Gas is the primary domain for geopolitical maritime signals",
        )
        assert ep.entry_id is not None
        assert len(ep.entry_domains) == 1
        assert ep.entry_strength > 0
        assert ep.confidence == SignalConfidence.HIGH

    def test_causal_entry_requires_domains(self):
        with pytest.raises(ValidationError):
            CausalEntryPoint(
                signal_id=uuid4(),
                signal_title="Test",
                source=SignalSource.ECONOMIC,
                entry_domains=[],  # must be non-empty
                direction=SignalDirection.NEGATIVE,
                inherited_severity=0.5,
                severity_level=SignalSeverity.ELEVATED,
                confidence=SignalConfidence.HIGH,
                entry_strength=0.45,
                regions=[GCCRegion.UAE],
                reasoning="This should fail because no entry domains",
            )

    def test_causal_channel_no_self_loop(self):
        with pytest.raises(ValidationError, match="self-loop"):
            CausalChannel(
                channel_id="oil_gas__oil_gas",
                from_domain=ImpactDomain.OIL_GAS,
                to_domain=ImpactDomain.OIL_GAS,
                relationship_type=RelationshipType.DIRECT_EXPOSURE,
                transmission_label="Self-loop should be rejected",
                base_weight=0.5,
            )

    def test_causal_channel_valid(self):
        ch = CausalChannel(
            channel_id="oil_gas__banking",
            from_domain=ImpactDomain.OIL_GAS,
            to_domain=ImpactDomain.BANKING,
            relationship_type=RelationshipType.DIRECT_EXPOSURE,
            transmission_label="Oil sector stress impacts bank asset quality",
            base_weight=0.8,
            lag_hours=48,
        )
        assert ch.decay_per_hop == 0.15  # default
        assert ch.bidirectional is False
        assert ch.lag_hours == 48
        assert ch.relationship_type == RelationshipType.DIRECT_EXPOSURE

    def test_causal_mapping_structure(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        assert isinstance(mapping, CausalMapping)
        assert mapping.entry_point is not None
        assert mapping.total_reachable_domains > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. PROPAGATION SCHEMA TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPropagationSchemas:
    def test_propagation_node_syncs_severity_level_and_state(self):
        node = PropagationNode(
            node_id="banking@depth_1",
            domain=ImpactDomain.BANKING,
            depth=1,
            severity_at_node=0.55,
            severity_level=SignalSeverity.NOMINAL,  # intentionally wrong
            state=NodeState.NOMINAL,  # intentionally wrong
            regions=[GCCRegion.UAE],
        )
        # Model validator should correct both
        assert node.severity_level == SignalSeverity.ELEVATED
        assert node.state == NodeState.DEGRADED

    def test_node_state_mapping(self):
        assert _state_from_severity(0.10) == NodeState.NOMINAL
        assert _state_from_severity(0.30) == NodeState.STRESSED
        assert _state_from_severity(0.55) == NodeState.DEGRADED
        assert _state_from_severity(0.72) == NodeState.CRITICAL
        assert _state_from_severity(0.90) == NodeState.FAILED

    def test_propagation_result_has_audit_hash(self, normalized_signal):
        result = PropagationResult(
            signal_id=normalized_signal.signal_id,
            signal_title=normalized_signal.title,
            entry_domains=[ImpactDomain.OIL_GAS],
        )
        assert len(result.audit_hash) == 64

    def test_propagation_hit_structure(self):
        hit = PropagationHit(
            signal_id=uuid4(),
            domain=ImpactDomain.BANKING,
            depth=1,
            severity_at_hit=0.55,
            severity_level=SignalSeverity.ELEVATED,
            regions=[GCCRegion.UAE],
            path_description="oil_gas → banking",
            reasoning="Oil stress propagated to banking via NPL channel",
        )
        assert hit.hit_id is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CAUSAL GRAPH INTEGRITY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalGraph:
    def test_no_self_loops_in_registry(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert ch.from_domain != ch.to_domain, (
                f"Self-loop found: {ch.channel_id}"
            )

    def test_all_weights_in_range(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert 0.0 <= ch.base_weight <= 1.0, (
                f"Weight out of range: {ch.channel_id} = {ch.base_weight}"
            )
            assert 0.0 <= ch.decay_per_hop <= 1.0, (
                f"Decay out of range: {ch.channel_id} = {ch.decay_per_hop}"
            )

    def test_channel_count_minimum(self):
        """GCC graph must have at least 25 channels for meaningful propagation."""
        assert len(GCC_CAUSAL_CHANNELS) >= 25

    def test_oil_gas_has_outgoing_channels(self):
        channels = get_outgoing_channels(ImpactDomain.OIL_GAS)
        assert len(channels) >= 4, "OIL_GAS must connect to at least 4 downstream domains"

    def test_banking_has_outgoing_channels(self):
        channels = get_outgoing_channels(ImpactDomain.BANKING)
        assert len(channels) >= 2

    def test_region_filtering_works(self):
        bahrain_channels = get_outgoing_channels(ImpactDomain.OIL_GAS, GCCRegion.BAHRAIN)
        gcc_channels = get_outgoing_channels(ImpactDomain.OIL_GAS)
        # Bahrain should have at least the GCC-wide channels
        assert len(bahrain_channels) >= len(gcc_channels) - 1

    def test_adjacency_index_complete(self):
        all_from_domains = {ch.from_domain for ch in GCC_CAUSAL_CHANNELS}
        for domain in all_from_domains:
            assert domain in ADJACENCY

    def test_all_12_domains_reachable(self):
        """At least 10 of 12 domains should be in the graph."""
        domains = get_all_domains()
        assert len(domains) >= 10

    def test_unique_channel_ids(self):
        """No duplicate channel_ids in the registry (except region-specific overrides)."""
        ids = [ch.channel_id for ch in GCC_CAUSAL_CHANNELS]
        gcc_wide = [ch for ch in GCC_CAUSAL_CHANNELS if GCCRegion.GCC_WIDE in ch.regions]
        gcc_ids = [ch.channel_id for ch in gcc_wide]
        assert len(gcc_ids) == len(set(gcc_ids)), "Duplicate channel_ids in GCC-wide channels"

    def test_all_channels_have_relationship_type(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert ch.relationship_type is not None, (
                f"Missing relationship_type: {ch.channel_id}"
            )
            assert isinstance(ch.relationship_type, RelationshipType)

    def test_all_channels_have_lag_hours(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert ch.lag_hours >= 0, (
                f"Invalid lag_hours: {ch.channel_id} = {ch.lag_hours}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CAUSAL MAPPER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalMapper:
    def test_entry_point_has_correct_domains(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        assert set(ep.entry_domains) == {ImpactDomain.OIL_GAS, ImpactDomain.MARITIME}

    def test_entry_point_inherits_severity(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        assert ep.inherited_severity == normalized_signal.severity_score

    def test_entry_point_has_reasoning(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        assert len(ep.reasoning) > 20
        assert "oil_gas" in ep.reasoning or "maritime" in ep.reasoning

    def test_discover_channels_from_oil_gas(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        channels = discover_activated_channels(ep, max_depth=2)
        assert len(channels) >= 5, "OIL_GAS + MARITIME should activate many channels"

    def test_full_causal_mapping(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        assert len(mapping.activated_channels) > 0
        assert mapping.total_reachable_domains >= 3

    def test_single_domain_signal(self):
        sig = _make_normalized(
            title="UAE Banking Sector Capital Adequacy Warning",
            source=SignalSource.ECONOMIC,
            impact_domains=[ImpactDomain.BANKING],
            severity_score=0.55,
        )
        mapping = map_signal_to_causal(sig)
        assert ImpactDomain.BANKING in mapping.entry_point.entry_domains
        assert mapping.total_reachable_domains >= 2

    def test_entry_strength_computed(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        expected = round(normalized_signal.severity_score * CONFIDENCE_WEIGHTS[normalized_signal.confidence], 6)
        assert ep.entry_strength == expected

    def test_entry_strength_varies_by_confidence(self):
        high_conf = _make_normalized(confidence=SignalConfidence.VERIFIED)
        low_conf = _make_normalized(confidence=SignalConfidence.UNVERIFIED)
        ep_high = map_signal_to_causal_entry(high_conf)
        ep_low = map_signal_to_causal_entry(low_conf)
        assert ep_high.entry_strength > ep_low.entry_strength

    def test_entry_point_has_direction(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        assert ep.direction == SignalDirection.NEGATIVE

    def test_entry_point_has_confidence(self, normalized_signal):
        ep = map_signal_to_causal_entry(normalized_signal)
        assert ep.confidence == SignalConfidence.HIGH


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PROPAGATION ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPropagationEngine:
    def test_propagation_produces_result(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        assert isinstance(result, PropagationResult)
        assert result.total_domains_reached >= 2

    def test_entry_domains_always_in_hits(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        hit_domains = {h.domain for h in result.hits}
        for d in mapping.entry_point.entry_domains:
            assert d in hit_domains, f"Entry domain {d.value} missing from hits"

    def test_severity_decays_with_depth(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        entry_hits = [h for h in result.hits if h.depth == 0]
        deep_hits = [h for h in result.hits if h.depth >= 2]
        if deep_hits:
            max_entry = max(h.severity_at_hit for h in entry_hits)
            max_deep = max(h.severity_at_hit for h in deep_hits)
            assert max_deep < max_entry, "Deep hits must have lower severity than entry"

    def test_no_cycles_in_propagation(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        # Each domain should appear at most once in hits
        hit_domains = [h.domain for h in result.hits]
        assert len(hit_domains) == len(set(hit_domains)), "Duplicate domains in hits — cycle detected"

    def test_severity_floor_respected(self):
        """Very low severity signal should not propagate far."""
        sig = _make_normalized(
            title="Minor Nominal Event With Minimal Impact",
            severity_score=0.08,
            direction=SignalDirection.NEGATIVE,
        )
        mapping = map_signal_to_causal(sig)
        result = propagate(mapping, min_severity=0.05)
        # With 8% severity and ~0.7 weights, should barely propagate
        for hit in result.hits:
            assert hit.severity_at_hit >= MIN_SEVERITY_THRESHOLD or hit.depth == 0

    def test_max_depth_respected(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping, max_depth=2)
        for hit in result.hits:
            assert hit.depth <= 2

    def test_paths_have_nodes_and_edges(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        for path in result.paths:
            assert len(path.nodes) >= 2, "Path must have at least entry + terminal"
            assert len(path.edges) == len(path.nodes) - 1

    def test_every_hit_has_reasoning(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        for hit in result.hits:
            assert len(hit.reasoning) > 10
            assert len(hit.path_description) > 0

    def test_audit_hash_populated(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        assert len(result.audit_hash) == 64

    def test_severe_signal_propagates_deeply(self):
        sig = _make_normalized(
            title="Full Hormuz Closure Severe Maritime Blockade",
            severity_score=0.92,
            impact_domains=[ImpactDomain.OIL_GAS, ImpactDomain.MARITIME],
        )
        mapping = map_signal_to_causal(sig)
        result = propagate(mapping, max_depth=5)
        assert result.total_domains_reached >= 5, "SEVERE signal should reach many domains"
        assert result.max_depth >= 2

    def test_nodes_have_state(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        for path in result.paths:
            for node in path.nodes:
                assert node.state is not None
                assert isinstance(node.state, NodeState)

    def test_edges_have_lag_hours(self, normalized_signal):
        mapping = map_signal_to_causal(normalized_signal)
        result = propagate(mapping)
        for path in result.paths:
            for edge in path.edges:
                assert edge.lag_hours >= 0

    def test_entry_strength_drives_propagation(self):
        """Low-confidence signal should propagate with reduced severity."""
        verified = _make_normalized(
            title="Verified signal for strength comparison",
            severity_score=0.72,
            confidence=SignalConfidence.VERIFIED,
        )
        unverified = _make_normalized(
            title="Unverified signal for strength comparison",
            severity_score=0.72,
            confidence=SignalConfidence.UNVERIFIED,
        )
        m_v = map_signal_to_causal(verified)
        m_u = map_signal_to_causal(unverified)
        r_v = propagate(m_v)
        r_u = propagate(m_u)
        # Verified should reach more domains or have higher severity at hits
        assert r_v.total_domains_reached >= r_u.total_domains_reached


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PROPAGATION SERVICE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPropagationService:
    def test_propagate_signal(self, prop_service, normalized_signal):
        result = prop_service.propagate_signal(normalized_signal)
        assert isinstance(result, PropagationResult)
        assert prop_service.store.size == 1

    def test_get_result_by_id(self, prop_service, normalized_signal):
        result = prop_service.propagate_signal(normalized_signal)
        found = prop_service.get_result(result.result_id)
        assert found is not None
        assert found.result_id == result.result_id

    def test_get_result_by_signal_id(self, prop_service, normalized_signal):
        result = prop_service.propagate_signal(normalized_signal)
        found = prop_service.get_result_by_signal(normalized_signal.signal_id)
        assert found is not None

    def test_list_results(self, prop_service):
        for i in range(3):
            sig = _make_normalized(
                title=f"Signal number {i} for propagation test",
                severity_score=0.3 + i * 0.15,
            )
            prop_service.propagate_signal(sig)
        summaries, total = prop_service.list_results()
        assert total == 3
        assert len(summaries) == 3

    def test_stats(self, prop_service, normalized_signal):
        prop_service.propagate_signal(normalized_signal)
        stats = prop_service.get_stats()
        assert stats["total_results"] == 1
        assert stats["avg_domains_reached"] > 0

    def test_causal_mapping_only(self, prop_service, normalized_signal):
        mapping = prop_service.get_causal_mapping(normalized_signal)
        assert isinstance(mapping, CausalMapping)
        # Should NOT be stored
        assert prop_service.store.size == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 7. API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_app():
    """Minimal FastAPI app with macro + propagation routers."""
    from src.api.v1.macro import router as macro_router
    from src.api.v1.propagation import router as prop_router
    app = FastAPI()
    app.include_router(macro_router)
    app.include_router(prop_router)
    return app


class TestPropagationAPI:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        from src.macro.macro_signal_service import get_signal_service
        from src.macro.propagation.propagation_service import get_propagation_service

        app = _make_app()

        fresh_sig_svc = MacroSignalService(registry=SignalRegistry())
        fresh_prop_svc = PropagationService(store=PropagationResultStore())

        app.dependency_overrides[get_signal_service] = lambda: fresh_sig_svc
        app.dependency_overrides[get_propagation_service] = lambda: fresh_prop_svc

        self.client = TestClient(app)
        self.sig_svc = fresh_sig_svc
        self.prop_svc = fresh_prop_svc
        yield
        app.dependency_overrides.clear()

    def _register_signal(self) -> dict:
        payload = {
            "title": "API Test Signal: Hormuz Disruption",
            "source": "geopolitical",
            "severity_score": 0.72,
            "direction": "negative",
            "confidence": "high",
            "regions": ["AE", "OM"],
            "impact_domains": ["oil_gas", "maritime"],
            "ttl_hours": 48,
        }
        resp = self.client.post("/api/v1/macro/signals", json=payload)
        assert resp.status_code == 201
        return resp.json()

    def test_propagate_by_registry_id(self):
        sig = self._register_signal()
        resp = self.client.post("/api/v1/macro/propagate", json={
            "registry_id": sig["registry_id"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"]["total_domains_reached"] >= 2

    def test_propagate_unknown_signal_404(self):
        resp = self.client.post("/api/v1/macro/propagate", json={
            "registry_id": str(uuid4()),
        })
        assert resp.status_code == 404

    def test_propagate_inline(self):
        resp = self.client.post("/api/v1/macro/propagate/inline", json={
            "signal": {
                "title": "Inline propagation test signal",
                "source": "economic",
                "severity_score": 0.55,
                "direction": "negative",
                "regions": ["SA"],
                "impact_domains": ["banking"],
            },
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["result"]["total_domains_reached"] >= 2

    def test_propagate_inline_invalid_422(self):
        resp = self.client.post("/api/v1/macro/propagate/inline", json={
            "signal": {
                "title": "Bad signal with contradictory params",
                "source": "economic",
                "severity_score": 0.85,
                "direction": "neutral",
                "regions": ["SA"],
            },
        })
        assert resp.status_code == 422

    def test_get_propagation_result(self):
        sig = self._register_signal()
        prop_resp = self.client.post("/api/v1/macro/propagate", json={
            "registry_id": sig["registry_id"],
        })
        result_id = prop_resp.json()["result"]["result_id"]
        resp = self.client.get(f"/api/v1/macro/propagation/{result_id}")
        assert resp.status_code == 200

    def test_get_propagation_result_404(self):
        resp = self.client.get(f"/api/v1/macro/propagation/{uuid4()}")
        assert resp.status_code == 404

    def test_get_propagation_by_signal(self):
        sig = self._register_signal()
        self.client.post("/api/v1/macro/propagate", json={
            "registry_id": sig["registry_id"],
        })
        signal_id = sig["signal_id"]
        resp = self.client.get(f"/api/v1/macro/propagation/by-signal/{signal_id}")
        assert resp.status_code == 200

    def test_list_propagation_results(self):
        sig = self._register_signal()
        self.client.post("/api/v1/macro/propagate", json={
            "registry_id": sig["registry_id"],
        })
        resp = self.client.get("/api/v1/macro/propagation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_propagation_stats(self):
        resp = self.client.get("/api/v1/macro/propagation/stats")
        assert resp.status_code == 200
        assert "total_results" in resp.json()

    def test_causal_mapping_only(self):
        sig = self._register_signal()
        resp = self.client.post(f"/api/v1/macro/causal/{sig['registry_id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "mapping" in data
        assert len(data["mapping"]["entry_point"]["entry_domains"]) >= 1
        assert len(data["mapping"]["activated_channels"]) > 0

    def test_causal_mapping_404(self):
        resp = self.client.post(f"/api/v1/macro/causal/{uuid4()}")
        assert resp.status_code == 404

    def test_propagate_by_signal_id(self):
        """POST /propagate/{signal_id} — propagate by signal_id path param."""
        sig = self._register_signal()
        signal_id = sig["signal_id"]
        resp = self.client.post(f"/api/v1/macro/propagate/{signal_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"]["total_domains_reached"] >= 2
        assert data["result"]["signal_id"] == signal_id

    def test_propagate_by_signal_id_404(self):
        """POST /propagate/{signal_id} — unknown signal returns 404."""
        resp = self.client.post(f"/api/v1/macro/propagate/{uuid4()}")
        assert resp.status_code == 404

    def test_propagate_by_signal_id_with_params(self):
        """POST /propagate/{signal_id}?max_depth=2 — query params respected."""
        sig = self._register_signal()
        signal_id = sig["signal_id"]
        resp = self.client.post(
            f"/api/v1/macro/propagate/{signal_id}?max_depth=2&min_severity=0.1"
        )
        assert resp.status_code == 200
        for hit in resp.json()["result"]["hits"]:
            assert hit["depth"] <= 2

    def test_propagation_result_has_explainable_hits(self):
        sig = self._register_signal()
        resp = self.client.post("/api/v1/macro/propagate", json={
            "registry_id": sig["registry_id"],
        })
        hits = resp.json()["result"]["hits"]
        for hit in hits:
            assert "reasoning" in hit
            assert len(hit["reasoning"]) > 10
            assert "path_description" in hit
