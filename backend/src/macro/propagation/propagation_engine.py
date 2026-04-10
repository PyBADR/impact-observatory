"""Macro Intelligence Layer — Propagation Engine.

Deterministic graph traversal engine that builds explainable
propagation paths from a CausalMapping.

Algorithm:
  BFS from each entry domain through activated channels.
  At each hop:
    1. Apply channel weight × (1 - decay) to compute transmitted severity
    2. Record node + edge
    3. Stop if severity drops below threshold or max depth reached
    4. Avoid revisiting domains (no cycles)

Design rules:
  - Deterministic: same CausalMapping → same PropagationResult
  - Explainable: every path, node, and hit includes reasoning
  - No external state: pure function
  - Severity floor: propagation stops when severity < MIN_SEVERITY_THRESHOLD
"""

from __future__ import annotations

from collections import deque
from uuid import UUID

from src.macro.macro_enums import GCCRegion, ImpactDomain, SignalSeverity
from src.macro.macro_validators import severity_from_score
from src.macro.causal.causal_schemas import CausalChannel, CausalMapping
from src.macro.propagation.propagation_schemas import (
    NodeState,
    PropagationEdge,
    PropagationHit,
    PropagationNode,
    PropagationPath,
    PropagationResult,
    _state_from_severity,
)


# ── Constants ────────────────────────────────────────────────────────────────

MIN_SEVERITY_THRESHOLD: float = 0.05  # Stop propagating below 5%
MAX_PROPAGATION_DEPTH: int = 5        # Hard cap on hop depth


# ── Internal Types ───────────────────────────────────────────────────────────

class _TraversalState:
    """Mutable BFS state for a single propagation run."""

    def __init__(self, signal_id: UUID, entry_severity: float, regions: list[GCCRegion]):
        self.signal_id = signal_id
        self.entry_severity = entry_severity
        self.regions = regions
        self.visited: dict[ImpactDomain, PropagationNode] = {}
        self.edges: list[PropagationEdge] = []
        self.paths: list[PropagationPath] = []
        # Track parent chain for path reconstruction
        self.parent: dict[ImpactDomain, tuple[ImpactDomain, CausalChannel, float]] = {}


# ── Engine Core ──────────────────────────────────────────────────────────────

def _build_channel_index(
    channels: list[CausalChannel],
) -> dict[ImpactDomain, list[CausalChannel]]:
    """Build adjacency from activated channels only."""
    adj: dict[ImpactDomain, list[CausalChannel]] = {}
    for ch in channels:
        adj.setdefault(ch.from_domain, []).append(ch)
        if ch.bidirectional:
            adj.setdefault(ch.to_domain, []).append(ch)
    return adj


def _compute_transmitted_severity(
    severity_in: float,
    weight: float,
    decay: float,
) -> float:
    """Compute severity after transmission through a channel.

    Formula: severity_out = severity_in × weight × (1 - decay)
    """
    return round(severity_in * weight * (1.0 - decay), 6)


def _make_node(
    domain: ImpactDomain,
    depth: int,
    severity: float,
    is_entry: bool,
    regions: list[GCCRegion],
) -> PropagationNode:
    return PropagationNode(
        node_id=f"{domain.value}@depth_{depth}",
        domain=domain,
        depth=depth,
        severity_at_node=round(severity, 6),
        severity_level=severity_from_score(severity),
        state=_state_from_severity(severity),
        is_entry=is_entry,
        regions=regions,
    )


def _make_edge(
    channel: CausalChannel,
    severity_in: float,
    severity_out: float,
) -> PropagationEdge:
    return PropagationEdge(
        edge_id=f"{channel.from_domain.value}→{channel.to_domain.value}",
        from_domain=channel.from_domain,
        to_domain=channel.to_domain,
        channel_id=channel.channel_id,
        transmission_label=channel.transmission_label,
        weight_applied=channel.base_weight,
        decay_applied=channel.decay_per_hop,
        lag_hours=channel.lag_hours,
        severity_in=round(severity_in, 6),
        severity_out=round(severity_out, 6),
    )


