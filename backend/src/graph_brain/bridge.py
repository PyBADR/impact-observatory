"""Graph Brain Integration Pack A — Type Bridge.

Converts Graph Brain types into Pack 2-compatible enrichment data
without modifying Pack 2 contracts. The bridge is a pure adapter:
it reads from Graph Brain and emits typed enrichment payloads that
Pack 2 functions can optionally consume.

Design rules:
  - Pure functions: no side effects, no mutation of Pack 2 types
  - Additive: enrichment data is supplementary, never replaces existing
  - Safe: returns empty/neutral values on any failure
  - Typed: all outputs are Pydantic models or typed dicts

Bridge responsibilities:
  1. Graph → CausalChannel discovery  (additional channels from graph edges)
  2. Graph → Propagation weight hints (confidence-weighted edge data)
  3. Graph → Explanation fragments    (reasoning text from graph paths)
"""

from __future__ import annotations

import logging
from typing import Optional

from src.graph_brain.store import GraphStore
from src.graph_brain.query import find_downstream, trace_paths, find_by_relation
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphPath,
    GraphRelationType,
    GraphSourceRef,
)
from src.macro.macro_enums import GCCRegion, ImpactDomain

logger = logging.getLogger(__name__)


# ── Enrichment Data Types ──────────────────────────────────────────────────

class GraphChannelHint:
    """A hint from the graph about an additional causal channel.

    Not a CausalChannel — this is advisory data that the causal mapper
    can use to discover additional channels it wouldn't find in the
    static causal graph.
    """

    __slots__ = (
        "from_domain", "to_domain", "graph_weight",
        "graph_confidence", "relation_type", "reasoning",
    )

    def __init__(
        self,
        from_domain: ImpactDomain,
        to_domain: ImpactDomain,
        graph_weight: float,
        graph_confidence: GraphConfidence,
        relation_type: GraphRelationType,
        reasoning: str,
    ) -> None:
        self.from_domain = from_domain
        self.to_domain = to_domain
        self.graph_weight = graph_weight
        self.graph_confidence = graph_confidence
        self.relation_type = relation_type
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return (
            f"GraphChannelHint({self.from_domain.value}→{self.to_domain.value}, "
            f"w={self.graph_weight:.2f}, conf={self.graph_confidence.value})"
        )


class GraphWeightHint:
    """A graph-derived weight modifier for an existing propagation edge.

    Used to optionally adjust transmission weight based on graph evidence.
    The propagation engine uses this as a secondary signal, not a replacement.
    """

    __slots__ = ("from_domain", "to_domain", "graph_weight", "confidence_factor", "reasoning")

    def __init__(
        self,
        from_domain: ImpactDomain,
        to_domain: ImpactDomain,
        graph_weight: float,
        confidence_factor: float,
        reasoning: str,
    ) -> None:
        self.from_domain = from_domain
        self.to_domain = to_domain
        self.graph_weight = graph_weight
        self.confidence_factor = confidence_factor
        self.reasoning = reasoning


class GraphExplanationFragment:
    """A fragment of graph-backed reasoning for inclusion in explanation output.

    Provides supplementary reasoning that the propagation engine wouldn't
    generate on its own (e.g. entity-level connections, multi-hop paths).
    """

    __slots__ = ("domain", "reasoning", "confidence", "graph_paths_count", "source_refs")

    def __init__(
        self,
        domain: ImpactDomain,
        reasoning: str,
        confidence: GraphConfidence,
        graph_paths_count: int = 0,
        source_refs: list[GraphSourceRef] | None = None,
    ) -> None:
        self.domain = domain
        self.reasoning = reasoning
        self.confidence = confidence
        self.graph_paths_count = graph_paths_count
        self.source_refs = source_refs or []


# ── Domain Key Mapping ─────────────────────────────────────────────────────

# Maps ImpactDomain enum values to graph node IDs
def _domain_to_graph_id(domain: ImpactDomain) -> str:
    """Convert an ImpactDomain to its Graph Brain node ID."""
    return f"impact_domain:{domain.value}"


def _graph_id_to_domain(node_id: str) -> Optional[ImpactDomain]:
    """Try to convert a graph node ID back to an ImpactDomain."""
    if not node_id.startswith("impact_domain:"):
        return None
    try:
        return ImpactDomain(node_id.split(":", 1)[1])
    except ValueError:
        return None


def _signal_graph_id(signal_id: str) -> str:
    """Convert a signal UUID to its Graph Brain node ID."""
    return f"signal:{signal_id}"


# ── Channel Hints ──────────────────────────────────────────────────────────

