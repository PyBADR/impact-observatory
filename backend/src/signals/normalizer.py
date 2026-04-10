"""Signal Intelligence Layer — Normalizer.

Normalizes SourceEvent fields and maps them to Pack 1 MacroSignalInput.

Two responsibilities:
  1. normalize_source_event() — cleans/deduplicates fields in-place on a copy
  2. to_signal_input() — maps a normalized SourceEvent to MacroSignalInput

Design rules:
  - Deterministic: same input → same output
  - Never raises: all hint resolution is best-effort
  - Pack 1 mapping is rules-based only (no ML, no LLM)
  - Region/domain resolution delegates to region_engine and domain_engine for
    richer coverage; private _resolve_* functions kept for backward compat
  - direction derived only when deterministic (explicit keyword matching)
  - severity_score derived from the multi-factor severity_engine
  - source_uri set from event.url or event.source_ref
  - raw_payload from the SourceEvent is forwarded to MacroSignalInput.raw_payload
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSource,
    SignalType,
)
from src.macro.macro_schemas import MacroSignalInput
from src.signals.source_models import SourceConfidence, SourceEvent
from src.signals.region_engine import resolve_regions as _engine_resolve_regions
from src.signals.region_engine import to_gcc_regions as _engine_to_gcc_regions
from src.signals.domain_engine import resolve_domains as _engine_resolve_domains
from src.signals.severity_engine import compute_severity as _engine_compute_severity


# ── GCC Region Hint Resolution ────────────────────────────────────────────────

# Maps common region/country strings (lowercase) to GCCRegion values.
# Longer/more specific patterns are checked first via sorted order in resolver.
_REGION_KEYWORDS: dict[str, GCCRegion] = {
    # GCC-wide
    "gcc":            GCCRegion.GCC_WIDE,
    "gulf":           GCCRegion.GCC_WIDE,
    "gulf cooperation": GCCRegion.GCC_WIDE,

    # Saudi Arabia
    "saudi":          GCCRegion.SAUDI_ARABIA,
    "saudi arabia":   GCCRegion.SAUDI_ARABIA,
    "ksa":            GCCRegion.SAUDI_ARABIA,
    "riyadh":         GCCRegion.SAUDI_ARABIA,

    # UAE
    "uae":            GCCRegion.UAE,
    "united arab":    GCCRegion.UAE,
    "dubai":          GCCRegion.UAE,
    "abu dhabi":      GCCRegion.UAE,

    # Qatar
    "qatar":          GCCRegion.QATAR,
    "doha":           GCCRegion.QATAR,

    # Kuwait
    "kuwait":         GCCRegion.KUWAIT,
    "kuwait city":    GCCRegion.KUWAIT,

    # Bahrain
    "bahrain":        GCCRegion.BAHRAIN,
    "manama":         GCCRegion.BAHRAIN,

    # Oman
    "oman":           GCCRegion.OMAN,
    "muscat":         GCCRegion.OMAN,
}


def _resolve_regions(hints: list[str]) -> list[GCCRegion]:
    """Resolve free-form region/country hint strings to GCCRegion values.

    Returns empty list if no GCC regions can be identified.
    Does NOT fall back to GCC_WIDE unless 'gcc' or 'gulf' is explicitly mentioned.
    """
    resolved: set[GCCRegion] = set()
    for hint in hints:
        lower = hint.lower().strip()
        for keyword, region in _REGION_KEYWORDS.items():
            if keyword in lower:
                resolved.add(region)
    return list(resolved)


# ── ImpactDomain Hint Resolution ──────────────────────────────────────────────

_DOMAIN_KEYWORDS: dict[str, ImpactDomain] = {
    "oil":             ImpactDomain.OIL_GAS,
    "gas":             ImpactDomain.OIL_GAS,
    "crude":           ImpactDomain.OIL_GAS,
    "petroleum":       ImpactDomain.OIL_GAS,
    "energy":          ImpactDomain.OIL_GAS,
    "opec":            ImpactDomain.OIL_GAS,

    "bank":            ImpactDomain.BANKING,
    "banking":         ImpactDomain.BANKING,
    "credit":          ImpactDomain.BANKING,
    "lending":         ImpactDomain.BANKING,
    "loan":            ImpactDomain.BANKING,
    "npl":             ImpactDomain.BANKING,
    "fintech":         ImpactDomain.BANKING,

    "insurance":       ImpactDomain.INSURANCE,
    "reinsurance":     ImpactDomain.INSURANCE,
    "takaful":         ImpactDomain.INSURANCE,

    "trade":           ImpactDomain.TRADE_LOGISTICS,
    "logistics":       ImpactDomain.TRADE_LOGISTICS,
    "supply chain":    ImpactDomain.TRADE_LOGISTICS,
    "port":            ImpactDomain.TRADE_LOGISTICS,
    "shipping":        ImpactDomain.MARITIME,
    "freight":         ImpactDomain.TRADE_LOGISTICS,

    "fiscal":          ImpactDomain.SOVEREIGN_FISCAL,
    "sovereign":       ImpactDomain.SOVEREIGN_FISCAL,
    "budget":          ImpactDomain.SOVEREIGN_FISCAL,
    "government revenue": ImpactDomain.SOVEREIGN_FISCAL,
    "treasury":        ImpactDomain.SOVEREIGN_FISCAL,

    "real estate":     ImpactDomain.REAL_ESTATE,
    "property":        ImpactDomain.REAL_ESTATE,
    "construction":    ImpactDomain.REAL_ESTATE,
    "mortgage":        ImpactDomain.REAL_ESTATE,

    "telecom":         ImpactDomain.TELECOMMUNICATIONS,
    "telecommunications": ImpactDomain.TELECOMMUNICATIONS,
    "internet":        ImpactDomain.TELECOMMUNICATIONS,
    "network":         ImpactDomain.TELECOMMUNICATIONS,

    "aviation":        ImpactDomain.AVIATION,
    "airline":         ImpactDomain.AVIATION,
    "airport":         ImpactDomain.AVIATION,
    "flight":          ImpactDomain.AVIATION,

    "maritime":        ImpactDomain.MARITIME,
    "vessel":          ImpactDomain.MARITIME,
    "tanker":          ImpactDomain.MARITIME,
    "strait":          ImpactDomain.MARITIME,
    "chokepoint":      ImpactDomain.MARITIME,

    "grid":            ImpactDomain.ENERGY_GRID,
    "power":           ImpactDomain.ENERGY_GRID,
    "electricity":     ImpactDomain.ENERGY_GRID,
    "utility":         ImpactDomain.ENERGY_GRID,
    "renewables":      ImpactDomain.ENERGY_GRID,

    "cyber":           ImpactDomain.CYBER_INFRASTRUCTURE,
    "cybersecurity":   ImpactDomain.CYBER_INFRASTRUCTURE,
    "hack":            ImpactDomain.CYBER_INFRASTRUCTURE,
    "ransomware":      ImpactDomain.CYBER_INFRASTRUCTURE,

    "capital market":  ImpactDomain.CAPITAL_MARKETS,
    "stock":           ImpactDomain.CAPITAL_MARKETS,
    "equity":          ImpactDomain.CAPITAL_MARKETS,
    "bond":            ImpactDomain.CAPITAL_MARKETS,
    "sukuk":           ImpactDomain.CAPITAL_MARKETS,
    "market":          ImpactDomain.CAPITAL_MARKETS,
}


def _resolve_domains(hints: list[str], category_hints: list[str]) -> list[ImpactDomain]:
    """Resolve hint strings to ImpactDomain values.

    Scans sector_hints first, then category_hints.
    Returns empty list if no domains can be identified.
    """
    resolved: set[ImpactDomain] = set()
    all_hints = [h.lower() for h in hints] + [c.lower() for c in category_hints]

    for text in all_hints:
        for keyword, domain in _DOMAIN_KEYWORDS.items():
            if keyword in text:
                resolved.add(domain)

    return list(resolved)


# ── SignalSource Mapping ───────────────────────────────────────────────────────

_CATEGORY_TO_SOURCE: dict[str, SignalSource] = {
    "geopolitical":  SignalSource.GEOPOLITICAL,
    "political":     SignalSource.GEOPOLITICAL,
    "conflict":      SignalSource.GEOPOLITICAL,
    "war":           SignalSource.GEOPOLITICAL,
    "sanction":      SignalSource.GEOPOLITICAL,
    "diplomatic":    SignalSource.GEOPOLITICAL,

    "economic":      SignalSource.ECONOMIC,
    "economy":       SignalSource.ECONOMIC,
    "gdp":           SignalSource.ECONOMIC,
    "inflation":     SignalSource.ECONOMIC,
    "recession":     SignalSource.ECONOMIC,

    "market":        SignalSource.MARKET,
    "price":         SignalSource.MARKET,
    "trading":       SignalSource.MARKET,
    "volatility":    SignalSource.MARKET,

    "regulatory":    SignalSource.REGULATORY,
    "regulation":    SignalSource.REGULATORY,
    "compliance":    SignalSource.REGULATORY,
    "law":           SignalSource.REGULATORY,

    "climate":       SignalSource.CLIMATE,
    "weather":       SignalSource.CLIMATE,
    "flood":         SignalSource.CLIMATE,
    "drought":       SignalSource.CLIMATE,

    "cyber":         SignalSource.CYBER,
    "hack":          SignalSource.CYBER,
    "breach":        SignalSource.CYBER,

    "infrastructure": SignalSource.INFRASTRUCTURE,
    "power outage":   SignalSource.INFRASTRUCTURE,

    "social":        SignalSource.SOCIAL,
    "protest":       SignalSource.SOCIAL,
    "unrest":        SignalSource.SOCIAL,

    "energy":        SignalSource.ENERGY,
    "oil":           SignalSource.ENERGY,
    "gas":           SignalSource.ENERGY,
    "opec":          SignalSource.ENERGY,

    "trade":         SignalSource.TRADE,
    "tariff":        SignalSource.TRADE,
    "export":        SignalSource.TRADE,
    "import":        SignalSource.TRADE,
}


def _resolve_signal_source(category_hints: list[str]) -> SignalSource:
    """Derive SignalSource from category hints. Defaults to GEOPOLITICAL."""
    for hint in category_hints:
        lower = hint.lower()
        for keyword, source in _CATEGORY_TO_SOURCE.items():
            if keyword in lower:
                return source
    return SignalSource.GEOPOLITICAL


# ── SignalType Mapping ─────────────────────────────────────────────────────────

_CATEGORY_TO_SIGNAL_TYPE: dict[str, SignalType] = {
    "geopolitical":  SignalType.GEOPOLITICAL,
    "political":     SignalType.GEOPOLITICAL,
    "conflict":      SignalType.GEOPOLITICAL,
    "war":           SignalType.GEOPOLITICAL,
    "sanction":      SignalType.GEOPOLITICAL,

    "policy":        SignalType.POLICY,
    "fiscal":        SignalType.POLICY,
    "monetary":      SignalType.POLICY,
    "central bank":  SignalType.POLICY,
    "interest rate": SignalType.POLICY,

    "market":        SignalType.MARKET,
    "price":         SignalType.MARKET,
    "trading":       SignalType.MARKET,
    "volatility":    SignalType.MARKET,
    "equity":        SignalType.MARKET,

    "commodity":     SignalType.COMMODITY,
    "oil":           SignalType.COMMODITY,
    "crude":         SignalType.COMMODITY,
    "energy":        SignalType.COMMODITY,
    "opec":          SignalType.COMMODITY,

    "regulatory":    SignalType.REGULATORY,
    "regulation":    SignalType.REGULATORY,
    "compliance":    SignalType.REGULATORY,

    "logistics":     SignalType.LOGISTICS,
    "supply chain":  SignalType.LOGISTICS,
    "shipping":      SignalType.LOGISTICS,
    "port":          SignalType.LOGISTICS,

    "sentiment":     SignalType.SENTIMENT,
    "social":        SignalType.SENTIMENT,
    "protest":       SignalType.SENTIMENT,

    "systemic":      SignalType.SYSTEMIC,
    "systemic risk": SignalType.SYSTEMIC,
}


def _resolve_signal_type(category_hints: list[str]) -> Optional[SignalType]:
    """Derive SignalType from category hints. Returns None if inconclusive."""
    for hint in category_hints:
        lower = hint.lower()
        for keyword, stype in _CATEGORY_TO_SIGNAL_TYPE.items():
            if keyword in lower:
                return stype
    return None


# ── Direction Detection ────────────────────────────────────────────────────────

# Only derive direction when explicitly deterministic.
# We do NOT try to infer direction from title sentiment — that requires NLP.
# Instead, match on explicit directional keywords in category_hints.

_NEGATIVE_KEYWORDS = frozenset([
    "conflict", "war", "attack", "sanction", "disruption", "crisis",
    "shortage", "collapse", "protest", "unrest", "breach", "hack",
    "cut", "decline", "drop", "fall", "risk", "threat", "warning",
    "concern", "downgrade", "default", "recession",
])

_POSITIVE_KEYWORDS = frozenset([
    "recovery", "growth", "expansion", "upgrade", "surplus",
    "agreement", "deal", "investment", "progress", "stability",
])


def _resolve_direction(category_hints: list[str], sector_hints: list[str]) -> SignalDirection:
    """Derive signal direction. Defaults to NEGATIVE for external signals.

    Returns NEGATIVE if any negative keyword appears.
    Returns POSITIVE only if explicit positive keywords and no negative.
    Returns NEGATIVE as the safe default for external feeds with no clear signal.
    """
    all_text = " ".join(h.lower() for h in category_hints + sector_hints)

    has_negative = any(kw in all_text for kw in _NEGATIVE_KEYWORDS)
    has_positive = any(kw in all_text for kw in _POSITIVE_KEYWORDS)

    if has_negative:
        return SignalDirection.NEGATIVE
    if has_positive:
        return SignalDirection.POSITIVE
    # Safe default for external feeds — unknown direction defaults to NEGATIVE
    # to ensure conservative risk handling
    return SignalDirection.NEGATIVE


# ── SourceConfidence → SignalConfidence ───────────────────────────────────────

_CONFIDENCE_MAP: dict[SourceConfidence, SignalConfidence] = {
    SourceConfidence.VERIFIED:   SignalConfidence.HIGH,
    SourceConfidence.HIGH:       SignalConfidence.HIGH,
    SourceConfidence.MODERATE:   SignalConfidence.MODERATE,
    SourceConfidence.LOW:        SignalConfidence.LOW,
    SourceConfidence.UNVERIFIED: SignalConfidence.UNVERIFIED,
}


def _map_confidence(source_conf: SourceConfidence) -> SignalConfidence:
    return _CONFIDENCE_MAP.get(source_conf, SignalConfidence.UNVERIFIED)


# ── SourceConfidence → severity_score ─────────────────────────────────────────

_CONFIDENCE_SEVERITY: dict[SourceConfidence, float] = {
    SourceConfidence.VERIFIED:   0.70,  # HIGH tier — high-confidence external signal
    SourceConfidence.HIGH:       0.65,  # ELEVATED/HIGH boundary
    SourceConfidence.MODERATE:   0.50,  # ELEVATED
    SourceConfidence.LOW:        0.35,  # GUARDED
    SourceConfidence.UNVERIFIED: 0.25,  # LOW — raw feed, conservative
}


def _default_severity(source_conf: SourceConfidence) -> float:
    """Derive a conservative severity score from source confidence.

    External signals never have a pre-computed severity — this assigns a
    conservative baseline that downstream Pack 1 validation can adjust.
    """
    return _CONFIDENCE_SEVERITY.get(source_conf, 0.25)


# ── String Normalization ──────────────────────────────────────────────────────

def _normalize_str(s: str) -> str:
    """Collapse internal whitespace, strip edges."""
    return " ".join(s.split()).strip()


def _normalize_list(items: list[str]) -> list[str]:
    """Strip, deduplicate, remove empty strings."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = _normalize_str(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


