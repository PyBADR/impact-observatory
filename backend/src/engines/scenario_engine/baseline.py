"""Capture baseline system state before scenario injection.

The baseline snapshot freezes the pre-shock state of the intelligence graph
so that post-scenario deltas can be computed accurately.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.propagation import compute_system_energy
from src.engines.math_core.disruption import compute_disruption_vector
from src.engines.math_core.confidence import compute_confidence_vector, compute_system_confidence
from src.engines.scenario.engine import GraphState


@dataclass
class SectorImpact:
    """Aggregated impact metrics for a single sector."""
    sector: str
    mean_risk: float
    max_risk: float
    node_count: int
    exposure_weight: float


@dataclass
class BaselineSnapshot:
    """Frozen pre-shock state of the intelligence graph.

    All vectors are numpy arrays of length N (number of nodes).
    """
    node_ids: list[str]
    node_index: dict[str, int]
    risk_vector: NDArray[np.float64]
    disruption_vector: NDArray[np.float64]
    confidence_vector: NDArray[np.float64]
    exposure_vector: NDArray[np.float64]
    pressure_vector: NDArray[np.float64]
    system_stress: float
    system_energy: float
    system_confidence: float
    sector_impacts: dict[str, SectorImpact]
    timestamp: datetime

    @property
    def n_nodes(self) -> int:
        return len(self.node_ids)

    def risk_for(self, node_id: str) -> float:
        """Look up baseline risk for a node by ID."""
        idx = self.node_index.get(node_id)
        if idx is None:
            return 0.0
        return float(self.risk_vector[idx])

    def sector_mean_risk(self, sector: str) -> float:
        """Mean baseline risk for a sector."""
        si = self.sector_impacts.get(sector)
        return si.mean_risk if si else 0.0


def _compute_sector_impacts(
    node_ids: list[str],
    risk_vector: NDArray[np.float64],
    node_sectors: list[str],
    sector_weights: dict[str, float],
) -> dict[str, SectorImpact]:
    """Aggregate risk by sector."""
    sector_nodes: dict[str, list[int]] = {}
    for i, sector in enumerate(node_sectors):
        sector_nodes.setdefault(sector, []).append(i)

    impacts: dict[str, SectorImpact] = {}
    for sector, indices in sector_nodes.items():
        risks = risk_vector[indices]
        impacts[sector] = SectorImpact(
            sector=sector,
            mean_risk=float(np.mean(risks)),
            max_risk=float(np.max(risks)),
            node_count=len(indices),
            exposure_weight=sector_weights.get(sector, 1.0 / max(len(sector_nodes), 1)),
        )

    return impacts


def capture_baseline(
    graph_state: GraphState,
    risk_vector: NDArray[np.float64] | None = None,
    disruption_vector: NDArray[np.float64] | None = None,
    confidence_vector: NDArray[np.float64] | None = None,
    exposure_vector: NDArray[np.float64] | None = None,
    pressure_vector: NDArray[np.float64] | None = None,
) -> BaselineSnapshot:
    """Capture or synthesize a baseline snapshot from the current graph state.

    If specific vectors are not supplied, sensible defaults are computed:
    - risk: uses graph_state.baseline_risk or uniform 0.05
    - disruption: derived from risk via disruption weights
    - confidence: uniform 0.8 (high confidence default)
    - exposure: uniform 0.3 (moderate exposure default)
    - pressure: uniform 0.1 (low pressure default)
    """
    n = len(graph_state.node_ids)
    node_index = {nid: i for i, nid in enumerate(graph_state.node_ids)}

    # --- Risk vector ---
    if risk_vector is not None:
        rv = risk_vector.copy()
    elif graph_state.baseline_risk is not None:
        rv = graph_state.baseline_risk.copy()
    else:
        rv = np.full(n, 0.05, dtype=np.float64)

    # --- Disruption vector ---
    if disruption_vector is not None:
        dv = disruption_vector.copy()
    else:
        # Derive disruption from risk using the canonical disruption equation
        dv, _ = compute_disruption_vector(
            graph_state.node_ids,
            rv,
        )

    # --- Confidence vector ---
    if confidence_vector is not None:
        cv = confidence_vector.copy()
    else:
        cv = np.full(n, 0.80, dtype=np.float64)

    # --- Exposure vector ---
    if exposure_vector is not None:
        ev = exposure_vector.copy()
    else:
        ev = np.full(n, 0.30, dtype=np.float64)

    # --- Pressure vector ---
    if pressure_vector is not None:
        pv = pressure_vector.copy()
    else:
        pv = np.full(n, 0.10, dtype=np.float64)

    # --- System-level metrics ---
    sys_energy = compute_system_energy(rv)
    sys_stress = float(np.mean(rv) + 0.5 * float(np.std(rv)))  # mean + half-sigma
    sys_confidence = compute_system_confidence(rv, cv)

    # --- Sector impacts ---
    node_sectors = graph_state.node_sectors if graph_state.node_sectors else ["unknown"] * n
    sector_weights = graph_state.sector_weights if graph_state.sector_weights else {}
    sector_impacts = _compute_sector_impacts(
        graph_state.node_ids, rv, node_sectors, sector_weights,
    )

    return BaselineSnapshot(
        node_ids=list(graph_state.node_ids),
        node_index=node_index,
        risk_vector=rv,
        disruption_vector=dv,
        confidence_vector=cv,
        exposure_vector=ev,
        pressure_vector=pv,
        system_stress=sys_stress,
        system_energy=sys_energy,
        system_confidence=sys_confidence,
        sector_impacts=sector_impacts,
        timestamp=datetime.utcnow(),
    )
