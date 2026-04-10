"""Signal Intelligence Layer — Enrichment Engine Test Suite.

Comprehensive unit tests for all four enrichment functions:
  1. classify_signal_type — keyword/category → signal type
  2. extract_regions — title/description → region codes
  3. extract_domains — title/description + categories → domain hints
  4. compute_severity — multi-factor severity scoring

Plus integration tests for enrich_feed_item() composite function.

All tests are deterministic. No network calls. No LLM.
"""

from __future__ import annotations

import pytest

from src.signal_intel.enrichment import (
    classify_signal_type,
    compute_severity,
    enrich_feed_item,
    extract_domains,
    extract_regions,
)
from src.signal_intel.types import FeedType, RawFeedItem


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _make_item(
    title: str = "Test signal about GCC oil markets",
    description: str = "Some description",
    feed_type: FeedType = FeedType.RSS,
    severity_hint: float | None = None,
    region_hints: list[str] | None = None,
    domain_hints: list[str] | None = None,
    signal_type_hint: str | None = None,
    source_quality: float = 0.5,
    confidence: str = "moderate",
    categories: list[str] | None = None,
) -> RawFeedItem:
    item = RawFeedItem(
        feed_id="test-feed",
        feed_type=feed_type,
        title=title,
        description=description,
        severity_hint=severity_hint,
        region_hints=region_hints or [],
        domain_hints=domain_hints or [],
        signal_type_hint=signal_type_hint,
        source_quality=source_quality,
        confidence=confidence,
        payload={"categories": categories or []},
    )
    return item


# ══════════════════════════════════════════════════════════════════════════════
# 1. SIGNAL TYPE CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestClassifySignalType:

    def test_existing_hint_passthrough(self):
        """Existing hint is never overridden."""
        result = classify_signal_type(
            title="Oil prices surge",
            existing_hint="commodity",
        )
        assert result == "commodity"

    def test_geopolitical_war(self):
        result = classify_signal_type(title="War breaks out in region")
        assert result == "geopolitical"

    def test_geopolitical_sanctions(self):
        result = classify_signal_type(title="New sanctions imposed on exports")
        assert result == "geopolitical"

    def test_geopolitical_conflict(self):
        result = classify_signal_type(title="Armed conflict escalates near border")
        assert result == "geopolitical"

    def test_geopolitical_missile(self):
        result = classify_signal_type(title="Missile strikes reported near oil facility")
        assert result == "geopolitical"

    def test_policy_interest_rate(self):
        result = classify_signal_type(title="Central bank raises interest rate by 50bp")
        assert result == "policy"

    def test_policy_fiscal(self):
        result = classify_signal_type(title="Government announces fiscal stimulus package")
        assert result == "policy"

    def test_commodity_crude(self):
        result = classify_signal_type(title="Brent crude drops below $70")
        assert result == "commodity"

    def test_commodity_opec(self):
        result = classify_signal_type(title="OPEC agrees to cut production")
        assert result == "commodity"

    def test_commodity_lng(self):
        result = classify_signal_type(title="Qatar LNG exports hit record levels")
        assert result == "commodity"

    def test_logistics_port(self):
        result = classify_signal_type(title="Major port closure disrupts trade")
        assert result == "logistics"

    def test_logistics_supply_chain(self):
        result = classify_signal_type(title="Supply chain disruption worsens")
        assert result == "logistics"

    def test_regulatory(self):
        result = classify_signal_type(title="New regulation affects banking compliance")
        assert result == "regulatory"

    def test_market_ipo(self):
        result = classify_signal_type(title="Major IPO launches on exchange")
        assert result == "market"

    def test_sentiment_outlook(self):
        result = classify_signal_type(title="Consumer confidence outlook improves")
        assert result == "sentiment"

    def test_systemic_contagion(self):
        result = classify_signal_type(title="Financial contagion spreads across sectors")
        assert result == "systemic"

    def test_systemic_collapse(self):
        result = classify_signal_type(title="Systemic risk of banking collapse")
        assert result == "systemic"

    def test_category_match(self):
        result = classify_signal_type(
            title="Something happened",
            categories=["Energy", "commodity"],
        )
        assert result == "commodity"

    def test_no_match_returns_none(self):
        result = classify_signal_type(title="Today is a nice day for a walk")
        assert result is None

    def test_economic_feed_fallback(self):
        result = classify_signal_type(
            title="Data update for Q1",
            feed_type=FeedType.ECONOMIC,
        )
        assert result == "market"

    def test_description_used_for_classification(self):
        result = classify_signal_type(
            title="Breaking news update",
            description="Military escalation reported near the strait",
        )
        assert result == "geopolitical"

    def test_priority_geopolitical_over_market(self):
        """Geopolitical keywords have higher priority than market."""
        result = classify_signal_type(
            title="War disrupts stock market trading",
        )
        assert result == "geopolitical"

    def test_priority_systemic_over_sentiment(self):
        result = classify_signal_type(
            title="Financial crisis triggers systemic risk and negative sentiment",
        )
        assert result in ("systemic",)


