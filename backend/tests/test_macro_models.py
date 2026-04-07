"""Macro Intelligence Layer — Pack 1 Model Tests.

Covers:
  1. Valid signal creation (all required and optional fields)
  2. Invalid missing required fields
  3. Invalid enum values
  4. Invalid severity/confidence ranges
  5. Tag normalization and deduplication
  6. Extended Pack 1 fields: signal_type, country_scope, sector_scope, raw_payload
"""

from datetime import datetime, timezone

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
from src.macro.macro_schemas import MacroSignalInput, NormalizedSignal
from src.macro.macro_normalizer import normalize_signal


# ── Helpers ───────────────────────────────────────────────────────────────────

def _minimal_input(**overrides) -> MacroSignalInput:
    """Minimal valid MacroSignalInput."""
    defaults = {
        "title": "Gulf shipping lane disruption detected",
        "source": SignalSource.GEOPOLITICAL,
        "severity_score": 0.55,
        "direction": SignalDirection.NEGATIVE,
        "regions": [GCCRegion.UAE],
    }
    defaults.update(overrides)
    return MacroSignalInput(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VALID SIGNAL CREATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidSignalCreation:
    def test_minimal_input_creates_successfully(self):
        inp = _minimal_input()
        assert inp.title == "Gulf shipping lane disruption detected"
        assert inp.source == SignalSource.GEOPOLITICAL
        assert inp.severity_score == 0.55
        assert inp.direction == SignalDirection.NEGATIVE
        assert inp.regions == [GCCRegion.UAE]

    def test_default_confidence_is_unverified(self):
        inp = _minimal_input()
        assert inp.confidence == SignalConfidence.UNVERIFIED

    def test_default_ttl_is_72h(self):
        inp = _minimal_input()
        assert inp.ttl_hours == 72

    def test_default_tags_is_empty_list(self):
        inp = _minimal_input()
        assert inp.tags == []

    def test_default_impact_domains_empty(self):
        inp = _minimal_input()
        assert inp.impact_domains == []

    def test_full_input_with_all_fields(self):
        inp = _minimal_input(
            description="Detailed description of the disruption event",
            source_uri="https://feeds.example.com/signal/123",
            confidence=SignalConfidence.HIGH,
            impact_domains=[ImpactDomain.OIL_GAS, ImpactDomain.MARITIME],
            event_time=datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc),
            ttl_hours=48,
            tags=["shipping", "GCC", "logistics"],
            external_id="EXT-2026-001",
            signal_type=SignalType.LOGISTICS,
            country_scope=["UAE", "Oman"],
            sector_scope=["oil", "shipping"],
            raw_payload={"source_ref": "Reuters-2026-001", "raw_score": 0.82},
        )
        assert inp.signal_type == SignalType.LOGISTICS
        assert inp.country_scope == ["Oman", "UAE"]  # sorted
        assert inp.sector_scope == ["oil", "shipping"]  # sorted
        assert inp.raw_payload == {"source_ref": "Reuters-2026-001", "raw_score": 0.82}

    def test_multiple_regions_accepted(self):
        inp = _minimal_input(regions=[GCCRegion.UAE, GCCRegion.QATAR, GCCRegion.KUWAIT])
        assert len(inp.regions) == 3

    def test_gcc_wide_region_accepted(self):
        inp = _minimal_input(regions=[GCCRegion.GCC_WIDE])
        assert GCCRegion.GCC_WIDE in inp.regions

    def test_mixed_direction_accepted(self):
        inp = _minimal_input(direction=SignalDirection.MIXED)
        assert inp.direction == SignalDirection.MIXED

    def test_uncertain_direction_low_severity_accepted(self):
        """UNCERTAIN is allowed at low severity (no directional contradiction)."""
        inp = _minimal_input(direction=SignalDirection.UNCERTAIN, severity_score=0.30)
        assert inp.direction == SignalDirection.UNCERTAIN


