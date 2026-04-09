"""Signal Intelligence Layer — Severity Engine.

Multi-factor severity scoring for SourceEvent signals.

Four weighted factors:
  confidence_factor  (weight 0.45) — source credibility tier
  domain_factor      (weight 0.20) — matched domain exposure weights
  urgency_factor     (weight 0.25) — urgency keyword presence in text
  region_factor      (weight 0.10) — GCC region coverage breadth

Design rules:
  - Deterministic: same inputs → same SeverityEstimate
  - No ML, no LLM, no external state
  - Never raises; returns a safe default SeverityEstimate on failure
  - Final score always in [0.0, 1.0]

Public API:
  compute_severity(source_confidence, domain_mapping, region_mapping, text_hints) -> SeverityEstimate
"""

from __future__ import annotations

import logging

from src.signals.source_models import SourceConfidence
from src.signals.types import DomainMapping, RegionMapping, SeverityEstimate

logger = logging.getLogger("signals.severity_engine")


# ── Factor Weights ────────────────────────────────────────────────────────────

_WEIGHT_CONFIDENCE: float = 0.45
_WEIGHT_DOMAIN:     float = 0.20
_WEIGHT_URGENCY:    float = 0.25
_WEIGHT_REGION:     float = 0.10


# ── Confidence → Factor ───────────────────────────────────────────────────────

_CONFIDENCE_FACTOR: dict[SourceConfidence, float] = {
    SourceConfidence.VERIFIED:   1.00,
    SourceConfidence.HIGH:       0.85,
    SourceConfidence.MODERATE:   0.65,
    SourceConfidence.LOW:        0.45,
    SourceConfidence.UNVERIFIED: 0.25,
}


# ── Domain Exposure Weights ───────────────────────────────────────────────────
# Mirrors DOMAIN_EXPOSURE_WEIGHTS from impact_engine — kept in sync manually.

_DOMAIN_EXPOSURE: dict[str, float] = {
    "oil_gas":              0.95,
    "sovereign_fiscal":     0.90,
    "banking":              0.85,
    "trade_logistics":      0.80,
    "capital_markets":      0.75,
    "energy_grid":          0.75,
    "maritime":             0.70,
    "real_estate":          0.70,
    "aviation":             0.65,
    "insurance":            0.65,
    "telecommunications":   0.60,
    "cyber_infrastructure": 0.55,
}

# Threshold above which a domain is considered "high-exposure"
_HIGH_EXPOSURE_THRESHOLD: float = 0.75


# ── Urgency Keywords ──────────────────────────────────────────────────────────
# (keyword, urgency_weight) — weight reflects severity of implied disruption.
# Listed longest-first to avoid partial-match collisions in text scan.

_URGENCY_KEYWORDS: list[tuple[str, float]] = [
    ("cyber attack",     0.90),
    ("cyberattack",      0.90),
    ("imminent",         1.00),
    ("immediate",        1.00),
    ("emergency",        1.00),
    ("escalating",       0.85),
    ("escalation",       0.90),
    ("ransomware",       0.90),
    ("critical",         0.95),
    ("explosion",        0.90),
    ("blockade",         0.85),
    ("collapse",         0.85),
    ("shutdown",         0.80),
    ("sanctions",        0.80),
    ("conflict",         0.80),
    ("default",          0.80),
    ("severe",           0.85),
    ("urgent",           0.90),
    ("attack",           0.85),
    ("strike",           0.75),
    ("crisis",           0.80),
    ("outage",           0.70),
    ("shortage",         0.70),
    ("disruption",       0.70),
    ("downgrade",        0.70),
    ("suspended",        0.65),
    ("freeze",           0.70),
    ("breach",           0.75),
    ("alert",            0.65),
    ("warning",          0.60),
    ("halt",             0.65),
    ("war",              0.90),
    ("hack",             0.75),
    ("tension",          0.60),
    ("protest",          0.55),
    ("risk",             0.40),
    ("concern",          0.35),
]


# ── Region Coverage → Factor ──────────────────────────────────────────────────

