"""Signal Intelligence Layer — Region Engine.

Comprehensive GCC region detection from free-form text hints.

Extends the basic keyword lookup in normalizer.py with:
  - Full country name coverage (official + common + Arabic transliteration)
  - Major cities and landmarks mapped to GCC members
  - Regional groupings (Arabian Gulf, Gulf region, GCC, MENA)
  - Organizations and landmarks that imply a region (Aramco → SA, DP World → UAE)
  - Per-match confidence based on specificity of the keyword
  - Coverage score (how many of the 6 GCC members are represented)

Design rules:
  - Deterministic: same hints → same RegionMapping
  - No external state, no ML, no fuzzy matching
  - All text lowercased before matching
  - Longer/more specific patterns take precedence in confidence scoring
  - Never raises; returns empty RegionMapping on failure

Public API:
  resolve_regions(hints: list[str]) -> RegionMapping
  detect_gcc(hints: list[str]) -> bool
"""

from __future__ import annotations

import logging
from typing import NamedTuple

from src.macro.macro_enums import GCCRegion
from src.signals.types import RegionMapping, RegionMatch

logger = logging.getLogger("signals.region_engine")


# ── Region Entry ──────────────────────────────────────────────────────────────

class _RegionEntry(NamedTuple):
    """A single keyword → region mapping with confidence."""
    keyword: str
    region: GCCRegion
    confidence: float  # 0.0–1.0


# ── Comprehensive GCC Keyword Table ───────────────────────────────────────────
# Entries with longer/more specific keywords are listed first.
# The engine scans ALL entries (not just first match) so all matches accumulate.
# Confidence reflects keyword specificity:
#   1.0 = exact official name / ISO code
#   0.9 = common well-known alias
#   0.8 = major city / capital
#   0.7 = secondary city / region
#   0.6 = organization / landmark implying region
#   0.5 = broad regional term (gulf, gcc-wide)