# ═══════════════════════════════════════════════════════════════════════════════
# 2. INVALID MISSING REQUIRED FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMissingRequiredFields:
    def test_missing_title_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            MacroSignalInput(
                source=SignalSource.MARKET,
                severity_score=0.4,
                direction=SignalDirection.NEGATIVE,
                regions=[GCCRegion.UAE],
            )
        assert "title" in str(exc_info.value).lower()

    def test_missing_source_raises(self):
        with pytest.raises(ValidationError):
            MacroSignalInput(
                title="Missing source field test signal",
                severity_score=0.4,
                direction=SignalDirection.NEGATIVE,
                regions=[GCCRegion.UAE],
            )

    def test_missing_severity_score_raises(self):
        with pytest.raises(ValidationError):
            MacroSignalInput(
                title="Missing severity score test signal",
                source=SignalSource.MARKET,
                direction=SignalDirection.NEGATIVE,
                regions=[GCCRegion.UAE],
            )

    def test_missing_direction_raises(self):
        with pytest.raises(ValidationError):
            MacroSignalInput(
                title="Missing direction field test signal",
                source=SignalSource.MARKET,
                severity_score=0.4,
                regions=[GCCRegion.UAE],
            )

    def test_missing_regions_raises(self):
        with pytest.raises(ValidationError):
            MacroSignalInput(
                title="Missing regions field test signal",
                source=SignalSource.MARKET,
                severity_score=0.4,
                direction=SignalDirection.NEGATIVE,
            )

    def test_empty_regions_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(regions=[])


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INVALID ENUM VALUES
# ═══════════════════════════════════════════════════════════════════════════════

class TestInvalidEnumValues:
    def test_invalid_source_string_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            MacroSignalInput(
                title="Invalid source enum test signal",
                source="unknown_source",  # not in SignalSource
                severity_score=0.4,
                direction=SignalDirection.NEGATIVE,
                regions=[GCCRegion.UAE],
            )
        assert "source" in str(exc_info.value).lower()

    def test_invalid_direction_string_raises(self):
        with pytest.raises(ValidationError):
            MacroSignalInput(
                title="Invalid direction enum test signal",
                source=SignalSource.MARKET,
                severity_score=0.4,
                direction="sideways",  # not in SignalDirection
                regions=[GCCRegion.UAE],
            )

    def test_invalid_confidence_string_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(confidence="maybe")  # not in SignalConfidence

    def test_invalid_signal_type_string_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(signal_type="unknown_type")  # not in SignalType

    def test_invalid_region_string_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(regions=["XX"])  # not in GCCRegion

    def test_valid_signal_type_enum_accepted(self):
        for st in SignalType:
            inp = _minimal_input(signal_type=st)
            assert inp.signal_type == st

    def test_all_signal_types_have_8_members(self):
        assert len(SignalType) == 8
        expected = {
            "geopolitical", "policy", "market", "commodity",
            "regulatory", "logistics", "sentiment", "systemic",
        }
        assert {t.value for t in SignalType} == expected

    def test_direction_has_mixed_and_uncertain(self):
        """Pack 1 requires mixed and uncertain in SignalDirection."""
        values = {d.value for d in SignalDirection}
        assert "mixed" in values
        assert "uncertain" in values


# ═══════════════════════════════════════════════════════════════════════════════
# 4. INVALID SEVERITY / CONFIDENCE RANGES
# ═══════════════════════════════════════════════════════════════════════════════

