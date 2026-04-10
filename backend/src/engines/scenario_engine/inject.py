"""Inject scenario shocks into the system.

Shock injection converts scenario definitions into numerical shock vectors,
applies geopolitical event multipliers, and propagates through the adjacency
structure for multi-hop impact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import EVENT_MULTIPLIERS
from src.engines.scenario_engine.baseline import BaselineSnapshot
from src.models.canonical import Scenario, ScenarioShock, DisruptionType


# Map DisruptionType to the closest EVENT_MULTIPLIERS key
_DISRUPTION_TO_EVENT: dict[DisruptionType, str] = {
    DisruptionType.CLOSURE: "port_closure",
    DisruptionType.BLOCKADE: "chokepoint_threat",
    DisruptionType.DAMAGE: "infrastructure_damage",
    DisruptionType.ESCALATION: "missile_strike",
    DisruptionType.REROUTE: "airport_shutdown",
    DisruptionType.DELAY: "sanctions_escalation",
    DisruptionType.CONGESTION: "protest_near_infra",
}


@dataclass
class ShockInjection:
    """Result of injecting a single shock into the system."""
    target_node_ids: list[str]
    severity: float
    event_type: str
    event_multiplier: float
    propagation_hops: int
    raw_shock_vector: NDArray[np.float64]
    amplified_shock_vector: NDArray[np.float64]
    affected_node_count: int


@dataclass
class InjectionResult:
    """Aggregate result of all shock injections for a scenario."""
    injections: list[ShockInjection]
    combined_shock_vector: NDArray[np.float64]
    modified_risk_vector: NDArray[np.float64]
    total_shock_energy: float
    direct_hit_count: int
    cascade_hit_count: int


def _resolve_event_key(shock_type: DisruptionType, description: str = "") -> str:
    """Resolve the EVENT_MULTIPLIERS key from disruption type and description."""
    desc_lower = description.lower()

    # Try to match description keywords first for precision
    if "missile" in desc_lower or "strike" in desc_lower:
        return "missile_strike"
    if "naval" in desc_lower or "vessel" in desc_lower:
        return "naval_attack"
    if "airspace" in desc_lower and ("strike" in desc_lower or "shut" in desc_lower):
        return "airspace_strike"
    if "cyber" in desc_lower:
        return "cyber_attack"
    if "rumor" in desc_lower or "unconfirm" in desc_lower or "false" in desc_lower:
        return "rumor_unverified"
    if "exercise" in desc_lower or "military" in desc_lower:
        return "military_exercise"
    if "diplomatic" in desc_lower:
        return "diplomatic_tension"
    if "protest" in desc_lower:
        return "protest_civil_unrest"

    # Fall back to type-based mapping
    return _DISRUPTION_TO_EVENT.get(shock_type, "sanctions_escalation")


def inject_shock(
    baseline: BaselineSnapshot,
    shock: ScenarioShock,
    adjacency: NDArray[np.float64],
    propagation_hops: int = 3,
) -> ShockInjection:
    """Inject a single shock into the system and propagate through adjacency.

    Steps:
    1. Create raw shock vector with severity at target node
    2. Look up event multiplier M_e from gcc_weights
    3. Amplify: amplified = severity * M_e
    4. Propagate through adjacency for `propagation_hops` hops with decay

    Returns a ShockInjection with both raw and amplified vectors.
    """
    n = baseline.n_nodes
    raw = np.zeros(n, dtype=np.float64)
    amplified = np.zeros(n, dtype=np.float64)

    # Resolve target index
    idx = baseline.node_index.get(shock.target_entity_id)
    target_ids = [shock.target_entity_id]

    # Determine event multiplier
    event_key = _resolve_event_key(shock.shock_type, shock.description)
    M_e = EVENT_MULTIPLIERS.get(event_key, 1.0)

    if idx is not None:
        raw[idx] = shock.severity_score
        amplified[idx] = min(shock.severity_score * M_e, 1.0)

        # Multi-hop propagation through adjacency with geometric decay
        current = amplified.copy()
        for hop in range(propagation_hops):
            decay = 0.5 ** (hop + 1)  # 0.5, 0.25, 0.125, ...
            propagated = adjacency.T @ current * decay
            amplified = np.maximum(amplified, propagated)
            current = propagated

    amplified = np.clip(amplified, 0.0, 1.0)

    affected = int(np.count_nonzero(amplified > 0.01))

    return ShockInjection(
        target_node_ids=target_ids,
        severity=shock.severity_score,
        event_type=event_key,
        event_multiplier=M_e,
        propagation_hops=propagation_hops,
        raw_shock_vector=raw,
        amplified_shock_vector=amplified,
        affected_node_count=affected,
    )


def inject_from_scenario(
    scenario: Scenario,
    graph_state_node_ids: list[str],
    adjacency: NDArray[np.float64],
    baseline: BaselineSnapshot,
    propagation_hops: int = 3,
) -> InjectionResult:
    """Inject all shocks from a Scenario definition.

    Combines individual shock vectors via element-wise maximum (worst case)
    and computes the modified risk vector as baseline + shock, clamped to [0, 1].
    """
    n = baseline.n_nodes
    combined = np.zeros(n, dtype=np.float64)
    injections: list[ShockInjection] = []
    direct_hits: set[int] = set()
    cascade_hits: set[int] = set()

    for shock in scenario.shocks:
        inj = inject_shock(baseline, shock, adjacency, propagation_hops)
        injections.append(inj)

        # Combine via maximum (worst-case overlay)
        combined = np.maximum(combined, inj.amplified_shock_vector)

        # Track direct vs cascade hits
        idx = baseline.node_index.get(shock.target_entity_id)
        if idx is not None:
            direct_hits.add(idx)
        cascade_indices = set(np.where(inj.amplified_shock_vector > 0.01)[0].tolist())
        cascade_hits.update(cascade_indices - direct_hits)

    # Modified risk = baseline risk + shock, clamped
    modified_risk = np.clip(baseline.risk_vector + combined, 0.0, 1.0)

    total_energy = float(np.sqrt(np.sum(combined ** 2)) / max(n, 1))

    return InjectionResult(
        injections=injections,
        combined_shock_vector=combined,
        modified_risk_vector=modified_risk,
        total_shock_energy=total_energy,
        direct_hit_count=len(direct_hits),
        cascade_hit_count=len(cascade_hits),
    )
