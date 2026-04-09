"""Signal Intelligence Layer — Signal Mapper.

classify_event() runs all three quality engines and derives a
SignalClassification with an overall quality tier.

Quality tiers (derived from quality_score 0.0–1.0):
  HIGH       ≥ 0.80 — region + domain + description + timestamp + good confidence
  GOOD       ≥ 0.60 — region + domain + reasonable confidence
  ACCEPTABLE ≥ 0.40 — region OR domain identified, moderate confidence
  LOW        ≥ 0.20 — some data but significant gaps
  POOR        < 0.20 — minimal usable data

Design rules:
  - Deterministic: same event → same SignalClassification
  - Delegates to region_engine, domain_engine, severity_engine
  - Never raises; returns a POOR classification with notes on failure

Public API:
  classify_event(event: SourceEvent) -> SignalClassification
"""

from __future__ import annotations

import logging

from src.signals.source_models import SourceConfidence, SourceEvent
from src.signals.types import (
    SignalClassification,
    SignalQuality,
)
from src.signals.region_engine import resolve_regions
from src.signals.domain_engine import resolve_domains
from src.signals.severity_engine import compute_severity

logger = logging.getLogger("signals.mapper")


# ── Quality Tiers ─────────────────────────────────────────────────────────────
# (min_score, tier) — checked in descending order, first match wins.

_QUALITY_TIERS: list[tuple[float, SignalQuality]] = [
    (0.80, SignalQuality.HIGH),
    (0.60, SignalQuality.GOOD),
    (0.40, SignalQuality.ACCEPTABLE),
    (0.20, SignalQuality.LOW),
]


# ── Source Confidence Quality Scores ─────────────────────────────────────────

_CONF_QUALITY_SCORE: dict[SourceConfidence, float] = {
    SourceConfidence.VERIFIED:   1.00,
    SourceConfidence.HIGH:       0.85,
    SourceConfidence.MODERATE:   0.65,
    SourceConfidence.LOW:        0.40,
    SourceConfidence.UNVERIFIED: 0.20,
}


# ── Public API ────────────────────────────────────────────────────────────────

def classify_event(event: SourceEvent) -> SignalClassification:
    """Classify a SourceEvent using all three quality engines.

    Runs region_engine, domain_engine, and severity_engine then derives
    an overall SignalQuality tier from a weighted quality score.

    Args:
        event: A SourceEvent (normalized or raw).

    Returns:
        SignalClassification — always valid, never raises.
    """
    try:
        return _classify(event)
    except Exception as e:
        logger.warning("mapper.classify_event failed: %s", e)
        return SignalClassification(notes=[f"classification failed: {e}"])


# ── Private Implementation ────────────────────────────────────────────────────

def _classify(event: SourceEvent) -> SignalClassification:

    # ── Engine calls ──────────────────────────────────────────────────────────

    # Region: combine region_hints + country_hints
    all_region_hints = list(event.region_hints) + list(event.country_hints)
    region_mapping = resolve_regions(all_region_hints)

    # Domain: title (optional) + sector_hints + category_hints
    domain_hints: list[str] = []
    if event.title:
        domain_hints.append(event.title)
    domain_hints.extend(event.sector_hints)
    domain_hints.extend(event.category_hints)
    domain_mapping = resolve_domains(domain_hints)

    # Severity: title + description + category_hints + sector_hints for urgency
    urgency_hints: list[str] = []
    if event.title:
        urgency_hints.append(event.title)
    if event.description:
        urgency_hints.append(event.description)
    urgency_hints.extend(event.category_hints)
    urgency_hints.extend(event.sector_hints)

    severity_estimate = compute_severity(
        source_confidence=event.source_confidence,
        domain_mapping=domain_mapping,
        region_mapping=region_mapping,
        text_hints=urgency_hints,
    )

    # ── Quality factor computation ─────────────────────────────────────────────
    quality_factors: dict[str, float] = {}
    notes: list[str] = []

    # 1. GCC region score (weight 0.25)
    if region_mapping.gcc_detected:
        cov = region_mapping.coverage_score
        region_score = cov if cov > 0.0 else 0.30   # 0.30 for GCC_WIDE-only
        region_score = round(region_score, 4)
    else:
        region_score = 0.0
        notes.append("no GCC region identified")
    quality_factors["region"] = region_score

    # 2. Domain score (weight 0.25)
    if domain_mapping.is_empty:
        domain_score = 0.0
        notes.append("no domain identified")
    else:
        # Base = domain confidence, small bonus per additional domain (capped at +0.20)
        multi_bonus = min(0.20, (domain_mapping.domain_count - 1) * 0.05)
        domain_score = round(min(1.0, domain_mapping.confidence + multi_bonus), 4)
    quality_factors["domain"] = domain_score

    # 3. Description completeness (weight 0.20)
    desc = (event.description or "").strip()
    if len(desc) >= 50:
        desc_score = 1.0
    elif len(desc) >= 10:
        desc_score = 0.50
    else:
        desc_score = 0.0
        notes.append("no description")
    quality_factors["description"] = desc_score

    # 4. Timestamp presence (weight 0.10)
    ts_score = 1.0 if event.published_at is not None else 0.0
    if ts_score == 0.0:
        notes.append("no timestamp")
    quality_factors["timestamp"] = ts_score

    # 5. Source confidence (weight 0.20)
    conf_score = _CONF_QUALITY_SCORE.get(event.source_confidence, 0.20)
    quality_factors["source_confidence"] = conf_score

    # ── Aggregate ─────────────────────────────────────────────────────────────
    quality_score = round(
        region_score * 0.25
        + domain_score * 0.25
        + desc_score   * 0.20
        + ts_score     * 0.10
        + conf_score   * 0.20,
        4,
    )

    # ── Tier assignment ───────────────────────────────────────────────────────
    quality = SignalQuality.POOR
    for threshold, tier in _QUALITY_TIERS:
        if quality_score >= threshold:
            quality = tier
            break

    return SignalClassification(
        quality=quality,
        region_mapping=region_mapping,
        domain_mapping=domain_mapping,
        severity_estimate=severity_estimate,
        quality_score=quality_score,
        quality_factors=quality_factors,
        notes=notes,
    )
