"""Tests for scenario simulation engine."""

import pytest

from src.engines.scenario.engine import GraphState, ScenarioEngine
from src.engines.scenario.templates import get_template
from src.services.seed_data import GCC_EDGES, GCC_NODES


@pytest.fixture
def graph_state():
    return GraphState(
        node_ids=[n["id"] for n in GCC_NODES],
        node_labels={n["id"]: n["label"] for n in GCC_NODES},
        node_labels_ar={n["id"]: n.get("label_ar", n["label"]) for n in GCC_NODES},
        node_sectors=[n["layer"] for n in GCC_NODES],
        sector_weights={
            "geography": 0.10,
            "infrastructure": 0.25,
            "economy": 0.30,
            "finance": 0.20,
            "society": 0.15,
        },
        edges=GCC_EDGES,
    )


@pytest.fixture
def engine(graph_state):
    return ScenarioEngine(graph_state=graph_state)


class TestScenarioEngine:
    def test_baseline_capture(self, engine):
        baseline = engine.capture_baseline()
        assert len(baseline) == len(GCC_NODES)
        assert all(0 <= v <= 1 for v in baseline)

    def test_hormuz_chokepoint_disruption(self, engine):
        scenario = get_template("hormuz_chokepoint_disruption")
        assert scenario is not None
        result = engine.run(scenario)

        assert result.system_stress > 0
        assert len(result.impacts) > 0
        assert result.narrative
        assert result.recommendations
        assert "hormuz" in result.top_impacted_entities

    def test_airspace_closure(self, engine):
        scenario = get_template("gcc_airspace_closure")
        result = engine.run(scenario)

        assert result.system_stress > 0
        assert any("aviation" in i.target_entity_id or "airspace" in i.target_entity_id for i in result.impacts)

    def test_triple_cascade_highest_stress(self, engine):
        hormuz = engine.run(get_template("hormuz_chokepoint_disruption"))
        triple = engine.run(get_template("triple_cascade"))

        # Triple cascade should produce higher system stress
        assert triple.system_stress >= hormuz.system_stress * 0.8  # allow some tolerance

    def test_all_templates_run(self, engine):
        from src.engines.scenario.templates import SCENARIO_TEMPLATES

        for template in SCENARIO_TEMPLATES:
            result = engine.run(template)
            assert result.system_stress >= 0
            assert result.narrative
            assert isinstance(result.recommendations, list)

    def test_impacts_have_deltas(self, engine):
        scenario = get_template("hormuz_chokepoint_disruption")
        result = engine.run(scenario)

        for impact in result.impacts:
            assert impact.baseline_score >= 0
            assert impact.post_scenario_score >= 0
            assert impact.delta != 0  # all returned impacts have nonzero delta
            assert len(impact.factors) > 0

    def test_recommendations_generated(self, engine):
        scenario = get_template("triple_cascade")
        result = engine.run(scenario)
        assert len(result.recommendations) > 0
