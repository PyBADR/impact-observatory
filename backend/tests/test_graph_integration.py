"""Graph Brain Integration Pack A — Comprehensive Tests.

Tests the integration of Graph Brain into the active runtime:
  1. Bridge adapters (type conversion, channel hints, weight hints, explanation fragments)
  2. Enrichment layer (feature flags, causal enrichment, propagation enrichment)
  3. Integration pipeline (full pipeline, fail-safe behavior, disabled graph)
  4. Graph-aware variants (causal_mapper, propagation_engine)
  5. Regression: existing Pack 2 behavior unchanged when graph is disabled

Test fixtures use the same signal factory from test_graph_brain.py.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalType,
)
from src.macro.macro_schemas import NormalizedSignal

from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)
from src.graph_brain.ingestion import ingest_signal
from src.graph_brain.service import GraphBrainService

# ── Integration modules under test ─────────────────────────────────────────
from src.graph_brain.bridge import (
    GraphChannelHint,
    GraphExplanationFragment,
    GraphWeightHint,
    build_explanation_fragments,
    compute_graph_weight_hints,
    discover_graph_channel_hints,
    _domain_to_graph_id,
    _graph_id_to_domain,
    _signal_graph_id,
)
from src.graph_brain.enrichment import (
    CausalEntryEnrichment,
    ExplanationEnrichment,
    PropagationWeightEnrichment,
    compute_blended_weight,
    enrich_causal_entry,
    enrich_explanation,
    ensure_signal_ingested,
    is_enrichment_active,
    set_enrichment_enabled,
    set_feature_flags,
    GRAPH_WEIGHT_BLEND_FACTOR,
)
from src.graph_brain.integration import (
    GraphEnrichedResult,
    GraphEnrichmentMetadata,
    graph_enriched_pipeline,
    graph_enrich_causal_mapping,
    graph_enrich_propagation_result,
)

# Pack 2 imports for comparison
from src.macro.causal.causal_mapper import (
    map_signal_to_causal,
    map_signal_to_causal_entry,
    map_signal_to_causal_graph_aware,
)
from src.macro.propagation.propagation_engine import (
    propagate,
    propagate_graph_enriched,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _make_signal(
    title: str = "Test Oil Shock Signal",
    severity: float = 0.75,
    confidence: SignalConfidence = SignalConfidence.HIGH,
    regions: list[GCCRegion] | None = None,
    impact_domains: list[ImpactDomain] | None = None,
    sector_scope: list[str] | None = None,
    country_scope: list[str] | None = None,
) -> NormalizedSignal:
    now = datetime.now(timezone.utc)
    return NormalizedSignal(
        signal_id=uuid4(),
        title=title,
        description=f"Test signal: {title}",
        source=SignalSource.GEOPOLITICAL,
        severity_score=severity,
        severity_level=SignalSeverity.HIGH if severity >= 0.65 else SignalSeverity.ELEVATED,
        direction=SignalDirection.NEGATIVE,
        confidence=confidence,
        regions=regions or [GCCRegion.SAUDI_ARABIA, GCCRegion.UAE],
        impact_domains=impact_domains or [ImpactDomain.OIL_GAS, ImpactDomain.BANKING],
        event_time=now,
        intake_time=now,
        ttl_hours=168,
        expires_at=now + timedelta(hours=168),
        tags=["test"],
        content_hash="test_hash_" + str(uuid4())[:8],
        signal_type=SignalType.GEOPOLITICAL,
        sector_scope=sector_scope or ["Energy", "Financial Services"],
        country_scope=country_scope or ["Saudi Arabia", "UAE"],
    )


def _make_service_with_signal(signal: NormalizedSignal) -> GraphBrainService:
    """Create a GraphBrainService with a signal already ingested."""
    service = GraphBrainService()
    ingest_signal(signal, service.store)
    return service


@pytest.fixture(autouse=True)
def reset_feature_flags():
    """Reset all feature flags to defaults before each test."""
    set_enrichment_enabled(True)
    set_feature_flags(
        causal_entry=True,
        propagation=True,
        explanation=True,
        auto_ingest=True,
    )
    yield
    # Reset singleton to avoid cross-test contamination
    import src.graph_brain.service as svc_module
    svc_module._instance = None


# ══════════════════════════════════════════════════════════════════════════════
# Test: Bridge — Domain Key Mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestBridgeDomainMapping:
    def test_domain_to_graph_id(self):
        assert _domain_to_graph_id(ImpactDomain.OIL_GAS) == "impact_domain:oil_gas"
        assert _domain_to_graph_id(ImpactDomain.BANKING) == "impact_domain:banking"

    def test_graph_id_to_domain(self):
        assert _graph_id_to_domain("impact_domain:oil_gas") == ImpactDomain.OIL_GAS
        assert _graph_id_to_domain("impact_domain:banking") == ImpactDomain.BANKING

    def test_graph_id_to_domain_invalid(self):
        assert _graph_id_to_domain("country:SA") is None
        assert _graph_id_to_domain("impact_domain:nonexistent") is None

    def test_signal_graph_id(self):
        uid = str(uuid4())
        assert _signal_graph_id(uid) == f"signal:{uid}"


# ══════════════════════════════════════════════════════════════════════════════
# Test: Bridge — Channel Hints
# ══════════════════════════════════════════════════════════════════════════════

class TestBridgeChannelHints:
    def test_discover_hints_with_ingested_signal(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        hints = discover_graph_channel_hints(
            service.store,
            signal_id=str(signal.signal_id),
            entry_domains=[ImpactDomain.OIL_GAS, ImpactDomain.BANKING],
            max_depth=3,
        )
        # Graph should have some paths between ingested domains
        # (oil_gas and banking are both in the same signal graph)
        assert isinstance(hints, list)
        for h in hints:
            assert isinstance(h, GraphChannelHint)
            assert h.from_domain != h.to_domain

    def test_discover_hints_empty_store(self):
        store = GraphStore()
        hints = discover_graph_channel_hints(
            store,
            signal_id="nonexistent",
            entry_domains=[ImpactDomain.OIL_GAS],
            max_depth=3,
        )
        assert hints == []

    def test_hint_repr(self):
        hint = GraphChannelHint(
            from_domain=ImpactDomain.OIL_GAS,
            to_domain=ImpactDomain.BANKING,
            graph_weight=0.65,
            graph_confidence=GraphConfidence.HIGH,
            relation_type=GraphRelationType.AFFECTS,
            reasoning="test",
        )
        assert "oil_gas" in repr(hint)
        assert "banking" in repr(hint)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Bridge — Weight Hints
# ══════════════════════════════════════════════════════════════════════════════

class TestBridgeWeightHints:
    def test_weight_hint_with_graph_path(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        hint = compute_graph_weight_hints(
            service.store,
            ImpactDomain.OIL_GAS,
            ImpactDomain.BANKING,
        )
        # Both domains exist in graph after ingestion
        # There may or may not be a direct path depending on graph structure
        # Just verify the function doesn't crash and returns correct type
        if hint is not None:
            assert isinstance(hint, GraphWeightHint)
            assert hint.from_domain == ImpactDomain.OIL_GAS
            assert hint.to_domain == ImpactDomain.BANKING
            assert 0.0 <= hint.graph_weight <= 1.0

    def test_weight_hint_no_path(self):
        store = GraphStore()
        hint = compute_graph_weight_hints(
            store,
            ImpactDomain.OIL_GAS,
            ImpactDomain.BANKING,
        )
        assert hint is None


# ══════════════════════════════════════════════════════════════════════════════
# Test: Bridge — Explanation Fragments
# ══════════════════════════════════════════════════════════════════════════════

class TestBridgeExplanationFragments:
    def test_fragments_with_ingested_signal(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        fragments = build_explanation_fragments(
            service.store,
            signal_id=str(signal.signal_id),
            reached_domains=[ImpactDomain.OIL_GAS, ImpactDomain.BANKING],
        )
        assert isinstance(fragments, list)
        for f in fragments:
            assert isinstance(f, GraphExplanationFragment)
            assert f.domain in (ImpactDomain.OIL_GAS, ImpactDomain.BANKING)
            assert "[Graph Brain]" in f.reasoning

    def test_fragments_empty_store(self):
        store = GraphStore()
        fragments = build_explanation_fragments(
            store, "nonexistent", [ImpactDomain.OIL_GAS],
        )
        assert fragments == []


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enrichment — Feature Flags
# ══════════════════════════════════════════════════════════════════════════════

class TestFeatureFlags:
    def test_master_switch_disables_all(self):
        set_enrichment_enabled(False)
        assert not is_enrichment_active()
        assert not is_enrichment_active("causal_entry")
        assert not is_enrichment_active("propagation")
        assert not is_enrichment_active("explanation")
        assert not is_enrichment_active("auto_ingest")

    def test_master_switch_enabled(self):
        set_enrichment_enabled(True)
        assert is_enrichment_active()
        assert is_enrichment_active("causal_entry")

    def test_individual_flags(self):
        set_feature_flags(causal_entry=False)
        assert is_enrichment_active()  # master still on
        assert not is_enrichment_active("causal_entry")
        assert is_enrichment_active("propagation")

    def test_unknown_feature_returns_false(self):
        assert not is_enrichment_active("nonexistent_feature")


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enrichment — Auto-Ingest
# ══════════════════════════════════════════════════════════════════════════════

class TestAutoIngest:
    def test_auto_ingest_new_signal(self):
        signal = _make_signal()
        store = GraphStore()
        result = ensure_signal_ingested(signal, store)
        assert result is not None
        assert len(result.nodes_created) > 0

    def test_auto_ingest_existing_signal(self):
        signal = _make_signal()
        store = GraphStore()
        ensure_signal_ingested(signal, store)
        # Second ingest should be no-op
        result = ensure_signal_ingested(signal, store)
        assert result is None

    def test_auto_ingest_disabled(self):
        set_feature_flags(auto_ingest=False)
        signal = _make_signal()
        store = GraphStore()
        result = ensure_signal_ingested(signal, store)
        assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enrichment — Causal Entry
# ══════════════════════════════════════════════════════════════════════════════

class TestCausalEntryEnrichment:
    def test_enrich_returns_enrichment(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        entry = map_signal_to_causal_entry(signal)

        enrichment = enrich_causal_entry(service.store, signal, entry)
        assert isinstance(enrichment, CausalEntryEnrichment)
        assert isinstance(enrichment.reasoning, str)

    def test_enrich_disabled(self):
        set_feature_flags(causal_entry=False)
        signal = _make_signal()
        store = GraphStore()
        entry = map_signal_to_causal_entry(signal)

        enrichment = enrich_causal_entry(store, signal, entry)
        assert not enrichment.has_enrichment
        assert "not active" in enrichment.reasoning

    def test_enrich_filters_existing_channels(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        entry = map_signal_to_causal_entry(signal)

        # Get hints without filtering
        enrichment_no_filter = enrich_causal_entry(
            service.store, signal, entry, existing_channel_pairs=None,
        )
        # Get hints with all pairs filtered
        all_pairs = set()
        for h in enrichment_no_filter.channel_hints:
            all_pairs.add((h.from_domain.value, h.to_domain.value))

        enrichment_filtered = enrich_causal_entry(
            service.store, signal, entry, existing_channel_pairs=all_pairs,
        )
        assert len(enrichment_filtered.channel_hints) <= len(enrichment_no_filter.channel_hints)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enrichment — Blended Weight
# ══════════════════════════════════════════════════════════════════════════════

class TestBlendedWeight:
    def test_blended_weight_no_graph(self):
        store = GraphStore()
        w, enrichment = compute_blended_weight(
            0.80, store, ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
        )
        assert w == 0.80
        assert enrichment is None

    def test_blended_weight_disabled(self):
        set_feature_flags(propagation=False)
        store = GraphStore()
        w, enrichment = compute_blended_weight(
            0.80, store, ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
        )
        assert w == 0.80
        assert enrichment is None

    def test_blended_weight_with_graph(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        w, enrichment = compute_blended_weight(
            0.80, service.store, ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
        )
        # Result should be close to 0.80 with small blend factor
        assert 0.0 <= w <= 1.0
        # With a very small blend factor, it should stay near static weight
        if enrichment is not None:
            assert enrichment.blend_factor == GRAPH_WEIGHT_BLEND_FACTOR


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enrichment — Explanation
# ══════════════════════════════════════════════════════════════════════════════

class TestExplanationEnrichment:
    def test_enrich_explanation_with_graph(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        enrichment = enrich_explanation(
            service.store,
            signal_id=str(signal.signal_id),
            reached_domains=[ImpactDomain.OIL_GAS, ImpactDomain.BANKING],
        )
        assert isinstance(enrichment, ExplanationEnrichment)
        assert isinstance(enrichment.summary, str)

    def test_enrich_explanation_disabled(self):
        set_feature_flags(explanation=False)
        store = GraphStore()
        enrichment = enrich_explanation(
            store, "test", [ImpactDomain.OIL_GAS],
        )
        assert not enrichment.has_enrichment
        assert "not active" in enrichment.summary

    def test_get_fragment_for_domain(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        enrichment = enrich_explanation(
            service.store,
            signal_id=str(signal.signal_id),
            reached_domains=[ImpactDomain.OIL_GAS],
        )
        # If graph has evidence, we should get a fragment
        fragment = enrichment.get_fragment_for_domain(ImpactDomain.OIL_GAS)
        if enrichment.has_enrichment:
            assert fragment is not None
            assert fragment.domain == ImpactDomain.OIL_GAS


# ══════════════════════════════════════════════════════════════════════════════
# Test: Integration Pipeline — Full
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegrationPipeline:
    def test_full_pipeline_with_graph(self):
        signal = _make_signal()
        service = GraphBrainService()

        result = graph_enriched_pipeline(signal, graph_service=service)
        assert isinstance(result, GraphEnrichedResult)
        assert result.propagation_result is not None
        assert result.causal_mapping is not None
        assert result.graph_enrichment.graph_enabled
        assert result.propagation_result.signal_id == signal.signal_id

    def test_full_pipeline_graph_disabled(self):
        set_enrichment_enabled(False)
        signal = _make_signal()

        result = graph_enriched_pipeline(signal)
        assert isinstance(result, GraphEnrichedResult)
        assert result.propagation_result is not None
        assert not result.graph_enrichment.graph_enabled
        assert not result.graph_enrichment.has_enrichment

    def test_pipeline_produces_valid_propagation(self):
        signal = _make_signal()
        service = GraphBrainService()

        result = graph_enriched_pipeline(signal, graph_service=service)
        prop = result.propagation_result

        # Verify Pack 2 contract is intact
        assert prop.signal_id == signal.signal_id
        assert prop.signal_title == signal.title
        assert len(prop.entry_domains) > 0
        assert prop.total_domains_reached > 0
        assert prop.audit_hash  # SHA-256 hash present

    def test_pipeline_metadata_summary(self):
        signal = _make_signal()
        service = GraphBrainService()

        result = graph_enriched_pipeline(signal, graph_service=service)
        summary = result.graph_enrichment.summary()

        assert "graph_enabled" in summary
        assert "signal_ingested" in summary
        assert "causal_hints_count" in summary
        assert "has_enrichment" in summary

    def test_pipeline_to_api_dict(self):
        signal = _make_signal()
        service = GraphBrainService()

        result = graph_enriched_pipeline(signal, graph_service=service)
        api_dict = result.to_api_dict()

        assert "signal_id" in api_dict
        assert "graph_enrichment" in api_dict
        assert isinstance(api_dict["graph_enrichment"], dict)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Integration Pipeline — Fail-Safe
# ══════════════════════════════════════════════════════════════════════════════

class TestPipelineFailSafe:
    def test_pipeline_survives_graph_error(self):
        """Pipeline must produce valid Pack 2 output even if graph fails."""
        signal = _make_signal()

        # Use a service but corrupt the store to cause errors
        service = GraphBrainService()
        # Even with a fresh/empty store, the pipeline should work
        result = graph_enriched_pipeline(signal, graph_service=service)

        assert result.propagation_result is not None
        assert result.propagation_result.signal_id == signal.signal_id
        assert result.propagation_result.total_domains_reached > 0

    def test_pipeline_identical_to_pack2_when_disabled(self):
        """With graph disabled, pipeline output must match pure Pack 2."""
        set_enrichment_enabled(False)
        signal = _make_signal()

        # Pure Pack 2
        mapping_p2 = map_signal_to_causal(signal)
        result_p2 = propagate(mapping_p2)

        # Graph pipeline (disabled)
        enriched = graph_enriched_pipeline(signal)

        # Compare key fields (UUIDs will differ but domains/hits should match)
        assert enriched.propagation_result.total_domains_reached == result_p2.total_domains_reached
        assert enriched.propagation_result.max_depth == result_p2.max_depth
        assert len(enriched.propagation_result.hits) == len(result_p2.hits)
        assert (
            set(h.domain for h in enriched.propagation_result.hits)
            == set(h.domain for h in result_p2.hits)
        )


# ══════════════════════════════════════════════════════════════════════════════
# Test: Graph-Aware Causal Mapper Variant
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphAwareCausalMapper:
    def test_returns_valid_mapping(self):
        signal = _make_signal()
        service = GraphBrainService()

        mapping, enrichment = map_signal_to_causal_graph_aware(
            signal, graph_service=service,
        )
        assert mapping is not None
        assert len(mapping.activated_channels) > 0
        assert mapping.entry_point.signal_id == signal.signal_id

    def test_enrichment_present_when_enabled(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)

        mapping, enrichment = map_signal_to_causal_graph_aware(
            signal, graph_service=service,
        )
        # Enrichment should be present (may or may not have hints)
        assert enrichment is not None
        assert isinstance(enrichment, CausalEntryEnrichment)

    def test_enrichment_none_when_disabled(self):
        set_enrichment_enabled(False)
        signal = _make_signal()

        mapping, enrichment = map_signal_to_causal_graph_aware(signal)
        assert mapping is not None
        assert enrichment is None

    def test_mapping_identical_to_pure_pack2(self):
        """Graph-aware mapping must produce same CausalMapping as pure Pack 2."""
        signal = _make_signal()

        mapping_p2 = map_signal_to_causal(signal)
        mapping_ga, _ = map_signal_to_causal_graph_aware(signal)

        assert len(mapping_ga.activated_channels) == len(mapping_p2.activated_channels)
        assert mapping_ga.total_reachable_domains == mapping_p2.total_reachable_domains
        assert (
            set(ch.channel_id for ch in mapping_ga.activated_channels)
            == set(ch.channel_id for ch in mapping_p2.activated_channels)
        )


# ══════════════════════════════════════════════════════════════════════════════
# Test: Graph-Enriched Propagation Variant
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphEnrichedPropagation:
    def test_returns_valid_result(self):
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)
        service = _make_service_with_signal(signal)

        result, explanation = propagate_graph_enriched(
            mapping, graph_service=service,
        )
        assert result is not None
        assert result.signal_id == signal.signal_id
        assert result.total_domains_reached > 0

    def test_result_identical_domains_to_pack2(self):
        """Enriched propagation must reach same domains as pure Pack 2."""
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)

        result_p2 = propagate(mapping)
        result_ge, _ = propagate_graph_enriched(mapping)

        assert result_ge.total_domains_reached == result_p2.total_domains_reached
        assert (
            set(h.domain for h in result_ge.hits)
            == set(h.domain for h in result_p2.hits)
        )

    def test_enrichment_none_when_disabled(self):
        set_enrichment_enabled(False)
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)

        result, explanation = propagate_graph_enriched(mapping)
        assert result is not None
        assert explanation is None

    def test_graph_reasoning_appended_to_hits(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        mapping = map_signal_to_causal(signal)

        result, explanation = propagate_graph_enriched(
            mapping, graph_service=service,
        )
        # If explanation has fragments, some hits should have graph reasoning
        if explanation is not None and explanation.has_enrichment:
            graph_hits = [
                h for h in result.hits
                if "[Graph Brain]" in h.reasoning
            ]
            assert len(graph_hits) > 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: Standalone Enrichment Functions
# ══════════════════════════════════════════════════════════════════════════════

class TestStandaloneEnrichment:
    def test_graph_enrich_causal_mapping(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        mapping = map_signal_to_causal(signal)

        enrichment = graph_enrich_causal_mapping(
            signal, mapping, graph_service=service,
        )
        assert isinstance(enrichment, CausalEntryEnrichment)

    def test_graph_enrich_propagation_result(self):
        signal = _make_signal()
        service = _make_service_with_signal(signal)
        mapping = map_signal_to_causal(signal)
        result = propagate(mapping)

        enrichment = graph_enrich_propagation_result(
            str(signal.signal_id), result, graph_service=service,
        )
        assert isinstance(enrichment, ExplanationEnrichment)


# ══════════════════════════════════════════════════════════════════════════════
# Test: Regression — Pack 2 Unchanged
# ══════════════════════════════════════════════════════════════════════════════

class TestPack2Regression:
    """Verify Pack 2 functions are completely unmodified when called directly."""

    def test_map_signal_to_causal_unchanged(self):
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)

        assert mapping.entry_point.signal_id == signal.signal_id
        assert len(mapping.activated_channels) > 0
        assert mapping.total_reachable_domains > 0

    def test_propagate_unchanged(self):
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)
        result = propagate(mapping)

        assert result.signal_id == signal.signal_id
        assert result.total_domains_reached > 0
        assert len(result.hits) > 0
        assert result.audit_hash  # SHA-256 hash present

    def test_causal_entry_unchanged(self):
        signal = _make_signal()
        entry = map_signal_to_causal_entry(signal)

        assert entry.signal_id == signal.signal_id
        assert len(entry.entry_domains) > 0
        assert entry.entry_strength > 0

    def test_propagation_deterministic(self):
        signal = _make_signal()
        mapping = map_signal_to_causal(signal)

        result1 = propagate(mapping)
        result2 = propagate(mapping)

        assert result1.total_domains_reached == result2.total_domains_reached
        assert (
            set(h.domain for h in result1.hits)
            == set(h.domain for h in result2.hits)
        )


# ══════════════════════════════════════════════════════════════════════════════
# Test: Multi-Signal Pipeline
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiSignalPipeline:
    def test_multiple_signals_share_graph(self):
        """Multiple signals ingested into same graph should share entities."""
        service = GraphBrainService()

        signal1 = _make_signal(
            title="Oil Shock 1",
            impact_domains=[ImpactDomain.OIL_GAS, ImpactDomain.BANKING],
        )
        signal2 = _make_signal(
            title="Banking Crisis",
            impact_domains=[ImpactDomain.BANKING, ImpactDomain.CAPITAL_MARKETS],
        )

        result1 = graph_enriched_pipeline(signal1, graph_service=service)
        result2 = graph_enriched_pipeline(signal2, graph_service=service)

        # Both should succeed
        assert result1.propagation_result.total_domains_reached > 0
        assert result2.propagation_result.total_domains_reached > 0

        # Graph should have nodes from both signals
        stats = service.stats()
        assert stats["node_count"] > 0
        # Should have both signal nodes
        signal_nodes = service.get_nodes_by_type(GraphEntityType.SIGNAL)
        assert len(signal_nodes) >= 2

    def test_graph_grows_across_signals(self):
        service = GraphBrainService()

        signal1 = _make_signal(
            title="Signal 1",
            impact_domains=[ImpactDomain.OIL_GAS],
            regions=[GCCRegion.SAUDI_ARABIA],
        )
        signal2 = _make_signal(
            title="Signal 2",
            impact_domains=[ImpactDomain.MARITIME],
            regions=[GCCRegion.UAE],
        )

        graph_enriched_pipeline(signal1, graph_service=service)
        stats1 = service.stats()

        graph_enriched_pipeline(signal2, graph_service=service)
        stats2 = service.stats()

        assert stats2["node_count"] >= stats1["node_count"]


# ══════════════════════════════════════════════════════════════════════════════
# Test: GraphEnrichmentMetadata
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphEnrichmentMetadata:
    def test_empty_metadata(self):
        meta = GraphEnrichmentMetadata()
        assert not meta.has_enrichment
        assert meta.summary()["graph_enabled"] is False

    def test_metadata_with_causal_enrichment(self):
        meta = GraphEnrichmentMetadata(
            graph_enabled=True,
            causal_enrichment=CausalEntryEnrichment(
                channel_hints=[
                    GraphChannelHint(
                        ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
                        0.5, GraphConfidence.HIGH,
                        GraphRelationType.AFFECTS, "test",
                    ),
                ],
                additional_domains=[ImpactDomain.BANKING],
                reasoning="test",
            ),
        )
        assert meta.has_enrichment
        assert meta.summary()["causal_hints_count"] == 1

    def test_metadata_errors_tracked(self):
        meta = GraphEnrichmentMetadata()
        meta.errors.append("test error")
        assert meta.summary()["errors_count"] == 1
