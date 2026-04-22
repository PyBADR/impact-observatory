"""
Integration tests for Impact Observatory.

Tests cross-module integration points including:
- Seed data loading via SeedLoader
- Mathematical core risk computation with GCC weights
- Physics intelligence modules (threat field, friction, shockwave, diffusion)
- Insurance intelligence (exposure, claims surge, underwriting)
- Scenario template loading and engine execution
- Decision output generation (5 mandatory questions)
- Mesa simulation bridge
- API model serialization
"""

# ─────────────────────────────────────────────────────────────────────────────
# QUARANTINED FOR v1.0.0 BASELINE
# ─────────────────────────────────────────────────────────────────────────────
# This test file imports from the abandoned `app.*` module tree (app.main /
# app.scenarios / app.intelligence / app.schemas / app.schema / app.orchestration).
# None of those modules exist in the current product architecture — product code
# lives under `src/*` and the module tree was not ported 1-to-1.
#
# Product runtime coverage for this surface is maintained by the active suites:
#   - tests/test_pipeline_contracts.py     (113 tests, 17-stage pipeline)
#   - tests/test_api_endpoints.py          (27 tests, HTTP contract)
#   - tests/test_macro_contracts.py        (64 tests, macro signal layer)
#   - tests/test_propagation_contracts.py  (64 tests, transmission)
#   - tests/unit/                          (201 tests, math/physics/scenario)
#
# Porting this file to src.* would be broad test-side refactor (out of v1.0.0
# stabilization scope). Defer to a post-v1.0.0 test-modernization sprint.
# ─────────────────────────────────────────────────────────────────────────────
import pytest
pytest.skip(
    "quarantined: imports abandoned app.* module tree; product runtime is covered "
    "by pipeline_contracts / api_endpoints / macro_contracts / propagation_contracts "
    "/ unit suites. See top-of-file governance note.",
    allow_module_level=True,
)

import pytest
from datetime import datetime, timedelta

# ============================================================================
# Layer 1: Schema
# ============================================================================
from app.schema.enums import (
    EventType, SeverityLevel, SourceType, TransportMode,
    AssetType, FlightStatus, VesselType, ScenarioStatus,
)
from app.schema.base import BaseEntity
from app.schema.geo import GeoPoint
from app.schema.events import Event
from app.schema.infrastructure import Airport, Port, Corridor

# ============================================================================
# Layer 2: Math Core
# ============================================================================
from app.intelligence.math_core.gcc_weights import (
    AIRPORT_WEIGHTS, SEAPORT_WEIGHTS, AIR_CORRIDOR_WEIGHTS,
    MARITIME_CORRIDOR_WEIGHTS, EVENT_MULTIPLIERS, CENTRALITY_WEIGHTS,
    LOGISTICS_WEIGHTS, DISRUPTION_WEIGHTS, UNCERTAINTY_WEIGHTS,
    ASSET_CLASS_WEIGHTS,
)
from app.intelligence.math_core.risk_score import compute_gcc_risk_score
from app.intelligence.math_core.geopolitical_threat import compute_geopolitical_threat
from app.intelligence.math_core.proximity import compute_proximity_score
from app.intelligence.math_core.network_centrality import compute_network_centrality
from app.intelligence.math_core.logistics_pressure import compute_logistics_pressure
from app.intelligence.math_core.temporal_persistence import compute_temporal_persistence
from app.intelligence.math_core.uncertainty import compute_uncertainty
from app.intelligence.math_core.disruption_score import compute_disruption_score
from app.intelligence.math_core.exposure_score import compute_exposure_score
from app.intelligence.math_core.state_vector import EntityStateVector, compute_state_vector
from app.intelligence.math_core.calibration import CalibrationEngine
from app.intelligence.math_core.scenario_delta import compute_scenario_delta