# ── normalize_source_event ────────────────────────────────────────────────────

def normalize_source_event(event: SourceEvent) -> SourceEvent:
    """Return a normalized copy of the source event.

    Applies:
      - String trimming and whitespace collapse on title/description
      - List deduplication and empty-string removal on all hint lists
      - Timezone normalization on published_at/detected_at
      - Recomputes dedup_key on the normalized copy

    Returns a NEW SourceEvent (input is not mutated).
    """
    data = event.model_dump()

    # ── Strings ───────────────────────────────────────────────────────────────
    data["title"] = _normalize_str(data["title"])
    if data.get("description"):
        data["description"] = _normalize_str(data["description"])
    if data.get("source_name"):
        data["source_name"] = _normalize_str(data["source_name"])
    if data.get("source_ref"):
        data["source_ref"] = _normalize_str(data["source_ref"])
    if data.get("url"):
        data["url"] = data["url"].strip()
    if data.get("external_id"):
        data["external_id"] = data["external_id"].strip()

    # ── Lists ─────────────────────────────────────────────────────────────────
    for field in ("region_hints", "country_hints", "sector_hints", "category_hints"):
        data[field] = _normalize_list(data.get(field) or [])

    # ── Timestamps ────────────────────────────────────────────────────────────
    if data.get("published_at"):
        dt = event.published_at
        if dt and dt.tzinfo is None:
            data["published_at"] = dt.replace(tzinfo=timezone.utc)

    if data.get("detected_at"):
        dt = event.detected_at
        if dt and dt.tzinfo is None:
            data["detected_at"] = dt.replace(tzinfo=timezone.utc)

    # ── Reset dedup_key so it recomputes from normalized fields ───────────────
    data["dedup_key"] = ""

    # Reset event_id to preserve identity
    data["event_id"] = event.event_id

    return SourceEvent(**data)