class TestInvalidRanges:
    def test_severity_above_1_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(severity_score=1.01)

    def test_severity_below_0_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(severity_score=-0.01)

    def test_severity_exactly_0_accepted(self):
        inp = _minimal_input(severity_score=0.0)
        assert inp.severity_score == 0.0

    def test_severity_exactly_1_accepted(self):
        inp = _minimal_input(severity_score=1.0)
        assert inp.severity_score == 1.0

    def test_ttl_zero_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(ttl_hours=0)

    def test_ttl_too_large_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(ttl_hours=8761)

    def test_ttl_at_min_accepted(self):
        inp = _minimal_input(ttl_hours=1)
        assert inp.ttl_hours == 1

    def test_ttl_at_max_accepted(self):
        inp = _minimal_input(ttl_hours=8760)
        assert inp.ttl_hours == 8760

    def test_title_too_short_raises(self):
        with pytest.raises(ValidationError):
            _minimal_input(title="Hi")

    def test_title_at_minimum_accepted(self):
        inp = _minimal_input(title="Short")
        assert inp.title == "Short"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TAG NORMALIZATION AND DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestTagNormalization:
    def test_tags_lowercased(self):
        inp = _minimal_input(tags=["OIL", "GAS"])
        assert inp.tags == ["oil", "gas"]

    def test_tags_stripped(self):
        inp = _minimal_input(tags=["  oil  ", " gas "])
        assert inp.tags == ["oil", "gas"]

    def test_tags_deduplicated(self):
        inp = _minimal_input(tags=["oil", "Oil", "OIL", "gas"])
        assert inp.tags == ["oil", "gas"]

    def test_empty_tags_dropped(self):
        inp = _minimal_input(tags=["oil", "", "  ", "gas"])
        assert "" not in inp.tags
        assert "  " not in inp.tags
        assert "oil" in inp.tags
        assert "gas" in inp.tags

    def test_mixed_case_dedup_preserves_first(self):
        inp = _minimal_input(tags=["Hormuz", "hormuz", "HORMUZ", "maritime"])
        assert inp.tags == ["hormuz", "maritime"]

    def test_empty_tags_list_accepted(self):
        inp = _minimal_input(tags=[])
        assert inp.tags == []

    def test_tags_order_preserved_after_dedup(self):
        inp = _minimal_input(tags=["alpha", "beta", "gamma", "Alpha"])
        assert inp.tags == ["alpha", "beta", "gamma"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EXTENDED PACK 1 FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtendedFields:
    def test_signal_type_defaults_to_none(self):
        inp = _minimal_input()
        assert inp.signal_type is None

    def test_country_scope_defaults_to_empty(self):
        inp = _minimal_input()
        assert inp.country_scope == []

    def test_sector_scope_defaults_to_empty(self):
        inp = _minimal_input()
        assert inp.sector_scope == []

    def test_raw_payload_defaults_to_none(self):
        inp = _minimal_input()
        assert inp.raw_payload is None

    def test_raw_payload_dict_preserved(self):
        payload = {"key": "value", "nested": {"a": 1}}
        inp = _minimal_input(raw_payload=payload)
        assert inp.raw_payload == payload

    def test_signal_type_policy_accepted(self):
        inp = _minimal_input(signal_type=SignalType.POLICY)
        assert inp.signal_type == SignalType.POLICY

    def test_signal_type_systemic_accepted(self):
        inp = _minimal_input(signal_type=SignalType.SYSTEMIC)
        assert inp.signal_type == SignalType.SYSTEMIC

    def test_normalized_signal_carries_extended_fields(self):
        inp = _minimal_input(
            signal_type=SignalType.COMMODITY,
            country_scope=["Kuwait", "Iraq"],
            sector_scope=["oil", "petrochemicals"],
            raw_payload={"price_change_pct": -12.5},
        )
        normalized = normalize_signal(inp)
        assert normalized.signal_type == SignalType.COMMODITY
        assert normalized.country_scope == ["Iraq", "Kuwait"]  # sorted
        assert normalized.sector_scope == ["oil", "petrochemicals"]
        assert normalized.raw_payload == {"price_change_pct": -12.5}

    def test_normalized_signal_extended_fields_default_to_none_empty(self):
        inp = _minimal_input()
        normalized = normalize_signal(inp)
        assert normalized.signal_type is None
        assert normalized.country_scope == []
        assert normalized.sector_scope == []
        assert normalized.raw_payload is None