# ============================================================================
# Layer 3: Physics
# ============================================================================
from app.intelligence.physics.threat_field import ThreatField
from app.intelligence.physics.flow_field import FlowField
from app.intelligence.physics.friction import compute_friction
from app.intelligence.physics.pressure import PressureNode
from app.intelligence.physics.shockwave import ShockwaveEngine
from app.intelligence.physics.potential_routing import compute_route_cost
from app.intelligence.physics.diffusion import diffuse_threat
from app.intelligence.physics.system_stress import compute_system_stress
from app.intelligence.physics.gcc_physics_config import (
    FRICTION_THREAT_WEIGHT, PRESSURE_PERSISTENCE_FACTOR,
    SHOCKWAVE_DECAY_FACTOR, SHOCKWAVE_AMPLITUDE_DAMPING,
)

# ============================================================================
# Layer 4: Insurance
# ============================================================================
from app.intelligence.insurance.portfolio_exposure import compute_portfolio_exposure, PolicyExposure
from app.intelligence.insurance.claims_surge import compute_claims_surge_potential
from app.intelligence.insurance.claims_uplift import compute_expected_claims_uplift
from app.intelligence.insurance.underwriting_watch import compute_underwriting_restriction
from app.intelligence.insurance.severity_projection import project_severity
from app.intelligence.insurance.insurance_engine import InsuranceIntelligenceEngine
from app.intelligence.insurance.gcc_insurance_config import GCC_INSURANCE_CONFIG

# ============================================================================
# Layer 5: Scenarios
# ============================================================================
from app.scenarios.templates import SCENARIO_TEMPLATES, ScenarioTemplate
from app.scenarios.engine import ScenarioEngine
from app.scenarios.runner import ScenarioRunner

# ============================================================================
# Layer 6: Simulation
# ============================================================================
from app.simulation.mesa_model import GCCModel, InfrastructureAgent, EventAgent
from app.simulation.bridge import MesaBridge

# ============================================================================
# Layer 7: Decision
# ============================================================================
from app.decision.output import DecisionOutputGenerator

# ============================================================================
# Layer 8: Services
# ============================================================================
from app.services.scoring_service import ScoringService
from app.services.physics_service import PhysicsService
from app.services.insurance_service import InsuranceService
from app.services.pipeline_status import PipelineStatusTracker

# ============================================================================
# Layer 9: Seeds
# ============================================================================
from seeds.loader import SeedLoader

# ============================================================================
# Layer 10: API Models
# ============================================================================
from app.api.models import HealthResponse, ScenarioRequest, ScenarioResponse


# ============================================================================
# Tests
# ============================================================================


class TestSeedDataIntegration:
    """Test seed data loading from production seed files."""

    def test_seed_loader_loads_all(self):
        loader = SeedLoader()
        data = loader.load_all()
        assert isinstance(data, dict)
        total = sum(len(v) for v in data.values())
        assert total >= 175, f"Expected >=175 seed records, got {total}"

    def test_seed_events_exist(self):
        loader = SeedLoader()
        data = loader.load_all()
        assert "events" in data
        assert len(data["events"]) >= 50

    def test_seed_airports_exist(self):
        loader = SeedLoader()
        data = loader.load_all()
        assert "airports" in data
        assert len(data["airports"]) >= 30

    def test_seed_ports_exist(self):
        loader = SeedLoader()
        data = loader.load_all()
        assert "ports" in data
        assert len(data["ports"]) >= 20

    def test_seed_corridors_exist(self):
        loader = SeedLoader()
        data = loader.load_all()
        assert "corridors" in data
        assert len(data["corridors"]) >= 15


class TestGCCWeightsIntegration:
    """Test GCC weight configurations are correctly defined."""

    def test_airport_weights_sum_to_one(self):
        assert abs(sum(AIRPORT_WEIGHTS) - 1.0) < 0.01

    def test_seaport_weights_sum_to_one(self):
        assert abs(sum(SEAPORT_WEIGHTS) - 1.0) < 0.01

    def test_air_corridor_weights_sum_to_one(self):
        assert abs(sum(AIR_CORRIDOR_WEIGHTS) - 1.0) < 0.01

    def test_maritime_corridor_weights_sum_to_one(self):
        assert abs(sum(MARITIME_CORRIDOR_WEIGHTS) - 1.0) < 0.01

    def test_event_multipliers_exist(self):
        assert "missile_strike" in EVENT_MULTIPLIERS
        assert EVENT_MULTIPLIERS["missile_strike"] == 1.40
        assert "naval_attack" in EVENT_MULTIPLIERS
        assert EVENT_MULTIPLIERS["naval_attack"] == 1.40

    def test_asset_class_weights_mapping(self):
        assert "airport" in ASSET_CLASS_WEIGHTS
        assert "seaport" in ASSET_CLASS_WEIGHTS
        assert "port" in ASSET_CLASS_WEIGHTS
        assert ASSET_CLASS_WEIGHTS["airport"] == AIRPORT_WEIGHTS


