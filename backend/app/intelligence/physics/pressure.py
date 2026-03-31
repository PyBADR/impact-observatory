"""
Pressure accumulation at network nodes.

Physics metaphor: Pressure at a node represents load stress (like fluid pressure).
Current pressure = current_load / base_capacity. When routes are disrupted,
flow reroutes to alternative paths, increasing pressure there. System pressure
is a weighted aggregate of node pressures.
"""

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np


@dataclass
class PressureNode:
    """
    A network node (airport, port, corridor, etc.) with capacity and load.
    
    Attributes:
        node_id: Unique identifier
        node_type: Category ('airport', 'port', 'corridor', 'waypoint', etc.)
        base_capacity: Maximum sustainable load [0, inf)
        current_load: Current load on node [0, inf)
    """
    node_id: str
    node_type: str
    base_capacity: float
    current_load: float = 0.0

    def __post_init__(self):
        """Validate non-negative values."""
        if self.base_capacity < 0:
            raise ValueError(f"base_capacity must be non-negative, got {self.base_capacity}")
        if self.current_load < 0:
            raise ValueError(f"current_load must be non-negative, got {self.current_load}")


def compute_pressure(node: PressureNode) -> float:
    """
    Compute pressure at a single node.
    
    Physics model: pressure = current_load / base_capacity, clamped to avoid
    undefined behavior when capacity is zero.
    
    A pressure of 1.0 means the node is at rated capacity.
    A pressure > 1.0 means the node is congested.
    
    Args:
        node: PressureNode instance
        
    Returns:
        Pressure value [0, inf), typically 0-2 in normal operation
    """
    if node.base_capacity == 0:
        # If capacity is zero, any load creates infinite pressure
        return float('inf') if node.current_load > 0 else 0.0

    pressure = node.current_load / node.base_capacity
    return float(pressure)


def accumulate_pressure(
    nodes: List[PressureNode],
    disrupted_routes: List[str],
    reroute_factor: float = 1.3
) -> Dict[str, float]:
    """
    Redistribute load when routes are disrupted.
    
    Physics model: When a route is disrupted, its load must reroute through
    alternative paths. This model assumes:
    1. Load from disrupted routes is redistributed evenly to remaining routes
    2. A reroute_factor > 1 models inefficiency (longer paths, extra hops)
    3. Pressure increases at nodes handling rerouted traffic
    
    Args:
        nodes: List of PressureNode instances
        disrupted_routes: IDs of disrupted routes (affects load redistribution)
        reroute_factor: Multiplier for rerouted load [default: 1.3 = 30% increase]
        
    Returns:
        Dictionary mapping node_id -> adjusted pressure value
    """
    # Create mutable copies of node loads
    adjusted_loads = {node.node_id: node.current_load for node in nodes}

    # Estimate load on disrupted routes (simplified model)
    # In a real system, this would use routing tables
    disrupted_load = len(disrupted_routes) * 0.1  # Placeholder scaling

    if disrupted_load > 0 and len(nodes) > 0:
        # Redistribute to remaining nodes with inefficiency factor
        per_node_increase = (disrupted_load * reroute_factor) / len(nodes)
        for node_id in adjusted_loads:
            adjusted_loads[node_id] += per_node_increase

    # Compute pressures with adjusted loads
    pressures = {}
    for node in nodes:
        adjusted_node = PressureNode(
            node.node_id,
            node.node_type,
            node.base_capacity,
            adjusted_loads[node.node_id]
        )
        pressures[node.node_id] = compute_pressure(adjusted_node)

    return pressures


def system_pressure(
    pressures: Dict[str, float],
    weights: Dict[str, float] = None
) -> float:
    """
    Compute aggregate system pressure.
    
    Physics model: System stress is a weighted sum of node pressures.
    Optionally applies weights to prioritize critical nodes.
    
    Args:
        pressures: Dictionary mapping node_id -> pressure value
        weights: Optional dictionary mapping node_id -> weight [0, 1]
                If None, all nodes weighted equally (1.0)
                
    Returns:
        Aggregate system pressure [0, inf), clamped to max 1.0 for interpretation
    """
    if not pressures:
        return 0.0

    if weights is None:
        weights = {node_id: 1.0 for node_id in pressures}

    # Compute weighted average, handling missing weights (default to 1.0)
    total_weight = 0.0
    weighted_pressure = 0.0

    for node_id, pressure in pressures.items():
        weight = weights.get(node_id, 1.0)
        weighted_pressure += pressure * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    system_p = weighted_pressure / total_weight

    # Clamp to [0, 1] for interpretation (though raw value may exceed 1)
    return float(np.clip(system_p, 0.0, 1.0))
