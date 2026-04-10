"""Macro Intelligence Layer — Signal Normalizer.

Transforms a validated MacroSignalInput into a NormalizedSignal.
All normalization rules live here. No normalization logic in routes or services.

Pipeline:
  1. Assign signal_id
  2. Resolve event_time (default to now UTC)
  3. Map severity_score → severity_level
  4. Infer impact_domains from source if not provided
  5. Compute expires_at from intake_time + ttl_hours
  6. Compute content_hash
  7. Pass through extended fields (signal_type, country_scope, sector_scope, raw_payload)
  8. Produce NormalizedSignal

String normalization rules (all fields):
  - trim leading/trailing whitespace
  - collapse internal whitespace sequences to single space
  - tags: lowercase + deduplicate + sort
  - country_scope / sector_scope: strip + deduplicate + sort (applied by schema validators)
  - raw_payload: passed through as-is (caller-owned structure)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.macro.macro_enums import (
    ImpactDomain,
    SignalSource,
    SignalStatus,
)
from src.macro.macro_schemas import (
    MacroSignal,
    MacroSignalInput,
    NormalizedSignal,
)
from src.macro.macro_validators import severity_from_score


# ── Source → Default Impact Domain Mapping ───────────────────────────────────

SOURCE_DOMAIN_MAP: dict[SignalSource, list[ImpactDomain]] = {
    SignalSource.GEOPOLITICAL: [
        ImpactDomain.OIL_GAS, ImpactDomain.SOVEREIGN_FISCAL,
        ImpactDomain.CAPITAL_MARKETS,
    ],
    SignalSource.ECONOMIC: [
        ImpactDomain.BANKING, ImpactDomain.CAPITAL_MARKETS,
        ImpactDomain.SOVEREIGN_FISCAL,
    ],
    SignalSource.MARKET: [
        ImpactDomain.CAPITAL_MARKETS, ImpactDomain.BANKING,
    ],
    SignalSource.REGULATORY: [
        ImpactDomain.INSURANCE, ImpactDomain.BANKING,
        ImpactDomain.CAPITAL_MARKETS,
    ],
    SignalSource.CLIMATE: [
        ImpactDomain.INSURANCE, ImpactDomain.REAL_ESTATE,
        ImpactDomain.ENERGY_GRID,
    ],
    SignalSource.CYBER: [
        ImpactDomain.CYBER_INFRASTRUCTURE, ImpactDomain.BANKING,
        ImpactDomain.TELECOMMUNICATIONS,
    ],
    SignalSource.INFRASTRUCTURE: [
        ImpactDomain.TRADE_LOGISTICS, ImpactDomain.MARITIME,
        ImpactDomain.AVIATION,
    ],
    SignalSource.SOCIAL: [
        ImpactDomain.INSURANCE, ImpactDomain.REAL_ESTATE,
    ],
    SignalSource.ENERGY: [
        ImpactDomain.OIL_GAS, ImpactDomain.ENERGY_GRID,
        ImpactDomain.CAPITAL_MARKETS,
    ],
    SignalSource.TRADE: [
        ImpactDomain.TRADE_LOGISTICS, ImpactDomain.MARITIME,
        ImpactDomain.OIL_GAS,
    ],
}


# ── Normalization Pipeline ───────────────────────────────────────────────────

def normalize_signal(input_data: MacroSignalInput) -> NormalizedSignal:
    """Transform validated MacroSignalInput → NormalizedSignal.

    This is a pure function: same input always produces same output
    (except for generated UUIDs and timestamps).
    """
    now = datetime.now(timezone.utc)

    # Step 1: Assign identity
    signal_id = uuid4()

    # Step 2: Resolve event_time
    event_time = input_data.event_time
    if event_time is None:
        event_time = now
    elif event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)

    # Step 3: Map severity
    severity_level = severity_from_score(input_data.severity_score)

    # Step 4: Infer impact domains if empty
    impact_domains = input_data.impact_domains
    if not impact_domains:
        impact_domains = SOURCE_DOMAIN_MAP.get(input_data.source, [])
    # Deduplicate while preserving order
    seen: set[ImpactDomain] = set()
    deduped: list[ImpactDomain] = []
    for d in impact_domains:
        if d not in seen:
            seen.add(d)
            deduped.append(d)
    impact_domains = deduped

    # Step 5: Compute TTL and expiry
    ttl_hours = input_data.ttl_hours if input_data.ttl_hours is not None else 72
    expires_at = now + timedelta(hours=ttl_hours)

    # Step 6–7: Build intermediate MacroSignal (computes content_hash)
    macro_signal = MacroSignal(
        signal_id=signal_id,
        title=input_data.title.strip(),
        description=input_data.description.strip() if input_data.description else None,
        source=input_data.source,
        source_uri=input_data.source_uri,
        severity_score=round(input_data.severity_score, 4),
        severity_level=severity_level,
        direction=input_data.direction,
        confidence=input_data.confidence,
        regions=input_data.regions,
        impact_domains=impact_domains,
        event_time=event_time,
        intake_time=now,
        ttl_hours=ttl_hours,
        tags=input_data.tags,
        external_id=input_data.external_id,
        status=SignalStatus.VALIDATED,
    )

    # Step 7: Normalize description whitespace
    description: str | None = None
    if input_data.description:
        description = " ".join(input_data.description.split())

    # Step 8: Produce NormalizedSignal (includes extended Pack 1 fields)
    return NormalizedSignal(
        signal_id=macro_signal.signal_id,
        title=macro_signal.title,
        description=description,
        source=macro_signal.source,
        source_uri=macro_signal.source_uri,
        severity_score=macro_signal.severity_score,
        severity_level=macro_signal.severity_level,
        direction=macro_signal.direction,
        confidence=macro_signal.confidence,
        regions=macro_signal.regions,
        impact_domains=macro_signal.impact_domains,
        event_time=macro_signal.event_time,
        intake_time=macro_signal.intake_time,
        ttl_hours=macro_signal.ttl_hours,
        expires_at=expires_at,
        tags=macro_signal.tags,
        external_id=macro_signal.external_id,
        status=SignalStatus.NORMALIZED,
        content_hash=macro_signal.content_hash,
        normalization_version="1.0.0",
        # Extended fields — passed through from validated input
        signal_type=input_data.signal_type,
        country_scope=input_data.country_scope,   # already normalized by schema validator
        sector_scope=input_data.sector_scope,     # already normalized by schema validator
        raw_payload=input_data.raw_payload,
    )
