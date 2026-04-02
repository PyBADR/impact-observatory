"""GCC-tuned potential routing — route scoring with exact theta weights.

Uses PotentialRoutingWeights (theta1=0.18, theta2=0.22, theta3=0.28,
theta4=0.20, theta5=0.12) from gcc_weights.

Route cost:
    C(route) = theta1*distance + theta2*time + theta3*threat_integral
               + theta4*friction + theta5*congestion

Returns ranked alternative routes with full per-segment explanation.
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
class SegmentScore:
    """Score breakdown for a single route segment."""
    from_node: str
    to_node: str
    distance_component: float
    time_component: float
    threat_component: float
    friction_component: float
    congestion_component: float
    segment_cost: float


@dataclass
class RouteScore:
    """Full score for a route alternative."""
    route_index: int
    route_nodes: list[str]
    total_cost: float
    avg_cost_per_segment: float
    segments: list[SegmentScore]
    dominant_cost_factor: str
    factor_totals: dict[str, float]


@dataclass
class GCCRoutingResult:
    """Full routing result with ranked alternatives."""
    ranked_routes: list[RouteScore]
    best_route_index: int
    worst_route_index: int
    cost_spread: float  # difference between worst and best
    weights_used: dict[str, float]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_routing_potential(
    routes: list[list[str]],
    risk_data: dict[str, float] | None = None,
    friction_data: dict[str, float] | None = None,
    congestion_data: dict[str, float] | None = None,
    edge_distances: dict[tuple[str, str], float] | None = None,
    edge_times: dict[tuple[str, str], float] | None = None,
    weights: PotentialRoutingWeights | None = None,
) -> GCCRoutingResult:
    """Compute GCC-tuned routing potential for a set of alternative routes.

    Args:
        routes: List of route alternatives, each a list of node IDs in order.
        risk_data: {node_id: threat_value [0, 1]}
        friction_data: {node_id or corridor_id: friction_value [0, 1]}
        congestion_data: {node_id: congestion_level [0, 1]}
        edge_distances: {(from, to): distance_km} -- if missing, defaults to 100 km.
        edge_times: {(from, to): travel_time_h} -- if missing, defaults to 1 h.
        weights: PotentialRoutingWeights override (default: GCC singleton).

    Returns:
        GCCRoutingResult with ranked routes and full explanation.
    """
    w = weights or POTENTIAL_ROUTING
    risk = risk_data or {}
    friction = friction_data or {}
    congestion = congestion_data or {}
    distances = edge_distances or {}
    times = edge_times or {}

    # Normalization references (for scaling raw values to [0, 1] range)
    max_distance = max(distances.values(), default=100.0) or 100.0
    max_time = max(times.values(), default=1.0) or 1.0

    route_scores: list[RouteScore] = []

    for route_idx, route in enumerate(routes):
        segments: list[SegmentScore] = []
        factor_totals: dict[str, float] = {
            "distance": 0.0,
            "time": 0.0,
            "threat": 0.0,
            "friction": 0.0,
            "congestion": 0.0,
        }

        if len(route) < 2:
            # Degenerate route: single node or empty
            route_scores.append(RouteScore(
                route_index=route_idx,
                route_nodes=route,
                total_cost=0.0,
                avg_cost_per_segment=0.0,
                segments=[],
                dominant_cost_factor="none",
                factor_totals=factor_totals,
            ))
            continue

        total_cost = 0.0

        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]

            # Raw values
            raw_dist = distances.get((from_node, to_node), 100.0)
            raw_time = times.get((from_node, to_node), 1.0)
            avg_threat = 0.5 * (risk.get(from_node, 0.0) + risk.get(to_node, 0.0))
            avg_friction = 0.5 * (friction.get(from_node, 0.0) + friction.get(to_node, 0.0))
            avg_congestion = 0.5 * (congestion.get(from_node, 0.0) + congestion.get(to_node, 0.0))

            # Normalized to [0, 1]
            norm_dist = raw_dist / max_distance
            norm_time = raw_time / max_time

            # GCC-weighted segment cost
            d_comp = w.distance * norm_dist
            t_comp = w.time * norm_time
            th_comp = w.threat_integral * avg_threat
            f_comp = w.friction * avg_friction
            c_comp = w.congestion * avg_congestion

            seg_cost = d_comp + t_comp + th_comp + f_comp + c_comp

            segments.append(SegmentScore(
                from_node=from_node,
                to_node=to_node,
                distance_component=d_comp,
                time_component=t_comp,
                threat_component=th_comp,
                friction_component=f_comp,
                congestion_component=c_comp,
                segment_cost=seg_cost,
            ))

            total_cost += seg_cost
            factor_totals["distance"] += d_comp
            factor_totals["time"] += t_comp
            factor_totals["threat"] += th_comp
            factor_totals["friction"] += f_comp
            factor_totals["congestion"] += c_comp

        n_segments = len(segments)
        avg_cost = total_cost / n_segments if n_segments > 0 else 0.0

        # Dominant factor
        dominant = max(factor_totals, key=factor_totals.get)  # type: ignore[arg-type]

        route_scores.append(RouteScore(
            route_index=route_idx,
            route_nodes=route,
            total_cost=total_cost,
            avg_cost_per_segment=avg_cost,
            segments=segments,
            dominant_cost_factor=dominant,
            factor_totals=factor_totals,
        ))

    # Rank by total cost (ascending = best first)
    route_scores.sort(key=lambda rs: rs.total_cost)

    best_idx = route_scores[0].route_index if route_scores else -1
    worst_idx = route_scores[-1].route_index if route_scores else -1
    cost_spread = (route_scores[-1].total_cost - route_scores[0].total_cost) if len(route_scores) > 1 else 0.0

    return GCCRoutingResult(
        ranked_routes=route_scores,
        best_route_index=best_idx,
        worst_route_index=worst_idx,
        cost_spread=cost_spread,
        weights_used={
            "theta1_distance": w.distance,
            "theta2_time": w.time,
            "theta3_threat_integral": w.threat_integral,
            "theta4_friction": w.friction,
            "theta5_congestion": w.congestion,
        },
    )
