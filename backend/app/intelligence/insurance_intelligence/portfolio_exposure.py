"""Portfolio Exposure: PE = SUM(policy_value * zone_factor * cat_loading)
Computes total portfolio exposure weighted by geographic zone and catastrophe type.
"""
import numpy as np

GCC_ZONE_FACTORS = {
    "hormuz": 1.8,
    "gulf_maritime": 1.5,
    "gcc_aviation": 1.3,
    "gcc_inland": 1.0,
    "gcc_urban": 1.2,
    "gcc_industrial": 1.4,
}

CAT_LOADINGS = {
    "war_risk": 2.5,
    "nat_cat": 1.8,
    "terrorism": 2.0,
    "cyber": 1.6,
    "pandemic": 1.4,
    "supply_chain": 1.3,
}


def compute_portfolio_exposure(policies: list[dict]) -> dict:
    """
    Compute total portfolio exposure with zone and catastrophe type weighting.

    Args:
        policies: List of policy dicts with keys: value, zone, cat_type

    Returns:
        Dictionary with:
        - total_exposure: Sum of weighted exposures
        - zone_breakdown: Exposure by zone
        - policy_count: Number of policies
        - avg_loading: Average loading factor
    """
    total_pe = 0.0
    zone_breakdown = {}

    for policy in policies:
        value = policy.get("value", 0)
        zone = policy.get("zone", "gcc_inland")
        cat = policy.get("cat_type", "supply_chain")

        zone_factor = GCC_ZONE_FACTORS.get(zone, 1.0)
        cat_loading = CAT_LOADINGS.get(cat, 1.0)

        pe = value * zone_factor * cat_loading
        total_pe += pe

        zone_breakdown[zone] = zone_breakdown.get(zone, 0) + pe

    total_value = sum(p.get("value", 0) for p in policies)
    avg_loading = total_pe / max(total_value, 1)

    return {
        "total_exposure": total_pe,
        "zone_breakdown": zone_breakdown,
        "policy_count": len(policies),
        "avg_loading": avg_loading,
    }
