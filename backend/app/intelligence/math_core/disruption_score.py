"""
Disruption scoring for GCC risk assessment.

Implements disruption:
D_i(t) = v1*R(t) + v2*C(t) + v3*A(t) + v4*K(t) + v5*B(t)

Where:
R(t) = Recovery capacity
C(t) = Criticality
A(t) = Accessibility (network connectivity)
K(t) = Knock-on propagation effects
B(t) = Buffer capacity
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np

from .gcc_weights import DISRUPTION_WEIGHTS


@dataclass
class DisruptionMetrics:
    """Container for disruption scoring metrics."""

    recovery_capacity: float  # R(t): Entity recovery capacity [0, 1]
    criticality: float  # C(t): Criticality to network [0, 1]
    accessibility: float  # A(t): Network accessibility/connectivity [0, 1]
    knock_on_propagation: float  # K(t): Knock-on cascade effects [0, 1]
    buffer_capacity: float  # B(t): Buffer/redundancy capacity [0, 1]


def compute_disruption_score(
    metrics: DisruptionMetrics,
    weights: Dict[str, float] = None,
) -> float:
    """
    Compute disruption score from component metrics.

    Implements:
    D_i(t) = v1*R(t) + v2*C(t) + v3*A(t) + v4*K(t) + v5*B(t)

    Args:
        metrics: DisruptionMetrics object with component values
        weights: Custom weight dictionary. Defaults to DISRUPTION_WEIGHTS if None.

    Returns:
        Disruption score in [0, 1]
    """
    if weights is None:
        weights = DISRUPTION_WEIGHTS.copy()

    # Validate weights sum to 1.0
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Validate input metrics are in [0, 1]
    recovery = np.clip(metrics.recovery_capacity, 0.0, 1.0)
    criticality = np.clip(metrics.criticality, 0.0, 1.0)
    accessibility = np.clip(metrics.accessibility, 0.0, 1.0)
    knock_on = np.clip(metrics.knock_on_propagation, 0.0, 1.0)
    buffer = np.clip(metrics.buffer_capacity, 0.0, 1.0)

    # Compute weighted sum
    disruption = (
        weights["recovery_capacity"] * recovery
        + weights["criticality"] * criticality
        + weights["accessibility"] * accessibility
        + weights["knock_on_propagation"] * knock_on
        + weights["buffer_capacity"] * buffer
    )

    return float(np.clip(disruption, 0.0, 1.0))


def compute_recovery_capacity(
    recovery_time_hours: float,
    baseline_hours: float = 72.0,
) -> float:
    """
    Compute recovery capacity (inverse of recovery time).

    R(t) = max(0, 1 - (recovery_time_hours / baseline_hours))

    Args:
        recovery_time_hours: Estimated time to recover [hours]
        baseline_hours: Baseline recovery time for normalization (default 72 hours)

    Returns:
        Recovery capacity in [0, 1] where 1 = instant recovery, 0 = very long recovery
    """
    if baseline_hours <= 0:
        return 0.0

    recovery_time_hours = max(0.0, recovery_time_hours)
    recovery_ratio = recovery_time_hours / baseline_hours

    capacity = 1.0 - np.clip(recovery_ratio, 0.0, 1.0)
    return float(np.clip(capacity, 0.0, 1.0))


def compute_criticality(
    dependent_entities: int,
    total_entities: int,
    criticality_flag: bool = False,
) -> float:
    """
    Compute criticality to network.

    C(t) = (dependent_entities / total_entities) [+ boost if critically important]

    Args:
        dependent_entities: Number of entities depending on this node
        total_entities: Total entities in network
        criticality_flag: True if entity is flagged as critical infrastructure

    Returns:
        Criticality in [0, 1]
    """
    if total_entities <= 0:
        return 0.0

    dependency_ratio = dependent_entities / total_entities
    criticality = np.clip(dependency_ratio, 0.0, 1.0)

    # Add boost for flagged critical infrastructure
    if criticality_flag:
        criticality = min(1.0, criticality + 0.25)

    return float(np.clip(criticality, 0.0, 1.0))


def compute_accessibility(
    connected_neighbors: int,
    total_possible_neighbors: int,
) -> float:
    """
    Compute network accessibility/connectivity.

    A(t) = connected_neighbors / total_possible_neighbors

    Args:
        connected_neighbors: Number of directly connected neighbors
        total_possible_neighbors: Total possible neighbors in fully connected network

    Returns:
        Accessibility in [0, 1] where 1 = fully connected, 0 = isolated
    """
    if total_possible_neighbors <= 0:
        return 0.0

    connectivity = connected_neighbors / total_possible_neighbors
    return float(np.clip(connectivity, 0.0, 1.0))


def compute_knock_on_propagation(
    cascade_depth: int,
    affected_downstream: int,
    total_downstream: int,
) -> float:
    """
    Compute knock-on cascade propagation effects.

    K(t) = (1 + cascade_depth / 10) * (affected_downstream / total_downstream)

    Args:
        cascade_depth: Depth of cascading failures (number of levels)
        affected_downstream: Number of downstream entities affected
        total_downstream: Total downstream entities reachable

    Returns:
        Knock-on propagation in [0, 1]
    """
    if total_downstream <= 0:
        return 0.0

    cascade_depth = max(0, cascade_depth)
    propagation_ratio = affected_downstream / total_downstream

    # Scale by cascade depth (deeper cascades = more knock-on effect)
    cascade_factor = 1.0 + (cascade_depth / 10.0)
    knock_on = propagation_ratio * cascade_factor

    return float(np.clip(knock_on, 0.0, 1.0))


def compute_buffer_capacity(
    inventory_hours: float,
    demand_hours: float = 48.0,
) -> float:
    """
    Compute buffer/redundancy capacity.

    B(t) = min(inventory_hours / demand_hours, 1.0)

    Args:
        inventory_hours: Hours of buffer inventory available
        demand_hours: Hours of demand covered by typical buffer (default 48 hours)

    Returns:
        Buffer capacity in [0, 1] where 1 = sufficient buffer, 0 = no buffer
    """
    if demand_hours <= 0:
        return 0.0

    inventory_hours = max(0.0, inventory_hours)
    buffer_ratio = inventory_hours / demand_hours

    capacity = np.clip(buffer_ratio, 0.0, 1.0)
    return float(capacity)


def compute_propagation_risk(
    node_criticality: float,
    network_density: float,
    cascade_multiplier: float = 1.5,
) -> float:
    """
    Compute risk of cascading failures through network.

    PropagationRisk = criticality * network_density * cascade_multiplier

    Args:
        node_criticality: Criticality of the failed node [0, 1]
        network_density: Network density/connectivity [0, 1]
        cascade_multiplier: Multiplier for cascade amplification

    Returns:
        Propagation risk in [0, 1]
    """
    node_criticality = np.clip(node_criticality, 0.0, 1.0)
    network_density = np.clip(network_density, 0.0, 1.0)

    risk = node_criticality * network_density * cascade_multiplier
    return float(np.clip(risk, 0.0, 1.0))


# Canonical alias for Master Prompt compliance
compute_disruption = compute_disruption_score
