"""
GCC Physics Intelligence Module Configuration.

Consolidated repository of all GCC (Global Coordination Core) physics defaults,
constants, and parameters used across the physics intelligence system. These
values are empirically derived from Impact Observatory calibration
and represent production defaults for all physics-inspired models.

Architecture:
- THREAT_FIELD_*: Threat field computation (Gaussian decay, pressure accumulation)
- SHOCKWAVE_*: Shockwave propagation (wave speed, decay rate, magnitude scaling)
- PRESSURE_*: Node pressure accumulation (inflow/outflow dynamics, shock coupling)
- FRICTION_*: Route friction/resistance model (multi-factor weighting)
- POTENTIAL_ROUTING_*: Potential field routing (cost functional weighting, normalization)
- SYSTEM_STRESS_*: System-level stress aggregation (component weighting)

All values are type-hinted and documented with physics interpretations.
"""

from typing import Dict, Tuple


# ============================================================================
# THREAT FIELD CONFIGURATION
# ============================================================================

# Gaussian decay parameters for threat field propagation
THREAT_FIELD_SIGMA: float = 85.0
"""
Sigma parameter for Gaussian threat decay (in km).
Controls spatial extent of threat influence. Larger values = wider influence.
Physics: Characteristic length scale of threat propagation.
"""

THREAT_FIELD_DECAY_POWER: float = 2.0
"""
Power law exponent for distance-based decay.
Physics: Quadratic decay models diffusive spreading in 2D space.
"""

THREAT_FIELD_MIN_THRESHOLD: float = 0.01
"""
Minimum threshold below which threat is treated as zero.
Computational efficiency: prevents negligible contributions.
"""

THREAT_FIELD_MAX_VALUE: float = 1.0
"""
Maximum clamped threat value [0, 1].
Normalization: ensures bounded output for scoring systems.
"""

THREAT_FIELD_TIME_DECAY_RATE: float = 0.05
"""
Exponential decay rate over time (per hour).
Physics: Threat intensity decreases as disruption is contained or resolved.
"""


# ============================================================================
# SHOCKWAVE CONFIGURATION
# ============================================================================

SHOCKWAVE_PROPAGATION_SPEED_KMH: float = 120.0
"""
Speed at which shockwave wavefront expands (in km/h).
Physics: Models how fast disruption propagates spatially.
"""

SHOCKWAVE_SPATIAL_DECAY_LAMBDA: float = 0.05
"""
Exponential spatial decay rate (inverse length scale in 1/km).
Formula: intensity = magnitude * exp(-lambda * distance)
Physics: Characteristic decay distance = 1/lambda = 20 km.
"""

SHOCKWAVE_MAGNITUDE_SCALE: float = 1.0
"""
Scaling factor for shock event magnitudes.
Applied as multiplier to reported event intensity.
"""

SHOCKWAVE_AMPLITUDE_DAMPING: float = 0.92
"""
Damping coefficient for shockwave amplitude.
Physics: Models energy dissipation as wave propagates.
"""

SHOCKWAVE_DECAY_FACTOR: float = 0.58
"""
Recursive decay factor for successive shockwave pulses.
Used in pressure coupling: R(t+1) = alpha*A*R(t) + ...
Physics: Models oscillation damping in system response.
"""

SHOCKWAVE_ENERGY_COUPLING: float = 0.47
"""
Energy coupling coefficient from external energy sources.
Used in pressure coupling: R(t+1) = ... + delta*E
Physics: Determines how external disruptions drive system shock.
"""


# ============================================================================
# PRESSURE ACCUMULATION CONFIGURATION
# ============================================================================

PRESSURE_PERSISTENCE_FACTOR: float = 0.72
"""
Recursive persistence of pressure across time steps.
Formula: C_i(t+1) = rho*C_i(t) + kappa*Inflow - omega*Outflow + xi*Shock
Physics: Memory effect - previous pressure persists into next step.
Range: [0, 1] where 0 = no memory, 1 = perfect memory.
"""

PRESSURE_INFLOW_COUPLING: float = 0.18
"""
Sensitivity of pressure to incoming flow.
Formula: C_i(t+1) = rho*C_i(t) + kappa*Inflow_i(t) + ...
Physics: Inflow drives pressure increase at node.
"""