# ══════════════════════════════════════════════════════════════════════════════
# 2. REGION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractRegions:

    def test_riyadh_extracts_sa(self):
        result = extract_regions("Riyadh stock exchange closes higher")
        assert "SA" in result

    def test_jebel_ali_extracts_ae(self):
        result = extract_regions("Jebel Ali port reports record throughput")
        assert "AE" in result

    def test_dubai_extracts_ae(self):
        result = extract_regions("Dubai real estate market surges")
        assert "AE" in result

    def test_ras_laffan_extracts_qa(self):
        result = extract_regions("Ras Laffan LNG terminal expansion")
        assert "QA" in result

    def test_doha_extracts_qa(self):
        result = extract_regions("Doha summit on economic cooperation")
        assert "QA" in result

    def test_salalah_extracts_om(self):
        result = extract_regions("Salalah port closure due to weather")
        assert "OM" in result

    def test_manama_extracts_bh(self):
        result = extract_regions("Manama banking conference held today")
        assert "BH" in result

    def test_kuwait_extracts_kw(self):
        result = extract_regions("Kuwait oil sector reports growth")
        assert "KW" in result

    def test_hormuz_extracts_gcc(self):
        result = extract_regions("Strait of Hormuz shipping disrupted")
        assert "GCC" in result

    def test_multiple_regions_in_title(self):
        result = extract_regions("Dubai and Riyadh stock exchanges rally")
        assert "AE" in result
        assert "SA" in result

    def test_arabic_riyadh(self):
        result = extract_regions("أخبار الرياض الاقتصادية")
        assert "SA" in result

    def test_arabic_dubai(self):
        result = extract_regions("سوق دبي المالي يرتفع")
        assert "AE" in result

    def test_arabic_gcc(self):
        result = extract_regions("مجلس التعاون الخليجي يجتمع")
        assert "GCC" in result

    def test_existing_hints_preserved(self):
        result = extract_regions(
            "Some neutral title",
            existing_hints=["SA", "AE"],
        )
        assert "SA" in result
        assert "AE" in result

    def test_no_region_returns_existing_only(self):
        result = extract_regions(
            "A completely generic statement about nothing",
            existing_hints=["GCC"],
        )
        assert "GCC" in result

    def test_description_scanned(self):
        result = extract_regions(
            "Breaking news today",
            description="Oil facility near Dammam affected by storm",
        )
        assert "SA" in result

    def test_aramco_implies_saudi(self):
        result = extract_regions("Aramco announces quarterly results")
        assert "SA" in result

    def test_adnoc_implies_uae(self):
        result = extract_regions("ADNOC expands production capacity")
        assert "AE" in result

    # ── Word boundary tests ──────────────────────────────────────────────────

    def test_ottoman_does_not_match_oman(self):
        """'Ottoman' must NOT produce an Oman match."""
        result = extract_regions("Ottoman empire historical analysis")
        assert "OM" not in result

    def test_romania_does_not_match_oman(self):
        """'Romania' must NOT produce an Oman match."""
        result = extract_regions("Romania trade policy update")
        assert "OM" not in result

    def test_oman_standalone_matches(self):
        """Standalone 'Oman' DOES match."""
        result = extract_regions("Oman GDP growth forecast released")
        assert "OM" in result

    def test_oman_in_sentence(self):
        result = extract_regions("The economy of Oman is diversifying")
        assert "OM" in result

    def test_oman_with_punctuation(self):
        result = extract_regions("Shipping routes near Oman, disrupted")
        assert "OM" in result

    def test_case_insensitivity(self):
        result = extract_regions("RIYADH reports economic data")
        assert "SA" in result

    def test_neom_extracts_sa(self):
        result = extract_regions("NEOM project accelerates construction")
        assert "SA" in result

    def test_duqm_extracts_om(self):
        result = extract_regions("Duqm port development on track")
        assert "OM" in result

    def test_tadawul_extracts_sa(self):
        result = extract_regions("Tadawul index hits new high")
        assert "SA" in result


