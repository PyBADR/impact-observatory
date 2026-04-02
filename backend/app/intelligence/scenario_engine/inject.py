"""Shock injection into the graph.
Applies exogenous shocks to selected nodes with specified impacts.
"""


def inject_shocks(baseline: dict, shocks: list[dict]) -> dict:
    """
    Inject shocks into the scenario baseline.

    Args:
        baseline: Baseline state dictionary
        shocks: List of shock dicts with nodeId, impact, type

    Returns:
        Dictionary with:
        - baseline: The input baseline
        - shocks_applied: List of processed shocks
        - shock_count: Number of shocks applied
    """
    shocked_state = dict(baseline)
    applied = []

    for shock in shocks:
        node_id = shock.get("nodeId", "")
        # Clamp impact to [-1.0, 1.0]
        impact = max(-1.0, min(1.0, shock.get("impact", 0)))
        shock_type = shock.get("type", "direct")

        applied.append(
            {
                "nodeId": node_id,
                "impact": impact,
                "type": shock_type,
            }
        )

    return {
        "baseline": baseline,
        "shocks_applied": applied,
        "shock_count": len(applied),
    }