PRESSURE_OUTFLOW_DAMPING: float = 0.14
"""
Sensitivity of pressure relief from outgoing flow.
Formula: C_i(t+1) = ... - omega*Outflow_i(t) + ...
Physics: Outflow removes pressure, prevents unbounded accumulation.
"""

PRESSURE_SHOCK_COUPLING: float = 0.30
"""
Shock intensity transfer to node pressure.
Formula: C_i(t+1) = ... + xi*Shock_i(t)
Physics: External disruptions directly couple to local pressure.
"""

PRESSURE_INFLOW_BASELINE: float = 0.1
"""
Baseline inflow for estimation when data unavailable.
Used in accumulate_pressure() for disrupted route load estimation.
"""

PRESSURE_REROUTE_INEFFICIENCY: float = 1.3
"""
Load multiplication factor when traffic reroutes.
Physics: Longer alternate routes and extra hops increase effective load by 30%.
"""


# ============================================================================
# FRICTION/RESISTANCE CONFIGURATION
# ============================================================================

FRICTION_BASE_COEFFICIENT: float = 0.10
"""
Base friction coefficient (minimum resistance).
Formula: mu_r = mu0 + mu1*Threat + mu2*Congestion + mu3*Political + mu4*Regulatory
Physics: Intrinsic route resistance independent of operational factors.
"""

FRICTION_THREAT_WEIGHT: float = 0.35
"""
Weight coefficient for threat impact on friction.
Physics: Security/threat factors dominate route viability assessment.
"""

FRICTION_CONGESTION_WEIGHT: float = 0.25
"""
Weight coefficient for congestion impact on friction.
Physics: Traffic density increases resistance through delay and rerouting.
"""

FRICTION_POLITICAL_WEIGHT: float = 0.25
"""
Weight coefficient for political constraints on friction.
Physics: Diplomatic restrictions and transit agreements create resistance.
"""

FRICTION_REGULATORY_WEIGHT: float = 0.15
"""
Weight coefficient for regulatory restrictions on friction.
Physics: Compliance overhead and certification requirements slow passage.
"""

FRICTION_CLASS_LOW_THRESHOLD: float = 0.35
"""
Upper threshold for LOW friction classification.
Routes with friction < 0.35: readily viable.
"""

FRICTION_CLASS_MEDIUM_THRESHOLD: float = 0.60
"""
Upper threshold for MEDIUM friction classification.
Routes with friction < 0.60: acceptable with minor delays.
"""

FRICTION_CLASS_HIGH_THRESHOLD: float = 0.85
"""
Upper threshold for HIGH friction classification.
Routes with friction < 0.85: degraded but feasible.
Routes with friction >= 0.85: CRITICAL, not recommended.
"""


# ============================================================================
# POTENTIAL FIELD ROUTING CONFIGURATION
# ============================================================================

ROUTING_DISTANCE_WEIGHT: float = 0.18
"""
Weight for distance component in route cost functional.
Formula: J_r = theta1*Distance + theta2*Time + theta3*ThreatIntegral
         + theta4*Friction + theta5*Congestion
Physics: Geometric distance contributes moderately to route cost.
"""

ROUTING_TIME_WEIGHT: float = 0.22
"""
Weight for transit time in route cost.
Physics: Time criticality drives significant cost contribution.
"""

ROUTING_THREAT_INTEGRAL_WEIGHT: float = 0.28
"""
Weight for integrated threat along route.
Physics: Security threat dominates routing decisions (28% of total cost).
"""

ROUTING_FRICTION_WEIGHT: float = 0.20
"""
Weight for route friction/resistance in cost.
Physics: Operational constraints (friction) moderately important.
"""

ROUTING_CONGESTION_WEIGHT: float = 0.12
"""
Weight for congestion along route.
Physics: Real-time congestion has minor weight vs. threat/friction.
"""

ROUTING_DISTANCE_NORMALIZATION: float = 5000.0
"""
Normalization scale for distance [km].
Converts raw distance to [0, 1] range for cost computation.
Physics: Routes up to 5000 km span expected operational theater.
"""

