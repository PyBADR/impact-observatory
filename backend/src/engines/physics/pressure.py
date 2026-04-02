"""Pressure accumulation model.

Congested ports, rerouted aircraft, and dense corridors accumulate "pressure".

Pressure(node) = Flow * Vulnerability * ThreatIntensity
SystemStress = aggregate(pressure + congestion + unresolved_disruption + uncertainty)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class NodePressure:
    node_id: str
    flow: float = 0.0  # normalized traffic flow through node
    vulnerability: float = 0.0  # structural vulnerability [0, 1]
    threat_intensity: float = 0.0  # current threat [0, 1]
    congestion: float = 0.0  # current congestion [0, 1]
    unresolved_disruptions: int = 0

    @property
    def pressure(self) -> float:
        """Pressure = Flow * Vulnerability * ThreatIntensity."""
        return float(np.clip(self.flow * self.vulnerability * self.threat_intensity, 0.0, 1.0))

    @property
    def stress(self) -> float:
        """Stress = pressure + congestion + disruption_factor."""
        disruption_factor = min(1.0, self.unresolved_disruptions * 0.1)
        return float(np.clip(self.pressure + self.congestion * 0.3 + disruption_factor * 0.3, 0.0, 1.0))


@dataclass
class PressureModel:
    """System-wide pressure aggregation."""

    nodes: dict[str, NodePressure] = field(default_factory=dict)

    def add_node(self, node_id: str, **kwargs) -> None:
        self.nodes[node_id] = NodePressure(node_id=node_id, **kwargs)

    def update_threat(self, node_id: str, threat: float) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].threat_intensity = threat

    def system_stress(self) -> float:
        """SystemStress = mean(stress) across all nodes."""
        if not self.nodes:
            return 0.0
        stresses = [n.stress for n in self.nodes.values()]
        return float(np.mean(stresses))

    def top_pressure_nodes(self, n: int = 10) -> list[tuple[str, float]]:
        """Return top N nodes by pressure."""
        ranked = sorted(self.nodes.items(), key=lambda x: x[1].pressure, reverse=True)
        return [(nid, node.pressure) for nid, node in ranked[:n]]

    def pressure_distribution(self) -> dict[str, float]:
        """All node pressures as a dict."""
        return {nid: n.pressure for nid, n in self.nodes.items()}


def congestion_pressure(
    current_traffic: float,
    capacity: float,
    threat_level: float = 0.0,
) -> tuple[float, dict]:
    """Calculate congestion pressure for a node.

    Args:
        current_traffic: Current normalized traffic volume.
        capacity: Maximum capacity (same units).
        threat_level: Ambient threat [0, 1].

    Returns:
        (pressure_score, explanation)
    """
    if capacity <= 0:
        utilization = 1.0
    else:
        utilization = min(current_traffic / capacity, 2.0)  # allow over-capacity

    # Pressure grows non-linearly as utilization approaches and exceeds capacity
    base_pressure = utilization ** 2 / (1 + utilization)
    threat_amplifier = 1.0 + threat_level * 0.5
    pressure = float(np.clip(base_pressure * threat_amplifier, 0.0, 1.0))

    explanation = {
        "utilization": utilization,
        "base_pressure": base_pressure,
        "threat_amplifier": threat_amplifier,
        "final_pressure": pressure,
    }
    return pressure, explanation
