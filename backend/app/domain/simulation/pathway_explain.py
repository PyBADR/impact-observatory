"""
Impact Observatory | مرصد الأثر — Phase 2 Pathway Headline Generator
Surfaces the dominant stress transmission path as executive-readable headlines.

Design:
  Walks the propagation graph to find the top-K highest-weight paths
  from shock origin to terminal impact, then renders each as a single
  headline string. These headlines slot directly into the demo UI's
  TransmissionStep and PropagationStep components.

Architecture layer: Explainability (Layer 7 — Governance)

Output examples:
  "Oil & Gas (Kuwait) → Banking (Kuwait) → Real Estate (Kuwait): $2.1B at risk"
  "Banking (UAE) → Banking (Bahrain): Correspondent corridor carries 65% of stress"
"""
from __future__ import annotations

from app.domain.simulation.graph_types import Edge, NodeId, PropagationGraph
from app.domain.simulation.schemas import CountryImpact, SectorImpact


def _fmt_usd(value: float) -> str:
    if abs(value) >= 1e9:
        return f"${value / 1e9:.1f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.0f}M"
    return f"${value:,.0f}"


def _node_label(node_id: NodeId, spec: object) -> str:
    """Human-readable label for a graph node."""
    country_meta = getattr(spec, "country_meta", {})
    sector_meta = getattr(spec, "sector_meta", {})
    c_name = country_meta.get(node_id.country, {}).get("name", node_id.country)
    s_label = sector_meta.get(node_id.sector, {}).get("label", node_id.sector)
    return f"{s_label} ({c_name})"


# ═══════════════════════════════════════════════════════════════════════════════
# Pathway Discovery
# ═══════════════════════════════════════════════════════════════════════════════

def _find_dominant_paths(
    graph: PropagationGraph,
    max_depth: int = 3,
    top_k: int = 5,
) -> list[list[Edge]]:
    """Find the top-K highest effective-weight paths in the graph.

    Uses greedy DFS from each high-stress source node, following the
    highest-weight outgoing edge at each hop. Paths are ranked by
    cumulative effective weight (product of source.stress * edge.weight
    along the path).
    """
    # Start from nodes with high initial shock (top 6 shock sources)
    start_nodes = sorted(
        graph.nodes.items(),
        key=lambda kv: kv[1].initial_shock,
        reverse=True,
    )[:6]

    all_paths: list[tuple[float, list[Edge]]] = []

    for start_id, start_state in start_nodes:
        if start_state.initial_shock < 0.05:
            continue

        # Greedy DFS: always follow the strongest outgoing edge
        path: list[Edge] = []
        visited: set[NodeId] = {start_id}
        current = start_id
        cumulative_weight = start_state.stress

        for _ in range(max_depth):
            outgoing = graph.neighbors(current)
            if not outgoing:
                break

            # Pick the edge with highest effective transmission
            best_edge: Edge | None = None
            best_effective = 0.0
            for edge in outgoing:
                if edge.target in visited:
                    continue
                eff = graph.nodes[edge.source].stress * edge.weight
                if eff > best_effective:
                    best_effective = eff
                    best_edge = edge

            if best_edge is None or best_effective < 0.02:
                break

            path.append(best_edge)
            visited.add(best_edge.target)
            current = best_edge.target
            cumulative_weight *= best_edge.weight

        if path:
            all_paths.append((cumulative_weight, path))

    # Sort by cumulative weight descending
    all_paths.sort(key=lambda p: p[0], reverse=True)
    return [p[1] for p in all_paths[:top_k]]


# ═══════════════════════════════════════════════════════════════════════════════
# Headline Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_pathway_headlines(
    graph: PropagationGraph,
    spec: object,
    country_impacts: list[CountryImpact],
    sector_impacts: list[SectorImpact],
) -> list[str]:
    """Generate executive-readable transmission pathway headlines.

    Returns 3–5 headlines describing the dominant stress transmission paths.
    Each headline names the path and quantifies the risk.
    """
    paths = _find_dominant_paths(graph)
    if not paths:
        return ["Stress contained within initial shock perimeter — no significant propagation detected."]

    headlines: list[str] = []

    # Build a quick lookup for country losses
    country_loss: dict[str, float] = {
        ci.country_code.value: ci.loss_usd for ci in country_impacts
    }

    for path in paths:
        # Build node chain: source of first edge → target of each edge
        chain_nodes = [path[0].source] + [e.target for e in path]
        chain_labels = [_node_label(n, spec) for n in chain_nodes]
        chain_str = " → ".join(chain_labels)

        # Quantify: use the terminal node's country loss
        terminal_country = chain_nodes[-1].country
        terminal_loss = country_loss.get(terminal_country, 0.0)

        # Channel of the first (strongest) edge
        primary_channel = path[0].channel

        headline = (
            f"{chain_str}: {primary_channel} — "
            f"{_fmt_usd(terminal_loss)} exposure in {chain_nodes[-1].country}"
        )
        headlines.append(headline)

    # Add a summary headline
    top_sector = sector_impacts[0] if sector_impacts else None
    top_country = country_impacts[0] if country_impacts else None
    if top_sector and top_country:
        headlines.append(
            f"Dominant channel: {top_sector.sector_label} sector drives "
            f"{top_country.country_name} to {_fmt_usd(top_country.loss_usd)} total exposure"
        )

    return headlines
