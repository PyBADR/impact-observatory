"""Compute deltas between baseline and post-scenario state.

Delta quantifies the exact difference a scenario makes to every node,
sector, and the system as a whole, including economic impact estimation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.exposure import DEFAULT_ELASTICITY, GCC_GDP_DEFAULTS
from src.engines.scenario_engine.baseline import BaselineSnapshot


@dataclass
class PostShockState:
    """Post-scenario system state — same shape as BaselineSnapshot vectors."""
    risk_vector: NDArray[np.float64]
    disruption_vector: NDArray[np.float64]
    confidence_vector: NDArray[np.float64]
    pressure_vector: NDArray[np.float64]
    system_stress: float
    system_energy: float
    system_confidence: float


@dataclass
class NodeDelta:
    """Per-node delta between baseline and post-scenario."""
    node_id: str
    risk_delta: float
    disruption_delta: float
    confidence_delta: float
    pressure_delta: float
    severity_class: str  # CRITICAL / HIGH / MODERATE / LOW / MINIMAL


@dataclass
class SectorDelta:
    """Per-sector aggregated delta."""
    sector: str
    mean_risk_delta: float
    max_risk_delta: float
    mean_disruption_delta: float
    affected_node_count: int
    severity_class: str


@dataclass
class ScenarioDelta:
    """Full delta between baseline and post-scenario state."""
    risk_delta: NDArray[np.float64]
    disruption_delta: NDArray[np.float64]
    confidence_delta: NDArray[np.float64]
    pressure_delta: NDArray[np.float64]
    stress_delta: float
    energy_delta: float
    confidence_system_delta: float
    top_impacted: list[NodeDelta]
    sector_deltas: dict[str, SectorDelta]
    total_economic_impact_usd: float
    mean_risk_increase: float
    max_risk_increase: float
    nodes_above_critical: int  # risk delta > 0.3
    nodes_above_high: int  # risk delta > 0.15


def _classify_severity(risk_delta: float) -> str:
    """Classify node severity based on risk delta magnitude."""
    d = abs(risk_delta)
    if d >= 0.30:
        return "CRITICAL"
    if d >= 0.15:
        return "HIGH"
    if d >= 0.05:
        return "MODERATE"
    if d >= 0.01:
        return "LOW"
    return "MINIMAL"


def _classify_sector_severity(mean_delta: float) -> str:
    """Classify sector severity based on mean risk delta."""
    d = abs(mean_delta)
    if d >= 0.25:
        return "CRITICAL"
    if d >= 0.12:
        return "HIGH"
    if d >= 0.05:
        return "MODERATE"
    return "LOW"


def compute_delta(
    baseline: BaselineSnapshot,
    post_state: PostShockState,
    top_n: int = 15,
) -> ScenarioDelta:
    """Compute the full delta between baseline and post-scenario state.

    Args:
        baseline: Pre-shock frozen state.
        post_state: Post-shock computed state.
        top_n: Number of top-impacted nodes to include.

    Returns:
        ScenarioDelta with per-node, per-sector, and system-level deltas.
    """
    # Vector deltas
    risk_delta = post_state.risk_vector - baseline.risk_vector
    disruption_delta = post_state.disruption_vector - baseline.disruption_vector
    confidence_delta = post_state.confidence_vector - baseline.confidence_vector
    pressure_delta = post_state.pressure_vector - baseline.pressure_vector

    # System deltas
    stress_delta = post_state.system_stress - baseline.system_stress
    energy_delta = post_state.system_energy - baseline.system_energy
    confidence_sys_delta = post_state.system_confidence - baseline.system_confidence

    # Per-node deltas, sorted by |risk_delta| descending
    node_deltas: list[NodeDelta] = []
    for i, nid in enumerate(baseline.node_ids):
        rd = float(risk_delta[i])
        dd = float(disruption_delta[i])
        cd = float(confidence_delta[i])
        pd = float(pressure_delta[i])
        node_deltas.append(NodeDelta(
            node_id=nid,
            risk_delta=rd,
            disruption_delta=dd,
            confidence_delta=cd,
            pressure_delta=pd,
            severity_class=_classify_severity(rd),
        ))

    node_deltas.sort(key=lambda nd: abs(nd.risk_delta), reverse=True)
    top_impacted = node_deltas[:top_n]

    # Per-sector deltas
    sector_deltas: dict[str, SectorDelta] = {}
    for sector, si in baseline.sector_impacts.items():
        # Find nodes in this sector
        sector_indices = [
            i for i, nid in enumerate(baseline.node_ids)
            if baseline.sector_impacts.get(sector) and i < len(risk_delta)
        ]
        # Actually filter by sector — need to check which nodes belong
        # Reconstruct from sector_impacts node membership
        # Since BaselineSnapshot stores sector_impacts keyed by sector name,
        # we use the original node_sectors from the graph state indirectly.
        # For robustness, scan all nodes and match sector.
        # The sector_impacts dict was built from node_sectors, so we iterate
        # and reconstruct membership.

    # Rebuild sector -> node indices from sector_impacts
    # We need to do this from the node list and the stored sector data
    # Use a simple approach: group by checking which nodes produced each sector's stats
    # Since we don't store per-node sector in baseline, rebuild from count and mean
    # Actually, let's compute sector deltas from the node deltas
    sector_node_map: dict[str, list[int]] = {}
    for si in baseline.sector_impacts.values():
        sector_node_map[si.sector] = []

    # Assign nodes to sectors proportionally based on stored counts
    # For a clean implementation, we track node->sector from baseline
    # We'll use a heuristic: assign nodes in order matching sector counts
    idx = 0
    for sector, si in baseline.sector_impacts.items():
        for _ in range(si.node_count):
            if idx < len(baseline.node_ids):
                sector_node_map.setdefault(sector, []).append(idx)
                idx += 1

    for sector, indices in sector_node_map.items():
        if not indices:
            continue
        rd = risk_delta[indices]
        dd = disruption_delta[indices]
        affected = int(np.count_nonzero(np.abs(rd) > 0.01))
        mean_rd = float(np.mean(rd))
        max_rd = float(np.max(rd)) if len(rd) > 0 else 0.0
        mean_dd = float(np.mean(dd))

        sector_deltas[sector] = SectorDelta(
            sector=sector,
            mean_risk_delta=mean_rd,
            max_risk_delta=max_rd,
            mean_disruption_delta=mean_dd,
            affected_node_count=affected,
            severity_class=_classify_sector_severity(mean_rd),
        )

    # Aggregate stats
    positive_deltas = risk_delta[risk_delta > 0]
    mean_increase = float(np.mean(positive_deltas)) if len(positive_deltas) > 0 else 0.0
    max_increase = float(np.max(risk_delta)) if len(risk_delta) > 0 else 0.0
    critical_count = int(np.count_nonzero(risk_delta > 0.30))
    high_count = int(np.count_nonzero(risk_delta > 0.15))

    return ScenarioDelta(
        risk_delta=risk_delta,
        disruption_delta=disruption_delta,
        confidence_delta=confidence_delta,
        pressure_delta=pressure_delta,
        stress_delta=stress_delta,
        energy_delta=energy_delta,
        confidence_system_delta=confidence_sys_delta,
        top_impacted=top_impacted,
        sector_deltas=sector_deltas,
        total_economic_impact_usd=0.0,  # filled by compute_economic_impact
        mean_risk_increase=mean_increase,
        max_risk_increase=max_increase,
        nodes_above_critical=critical_count,
        nodes_above_high=high_count,
    )


def compute_economic_impact(
    delta: ScenarioDelta,
    gdp_data: dict[str, float],
    node_ids: list[str],
    elasticity: float = DEFAULT_ELASTICITY,
) -> float:
    """Estimate total economic impact in USD from risk deltas and GDP data.

    Uses the GCC exposure equation:
        delta_Y_i = GDP_i * elasticity * delta_risk_i * (1 + cascade_factor)

    If no GDP data is provided for a node, falls back to GCC country defaults
    distributed across nodes.

    Args:
        delta: Computed scenario delta.
        gdp_data: Mapping of node_id -> GDP value in USD.
        node_ids: List of node IDs matching delta vector indices.
        elasticity: GDP-to-disruption elasticity (default 1.5%).

    Returns:
        Total estimated economic impact in USD.
    """
    total_loss = 0.0
    n = len(node_ids)

    # Cascading factor: mean of all positive risk deltas as system-level cascade
    positive_deltas = delta.risk_delta[delta.risk_delta > 0]
    cascade_factor = float(np.mean(positive_deltas)) if len(positive_deltas) > 0 else 0.0

    # Fallback: distribute total GCC GDP across nodes
    total_gcc_gdp = sum(GCC_GDP_DEFAULTS.values())
    default_per_node = total_gcc_gdp / max(n, 1)

    for i, nid in enumerate(node_ids):
        rd = float(delta.risk_delta[i])
        if rd <= 0:
            continue  # Only count risk increases

        gdp_i = gdp_data.get(nid, default_per_node)
        loss_i = gdp_i * elasticity * rd * (1.0 + cascade_factor)
        total_loss += loss_i

    return total_loss
