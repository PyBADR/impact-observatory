"""
Potential field routing for threat-aware path planning.

Physics metaphor: Threat forms a potential field (like gravitational or electric
potential). Routing algorithms find paths that minimize integrated potential energy
(threat exposure). Low-threat routes have low potential energy, high-threat routes
have high potential energy.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class RouteResult:
    """
    Result of route cost analysis.
    
    Attributes:
        route_id: Identifier for the route
        total_cost: Cumulative cost (base + threat exposure)
        threat_exposure: Integrated threat along route
        segments: List of (lat, lon) waypoints defining the route
        ranking: Relative ranking among all routes evaluated (lower = better)
    """
    route_id: str
    total_cost: float
    threat_exposure: float
    segments: List[Tuple[float, float]]
    ranking: int = 0


def compute_route_cost(
    route_points: List[Tuple[float, float]],
    threat_field,
    base_cost: float = 1.0
) -> Tuple[float, float]:
    """
    Compute total cost of a route incorporating threat exposure.
    
    Physics model: Total cost = base_cost + threat_exposure, where:
        - base_cost: Intrinsic cost (distance, fuel, time) independent of threat
        - threat_exposure: Integral of threat potential along the route path
    
    Threat exposure is computed by sampling threat field at waypoints and
    integrating (using trapezoidal rule for piecewise linear segments).
    
    Args:
        route_points: List of (lat, lon) waypoints defining route path
        threat_field: ThreatField instance with evaluate() method
        base_cost: Baseline cost before threat adjustment [default: 1.0]
        
    Returns:
        Tuple of (total_cost, threat_exposure)
    """
    if not route_points or len(route_points) == 0:
        return base_cost, 0.0

    if len(route_points) == 1:
        # Single point: threat at that point
        lat, lon = route_points[0]
        threat_at_point = threat_field.evaluate(lat, lon)
        return base_cost + threat_at_point, threat_at_point

    # Integrate threat along path using trapezoidal rule
    threat_exposure = 0.0
    for i in range(len(route_points) - 1):
        lat1, lon1 = route_points[i]
        lat2, lon2 = route_points[i + 1]

        # Threat at endpoints
        threat1 = threat_field.evaluate(lat1, lon1)
        threat2 = threat_field.evaluate(lat2, lon2)

        # Approximate segment distance
        dx = (lat2 - lat1) * 111.0
        dy = (lon2 - lon1) * 111.0 * np.cos(np.radians((lat1 + lat2) / 2))
        segment_distance = np.sqrt(dx * dx + dy * dy)

        # Trapezoidal integration
        threat_exposure += (threat1 + threat2) / 2.0 * segment_distance

    total_cost = base_cost + threat_exposure

    return total_cost, threat_exposure


def find_lowest_cost_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    candidate_routes: List[List[Tuple[float, float]]],
    threat_field,
    base_cost: float = 1.0,
    route_ids: List[str] = None
) -> RouteResult:
    """
    Evaluate candidate routes and return the lowest-cost option.
    
    Args:
        origin: (lat, lon) starting point
        destination: (lat, lon) ending point
        candidate_routes: List of route paths, each a list of (lat, lon) waypoints
        threat_field: ThreatField instance with evaluate() method
        base_cost: Baseline cost for comparison [default: 1.0]
        route_ids: Optional list of route identifiers (default: "route_0", "route_1", ...)
        
    Returns:
        RouteResult for the lowest-cost route with ranking information
    """
    if not candidate_routes:
        raise ValueError("No candidate routes provided")

    if route_ids is None:
        route_ids = [f"route_{i}" for i in range(len(candidate_routes))]

    if len(route_ids) != len(candidate_routes):
        raise ValueError(f"route_ids length {len(route_ids)} != candidate_routes length {len(candidate_routes)}")

    # Evaluate all routes
    route_costs = []
    for route_id, route in zip(route_ids, candidate_routes):
        total_cost, threat_exposure = compute_route_cost(
            route, threat_field, base_cost
        )
        route_costs.append({
            'route_id': route_id,
            'total_cost': total_cost,
            'threat_exposure': threat_exposure,
            'segments': route
        })

    # Sort by cost and assign rankings
    sorted_routes = sorted(route_costs, key=lambda x: x['total_cost'])

    # Return the best route with ranking
    best_route = sorted_routes[0]

    # Find its original ranking (position among all routes)
    best_ranking = next(
        i for i, r in enumerate(sorted_routes)
        if r['route_id'] == best_route['route_id']
    )

    return RouteResult(
        route_id=best_route['route_id'],
        total_cost=best_route['total_cost'],
        threat_exposure=best_route['threat_exposure'],
        segments=best_route['segments'],
        ranking=best_ranking + 1  # 1-indexed ranking
    )
