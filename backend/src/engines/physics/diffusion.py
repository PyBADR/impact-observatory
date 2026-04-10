"""Diffusion model — threat/instability spreads across neighboring regions and networks.

Models impact diffusion as a discrete heat equation on the graph:

    u_i(t+1) = u_i(t) + D * Σ_j A_ij * (u_j(t) - u_i(t))

Where:
    u_i(t) = instability at node i at time t
    D = diffusion coefficient (0 < D < 0.5 for stability)
    A_ij = adjacency weight between i and j

This is distinct from propagation (shock-driven) — diffusion is continuous,
ambient spread of instability from high-concentration regions to low ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class DiffusionConfig:
    diffusion_coefficient: float = 0.15  # D: rate of spread (must be < 0.5)
    dissipation_rate: float = 0.02  # natural decay per step
    boundary_absorption: float = 0.0  # how much boundaries absorb (0=reflect, 1=absorb)
    max_steps: int = 20
    convergence_threshold: float = 1e-4


@dataclass
class DiffusionModel:
    """Graph-based diffusion of instability / threat."""

    config: DiffusionConfig = field(default_factory=DiffusionConfig)

    def diffuse_step(
        self,
        adjacency: NDArray[np.float64],
        state: NDArray[np.float64],
        boundary_mask: NDArray[np.bool_] | None = None,
    ) -> NDArray[np.float64]:
        """Single diffusion step.

        Args:
            adjacency: (N, N) weighted adjacency. A_ij > 0 means i and j are connected.
            state: (N,) current instability values.
            boundary_mask: (N,) boolean — True for boundary nodes.

        Returns:
            (N,) updated state after one diffusion step.
        """
        n = len(state)
        D = self.config.diffusion_coefficient

        # Symmetrize adjacency for diffusion (undirected spread)
        sym = (adjacency + adjacency.T) / 2.0

        # Compute Laplacian-style diffusion
        new_state = state.copy()
        for i in range(n):
            neighbors = np.where(sym[i] > 0)[0]
            if len(neighbors) == 0:
                continue
            flux = 0.0
            for j in neighbors:
                weight = sym[i, j]
                flux += weight * (state[j] - state[i])
            new_state[i] += D * flux

        # Natural dissipation
        new_state *= (1.0 - self.config.dissipation_rate)

        # Boundary absorption
        if boundary_mask is not None and self.config.boundary_absorption > 0:
            new_state[boundary_mask] *= (1.0 - self.config.boundary_absorption)

        return np.clip(new_state, 0.0, 1.0)

    def diffuse(
        self,
        adjacency: NDArray[np.float64],
        initial_state: NDArray[np.float64],
        boundary_mask: NDArray[np.bool_] | None = None,
    ) -> tuple[NDArray[np.float64], int, list[NDArray[np.float64]]]:
        """Run diffusion until convergence or max steps.

        Returns:
            (final_state, steps_taken, history)
        """
        state = initial_state.copy()
        history = [state.copy()]

        for step in range(self.config.max_steps):
            new_state = self.diffuse_step(adjacency, state, boundary_mask)
            delta = np.max(np.abs(new_state - state))
            state = new_state
            history.append(state.copy())

            if delta < self.config.convergence_threshold:
                return state, step + 1, history

        return state, self.config.max_steps, history

    def steady_state_risk(
        self,
        adjacency: NDArray[np.float64],
        source_intensities: NDArray[np.float64],
        boundary_mask: NDArray[np.bool_] | None = None,
    ) -> NDArray[np.float64]:
        """Compute steady-state risk distribution from continuous sources.

        Sources are re-injected each step (persistent threat emitters).
        """
        state = source_intensities.copy()
        for _ in range(self.config.max_steps):
            new_state = self.diffuse_step(adjacency, state, boundary_mask)
            # Re-inject sources
            new_state = np.maximum(new_state, source_intensities)
            if np.max(np.abs(new_state - state)) < self.config.convergence_threshold:
                return new_state
            state = new_state
        return state
