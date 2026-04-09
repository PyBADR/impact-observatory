"""Graph Brain Integration Pack A — Enrichment Layer.

Feature-flagged enrichment functions that optionally enhance
Pack 2 causal entry and propagation with Graph Brain data.

Architecture:
  - Every enrichment function has a feature flag (enabled/disabled)
  - Disabled enrichment = exact same behavior as before Graph Brain
  - Enabled enrichment = additive overlay, never replaces Pack 2 logic
  - All enrichment is fail-safe: exceptions → log + return original data

Integration points:
  1. enrich_causal_entry     — adds graph-discovered channels to entry
  2. enrich_propagation_hit  — appends graph reasoning to hit explanation
  3. build_graph_enriched_result — post-process PropagationResult with graph data

Design rules:
  - NEVER modify Pack 2 types or schemas
  - NEVER block propagation if graph is unavailable
  - All enrichment appends, never replaces
  - Feature flags are module-level, changeable at runtime
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from src.graph_brain.bridge import (
    GraphChannelHint,
    GraphExplanationFragment,
    GraphWeightHint,
    build_explanation_fragments,
    compute_graph_weight_hints,
    discover_graph_channel_hints,
)
from src.graph_brain.store import GraphStore
from src.graph_brain.ingestion import ingest_signal, IngestionResult
from src.graph_brain.types import CONFIDENCE_WEIGHTS, GraphConfidence
from src.macro.macro_enums import ImpactDomain
from src.macro.macro_schemas import NormalizedSignal
from src.macro.causal.causal_schemas import CausalEntryPoint, CausalMapping

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Feature Flags — module-level, runtime-switchable
# ══════════════════════════════════════════════════════════════════════════════

# Master switch: if False, all enrichment is disabled
GRAPH_ENRICHMENT_ENABLED: bool = True

# Individual feature flags
GRAPH_CAUSAL_ENTRY_ENRICHMENT: bool = True    # Add graph hints to causal entry
GRAPH_PROPAGATION_ENRICHMENT: bool = True      # Add graph weight hints to propagation
GRAPH_EXPLANATION_ENRICHMENT: bool = True       # Add graph reasoning to explanations
GRAPH_AUTO_INGEST: bool = True                  # Auto-ingest signals into graph


def set_enrichment_enabled(enabled: bool) -> None:
    """Set the master enrichment switch."""
    global GRAPH_ENRICHMENT_ENABLED
    GRAPH_ENRICHMENT_ENABLED = enabled


def set_feature_flags(
    *,
    causal_entry: Optional[bool] = None,
    propagation: Optional[bool] = None,
    explanation: Optional[bool] = None,
    auto_ingest: Optional[bool] = None,
) -> None:
    """Set individual feature flags."""
    global GRAPH_CAUSAL_ENTRY_ENRICHMENT, GRAPH_PROPAGATION_ENRICHMENT
    global GRAPH_EXPLANATION_ENRICHMENT, GRAPH_AUTO_INGEST

    if causal_entry is not None:
        GRAPH_CAUSAL_ENTRY_ENRICHMENT = causal_entry
    if propagation is not None:
        GRAPH_PROPAGATION_ENRICHMENT = propagation
    if explanation is not None:
        GRAPH_EXPLANATION_ENRICHMENT = explanation
    if auto_ingest is not None:
        GRAPH_AUTO_INGEST = auto_ingest


def is_enrichment_active(feature: str = "master") -> bool:
    """Check if a specific enrichment feature is active."""
    if not GRAPH_ENRICHMENT_ENABLED:
        return False
    flag_map = {
        "master": True,
        "causal_entry": GRAPH_CAUSAL_ENTRY_ENRICHMENT,
        "propagation": GRAPH_PROPAGATION_ENRICHMENT,
        "explanation": GRAPH_EXPLANATION_ENRICHMENT,
        "auto_ingest": GRAPH_AUTO_INGEST,
    }
    return flag_map.get(feature, False)


# ══════════════════════════════════════════════════════════════════════════════
# Auto-Ingest
# ══════════════════════════════════════════════════════════════════════════════

def ensure_signal_ingested(
    signal: NormalizedSignal,
    store: GraphStore,
) -> Optional[IngestionResult]:
    """Ensure a signal is ingested into the graph store.

    Idempotent: if signal already exists in graph, returns None.
    Fail-safe: on error, logs and returns None.
    """
    if not is_enrichment_active("auto_ingest"):
        return None

    try:
        signal_node_id = f"signal:{signal.signal_id}"
        if store.has_node(signal_node_id):
            return None  # Already ingested
        result = ingest_signal(signal, store)
        logger.info(
            "Graph Brain auto-ingested signal %s: %s",
            signal.signal_id, result,
        )
        return result
    except Exception as e:
        logger.warning(
            "Graph Brain auto-ingest failed for signal %s: %s",
            signal.signal_id, e,
        )
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Causal Entry Enrichment
# ══════════════════════════════════════════════════════════════════════════════

class CausalEntryEnrichment:
    """Enrichment data for a causal entry point.

    Contains graph-discovered channel hints that the causal mapper
    can optionally use to supplement its static channel discovery.
    """

    def __init__(
        self,
        channel_hints: list[GraphChannelHint],
        additional_domains: list[ImpactDomain],
        reasoning: str,
    ) -> None:
        self.channel_hints = channel_hints
        self.additional_domains = additional_domains
        self.reasoning = reasoning

    @property
    def has_enrichment(self) -> bool:
        return len(self.channel_hints) > 0

    def __repr__(self) -> str:
        return (
            f"CausalEntryEnrichment(hints={len(self.channel_hints)}, "
            f"additional_domains={len(self.additional_domains)})"
        )


def enrich_causal_entry(
    store: GraphStore,
    signal: NormalizedSignal,
    entry_point: CausalEntryPoint,
    existing_channel_pairs: set[tuple[str, str]] | None = None,
) -> CausalEntryEnrichment:
    """Enrich a causal entry with graph-discovered channels.

    Args:
        store: The GraphStore to query.
        signal: The source NormalizedSignal.
        entry_point: The Pack 2 CausalEntryPoint.
        existing_channel_pairs: Set of (from.value, to.value) tuples
            for channels already in the static graph. Hints for
            existing pairs are excluded.

    Returns:
        CausalEntryEnrichment with supplementary channel hints.
        Empty enrichment if feature is disabled or graph has no data.
    """
    empty = CausalEntryEnrichment([], [], "Graph enrichment not active")

    if not is_enrichment_active("causal_entry"):
        return empty

    try:
        hints = discover_graph_channel_hints(
            store,
            signal_id=str(signal.signal_id),
            entry_domains=list(entry_point.entry_domains),
            max_depth=3,
        )

        # Filter out hints for channels that already exist in static graph
        if existing_channel_pairs:
            hints = [
                h for h in hints
                if (h.from_domain.value, h.to_domain.value) not in existing_channel_pairs
            ]

        # Identify additional domains not in entry_domains
        entry_set = set(entry_point.entry_domains)
        additional: list[ImpactDomain] = []
        for h in hints:
            if h.to_domain not in entry_set:
                additional.append(h.to_domain)
                entry_set.add(h.to_domain)

        reasoning = (
            f"Graph Brain discovered {len(hints)} additional channel hint(s) "
            f"and {len(additional)} new domain(s) for signal {signal.signal_id}."
            if hints else
            f"Graph Brain found no additional channels for signal {signal.signal_id}."
        )

        return CausalEntryEnrichment(
            channel_hints=hints,
            additional_domains=additional,
            reasoning=reasoning,
        )

    except Exception as e:
        logger.warning(
            "Graph causal entry enrichment failed for signal %s: %s",
            signal.signal_id, e,
        )
        return empty


# ══════════════════════════════════════════════════════════════════════════════
# Propagation Weight Enrichment
# ══════════════════════════════════════════════════════════════════════════════

class PropagationWeightEnrichment:
    """Graph-derived weight modifier for a propagation edge.

    The propagation engine can use this to blend graph evidence
    with its static channel weights.
    """

    def __init__(
        self,
        weight_hint: GraphWeightHint,
        blended_weight: float,
        blend_factor: float,
    ) -> None:
        self.weight_hint = weight_hint
        self.blended_weight = blended_weight
        self.blend_factor = blend_factor


# Default blend factor: how much graph evidence influences propagation weight.
# 0.0 = ignore graph entirely, 1.0 = fully override with graph weight.
# 0.15 is conservative — slight nudge from graph evidence.
GRAPH_WEIGHT_BLEND_FACTOR: float = 0.15


def compute_blended_weight(
    static_weight: float,
    store: GraphStore,
    from_domain: ImpactDomain,
    to_domain: ImpactDomain,
    blend_factor: float = GRAPH_WEIGHT_BLEND_FACTOR,
) -> tuple[float, Optional[PropagationWeightEnrichment]]:
    """Compute a blended weight using static channel weight + graph evidence.

    Formula: blended = static × (1 - bf) + graph × bf × confidence_factor

    If graph evidence is unavailable or enrichment is disabled,
    returns (static_weight, None) — zero behavioral change.

    Args:
        static_weight: The Pack 2 CausalChannel base_weight.
        store: The GraphStore to query.
        from_domain: Source domain.
        to_domain: Target domain.
        blend_factor: How much graph evidence influences the result.

    Returns:
        Tuple of (effective_weight, enrichment_or_none).
    """
    if not is_enrichment_active("propagation"):
        return static_weight, None

    try:
        hint = compute_graph_weight_hints(store, from_domain, to_domain)
        if hint is None:
            return static_weight, None

        graph_contribution = hint.graph_weight * hint.confidence_factor
        blended = static_weight * (1.0 - blend_factor) + graph_contribution * blend_factor
        # Clamp to [0.0, 1.0]
        blended = max(0.0, min(1.0, round(blended, 6)))

        enrichment = PropagationWeightEnrichment(
            weight_hint=hint,
            blended_weight=blended,
            blend_factor=blend_factor,
        )

        return blended, enrichment

    except Exception as e:
        logger.warning(
            "Graph weight enrichment failed for %s→%s: %s",
            from_domain.value, to_domain.value, e,
        )
        return static_weight, None


# ══════════════════════════════════════════════════════════════════════════════
# Explanation Enrichment
# ══════════════════════════════════════════════════════════════════════════════

class ExplanationEnrichment:
    """Graph-backed reasoning fragments for propagation explanation."""

    def __init__(
        self,
        fragments: list[GraphExplanationFragment],
        summary: str,
    ) -> None:
        self.fragments = fragments
        self.summary = summary

    @property
    def has_enrichment(self) -> bool:
        return len(self.fragments) > 0

    def get_fragment_for_domain(
        self,
        domain: ImpactDomain,
    ) -> Optional[GraphExplanationFragment]:
        """Get the explanation fragment for a specific domain, if any."""
        for f in self.fragments:
            if f.domain == domain:
                return f
        return None


def enrich_explanation(
    store: GraphStore,
    signal_id: str,
    reached_domains: list[ImpactDomain],
    max_depth: int = 4,
) -> ExplanationEnrichment:
    """Build graph-backed explanation enrichment for propagation results.

    Args:
        store: The GraphStore to query.
        signal_id: The signal UUID string.
        reached_domains: All domains reached by propagation.
        max_depth: Max graph traversal depth.

    Returns:
        ExplanationEnrichment with fragments for each domain with graph evidence.
        Empty enrichment if feature is disabled or graph is empty.
    """
    empty = ExplanationEnrichment([], "Graph explanation enrichment not active")

    if not is_enrichment_active("explanation"):
        return empty

    try:
        fragments = build_explanation_fragments(
            store, signal_id, reached_domains, max_depth=max_depth,
        )

        if fragments:
            summary = (
                f"Graph Brain provided reasoning for {len(fragments)}/{len(reached_domains)} "
                f"domains reached by propagation."
            )
        else:
            summary = "Graph Brain had no additional reasoning for reached domains."

        return ExplanationEnrichment(
            fragments=fragments,
            summary=summary,
        )

    except Exception as e:
        logger.warning(
            "Graph explanation enrichment failed for signal %s: %s",
            signal_id, e,
        )
        return empty
