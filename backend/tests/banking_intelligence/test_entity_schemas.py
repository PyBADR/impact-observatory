"""
Tests — Entity Registry Schema Validation
==========================================
Validates all 7 entity types, dedup key computation,
field constraints, and rejection of invalid data.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.banking_intelligence.schemas.entities import (
    Country,
    Authority,
    Bank,
    Fintech,
    PaymentRail,
    ScenarioTrigger,
    DecisionPlaybook,
    PlaybookStep,
    SourceMetadata,
    ValidationStatus,
    GCCCountryCode,
    BankTier,
    ENTITY_TYPE_MAP,
)


# ─── Fixtures ───────────────────────────────────────────────────────────────

def _source() -> dict:
    return {
        "source_system": "test_suite",
        "extracted_by": "pytest",
    }


# ─── Country Tests ──────────────────────────────────────────────────────────

class TestCountry:
    def test_valid_country(self):
        c = Country(
            canonical_id="country:sa",
            name_en="Saudi Arabia",
            iso_alpha2=GCCCountryCode.SA,
            iso_alpha3="SAU",
            currency_code="SAR",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.95,
        )
        assert c.dedup_key == "country:SA"
        assert c.confidence_level.value == "DEFINITIVE"

    def test_country_rejects_invalid_iso(self):
        with pytest.raises(ValidationError):
            Country(
                canonical_id="country:xx",
                name_en="Fake",
                iso_alpha2="XX",  # not in GCCCountryCode
                iso_alpha3="XXX",
                currency_code="XXX",
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )

    def test_country_rejects_bad_id_pattern(self):
        with pytest.raises(ValidationError):
            Country(
                canonical_id="COUNTRY:SA",  # uppercase not allowed
                name_en="Saudi",
                iso_alpha2=GCCCountryCode.SA,
                iso_alpha3="SAU",
                currency_code="SAR",
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )


# ─── Authority Tests ────────────────────────────────────────────────────────

class TestAuthority:
    def test_valid_authority(self):
        a = Authority(
            canonical_id="authority:sa_sama",
            name_en="SAMA",
            authority_type="central_bank",
            country_code=GCCCountryCode.SA,
            jurisdiction_scope="national",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.99,
        )
        assert a.dedup_key.startswith("authority:")
        assert len(a.dedup_key) > 10

    def test_dedup_key_deterministic(self):
        """Same inputs produce same dedup key."""
        kwargs = dict(
            canonical_id="authority:sa_sama",
            name_en="SAMA",
            authority_type="central_bank",
            country_code=GCCCountryCode.SA,
            jurisdiction_scope="national",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.99,
        )
        a1 = Authority(**kwargs)
        a2 = Authority(**kwargs)
        assert a1.dedup_key == a2.dedup_key


# ─── Bank Tests ─────────────────────────────────────────────────────────────

class TestBank:
    def test_valid_bank_with_swift(self):
        b = Bank(
            canonical_id="bank:sa_snb",
            name_en="SNB",
            country_code=GCCCountryCode.SA,
            swift_code="ncbksaje",  # should normalize to uppercase
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.90,
        )
        assert b.swift_code == "NCBKSAJE"
        assert b.dedup_key.startswith("bank:")

    def test_bank_dedup_by_swift(self):
        kwargs = dict(
            canonical_id="bank:sa_snb",
            name_en="SNB",
            country_code=GCCCountryCode.SA,
            swift_code="NCBKSAJE",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.90,
        )
        b1 = Bank(**kwargs)
        b2 = Bank(**kwargs)
        assert b1.dedup_key == b2.dedup_key

    def test_bank_rejects_bad_swift(self):
        with pytest.raises(ValidationError):
            Bank(
                canonical_id="bank:sa_bad",
                name_en="Bad",
                country_code=GCCCountryCode.SA,
                swift_code="XY",  # too short
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )

    def test_bank_confidence_ranges(self):
        b = Bank(
            canonical_id="bank:sa_low",
            name_en="LowConf",
            country_code=GCCCountryCode.SA,
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.15,
        )
        assert b.confidence_level.value == "SPECULATIVE"

    def test_bank_rejects_negative_assets(self):
        with pytest.raises(ValidationError):
            Bank(
                canonical_id="bank:sa_neg",
                name_en="Negative",
                country_code=GCCCountryCode.SA,
                total_assets_usd_millions=-100,
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )


# ─── Fintech Tests ──────────────────────────────────────────────────────────

class TestFintech:
    def test_valid_fintech(self):
        f = Fintech(
            canonical_id="fintech:sa_stcpay",
            name_en="stc pay",
            country_code=GCCCountryCode.SA,
            category="payments",
            license_type="emi",
            license_number="SAMA_EMI_001",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.88,
        )
        assert f.dedup_key.startswith("fintech:")

    def test_fintech_dedup_without_license(self):
        f = Fintech(
            canonical_id="fintech:sa_test",
            name_en="TestFin",
            country_code=GCCCountryCode.SA,
            category="lending",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.5,
        )
        assert "fintech:" in f.dedup_key


# ─── PaymentRail Tests ─────────────────────────────────────────────────────

class TestPaymentRail:
    def test_valid_rail(self):
        r = PaymentRail(
            canonical_id="rail:sa_sarie",
            name_en="SARIE",
            rail_type="rtgs",
            operator_country=GCCCountryCode.SA,
            system_name="SARIE",
            settlement_currency="SAR",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.97,
        )
        assert r.dedup_key.startswith("rail:")

    def test_rail_rejects_bad_currency(self):
        with pytest.raises(ValidationError):
            PaymentRail(
                canonical_id="rail:sa_bad",
                name_en="Bad",
                rail_type="rtgs",
                operator_country=GCCCountryCode.SA,
                system_name="BAD",
                settlement_currency="TOOLONG",
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )


# ─── ScenarioTrigger Tests ─────────────────────────────────────────────────

class TestScenarioTrigger:
    def test_valid_trigger(self):
        t = ScenarioTrigger(
            canonical_id="trigger:hormuz_oil_price",
            name_en="Hormuz Oil Price Trigger",
            scenario_id="hormuz_chokepoint_disruption",
            trigger_type="price_threshold",
            trigger_source="bloomberg",
            threshold_condition="brent_crude_usd > 120",
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.80,
        )
        assert t.dedup_key.startswith("trigger:")


# ─── DecisionPlaybook Tests ────────────────────────────────────────────────

class TestDecisionPlaybook:
    def test_valid_playbook(self):
        p = DecisionPlaybook(
            canonical_id="playbook:hormuz_liquidity",
            name_en="Hormuz Liquidity Response",
            playbook_type="liquidity_management",
            scenario_id="hormuz_chokepoint_disruption",
            legal_authority_basis="SAMA_BCR_Art_42",
            primary_owner_id="authority:sa_sama",
            max_response_hours=24.0,
            steps=[
                PlaybookStep(
                    step_number=1,
                    action="Activate emergency repo facility",
                    owner_entity_id="authority:sa_sama",
                    time_window_hours=2.0,
                ),
                PlaybookStep(
                    step_number=2,
                    action="Reduce reserve requirement by 50bps",
                    owner_entity_id="authority:sa_sama",
                    time_window_hours=4.0,
                    requires_approval=True,
                    approval_authority_id="authority:sa_sama",
                ),
            ],
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.85,
        )
        assert p.dedup_key.startswith("playbook:")
        assert len(p.steps) == 2

    def test_playbook_rejects_unordered_steps(self):
        with pytest.raises(ValidationError):
            DecisionPlaybook(
                canonical_id="playbook:bad",
                name_en="Bad",
                playbook_type="crisis_response",
                scenario_id="test",
                legal_authority_basis="TEST",
                primary_owner_id="authority:sa_sama",
                max_response_hours=24.0,
                steps=[
                    PlaybookStep(step_number=2, action="Second", owner_entity_id="a:b"),
                    PlaybookStep(step_number=1, action="First", owner_entity_id="a:b"),
                ],
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )

    def test_playbook_rejects_duplicate_step_numbers(self):
        with pytest.raises(ValidationError):
            DecisionPlaybook(
                canonical_id="playbook:dup",
                name_en="Dup",
                playbook_type="crisis_response",
                scenario_id="test",
                legal_authority_basis="TEST",
                primary_owner_id="authority:sa_sama",
                max_response_hours=24.0,
                steps=[
                    PlaybookStep(step_number=1, action="A", owner_entity_id="a:b"),
                    PlaybookStep(step_number=1, action="B", owner_entity_id="a:b"),
                ],
                source_metadata=SourceMetadata(**_source()),
                source_confidence=0.5,
            )


# ─── Entity Type Registry ──────────────────────────────────────────────────

class TestEntityTypeMap:
    def test_all_types_present(self):
        expected = {"country", "authority", "bank", "fintech", "payment_rail", "scenario_trigger", "decision_playbook"}
        assert set(ENTITY_TYPE_MAP.keys()) == expected

    def test_confidence_boundary(self):
        """Test confidence level boundaries."""
        b = Bank(
            canonical_id="bank:sa_edge",
            name_en="Edge",
            country_code=GCCCountryCode.SA,
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.90,
        )
        assert b.confidence_level.value == "DEFINITIVE"

        b2 = Bank(
            canonical_id="bank:sa_edge2",
            name_en="Edge2",
            country_code=GCCCountryCode.SA,
            source_metadata=SourceMetadata(**_source()),
            source_confidence=0.89,
        )
        assert b2.confidence_level.value == "HIGH"
