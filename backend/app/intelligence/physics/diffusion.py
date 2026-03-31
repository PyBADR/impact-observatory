"""
Threat diffusion across regional networks.

Physics metaphor: Threat spreads across regions like heat diffusion through a
material. The discrete diffusion equation governs how threat density equilibrates:
    T(t+dt) = T(t) + D * dt * L * T(t)
where L is the graph Laplacian (captures local spreading tendency).
"""

from dataclasses import dataclass, field
from typing import List
import numpy as np


@dataclass
class DiffusionResult:
    """
    Result of a threat diffusion simulation.
    
    Attributes:
        final_state: Final threat vector after diffusion steps
        history: List of threat states at each time step (shape: steps x num_regions)
        equilibrium_reached: Whether threat distribution reached equilibrium
    """
    final_state: np.ndarray
    history: List[np.ndarray] = field(default_factory=list)
    equilibrium_reached: bool = False


def compute_laplacian(adjacency: np.ndarray) -> np.ndarray:
    """
    Compute graph Laplacian from adjacency matrix.
    
    The Laplacian L = D - A where:
        - A: adjacency matrix (element [i,j] = 1 if regions i,j connected)
        - D: degree matrix (diagonal, D[i,i] = sum of row i in A)
    
    The Laplacian encodes how neighboring regions influence each other.
    Negative Laplacian applied to a threat vector models spreading to neighbors.
    
    Args:
        adjacency: Square adjacency matrix (n_regions x n_regions)
                  Non-zero entries represent edges
        
    Returns:
        Laplacian matrix (n_regions x n_regions)
    """
    adjacency = np.asarray(adjacency, dtype=float)
    n = adjacency.shape[0]

    if adjacency.shape != (n, n):
        raise ValueError(f"adjacency must be square, got shape {adjacency.shape}")

    # Degree matrix: sum of neighbors for each node
    degrees = np.sum(adjacency, axis=1)
    degree_matrix = np.diag(degrees)

    # Laplacian: L = D - A
    laplacian = degree_matrix - adjacency

    return laplacian


def diffuse_threat(
    adjacency: np.ndarray,
    threat_vector: np.ndarray,
    diffusion_coefficient: float = 0.1,
    dt: float = 1.0,
    steps: int = 10,
    equilibrium_threshold: float = 1e-6
) -> DiffusionResult:
    """
    Simulate threat diffusion across a network.

    Physics model: Threat spreads from high-concentration regions to neighbors
    according to the discrete diffusion equation:
        T(t+dt) = T(t) - D * dt * L * T(t)

    The negative Laplacian encodes spreading: threat flows from high-concentration
    nodes to lower-concentration neighbors, equilibrating the distribution.

    This models how disruptions, conflicts, or risks diffuse through connected
    regional networks, with higher diffusion coefficients causing faster spreading.

    Args:
        adjacency: Adjacency matrix describing regional connectivity
                   (n_regions x n_regions)
        threat_vector: Initial threat distribution across regions
                      (n_regions,)
        diffusion_coefficient: Diffusion rate D [default: 0.1]
                              Higher values = faster spreading
        dt: Time step size [default: 1.0]
        steps: Number of simulation steps [default: 10]
        equilibrium_threshold: Consider equilibrium reached when max change < threshold

    Returns:
        DiffusionResult with final state, history, and equilibrium status
    """
    adjacency = np.asarray(adjacency, dtype=float)
    threat = np.asarray(threat_vector, dtype=float).copy()

    if threat.shape[0] != adjacency.shape[0]:
        raise ValueError(
            f"threat_vector size {threat.shape[0]} != adjacency size {adjacency.shape[0]}"
        )

    laplacian = compute_laplacian(adjacency)

    history = [threat.copy()]
    equilibrium_reached = False

    for step in range(steps):
        # Diffusion step: T_new = T - D * dt * L * T
        # The negative Laplacian models spreading from high to low concentration
        laplacian_action = laplacian @ threat
        threat_new = threat - diffusion_coefficient * dt * laplacian_action

        # Clamp to non-negative (threat cannot be negative)
        threat_new = np.maximum(threat_new, 0.0)

        # Check for equilibrium (negligible change)
        change = np.max(np.abs(threat_new - threat))
        if change < equilibrium_threshold:
            equilibrium_reached = True
            threat = threat_new
            history.append(threat.copy())
            break

        threat = threat_new
        history.append(threat.copy())

    return DiffusionResult(
        final_state=threat,
        history=history,
        equilibrium_reached=equilibrium_reached
    )