ROUTING_TIME_NORMALIZATION: float = 100.0
"""
Normalization scale for transit time [hours].
Routes up to 100 hours (4+ days) span expected transit durations.
"""

ROUTING_THREAT_INTEGRAL_SATURATION: float = 1.0
"""
Saturation parameter for threat integral normalization.
Formula: normalized = 1 - exp(-threat_integral / saturation)
Prevents unbounded threat accumulation; limits max contribution to 1.0.
"""

ROUTING_VIABILITY_OPTIMAL_THRESHOLD: float = 0.40
"""
Upper threshold for OPTIMAL viability classification.
Routes with cost < 0.40: best available options.
"""

ROUTING_VIABILITY_ACCEPTABLE_THRESHOLD: float = 0.65
"""
Upper threshold for ACCEPTABLE viability classification.
Routes with cost < 0.65: usable alternatives.
"""

ROUTING_VIABILITY_DEGRADED_THRESHOLD: float = 0.90
"""
Upper threshold for DEGRADED viability classification.
Routes with cost < 0.90: limited availability.
Routes with cost >= 0.90: NON_VIABLE, not recommended.
"""


# ============================================================================
# SYSTEM STRESS CONFIGURATION
# ============================================================================

STRESS_PRESSURE_WEIGHT: float = 0.35
"""
Weight for pressure component in system stress aggregation.
Physics: Node load stress is primary system stress indicator (35%).
"""

STRESS_CONGESTION_WEIGHT: float = 0.30
"""
Weight for congestion component in system stress.
Physics: Flow density affects network capacity (30%).
"""

STRESS_DISRUPTION_WEIGHT: float = 0.20
"""
Weight for active disruptions in system stress.
Physics: Unresolved disruptions indicate system fragility (20%).
"""

STRESS_UNCERTAINTY_WEIGHT: float = 0.15
"""
Weight for epistemic uncertainty in system stress.
Physics: Unknown state contributes to overall risk (15%).
"""

STRESS_PRESSURE_NORMALIZATION: float = 2.0
"""
Normalization divisor for pressure component.
Raw pressure values divided by this for [0, 1] mapping.
Physics: Pressures exceed 1.0 under congestion; normalize to 2.0 scale.
"""

STRESS_DISRUPTION_DECAY_RATE: float = 0.5
"""
Decay rate for exponential disruption stress scaling.
Formula: stress = 1 - exp(-decay_rate * disruption_count)
Physics: Each additional disruption has multiplicative impact.
"""

STRESS_LEVEL_NOMINAL_THRESHOLD: float = 0.25
"""
Upper threshold for NOMINAL stress classification.
System stress < 0.25: nominal operation.
"""

STRESS_LEVEL_ELEVATED_THRESHOLD: float = 0.50
"""
Upper threshold for ELEVATED stress classification.
System stress < 0.50: elevated but manageable.
"""

STRESS_LEVEL_HIGH_THRESHOLD: float = 0.75
"""
Upper threshold for HIGH stress classification.
System stress < 0.75: high stress, intervention recommended.
System stress >= 0.75: CRITICAL, immediate action required.
"""


# ============================================================================
# UTILITY FUNCTIONS FOR CONFIG ACCESS
# ============================================================================

def get_threat_field_config() -> Dict[str, float]:
    """
    Get all threat field configuration parameters as dictionary.
    
    Returns:
        Dictionary with keys: sigma, decay_power, min_threshold, max_value,
        time_decay_rate
    """
    return {
        'sigma': THREAT_FIELD_SIGMA,
        'decay_power': THREAT_FIELD_DECAY_POWER,
        'min_threshold': THREAT_FIELD_MIN_THRESHOLD,
        'max_value': THREAT_FIELD_MAX_VALUE,
        'time_decay_rate': THREAT_FIELD_TIME_DECAY_RATE,
    }


