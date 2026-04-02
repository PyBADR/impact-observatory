"""Shockwave propagation model.

Major events produce a wave of downstream impacts through dependent routes
and connected regions. The shockwave attenuates with graph distance and time.

This is the physics-layer complement to the math propagation engine.
It adds time-domain wave behavior: an initial spike followed by decay.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class ShockwaveConfig:
    initial_amplitude: float = 1.0
    propagation_speed: float = 1.0  # graph hops per time step
    attenuation_per_hop: float = 0.3  # amplitude loss per hop
    temporal_decay_rate: float = 0.1  # amplitude loss per time step
    reflection_coefficient: float = 0.1  # bounce-back at boundaries


@dataclass
class ShockwaveModel:
    """Simulate shockwave propagation through a network."""

    config: ShockwaveConfig = field(default_factory=ShockwaveConfig)

    def propagate(
        self,
        adjacency: NDArray[np.float64],
        origin_indices: list[int],
        n_steps: int = 10,
    ) -> list[NDArray[np.float64]]:
        """Propagate a shockwave from origin nodes through the network.

        Returns a list of (N,) arrays, one per time step, representing
        the shockwave amplitude at each node.
        """
        n = adjacency.shape[0]
        c = self.config

        # Normalize adjacency rows for propagation
        row_sums = adjacency.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1.0, row_sums)
        norm_adj = adjacency / row_sums

        # Initial wave: full amplitude at origin nodes
        wave = np.zeros(n, dtype=np.float64)
        for idx in origin_indices:
            wave[idx] = c.initial_amplitude

        history = [wave.copy()]

        for t in range(1, n_steps + 1):
            # Propagate through network
            propagated = norm_adj.T @ wave

            # Attenuation per hop (approximated as per-step)
            propagated *= (1.0 - c.attenuation_per_hop)

            # Temporal decay of existing wave
            wave *= (1.0 - c.temporal_decay_rate)

            # Superpose propagated wave onto existing
            wave = np.maximum(wave, propagated)

            # Boundary reflection: nodes with no outgoing edges reflect some energy back
            dead_ends = (adjacency.sum(axis=1) == 0)
            if dead_ends.any():
                wave[dead_ends] *= (1.0 + c.reflection_coefficient)

            wave = np.clip(wave, 0.0, 1.0)
            history.append(wave.copy())

        return history

    def peak_impact(self, history: list[NDArray[np.float64]]) -> NDArray[np.float64]:
        """Maximum amplitude each node experienced across all time steps."""
        return np.max(np.stack(history), axis=0)


def propagate_shockwave(
    adjacency: NDArray[np.float64],
    origin_indices: list[int],
    n_steps: int = 10,
    config: ShockwaveConfig | None = None,
) -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """Convenience function: propagate and return (peak_impact, full_history)."""
    model = ShockwaveModel(config=config or ShockwaveConfig())
    history = model.propagate(adjacency, origin_indices, n_steps)
    peak = model.peak_impact(history)
    return peak, history