def _compute_region_factor(region_mapping: RegionMapping) -> float:
    """Derive region factor from GCC coverage.

    - No GCC detection  → 0.0
    - GCC_WIDE only     → 0.30 (conservative — broad but unspecific)
    - Partial coverage  → linear fraction of members covered
    - Full coverage     → 1.0
    """
    if not region_mapping.gcc_detected:
        return 0.0
    cov = region_mapping.coverage_score
    if cov == 0.0:
        # gcc_detected but no member states — implies GCC_WIDE match only
        return 0.30
    return round(max(0.20, cov), 4)


# ── Engine ────────────────────────────────────────────────────────────────────

def compute_severity(
    source_confidence: SourceConfidence,
    domain_mapping: DomainMapping,
    region_mapping: RegionMapping,
    text_hints: list[str],
) -> SeverityEstimate:
    """Compute a multi-factor severity estimate.

    Args:
        source_confidence: Source credibility tier from SourceEvent.
        domain_mapping:    Output of domain_engine.resolve_domains().
        region_mapping:    Output of region_engine.resolve_regions().
        text_hints:        Combined title + description + category/sector hints.

    Returns:
        SeverityEstimate — always valid, never raises.
    """
    try:
        return _compute(source_confidence, domain_mapping, region_mapping, text_hints)
    except Exception as e:
        logger.warning("severity_engine.compute_severity failed: %s", e)
        return SeverityEstimate(notes=f"fallback due to error: {e}")


def _compute(
    source_confidence: SourceConfidence,
    domain_mapping: DomainMapping,
    region_mapping: RegionMapping,
    text_hints: list[str],
) -> SeverityEstimate:

    # ── 1. Confidence factor ───────────────────────────────────────────────────
    conf_factor = _CONFIDENCE_FACTOR.get(source_confidence, 0.25)

    # ── 2. Domain factor ───────────────────────────────────────────────────────
    high_exposure_domains: list[str] = []
    if domain_mapping.matched_domains:
        domain_scores: list[float] = []
        for dv in domain_mapping.matched_domains:
            exp = _DOMAIN_EXPOSURE.get(dv, 0.50)
            w   = domain_mapping.domain_weights.get(dv, 0.0)
            domain_scores.append(exp * w)
            if exp >= _HIGH_EXPOSURE_THRESHOLD:
                high_exposure_domains.append(dv)
        # Average cross-domain score, scaled up slightly for multi-domain signals
        avg = sum(domain_scores) / len(domain_scores)
        dom_factor = round(min(1.0, avg * 1.50), 4)
    else:
        dom_factor = 0.0

    # ── 3. Urgency factor ─────────────────────────────────────────────────────
    combined_text = " ".join(h.lower() for h in text_hints)
    urgency_found: list[str] = []
    max_urgency   = 0.0

    for keyword, weight in _URGENCY_KEYWORDS:
        if keyword in combined_text and keyword not in urgency_found:
            urgency_found.append(keyword)
            max_urgency = max(max_urgency, weight)

    if urgency_found:
        # Primary signal: max keyword weight; small multi-keyword bonus (up to +0.10)
        bonus      = min(0.10, (len(urgency_found) - 1) * 0.02)
        urg_factor = round(min(1.0, max_urgency + bonus), 4)
    else:
        urg_factor = 0.0

    # ── 4. Region factor ──────────────────────────────────────────────────────
    reg_factor = _compute_region_factor(region_mapping)

    # ── Final weighted score ──────────────────────────────────────────────────
    score = (
        conf_factor * _WEIGHT_CONFIDENCE
        + dom_factor  * _WEIGHT_DOMAIN
        + urg_factor  * _WEIGHT_URGENCY
        + reg_factor  * _WEIGHT_REGION
    )
    score = round(min(1.0, max(0.0, score)), 4)

    notes = (
        f"conf={conf_factor:.2f}×{_WEIGHT_CONFIDENCE} "
        f"dom={dom_factor:.2f}×{_WEIGHT_DOMAIN} "
        f"urg={urg_factor:.2f}×{_WEIGHT_URGENCY} "
        f"reg={reg_factor:.2f}×{_WEIGHT_REGION} "
        f"→ {score:.4f}"
    )

    return SeverityEstimate(
        score=score,
        confidence_factor=round(conf_factor, 4),
        domain_factor=round(dom_factor, 4),
        urgency_factor=round(urg_factor, 4),
        region_factor=round(reg_factor, 4),
        urgency_keywords_found=urgency_found,
        high_exposure_domains=high_exposure_domains,
        notes=notes,
    )
