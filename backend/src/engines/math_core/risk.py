"""GCC-tuned risk scoring — exact equations with asset-class-specific weights.

Core Risk Equation:
    R_i(t) = w1*G_i(t) + w2*P_i(t) + w3*N_i(t) + w4*L_i(t) + w5*T_i(t) + w6*U_i(t)

Where:
    G = Geopolitical threat field
    P = Proximity effect
    N = Network centrality
    L = Logistics pressure
    T = Temporal persistence
    U = Uncertainty penalty
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    AssetClass,
    RISK_WEIGHTS_BY_ASSET,
    EVENT_MULTIPLIERS,
    LAMBDA_D_DEFAULT,
    LAMBDA_D_MARITIME_CHOKEPOINT,
    LAMBDA_D_URBAN,
    LAMBDA_T_KINETIC,
    LAMBDA_T_SOFT,
    PROXIMITY_BANDS,
    CENTRALITY,
    LOGISTICS,
    UNCERTAINTY,
)


@dataclass
class ThreatSource:
    """A geopolitical event generating a threat field."""
    event_type: str
    severity: float  # [0, 1]
    confidence: float  # [0, 1]
    lat: float
    lng: float
    hours_ago: float = 0.0
    is_kinetic: bool = False


@dataclass
class NodeContext:
    """All context needed to score a single node."""
    node_id: str
    asset_class: AssetClass
    lat: float
    lng: float

    # Network centrality inputs
    betweenness: float = 0.0
    degree: float = 0.0
    flow_share: float = 0.0
    chokepoint_dependency: float = 0.0

    # Logistics inputs
    queue_depth: float = 0.0
    delay: float = 0.0
    reroute_cost: float = 0.0
    capacity_stress: float = 0.0

    # Uncertainty inputs
    source_quality: float = 1.0
    cross_validation: float = 1.0
    data_freshness: float = 1.0
    signal_agreement: float = 1.0


@dataclass
class RiskBreakdown:
    """Full explainable risk breakdown for one node."""
    node_id: str
    asset_class: str
    risk_score: float
    geopolitical: float
    proximity: float
    network: float
    logistics: float
    temporal: float
    uncertainty: float
    weights: list[float]
    dominant_factor: str
    threat_contributions: list[dict]


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---- Component G: Geopolitical Threat Field ----

def compute_geopolitical_threat(
    node_lat: float,
    node_lng: float,
    threats: list[ThreatSource],
    lambda_d: float = LAMBDA_D_DEFAULT,
) -> tuple[float, list[dict]]:
    """Phi_e(i,t) = M_e * Sev_e * Conf_e * exp(-λd * d) * exp(-λt * Δt)

    Returns aggregated threat and per-source contributions.
    """
    total = 0.0
    contributions: list[dict] = []

    for t in threats:
        M_e = EVENT_MULTIPLIERS.get(t.event_type, 0.60)
        d_km = haversine_km(node_lat, node_lng, t.lat, t.lng)
        lambda_t = LAMBDA_T_KINETIC if t.is_kinetic else LAMBDA_T_SOFT

        spatial = math.exp(-lambda_d * d_km)
        temporal = math.exp(-lambda_t * t.hours_ago)
        phi = M_e * t.severity * t.confidence * spatial * temporal

        total += phi
        contributions.append({
            "event_type": t.event_type,
            "multiplier": M_e,
            "distance_km": round(d_km, 1),
            "spatial_decay": round(spatial, 6),
            "temporal_decay": round(temporal, 6),
            "phi": round(phi, 6),
        })

    return float(np.clip(total, 0.0, 1.0)), contributions


# ---- Component P: Proximity Effect ----

def compute_proximity_effect(
    node_lat: float,
    node_lng: float,
    threats: list[ThreatSource],
) -> float:
    """Proximity band scoring using distance bands.

    Returns max proximity factor across all threats.
    """
    if not threats:
        return 0.0

    max_prox = 0.0
    for t in threats:
        d_km = haversine_km(node_lat, node_lng, t.lat, t.lng)
        for lo, hi, factor in PROXIMITY_BANDS:
            if lo <= d_km < hi:
                weighted = factor * t.severity * t.confidence
                max_prox = max(max_prox, weighted)
                break

    return float(np.clip(max_prox, 0.0, 1.0))


# ---- Component N: Network Centrality ----

def compute_network_centrality(ctx: NodeContext) -> float:
    """N_i = α1*betweenness + α2*degree + α3*flow_share + α4*chokepoint_dep"""
    return float(np.clip(
        CENTRALITY.betweenness * ctx.betweenness
        + CENTRALITY.degree * ctx.degree
        + CENTRALITY.flow_share * ctx.flow_share
        + CENTRALITY.chokepoint_dependency * ctx.chokepoint_dependency,
        0.0,
        1.0,
    ))


# ---- Component L: Logistics Pressure ----

def compute_logistics_pressure(ctx: NodeContext) -> float:
    """L_i = β1*queue + β2*delay + β3*reroute_cost + β4*capacity_stress"""
    return float(np.clip(
        LOGISTICS.queue_depth * ctx.queue_depth
        + LOGISTICS.delay * ctx.delay
        + LOGISTICS.reroute_cost * ctx.reroute_cost
        + LOGISTICS.capacity_stress * ctx.capacity_stress,
        0.0,
        1.0,
    ))


# ---- Component T: Temporal Persistence ----

def compute_temporal_persistence(
    threats: list[ThreatSource],
) -> float:
    """Aggregate temporal persistence across active threats.

    Uses kinetic/soft lambda_t to weight recent vs stale signals.
    """
    if not threats:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0
    for t in threats:
        lambda_t = LAMBDA_T_KINETIC if t.is_kinetic else LAMBDA_T_SOFT
        decay = math.exp(-lambda_t * t.hours_ago)
        w = t.severity * t.confidence
        weighted_sum += w * decay
        weight_total += w

    if weight_total == 0:
        return 0.0

    return float(np.clip(weighted_sum / weight_total, 0.0, 1.0))


# ---- Component U: Uncertainty Penalty ----

def compute_uncertainty_penalty(ctx: NodeContext) -> float:
    """U_i = 1 - (η1*source_quality + η2*cross_val + η3*freshness + η4*agreement)"""
    certainty = (
        UNCERTAINTY.source_quality * ctx.source_quality
        + UNCERTAINTY.cross_validation * ctx.cross_validation
        + UNCERTAINTY.data_freshness * ctx.data_freshness
        + UNCERTAINTY.signal_agreement * ctx.signal_agreement
    )
    return float(np.clip(1.0 - certainty, 0.0, 1.0))


# ---- Composite Risk Score ----

def compute_risk_score(
    ctx: NodeContext,
    threats: list[ThreatSource],
    lambda_d: float | None = None,
) -> RiskBreakdown:
    """R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U

    Full GCC-tuned risk score with asset-class-specific weights.
    """
    if lambda_d is None:
        if ctx.asset_class == AssetClass.MARITIME_CORRIDOR:
            lambda_d = LAMBDA_D_MARITIME_CHOKEPOINT
        elif ctx.asset_class in (AssetClass.INFRASTRUCTURE, AssetClass.SOCIETY):
            lambda_d = LAMBDA_D_URBAN
        else:
            lambda_d = LAMBDA_D_DEFAULT

    weights = RISK_WEIGHTS_BY_ASSET[ctx.asset_class]

    G, threat_contribs = compute_geopolitical_threat(ctx.lat, ctx.lng, threats, lambda_d)
    P = compute_proximity_effect(ctx.lat, ctx.lng, threats)
    N = compute_network_centrality(ctx)
    L = compute_logistics_pressure(ctx)
    T = compute_temporal_persistence(threats)
    U = compute_uncertainty_penalty(ctx)

    components = [G, P, N, L, T, U]
    risk = sum(w * c for w, c in zip(weights, components))
    risk = float(np.clip(risk, 0.0, 1.0))

    # Dominant factor
    weighted_components = {
        "geopolitical": weights[0] * G,
        "proximity": weights[1] * P,
        "network": weights[2] * N,
        "logistics": weights[3] * L,
        "temporal": weights[4] * T,
        "uncertainty": weights[5] * U,
    }
    dominant = max(weighted_components, key=weighted_components.get)

    return RiskBreakdown(
        node_id=ctx.node_id,
        asset_class=ctx.asset_class.value,
        risk_score=risk,
        geopolitical=G,
        proximity=P,
        network=N,
        logistics=L,
        temporal=T,
        uncertainty=U,
        weights=weights,
        dominant_factor=dominant,
        threat_contributions=threat_contribs,
    )


# ---- Vectorized batch scoring ----

def compute_risk_vector(
    nodes: list[NodeContext],
    threats: list[ThreatSource],
) -> tuple[NDArray[np.float64], list[RiskBreakdown]]:
    """Score all nodes in batch. Returns (risk_vector, breakdowns)."""
    breakdowns = [compute_risk_score(ctx, threats) for ctx in nodes]
    vector = np.array([b.risk_score for b in breakdowns], dtype=np.float64)
    return vector, breakdowns
