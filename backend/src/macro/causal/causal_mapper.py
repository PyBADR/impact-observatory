"""Macro Intelligence Layer — Causal Mapper Service.

Maps a NormalizedSignal → CausalMapping (entry point + activated channels).

Responsibilities:
  1. Determine causal entry domains from the signal's impact_domains
  2. Compute entry_strength from severity × confidence_weight
  3. Build a CausalEntryPoint with full explainability
  4. Discover all activated channels reachable from entry domains
  5. Package into a CausalMapping for the propagation engine

Design rules:
  - Pure function: same signal → same mapping (deterministic)
  - No state — stateless mapper service
  - All reasoning is explicit string tracing
  - entry_strength = severity × confidence_weight (deterministic, no ML)
"""

from __future__ import annotations

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
)
from src.macro.macro_schemas import NormalizedSignal
from src.macro.causal.causal_schemas import (
    CausalChannel,
    CausalEntryPoint,
    CausalMapping,
)
from src.macro.causal.causal_graph import get_outgoing_channels


# ── Confidence → Weight Mapping ──────────────────────────────────────────────

CONFIDENCE_WEIGHTS: dict[SignalConfidence, float] = {
    SignalConfidence.VERIFIED: 1.00,
    SignalConfidence.HIGH: 0.90,
    SignalConfidence.MODERATE: 0.70,
    SignalConfidence.LOW: 0.45,
    SignalConfidence.UNVERIFIED: 0.25,
}


def compute_entry_strength(severity: float, confidence: SignalConfidence) -> float:
    """Compute entry strength: severity × confidence_weight.

    Deterministic. No ML. Confidence downgrades propagation force.
    """
    weight = CONFIDENCE_WEIGHTS.get(confidence, 0.25)
    return round(severity * weight, 6)


# ── Entry Point Builder ──────────────────────────────────────────────────────

def map_signal_to_causal_entry(signal: NormalizedSignal) -> CausalEntryPoint:
    """Map a normalized signal to its causal entry point.

    Entry domains come directly from the signal's impact_domains
    (already inferred/validated in Pack 1 normalization).
    """
    entry_domains = signal.impact_domains
    regions = signal.regions
    entry_strength = compute_entry_strength(signal.severity_score, signal.confidence)

    # Build reasoning string
    domain_str = ", ".join(d.value for d in entry_domains)
    region_str = ", ".join(r.value for r in regions)
    conf_weight = CONFIDENCE_WEIGHTS.get(signal.confidence, 0.25)
    reasoning = (
        f"Signal '{signal.title}' (source={signal.source.value}, "
        f"severity={signal.severity_score:.2f}/{signal.severity_level.value}, "
        f"confidence={signal.confidence.value}, direction={signal.direction.value}) "
        f"enters causal graph through [{domain_str}] "
        f"affecting regions [{region_str}]. "
        f"Entry strength={entry_strength:.4f} "
        f"(severity {signal.severity_score:.2f} × confidence_weight {conf_weight:.2f}). "
        f"Entry domains derived from signal impact_domains "
        f"(source-inferred or explicitly provided at intake)."
    )

    return CausalEntryPoint(
        signal_id=signal.signal_id,
        signal_title=signal.title,
        source=signal.source,
        signal_type=getattr(signal, "signal_type", None),
        entry_domains=entry_domains,
        direction=signal.direction,
        inherited_severity=signal.severity_score,
        severity_level=signal.severity_level,
        confidence=signal.confidence,
        entry_strength=entry_strength,
        regions=regions,
        reasoning=reasoning,
    )


# ── Channel Discovery ────────────────────────────────────────────────────────

def discover_activated_channels(
    entry_point: CausalEntryPoint,
    max_depth: int = 4,
) -> list[CausalChannel]:
    """Discover all causal channels reachable from entry domains.

    Uses BFS to find all channels within max_depth hops.
    Region filtering: only activates channels relevant to the signal's regions.

    Returns deduplicated list of activated channels.
    """
    activated: dict[str, CausalChannel] = {}
    visited_domains: set[ImpactDomain] = set()
    frontier: list[ImpactDomain] = list(entry_point.entry_domains)
    depth = 0

    while frontier and depth < max_depth:
        next_frontier: list[ImpactDomain] = []
        for domain in frontier:
            if domain in visited_domains:
                continue
            visited_domains.add(domain)

            # Get outgoing channels, filtered by signal regions
            for region in entry_point.regions:
                for channel in get_outgoing_channels(domain, region):
                    if channel.channel_id not in activated:
                        activated[channel.channel_id] = channel
                        downstream = channel.to_domain
                        if channel.bidirectional and channel.to_domain == domain:
                            downstream = channel.from_domain
                        if downstream not in visited_domains:
                            next_frontier.append(downstream)

        frontier = next_frontier
        depth += 1

    return list(activated.values())


# ── Full Mapping ─────────────────────────────────────────────────────────────

def map_signal_to_causal(
    signal: NormalizedSignal,
    max_depth: int = 4,
) -> CausalMapping:
    """Full causal mapping: signal → entry point → activated channels.

    This is the primary entry point for the causal mapper.
    """
    entry_point = map_signal_to_causal_entry(signal)
    activated = discover_activated_channels(entry_point, max_depth=max_depth)

    reachable: set[ImpactDomain] = set(entry_point.entry_domains)
    for ch in activated:
        reachable.add(ch.from_domain)
        reachable.add(ch.to_domain)

    return CausalMapping(
        entry_point=entry_point,
        activated_channels=activated,
        total_reachable_domains=len(reachable),
    )


# ── Graph-Aware Variant (Integration Pack A) ───────────────────────────────
# The functions above are UNCHANGED. This variant wraps them with
# optional Graph Brain enrichment. If graph is unavailable or disabled,
# the result is identical to map_signal_to_causal().

def map_signal_to_causal_graph_aware(
    signal: NormalizedSignal,
    max_depth: int = 4,
    graph_service: object | None = None,
) -> tuple["CausalMapping", object | None]:
    """Graph-aware causal mapping: runs Pack 2 mapping + graph enrichment.

    Returns:
        Tuple of (CausalMapping, CausalEntryEnrichment or None).
        The CausalMapping is always the standard Pack 2 output.
        The enrichment is supplementary metadata from Graph Brain.

    If graph enrichment is disabled or fails, returns (mapping, None).
    """
    import logging
    _logger = logging.getLogger(__name__)

    # Step 1: Standard Pack 2 mapping (always runs)
    mapping = map_signal_to_causal(signal, max_depth=max_depth)

    # Step 2: Graph enrichment (optional, fail-safe)
    enrichment = None
    try:
        from src.graph_brain.enrichment import (
            enrich_causal_entry,
            ensure_signal_ingested,
            is_enrichment_active,
        )

        if not is_enrichment_active("causal_entry"):
            return mapping, None

        # Lazy import to avoid circular dependency at module load time
        from src.graph_brain.service import get_graph_brain_service

        service = graph_service or get_graph_brain_service()
        store = service.store  # type: ignore[union-attr]

        ensure_signal_ingested(signal, store)

        existing_pairs = {
            (ch.from_domain.value, ch.to_domain.value)
            for ch in mapping.activated_channels
        }
        enrichment = enrich_causal_entry(
            store, signal, mapping.entry_point, existing_pairs,
        )

    except Exception as e:
        _logger.warning(
            "Graph-aware causal mapping enrichment failed for signal %s: %s",
            signal.signal_id, e,
        )

    return mapping, enrichment
