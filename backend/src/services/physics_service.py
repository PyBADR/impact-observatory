"""Service 2: physics_service — Flow Impact (أثر التدفق).

Wraps existing physics engines (threat_field, shockwave, pressure, flow_field,
friction, system_stress) into a single service that computes FlowState per entity.
"""

from __future__ import annotations

import logging
import math

from src.schemas.flow_state import FlowState

logger = logging.getLogger(__name__)


def compute_flow_states(
    entities: list[dict],
    edges: list[dict],
    shock_nodes: list[str],
    severity: float,
    horizon_hours: int,
) -> list[FlowState]:
    """Compute physics flow state for each entity given shocks.

    Uses existing engine formulas:
    - Threat field: T(r) = S * exp(-λ*d) where λ=0.005, d=graph distance
    - Shockwave: W(t) = α * Σ(A_ij * W_j(t-1)) + β * shock
    - Pressure: P(t) = ρ*P(t-1) + κ*inflow - ω*outflow + ξ*shock
    - Friction: μ = base + threat*0.35 + congestion*0.25 + political*0.25 + regulatory*0.15
    - System stress: σ = 0.35*congestion + 0.30*risk + 0.20*uncertainty + 0.15*insurance
    """
    entity_index = {e["id"]: i for i, e in enumerate(entities)}
    n = len(entities)

    # Build adjacency
    adj: dict[str, list[str]] = {e["id"]: [] for e in entities}
    for edge in edges:
        src = edge.get("source") or edge.get("source_id", "")
        tgt = edge.get("target") or edge.get("target_id", "")
        if src in adj:
            adj[src].append(tgt)

    # BFS distance from shock nodes
    distances: dict[str, int] = {}
    queue = list(shock_nodes)
    for nid in shock_nodes:
        distances[nid] = 0
    while queue:
        current = queue.pop(0)
        for neighbor in adj.get(current, []):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)

    results = []
    for entity in entities:
        eid = entity["id"]
        dist = distances.get(eid, 999)

        # Threat field: T(r) = severity * exp(-0.005 * dist_hops * 100km_equiv)
        threat = severity * math.exp(-0.005 * dist * 100) if dist < 999 else 0.0

        # Shockwave amplitude: decays with hop distance
        # α=0.58, β=0.92
        if dist == 0:
            shockwave = severity * 0.92
        elif dist < 999:
            shockwave = severity * 0.92 * (0.58 ** dist)
        else:
            shockwave = 0.0

        # Pressure accumulation: P = ρ*baseline + κ*inflow + ξ*shock
        # ρ=0.72, κ=0.18, ξ=0.30
        baseline_pressure = entity.get("criticality", 0.5) * 0.1
        inflow = sum(1 for e in edges if (e.get("target") or e.get("target_id")) == eid) / max(len(edges), 1)
        shock_contribution = severity if eid in shock_nodes else shockwave * 0.3
        pressure = min(0.72 * baseline_pressure + 0.18 * inflow + 0.30 * shock_contribution, 1.0)

        # Flow magnitude
        outflow = sum(1 for e in edges if (e.get("source") or e.get("source_id")) == eid) / max(len(edges), 1)
        flow_mag = min((inflow + outflow) * (1.0 + threat), 1.0)

        # Friction: μ = 0.35*threat + 0.25*congestion_proxy + 0.25*political + 0.15*regulatory
        congestion_proxy = pressure * 0.5
        friction = min(0.35 * threat + 0.25 * congestion_proxy + 0.25 * severity * 0.3 + 0.15 * 0.1, 1.0)

        # System stress: σ = 0.35*congestion + 0.30*risk + 0.20*uncertainty + 0.15*insurance_severity
        system_stress = min(
            0.35 * congestion_proxy + 0.30 * threat + 0.20 * 0.3 + 0.15 * shockwave * 0.5,
            1.0,
        )

        # Route efficiency: Flow(t) = Capacity × Availability × RouteEfficiency
        route_efficiency = 1.0 - friction

        # Delay(t) = BaseDelay × CongestionFactor
        # BaseDelay depends on entity type
        entity_type = entity.get("type", "").lower()
        if entity_type in ("maritime", "shipping", "port", "vessel"):
            base_delay = 48.0
        elif entity_type in ("aviation", "airline", "airport", "flight"):
            base_delay = 6.0
        elif entity_type in ("financial", "bank", "insurance", "finance"):
            base_delay = 2.0
        elif entity_type in ("energy", "infrastructure", "pipeline", "grid", "power"):
            base_delay = 24.0
        else:
            base_delay = 12.0
        # CongestionFactor ranges from 1.0 to 4.0
        congestion_factor = min(1.0 + congestion_proxy * 3.0, 4.0)
        delay_hours = base_delay * congestion_factor

        results.append(FlowState(
            entity_id=eid,
            timestep_hours=float(horizon_hours),
            pressure=round(pressure, 4),
            flow_magnitude=round(flow_mag, 4),
            threat_level=round(threat, 4),
            shockwave_amplitude=round(shockwave, 4),
            friction=round(friction, 4),
            system_stress=round(system_stress, 4),
            route_efficiency=round(route_efficiency, 4),
            delay_hours=round(delay_hours, 2),
        ))

    return results
