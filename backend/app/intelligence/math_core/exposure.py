"""Exposure scoring: E = SUM(value * impact * prob)"""
from ..engines.gcc_constants import SECTOR_GDP_BASE


def compute_exposure_score(node_values: dict[str, float], node_impacts: dict[str, float], node_probs: dict[str, float] = None) -> float:
    total = 0.0
    for node_id, value in node_values.items():
        impact = abs(node_impacts.get(node_id, 0))
        prob = node_probs.get(node_id, 1.0) if node_probs else 1.0
        total += value * impact * prob
    return total


def compute_sector_exposure(sector_impacts: dict[str, float]) -> dict:
    exposure = {}
    for sector, impact in sector_impacts.items():
        base = SECTOR_GDP_BASE.get(sector, 0)
        exposure[sector] = base * abs(impact)
    return {"sector_exposure": exposure, "total": sum(exposure.values())}
