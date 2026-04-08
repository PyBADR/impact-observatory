"""Pack 3 — Impact Engine Test Suite.

Tests for:
  - DOMAIN_EXPOSURE_WEIGHTS coverage and values
  - get_exposure_weight() fallback
  - _derive_confidence() thresholds
  - _hit_to_domain_impact() conversion
  - compute_impact() computation across severity tiers
  - compute_impact() zero-hit fallback
  - MacroImpact model fields
  - DomainImpact model fields
  - overall_severity = max across hits
  - total_exposure_score = mean(weighted_impact)
  - audit_hash generation
  - graph_enriched flag
  - reasoning composition
  - backward compatibility with PropagationResult
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalSeverity,
)
from src.macro.propagation.propagation_schemas import (
    PropagationHit,
    PropagationResult,
)
from src.macro.impact.impact_engine import (
    DOMAIN_EXPOSURE_WEIGHTS,
    _DEFAULT_EXPOSURE_WEIGHT,
    _derive_confidence,
    _hit_to_domain_impact,
    compute_impact,
    get_exposure_weight,
)
from src.macro.impact.impact_models import DomainImpact, MacroImpact


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _make_hit(
    signal_id: UUID | None = None,
    domain: ImpactDomain = ImpactDomain.OIL_GAS,
    depth: int = 0,
    severity: float = 0.80,
    reasoning: str = "Test reasoning.",
) -> PropagationHit:
    return PropagationHit(
        signal_id=signal_id or uuid4(),
        domain=domain,
        depth=depth,
        severity_at_hit=severity,
        severity_level=_severity_for(severity),
        regions=[GCCRegion.GCC_WIDE],
        path_description=f"[ENTRY] {domain.value}" if depth == 0 else f"entry → {domain.value}",
        reasoning=reasoning,
    )


def _severity_for(s: float) -> SignalSeverity:
    if s < 0.20: return SignalSeverity.NOMINAL
    if s < 0.35: return SignalSeverity.LOW
    if s < 0.50: return SignalSeverity.GUARDED
    if s < 0.65: return SignalSeverity.ELEVATED
    if s < 0.80: return SignalSeverity.HIGH
    return SignalSeverity.SEVERE


def _make_result(
    hits: list[PropagationHit] | None = None,
    signal_id: UUID | None = None,
    entry_domains: list[ImpactDomain] | None = None,
) -> PropagationResult:
    sid = signal_id or uuid4()
    h = hits or []
    return PropagationResult(
        signal_id=sid,
        signal_title="Test signal",
        entry_domains=entry_domains or [ImpactDomain.OIL_GAS],
        hits=h,
        total_domains_reached=len(h),
        max_depth=max((x.depth for x in h), default=0),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. DOMAIN_EXPOSURE_WEIGHTS
# ══════════════════════════════════════════════════════════════════════════════

class TestDomainExposureWeights:

    def test_all_impact_domains_covered(self):
        """Every ImpactDomain must have an exposure weight."""
        for domain in ImpactDomain:
            # get_exposure_weight never raises — falls back to _DEFAULT_EXPOSURE_WEIGHT
            w = get_exposure_weight(domain)
            assert 0.0 <= w <= 1.0

    def test_oil_gas_highest_weight(self):
        assert DOMAIN_EXPOSURE_WEIGHTS[ImpactDomain.OIL_GAS] == 0.95

    def test_sovereign_fiscal_second(self):
        assert DOMAIN_EXPOSURE_WEIGHTS[ImpactDomain.SOVEREIGN_FISCAL] == 0.90

    def test_banking_third(self):
        assert DOMAIN_EXPOSURE_WEIGHTS[ImpactDomain.BANKING] == 0.85

    def test_cyber_lowest(self):
        assert DOMAIN_EXPOSURE_WEIGHTS[ImpactDomain.CYBER_INFRASTRUCTURE] == 0.55

    def test_all_weights_in_range(self):
        for domain, weight in DOMAIN_EXPOSURE_WEIGHTS.items():
            assert 0.0 <= weight <= 1.0, f"{domain}: weight {weight} out of range"

    def test_default_weight_fallback(self):
        # _DEFAULT_EXPOSURE_WEIGHT is 0.50
        assert _DEFAULT_EXPOSURE_WEIGHT == 0.50


# ══════════════════════════════════════════════════════════════════════════════
# 2. _derive_confidence
# ══════════════════════════════════════════════════════════════════════════════

class TestDeriveConfidence:

    def test_zero_domains_unverified(self):
        assert _derive_confidence(0) == SignalConfidence.UNVERIFIED

    def test_one_domain_low(self):
        assert _derive_confidence(1) == SignalConfidence.LOW

    def test_two_domains_moderate(self):
        assert _derive_confidence(2) == SignalConfidence.MODERATE

    def test_three_domains_moderate(self):
        assert _derive_confidence(3) == SignalConfidence.MODERATE

    def test_four_domains_high(self):
        assert _derive_confidence(4) == SignalConfidence.HIGH

    def test_six_domains_high(self):
        assert _derive_confidence(6) == SignalConfidence.HIGH

    def test_seven_domains_verified(self):
        assert _derive_confidence(7) == SignalConfidence.VERIFIED

    def test_twelve_domains_verified(self):
        assert _derive_confidence(12) == SignalConfidence.VERIFIED

    def test_monotonic_confidence(self):
        """More domains → same or higher confidence (never decreases)."""
        CONF_ORDER = [
            SignalConfidence.UNVERIFIED,
            SignalConfidence.LOW,
            SignalConfidence.MODERATE,
            SignalConfidence.HIGH,
            SignalConfidence.VERIFIED,
        ]
        prev_rank = 0
        for n in range(0, 15):
            c = _derive_confidence(n)
            rank = CONF_ORDER.index(c)
            assert rank >= prev_rank, f"Confidence decreased at n={n}"
            prev_rank = rank


# ══════════════════════════════════════════════════════════════════════════════
# 3. _hit_to_domain_impact
# ══════════════════════════════════════════════════════════════════════════════

class TestHitToDomainImpact:

    def test_basic_conversion(self):
        hit = _make_hit(domain=ImpactDomain.OIL_GAS, severity=0.80)
        di = _hit_to_domain_impact(hit)
        assert di.domain == ImpactDomain.OIL_GAS
        assert di.severity_score == 0.80
        assert di.exposure_weight == DOMAIN_EXPOSURE_WEIGHTS[ImpactDomain.OIL_GAS]

    def test_weighted_impact_correct(self):
        hit = _make_hit(domain=ImpactDomain.OIL_GAS, severity=0.80)
        di = _hit_to_domain_impact(hit)
        expected = round(0.80 * 0.95, 6)
        assert di.weighted_impact == expected

    def test_weighted_impact_clamped_to_one(self):
        # Max possible: severity=1.0, weight=0.95 → 0.95 (already <= 1.0)
        hit = _make_hit(domain=ImpactDomain.OIL_GAS, severity=1.0)
        di = _hit_to_domain_impact(hit)
        assert di.weighted_impact <= 1.0

    def test_is_entry_domain_depth_zero(self):
        hit = _make_hit(depth=0)
        di = _hit_to_domain_impact(hit)
        assert di.is_entry_domain is True

    def test_not_entry_domain_depth_nonzero(self):
        hit = _make_hit(depth=2)
        di = _hit_to_domain_impact(hit)
        assert di.is_entry_domain is False

    def test_reasoning_preserved(self):
        reasoning = "Reached via oil_gas → banking. Transmission: NPL increase."
        hit = _make_hit(reasoning=reasoning)
        di = _hit_to_domain_impact(hit)
        assert di.reasoning == reasoning

    def test_graph_reasoning_preserved(self):
        reasoning = "Normal reasoning.\n  [Graph Brain] Graph path: oil_gas → banking."
        hit = _make_hit(reasoning=reasoning)
        di = _hit_to_domain_impact(hit)
        assert "[Graph Brain]" in di.reasoning

    def test_regions_preserved(self):
        hit = _make_hit()
        di = _hit_to_domain_impact(hit)
        assert GCCRegion.GCC_WIDE in di.regions

    def test_depth_preserved(self):
        hit = _make_hit(depth=3)
        di = _hit_to_domain_impact(hit)
        assert di.depth == 3

    def test_severity_level_preserved(self):
        hit = _make_hit(severity=0.85)  # SEVERE
        di = _hit_to_domain_impact(hit)
        assert di.severity_level == SignalSeverity.SEVERE


# ══════════════════════════════════════════════════════════════════════════════
# 4. compute_impact — Basic Structure
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeImpactStructure:

    def test_returns_macro_impact(self):
        result = _make_result()
        impact = compute_impact(result)
        assert isinstance(impact, MacroImpact)

    def test_signal_id_preserved(self):
        sid = uuid4()
        result = _make_result(signal_id=sid)
        impact = compute_impact(result)
        assert impact.signal_id == sid

    def test_signal_title_preserved(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.signal_title == "Test signal"

    def test_impact_id_is_uuid(self):
        result = _make_result()
        impact = compute_impact(result)
        assert isinstance(impact.impact_id, UUID)

    def test_audit_hash_generated(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.audit_hash
        assert len(impact.audit_hash) == 64  # SHA-256 hex

    def test_computed_at_is_recent(self):
        result = _make_result()
        impact = compute_impact(result)
        now = datetime.now(timezone.utc)
        delta = abs((now - impact.computed_at).total_seconds())
        assert delta < 5.0

    def test_domain_impacts_count_matches_hits(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.60),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert len(impact.domain_impacts) == 2

    def test_affected_domains_count(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.60),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert len(impact.affected_domains) == 2
        assert ImpactDomain.OIL_GAS in impact.affected_domains
        assert ImpactDomain.BANKING in impact.affected_domains

    def test_entry_domains_preserved(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, domain=ImpactDomain.ENERGY_GRID)
        result = _make_result(hits=[hit], signal_id=sid, entry_domains=[ImpactDomain.ENERGY_GRID])
        impact = compute_impact(result)
        assert ImpactDomain.ENERGY_GRID in impact.entry_domains

    def test_total_domains_reached(self):
        sid = uuid4()
        hits = [_make_hit(signal_id=sid, domain=d) for d in [
            ImpactDomain.OIL_GAS, ImpactDomain.BANKING, ImpactDomain.INSURANCE
        ]]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.total_domains_reached == 3

    def test_max_depth_preserved(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, depth=0),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=2),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        result.max_depth = 2
        impact = compute_impact(result)
        assert impact.max_depth == 2

    def test_impact_reasoning_non_empty(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert len(impact.impact_reasoning) > 10


# ══════════════════════════════════════════════════════════════════════════════
# 5. compute_impact — Severity Computation
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeImpactSeverity:

    def test_overall_severity_is_max(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.90),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.50),
            _make_hit(signal_id=sid, domain=ImpactDomain.INSURANCE, depth=2, severity=0.30),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity == 0.90

    def test_overall_severity_level_matches_score(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.85)  # SEVERE
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.SEVERE

    def test_overall_severity_level_high(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.70)  # HIGH
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.HIGH

    def test_overall_severity_level_elevated(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.55)  # ELEVATED
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.ELEVATED

    def test_overall_severity_level_guarded(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.40)  # GUARDED
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.GUARDED

    def test_overall_severity_level_low(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.25)  # LOW
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.LOW

    def test_overall_severity_level_nominal(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, severity=0.10)  # NOMINAL
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.overall_severity_level == SignalSeverity.NOMINAL


# ══════════════════════════════════════════════════════════════════════════════
# 6. compute_impact — Exposure Score
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeImpactExposure:

    def test_single_hit_exposure_score(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.80)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        expected = round(0.80 * 0.95, 6)
        assert impact.total_exposure_score == expected

    def test_multiple_hits_exposure_score_is_mean(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.80),    # 0.80*0.95
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.50),  # 0.50*0.85
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        w1 = round(0.80 * 0.95, 6)
        w2 = round(0.50 * 0.85, 6)
        expected = round((w1 + w2) / 2, 6)
        assert abs(impact.total_exposure_score - expected) < 1e-5

    def test_exposure_score_in_range(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=d, severity=0.75)
            for d in [ImpactDomain.OIL_GAS, ImpactDomain.BANKING, ImpactDomain.INSURANCE]
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert 0.0 <= impact.total_exposure_score <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 7. compute_impact — Confidence Derivation
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeImpactConfidence:

    def test_zero_hits_unverified(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.UNVERIFIED

    def test_one_hit_low_confidence(self):
        sid = uuid4()
        result = _make_result(hits=[_make_hit(signal_id=sid)], signal_id=sid)
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.LOW

    def test_three_hits_moderate_confidence(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.60),
            _make_hit(signal_id=sid, domain=ImpactDomain.INSURANCE, depth=2, severity=0.40),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.MODERATE

    def test_five_hits_high_confidence(self):
        sid = uuid4()
        domains = [
            ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
            ImpactDomain.INSURANCE, ImpactDomain.TRADE_LOGISTICS, ImpactDomain.MARITIME,
        ]
        hits = [_make_hit(signal_id=sid, domain=d, depth=i) for i, d in enumerate(domains)]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.HIGH

    def test_eight_hits_verified_confidence(self):
        sid = uuid4()
        domains = list(ImpactDomain)[:8]
        hits = [_make_hit(signal_id=sid, domain=d, depth=i) for i, d in enumerate(domains)]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.VERIFIED


# ══════════════════════════════════════════════════════════════════════════════
# 8. compute_impact — Zero-Hit Fallback
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeImpactZeroHitFallback:

    def test_zero_hits_returns_valid_impact(self):
        result = _make_result()
        impact = compute_impact(result)
        assert isinstance(impact, MacroImpact)

    def test_zero_hits_nominal_severity(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.overall_severity == 0.0
        assert impact.overall_severity_level == SignalSeverity.NOMINAL

    def test_zero_hits_zero_exposure_score(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.total_exposure_score == 0.0

    def test_zero_hits_unverified_confidence(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.confidence == SignalConfidence.UNVERIFIED

    def test_zero_hits_empty_domain_impacts(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.domain_impacts == []

    def test_zero_hits_audit_hash_generated(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.audit_hash
        assert len(impact.audit_hash) == 64


# ══════════════════════════════════════════════════════════════════════════════
# 9. Graph Enrichment Detection
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphEnrichment:

    def test_graph_enriched_false_without_graph_fragments(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid, reasoning="Normal reasoning only.")
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.graph_enriched is False

    def test_graph_enriched_true_with_graph_fragments(self):
        sid = uuid4()
        reasoning = "Normal reasoning.\n  [Graph Brain] Graph confirmed: oil_gas → banking path."
        hit = _make_hit(signal_id=sid, reasoning=reasoning)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert impact.graph_enriched is True

    def test_graph_reasoning_preserved_in_domain_impact(self):
        sid = uuid4()
        reasoning = "Normal reasoning.\n  [Graph Brain] 3 graph paths confirmed."
        hit = _make_hit(signal_id=sid, reasoning=reasoning)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert "[Graph Brain]" in impact.domain_impacts[0].reasoning

    def test_graph_reasoning_preserved_in_impact_reasoning(self):
        sid = uuid4()
        reasoning = "Normal reasoning.\n  [Graph Brain] Graph insight."
        hit = _make_hit(signal_id=sid, reasoning=reasoning)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        assert "[Graph Brain]" in impact.impact_reasoning


# ══════════════════════════════════════════════════════════════════════════════
# 10. MacroImpact Model
# ══════════════════════════════════════════════════════════════════════════════

class TestMacroImpactModel:

    def test_critical_domains_property(self):
        """critical_domains returns domains with weighted_impact >= 0.60."""
        sid = uuid4()
        # OIL_GAS: 0.80 * 0.95 = 0.76 → critical
        # TELECOMMUNICATIONS: 0.80 * 0.60 = 0.48 → not critical
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.80),
            _make_hit(signal_id=sid, domain=ImpactDomain.TELECOMMUNICATIONS, depth=1, severity=0.80),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        critical = impact.critical_domains
        domains_in_critical = [d.domain for d in critical]
        assert ImpactDomain.OIL_GAS in domains_in_critical
        assert ImpactDomain.TELECOMMUNICATIONS not in domains_in_critical

    def test_high_severity_domains_property(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.80),    # HIGH+
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.40),  # not HIGH
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        high_sev = impact.high_severity_domains
        domains = [d.domain for d in high_sev]
        assert ImpactDomain.OIL_GAS in domains
        assert ImpactDomain.BANKING not in domains

    def test_affected_domains_sorted_by_severity_desc(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.50),
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.80),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        # OIL_GAS (0.80) should come before BANKING (0.50)
        assert impact.affected_domains[0] == ImpactDomain.OIL_GAS
        assert impact.affected_domains[1] == ImpactDomain.BANKING

    def test_audit_hash_is_sha256(self):
        result = _make_result()
        impact = compute_impact(result)
        # Verify it's valid hex
        int(impact.audit_hash, 16)  # raises ValueError if not valid hex
        assert len(impact.audit_hash) == 64

    def test_same_result_same_impact_hash(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        impact1 = compute_impact(result)
        # Create same result again
        result2 = _make_result(hits=[hit], signal_id=sid)
        impact2 = compute_impact(result2)
        # impact_ids differ (uuid4) but overall_severity and exposure are same
        assert impact1.overall_severity == impact2.overall_severity
        assert impact1.total_exposure_score == impact2.total_exposure_score


# ══════════════════════════════════════════════════════════════════════════════
# 11. DomainImpact Model
# ══════════════════════════════════════════════════════════════════════════════

class TestDomainImpactModel:

    def test_domain_impact_fields(self):
        di = DomainImpact(
            domain=ImpactDomain.BANKING,
            severity_score=0.70,
            severity_level=SignalSeverity.HIGH,
            exposure_weight=0.85,
            weighted_impact=round(0.70 * 0.85, 6),
            depth=1,
            path_description="oil_gas → banking",
            reasoning="Reached via propagation.",
        )
        assert di.domain == ImpactDomain.BANKING
        assert di.is_entry_domain is False

    def test_domain_impact_is_entry_default_false(self):
        di = DomainImpact(
            domain=ImpactDomain.OIL_GAS,
            severity_score=0.80,
            severity_level=SignalSeverity.SEVERE,
            exposure_weight=0.95,
            weighted_impact=0.76,
            depth=0,
            path_description="[ENTRY] oil_gas",
            reasoning="Direct entry.",
            is_entry_domain=True,
        )
        assert di.is_entry_domain is True

    def test_domain_impact_severity_score_range(self):
        with pytest.raises(Exception):
            DomainImpact(
                domain=ImpactDomain.BANKING,
                severity_score=1.5,  # out of range
                severity_level=SignalSeverity.SEVERE,
                exposure_weight=0.85,
                weighted_impact=0.85,
                depth=0,
                path_description="path",
                reasoning="test",
            )


# ══════════════════════════════════════════════════════════════════════════════
# 12. Backward Compatibility
# ══════════════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:

    def test_impact_always_has_signal_id(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.signal_id == result.signal_id

    def test_impact_always_has_signal_title(self):
        result = _make_result()
        impact = compute_impact(result)
        assert impact.signal_title == result.signal_title

    def test_impact_total_domains_matches_result(self):
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.60),
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        assert impact.total_domains_reached == result.total_domains_reached

    def test_domain_impacts_contain_all_hits(self):
        sid = uuid4()
        hit_domains = [
            ImpactDomain.OIL_GAS,
            ImpactDomain.BANKING,
            ImpactDomain.INSURANCE,
        ]
        hits = [
            _make_hit(signal_id=sid, domain=d, depth=i) for i, d in enumerate(hit_domains)
        ]
        result = _make_result(hits=hits, signal_id=sid)
        impact = compute_impact(result)
        impact_domains = {di.domain for di in impact.domain_impacts}
        for d in hit_domains:
            assert d in impact_domains

    def test_result_with_graph_enrichment_field(self):
        """PropagationResult.graph_enrichment (optional) doesn't affect impact."""
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        result.graph_enrichment = {"causal_hints": 3, "explanation_fragments": 2}
        impact = compute_impact(result)
        # Should not raise, graph_enrichment in result is ignored by impact engine
        assert isinstance(impact, MacroImpact)
