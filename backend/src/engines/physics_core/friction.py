"""GCC-tuned friction model — corridor resistance with exact mu weights.

Uses FrictionWeights (mu1=0.35, mu2=0.25, mu3=0.25, mu4=0.15) from gcc_weights.
Returns per-corridor friction with full factor breakdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    FRICTION,
    FrictionWeights,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CorridorFrictionBreakdown:
    """Detailed friction breakdown for a single corridor."""
    corridor_id: str
    total_friction: float
    base_friction: float
    threat_component: float
    congestion_component: float
    political_component: float
    regulatory_component: float
    effective_flow_ratio: float
    transit_delay_factor: float
    is_blocked: bool


@dataclass
class GCCFrictionResult:
    """Full friction result across all corridors."""
    corridor_frictions: dict[str, CorridorFrictionBreakdown]
    mean_friction: float
    max_friction: float
    blocked_corridors: list[str]
    high_friction_corridors: list[str]
    weights_used: dict[str, float]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_friction(
    corridors: list[dict],
    threat_data: dict[str, float] | None = None,
    congestion_data: dict[str, float] | None = None,
    political_data: dict[str, float] | None = None,
    regulatory_data: dict[str, float] | None = None,
    weights: FrictionWeights | None = None,
    blocked_threshold: float = 0.95,
    high_friction_threshold: float = 0.6,
) -> GCCFrictionResult:
    """Compute GCC-tuned friction for a set of corridors.

    Args:
        corridors: List of corridor dicts. Each must have:
            - corridor_id (str)
            - base_resistance (float): inherent corridor friction [0, 1]
            Optional: is_chokepoint (bool), capacity (float)
        threat_data: {corridor_id: threat_intensity [0, 1]}
        congestion_data: {corridor_id: congestion_level [0, 1]}
        political_data: {corridor_id: political_constraint [0, 1]}
        regulatory_data: {corridor_id: regulatory_restriction [0, 1]}
        weights: FrictionWeights override (default: GCC singleton mu1-mu4).
        blocked_threshold: friction above which corridor is considered blocked.
        high_friction_threshold: friction above which corridor is flagged.

    Returns:
        GCCFrictionResult with per-corridor breakdown.
    """
    w = weights or FRICTION
    threats = threat_data or {}
    congestion = congestion_data or {}
    political = political_data or {}
    regulatory = regulatory_data or {}

    corridor_frictions: dict[str, CorridorFrictionBreakdown] = {}
    friction_values: list[float] = []
    blocked: list[str] = []
    high_friction: list[str] = []

    for corr in corridors:
        cid = corr["corridor_id"]
        base = corr.get("base_resistance", 0.1)

        # Raw factor values
        threat_val = threats.get(cid, 0.0)
        congestion_val = congestion.get(cid, 0.0)
        political_val = political.get(cid, 0.0)
        regulatory_val = regulatory.get(cid, 0.0)

        # Chokepoint amplification: chokepoints get 20% higher friction
        chokepoint_amp = 1.2 if corr.get("is_chokepoint", False) else 1.0

        # GCC-weighted friction components (mu1-mu4)
        threat_component = w.threat_along_route * threat_val * chokepoint_amp
        congestion_component = w.congestion * congestion_val
        political_component = w.political_constraint * political_val
        regulatory_component = w.regulatory_restriction * regulatory_val

        # Total friction: base + weighted components, clamped to [0, 1]
        total = float(np.clip(
            base + threat_component + congestion_component + political_component + regulatory_component,
            0.0,
            1.0,
        ))

        # Derived metrics
        effective_flow_ratio = 1.0 - total
        if total >= 0.99:
            delay_factor = 100.0
        else:
            delay_factor = 1.0 / (1.0 - total)

        is_blocked = total >= blocked_threshold

        corridor_frictions[cid] = CorridorFrictionBreakdown(
            corridor_id=cid,
            total_friction=total,
            base_friction=base,
            threat_component=threat_component,
            congestion_component=congestion_component,
            political_component=political_component,
            regulatory_component=regulatory_component,
            effective_flow_ratio=effective_flow_ratio,
            transit_delay_factor=delay_factor,
            is_blocked=is_blocked,
        )

        friction_values.append(total)
        if is_blocked:
            blocked.append(cid)
        elif total >= high_friction_threshold:
            high_friction.append(cid)

    arr = np.array(friction_values) if friction_values else np.array([0.0])

    return GCCFrictionResult(
        corridor_frictions=corridor_frictions,
        mean_friction=float(np.mean(arr)),
        max_friction=float(np.max(arr)),
        blocked_corridors=blocked,
        high_friction_corridors=high_friction,
        weights_used={
            "mu1_threat_along_route": w.threat_along_route,
            "mu2_congestion": w.congestion,
            "mu3_political_constraint": w.political_constraint,
            "mu4_regulatory_restriction": w.regulatory_restriction,
        },
    )