def discover_graph_channel_hints(
    store: GraphStore,
    signal_id: str,
    entry_domains: list[ImpactDomain],
    max_depth: int = 3,
) -> list[GraphChannelHint]:
    """Discover additional causal channels from graph structure.

    Looks at graph edges connected to the signal's entry domains
    and finds domain→domain relationships that the static causal graph
    might not contain.

    Args:
        store: The GraphStore to query.
        signal_id: The signal UUID (used for signal-specific graph paths).
        entry_domains: The causal entry domains from Pack 2.
        max_depth: Max traversal depth in graph.

    Returns:
        List of GraphChannelHint for additional channels found.
    """
    hints: list[GraphChannelHint] = []
    seen_pairs: set[tuple[str, str]] = set()

    for domain in entry_domains:
        domain_node_id = _domain_to_graph_id(domain)
        if not store.has_node(domain_node_id):
            continue

        # Find downstream impact domains reachable from this domain
        downstream = find_downstream(
            store, domain_node_id,
            max_depth=max_depth,
            relation_filter={
                GraphRelationType.AFFECTS,
                GraphRelationType.PROPAGATES_TO,
                GraphRelationType.EXPOSED_TO,
                GraphRelationType.INFLUENCES,
            },
        )

        for target_node in downstream:
            target_domain = _graph_id_to_domain(target_node.node_id)
            if target_domain is None:
                continue
            if target_domain == domain:
                continue

            pair_key = (domain.value, target_domain.value)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Get the best path for weight/confidence info
            paths = trace_paths(
                store, domain_node_id, target_node.node_id,
                max_depth=max_depth, max_paths=1,
            )
            if not paths:
                continue

            best_path = paths[0]
            # Use path weight as the graph-derived channel strength
            graph_weight = best_path.total_weight

            # Determine confidence from the path's weakest edge
            min_conf = GraphConfidence.MODERATE
            if best_path.edges:
                min_conf_weight = min(
                    CONFIDENCE_WEIGHTS.get(e.confidence, 0.5)
                    for e in best_path.edges
                )
                for level in [
                    GraphConfidence.DEFINITIVE, GraphConfidence.HIGH,
                    GraphConfidence.MODERATE, GraphConfidence.LOW,
                    GraphConfidence.SPECULATIVE,
                ]:
                    if min_conf_weight >= CONFIDENCE_WEIGHTS[level]:
                        min_conf = level
                        break

            # Determine the dominant relation type
            rel_type = GraphRelationType.PROPAGATES_TO
            if best_path.edges:
                rel_type = best_path.edges[0].relation_type

            reasoning = (
                f"Graph Brain discovered path: {best_path.path_description} "
                f"(weight={graph_weight:.4f}, hops={best_path.total_hops}, "
                f"confidence={min_conf.value})"
            )

            hints.append(GraphChannelHint(
                from_domain=domain,
                to_domain=target_domain,
                graph_weight=graph_weight,
                graph_confidence=min_conf,
                relation_type=rel_type,
                reasoning=reasoning,
            ))

    return hints


# ── Weight Hints ───────────────────────────────────────────────────────────

def compute_graph_weight_hints(
    store: GraphStore,
    from_domain: ImpactDomain,
    to_domain: ImpactDomain,
) -> Optional[GraphWeightHint]:
    """Compute a graph-derived weight hint for a specific domain pair.

    If the graph has edges between these domains, returns a weight hint
    that the propagation engine can use as a secondary signal.

    Returns None if no graph evidence exists for this pair.
    """
    from_id = _domain_to_graph_id(from_domain)
    to_id = _domain_to_graph_id(to_domain)

    if not store.has_node(from_id) or not store.has_node(to_id):
        return None

    paths = trace_paths(store, from_id, to_id, max_depth=3, max_paths=1)
    if not paths:
        return None

    best = paths[0]
    # Confidence factor: graph confidence → numeric weight
    conf_factor = 1.0
    if best.edges:
        conf_factor = min(
            CONFIDENCE_WEIGHTS.get(e.confidence, 0.5)
            for e in best.edges
        )

    return GraphWeightHint(
        from_domain=from_domain,
        to_domain=to_domain,
        graph_weight=best.total_weight,
        confidence_factor=conf_factor,
        reasoning=(
            f"Graph path {best.path_description} "
            f"weight={best.total_weight:.4f}, "
            f"confidence_factor={conf_factor:.2f}"
        ),
    )


# ── Explanation Fragments ──────────────────────────────────────────────────

def build_explanation_fragments(
    store: GraphStore,
    signal_id: str,
    reached_domains: list[ImpactDomain],
    max_depth: int = 4,
) -> list[GraphExplanationFragment]:
    """Build graph-backed explanation fragments for reached domains.

    For each domain reached by propagation, queries the graph for
    supporting evidence and builds a reasoning fragment.

    Args:
        store: The GraphStore to query.
        signal_id: The signal UUID.
        reached_domains: Domains reached by the propagation engine.
        max_depth: Max graph traversal depth.

    Returns:
        List of GraphExplanationFragment for each domain with graph evidence.
    """
    fragments: list[GraphExplanationFragment] = []
    signal_node_id = _signal_graph_id(signal_id)

    if not store.has_node(signal_node_id):
        return fragments

    for domain in reached_domains:
        domain_node_id = _domain_to_graph_id(domain)
        if not store.has_node(domain_node_id):
            continue

        # Trace paths from signal to this domain in the graph
        paths = trace_paths(
            store, signal_node_id, domain_node_id,
            max_depth=max_depth, max_paths=3,
        )

        if not paths:
            continue

        best = paths[0]

        # Collect source refs from all path elements
        refs: list[GraphSourceRef] = []
        for node in best.nodes:
            refs.extend(node.source_refs)
        for edge in best.edges:
            refs.extend(edge.source_refs)

        # Determine confidence
        conf = GraphConfidence.MODERATE
        if best.edges:
            min_w = min(CONFIDENCE_WEIGHTS.get(e.confidence, 0.5) for e in best.edges)
            for level in [
                GraphConfidence.DEFINITIVE, GraphConfidence.HIGH,
                GraphConfidence.MODERATE, GraphConfidence.LOW,
                GraphConfidence.SPECULATIVE,
            ]:
                if min_w >= CONFIDENCE_WEIGHTS[level]:
                    conf = level
                    break

        reasoning = (
            f"[Graph Brain] Signal→{domain.value}: "
            f"{len(paths)} graph path(s) found. "
            f"Best path: {best.path_description} "
            f"(weight={best.total_weight:.4f}, hops={best.total_hops}). "
            f"Graph confidence: {conf.value}."
        )

        fragments.append(GraphExplanationFragment(
            domain=domain,
            reasoning=reasoning,
            confidence=conf,
            graph_paths_count=len(paths),
            source_refs=refs,
        ))

    return fragments
