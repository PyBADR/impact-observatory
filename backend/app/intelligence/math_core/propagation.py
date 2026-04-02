"""Propagation mathematics — wraps the core engine with scoring."""
import numpy as np


def compute_system_energy(impacts: dict[str, float]) -> float:
    """E_sys = SUM(x_i^2)"""
    return float(np.sum([v**2 for v in impacts.values()]))


def compute_propagation_depth(iteration_snapshots: list[dict]) -> int:
    max_depth = 0
    prev_affected = 0
    for snap in iteration_snapshots:
        affected = sum(1 for v in snap.get("impacts", {}).values() if abs(v) > 0.01)
        if affected > prev_affected:
            max_depth = snap.get("iteration", 0)
        prev_affected = affected
    return max_depth


def compute_sector_spread(affected_sectors: list[dict]) -> int:
    return len([s for s in affected_sectors if s.get("avg_impact", 0) > 0.01])
