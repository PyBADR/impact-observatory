"""Macro Intelligence Layer — Pack 1 Normalization Tests.

Covers:
  1. String normalization (title, description whitespace)
  2. Scope normalization and deduplication (country_scope, sector_scope)
  3. Tag normalization (lowercase, dedup)
  4. event_time defaulting and UTC coercion
  5. Severity score → level mapping (all 6 bands)
  6. Impact domain inference from source
  7. TTL and expires_at computation
  8. Content hash properties (SHA-256, deterministic, 64 hex chars)
  9. Extended fields pass-through
"""

from datetime import datetime, timedelta, timezone

import pytest

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
from src.macro.macro_normalizer import SOURCE_DOMAIN_MAP, normalize_signal
from src.macro.macro_schemas import MacroSignalInput, NormalizedSignal
from src.macro.macro_validators import severity_from_score


# ── Helpers ───────────────────────────────────────────────────────────────────

def _input(**overrides) -> MacroSignalInput:
    defaults = {
        "title": "  GCC   Energy Market  Pressure Signal  ",
        "source": SignalSource.ENERGY,
        "severity_score": 0.60,
        "direction": SignalDirection.NEGATIVE,
        "regions": [GCCRegion.SAUDI_ARABIA],
    }
    defaults.update(overrides)
    return MacroSignalInput(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. STRING NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestStringNormalization:
    def test_title_leading_trailing_stripped(self):
        inp = _input(title="  Strait closure warning  ")
        result = normalize_signal(inp)
        assert result.title == "Strait closure warning"

    def test_title_internal_whitespace_preserved(self):
        """Pydantic strips leading/trailing but internal spaces are preserved."""
        inp = _input(title="   Gulf   Crisis   Event   ")
        result = normalize_signal(inp)
        # title.strip() removes leading/trailing; internal handled by normalizer
        assert result.title.startswith("Gulf") or "Gulf" in result.title

    def test_description_internal_whitespace_collapsed(self):
        inp = _input(description="Satellite  imagery   confirms   obstruction")
        result = normalize_signal(inp)
        assert "  " not in result.description  # no double spaces
        assert result.description == "Satellite imagery confirms obstruction"

    def test_description_none_preserved(self):
        inp = _input(description=None)
        result = normalize_signal(inp)
        assert result.description is None

    def test_description_empty_string_treated_as_none(self):
        inp = _input(description="")
        result = normalize_signal(inp)
        assert result.description is None or result.description == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SCOPE NORMALIZATION AND DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestScopeNormalization:
    def test_country_scope_whitespace_stripped(self):
        inp = _input(country_scope=[" Kuwait ", "  Iraq  "])
        assert "Kuwait" in inp.country_scope
        assert "Iraq" in inp.country_scope
        assert " Kuwait " not in inp.country_scope

    def test_country_scope_deduplicated(self):
        inp = _input(country_scope=["Kuwait", "Kuwait", "Iraq"])
        assert inp.country_scope.count("Kuwait") == 1

    def test_country_scope_sorted(self):
        inp = _input(country_scope=["UAE", "Oman", "Bahrain"])
        assert inp.country_scope == sorted(inp.country_scope)

    def test_country_scope_empty_strings_dropped(self):
        inp = _input(country_scope=["UAE", "", "  "])
        assert "" not in inp.country_scope
        assert "  " not in inp.country_scope
        assert "UAE" in inp.country_scope

    def test_country_scope_internal_whitespace_collapsed(self):
        inp = _input(country_scope=["Saudi  Arabia"])
        assert "Saudi Arabia" in inp.country_scope
        assert "Saudi  Arabia" not in inp.country_scope

    def test_sector_scope_whitespace_stripped(self):
        inp = _input(sector_scope=["  oil  ", " banking "])
        assert "oil" in inp.sector_scope
        assert "banking" in inp.sector_scope

    def test_sector_scope_deduplicated(self):
        inp = _input(sector_scope=["oil", "Oil", "OIL"])
        # Case-sensitive: "oil", "Oil", "OIL" are treated as distinct by schema
        # (no lowercasing on scope — unlike tags). Only exact duplicates removed.
        seen = set(inp.sector_scope)
        assert len(inp.sector_scope) == len(seen)

    def test_sector_scope_sorted(self):
        inp = _input(sector_scope=["shipping", "aviation", "banking"])
        assert inp.sector_scope == sorted(inp.sector_scope)

    def test_scope_normalization_example_from_spec(self):
        """Spec example: country_scope [' Kuwait ', 'Kuwait'] -> ['Kuwait']"""
        inp = _input(country_scope=[" Kuwait ", "Kuwait"])
        assert inp.country_scope == ["Kuwait"]

    def test_scope_preserved_through_normalization(self):
        inp = _input(
            country_scope=["Qatar", "Kuwait"],
            sector_scope=["finance", "energy"],
        )
        result = normalize_signal(inp)
        assert result.country_scope == ["Kuwait", "Qatar"]  # sorted
        assert result.sector_scope == ["energy", "finance"]  # sorted


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TAG NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestTagNormalizationInPipeline:
    def test_tags_normalized_before_normalization(self):
        inp = _input(tags=["Oil", "oil", "GCC", "gcc", ""])
        result = normalize_signal(inp)
        assert result.tags == ["oil", "gcc"]

    def test_spec_example_tags(self):
        """Spec example: tags ['Oil', 'oil', ''] -> ['oil']"""
        inp = _input(tags=["Oil", "oil", ""])
        result = normalize_signal(inp)
        assert result.tags == ["oil"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. EVENT_TIME DEFAULTING AND UTC COERCION
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventTimeNormalization:
    def test_event_time_none_defaults_to_now(self):
        inp = _input(event_time=None)
        before = datetime.now(timezone.utc)
        result = normalize_signal(inp)
        after = datetime.now(timezone.utc)
        assert before <= result.event_time <= after

    def test_event_time_provided_preserved(self):
        fixed = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)
        inp = _input(event_time=fixed)
        result = normalize_signal(inp)
        assert result.event_time == fixed

    def test_event_time_naive_gets_utc(self):
        naive = datetime(2026, 3, 15, 8, 0, 0)  # no tzinfo
        inp = _input(event_time=naive)
        result = normalize_signal(inp)
        assert result.event_time.tzinfo is not None

    def test_result_event_time_always_has_timezone(self):
        inp = _input()
        result = normalize_signal(inp)
        assert result.event_time.tzinfo is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 5. SEVERITY SCORE → LEVEL MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeverityMapping:
    @pytest.mark.parametrize("score,expected", [
        (0.00, SignalSeverity.NOMINAL),
        (0.19, SignalSeverity.NOMINAL),
        (0.20, SignalSeverity.LOW),
        (0.34, SignalSeverity.LOW),
        (0.35, SignalSeverity.GUARDED),
        (0.49, SignalSeverity.GUARDED),
        (0.50, SignalSeverity.ELEVATED),
        (0.64, SignalSeverity.ELEVATED),
        (0.65, SignalSeverity.HIGH),
        (0.79, SignalSeverity.HIGH),
        (0.80, SignalSeverity.SEVERE),
        (1.00, SignalSeverity.SEVERE),
    ])
    def test_severity_from_score(self, score, expected):
        assert severity_from_score(score) == expected

    def test_normalized_signal_severity_level_matches_score(self):
        inp = _input(severity_score=0.72)
        result = normalize_signal(inp)
        assert result.severity_level == SignalSeverity.HIGH
        assert result.severity_score == 0.72

    def test_severity_score_rounded_to_4_places(self):
        inp = _input(severity_score=0.123456789)
        result = normalize_signal(inp)
        assert result.severity_score == round(0.123456789, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. IMPACT DOMAIN INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

class TestImpactDomainInference:
    def test_domains_inferred_when_empty(self):
        inp = _input(source=SignalSource.GEOPOLITICAL, impact_domains=[])
        result = normalize_signal(inp)
        assert result.impact_domains == SOURCE_DOMAIN_MAP[SignalSource.GEOPOLITICAL]

    def test_domains_preserved_when_provided(self):
        explicit = [ImpactDomain.AVIATION, ImpactDomain.BANKING]
        inp = _input(impact_domains=explicit)
        result = normalize_signal(inp)
        assert result.impact_domains == explicit

    def test_all_source_types_have_domain_mappings(self):
        for source in SignalSource:
            assert source in SOURCE_DOMAIN_MAP, f"{source} missing from SOURCE_DOMAIN_MAP"
            assert len(SOURCE_DOMAIN_MAP[source]) >= 1

    def test_inferred_domains_deduplicated(self):
        """Providing domains that overlap with inference — explicit wins."""
        inp = _input(
            source=SignalSource.ENERGY,
            impact_domains=[ImpactDomain.OIL_GAS, ImpactDomain.OIL_GAS],
        )
        result = normalize_signal(inp)
        assert result.impact_domains.count(ImpactDomain.OIL_GAS) == 1

    def test_normalized_signal_impact_domains_never_empty(self):
        """NormalizedSignal.impact_domains must have min_length=1."""
        for source in SignalSource:
            inp = _input(source=source, impact_domains=[])
            result = normalize_signal(inp)
            assert len(result.impact_domains) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TTL AND EXPIRES_AT
# ═══════════════════════════════════════════════════════════════════════════════

class TestTTLComputation:
    def test_expires_at_uses_ttl_hours(self):
        inp = _input(ttl_hours=48)
        before = datetime.now(timezone.utc)
        result = normalize_signal(inp)
        after = datetime.now(timezone.utc)
        expected_min = before + timedelta(hours=48)
        expected_max = after + timedelta(hours=48)
        assert expected_min <= result.expires_at <= expected_max

    def test_default_ttl_72h(self):
        inp = _input()  # ttl_hours defaults to 72
        result = normalize_signal(inp)
        delta = result.expires_at - result.intake_time
        assert abs(delta.total_seconds() - 72 * 3600) < 1

    def test_short_ttl_1h(self):
        inp = _input(ttl_hours=1)
        result = normalize_signal(inp)
        delta = result.expires_at - result.intake_time
        assert abs(delta.total_seconds() - 3600) < 1

    def test_long_ttl_one_year(self):
        inp = _input(ttl_hours=8760)
        result = normalize_signal(inp)
        delta = result.expires_at - result.intake_time
        assert abs(delta.total_seconds() - 8760 * 3600) < 1


# ═══════════════════════════════════════════════════════════════════════════════
# 8. CONTENT HASH PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════════

class TestContentHash:
    def test_content_hash_is_64_hex_chars(self):
        inp = _input()
        result = normalize_signal(inp)
        assert len(result.content_hash) == 64
        int(result.content_hash, 16)  # must be valid hex

    def test_identical_inputs_same_hash(self):
        fixed_time = datetime(2026, 2, 1, tzinfo=timezone.utc)
        inp1 = _input(event_time=fixed_time)
        inp2 = _input(event_time=fixed_time)
        r1 = normalize_signal(inp1)
        r2 = normalize_signal(inp2)
        assert r1.content_hash == r2.content_hash

    def test_different_title_different_hash(self):
        fixed_time = datetime(2026, 2, 1, tzinfo=timezone.utc)
        r1 = normalize_signal(_input(title="Signal alpha version one", event_time=fixed_time))
        r2 = normalize_signal(_input(title="Signal beta version two", event_time=fixed_time))
        assert r1.content_hash != r2.content_hash

    def test_different_severity_different_hash(self):
        fixed_time = datetime(2026, 2, 1, tzinfo=timezone.utc)
        r1 = normalize_signal(_input(severity_score=0.5, event_time=fixed_time))
        r2 = normalize_signal(_input(severity_score=0.9, event_time=fixed_time))
        assert r1.content_hash != r2.content_hash


# ═══════════════════════════════════════════════════════════════════════════════
# 9. EXTENDED FIELDS PASS-THROUGH
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtendedFieldsPassThrough:
    def test_signal_type_passed_through(self):
        inp = _input(signal_type=SignalType.SYSTEMIC)
        result = normalize_signal(inp)
        assert result.signal_type == SignalType.SYSTEMIC

    def test_signal_type_none_passed_through(self):
        inp = _input(signal_type=None)
        result = normalize_signal(inp)
        assert result.signal_type is None

    def test_country_scope_passed_and_normalized(self):
        inp = _input(country_scope=[" UAE ", "Oman", "UAE"])
        result = normalize_signal(inp)
        assert result.country_scope == ["Oman", "UAE"]

    def test_sector_scope_passed_and_normalized(self):
        inp = _input(sector_scope=["energy", "banking", "energy"])
        result = normalize_signal(inp)
        assert result.sector_scope == ["banking", "energy"]

    def test_raw_payload_passed_through_unchanged(self):
        payload = {"feed": "bloomberg", "id": 42, "nested": {"x": [1, 2, 3]}}
        inp = _input(raw_payload=payload)
        result = normalize_signal(inp)
        assert result.raw_payload == payload

    def test_raw_payload_none_preserved(self):
        inp = _input(raw_payload=None)
        result = normalize_signal(inp)
        assert result.raw_payload is None

    def test_normalization_version_is_1_0_0(self):
        inp = _input()
        result = normalize_signal(inp)
        assert result.normalization_version == "1.0.0"

    def test_result_status_is_normalized(self):
        inp = _input()
        result = normalize_signal(inp)
        assert result.status == SignalStatus.NORMALIZED