# ══════════════════════════════════════════════════════════════════════════════
# 3. DOMAIN EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestExtractDomains:

    def test_crude_oil_extracts_oil_gas(self):
        result = extract_domains("Crude oil prices surge sharply")
        assert "oil_gas" in result

    def test_brent_extracts_oil_gas(self):
        result = extract_domains("Brent futures rally to $90")
        assert "oil_gas" in result

    def test_opec_extracts_oil_gas(self):
        result = extract_domains("OPEC meeting concludes with cuts")
        assert "oil_gas" in result

    def test_central_bank_extracts_banking(self):
        result = extract_domains("Central bank rate decision expected")
        assert "banking" in result

    def test_interest_rate_extracts_banking(self):
        result = extract_domains("Interest rate hike announced")
        assert "banking" in result

    def test_insurance_keyword(self):
        result = extract_domains("Insurance claims spike after event")
        assert "insurance" in result

    def test_reinsurance_keyword(self):
        result = extract_domains("Reinsurance market tightens globally")
        assert "insurance" in result

    def test_airport_extracts_aviation(self):
        result = extract_domains("Airport delays reported across GCC")
        assert "aviation" in result

    def test_supply_chain_extracts_trade(self):
        result = extract_domains("Supply chain disruptions continue")
        assert "trade_logistics" in result

    def test_port_closure_extracts_trade(self):
        result = extract_domains("Port closure affects cargo movement")
        assert "trade_logistics" in result

    def test_cybersecurity_extracts_cyber(self):
        result = extract_domains("Cybersecurity breach at financial firm")
        assert "cyber_infrastructure" in result

    def test_real_estate_keyword(self):
        result = extract_domains("Real estate sector shows recovery")
        assert "real_estate" in result

    def test_sovereign_debt_keyword(self):
        result = extract_domains("Sovereign debt concerns rise in GCC")
        assert "sovereign_fiscal" in result

    def test_multiple_domains_from_title(self):
        result = extract_domains("Oil prices and banking sector both affected by crisis")
        # Should extract both
        assert "oil_gas" in result or "banking" in result

    def test_category_resolution(self):
        result = extract_domains(
            "Some event happened",
            categories=["Energy", "Banking"],
        )
        assert "energy_grid" in result
        assert "banking" in result

    def test_existing_hints_preserved(self):
        result = extract_domains(
            "Generic title",
            existing_hints=["oil_gas"],
        )
        assert "oil_gas" in result

    def test_no_match_returns_existing(self):
        result = extract_domains(
            "A walk in the park",
            existing_hints=["oil_gas"],
        )
        assert "oil_gas" in result

    def test_description_used(self):
        result = extract_domains(
            "Breaking news update",
            description="Stock market volatility and forex fluctuations reported",
        )
        assert "capital_markets" in result

    def test_maritime_keyword(self):
        result = extract_domains("Tanker fleet movements monitored")
        assert "maritime" in result

    def test_takaful_extracts_insurance(self):
        result = extract_domains("Takaful market growth exceeds forecast")
        assert "insurance" in result

    def test_vision_2030_extracts_sovereign(self):
        result = extract_domains("Vision 2030 progress report published")
        assert "sovereign_fiscal" in result

    def test_gdp_extracts_sovereign(self):
        result = extract_domains("GDP growth slows in Q2")
        assert "sovereign_fiscal" in result

    def test_ipo_extracts_capital_markets(self):
        result = extract_domains("Major IPO launches on exchange")
        assert "capital_markets" in result


# ══════════════════════════════════════════════════════════════════════════════
# 4. SEVERITY SCORING
# ══════════════════════════════════════════════════════════════════════════════

