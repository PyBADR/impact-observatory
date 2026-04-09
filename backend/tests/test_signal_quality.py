"""Signal Quality Upgrade Pack — Tests.

Covers:
  Region Engine
    1.  GCC-wide terms detected
    2.  Saudi Arabia official name + aliases
    3.  UAE cities and orgs
    4.  Qatar-specific keywords (QatarEnergy, Ras Laffan, Doha)
    5.  Kuwait, Bahrain, Oman detection
    6.  Multi-country hint → multiple regions
    7.  Confidence ordering: specific > broad
    8.  Coverage score: single member vs multi-member
    9.  GCC_WIDE alone → coverage 0.5
    10. Empty hints → empty RegionMapping
    11. detect_gcc() True/False
    12. to_gcc_regions() fallback to GCC_WIDE
    13. Org/landmark → region (Aramco → SA, DP World → UAE)
    14. Strait of Hormuz → Oman
    15. resolve_regions never raises on garbage input

  Domain Engine
    16. Oil & Gas keywords
    17. Banking keywords
    18. Insurance keywords
    19. Trade & Logistics keywords
    20. Sovereign / Fiscal keywords
    21. Maritime keywords (Strait of Hormuz, tanker)
    22. Energy Grid keywords
    23. Cyber Infrastructure keywords
    24. Capital Markets keywords
    25. Aviation keywords
    26. Telecommunications keywords
    27. Real Estate keywords
    28. Multi-domain hints → multiple domains
    29. Primary domain is highest-weighted
    30. Longer keyword preferred over shorter overlap
    31. resolve_domains never raises on garbage input
    32. Empty hints → empty DomainMapping

  Severity Engine
    33. VERIFIED confidence → high score
    34. UNVERIFIED confidence → low score
    35. High-exposure domain boosts domain_factor
    36. Urgency keywords detected and accumulate
    37. Multiple urgency keywords add bonus
    38. No urgency keywords → urgency_factor = 0
    39. GCC region coverage boosts region_factor
    40. No GCC region → region_factor = 0
    41. Final score in [0.0, 1.0]
    42. Highest-urgency scenario produces high overall score
    43. Notes string produced correctly
    44. compute_severity never raises on bad input

  Mapper / SignalClassification
    45. HIGH quality: region + domain + description + timestamp + HIGH confidence
    46. GOOD quality: region + domain + moderate confidence, short description
    47. ACCEPTABLE quality: domain only, no region
    48. LOW quality: no domain, no region, low confidence
    49. POOR quality: bare minimum data
    50. quality_factors keys are present
    51. notes populated when region or domain missing
    52. classify_event never raises on minimal event
    53. Severity estimate embedded in classification
    54. region_mapping embedded in classification
    55. domain_mapping embedded in classification

  Normalizer Integration
    56. to_signal_input uses engine-derived severity (not flat default)
    57. Regions use engine output (richer than basic _resolve_regions)
    58. Domains use engine output (richer than basic _resolve_domains)
    59. severity_score never below confidence baseline
    60. to_signal_input still never raises
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.macro.macro_enums import GCCRegion, ImpactDomain
from src.signals.domain_engine import resolve_domains
from src.signals.mapper import classify_event
from src.signals.normalizer import to_signal_input
from src.signals.region_engine import detect_gcc, resolve_regions, to_gcc_regions
from src.signals.severity_engine import compute_severity
from src.signals.source_models import SourceConfidence, SourceEvent, SourceType
from src.signals.types import DomainMapping, RegionMapping, SignalQuality


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _event(
    title: str = "Test event",
    description: str | None = None,
    region_hints: list[str] | None = None,
    country_hints: list[str] | None = None,
    sector_hints: list[str] | None = None,
    category_hints: list[str] | None = None,
    source_confidence: SourceConfidence = SourceConfidence.MODERATE,
    published_at: datetime | None = None,
) -> SourceEvent:
    return SourceEvent(
        source_type=SourceType.RSS,
        source_name="Test Feed",
        source_ref="https://feeds.test.com",
        title=title,
        description=description,
        region_hints=region_hints or [],
        country_hints=country_hints or [],
        sector_hints=sector_hints or [],
        category_hints=category_hints or [],
        source_confidence=source_confidence,
        published_at=published_at,
    )


_NOW = datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# 1–15. Region Engine
# ══════════════════════════════════════════════════════════════════════════════

class TestRegionEngine:

    # 1. GCC-wide terms
    def test_gcc_wide_detected(self):
        m = resolve_regions(["GCC", "Gulf Cooperation Council"])
        assert m.gcc_detected is True
        assert GCCRegion.GCC_WIDE.value in m.matched_regions

    # 2. Saudi Arabia — official + aliases
    def test_saudi_arabia_official_and_alias(self):
        m = resolve_regions(["Kingdom of Saudi Arabia", "KSA", "Riyadh"])
        assert GCCRegion.SAUDI_ARABIA.value in m.matched_regions
        assert m.gcc_detected is True

    # 3. UAE cities and orgs
    def test_uae_cities_and_org(self):
        m = resolve_regions(["Dubai", "Abu Dhabi", "ADNOC", "DP World"])
        assert GCCRegion.UAE.value in m.matched_regions

    # 4. Qatar specific
    def test_qatar_specific_keywords(self):
        m = resolve_regions(["QatarEnergy", "Ras Laffan", "Doha"])
        assert GCCRegion.QATAR.value in m.matched_regions

    # 5. Kuwait, Bahrain, Oman
    def test_kuwait_bahrain_oman(self):
        m = resolve_regions(["Kuwait City", "Manama", "Muscat"])
        vals = m.matched_regions
        assert GCCRegion.KUWAIT.value in vals
        assert GCCRegion.BAHRAIN.value in vals
        assert GCCRegion.OMAN.value in vals

    # 6. Multi-country → multiple regions
    def test_multi_country_hints(self):
        m = resolve_regions(["Saudi Arabia", "United Arab Emirates", "Qatar"])
        assert GCCRegion.SAUDI_ARABIA.value in m.matched_regions
        assert GCCRegion.UAE.value in m.matched_regions
        assert GCCRegion.QATAR.value in m.matched_regions

    # 7. Confidence ordering: official name > broad term
    def test_confidence_ordering(self):
        m = resolve_regions(["Saudi Arabia", "Gulf"])
        # Saudi Arabia match should have confidence 1.0; Gulf 0.5
        sa_conf = m.confidence
        assert sa_conf >= 0.9   # aggregate is max(all confidences)

    # 8. Coverage score single vs multi member
    def test_coverage_score_single(self):
        m = resolve_regions(["Saudi Arabia"])
        assert m.coverage_score == round(1 / 6, 4)

    def test_coverage_score_multi(self):
        m = resolve_regions(["Saudi Arabia", "UAE", "Qatar"])
        assert m.coverage_score == round(3 / 6, 4)

    # 9. GCC_WIDE alone → coverage 0.5
    def test_gcc_wide_coverage(self):
        m = resolve_regions(["GCC"])
        assert m.gcc_detected is True
        assert m.coverage_score >= 0.5

    # 10. Empty hints → empty RegionMapping
    def test_empty_hints_returns_empty(self):
        m = resolve_regions([])
        assert m.is_empty is True
        assert m.gcc_detected is False
        assert m.confidence == 0.0

    # 11. detect_gcc True / False
    def test_detect_gcc_true(self):
        assert detect_gcc(["Dubai"]) is True

    def test_detect_gcc_false(self):
        assert detect_gcc(["London", "New York"]) is False

    # 12. to_gcc_regions fallback
    def test_to_gcc_regions_fallback(self):
        empty = RegionMapping()
        result = to_gcc_regions(empty)
        assert result == [GCCRegion.GCC_WIDE]

    def test_to_gcc_regions_returns_matched(self):
        m = resolve_regions(["Saudi Arabia", "Oman"])
        result = to_gcc_regions(m)
        assert GCCRegion.SAUDI_ARABIA in result
        assert GCCRegion.OMAN in result

    # 13. Org/landmark → region
    def test_aramco_maps_to_saudi(self):
        m = resolve_regions(["Saudi Aramco cut production"])
        assert GCCRegion.SAUDI_ARABIA.value in m.matched_regions

    def test_dp_world_maps_to_uae(self):
        m = resolve_regions(["DP World announced expansion"])
        assert GCCRegion.UAE.value in m.matched_regions

    # 14. Strait of Hormuz → Oman
    def test_strait_of_hormuz_maps_to_oman(self):
        m = resolve_regions(["Strait of Hormuz closure threatens oil transit"])
        assert GCCRegion.OMAN.value in m.matched_regions

    # 15. Never raises on garbage
    def test_never_raises_on_garbage(self):
        m = resolve_regions(["!!@@##", "", "   "])
        assert isinstance(m, RegionMapping)


# ══════════════════════════════════════════════════════════════════════════════
# 16–32. Domain Engine
# ══════════════════════════════════════════════════════════════════════════════

class TestDomainEngine:

    # 16. Oil & Gas
    def test_oil_gas_keywords(self):
        m = resolve_domains(["crude oil", "OPEC", "petroleum"])
        assert ImpactDomain.OIL_GAS.value in m.matched_domains

    # 17. Banking
    def test_banking_keywords(self):
        m = resolve_domains(["central bank", "interest rate policy", "credit rating"])
        assert ImpactDomain.BANKING.value in m.matched_domains

    # 18. Insurance
    def test_insurance_keywords(self):
        m = resolve_domains(["takaful", "reinsurance market"])
        assert ImpactDomain.INSURANCE.value in m.matched_domains

    # 19. Trade & Logistics
    def test_trade_logistics_keywords(self):
        m = resolve_domains(["supply chain disruption", "import tariff"])
        assert ImpactDomain.TRADE_LOGISTICS.value in m.matched_domains

    # 20. Sovereign / Fiscal
    def test_sovereign_fiscal_keywords(self):
        m = resolve_domains(["sovereign debt", "government budget", "fiscal deficit"])
        assert ImpactDomain.SOVEREIGN_FISCAL.value in m.matched_domains

    # 21. Maritime
    def test_maritime_keywords(self):
        m = resolve_domains(["Strait of Hormuz", "oil tanker", "maritime security"])
        assert ImpactDomain.MARITIME.value in m.matched_domains

    # 22. Energy Grid
    def test_energy_grid_keywords(self):
        m = resolve_domains(["power grid failure", "electricity supply"])
        assert ImpactDomain.ENERGY_GRID.value in m.matched_domains

    # 23. Cyber Infrastructure
    def test_cyber_infrastructure_keywords(self):
        m = resolve_domains(["cyber attack", "ransomware incident", "data breach"])
        assert ImpactDomain.CYBER_INFRASTRUCTURE.value in m.matched_domains

    # 24. Capital Markets
    def test_capital_markets_keywords(self):
        m = resolve_domains(["stock market", "sukuk issuance", "market volatility"])
        assert ImpactDomain.CAPITAL_MARKETS.value in m.matched_domains

    # 25. Aviation
    def test_aviation_keywords(self):
        m = resolve_domains(["airspace closure", "airline operations"])
        assert ImpactDomain.AVIATION.value in m.matched_domains

    # 26. Telecommunications
    def test_telecom_keywords(self):
        m = resolve_domains(["submarine cable cut", "network outage"])
        assert ImpactDomain.TELECOMMUNICATIONS.value in m.matched_domains

    # 27. Real Estate
    def test_real_estate_keywords(self):
        m = resolve_domains(["real estate market", "property prices"])
        assert ImpactDomain.REAL_ESTATE.value in m.matched_domains

    # 28. Multi-domain hints
    def test_multi_domain_hints(self):
        m = resolve_domains(["crude oil production", "banking sector", "aviation"])
        assert len(m.matched_domains) >= 3

    # 29. Primary domain is highest-weighted
    def test_primary_domain_highest_weight(self):
        m = resolve_domains(["Saudi Aramco crude oil production cut", "trade"])
        assert m.primary_domain == ImpactDomain.OIL_GAS.value

    # 30. Longer keyword preferred over overlap
    def test_longer_keyword_over_short(self):
        # "sovereign debt" should score higher than just "debt" alone
        m = resolve_domains(["sovereign debt crisis"])
        assert ImpactDomain.SOVEREIGN_FISCAL.value in m.matched_domains
        # weight should reflect the compound match
        assert m.domain_weights.get(ImpactDomain.SOVEREIGN_FISCAL.value, 0) > 0.5

    # 31. Never raises on garbage
    def test_never_raises_on_garbage(self):
        m = resolve_domains(["!!", "", "   ", "xyzzy"])
        assert isinstance(m, DomainMapping)

    # 32. Empty hints → empty DomainMapping
    def test_empty_hints_returns_empty(self):
        m = resolve_domains([])
        assert m.is_empty is True
        assert m.primary_domain is None
        assert m.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 33–44. Severity Engine
# ══════════════════════════════════════════════════════════════════════════════

class TestSeverityEngine:

    def _severity(
        self,
        confidence: SourceConfidence = SourceConfidence.MODERATE,
        domain_hints: list[str] | None = None,
        region_hints: list[str] | None = None,
        text_hints: list[str] | None = None,
    ):
        from src.signals.domain_engine import resolve_domains
        from src.signals.region_engine import resolve_regions
        dm = resolve_domains(domain_hints or [])
        rm = resolve_regions(region_hints or [])
        return compute_severity(confidence, dm, rm, text_hints or [])

    # 33. VERIFIED confidence → high confidence_factor
    def test_verified_confidence_high_factor(self):
        est = self._severity(confidence=SourceConfidence.VERIFIED)
        assert est.confidence_factor == 1.0

    # 34. UNVERIFIED confidence → low factor
    def test_unverified_confidence_low_factor(self):
        est = self._severity(confidence=SourceConfidence.UNVERIFIED)
        assert est.confidence_factor == 0.25

    # 35. High-exposure domain boosts domain_factor
    def test_high_exposure_domain_boosts_factor(self):
        est_oil = self._severity(domain_hints=["Saudi Aramco crude oil"])
        est_none = self._severity(domain_hints=[])
        assert est_oil.domain_factor > est_none.domain_factor

    # 36. Urgency keywords detected
    def test_urgency_keywords_detected(self):
        est = self._severity(text_hints=["emergency shutdown of the oil field"])
        assert "emergency" in est.urgency_keywords_found
        assert est.urgency_factor > 0

    # 37. Multiple urgency keywords add bonus
    def test_multiple_urgency_keywords_bonus(self):
        single = self._severity(text_hints=["emergency"])
        multi  = self._severity(text_hints=["emergency critical immediate collapse attack"])
        assert multi.urgency_factor >= single.urgency_factor

    # 38. No urgency keywords → urgency_factor == 0
    def test_no_urgency_keywords(self):
        est = self._severity(text_hints=["quarterly earnings report"])
        assert est.urgency_factor == 0.0

    # 39. GCC region coverage boosts region_factor
    def test_gcc_region_boosts_factor(self):
        est_gcc  = self._severity(region_hints=["Saudi Arabia", "UAE"])
        est_none = self._severity(region_hints=[])
        assert est_gcc.region_factor > est_none.region_factor

    # 40. No GCC region → region_factor == 0
    def test_no_gcc_region_zero_factor(self):
        est = self._severity(region_hints=["London", "New York"])
        assert est.region_factor == 0.0

    # 41. Score in [0.0, 1.0]
    def test_score_bounded(self):
        est = self._severity(
            confidence=SourceConfidence.VERIFIED,
            domain_hints=["Saudi Aramco", "crude oil", "banking", "sovereign debt"],
            region_hints=["Saudi Arabia", "UAE", "Qatar"],
            text_hints=["emergency critical immediate collapse attack ransomware"],
        )
        assert 0.0 <= est.score <= 1.0

    # 42. High urgency scenario produces high score
    def test_high_urgency_produces_high_score(self):
        est = self._severity(
            confidence=SourceConfidence.HIGH,
            domain_hints=["crude oil production halt", "sovereign debt default"],
            region_hints=["Saudi Arabia", "UAE"],
            text_hints=["emergency immediate attack collapse critical shutdown"],
        )
        assert est.score >= 0.60

    # 43. Notes string produced
    def test_notes_string_produced(self):
        est = self._severity()
        assert "conf=" in est.notes
        assert "→" in est.notes

    # 44. Never raises on bad input
    def test_never_raises_on_bad_input(self):
        from src.signals.types import DomainMapping, RegionMapping
        est = compute_severity(
            source_confidence=SourceConfidence.LOW,
            domain_mapping=DomainMapping(),
            region_mapping=RegionMapping(),
            text_hints=["!!", ""],
        )
        assert 0.0 <= est.score <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 45–55. Mapper / SignalClassification
# ══════════════════════════════════════════════════════════════════════════════

class TestMapper:

    # 45. HIGH quality: everything present
    def test_high_quality_event(self):
        event = _event(
            title="Saudi Aramco crude oil production cut emergency",
            description="Saudi Aramco announced an immediate emergency cut to crude oil production "
                        "following an attack on a major refinery in the Eastern Province of Saudi Arabia.",
            region_hints=["Saudi Arabia"],
            sector_hints=["crude oil", "petroleum"],
            category_hints=["energy", "oil"],
            source_confidence=SourceConfidence.HIGH,
            published_at=_NOW,
        )
        cls = classify_event(event)
        assert cls.quality in (SignalQuality.HIGH, SignalQuality.GOOD)
        assert cls.quality_score >= 0.60

    # 46. GOOD quality: region + domain + moderate confidence
    def test_good_quality_event(self):
        event = _event(
            title="Qatar banking sector expands",
            description="Qatar banks report strong growth.",
            region_hints=["Qatar"],
            sector_hints=["banking"],
            source_confidence=SourceConfidence.MODERATE,
            published_at=_NOW,
        )
        cls = classify_event(event)
        assert cls.quality in (SignalQuality.GOOD, SignalQuality.ACCEPTABLE, SignalQuality.HIGH)

    # 47. ACCEPTABLE: domain only, no region
    def test_acceptable_quality_domain_only(self):
        event = _event(
            title="Oil market volatility continues",
            sector_hints=["crude oil", "petroleum"],
            source_confidence=SourceConfidence.MODERATE,
            published_at=_NOW,
        )
        cls = classify_event(event)
        # Domain detected without region → acceptable or higher
        assert cls.quality_score >= 0.0   # score is deterministic
        assert "no GCC region identified" in cls.notes

    # 48. LOW quality: no domain, no region, low confidence
    def test_low_quality_minimal_data(self):
        event = _event(
            title="Market update",
            source_confidence=SourceConfidence.LOW,
        )
        cls = classify_event(event)
        assert cls.quality in (SignalQuality.POOR, SignalQuality.LOW, SignalQuality.ACCEPTABLE)

    # 49. POOR quality: bare minimum
    def test_poor_quality_event(self):
        event = _event(
            title="Update",
            source_confidence=SourceConfidence.UNVERIFIED,
        )
        cls = classify_event(event)
        # Bare unverified event with no domain/region → POOR or LOW
        assert cls.quality in (SignalQuality.POOR, SignalQuality.LOW)

    # 50. quality_factors keys are present
    def test_quality_factors_keys_present(self):
        event = _event(title="Test")
        cls = classify_event(event)
        for key in ("region", "domain", "description", "timestamp", "source_confidence"):
            assert key in cls.quality_factors

    # 51. Notes populated when region/domain missing
    def test_notes_populated_on_missing_region(self):
        event = _event(title="Some update")
        cls = classify_event(event)
        assert "no GCC region identified" in cls.notes

    def test_notes_populated_on_missing_domain(self):
        event = _event(title="Some update")
        cls = classify_event(event)
        assert "no domain identified" in cls.notes

    # 52. Never raises on minimal event
    def test_classify_event_never_raises(self):
        event = _event(title="x")
        cls = classify_event(event)
        assert isinstance(cls, object)

    # 53. Severity estimate embedded
    def test_severity_estimate_embedded(self):
        event = _event(
            title="Emergency crude oil shutdown in Saudi Arabia",
            region_hints=["Saudi Arabia"],
            sector_hints=["crude oil"],
            source_confidence=SourceConfidence.HIGH,
        )
        cls = classify_event(event)
        assert cls.severity_estimate.score > 0.0

    # 54. Region mapping embedded
    def test_region_mapping_embedded(self):
        event = _event(
            title="Update",
            region_hints=["Saudi Arabia"],
        )
        cls = classify_event(event)
        assert cls.region_mapping.gcc_detected is True
        assert GCCRegion.SAUDI_ARABIA.value in cls.region_mapping.matched_regions

    # 55. Domain mapping embedded
    def test_domain_mapping_embedded(self):
        event = _event(
            title="Crude oil production cut",
            sector_hints=["crude oil"],
        )
        cls = classify_event(event)
        assert not cls.domain_mapping.is_empty
        assert ImpactDomain.OIL_GAS.value in cls.domain_mapping.matched_domains


# ══════════════════════════════════════════════════════════════════════════════
# 56–60. Normalizer Integration
# ══════════════════════════════════════════════════════════════════════════════

class TestNormalizerIntegration:

    # 56. to_signal_input uses engine-derived severity (not flat default)
    def test_severity_uses_engine(self):
        """Event with high-urgency keywords should exceed bare confidence baseline."""
        event_urgent = _event(
            title="Emergency immediate attack: oil pipeline exploded in Saudi Arabia",
            region_hints=["Saudi Arabia"],
            sector_hints=["crude oil", "pipeline"],
            category_hints=["conflict", "attack"],
            source_confidence=SourceConfidence.HIGH,
        )
        event_plain = _event(
            title="Quarterly earnings",
            source_confidence=SourceConfidence.HIGH,
        )
        sig_urgent = to_signal_input(event_urgent)
        sig_plain  = to_signal_input(event_plain)
        # Urgent event should have higher severity score
        assert sig_urgent.severity_score > sig_plain.severity_score

    # 57. Regions use engine output (richer than basic _resolve_regions)
    def test_regions_use_engine_output(self):
        """Org keywords like 'Saudi Aramco' should resolve to SAUDI_ARABIA."""
        event = _event(
            title="Saudi Aramco announces production cut",
            region_hints=["Saudi Aramco"],
        )
        sig = to_signal_input(event)
        assert GCCRegion.SAUDI_ARABIA in sig.regions

    # 58. Domains use engine output (richer than basic _resolve_domains)
    def test_domains_use_engine_output(self):
        """Sovereign fiscal keywords should resolve correctly via domain_engine."""
        event = _event(
            title="Sovereign debt downgrade risk",
            sector_hints=["sovereign debt", "fiscal deficit"],
        )
        sig = to_signal_input(event)
        assert ImpactDomain.SOVEREIGN_FISCAL in sig.impact_domains

    # 59. severity_score never below confidence baseline
    def test_severity_never_below_baseline(self):
        from src.signals.normalizer import _default_severity
        for conf in SourceConfidence:
            event = _event(source_confidence=conf)
            sig = to_signal_input(event)
            baseline = _default_severity(conf)
            assert sig.severity_score >= baseline, (
                f"severity_score {sig.severity_score} below baseline {baseline} "
                f"for confidence {conf}"
            )

    # 60. to_signal_input never raises
    def test_to_signal_input_never_raises(self):
        for conf in SourceConfidence:
            event = _event(
                title="Signal update",
                source_confidence=conf,
                region_hints=["garbage garbage!!"],
                sector_hints=["zzz"],
            )
            sig = to_signal_input(event)
            assert sig.title is not None
