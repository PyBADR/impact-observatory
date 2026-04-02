"""GCC-tuned flow field — models traffic flow with calibrated routing weights.

Uses PotentialRoutingWeights (theta1-5) from gcc_weights to weight flow
components. Identifies congestion zones with explainability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    POTENTIAL_ROUTING,
    PotentialRoutingWeights,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class NodeFlowVector:
    """Aggregated flow vector at a node."""
    node_id: str
    flow_vx: float
    flow_vy: float
    magnitude: float
    density: float
    congestion_score: float


@dataclass
class CongestionZone:
    """Detected congestion zone."""
    node_id: str
    congestion_score: float
    contributing_factors: dict[str, float]


@dataclass
class GCCFlowFieldResult:
    """Full flow field result."""
    node_flows: dict[str, NodeFlowVector]
    congestion_zones: list[CongestionZone]
    mean_flow_magnitude: float
    max_congestion: float
    weights_used: dict[str, float]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_flow_field(
    nodes: dict[str, dict],
    edges: list[dict],
    risk_vector: dict[str, float] | None = None,
    weights: PotentialRoutingWeights | None = None,
    congestion_threshold: float = 0.6,
) -> GCCFlowFieldResult:
    """Compute GCC-tuned flow field across a node-edge network.

    Args:
        nodes: {node_id: {"lat": float, "lng": float, "capacity": float, "current_traffic": float}}
        edges: [{"from": node_id, "to": node_id, "distance_km": float, "travel_time_h": float,
                 "traffic_volume": float}]
        risk_vector: {node_id: risk_value} optional per-node risk.
        weights: PotentialRoutingWeights override (default: GCC singleton).
        congestion_threshold: score above which a node is flagged as congested.

    Returns:
        GCCFlowFieldResult with per-node flow vectors and congestion zones.
    """
    w = weights or POTENTIAL_ROUTING
    risk = risk_vector or {}

    node_ids = list(nodes.keys())
    n = len(node_ids)
    id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

    # Accumulate flow vectors per node from edges
    flow_vx = np.zeros(n, dtype=np.float64)
    flow_vy = np.zeros(n, dtype=np.float64)
    inflow_count = np.zeros(n, dtype=np.float64)
    outflow_count = np.zeros(n, dtype=np.float64)

    # Edge-level aggregated cost for congestion scoring
    edge_load = np.zeros(n, dtype=np.float64)  # traffic pressure per node

    for edge in edges:
        src_id = edge["from"]
        dst_id = edge["to"]
        if src_id not in id_to_idx or dst_id not in id_to_idx:
            continue

        src_idx = id_to_idx[src_id]
        dst_idx = id_to_idx[dst_id]
        src_node = nodes[src_id]
        dst_node = nodes[dst_id]

        # Direction vector (lat/lng difference as proxy)
        dlat = dst_node["lat"] - src_node["lat"]
        dlng = dst_node["lng"] - src_node["lng"]
        dist = np.sqrt(dlat ** 2 + dlng ** 2) + 1e-9

        volume = edge.get("traffic_volume", 1.0)
        travel_time = edge.get("travel_time_h", 1.0)
        distance_km = edge.get("distance_km", 1.0)

        # Normalize direction, scale by volume
        vx = (dlng / dist) * volume
        vy = (dlat / dist) * volume

        # Weighted edge cost using GCC theta weights
        threat_at_edge = 0.5 * (risk.get(src_id, 0.0) + risk.get(dst_id, 0.0))
        edge_cost = (
            w.distance * (distance_km / (distance_km + 100.0))  # normalized distance component
            + w.time * (travel_time / (travel_time + 1.0))  # normalized time component
            + w.threat_integral * threat_at_edge
            + w.congestion * (volume / (volume + 10.0))  # normalized congestion proxy
        )

        # Accumulate at source (outflow) and destination (inflow)
        flow_vx[src_idx] += vx
        flow_vy[src_idx] += vy
        outflow_count[src_idx] += volume
        inflow_count[dst_idx] += volume
        edge_load[src_idx] += edge_cost
        edge_load[dst_idx] += edge_cost

    # Per-node results
    magnitudes = np.sqrt(flow_vx ** 2 + flow_vy ** 2)

    # Congestion score per node: combines capacity utilization and edge load
    congestion_scores = np.zeros(n, dtype=np.float64)
    for i, nid in enumerate(node_ids):
        capacity = nodes[nid].get("capacity", 100.0)
        current = nodes[nid].get("current_traffic", 0.0)
        utilization = min(current / max(capacity, 1.0), 2.0)

        # GCC-weighted congestion:
        # w.congestion * utilization + w.threat_integral * risk + w.friction * edge_load_norm
        node_risk = risk.get(nid, 0.0)
        edge_load_norm = float(edge_load[i] / max(edge_load.max(), 1e-9))

        cong = (
            w.congestion * utilization
            + w.threat_integral * node_risk
            + w.friction * edge_load_norm
            + w.distance * (1.0 - 1.0 / (1.0 + 0.1 * (inflow_count[i] + outflow_count[i])))
        )
        congestion_scores[i] = float(np.clip(cong, 0.0, 1.0))

    # Build results
    node_flows: dict[str, NodeFlowVector] = {}
    for i, nid in enumerate(node_ids):
        density = float(inflow_count[i] + outflow_count[i])
        node_flows[nid] = NodeFlowVector(
            node_id=nid,
            flow_vx=float(flow_vx[i]),
            flow_vy=float(flow_vy[i]),
            magnitude=float(magnitudes[i]),
            density=density,
            congestion_score=float(congestion_scores[i]),
        )

    # Congestion zones
    congestion_zones: list[CongestionZone] = []
    for i, nid in enumerate(node_ids):
        if congestion_scores[i] >= congestion_threshold:
            capacity = nodes[nid].get("capacity", 100.0)
            current = nodes[nid].get("current_traffic", 0.0)
            utilization = min(current / max(capacity, 1.0), 2.0)
            node_risk = risk.get(nid, 0.0)
            edge_load_norm = float(edge_load[i] / max(edge_load.max(), 1e-9))

            congestion_zones.append(CongestionZone(
                node_id=nid,
                congestion_score=float(congestion_scores[i]),
                contributing_factors={
                    "utilization_component": float(w.congestion * utilization),
                    "threat_component": float(w.threat_integral * node_risk),
                    "friction_component": float(w.friction * edge_load_norm),
                    "traffic_density_component": float(
                        w.distance * (1.0 - 1.0 / (1.0 + 0.1 * (inflow_count[i] + outflow_count[i])))
                    ),
                },
            ))

    congestion_zones.sort(key=lambda z: z.congestion_score, reverse=True)

    return GCCFlowFieldResult(
        node_flows=node_flows,
        congestion_zones=congestion_zones,
        mean_flow_magnitude=float(np.mean(magnitudes)) if n > 0 else 0.0,
        max_congestion=float(np.max(congestion_scores)) if n > 0 else 0.0,
        weights_used={
            "theta1_distance": w.distance,
            "theta2_time": w.time,
            "theta3_threat_integral": w.threat_integral,
            "theta4_friction": w.friction,
            "theta5_congestion": w.congestion,
        },
    )