def _reconstruct_path(
    state: _TraversalState,
    terminal_domain: ImpactDomain,
    entry_domain: ImpactDomain,
) -> PropagationPath | None:
    """Reconstruct the path from entry_domain to terminal_domain."""
    # Walk backward from terminal to entry
    chain: list[ImpactDomain] = [terminal_domain]
    current = terminal_domain
    while current != entry_domain:
        if current not in state.parent:
            return None  # disconnected — should not happen
        parent_domain, _, _ = state.parent[current]
        chain.append(parent_domain)
        current = parent_domain

    chain.reverse()

    # Build ordered nodes and edges
    nodes: list[PropagationNode] = []
    edges: list[PropagationEdge] = []

    for i, domain in enumerate(chain):
        node = state.visited.get(domain)
        if node:
            nodes.append(node)

        if i > 0:
            prev_domain = chain[i - 1]
            # Find the edge between prev and current
            if domain in state.parent:
                _, channel, sev_in = state.parent[domain]
                sev_out = state.visited[domain].severity_at_node if domain in state.visited else 0
                edges.append(_make_edge(channel, sev_in, sev_out))

    if not nodes:
        return None

    entry_sev = nodes[0].severity_at_node
    terminal_sev = nodes[-1].severity_at_node
    cumulative = terminal_sev / entry_sev if entry_sev > 0 else 0.0

    path_desc = " → ".join(n.domain.value for n in nodes)

    return PropagationPath(
        signal_id=state.signal_id,
        nodes=nodes,
        edges=edges,
        entry_domain=entry_domain,
        terminal_domain=terminal_domain,
        total_hops=len(nodes) - 1,
        entry_severity=entry_sev,
        terminal_severity=terminal_sev,
        cumulative_decay=round(cumulative, 6),
        path_description=path_desc,
    )


def propagate(
    mapping: CausalMapping,
    max_depth: int = MAX_PROPAGATION_DEPTH,
    min_severity: float = MIN_SEVERITY_THRESHOLD,
) -> PropagationResult:
    """Run deterministic BFS propagation from a CausalMapping.

    Returns a complete PropagationResult with paths, hits, and audit hash.
    """
    entry = mapping.entry_point
    channels = mapping.activated_channels
    adj = _build_channel_index(channels)

    # Use entry_strength (severity × confidence_weight) for propagation seed.
    # This means low-confidence signals propagate with reduced force.
    seed_severity = entry.entry_strength

    state = _TraversalState(
        signal_id=entry.signal_id,
        entry_severity=seed_severity,
        regions=entry.regions,
    )

    # Initialize BFS queue: (domain, depth, severity_at_domain)
    queue: deque[tuple[ImpactDomain, int, float]] = deque()

    # Seed with entry domains
    for domain in entry.entry_domains:
        node = _make_node(domain, 0, seed_severity, True, entry.regions)
        state.visited[domain] = node
        queue.append((domain, 0, seed_severity))

    # BFS
    while queue:
        current_domain, depth, current_severity = queue.popleft()

        if depth >= max_depth:
            continue

        outgoing = adj.get(current_domain, [])
        for channel in outgoing:
            # Determine downstream domain
            downstream = channel.to_domain
            if channel.bidirectional and channel.to_domain == current_domain:
                downstream = channel.from_domain

            if downstream in state.visited:
                continue  # No revisiting

            transmitted = _compute_transmitted_severity(
                current_severity, channel.base_weight, channel.decay_per_hop
            )

            if transmitted < min_severity:
                continue  # Below threshold

            new_depth = depth + 1
            node = _make_node(downstream, new_depth, transmitted, False, entry.regions)
            state.visited[downstream] = node
            state.parent[downstream] = (current_domain, channel, current_severity)
            state.edges.append(_make_edge(channel, current_severity, transmitted))

            queue.append((downstream, new_depth, transmitted))

    # Build paths: one per terminal node (non-entry visited node)
    paths: list[PropagationPath] = []
    for domain, node in state.visited.items():
        if node.is_entry:
            continue
        # Find the entry domain this path originates from
        # Walk parent chain to find entry
        current = domain
        entry_domain = domain
        while current in state.parent:
            parent_d, _, _ = state.parent[current]
            current = parent_d
            entry_domain = current

        path = _reconstruct_path(state, domain, entry_domain)
        if path:
            paths.append(path)

    # Build hits: one per reached domain
    hits: list[PropagationHit] = []
    for domain, node in state.visited.items():
        # Build path description for this hit
        if node.is_entry:
            path_desc = f"[ENTRY] {domain.value}"
            reasoning = (
                f"Direct causal entry domain from signal. "
                f"Severity {node.severity_at_node:.4f} inherited from source signal."
            )
        else:
            # Reconstruct path string
            chain: list[str] = [domain.value]
            cur = domain
            while cur in state.parent:
                parent_d, ch, _ = state.parent[cur]
                chain.append(parent_d.value)
                cur = parent_d
            chain.reverse()
            path_desc = " → ".join(chain)
            last_channel = state.parent[domain][1] if domain in state.parent else None
            mechanism = last_channel.transmission_label if last_channel else "unknown"
            reasoning = (
                f"Reached via propagation path [{path_desc}]. "
                f"Transmission mechanism: {mechanism}. "
                f"Severity decayed to {node.severity_at_node:.4f} "
                f"({node.severity_level.value}) at depth {node.depth}."
            )

        hits.append(PropagationHit(
            signal_id=entry.signal_id,
            domain=domain,
            depth=node.depth,
            severity_at_hit=node.severity_at_node,
            severity_level=node.severity_level,
            regions=node.regions,
            path_description=path_desc,
            reasoning=reasoning,
        ))

    max_hit_depth = max((h.depth for h in hits), default=0)

    return PropagationResult(
        signal_id=entry.signal_id,
        signal_title=entry.signal_title,
        entry_domains=list(entry.entry_domains),
        paths=paths,
        hits=hits,
        total_domains_reached=len(state.visited),
        max_depth=max_hit_depth,
    )


