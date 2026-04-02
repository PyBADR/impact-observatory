"""
Network propagation engine for modeling risk cascade through infrastructure.

Implements graph-based risk propagation using iterative matrix operations
to model how threats spread through interconnected network systems.
"""

from dataclasses import dataclass, field
from typing import List
import numpy as np


@dataclass
class PropagationResult:
    """
    Result of network risk propagation analysis.

    Attributes:
        final_risk: Final risk vector after propagation
        history: List of risk vectors at each iteration step
        steps_to_converge: Number of iterations to reach convergence threshold
        converged: Whether the system converged before maximum steps
    """
    final_risk: np.ndarray
    history: List[np.ndarray] = field(default_factory=list)
    steps_to_converge: int = 0
    converged: bool = False


def propagate_risk(
    adjacency_matrix: np.ndarray,
    risk_vector: np.ndarray,
    shock_vector: np.ndarray,
    alpha: float = 0.7,
    beta: float = 0.3,
    steps: int = 10,
    convergence_threshold: float = 1e-6,
) -> PropagationResult:
    """
    Propagate risk through network using iterative matrix multiplication.

    Models risk dynamics on a network using the update rule:

    R(t+1) = α * A * R(t) + β * S(t) + ε

    Where:
        - A: adjacency matrix (normalized, columns sum to 1)
        - R(t): risk vector at time t
        - S(t): shock/exogenous risk vector
        - α: influence weight of network propagation (0-1)
        - β: influence weight of external shocks (0-1)
        - ε: small stability noise (1e-10)

    The adjacency matrix is normalized column-wise so that each column sums to 1,
    representing probability of risk transmission along edges.

    Convergence is detected when the L2 norm of the change between iterations
    falls below the threshold: ||R(t+1) - R(t)||₂ < threshold

    Args:
        adjacency_matrix: Square matrix of network connections (n×n)
                         Can be weighted or unweighted (will be normalized)
        risk_vector: Initial risk distribution (length n)
        shock_vector: Exogenous risk/shock input (length n)
        alpha: Network propagation weight (default 0.7, must be in [0,1])
        beta: Shock influence weight (default 0.3, must be in [0,1])
        steps: Maximum number of iteration steps (default 10)
        convergence_threshold: L2 norm threshold for convergence (default 1e-6)

    Returns:
        PropagationResult containing final risk vector, iteration history,
        convergence status, and steps to convergence.

    Raises:
        ValueError: If matrix/vector dimensions don't match, weights invalid,
                   or adjacency matrix is not square
    """
    # Validate inputs
    if len(risk_vector) != len(shock_vector):
        raise ValueError(
            f"Risk vector (len {len(risk_vector)}) and shock vector "
            f"(len {len(shock_vector)}) must have same length"
        )

    n = len(risk_vector)
    if adjacency_matrix.shape != (n, n):
        raise ValueError(
            f"Adjacency matrix ({adjacency_matrix.shape}) must be square "
            f"with dimension matching risk/shock vectors ({n})"
        )

    if not np.isclose(alpha + beta, 1.0, rtol=1e-6):
        raise ValueError(
            f"Alpha ({alpha}) and beta ({beta}) weights must sum to 1.0, "
            f"got {alpha + beta}"
        )

    if not (0 <= alpha <= 1 and 0 <= beta <= 1):
        raise ValueError(
            f"Both alpha ({alpha}) and beta ({beta}) must be in [0, 1]"
        )

    if steps < 1:
        raise ValueError(f"Steps must be at least 1, got {steps}")

    # Normalize adjacency matrix (column-stochastic)
    # Each column represents outflow from a node, so columns sum to 1
    A_normalized = adjacency_matrix.astype(np.float64)
    col_sums = np.sum(A_normalized, axis=0)
    col_sums[col_sums == 0] = 1.0  # Avoid division by zero for isolated nodes
    A_normalized = A_normalized / col_sums

    # Initialize
    R = np.array(risk_vector, dtype=np.float64)
    S = np.array(shock_vector, dtype=np.float64)

    # Clamp inputs to valid range
    R = np.clip(R, 0.0, 1.0)
    S = np.clip(S, 0.0, 1.0)

    history = [R.copy()]
    converged = False
    steps_to_converge = 0

    # Small noise for stability
    epsilon = 1e-10

    # Iterative propagation
    for iteration in range(steps):
        # Risk update rule
        R_new = alpha * (A_normalized @ R) + beta * S + epsilon
        R_new = np.clip(R_new, 0.0, 1.0)

        history.append(R_new.copy())

        # Check convergence
        change = np.linalg.norm(R_new - R, ord=2)
        if change < convergence_threshold:
            converged = True
            steps_to_converge = iteration + 1
            R = R_new
            break

        R = R_new

    if not converged:
        steps_to_converge = steps

    return PropagationResult(
        final_risk=R,
        history=history,
        steps_to_converge=steps_to_converge,
        converged=converged,
    )


# Canonical alias for Master Prompt compliance
propagate = propagate_risk
