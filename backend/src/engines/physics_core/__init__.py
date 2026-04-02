"""GCC-tuned physics core — wraps physics/ modules with exact calibrated coefficients.

Every function in this package uses the GCC-specific weight configurations from
math_core/gcc_weights.py as defaults, producing explainable results with full
factor breakdowns.

Modules:
    threat_field        GCC-tuned threat field with EVENT_MULTIPLIERS and PROXIMITY_BANDS
    flow_field          GCC-tuned flow field with PotentialRoutingWeights for congestion
    friction            GCC-tuned corridor friction with FrictionWeights (mu1-mu4)
    pressure            GCC-tuned pressure accumulation with PressureParams (rho/kappa/omega/xi)
    shockwave           GCC-tuned shockwave propagation with ShockwaveParams (alpha/beta/delta)
    potential_routing   GCC-tuned potential routing with PotentialRoutingWeights (theta1-5)
    system_stress       GCC-tuned system stress aggregator with SystemStressWeights
"""

from __future__ import annotations