# ── Graph-Enriched Variant (Integration Pack A) ────────────────────────────
# The propagate() function above is UNCHANGED. This variant wraps it
# with optional post-propagation Graph Brain explanation enrichment.

def propagate_graph_enriched(
    mapping: CausalMapping,
    max_depth: int = MAX_PROPAGATION_DEPTH,
    min_severity: float = MIN_SEVERITY_THRESHOLD,
    graph_service: object | None = None,
) -> tuple[PropagationResult, object | None]:
    """Graph-enriched propagation: runs Pack 2 propagation + graph explanation.

    Returns:
        Tuple of (PropagationResult, ExplanationEnrichment or None).
        The PropagationResult is always the standard Pack 2 output
        (with graph reasoning optionally appended to hit descriptions).

    If graph enrichment is disabled or fails, returns (result, None).
    """
    import logging
    _logger = logging.getLogger(__name__)

    # Step 1: Standard Pack 2 propagation (always runs)
    result = propagate(mapping, max_depth=max_depth, min_severity=min_severity)

    # Step 2: Graph explanation enrichment (optional, fail-safe)
    explanation_enrichment = None
    try:
        from src.graph_brain.enrichment import (
            enrich_explanation,
            is_enrichment_active,
        )

        if not is_enrichment_active("explanation"):
            return result, None

        from src.graph_brain.service import get_graph_brain_service

        service = graph_service or get_graph_brain_service()
        store = service.store  # type: ignore[union-attr]

        reached_domains = [h.domain for h in result.hits]
        explanation_enrichment = enrich_explanation(
            store,
            signal_id=str(mapping.entry_point.signal_id),
            reached_domains=reached_domains,
        )

        # Append graph reasoning to hits (additive, never replaces)
        if explanation_enrichment.has_enrichment:
            count = 0
            for hit in result.hits:
                fragment = explanation_enrichment.get_fragment_for_domain(hit.domain)
                if fragment is not None:
                    hit.reasoning = f"{hit.reasoning}\n  {fragment.reasoning}"
                    count += 1
            _logger.info(
                "Graph enriched %d/%d propagation hits for signal %s",
                count, len(result.hits), mapping.entry_point.signal_id,
            )

    except Exception as e:
        _logger.warning(
            "Graph-enriched propagation failed for signal %s: %s",
            mapping.entry_point.signal_id, e,
        )

    return result, explanation_enrichment
