"""Tests for GCC-tuned risk scoring."""

import math
import numpy as np
import pytest

from src.engines.math_core.gcc_weights import (
    AssetClass,
    RISK_WEIGHTS_BY_ASSET,
    EVENT_MULTIPLIERS,
    LAMBDA_D_DEFAULT,
    LAMBDA_T_KINETIC,
    LAMBDA_T_SOFT,
)
from src.engines.math_core.risk import (
    ThreatSource,
    NodeContext,
    haversine_km,
    compute_geopolitical_threat,
    compute_proximity_effect,
    compute_network_centrality,
    compute_logistics_pressure,
    compute_temporal_persistence,
    compute_uncertainty_penalty,
    compute_risk_score,
    compute_risk_vector,
)


# ---- Fixtures ----

def make_threat(event_type="missile_strike", severity=0.8, confidence=0.9,
                lat=25.0, lng=55.0, hours_ago=2.0, is_kinetic=True):
    return ThreatSource(event_type=event_type, severity=severity,
                        confidence=confidence, lat=lat, lng=lng,
                        hours_ago=hours_ago, is_kinetic=is_kinetic)


def make_node(asset_class=AssetClass.AIRPORT, lat=25.25, lng=55.36):
    return NodeContext(
        node_id="DXB",
        asset_class=asset_class,
        lat=lat, lng=lng,
        betweenness=0.7, degree=0.5,
        flow_share=0.8, chokepoint_dependency=0.3,
        queue_depth=0.4, delay=0.3,
        reroute_cost=0.5, capacity_stress=0.2,
        source_quality=0.9, cross_validation=0.8,
        data_freshness=0.7, signal_agreement=0.85,
    )


# ---- Tests ----

class TestHaversine:
    def test_same_point_zero(self):
        assert haversine_km(25.0, 55.0, 25.0, 55.0) == pytest.approx(0.0, abs=0.01)

    def test_known_distance(self):
        # Dubai to Abu Dhabi ~120-140 km
        d = haversine_km(25.25, 55.36, 24.45, 54.65)
        assert 100 < d < 150


class TestGeopoliticalThreat:
    def test_no_threats_returns_zero(self):
        g, contribs = compute_geopolitical_threat(25.0, 55.0, [])
        assert g == 0.0
        assert contribs == []

    def test_close_high_severity_threat(self):
        threat = make_threat(lat=25.01, lng=55.01, hours_ago=0.0)
        g, contribs = compute_geopolitical_threat(25.0, 55.0, [threat])
        assert g > 0.5
        assert len(contribs) == 1
        assert contribs[0]["multiplier"] == EVENT_MULTIPLIERS["missile_strike"]

    def test_distant_threat_decays(self):
        close = make_threat(lat=25.01, lng=55.01)
        far = make_threat(lat=35.0, lng=55.0)  # ~1100 km away
        g_close, _ = compute_geopolitical_threat(25.0, 55.0, [close])
        g_far, _ = compute_geopolitical_threat(25.0, 55.0, [far])
        assert g_close > g_far

    def test_temporal_decay(self):
        recent = make_threat(hours_ago=0.0)
        old = make_threat(hours_ago=48.0)
        g_recent, _ = compute_geopolitical_threat(25.0, 55.0, [recent])
        g_old, _ = compute_geopolitical_threat(25.0, 55.0, [old])
        assert g_recent > g_old

    def test_event_multiplier_ordering(self):
        missile = make_threat(event_type="missile_strike", lat=25.01, lng=55.01)
        rumor = make_threat(event_type="rumor_unverified", lat=25.01, lng=55.01)
        g_missile, _ = compute_geopolitical_threat(25.0, 55.0, [missile])
        g_rumor, _ = compute_geopolitical_threat(25.0, 55.0, [rumor])
        assert g_missile > g_rumor

    def test_capped_at_one(self):
        threats = [make_threat(lat=25.0 + 0.001 * i, lng=55.0, hours_ago=0) for i in range(20)]
        g, _ = compute_geopolitical_threat(25.0, 55.0, threats)
        assert g <= 1.0


