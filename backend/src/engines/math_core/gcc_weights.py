"""GCC weight configuration — asset-class-specific and equation-specific defaults.

Every weight in the system is centralized here for auditability and calibration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AssetClass(StrEnum):
    AIRPORT = "airport"
    SEAPORT = "seaport"
    AIR_CORRIDOR = "air_corridor"
    MARITIME_CORRIDOR = "maritime_corridor"
    INFRASTRUCTURE = "infrastructure"
    ECONOMY = "economy"
    FINANCE = "finance"
    SOCIETY = "society"


# ------------------------------------------------------------------
# Core risk weights: w = [w1(G), w2(P), w3(N), w4(L), w5(T), w6(U)]
# ------------------------------------------------------------------
RISK_WEIGHTS_BY_ASSET: dict[AssetClass, list[float]] = {
    AssetClass.AIRPORT:            [0.27, 0.16, 0.19, 0.17, 0.11, 0.10],
    AssetClass.SEAPORT:            [0.24, 0.14, 0.22, 0.23, 0.09, 0.08],
    AssetClass.AIR_CORRIDOR:       [0.28, 0.13, 0.21, 0.20, 0.10, 0.08],
    AssetClass.MARITIME_CORRIDOR:  [0.30, 0.12, 0.20, 0.24, 0.08, 0.06],
    AssetClass.INFRASTRUCTURE:     [0.26, 0.15, 0.20, 0.20, 0.10, 0.09],
    AssetClass.ECONOMY:            [0.25, 0.14, 0.18, 0.22, 0.11, 0.10],
    AssetClass.FINANCE:            [0.22, 0.12, 0.16, 0.20, 0.15, 0.15],
    AssetClass.SOCIETY:            [0.20, 0.18, 0.15, 0.15, 0.12, 0.20],
}

# ------------------------------------------------------------------
# Geopolitical threat multipliers M_e
# ------------------------------------------------------------------
EVENT_MULTIPLIERS: dict[str, float] = {
    "missile_strike":          1.40,
    "naval_attack":            1.40,
    "airspace_strike":         1.40,
    "port_closure":            1.35,
    "chokepoint_threat":       1.35,
    "airport_shutdown":        1.30,
    "infrastructure_damage":   1.25,
    "military_exercise":       1.10,
    "sanctions_escalation":    1.00,
    "cyber_attack":            0.95,
    "protest_near_infra":      0.90,
    "protest_civil_unrest":    0.75,
    "diplomatic_tension":      0.60,
    "rumor_unverified":        0.40,
}

# ------------------------------------------------------------------
# Distance decay lambda_d (per km)
# ------------------------------------------------------------------
LAMBDA_D_DEFAULT = 0.005
LAMBDA_D_MARITIME_CHOKEPOINT = 0.0035  # slower decay near Hormuz
LAMBDA_D_URBAN = 0.006  # faster decay in dense areas

# ------------------------------------------------------------------
# Temporal decay lambda_t (per hour)
# ------------------------------------------------------------------
LAMBDA_T_KINETIC = 0.015  # severe kinetic/missile/airspace
LAMBDA_T_SOFT = 0.035  # soft signal

# ------------------------------------------------------------------
# Proximity bands
# ------------------------------------------------------------------
PROXIMITY_BANDS: list[tuple[float, float, float]] = [
    (0,    100,  1.00),
    (100,  250,  0.80),
    (250,  500,  0.55),
    (500,  900,  0.30),
    (900,  1e9,  0.10),
]

# ------------------------------------------------------------------
# Network centrality weights (alpha)
# ------------------------------------------------------------------
@dataclass
class CentralityWeights:
    betweenness: float = 0.30
    degree: float = 0.15
    flow_share: float = 0.30
    chokepoint_dependency: float = 0.25


# ------------------------------------------------------------------
# Logistics pressure weights (beta)
# ------------------------------------------------------------------
@dataclass
class LogisticsWeights:
    queue_depth: float = 0.25
    delay: float = 0.25
    reroute_cost: float = 0.30
    capacity_stress: float = 0.20


# ------------------------------------------------------------------
# Uncertainty penalty weights (eta)
# ------------------------------------------------------------------
@dataclass
class UncertaintyWeights:
    source_quality: float = 0.30
    cross_validation: float = 0.30
    data_freshness: float = 0.20
    signal_agreement: float = 0.20


# ------------------------------------------------------------------
# Disruption weights (v)
# ------------------------------------------------------------------
@dataclass
class DisruptionWeights:
    risk: float = 0.28
    congestion: float = 0.22
    accessibility_loss: float = 0.18
    reroute_penalty: float = 0.22
    boundary_restriction: float = 0.10


# ------------------------------------------------------------------
# Physics: friction weights (mu)
# ------------------------------------------------------------------
@dataclass
class FrictionWeights:
    base: float = 0.0
    threat_along_route: float = 0.35
    congestion: float = 0.25
    political_constraint: float = 0.25
    regulatory_restriction: float = 0.15


# ------------------------------------------------------------------
# Physics: pressure accumulation
# ------------------------------------------------------------------
@dataclass
class PressureParams:
    rho: float = 0.72   # persistence
    kappa: float = 0.18  # inflow coefficient
    omega: float = 0.14  # outflow coefficient
    xi: float = 0.30     # shock coefficient


# ------------------------------------------------------------------
# Physics: shockwave propagation
# ------------------------------------------------------------------
@dataclass
class ShockwaveParams:
    alpha: float = 0.58  # adjacency propagation
    beta: float = 0.92   # shock sensitivity
    delta: float = 0.47  # external perturbation


# ------------------------------------------------------------------
# Physics: potential routing
# ------------------------------------------------------------------
@dataclass
class PotentialRoutingWeights:
    distance: float = 0.18
    time: float = 0.22
    threat_integral: float = 0.28
    friction: float = 0.20
    congestion: float = 0.12


# ------------------------------------------------------------------
# Physics: system stress
# ------------------------------------------------------------------
@dataclass
class SystemStressWeights:
    congestion: float = 0.35
    risk: float = 0.30
    uncertainty: float = 0.20
    insurance_severity: float = 0.15


# ------------------------------------------------------------------
# Insurance weights
# ------------------------------------------------------------------
@dataclass
class InsuranceExposureWeights:
    tiv: float = 0.30
    route_dependency: float = 0.25
    region_risk: float = 0.25
    claims_elasticity: float = 0.20


@dataclass
class ClaimsSurgeWeights:
    risk: float = 0.28
    disruption: float = 0.30
    exposure: float = 0.25
    policy_sensitivity: float = 0.17


@dataclass
class ClaimsUpliftParams:
    chi1: float = 0.45
    chi2: float = 0.30
    chi3: float = 0.25


# Singletons
CENTRALITY = CentralityWeights()
LOGISTICS = LogisticsWeights()
UNCERTAINTY = UncertaintyWeights()
DISRUPTION = DisruptionWeights()
FRICTION = FrictionWeights()
PRESSURE = PressureParams()
SHOCKWAVE = ShockwaveParams()
POTENTIAL_ROUTING = PotentialRoutingWeights()
SYSTEM_STRESS = SystemStressWeights()
INSURANCE_EXPOSURE = InsuranceExposureWeights()
CLAIMS_SURGE = ClaimsSurgeWeights()
CLAIMS_UPLIFT = ClaimsUpliftParams()
