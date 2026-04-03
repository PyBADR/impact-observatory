"""Multi-hop impact analysis — trace cascading effects through the graph.

Given a shock at node S, compute the attenuated impact at every reachable
node up to K hops, accounting for edge weights and damping.

Impact(S → T, k hops) = severity * Π (edge_weight_i * polarity_i) * (1 - damping)^k

This produces an explicit impact chain for explainability:
    S → A (w=0.9) → B (w=0.7) → T  →  impact = sev * 0.9 * 0.7 * (1-d)^2
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class HopImpact:
    """Impact on a single target via a specific path."""

    source_id: str
    target_id: str
    path: list[str]
    hops: int
    raw_product: float  # product of edge weights along path
    damped_impact: float  # after damping
    final_impact: float  # severity * damped_impact


@dataclass
class MultiHopResult:
    """Complete multi-hop impact analysis from one or more sources."""

    source_ids: list[str]
    severity: float
    max_hops: int
    impacts: dict[str, float]  # node_id → aggregated impact
    chains: list[HopImpact]  # all individual chains
    top_impacted: list[tuple[str, float]]


def compute_multi_hop_impacts(
    adjacency: NDArray[np.float64],
    node_ids: list[str],
    source_indices: list[int],
    severity: float = 1.0,
    max_hops: int = 5,
    damping: float = 0.15,
    min_impact: float = 0.01,
) -> MultiHopResult:
    """Compute multi-hop cascading impacts using BFS with weight tracking.

    Args:
        adjacency: (N, N) weighted adjacency matrix. A[i, j] = weight from i to j.
        node_ids: ordered node id list.
        source_indices: indices of shock source nodes.
        severity: initial shock severity [0, 1].
        max_hops: maximum propagation depth.
        damping: per-hop attenuation factor.
        min_impact: prune chains below this threshold.

    Returns:
        MultiHopResult with per-node impacts and explicit chains.
    """
    n = len(node_ids)
    all_chains: list[HopImpact] = []
    node_impacts: dict[str, float] = {}

    for src_idx in source_indices:
        src_id = node_ids[src_idx]

        # BFS with path tracking
        # queue: (current_index, path_indices, cumulative_weight_product, hop_count)
        queue: list[tuple[int, list[int], float, int]] = [(src_idx, [src_idx], 1.0, 0)]
        visited_paths: set[tuple[int, ...]] = set()

        while queue:
            current, path, weight_product, hops = queue.pop(0)

            if hops >= max_hops:
                continue

            # Find outgoing edges
            for neighbor in range(n):
                edge_weight = adjacency[current, neighbor]
                if edge_weight == 0 or neighbor in path:
                    continue

                new_product = weight_product * abs(edge_weight)
                new_hops = hops + 1
                damped = new_product * (1.0 - damping) ** new_hops
                final = severity * damped

                if final < min_impact:
                    continue

                new_path = path + [neighbor]
                path_key = tuple(new_path)
                if path_key in visited_paths:
                    continue
                visited_paths.add(path_key)

                target_id = node_ids[neighbor]
                chain = HopImpact(
                    source_id=src_id,
                    target_id=target_id,
                    path=[node_ids[i] for i in new_path],
                    hops=new_hops,
                    raw_product=new_product,
                    damped_impact=damped,
                    final_impact=final,
                )
                all_chains.append(chain)

                # Aggregate: take max impact per node (strongest path dominates)
                if target_id not in node_impacts or final > node_impacts[target_id]:
                    node_impacts[target_id] = final

                queue.append((neighbor, new_path, new_product, new_hops))

    # Sort chains by impact
    all_chains.sort(key=lambda c: c.final_impact, reverse=True)
    top = sorted(node_impacts.items(), key=lambda x: x[1], reverse=True)[:20]

    return MultiHopResult(
        source_ids=[node_ids[i] for i in source_indices],
        severity=severity,
        max_hops=max_hops,
        impacts=node_impacts,
        chains=all_chains[:100],  # cap for performance
        top_impacted=top,
    )
