"""GCC-tuned threat field — events radiate risk with calibrated multipliers and decay.

Uses exact EVENT_MULTIPLIERS, LAMBDA_D values, and PROXIMITY_BANDS from gcc_weights.
Wraps the base ThreatField with GCC-specific defaults and adds explainability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    EVENT_MULTIPLIERS,
    LAMBDA_D_DEFAULT,
    LAMBDA_D_MARITIME_CHOKEPOINT,
    LAMBDA_D_URBAN,
    LAMBDA_T_KINETIC,
    LAMBDA_T_SOFT,
    PROXIMITY_BANDS,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ThreatContribution:
    """A single event's contribution to a node's threat value."""
    event_id: str
    event_type: str
    multiplier: float
    distance_km: float
    proximity_band_weight: float
    spatial_decay: float
    temporal_decay: float
    raw_severity: float
    final_contribution: float


@dataclass
class NodeThreatResult:
    """Threat result for a single node."""
    node_id: str
    threat_value: float
    dominant_event_id: str | None
    contributions: list[ThreatContribution]


@dataclass
class GCCThreatFieldResult:
    """Full threat field result across all nodes."""
    node_results: dict[str, NodeThreatResult]
    global_max_threat: float
    global_mean_threat: float
    hotspot_node_ids: list[str]
    config_snapshot: dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    r = 6371.0
    d_lat = np.radians(lat2 - lat1)
    d_lng = np.radians(lng2 - lng1)
    a = (
        np.sin(d_lat / 2.0) ** 2
        + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(d_lng / 2.0) ** 2
    )
    return float(r * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a)))


def _proximity_band_weight(distance_km: float) -> float:
    """Look up the GCC proximity band weight for a given distance."""
    for low, high, weight in PROXIMITY_BANDS:
        if low <= distance_km < high:
            return weight
    return 0.0


def _get_lambda_d(event_type: str, context: str = "default") -> float:
    """Select the appropriate spatial decay rate based on event context."""
    if context == "maritime_chokepoint":
        return LAMBDA_D_MARITIME_CHOKEPOINT
    if context == "urban":
        return LAMBDA_D_URBAN
    return LAMBDA_D_DEFAULT


def _get_lambda_t(event_type: str) -> float:
    """Select temporal decay rate: kinetic events decay slower."""
    kinetic_types = {"missile_strike", "naval_attack", "airspace_strike", "infrastructure_damage"}
    if event_type in kinetic_types:
        return LAMBDA_T_KINETIC
    return LAMBDA_T_SOFT


def _get_event_multiplier(event_type: str) -> float:
    """Look up the GCC event multiplier M_e."""
    return EVENT_MULTIPLIERS.get(event_type, 0.50)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_threat_field(
    events: list[dict],
    node_positions: dict[str, tuple[float, float]],
    hours_since_events: dict[str, float] | None = None,
    context: str = "default",
    hotspot_threshold: float = 0.5,
) -> GCCThreatFieldResult:
    """Compute per-node threat values using exact GCC coefficients.

    Args:
        events: List of event dicts. Each must have:
            - event_id (str)
            - event_type (str): key into EVENT_MULTIPLIERS
            - lat, lng (float)
            - severity_score (float): raw severity in [0, 1]
        node_positions: {node_id: (lat, lng)}
        hours_since_events: {event_id: hours} for temporal decay. If None, no temporal decay.
        context: "default", "maritime_chokepoint", or "urban" for lambda_d selection.
        hotspot_threshold: threat value above which a node is a hotspot.

    Returns:
        GCCThreatFieldResult with per-node threat, contributions, and hotspots.
    """
    hours_map = hours_since_events or {}
    node_results: dict[str, NodeThreatResult] = {}

    all_threat_values: list[float] = []

    for node_id, (node_lat, node_lng) in node_positions.items():
        contributions: list[ThreatContribution] = []
        total_threat = 0.0

        for ev in events:
            ev_id = ev["event_id"]
            ev_type = ev.get("event_type", "rumor_unverified")
            ev_lat = ev["lat"]
            ev_lng = ev["lng"]
            raw_severity = ev.get("severity_score", 0.5)

            # GCC event multiplier
            multiplier = _get_event_multiplier(ev_type)

            # Distance and spatial decay
            dist_km = _haversine_km(node_lat, node_lng, ev_lat, ev_lng)
            lambda_d = _get_lambda_d(ev_type, context)
            spatial_decay_val = float(np.exp(-lambda_d * dist_km))

            # Proximity band weight
            band_weight = _proximity_band_weight(dist_km)

            # Temporal decay
            hours = hours_map.get(ev_id, 0.0)
            lambda_t = _get_lambda_t(ev_type)
            temporal_decay_val = float(np.exp(-lambda_t * hours))

            # Final contribution: severity * multiplier * spatial * band * temporal
            contribution = raw_severity * multiplier * spatial_decay_val * band_weight * temporal_decay_val
            total_threat += contribution

            contributions.append(ThreatContribution(
                event_id=ev_id,
                event_type=ev_type,
                multiplier=multiplier,
                distance_km=dist_km,
                proximity_band_weight=band_weight,
                spatial_decay=spatial_decay_val,
                temporal_decay=temporal_decay_val,
                raw_severity=raw_severity,
                final_contribution=contribution,
            ))

        # Clamp to [0, 1]
        total_threat = float(np.clip(total_threat, 0.0, 1.0))

        # Sort contributions by impact
        contributions.sort(key=lambda c: c.final_contribution, reverse=True)

        dominant = contributions[0].event_id if contributions else None

        node_results[node_id] = NodeThreatResult(
            node_id=node_id,
            threat_value=total_threat,
            dominant_event_id=dominant,
            contributions=contributions,
        )
        all_threat_values.append(total_threat)

    threat_arr = np.array(all_threat_values) if all_threat_values else np.array([0.0])
    hotspot_ids = [nid for nid, nr in node_results.items() if nr.threat_value >= hotspot_threshold]

    return GCCThreatFieldResult(
        node_results=node_results,
        global_max_threat=float(np.max(threat_arr)),
        global_mean_threat=float(np.mean(threat_arr)),
        hotspot_node_ids=hotspot_ids,
        config_snapshot={
            "lambda_d_default": LAMBDA_D_DEFAULT,
            "lambda_d_maritime_chokepoint": LAMBDA_D_MARITIME_CHOKEPOINT,
            "lambda_d_urban": LAMBDA_D_URBAN,
            "lambda_t_kinetic": LAMBDA_T_KINETIC,
            "lambda_t_soft": LAMBDA_T_SOFT,
            "proximity_bands": PROXIMITY_BANDS,
            "context": context,
            "event_multipliers_used": list(EVENT_MULTIPLIERS.keys()),
        },
    )
