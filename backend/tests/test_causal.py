"""Macro Intelligence Layer — Pack 2 Causal Entry Layer Tests.

Covers:
  1. CausalEntryPoint construction from NormalizedSignal
  2. Entry strength computation (severity × confidence_weight)
  3. CausalChannel contracts (self-loop guard, field validation)
  4. Static GCC causal channel graph integrity
  5. Causal mapper (map_signal_to_causal_entry, discover_activated_channels)
  6. CausalMapping full output
  7. CausalService (map_signal, caching, get_entry_point, get_entry_strength)
  8. domain/causal re-export layer
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalStatus,
    SignalType,
)
from src.macro.macro_normalizer import normalize_signal
from src.macro.macro_schemas import MacroSignalInput, NormalizedSignal
from src.macro.causal.causal_schemas import (
    CausalChannel,
    CausalEntryPoint,
    CausalMapping,
    RelationshipType,
)
from src.macro.causal.causal_graph import (
    ADJACENCY,
    GCC_CAUSAL_CHANNELS,
    get_all_domains,
    get_outgoing_channels,
)
from src.macro.causal.causal_mapper import (
    CONFIDENCE_WEIGHTS,
    compute_entry_strength,
    discover_activated_channels,
    map_signal_to_causal,
    map_signal_to_causal_entry,
)
from src.services.causal_service import (
    CausalResultStore,
    CausalService,
    get_causal_service,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_normalized(**overrides) -> NormalizedSignal:
    """Build a NormalizedSignal via the pack 1 normalizer."""
    defaults = {
        "title": "GCC oil transit disruption at Strait of Hormuz",
        "source": SignalSource.GEOPOLITICAL,
        "severity_score": 0.72,
        "direction": SignalDirection.NEGATIVE,
        "confidence": SignalConfidence.HIGH,
        "regions": [GCCRegion.UAE, GCCRegion.OMAN],
        "impact_domains": [ImpactDomain.OIL_GAS, ImpactDomain.MARITIME],
        "ttl_hours": 48,
    }
    defaults.update(overrides)
    return normalize_signal(MacroSignalInput(**defaults))


@pytest.fixture
def geo_signal() -> NormalizedSignal:
    return _make_normalized()


@pytest.fixture
def svc() -> CausalService:
    return CausalService(store=CausalResultStore())


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CAUSAL ENTRY POINT CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalEntryPoint:
    def test_entry_point_built_from_signal(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert isinstance(ep, CausalEntryPoint)
        assert ep.signal_id == geo_signal.signal_id

    def test_entry_domains_from_signal_impact_domains(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.entry_domains == geo_signal.impact_domains

    def test_entry_domains_min_length_1(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert len(ep.entry_domains) >= 1

    def test_severity_inherited(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.inherited_severity == geo_signal.severity_score

    def test_severity_level_inherited(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.severity_level == geo_signal.severity_level

    def test_direction_inherited(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.direction == geo_signal.direction

    def test_confidence_inherited(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.confidence == geo_signal.confidence

    def test_regions_inherited(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.regions == geo_signal.regions

    def test_reasoning_is_non_empty(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert len(ep.reasoning) >= 10
        assert geo_signal.title[:20] in ep.reasoning or geo_signal.source.value in ep.reasoning

    def test_signal_type_passed_through(self):
        sig = _make_normalized(signal_type=SignalType.SYSTEMIC)
        ep = map_signal_to_causal_entry(sig)
        assert ep.signal_type == SignalType.SYSTEMIC

    def test_signal_type_none_passed_through(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.signal_type is None

    def test_entry_id_is_unique(self, geo_signal):
        ep1 = map_signal_to_causal_entry(geo_signal)
        ep2 = map_signal_to_causal_entry(geo_signal)
        assert ep1.entry_id != ep2.entry_id  # each call generates a new UUID

    def test_entry_point_has_timestamp(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        assert ep.created_at is not None
        assert ep.created_at.tzinfo is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENTRY STRENGTH COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestEntryStrength:
    def test_verified_confidence_full_weight(self):
        strength = compute_entry_strength(1.0, SignalConfidence.VERIFIED)
        assert strength == pytest.approx(1.0 * CONFIDENCE_WEIGHTS[SignalConfidence.VERIFIED])

    def test_high_confidence_weight(self):
        strength = compute_entry_strength(0.8, SignalConfidence.HIGH)
        expected = round(0.8 * CONFIDENCE_WEIGHTS[SignalConfidence.HIGH], 6)
        assert strength == pytest.approx(expected)

    def test_unverified_reduces_strength_significantly(self):
        verified = compute_entry_strength(0.7, SignalConfidence.VERIFIED)
        unverified = compute_entry_strength(0.7, SignalConfidence.UNVERIFIED)
        assert unverified < verified
        assert unverified < 0.3  # 0.7 × 0.25 = 0.175

    def test_zero_severity_gives_zero_strength(self):
        for conf in SignalConfidence:
            assert compute_entry_strength(0.0, conf) == 0.0

    def test_entry_strength_bounds(self):
        for conf in SignalConfidence:
            s = compute_entry_strength(0.5, conf)
            assert 0.0 <= s <= 1.0

    def test_entry_strength_in_entry_point(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        expected = compute_entry_strength(
            geo_signal.severity_score, geo_signal.confidence
        )
        assert ep.entry_strength == pytest.approx(expected)

    def test_all_confidence_weights_defined(self):
        for conf in SignalConfidence:
            assert conf in CONFIDENCE_WEIGHTS
            assert 0.0 <= CONFIDENCE_WEIGHTS[conf] <= 1.0

    def test_confidence_weights_ordered(self):
        """VERIFIED > HIGH > MODERATE > LOW > UNVERIFIED."""
        w = CONFIDENCE_WEIGHTS
        assert w[SignalConfidence.VERIFIED] > w[SignalConfidence.HIGH]
        assert w[SignalConfidence.HIGH] > w[SignalConfidence.MODERATE]
        assert w[SignalConfidence.MODERATE] > w[SignalConfidence.LOW]
        assert w[SignalConfidence.LOW] > w[SignalConfidence.UNVERIFIED]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CAUSAL CHANNEL CONTRACTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalChannel:
    def test_valid_channel_creates_successfully(self):
        ch = CausalChannel(
            channel_id="oil_gas__banking",
            from_domain=ImpactDomain.OIL_GAS,
            to_domain=ImpactDomain.BANKING,
            relationship_type=RelationshipType.DIRECT_EXPOSURE,
            transmission_label="Oil sector stress → bank asset quality",
            base_weight=0.80,
        )
        assert ch.channel_id == "oil_gas__banking"

    def test_self_loop_raises(self):
        with pytest.raises(ValueError, match="self-loop"):
            CausalChannel(
                channel_id="oil_gas__oil_gas",
                from_domain=ImpactDomain.OIL_GAS,
                to_domain=ImpactDomain.OIL_GAS,
                relationship_type=RelationshipType.DIRECT_EXPOSURE,
                transmission_label="Self loop test",
                base_weight=0.5,
            )

    def test_base_weight_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            CausalChannel(
                channel_id="test_ch",
                from_domain=ImpactDomain.OIL_GAS,
                to_domain=ImpactDomain.BANKING,
                relationship_type=RelationshipType.DIRECT_EXPOSURE,
                transmission_label="Test channel weight validation",
                base_weight=1.5,  # > 1.0
            )

    def test_default_decay_per_hop(self):
        ch = CausalChannel(
            channel_id="test__ch",
            from_domain=ImpactDomain.BANKING,
            to_domain=ImpactDomain.CAPITAL_MARKETS,
            relationship_type=RelationshipType.MARKET_CONTAGION,
            transmission_label="Test default decay channel",
            base_weight=0.7,
        )
        assert ch.decay_per_hop == 0.15  # default

    def test_default_regions_is_gcc_wide(self):
        ch = CausalChannel(
            channel_id="test__ch2",
            from_domain=ImpactDomain.BANKING,
            to_domain=ImpactDomain.INSURANCE,
            relationship_type=RelationshipType.RISK_TRANSFER,
            transmission_label="Test default region channel",
            base_weight=0.5,
        )
        assert GCCRegion.GCC_WIDE in ch.regions

    def test_all_relationship_types_have_values(self):
        expected = {
            "direct_exposure", "supply_chain", "market_contagion",
            "fiscal_linkage", "infrastructure_dep", "regulatory", "risk_transfer",
        }
        actual = {rt.value for rt in RelationshipType}
        assert actual == expected


# ═══════════════════════════════════════════════════════════════════════════════
# 4. STATIC CAUSAL GRAPH INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalGraph:
    def test_channel_registry_is_non_empty(self):
        assert len(GCC_CAUSAL_CHANNELS) >= 20

    def test_no_self_loops_in_registry(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert ch.from_domain != ch.to_domain, (
                f"Self-loop detected: {ch.channel_id}"
            )

    def test_all_weights_in_valid_range(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert 0.0 <= ch.base_weight <= 1.0, (
                f"Weight out of range for {ch.channel_id}: {ch.base_weight}"
            )
            assert 0.0 <= ch.decay_per_hop <= 1.0

    def test_all_channel_ids_unique(self):
        # Multiple channels may share from→to but have different regions.
        # channel_id is from→to, so duplicates are allowed for region variants.
        # Just verify no identical (id, regions) pair.
        seen: set[tuple[str, frozenset]] = set()
        for ch in GCC_CAUSAL_CHANNELS:
            key = (ch.channel_id, frozenset(r.value for r in ch.regions))
            assert key not in seen, f"Duplicate channel: {key}"
            seen.add(key)

    def test_adjacency_covers_all_source_domains(self):
        for ch in GCC_CAUSAL_CHANNELS:
            assert ch.from_domain in ADJACENCY

    def test_get_outgoing_channels_returns_list(self):
        channels = get_outgoing_channels(ImpactDomain.OIL_GAS)
        assert isinstance(channels, list)
        assert len(channels) > 0

    def test_get_outgoing_channels_region_filter(self):
        # GCC_WIDE channels must appear for any region
        all_channels = get_outgoing_channels(ImpactDomain.OIL_GAS)
        gcc_wide_only = get_outgoing_channels(ImpactDomain.OIL_GAS, GCCRegion.QATAR)
        # Qatar-filtered results should be a subset of all
        for ch in gcc_wide_only:
            assert ch in all_channels

    def test_get_outgoing_channels_gcc_wide_always_included(self):
        # GCC_WIDE channels should be present regardless of region
        for region in GCCRegion:
            if region == GCCRegion.GCC_WIDE:
                continue
            channels = get_outgoing_channels(ImpactDomain.OIL_GAS, region)
            gcc_wide_channels = [
                ch for ch in channels if GCCRegion.GCC_WIDE in ch.regions
            ]
            assert len(gcc_wide_channels) > 0

    def test_oil_gas_has_high_weight_to_fiscal(self):
        channels = get_outgoing_channels(ImpactDomain.OIL_GAS)
        fiscal = [c for c in channels if c.to_domain == ImpactDomain.SOVEREIGN_FISCAL]
        assert len(fiscal) > 0
        assert any(c.base_weight >= 0.85 for c in fiscal)

    def test_maritime_to_trade_logistics_exists(self):
        channels = get_outgoing_channels(ImpactDomain.MARITIME)
        trade = [c for c in channels if c.to_domain == ImpactDomain.TRADE_LOGISTICS]
        assert len(trade) > 0

    def test_get_all_domains_non_empty(self):
        domains = get_all_domains()
        assert len(domains) >= 5
        assert ImpactDomain.OIL_GAS in domains
        assert ImpactDomain.BANKING in domains


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CAUSAL MAPPER
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalMapper:
    def test_discover_activated_channels_from_oil_gas(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        channels = discover_activated_channels(ep, max_depth=3)
        assert len(channels) > 0

    def test_discover_channels_no_self_loops(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        channels = discover_activated_channels(ep, max_depth=4)
        for ch in channels:
            assert ch.from_domain != ch.to_domain

    def test_discover_channels_depth_0_is_empty(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        channels = discover_activated_channels(ep, max_depth=0)
        assert channels == []

    def test_discover_channels_depth_limits_results(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        shallow = discover_activated_channels(ep, max_depth=1)
        deep = discover_activated_channels(ep, max_depth=4)
        assert len(deep) >= len(shallow)

    def test_discover_channels_deduplicated(self, geo_signal):
        ep = map_signal_to_causal_entry(geo_signal)
        channels = discover_activated_channels(ep, max_depth=4)
        ids = [(c.channel_id, frozenset(r.value for r in c.regions)) for c in channels]
        assert len(ids) == len(set(ids))

    def test_map_signal_to_causal_returns_mapping(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert isinstance(mapping, CausalMapping)

    def test_mapping_entry_point_matches_signal(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert mapping.entry_point.signal_id == geo_signal.signal_id

    def test_mapping_activated_channels_non_empty(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert len(mapping.activated_channels) > 0

    def test_mapping_reachable_domains_count(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert mapping.total_reachable_domains >= len(mapping.entry_point.entry_domains)

    def test_mapping_deterministic(self, geo_signal):
        """Same signal → same entry_domains and channel count (UUIDs differ)."""
        m1 = map_signal_to_causal(geo_signal)
        m2 = map_signal_to_causal(geo_signal)
        assert m1.entry_point.entry_domains == m2.entry_point.entry_domains
        assert len(m1.activated_channels) == len(m2.activated_channels)
        assert m1.total_reachable_domains == m2.total_reachable_domains

    def test_mapping_has_timestamp(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert mapping.created_at is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CAUSAL MAPPING CONTRACTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalMapping:
    def test_mapping_has_valid_mapping_id(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert mapping.mapping_id is not None

    def test_mapping_entry_point_entry_strength_bounds(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        assert 0.0 <= mapping.entry_point.entry_strength <= 1.0

    def test_mapping_channels_all_have_valid_weights(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        for ch in mapping.activated_channels:
            assert 0.0 <= ch.base_weight <= 1.0
            assert 0.0 <= ch.decay_per_hop <= 1.0

    def test_mapping_entry_domains_are_impact_domain_enum(self, geo_signal):
        mapping = map_signal_to_causal(geo_signal)
        for d in mapping.entry_point.entry_domains:
            assert isinstance(d, ImpactDomain)

    def test_cyber_signal_activates_different_channels(self):
        sig = _make_normalized(
            source=SignalSource.CYBER,
            impact_domains=[ImpactDomain.CYBER_INFRASTRUCTURE],
        )
        mapping = map_signal_to_causal(sig)
        domains = {ch.to_domain for ch in mapping.activated_channels}
        assert ImpactDomain.BANKING in domains or ImpactDomain.TELECOMMUNICATIONS in domains

    def test_climate_signal_activates_channels(self):
        sig = _make_normalized(
            source=SignalSource.CLIMATE,
            impact_domains=[ImpactDomain.INSURANCE, ImpactDomain.REAL_ESTATE],
        )
        mapping = map_signal_to_causal(sig)
        assert len(mapping.activated_channels) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CAUSAL SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestCausalService:
    def test_map_signal_returns_mapping(self, svc, geo_signal):
        mapping = svc.map_signal(geo_signal)
        assert isinstance(mapping, CausalMapping)

    def test_map_signal_caches_result(self, svc, geo_signal):
        m1 = svc.map_signal(geo_signal)
        m2 = svc.map_signal(geo_signal)
        assert m1 is m2  # same object from cache

    def test_map_signal_cache_by_signal_id(self, svc, geo_signal):
        svc.map_signal(geo_signal)
        cached = svc.get_mapping(geo_signal.signal_id)
        assert cached is not None

    def test_get_mapping_returns_none_before_compute(self, svc):
        fake_id = uuid4()
        assert svc.get_mapping(fake_id) is None

    def test_get_entry_point_returns_entry_point(self, svc, geo_signal):
        ep = svc.get_entry_point(geo_signal)
        assert isinstance(ep, CausalEntryPoint)

    def test_get_entry_strength_matches_manual(self, svc, geo_signal):
        expected = compute_entry_strength(
            geo_signal.severity_score, geo_signal.confidence
        )
        assert svc.get_entry_strength(geo_signal) == pytest.approx(expected)

    def test_get_stats_empty_store(self, svc):
        stats = svc.get_stats()
        assert stats["total_mappings"] == 0

    def test_get_stats_after_mapping(self, svc, geo_signal):
        svc.map_signal(geo_signal)
        stats = svc.get_stats()
        assert stats["total_mappings"] == 1
        assert stats["avg_channels"] >= 0
        assert stats["avg_reachable_domains"] >= 1

    def test_get_causal_service_returns_singleton(self):
        svc1 = get_causal_service()
        svc2 = get_causal_service()
        assert svc1 is svc2

    def test_store_clear(self, svc, geo_signal):
        svc.map_signal(geo_signal)
        assert svc.store.size == 1
        svc.store.clear()
        assert svc.store.size == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 8. DOMAIN/CAUSAL RE-EXPORT LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class TestDomainCausalReexport:
    def test_import_via_domain_causal(self):
        from src.domain.causal import (
            CausalChannel,
            CausalEntryPoint,
            CausalMapping,
            RelationshipType,
            GCC_CAUSAL_CHANNELS,
            get_outgoing_channels,
            map_signal_to_causal,
            compute_entry_strength,
            CONFIDENCE_WEIGHTS,
        )
        assert CausalChannel is not None
        assert len(GCC_CAUSAL_CHANNELS) > 0

    def test_reexported_map_signal_works(self, geo_signal):
        from src.domain.causal import map_signal_to_causal as domain_map
        mapping = domain_map(geo_signal)
        assert isinstance(mapping, CausalMapping)

    def test_reexported_entry_strength_works(self, geo_signal):
        from src.domain.causal import compute_entry_strength as domain_strength
        s = domain_strength(0.7, SignalConfidence.HIGH)
        assert 0.0 < s < 1.0
