"""Baseline state computation for scenario comparison.
Establishes baseline metrics from graph structure for delta calculation.
"""

# Default sector GDP bases (in billions USD)
SECTOR_GDP_BASE = {
    "infrastructure": 450,
    "economy": 1200,
    "finance": 800,
    "society": 600,
    "geography": 200,
}


def compute_baseline(graph_nodes: list[dict], graph_edges: list[dict]) -> dict:
    """
    Compute baseline state from graph structure.

    Args:
        graph_nodes: List of node dicts with layer, weight, etc.
        graph_edges: List of edge connections

    Returns:
        Dictionary with:
        - sector_baseline: GDP and metrics per sector
        - total_gdp: Sum of all sector GDPs
        - node_count: Total nodes
        - edge_count: Total edges
    """
    sector_baseline = {}

    for sector, gdp in SECTOR_GDP_BASE.items():
        # Filter nodes by layer
        nodes = [n for n in graph_nodes if n.get("layer") == sector]
        node_count = len(nodes)
        avg_weight = (
            sum(n.get("weight", 0.5) for n in nodes) / max(node_count, 1)
        )

        sector_baseline[sector] = {
            "gdp_base": gdp,
            "node_count": node_count,
            "avg_weight": avg_weight,
        }

    total_gdp = sum(SECTOR_GDP_BASE.values())

    return {
        "sector_baseline": sector_baseline,
        "total_gdp": total_gdp,
        "node_count": len(graph_nodes),
        "edge_count": len(graph_edges),
    }