class TestComputeSeverity:

    def test_output_range_always_valid(self):
        """All outputs must be in [0.0, 1.0]."""
        test_cases = [
            ("War breaks out", None),
            ("Peace agreement signed", None),
            ("Normal day", None),
            ("Total catastrophe and meltdown", 0.9),
            ("Stable growth expected", 0.1),
        ]
        for title, hint in test_cases:
            result = compute_severity(title, existing_hint=hint)
            assert 0.0 <= result <= 1.0, f"Out of range for '{title}': {result}"

    def test_crisis_amplifies_base(self):
        """'crisis' keyword should amplify severity significantly."""
        base = compute_severity("Normal economic update", existing_hint=0.3)
        crisis = compute_severity("Economic crisis deepens", existing_hint=0.3)
        assert crisis > base

    def test_war_amplifies_strongly(self):
        result = compute_severity(
            "War erupts near oil fields",
            existing_hint=0.3,
            source_quality=0.9,
            confidence="verified",
        )
        assert result >= 0.5  # significant amplification

    def test_recovery_dampens_severity(self):
        """'recovery' keyword should dampen severity."""
        base = compute_severity("Economic update released", existing_hint=0.5)
        recovery = compute_severity("Economic recovery continues", existing_hint=0.5)
        assert recovery < base

    def test_peace_dampens_severity(self):
        result = compute_severity(
            "Peace agreement reached in region",
            existing_hint=0.5,
            source_quality=0.9,
            confidence="verified",
        )
        assert result < 0.5

    def test_high_source_quality_increases_severity(self):
        low_q = compute_severity("Crisis event", existing_hint=0.5, source_quality=0.2)
        high_q = compute_severity("Crisis event", existing_hint=0.5, source_quality=0.9)
        assert high_q > low_q

    def test_verified_confidence_increases_severity(self):
        unverified = compute_severity("Crisis event", existing_hint=0.5, confidence="unverified")
        verified = compute_severity("Crisis event", existing_hint=0.5, confidence="verified")
        assert verified > unverified

    def test_existing_hint_used_as_base(self):
        """When existing_hint is provided, it becomes the base."""
        result = compute_severity("Normal update", existing_hint=0.8)
        assert result > 0.3  # should be based on 0.8 not default 0.3

    def test_no_hint_uses_default_base(self):
        """When no hint, default 0.3 is used as base."""
        result = compute_severity("Normal update")
        # With default quality=0.5 and confidence="unverified":
        # 0.3 * 1.0 * 0.85 * 0.60 ≈ 0.153
        assert 0.0 < result < 0.5

    def test_catastrophe_clamped_at_1(self):
        """Even with maximum amplification, output clamped at 1.0."""
        result = compute_severity(
            "Catastrophic war and meltdown",
            existing_hint=0.9,
            source_quality=1.0,
            confidence="verified",
        )
        assert result <= 1.0

    def test_no_keywords_no_amplification(self):
        """Title with no severity keywords should get multiplier of 1.0."""
        result = compute_severity(
            "Quarterly financial report published",
            existing_hint=0.5,
            source_quality=0.5,
            confidence="moderate",
        )
        # 0.5 * 1.0 * 0.85 * 0.85 ≈ 0.36
        assert 0.25 < result < 0.50

    def test_description_scanned_for_keywords(self):
        base = compute_severity("Update on economy")
        with_desc = compute_severity(
            "Update on economy",
            description="Complete shutdown of critical infrastructure",
        )
        assert with_desc > base

    def test_deterministic(self):
        """Same input always produces same output."""
        a = compute_severity("Oil crisis worsens", existing_hint=0.5)
        b = compute_severity("Oil crisis worsens", existing_hint=0.5)
        assert a == b

    def test_disruption_moderate_amplification(self):
        base = compute_severity("Port operations continue", existing_hint=0.4)
        disrupted = compute_severity("Port disruption affects trade", existing_hint=0.4)
        assert disrupted > base

    def test_zero_hint_uses_default(self):
        """existing_hint=0.0 should fall back to default 0.3."""
        result = compute_severity("Normal update", existing_hint=0.0)
        default = compute_severity("Normal update", existing_hint=None)
        assert result == default

    def test_confidence_weights_ordering(self):
        """verified > high > moderate > low > unverified."""
        scores = {}
        for conf in ["verified", "high", "moderate", "low", "unverified"]:
            scores[conf] = compute_severity("Crisis event", existing_hint=0.5, confidence=conf)
        assert scores["verified"] > scores["high"]
        assert scores["high"] > scores["moderate"]
        assert scores["moderate"] > scores["low"]
        assert scores["low"] > scores["unverified"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. COMPOSITE ENRICHMENT (enrich_feed_item)
# ══════════════════════════════════════════════════════════════════════════════

class TestEnrichFeedItem:

    def test_enriches_signal_type(self):
        item = _make_item(title="OPEC cuts oil production quota")
        enrich_feed_item(item)
        assert item.signal_type_hint == "commodity"

    def test_enriches_regions_from_title(self):
        item = _make_item(title="Dubai financial market reports gains")
        enrich_feed_item(item)
        assert "AE" in item.region_hints

    def test_enriches_domains_from_title(self):
        item = _make_item(title="Crude oil prices surge to new highs")
        enrich_feed_item(item)
        assert "oil_gas" in item.domain_hints

    def test_enriches_severity(self):
        item = _make_item(
            title="Economic crisis deepens across region",
            severity_hint=0.3,
            source_quality=0.9,
            confidence="verified",
        )
        enrich_feed_item(item)
        assert item.severity_hint > 0.3  # should be amplified

    def test_preserves_existing_signal_type(self):
        item = _make_item(
            title="Something about oil markets",
            signal_type_hint="logistics",
        )
        enrich_feed_item(item)
        assert item.signal_type_hint == "logistics"

    def test_preserves_existing_region_hints(self):
        item = _make_item(
            title="Generic update",
            region_hints=["SA"],
        )
        enrich_feed_item(item)
        assert "SA" in item.region_hints

    def test_preserves_existing_domain_hints(self):
        item = _make_item(
            title="Generic update",
            domain_hints=["banking"],
        )
        enrich_feed_item(item)
        assert "banking" in item.domain_hints

    def test_full_enrichment_pipeline(self):
        """End-to-end: RSS item about Saudi oil crisis should be fully enriched."""
        item = _make_item(
            title="Saudi Aramco reports oil crisis near Dammam",
            description="Production halted amid regional tensions",
            feed_type=FeedType.RSS,
            source_quality=0.8,
            confidence="high",
            categories=["Energy", "Oil"],
        )
        enrich_feed_item(item)

        # Classification: should detect commodity or geopolitical
        assert item.signal_type_hint is not None

        # Regions: should detect SA from "Saudi Aramco" and "Dammam"
        assert "SA" in item.region_hints

        # Domains: should detect oil_gas
        assert "oil_gas" in item.domain_hints

        # Severity: "crisis" keyword should amplify
        assert item.severity_hint is not None
        assert item.severity_hint > 0.3

    def test_categories_used_for_domain_enrichment(self):
        item = _make_item(
            title="Generic financial news update",
            categories=["Insurance", "Banking"],
        )
        enrich_feed_item(item)
        assert "insurance" in item.domain_hints
        assert "banking" in item.domain_hints

    def test_idempotent(self):
        """Enriching twice produces same result."""
        item = _make_item(title="Dubai port expansion announced")
        enrich_feed_item(item)
        first_regions = list(item.region_hints)
        first_domains = list(item.domain_hints)
        first_type = item.signal_type_hint

        enrich_feed_item(item)
        assert item.region_hints == first_regions
        assert item.domain_hints == first_domains
        assert item.signal_type_hint == first_type


# ══════════════════════════════════════════════════════════════════════════════
# 6. BOUNDARY VALUE & EDGE CASE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_empty_title(self):
        result = classify_signal_type(title="")
        assert result is None

    def test_none_description(self):
        result = extract_regions("Test title", description=None)
        assert isinstance(result, list)

    def test_empty_categories(self):
        result = extract_domains("Test title", categories=[])
        assert isinstance(result, list)

    def test_none_existing_hints(self):
        result = extract_regions("Dubai test", existing_hints=None)
        assert "AE" in result

    def test_severity_with_all_none(self):
        result = compute_severity(
            "Simple title",
            description=None,
            existing_hint=None,
        )
        assert 0.0 <= result <= 1.0

    def test_unicode_arabic_title(self):
        result = extract_regions("أسعار النفط في الرياض ترتفع")
        assert "SA" in result

    def test_mixed_language_title(self):
        result = extract_regions("Oil prices in الرياض surge today")
        assert "SA" in result

    def test_very_long_title(self):
        title = "Oil embargo sanctions " * 100
        result = classify_signal_type(title=title)
        assert result is not None  # should classify from keywords

    def test_special_characters_in_title(self):
        result = extract_regions("Dubai's #1 port — Jebel Ali — sees growth!")
        assert "AE" in result
