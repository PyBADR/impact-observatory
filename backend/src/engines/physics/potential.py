"""Potential field routing model.

Alternative route preference modeled as moving away from high-risk
potentials and toward lower-cost potentials.

phi(node) = threat_potential + congestion_potential - accessibility_potential

Reroute preference: entities prefer paths through low-potential regions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class PotentialField:
    """Compute potential field for route optimization."""

    threat_weight: float = 0.4
    congestion_weight: float = 0.3
    accessibility_weight: float = 0.3

    def compute_node_potentials(
        self,
        threat_values: NDArray[np.float64],
        congestion_values: NDArray[np.float64],
        accessibility_values: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Compute potential at each node.

        phi(i) = w_t * threat_i + w_c * congestion_i - w_a * accessibility_i

        Low potential = preferable for routing.
        """
        potentials = (
            self.threat_weight * threat_values
            + self.congestion_weight * congestion_values
            - self.accessibility_weight * accessibility_values
        )
        return potentials

    def gradient(
        self,
        potentials: NDArray[np.float64],
        adjacency: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Compute potential gradient at each node.

        grad(i) = mean(phi(j) - phi(i)) for neighbors j.
        Positive gradient = neighbors have higher potential = this node is safer.
        """
        n = len(potentials)
        grad = np.zeros(n, dtype=np.float64)
        for i in range(n):
            neighbors = np.where(adjacency[i] > 0)[0]
            if len(neighbors) > 0:
                grad[i] = float(np.mean(potentials[neighbors] - potentials[i]))
        return grad


def reroute_preference(
    route_node_ids: list[int],
    potentials: NDArray[np.float64],
) -> tuple[float, list[dict]]:
    """Score a route based on potential field traversal.

    Lower total potential = better route.

    Args:
        route_node_ids: Ordered list of node indices along the route.
        potentials: (N,) potential values.

    Returns:
        (route_cost, per_node_details)
    """
    if not route_node_ids:
        return 0.0, []

    total = 0.0
    details = []
    for idx in route_node_ids:
        phi = float(potentials[idx])
        total += phi
        details.append({"node_index": idx, "potential": phi})

    avg_cost = total / len(route_node_ids)
    return avg_cost, details


def rank_alternative_routes(
    routes: list[list[int]],
    potentials: NDArray[np.float64],
) -> list[tuple[int, float, list[dict]]]:
    """Rank multiple route alternatives by potential cost (ascending).

    Returns:
        List of (route_index, avg_cost, details) sorted by cost.
    """
    scored = []
    for i, route in enumerate(routes):
        cost, details = reroute_preference(route, potentials)
        scored.append((i, cost, details))
    scored.sort(key=lambda x: x[1])
    return scored
