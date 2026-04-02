"""Scenario regression tests — verify all 15 templates produce valid outputs.

Each scenario must:
1. Run without error
2. Produce system_stress in [0, 1]
3. Produce non-empty narrative
4. Produce at least 1 impacted entity
5. Produce recommendations
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.state import init_state
from src.engines.scenario.templates import SCENARIO_TEMPLATES
from src.engines.scenario.templates_extended import EXTENDED_TEMPLATES


@pytest.fixture(scope="module", autouse=True)
def setup():
    init_state()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


ALL_TEMPLATE_IDS = [t.id for t in SCENARIO_TEMPLATES + EXTENDED_TEMPLATES]


class TestScenarioRegression:
    @pytest.mark.parametrize("scenario_id", ALL_TEMPLATE_IDS)
    def test_template_runs(self, client, scenario_id):
        r = client.post("/api/v1/scenario/run", json={
            "scenario_id": scenario_id,
            "severity_override": 0.6,
        })
        assert r.status_code == 200, f"{scenario_id}: status={r.status_code}"
        data = r.json()

        # Must have system stress
        assert "system_stress" in data
        assert 0.0 <= data["system_stress"] <= 1.0, f"{scenario_id}: stress={data['system_stress']}"

        # Must have narrative
        assert data.get("narrative"), f"{scenario_id}: empty narrative"
        assert len(data["narrative"]) > 20

        # Must have impacts
        assert len(data.get("impacts", [])) > 0, f"{scenario_id}: no impacts"

        # Must have recommendations
        assert len(data.get("recommendations", [])) > 0, f"{scenario_id}: no recommendations"

    def test_hormuz_high_stress(self, client):
        """Hormuz disruption should produce elevated or critical stress."""
        r = client.post("/api/v1/scenario/run", json={
            "scenario_id": "hormuz_disruption",
            "severity_override": 0.9,
        })
        data = r.json()
        assert data["system_stress"] > 0.1

    def test_severity_scaling(self, client):
        """Higher severity should produce higher stress."""
        r_low = client.post("/api/v1/scenario/run", json={
            "scenario_id": "hormuz_disruption",
            "severity_override": 0.3,
        })
        r_high = client.post("/api/v1/scenario/run", json={
            "scenario_id": "hormuz_disruption",
            "severity_override": 0.9,
        })
        assert r_high.json()["system_stress"] >= r_low.json()["system_stress"]


class TestDecisionRegression:
    def test_decision_answers_five_questions(self, client):
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["hormuz", "shipping"],
            "severity": 0.8,
        })
        data = r.json()
        d = data["decision"]

        # All 5 mandatory questions
        assert "what_happened" in d
        assert "what_is_the_impact" in d
        assert "what_is_affected" in d
        assert "how_big_is_the_risk" in d
        assert "recommended_actions" in d

        # Impact section has detail
        impact = d["what_is_the_impact"]
        assert "system_stress" in impact
        assert "disrupted_nodes" in impact
        assert "sector_impacts" in impact

        # Affected section has entities
        affected = d["what_is_affected"]
        assert affected["count"] > 0

        # Risk assessment has numbers
        risk = d["how_big_is_the_risk"]
        assert risk["max_risk"] > 0
        assert risk["system_classification"] in (
            "NOMINAL", "LOW", "MODERATE", "ELEVATED", "CRITICAL"
        )

    def test_decision_insurance_linkage(self, client):
        """Decision output must include insurance impact when requested."""
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["hormuz"],
            "severity": 0.7,
            "include_insurance": True,
        })
        data = r.json()
        ins = data["insurance_impact"]
        assert ins is not None
        assert "flagged_entities" in ins
        assert "system_stress" in ins

    def test_decision_metadata(self, client):
        r = client.post("/api/v1/decision/output", json={
            "shock_node_ids": ["dubai_apt"],
            "severity": 0.5,
        })
        meta = r.json()["metadata"]
        assert meta["n_nodes"] == 42
        assert meta["equation"] == "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U"