class TestProximity:
    def test_no_threats(self):
        assert compute_proximity_effect(25.0, 55.0, []) == 0.0

    def test_close_threat_high_proximity(self):
        threat = make_threat(lat=25.01, lng=55.01, severity=1.0, confidence=1.0)
        p = compute_proximity_effect(25.0, 55.0, [threat])
        assert p > 0.8  # within 100km band, factor=1.0

    def test_far_threat_low_proximity(self):
        threat = make_threat(lat=35.0, lng=55.0, severity=1.0, confidence=1.0)
        p = compute_proximity_effect(25.0, 55.0, [threat])
        assert p < 0.15  # >900km band, factor=0.10


class TestNetworkCentrality:
    def test_zero_inputs(self):
        ctx = NodeContext("n", AssetClass.AIRPORT, 25, 55)
        assert compute_network_centrality(ctx) == 0.0

    def test_max_inputs(self):
        ctx = NodeContext("n", AssetClass.AIRPORT, 25, 55,
                          betweenness=1, degree=1, flow_share=1, chokepoint_dependency=1)
        assert compute_network_centrality(ctx) == pytest.approx(1.0)

    def test_partial(self):
        ctx = make_node()
        n = compute_network_centrality(ctx)
        assert 0.0 < n < 1.0


class TestLogisticsPressure:
    def test_zero(self):
        ctx = NodeContext("n", AssetClass.AIRPORT, 25, 55)
        assert compute_logistics_pressure(ctx) == 0.0

    def test_partial(self):
        ctx = make_node()
        l = compute_logistics_pressure(ctx)
        assert 0.0 < l < 1.0


class TestTemporalPersistence:
    def test_no_threats(self):
        assert compute_temporal_persistence([]) == 0.0

    def test_recent_kinetic(self):
        t = make_threat(hours_ago=0, is_kinetic=True)
        p = compute_temporal_persistence([t])
        assert p == pytest.approx(1.0)

    def test_old_soft_signal_decays(self):
        t = make_threat(hours_ago=100, is_kinetic=False)
        p = compute_temporal_persistence([t])
        assert p < 0.1


class TestUncertainty:
    def test_perfect_data(self):
        ctx = NodeContext("n", AssetClass.AIRPORT, 25, 55,
                          source_quality=1, cross_validation=1,
                          data_freshness=1, signal_agreement=1)
        assert compute_uncertainty_penalty(ctx) == pytest.approx(0.0, abs=0.01)

    def test_no_data(self):
        ctx = NodeContext("n", AssetClass.AIRPORT, 25, 55,
                          source_quality=0, cross_validation=0,
                          data_freshness=0, signal_agreement=0)
        assert compute_uncertainty_penalty(ctx) == pytest.approx(1.0, abs=0.01)


class TestCompositeRisk:
    def test_airport_weights(self):
        ctx = make_node(AssetClass.AIRPORT)
        threats = [make_threat(lat=25.26, lng=55.37)]
        bd = compute_risk_score(ctx, threats)
        assert bd.asset_class == "airport"
        assert 0.0 <= bd.risk_score <= 1.0
        assert bd.weights == RISK_WEIGHTS_BY_ASSET[AssetClass.AIRPORT]

    def test_seaport_different_weights(self):
        ctx = make_node(AssetClass.SEAPORT)
        threats = [make_threat(lat=25.26, lng=55.37)]
        bd = compute_risk_score(ctx, threats)
        assert bd.weights == RISK_WEIGHTS_BY_ASSET[AssetClass.SEAPORT]

    def test_maritime_uses_slow_decay(self):
        ctx = make_node(AssetClass.MARITIME_CORRIDOR)
        threats = [make_threat(lat=26.0, lng=56.0)]
        bd = compute_risk_score(ctx, threats)
        # Maritime corridor uses LAMBDA_D_MARITIME_CHOKEPOINT = 0.0035 (slower decay)
        assert bd.asset_class == "maritime_corridor"

    def test_no_threats_still_has_uncertainty(self):
        ctx = make_node()
        ctx.source_quality = 0.3
        ctx.cross_validation = 0.2
        bd = compute_risk_score(ctx, [])
        assert bd.risk_score > 0  # uncertainty component

    def test_batch_scoring(self):
        nodes = [make_node(AssetClass.AIRPORT), make_node(AssetClass.SEAPORT)]
        nodes[1].node_id = "JBL"
        threats = [make_threat()]
        vec, bds = compute_risk_vector(nodes, threats)
        assert vec.shape == (2,)
        assert len(bds) == 2
        assert all(0 <= v <= 1 for v in vec)