_REGION_TABLE: list[_RegionEntry] = [
    # ── GCC-Wide ──────────────────────────────────────────────────────────────
    _RegionEntry("gulf cooperation council", GCCRegion.GCC_WIDE, 1.0),
    _RegionEntry("gcc",                      GCCRegion.GCC_WIDE, 0.9),
    _RegionEntry("gulf states",              GCCRegion.GCC_WIDE, 0.8),
    _RegionEntry("gulf region",              GCCRegion.GCC_WIDE, 0.8),
    _RegionEntry("arabian gulf",             GCCRegion.GCC_WIDE, 0.7),
    _RegionEntry("persian gulf",             GCCRegion.GCC_WIDE, 0.7),
    _RegionEntry("gulf",                     GCCRegion.GCC_WIDE, 0.5),
    _RegionEntry("mena",                     GCCRegion.GCC_WIDE, 0.5),
    _RegionEntry("middle east",              GCCRegion.GCC_WIDE, 0.4),

    # ── Saudi Arabia ──────────────────────────────────────────────────────────
    _RegionEntry("kingdom of saudi arabia",  GCCRegion.SAUDI_ARABIA, 1.0),
    _RegionEntry("saudi arabia",             GCCRegion.SAUDI_ARABIA, 1.0),
    _RegionEntry("saudi",                    GCCRegion.SAUDI_ARABIA, 0.9),
    _RegionEntry("ksa",                      GCCRegion.SAUDI_ARABIA, 0.9),
    _RegionEntry("riyadh",                   GCCRegion.SAUDI_ARABIA, 0.9),
    _RegionEntry("jeddah",                   GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("mecca",                    GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("medina",                   GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("dammam",                   GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("dhahran",                  GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("jubail",                   GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("yanbu",                    GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("abha",                     GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("tabuk",                    GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("neom",                     GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("vision 2030",              GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("aramco",                   GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("saudi aramco",             GCCRegion.SAUDI_ARABIA, 0.8),
    _RegionEntry("sabic",                    GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("sama",                     GCCRegion.SAUDI_ARABIA, 0.6),  # central bank
    _RegionEntry("al-ahsa",                  GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("qatif",                    GCCRegion.SAUDI_ARABIA, 0.7),
    _RegionEntry("hejaz",                    GCCRegion.SAUDI_ARABIA, 0.6),
    _RegionEntry("najd",                     GCCRegion.SAUDI_ARABIA, 0.6),

    # ── UAE ───────────────────────────────────────────────────────────────────
    _RegionEntry("united arab emirates",     GCCRegion.UAE, 1.0),
    _RegionEntry("uae",                      GCCRegion.UAE, 1.0),
    _RegionEntry("abu dhabi",                GCCRegion.UAE, 0.9),
    _RegionEntry("dubai",                    GCCRegion.UAE, 0.9),
    _RegionEntry("sharjah",                  GCCRegion.UAE, 0.8),
    _RegionEntry("ajman",                    GCCRegion.UAE, 0.8),
    _RegionEntry("fujairah",                 GCCRegion.UAE, 0.8),
    _RegionEntry("ras al khaimah",           GCCRegion.UAE, 0.8),
    _RegionEntry("umm al quwain",            GCCRegion.UAE, 0.8),
    _RegionEntry("adnoc",                    GCCRegion.UAE, 0.7),  # Abu Dhabi NOC
    _RegionEntry("dp world",                 GCCRegion.UAE, 0.7),
    _RegionEntry("etisalat",                 GCCRegion.UAE, 0.6),
    _RegionEntry("du telecom",               GCCRegion.UAE, 0.6),
    _RegionEntry("difc",                     GCCRegion.UAE, 0.7),  # Dubai Int'l Financial Centre
    _RegionEntry("adx",                      GCCRegion.UAE, 0.6),  # Abu Dhabi Exchange
    _RegionEntry("dfm",                      GCCRegion.UAE, 0.6),  # Dubai Financial Market
    _RegionEntry("jebel ali",                GCCRegion.UAE, 0.7),
    _RegionEntry("masdar",                   GCCRegion.UAE, 0.6),
    _RegionEntry("mubadala",                 GCCRegion.UAE, 0.7),
    _RegionEntry("emaar",                    GCCRegion.UAE, 0.6),

    # ── Qatar ─────────────────────────────────────────────────────────────────
    _RegionEntry("state of qatar",           GCCRegion.QATAR, 1.0),
    _RegionEntry("qatar",                    GCCRegion.QATAR, 1.0),
    _RegionEntry("doha",                     GCCRegion.QATAR, 0.9),
    _RegionEntry("lusail",                   GCCRegion.QATAR, 0.7),
    _RegionEntry("qatargas",                 GCCRegion.QATAR, 0.7),
    _RegionEntry("rasgas",                   GCCRegion.QATAR, 0.7),
    _RegionEntry("qatarenergy",              GCCRegion.QATAR, 0.8),
    _RegionEntry("qatar energy",             GCCRegion.QATAR, 0.8),
    _RegionEntry("qnb",                      GCCRegion.QATAR, 0.7),  # Qatar National Bank
    _RegionEntry("qcb",                      GCCRegion.QATAR, 0.6),  # Qatar Central Bank
    _RegionEntry("ras laffan",               GCCRegion.QATAR, 0.8),
    _RegionEntry("qatar airways",            GCCRegion.QATAR, 0.7),
    _RegionEntry("mesaieed",                 GCCRegion.QATAR, 0.7),
    _RegionEntry("dukhan",                   GCCRegion.QATAR, 0.7),

    # ── Kuwait ────────────────────────────────────────────────────────────────
    _RegionEntry("state of kuwait",          GCCRegion.KUWAIT, 1.0),
    _RegionEntry("kuwait",                   GCCRegion.KUWAIT, 1.0),
    _RegionEntry("kuwait city",              GCCRegion.KUWAIT, 0.9),
    _RegionEntry("hawalli",                  GCCRegion.KUWAIT, 0.7),
    _RegionEntry("ahmadi",                   GCCRegion.KUWAIT, 0.7),
    _RegionEntry("salmiya",                  GCCRegion.KUWAIT, 0.7),
    _RegionEntry("knpc",                     GCCRegion.KUWAIT, 0.7),  # Kuwait National Petroleum
    _RegionEntry("kpc",                      GCCRegion.KUWAIT, 0.6),  # Kuwait Petroleum
    _RegionEntry("kfh",                      GCCRegion.KUWAIT, 0.6),  # Kuwait Finance House
    _RegionEntry("cbk",                      GCCRegion.KUWAIT, 0.6),  # Central Bank of Kuwait
    _RegionEntry("burgan",                   GCCRegion.KUWAIT, 0.7),  # Burgan oil field
    _RegionEntry("jahra",                    GCCRegion.KUWAIT, 0.7),

    # ── Bahrain ───────────────────────────────────────────────────────────────
    _RegionEntry("kingdom of bahrain",       GCCRegion.BAHRAIN, 1.0),
    _RegionEntry("bahrain",                  GCCRegion.BAHRAIN, 1.0),
    _RegionEntry("manama",                   GCCRegion.BAHRAIN, 0.9),
    _RegionEntry("riffa",                    GCCRegion.BAHRAIN, 0.7),
    _RegionEntry("muharraq",                 GCCRegion.BAHRAIN, 0.7),
    _RegionEntry("bapco",                    GCCRegion.BAHRAIN, 0.7),  # Bahrain Petroleum
    _RegionEntry("alba",                     GCCRegion.BAHRAIN, 0.7),  # Aluminium Bahrain
    _RegionEntry("cbb",                      GCCRegion.BAHRAIN, 0.6),  # Central Bank of Bahrain
    _RegionEntry("bahrain financial harbour", GCCRegion.BAHRAIN, 0.7),
    _RegionEntry("gulf international bank",  GCCRegion.BAHRAIN, 0.6),
    _RegionEntry("gib",                      GCCRegion.BAHRAIN, 0.5),

    # ── Oman ──────────────────────────────────────────────────────────────────
    _RegionEntry("sultanate of oman",        GCCRegion.OMAN, 1.0),
    _RegionEntry("oman",                     GCCRegion.OMAN, 1.0),
    _RegionEntry("muscat",                   GCCRegion.OMAN, 0.9),
    _RegionEntry("salalah",                  GCCRegion.OMAN, 0.8),
    _RegionEntry("sohar",                    GCCRegion.OMAN, 0.8),
    _RegionEntry("duqm",                     GCCRegion.OMAN, 0.8),
    _RegionEntry("nizwa",                    GCCRegion.OMAN, 0.7),
    _RegionEntry("sur",                      GCCRegion.OMAN, 0.6),
    _RegionEntry("pdo",                      GCCRegion.OMAN, 0.7),  # Petroleum Development Oman
    _RegionEntry("omantel",                  GCCRegion.OMAN, 0.6),
    _RegionEntry("bank muscat",              GCCRegion.OMAN, 0.7),
    _RegionEntry("cbo",                      GCCRegion.OMAN, 0.6),  # Central Bank of Oman
    _RegionEntry("strait of hormuz",         GCCRegion.OMAN, 0.7),
    _RegionEntry("hormuz",                   GCCRegion.OMAN, 0.7),
]

# Pre-sort by keyword length descending so longer (more specific) keywords
# are checked first — improves match accuracy for overlapping patterns.
_SORTED_TABLE = sorted(_REGION_TABLE, key=lambda e: len(e.keyword), reverse=True)

# GCC members for coverage scoring
_GCC_MEMBERS = {
    GCCRegion.SAUDI_ARABIA,
    GCCRegion.UAE,
    GCCRegion.QATAR,
    GCCRegion.KUWAIT,
    GCCRegion.BAHRAIN,
    GCCRegion.OMAN,
}
_GCC_MEMBER_COUNT = len(_GCC_MEMBERS)


# ── Engine ────────────────────────────────────────────────────────────────────

def resolve_regions(hints: list[str]) -> RegionMapping:
    """Resolve free-form hint strings to a RegionMapping.

    Scans all hints against the comprehensive region table.
    Returns a RegionMapping with matched regions, confidence, and coverage.

    Args:
        hints: Combined region_hints + country_hints from SourceEvent.

    Returns:
        RegionMapping — always valid, never raises.
    """
    try:
        return _resolve(hints)
    except Exception as e:
        logger.warning("region_engine.resolve_regions failed: %s", e)
        return RegionMapping()


def _resolve(hints: list[str]) -> RegionMapping:
    matched: dict[str, float] = {}        # region_value → best_confidence
    region_matches: list[RegionMatch] = []

    for hint in hints:
        lower = hint.lower().strip()
        if not lower:
            continue
        for entry in _SORTED_TABLE:
            if entry.keyword in lower:
                region_val = entry.region.value
                prev_conf = matched.get(region_val, 0.0)
                # Keep highest confidence for this region
                if entry.confidence > prev_conf:
                    matched[region_val] = entry.confidence
                # Always record the match for traceability
                region_matches.append(RegionMatch(
                    region_value=region_val,
                    matched_keyword=entry.keyword,
                    matched_text=hint,
                    confidence=entry.confidence,
                ))

    if not matched:
        return RegionMapping(
            matched_regions=[],
            gcc_detected=False,
            region_matches=[],
            confidence=0.0,
            coverage_score=0.0,
        )

    # Sort matched regions by confidence descending
    matched_regions = sorted(matched.keys(), key=lambda r: matched[r], reverse=True)
    aggregate_confidence = max(matched.values())

    # GCC detection: any member state OR GCC_WIDE
    gcc_detected = any(
        r in (m.value for m in _GCC_MEMBERS) or r == GCCRegion.GCC_WIDE.value
        for r in matched_regions
    )

    # Coverage score: fraction of GCC members represented
    members_covered = sum(
        1 for r in matched_regions if r in (m.value for m in _GCC_MEMBERS)
    )
    if GCCRegion.GCC_WIDE.value in matched_regions:
        # GCC_WIDE alone counts as 0.5 coverage
        coverage_score = max(0.5, members_covered / _GCC_MEMBER_COUNT)
    else:
        coverage_score = round(members_covered / _GCC_MEMBER_COUNT, 4)

    return RegionMapping(
        matched_regions=matched_regions,
        gcc_detected=gcc_detected,
        region_matches=region_matches,
        confidence=round(aggregate_confidence, 4),
        coverage_score=round(coverage_score, 4),
    )


# ── Convenience ───────────────────────────────────────────────────────────────

def detect_gcc(hints: list[str]) -> bool:
    """Return True if any GCC region can be identified from hints."""
    return resolve_regions(hints).gcc_detected


def to_gcc_regions(mapping: RegionMapping) -> list[GCCRegion]:
    """Convert a RegionMapping to a list of GCCRegion enum values.

    Filters to valid GCCRegion values only. Falls back to [GCC_WIDE] if empty.
    """
    result: list[GCCRegion] = []
    for r in mapping.matched_regions:
        try:
            result.append(GCCRegion(r))
        except ValueError:
            pass
    return result if result else [GCCRegion.GCC_WIDE]
