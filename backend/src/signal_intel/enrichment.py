"""Signal Intelligence Layer — Signal Enrichment Engine.

Pure-function enrichment that enhances RawFeedItem fields before mapping.
Called by mapper.map_feed_item() — NOT a new pipeline stage.

Four deterministic sub-functions:
  1. classify_signal_type  — keyword/category → SignalType hint
  2. extract_regions       — title/description scanning → region hints
  3. extract_domains       — title/description + categories → domain hints
  4. compute_severity      — multi-factor severity scoring

No LLM inference. No network calls. No randomness.
All functions are idempotent: same input → same output.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from src.signal_intel.dictionaries import (
    CONFIDENCE_WEIGHTS,
    DOMAIN_SCAN_KEYWORDS,
    REGION_BOUNDARY_PHRASES,
    REGION_SCAN_PHRASES,
    SEVERITY_KEYWORDS,
    SIGNAL_TYPE_KEYWORDS,
)
from src.signal_intel.types import FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.enrichment")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SIGNAL TYPE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def classify_signal_type(
    title: str,
    description: Optional[str] = None,
    categories: Optional[list[str]] = None,
    feed_type: Optional[FeedType] = None,
    existing_hint: Optional[str] = None,
) -> Optional[str]:
    """Classify signal type from title, description, categories.

    Priority order:
      1. Existing hint (pass-through if already set)
      2. Category match against SIGNAL_TYPE_KEYWORDS
      3. Title + description keyword scan (highest priority wins)
      4. Feed type fallback (ECONOMIC → "market")
      5. None if no match

    Returns:
        Signal type string (e.g., "geopolitical") or None.
    """
    # 1. Pass through existing hint
    if existing_hint:
        return existing_hint

    best_type: Optional[str] = None
    best_priority: int = -1

    # 2. Category scan
    for cat in (categories or []):
        cat_lower = cat.strip().lower()
        if cat_lower in SIGNAL_TYPE_KEYWORDS:
            stype, priority = SIGNAL_TYPE_KEYWORDS[cat_lower]
            if priority > best_priority:
                best_type = stype
                best_priority = priority

    # 3. Title + description keyword scan
    corpus = title.lower()
    if description:
        corpus += " " + description.lower()

    for keyword, (stype, priority) in SIGNAL_TYPE_KEYWORDS.items():
        if priority > best_priority and keyword in corpus:
            best_type = stype
            best_priority = priority

    if best_type is not None:
        logger.debug(
            "enrichment.classify type=%s priority=%d title=%.60s",
            best_type, best_priority, title,
        )
        return best_type

    # 4. Feed type fallback
    if feed_type == FeedType.ECONOMIC:
        return "market"

    # 5. No match
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 2. REGION EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

# Pre-compiled word boundary pattern for short keywords
_WORD_BOUNDARY_CACHE: dict[str, re.Pattern] = {}


def _is_word_boundary_match(phrase: str, corpus: str) -> bool:
    """Check if phrase appears as a whole word in corpus.

    Uses word-boundary regex to prevent partial matches
    (e.g., 'oman' should not match inside 'ottoman' or 'romania').
    """
    if phrase not in _WORD_BOUNDARY_CACHE:
        _WORD_BOUNDARY_CACHE[phrase] = re.compile(
            r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE
        )
    return bool(_WORD_BOUNDARY_CACHE[phrase].search(corpus))


def extract_regions(
    title: str,
    description: Optional[str] = None,
    existing_hints: Optional[list[str]] = None,
) -> list[str]:
    """Extract GCC region codes from title and description content.

    Supplements (never replaces) existing hints. Uses:
      1. REGION_SCAN_PHRASES — longest-first substring matching
      2. REGION_BOUNDARY_PHRASES — word-boundary matching for short terms

    Returns:
        Deduplicated list of region code strings (e.g., ["SA", "AE"]).
    """
    hints: set[str] = set(existing_hints or [])

    corpus = title.lower()
    if description:
        corpus += " " + description.lower()

    # Phase 1: Longest-first phrase matching (safe substrings)
    for phrase, region_code in REGION_SCAN_PHRASES:
        if phrase in corpus:
            hints.add(region_code)

    # Phase 2: Word-boundary matching for short/ambiguous terms
    for phrase, region_code in REGION_BOUNDARY_PHRASES:
        if _is_word_boundary_match(phrase, corpus):
            hints.add(region_code)

    added = hints - set(existing_hints or [])
    if added:
        logger.debug(
            "enrichment.region added=%s title=%.60s",
            sorted(added), title,
        )

    return sorted(hints)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DOMAIN EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_domains(
    title: str,
    description: Optional[str] = None,
    categories: Optional[list[str]] = None,
    existing_hints: Optional[list[str]] = None,
) -> list[str]:
    """Extract impact domain hints from title, description, and categories.

    Supplements (never replaces) existing hints. Uses:
      1. Category resolution against DOMAIN_SCAN_KEYWORDS
      2. Title + description keyword scanning

    Returns:
        Deduplicated list of domain value strings (e.g., ["oil_gas", "banking"]).
    """
    from src.signal_intel.dictionaries import DOMAIN_ALIASES

    hints: set[str] = set(existing_hints or [])

    # Phase 1: Resolve categories
    for cat in (categories or []):
        cat_lower = cat.strip().lower()
        if cat_lower in DOMAIN_ALIASES:
            hints.add(DOMAIN_ALIASES[cat_lower])

    # Phase 2: Title + description keyword scan (longest-first)
    corpus = title.lower()
    if description:
        corpus += " " + description.lower()

    # Sort keywords longest-first for correct multi-word matching
    for keyword in sorted(DOMAIN_SCAN_KEYWORDS.keys(), key=len, reverse=True):
        if keyword in corpus:
            hints.add(DOMAIN_SCAN_KEYWORDS[keyword])

    added = hints - set(existing_hints or [])
    if added:
        logger.debug(
            "enrichment.domain added=%s title=%.60s",
            sorted(added), title,
        )

    return sorted(hints)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SEVERITY SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def compute_severity(
    title: str,
    description: Optional[str] = None,
    source_quality: float = 0.5,
    confidence: str = "unverified",
    existing_hint: Optional[float] = None,
) -> float:
    """Compute multi-factor severity score.

    Formula:
      base = existing_hint if > 0 else 0.3
      keyword_mod = max keyword multiplier from title (default 1.0)
      quality_factor = 0.7 + 0.3 * source_quality  (range 0.7 – 1.0)
      confidence_weight = CONFIDENCE_WEIGHTS[confidence]
      final = clamp(base * keyword_mod * quality_factor * confidence_weight, 0.0, 1.0)

    Returns:
        Float in [0.0, 1.0].
    """
    # Base score
    base = existing_hint if (existing_hint is not None and existing_hint > 0) else 0.3

    # Keyword modifier — scan title (primary signal) and description
    corpus = title.lower()
    if description:
        corpus += " " + description.lower()

    keyword_mod = 1.0
    matched_keyword = None

    # Sort keywords longest-first so multi-word phrases match before sub-words
    for keyword in sorted(SEVERITY_KEYWORDS.keys(), key=len, reverse=True):
        if keyword in corpus:
            mod = SEVERITY_KEYWORDS[keyword]
            if mod > keyword_mod or (mod < 1.0 and keyword_mod == 1.0):
                # Take highest amplifier, or first dampener if no amplifier found
                keyword_mod = mod
                matched_keyword = keyword

    # Source quality factor: high-quality feeds get full weight
    quality_factor = 0.7 + 0.3 * max(0.0, min(1.0, source_quality))

    # Confidence weight
    confidence_weight = CONFIDENCE_WEIGHTS.get(
        confidence.strip().lower() if confidence else "unverified",
        0.60,
    )

    # Final score
    raw = base * keyword_mod * quality_factor * confidence_weight
    final = max(0.0, min(1.0, raw))

    logger.debug(
        "enrichment.severity base=%.2f keyword=%.2f(%s) quality=%.2f conf=%.2f final=%.2f title=%.60s",
        base, keyword_mod, matched_keyword or "none",
        quality_factor, confidence_weight, final, title,
    )

    return round(final, 4)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE ENRICHMENT
# ═══════════════════════════════════════════════════════════════════════════════

def enrich_feed_item(item: RawFeedItem) -> RawFeedItem:
    """Apply all enrichment functions to a RawFeedItem in-place.

    Enriches: signal_type_hint, region_hints, domain_hints, severity_hint.
    Never removes existing values — only supplements.

    Returns the same item (mutated) for chaining convenience.
    """
    # Extract categories from payload
    categories: list[str] = []
    if item.payload:
        cats = item.payload.get("categories", [])
        if isinstance(cats, list):
            categories = [str(c) for c in cats if c]

    # 1. Classification
    item.signal_type_hint = classify_signal_type(
        title=item.title,
        description=item.description or None,
        categories=categories,
        feed_type=item.feed_type,
        existing_hint=item.signal_type_hint,
    )

    # 2. Region extraction
    item.region_hints = extract_regions(
        title=item.title,
        description=item.description or None,
        existing_hints=item.region_hints,
    )

    # 3. Domain extraction
    item.domain_hints = extract_domains(
        title=item.title,
        description=item.description or None,
        categories=categories,
        existing_hints=item.domain_hints,
    )

    # 4. Severity scoring
    item.severity_hint = compute_severity(
        title=item.title,
        description=item.description or None,
        source_quality=item.source_quality,
        confidence=item.confidence,
        existing_hint=item.severity_hint,
    )

    return item