def get_shockwave_config() -> Dict[str, float]:
    """Get all shockwave configuration parameters."""
    return {
        'propagation_speed_kmh': SHOCKWAVE_PROPAGATION_SPEED_KMH,
        'spatial_decay_lambda': SHOCKWAVE_SPATIAL_DECAY_LAMBDA,
        'magnitude_scale': SHOCKWAVE_MAGNITUDE_SCALE,
        'amplitude_damping': SHOCKWAVE_AMPLITUDE_DAMPING,
        'decay_factor': SHOCKWAVE_DECAY_FACTOR,
        'energy_coupling': SHOCKWAVE_ENERGY_COUPLING,
    }


def get_pressure_config() -> Dict[str, float]:
    """Get all pressure accumulation configuration parameters."""
    return {
        'persistence_factor': PRESSURE_PERSISTENCE_FACTOR,
        'inflow_coupling': PRESSURE_INFLOW_COUPLING,
        'outflow_damping': PRESSURE_OUTFLOW_DAMPING,
        'shock_coupling': PRESSURE_SHOCK_COUPLING,
        'inflow_baseline': PRESSURE_INFLOW_BASELINE,
        'reroute_inefficiency': PRESSURE_REROUTE_INEFFICIENCY,
    }


def get_friction_config() -> Dict[str, float]:
    """Get all friction/resistance configuration parameters."""
    return {
        'base_coefficient': FRICTION_BASE_COEFFICIENT,
        'threat_weight': FRICTION_THREAT_WEIGHT,
        'congestion_weight': FRICTION_CONGESTION_WEIGHT,
        'political_weight': FRICTION_POLITICAL_WEIGHT,
        'regulatory_weight': FRICTION_REGULATORY_WEIGHT,
        'low_threshold': FRICTION_CLASS_LOW_THRESHOLD,
        'medium_threshold': FRICTION_CLASS_MEDIUM_THRESHOLD,
        'high_threshold': FRICTION_CLASS_HIGH_THRESHOLD,
    }


def get_routing_config() -> Dict[str, float]:
    """Get all potential field routing configuration parameters."""
    return {
        'distance_weight': ROUTING_DISTANCE_WEIGHT,
        'time_weight': ROUTING_TIME_WEIGHT,
        'threat_integral_weight': ROUTING_THREAT_INTEGRAL_WEIGHT,
        'friction_weight': ROUTING_FRICTION_WEIGHT,
        'congestion_weight': ROUTING_CONGESTION_WEIGHT,
        'distance_normalization': ROUTING_DISTANCE_NORMALIZATION,
        'time_normalization': ROUTING_TIME_NORMALIZATION,
        'threat_integral_saturation': ROUTING_THREAT_INTEGRAL_SATURATION,
        'optimal_threshold': ROUTING_VIABILITY_OPTIMAL_THRESHOLD,
        'acceptable_threshold': ROUTING_VIABILITY_ACCEPTABLE_THRESHOLD,
        'degraded_threshold': ROUTING_VIABILITY_DEGRADED_THRESHOLD,
    }


def get_stress_config() -> Dict[str, float]:
    """Get all system stress configuration parameters."""
    return {
        'pressure_weight': STRESS_PRESSURE_WEIGHT,
        'congestion_weight': STRESS_CONGESTION_WEIGHT,
        'disruption_weight': STRESS_DISRUPTION_WEIGHT,
        'uncertainty_weight': STRESS_UNCERTAINTY_WEIGHT,
        'pressure_normalization': STRESS_PRESSURE_NORMALIZATION,
        'disruption_decay_rate': STRESS_DISRUPTION_DECAY_RATE,
        'nominal_threshold': STRESS_LEVEL_NOMINAL_THRESHOLD,
        'elevated_threshold': STRESS_LEVEL_ELEVATED_THRESHOLD,
        'high_threshold': STRESS_LEVEL_HIGH_THRESHOLD,
    }


def get_all_config() -> Dict[str, Dict[str, float]]:
    """
    Get all physics configuration as nested dictionary.
    
    Returns:
        Dictionary with keys: threat_field, shockwave, pressure, friction,
        routing, stress
    """
    return {
        'threat_field': get_threat_field_config(),
        'shockwave': get_shockwave_config(),
        'pressure': get_pressure_config(),
        'friction': get_friction_config(),
        'routing': get_routing_config(),
        'stress': get_stress_config(),
    }