# ── Pack 1 Mapping ────────────────────────────────────────────────────────────

def to_signal_input(event: SourceEvent) -> MacroSignalInput:
    """Map a SourceEvent to a Pack 1 MacroSignalInput.

    Mapping rules (all deterministic, no ML):
      title        → title (truncated to 300 chars)
      description  → description
      source_ref   → source_uri
      category/sector hints → source (SignalSource)
      category/sector hints → signal_type (Optional[SignalType])
      region/country hints  → regions (via region_engine, fallback GCC_WIDE)
      sector/category hints → impact_domains (via domain_engine)
      category hints        → direction (conservative default: NEGATIVE)
      source_confidence     → confidence
      multi-factor engines  → severity_score
      external_id          → external_id
      published_at         → event_time
      raw_payload          → raw_payload (with source traceability added)
      sector/country hints → sector_scope / country_scope
    """
    # ── Regions — delegate to region_engine for richer coverage ──────────────
    all_region_hints = list(event.region_hints) + list(event.country_hints)
    region_mapping = _engine_resolve_regions(all_region_hints)
    regions = _engine_to_gcc_regions(region_mapping)
    # to_gcc_regions already falls back to [GCC_WIDE] if empty

    # ── Domains — delegate to domain_engine ───────────────────────────────────
    domain_hints: list[str] = list(event.sector_hints) + list(event.category_hints)
    domain_mapping = _engine_resolve_domains(domain_hints)
    domains: list[ImpactDomain] = []
    for dv in domain_mapping.matched_domains:
        try:
            domains.append(ImpactDomain(dv))
        except ValueError:
            pass

    # ── Source and type ───────────────────────────────────────────────────────
    signal_source = _resolve_signal_source(event.category_hints)
    signal_type   = _resolve_signal_type(event.category_hints)

    # ── Direction ─────────────────────────────────────────────────────────────
    direction = _resolve_direction(event.category_hints, event.sector_hints)

    # ── Confidence ────────────────────────────────────────────────────────────
    confidence = _map_confidence(event.source_confidence)

    # ── Severity — multi-factor via severity_engine ───────────────────────────
    urgency_hints: list[str] = []
    if event.title:
        urgency_hints.append(event.title)
    if event.description:
        urgency_hints.append(event.description)
    urgency_hints.extend(event.category_hints)
    urgency_hints.extend(event.sector_hints)

    severity_estimate = _engine_compute_severity(
        source_confidence=event.source_confidence,
        domain_mapping=domain_mapping,
        region_mapping=region_mapping,
        text_hints=urgency_hints,
    )
    severity = severity_estimate.score
    # Guard: never go below the baseline for the source confidence tier
    severity = max(severity, _default_severity(event.source_confidence))

    # ── Title (safe truncation) ────────────────────────────────────────────────
    title = event.title[:300]

    # ── Raw payload with source traceability ──────────────────────────────────
    enriched_payload: dict = {
        "_signal_source_name": event.source_name,
        "_signal_source_ref":  event.source_ref,
        "_signal_source_type": event.source_type.value,
        "_signal_event_id":    str(event.event_id),
        "_signal_dedup_key":   event.dedup_key,
    }
    if event.raw_payload:
        enriched_payload.update(event.raw_payload)

    # ── Country/sector scope ───────────────────────────────────────────────────
    country_scope = list(event.country_hints)[:20]
    sector_scope  = list(event.sector_hints)[:20]

    # ── Tags from category hints ───────────────────────────────────────────────
    tags = [c.lower() for c in event.category_hints[:20]]

    return MacroSignalInput(
        title=title,
        description=event.description,
        source=signal_source,
        source_uri=event.url or event.source_ref,
        severity_score=severity,
        direction=direction,
        confidence=confidence,
        regions=regions,
        impact_domains=domains,
        event_time=event.published_at,
        signal_type=signal_type,
        country_scope=country_scope,
        sector_scope=sector_scope,
        tags=tags,
        external_id=event.external_id,
        raw_payload=enriched_payload,
    )
