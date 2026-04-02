"""Regression tests for exact GCC weight configurations.

These tests lock in the exact calibrated coefficients to prevent
accidental modification. Any change to weights must be deliberate.
"""

import pytest

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
    DISRUPTION,
    FRICTION,
    PRESSURE,
    SHOCKWAVE,
    POTENTIAL_ROUTING,
    SYSTEM_STRESS,
    INSURANCE_EXPOSURE,
    CLAIMS_SURGE,
    CLAIMS_UPLIFT,
)


class TestAssetClassWeights:
    def test_airport_weights(self):
        assert RISK_WEIGHTS_BY_ASSET[AssetClass.AIRPORT] == [0.27, 0.16, 0.19, 0.17, 0.11, 0.10]

    def test_seaport_weights(self):
        assert RISK_WEIGHTS_BY_ASSET[AssetClass.SEAPORT] == [0.24, 0.14, 0.22, 0.23, 0.09, 0.08]

    def test_air_corridor_weights(self):
        assert RISK_WEIGHTS_BY_ASSET[AssetClass.AIR_CORRIDOR] == [0.28, 0.13, 0.21, 0.20, 0.10, 0.08]

    def test_maritime_corridor_weights(self):
        assert RISK_WEIGHTS_BY_ASSET[AssetClass.MARITIME_CORRIDOR] == [0.30, 0.12, 0.20, 0.24, 0.08, 0.06]

    def test_weights_sum_to_one(self):
        for ac, weights in RISK_WEIGHTS_BY_ASSET.items():
            assert abs(sum(weights) - 1.0) < 0.01, f"{ac}: sum={sum(weights)}"

    def test_all_asset_classes_covered(self):
        for ac in AssetClass:
            assert ac in RISK_WEIGHTS_BY_ASSET


class TestEventMultipliers:
    def test_kinetic_multipliers(self):
        assert EVENT_MULTIPLIERS["missile_strike"] == 1.40
        assert EVENT_MULTIPLIERS["naval_attack"] == 1.40
        assert EVENT_MULTIPLIERS["airspace_strike"] == 1.40

    def test_infrastructure_multipliers(self):
        assert EVENT_MULTIPLIERS["port_closure"] == 1.35
        assert EVENT_MULTIPLIERS["chokepoint_threat"] == 1.35
        assert EVENT_MULTIPLIERS["airport_shutdown"] == 1.30

    def test_soft_signal_multipliers(self):
        assert EVENT_MULTIPLIERS["diplomatic_tension"] == 0.60
        assert EVENT_MULTIPLIERS["rumor_unverified"] == 0.40


class TestDecayConstants:
    def test_spatial_decay(self):
        assert LAMBDA_D_DEFAULT == 0.005
        assert LAMBDA_D_MARITIME_CHOKEPOINT == 0.0035
        assert LAMBDA_D_URBAN == 0.006

    def test_temporal_decay(self):
        assert LAMBDA_T_KINETIC == 0.015
        assert LAMBDA_T_SOFT == 0.035


class TestProximityBands:
    def test_band_count(self):
        assert len(PROXIMITY_BANDS) == 5

    def test_exact_bands(self):
        assert PROXIMITY_BANDS[0] == (0, 100, 1.00)
        assert PROXIMITY_BANDS[1] == (100, 250, 0.80)
        assert PROXIMITY_BANDS[2] == (250, 500, 0.55)
        assert PROXIMITY_BANDS[3] == (500, 900, 0.30)
        assert PROXIMITY_BANDS[4] == (900, 1e9, 0.10)


class TestPhysicsCoefficients:
    def test_shockwave_params(self):
        assert SHOCKWAVE.alpha == 0.58
        assert SHOCKWAVE.beta == 0.92
        assert SHOCKWAVE.delta == 0.47

    def test_pressure_params(self):
        assert PRESSURE.rho == 0.72
        assert PRESSURE.kappa == 0.18
        assert PRESSURE.omega == 0.14
        assert PRESSURE.xi == 0.30

    def test_friction_weights(self):
        assert FRICTION.threat_along_route == 0.35
        assert FRICTION.congestion == 0.25
        assert FRICTION.political_constraint == 0.25
        assert FRICTION.regulatory_restriction == 0.15

    def test_potential_routing_weights(self):
        assert POTENTIAL_ROUTING.distance == 0.18
        assert POTENTIAL_ROUTING.time == 0.22
        assert POTENTIAL_ROUTING.threat_integral == 0.28
        assert POTENTIAL_ROUTING.friction == 0.20
        assert POTENTIAL_ROUTING.congestion == 0.12


class TestCentralityWeights:
    def test_centrality(self):
        assert CENTRALITY.betweenness == 0.30
        assert CENTRALITY.degree == 0.15
        assert CENTRALITY.flow_share == 0.30
        assert CENTRALITY.chokepoint_dependency == 0.25


class TestInsuranceWeights:
    def test_exposure(self):
        assert INSURANCE_EXPOSURE.tiv == 0.30
        assert INSURANCE_EXPOSURE.route_dependency == 0.25
        assert INSURANCE_EXPOSURE.region_risk == 0.25
        assert INSURANCE_EXPOSURE.claims_elasticity == 0.20

    def test_claims_surge(self):
        assert CLAIMS_SURGE.risk == 0.28
        assert CLAIMS_SURGE.disruption == 0.30
        assert CLAIMS_SURGE.exposure == 0.25
        assert CLAIMS_SURGE.policy_sensitivity == 0.17

    def test_claims_uplift(self):
        assert CLAIMS_UPLIFT.chi1 == 0.45
        assert CLAIMS_UPLIFT.chi2 == 0.30
        assert CLAIMS_UPLIFT.chi3 == 0.25