class TestRiskScoreIntegration:
    """Test risk score computation end-to-end."""

    def test_risk_score_airport_basic(self):
        result = compute_gcc_risk_score(
            geopolitical_threat=0.8,
            proximity_score=0.7,
            network_centrality=0.6,
            logistics_pressure=0.5,
            temporal_persistence=0.4,
            uncertainty=0.3,
            asset_class="airport",
        )
        assert "raw_score" in result
        assert "normalized_score" in result
        assert "severity" in result
        assert "components" in result
        assert "weights" in result
        assert 0 <= result["normalized_score"] <= 1

    def test_risk_score_seaport_basic(self):
        result = compute_gcc_risk_score(
            geopolitical_threat=0.9,
            proximity_score=0.8,
            network_centrality=0.7,
            logistics_pressure=0.6,
            temporal_persistence=0.5,
            uncertainty=0.4,
            asset_class="seaport",
        )
        assert result["asset_class"] == "seaport"
        assert result["normalized_score"] > 0

    def test_risk_score_with_regional_multiplier(self):
        base = compute_gcc_risk_score(
            geopolitical_threat=0.7, proximity_score=0.6,
            network_centrality=0.5, logistics_pressure=0.4,
            temporal_persistence=0.3, uncertainty=0.2,
            asset_class="airport", regional_multiplier=1.0,
        )
        scaled = compute_gcc_risk_score(
            geopolitical_threat=0.7, proximity_score=0.6,
            network_centrality=0.5, logistics_pressure=0.4,
            temporal_persistence=0.3, uncertainty=0.2,
            asset_class="airport", regional_multiplier=1.20,  # AE
        )
        assert scaled["raw_score"] > base["raw_score"]

    def test_risk_score_severity_bands(self):
        # Low input -> low severity
        low = compute_gcc_risk_score(
            geopolitical_threat=0.1, proximity_score=0.1,
            network_centrality=0.1, logistics_pressure=0.1,
            temporal_persistence=0.1, uncertainty=0.1,
        )
        # High input -> high severity
        high = compute_gcc_risk_score(
            geopolitical_threat=0.95, proximity_score=0.95,
            network_centrality=0.95, logistics_pressure=0.95,
            temporal_persistence=0.95, uncertainty=0.95,
        )
        assert high["normalized_score"] > low["normalized_score"]


class TestPhysicsIntegration:
    """Test physics modules integration."""

    def test_friction_computation(self):
        result = compute_friction(
            route_id="test_route",
            threat_along_route=0.7,
            congestion=0.5,
            political_constraint=0.3,
            regulatory_restriction=0.2,
        )
        assert result is not None
        assert hasattr(result, 'total_friction')
        assert 0 <= result.total_friction <= 1

    def test_shockwave_engine_creation(self):
        engine = ShockwaveEngine()
        assert engine is not None

    def test_gcc_physics_defaults(self):
        assert FRICTION_THREAT_WEIGHT > 0
        assert PRESSURE_PERSISTENCE_FACTOR > 0
        assert SHOCKWAVE_DECAY_FACTOR == 0.58
        assert SHOCKWAVE_AMPLITUDE_DAMPING == 0.92


class TestInsuranceIntegration:
    """Test insurance intelligence modules."""

    def test_portfolio_exposure(self):
        policies = [PolicyExposure(
            policy_id="POL-001",
            tiv=0.8,
            route_dependency=0.7,
            region_risk=0.6,
            claims_elasticity=0.5,
        )]
        result = compute_portfolio_exposure(policies=policies)
        assert result is not None

    def test_claims_surge(self):
        result = compute_claims_surge_potential(
            risk_score=0.8,
            disruption_score=0.7,
            exposure=0.6,
            policy_sensitivity=0.5,
        )
        assert result is not None

    def test_underwriting_restriction(self):
        result = compute_underwriting_restriction(
            region_risk=0.85,
            logistics_stress=0.7,
            claims_surge=0.6,
            uncertainty=0.3,
        )
        assert result is not None

    def test_gcc_insurance_config(self):
        assert GCC_INSURANCE_CONFIG is not None


