"""
Regime Graph Adapter — applies regime-driven modifiers to graph propagation.

Translates RegimeState into concrete node-level and edge-level modifiers
that the propagation engine and map payload engine consume.

Key formula:
  propagated_shock = base_shock × edge_transfer × node_sensitivity
                     × regime_amplifier × delay_decay

Layer: Regime → Graph/Propagation (one-way dependency)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from src.regime.regime_types import RegimeType, REGIME_DEFINITIONS
from src.utils import clamp


# ── Sector sensitivity profiles per regime ──────────────────────────────────
# Each regime amplifies certain sectors more than others.
# Values are multipliers applied to the node's base sensitivity.
_SECTOR_SENSITIVITY: dict[RegimeType, dict[str, float]] = {
    "STABLE": {
        "banking": 1.00, "insurance": 1.00, "fintech": 1.00,
        "energy": 1.00, "maritime": 1.00, "logistics": 1.00,
        "infrastructure": 1.00, "government": 1.00, "healthcare": 1.00,
    },
    "ELEVATED_STRESS": {
        "banking": 1.10, "insurance": 1.05, "fintech": 1.08,
        "energy": 1.05, "maritime": 1.05, "logistics": 1.03,
        "infrastructure": 1.02, "government": 1.00, "healthcare": 1.00,
    },
    "LIQUIDITY_STRESS": {
        "banking": 1.35, "insurance": 1.15, "fintech": 1.25,
        "energy": 1.10, "maritime": 1.08, "logistics": 1.05,
        "infrastructure": 1.05, "government": 1.02, "healthcare": 1.00,
    },
    "SYSTEMIC_STRESS": {
        "banking": 1.50, "insurance": 1.30, "fintech": 1.40,
        "energy": 1.25, "maritime": 1.20, "logistics": 1.15,
        "infrastructure": 1.10, "government": 1.08, "healthcare": 1.05,
    },
    "CRISIS_ESCALATION": {
        "banking": 1.80, "insurance": 1.50, "fintech": 1.60,
        "energy": 1.40, "maritime": 1.35, "logistics": 1.25,
        "infrastructure": 1.20, "government": 1.15, "healthcare": 1.10,
    },
}

# Cross-sector transmission boost: edges connecting these sector pairs
# receive additional transfer coefficient boost under stress regimes.
_CROSS_SECTOR_BOOST: dict[tuple[str, str], float] = {
    ("banking", "insurance"):     0.12,
    ("banking", "fintech"):       0.10,
    ("energy", "maritime"):       0.08,
    ("maritime", "logistics"):    0.06,
    ("energy", "banking"):        0.05,
    ("fintech", "banking"):       0.10,
    ("insurance", "banking"):     0.12,
    ("logistics", "maritime"):    0.06,
    ("maritime", "energy"):       0.08,
    ("banking", "energy"):        0.05,
}


# ── Output contract ────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class RegimeGraphModifiers:
    """
    Computed modifiers for the graph/propagation layer.

    Consumed by:
      - map_payload_engine (stress adjustment)
      - propagation calculations (shock amplification)
      - decision trigger engine (threshold shifts)
    """
    regime_id: RegimeType
    propagation_amplifier: float          # global shock amplifier (1.0 = neutral)
    delay_compression: float              # time compression (1.0 = neutral, <1 = faster)
    failure_threshold_shift: float        # negative = thresholds tighten
    node_sensitivity: dict[str, float] = field(default_factory=dict)
    # node_id → sensitivity multiplier
    edge_modifiers: dict[str, dict[str, float]] = field(default_factory=dict)
    # "src->tgt" → {transfer_boost, delay_factor}

    def to_dict(self) -> dict[str, Any]:
        return {
            "regime_id": self.regime_id,
            "propagation_amplifier": round(self.propagation_amplifier, 4),
            "delay_compression": round(self.delay_compression, 4),
            "failure_threshold_shift": round(self.failure_threshold_shift, 4),
            "node_sensitivity_count": len(self.node_sensitivity),
            "edge_modifier_count": len(self.edge_modifiers),
        }


# ── Public API ──────────────────────────────────────────────────────────────

def apply_regime_to_graph(
    regime_id: RegimeType,
    gcc_nodes: list[dict[str, Any]],
    gcc_adjacency: dict[str, list[str]] | None = None,
) -> RegimeGraphModifiers:
    """
    Compute regime-driven modifiers for all nodes and edges.

    Pure function. No side effects.

    Args:
        regime_id:       Current regime classification.
        gcc_nodes:       GCC_NODES list (each has id, sector, criticality).
        gcc_adjacency:   GCC_ADJACENCY dict (node_id → [neighbor_ids]).

    Returns:
        RegimeGraphModifiers with per-node sensitivity and per-edge transfer modifiers.
    """
    defn = REGIME_DEFINITIONS[regime_id]
    sector_profile = _SECTOR_SENSITIVITY[regime_id]

    # ── Node sensitivity ────────────────────────────────────────────────────
    node_map: dict[str, dict] = {n["id"]: n for n in gcc_nodes}
    node_sensitivity: dict[str, float] = {}

    for node in gcc_nodes:
        nid = node["id"]
        sector = node.get("sector", "").lower()
        base_criticality = float(node.get("criticality", 0.5))

        # Sector multiplier from regime profile (default 1.0)
        sector_mult = sector_profile.get(sector, 1.0)

        # Criticality amplification: high-criticality nodes are MORE sensitive
        # under stress regimes, not less
        criticality_boost = 1.0 + (base_criticality - 0.5) * 0.3 * (
            defn["propagation_amplifier"] - 1.0
        )

        sensitivity = clamp(
            sector_mult * max(criticality_boost, 0.8),
            0.5,
            3.0,
        )
        node_sensitivity[nid] = round(sensitivity, 4)

    # ── Edge modifiers ──────────────────────────────────────────────────────
    edge_modifiers: dict[str, dict[str, float]] = {}

    if gcc_adjacency:
        for src_id, neighbors in gcc_adjacency.items():
            src_node = node_map.get(src_id)
            if not src_node:
                continue
            src_sector = src_node.get("sector", "").lower()

            for tgt_id in neighbors:
                tgt_node = node_map.get(tgt_id)
                if not tgt_node:
                    continue
                tgt_sector = tgt_node.get("sector", "").lower()

                edge_key = f"{src_id}->{tgt_id}"

                # Base transfer boost from regime
                base_boost = defn["propagation_amplifier"] - 1.0  # 0.0 for STABLE

                # Cross-sector contagion boost (bidirectional lookup)
                cross_boost = _CROSS_SECTOR_BOOST.get(
                    (src_sector, tgt_sector), 0.0
                )
                # Scale cross-sector boost by regime severity
                regime_severity_idx = list(REGIME_DEFINITIONS.keys()).index(regime_id)
                cross_boost *= (regime_severity_idx / 4.0)  # 0.0 for STABLE, 1.0 for CRISIS

                transfer_boost = round(clamp(base_boost + cross_boost, 0.0, 1.5), 4)
                delay_factor = round(defn["delay_compression"], 4)

                edge_modifiers[edge_key] = {
                    "transfer_boost": transfer_boost,
                    "delay_factor": delay_factor,
                }

    return RegimeGraphModifiers(
        regime_id=regime_id,
        propagation_amplifier=defn["propagation_amplifier"],
        delay_compression=defn["delay_compression"],
        failure_threshold_shift=defn["failure_threshold_shift"],
        node_sensitivity=node_sensitivity,
        edge_modifiers=edge_modifiers,
    )


def compute_regime_adjusted_stress(
    base_stress: float,
    node_id: str,
    modifiers: RegimeGraphModifiers,
) -> float:
    """
    Apply regime modifiers to a node's base stress score.

    Formula:
      adjusted = base_stress × node_sensitivity × propagation_amplifier

    Returns clamped to [0, 1].
    """
    sensitivity = modifiers.node_sensitivity.get(node_id, 1.0)
    adjusted = base_stress * sensitivity * modifiers.propagation_amplifier
    return clamp(adjusted, 0.0, 1.0)


def compute_regime_adjusted_transfer(
    base_transfer: float,
    source_id: str,
    target_id: str,
    modifiers: RegimeGraphModifiers,
) -> float:
    """
    Apply regime modifiers to an edge's transfer coefficient.

    Formula:
      adjusted = base_transfer × (1 + edge_transfer_boost)

    Returns clamped to [0, 1].
    """
    edge_key = f"{source_id}->{target_id}"
    edge_mod = modifiers.edge_modifiers.get(edge_key, {})
    boost = edge_mod.get("transfer_boost", 0.0)
    adjusted = base_transfer * (1.0 + boost)
    return clamp(adjusted, 0.0, 1.0)