class TestScenarioIntegration:
    """Test scenario templates and engine."""

    def test_15_scenario_templates_exist(self):
        assert len(SCENARIO_TEMPLATES) == 15

    def test_hormuz_closure_template(self):
        assert "hormuz_closure" in SCENARIO_TEMPLATES
        template = SCENARIO_TEMPLATES["hormuz_closure"]
        assert template.name is not None

    def test_scenario_template_keys(self):
        expected_keys = [
            "hormuz_closure", "gcc_airspace_closure", "missile_escalation",
            "airport_shutdown", "port_congestion", "conflict_spillover",
            "maritime_risk_surge", "combined_disruption", "insurance_surge",
            "executive_board", "red_sea_diversion", "dual_disruption",
            "oil_corridor_risk", "false_signal", "cascading_reroute",
        ]
        for key in expected_keys:
            assert key in SCENARIO_TEMPLATES, f"Missing scenario: {key}"


class TestDecisionOutputIntegration:
    """Test decision output generator."""

    def test_decision_generator_creation(self):
        gen = DecisionOutputGenerator()
        assert gen is not None

    def test_decision_output_has_five_questions(self):
        """Every decision output contract must answer 5 questions."""
        gen = DecisionOutputGenerator()
        # Verify the generator knows about the 5 mandatory questions
        assert hasattr(gen, 'generate') or hasattr(gen, 'generate_output')


class TestMesaSimulationIntegration:
    """Test Mesa agent-based simulation."""

    def test_gcc_model_creation(self):
        model = GCCModel(
            node_locations={"A": (25.0, 55.0), "B": (26.0, 56.0)},
            adjacency_matrix={"A": ["B"], "B": ["A"]},
            node_criticality={"A": 0.8, "B": 0.6},
            node_exposure={"A": 0.7, "B": 0.5},
        )
        assert model is not None

    def test_mesa_bridge_creation(self):
        bridge = MesaBridge()
        assert bridge is not None


class TestAPIModelsIntegration:
    """Test API model serialization."""

    def test_health_response(self):
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            service_name="Impact Observatory",
            version="1.0.0",
        )
        data = health.model_dump()
        assert data["status"] == "healthy"

    def test_scenario_request(self):
        request = ScenarioRequest(
            name="Test Scenario",
            description="Test description",
            scenario_type="disruption",
            parameters={"duration": 30},
        )
        assert request.name == "Test Scenario"


class TestCrossLayerIntegration:
    """Test integration across multiple layers."""

    def test_risk_to_insurance_pipeline(self):
        """Risk score feeds into insurance exposure."""
        risk = compute_gcc_risk_score(
            geopolitical_threat=0.85,
            proximity_score=0.75,
            network_centrality=0.65,
            logistics_pressure=0.55,
            temporal_persistence=0.45,
            uncertainty=0.35,
            asset_class="seaport",
            regional_multiplier=1.15,  # SA
        )
        policies = [PolicyExposure(
            policy_id="POL-CROSS",
            tiv=0.9,
            route_dependency=0.8,
            region_risk=risk["normalized_score"],
            claims_elasticity=0.6,
        )]
        exposure = compute_portfolio_exposure(policies=policies)
        assert exposure is not None

    def test_all_layers_importable(self):
        """Verify all 10 layers can be imported in a single context."""
        # Already imported at module level — if we got here, all 10 layers work
        assert compute_gcc_risk_score is not None
        assert ThreatField is not None
        assert compute_portfolio_exposure is not None
        assert SCENARIO_TEMPLATES is not None
        assert GCCModel is not None
        assert DecisionOutputGenerator is not None
        assert ScoringService is not None
        assert SeedLoader is not None
        assert HealthResponse is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
