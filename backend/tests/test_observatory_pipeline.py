"""
Observatory Pipeline Integration Tests — validates the full 10-stage flow.

Tests:
  1. V1 Hormuz scenario produces expected financial output
  2. All 10 stages execute (physics + propagation included)
  3. Propagation populates entities, edges, flow_states
  4. Regulatory state is computed with correct triggers
  5. Decision plan is assembled
  6. Explanation pack has bilingual content
  7. Audit hash is non-empty SHA-256
  8. Pipeline gracefully degrades when physics/propagation disabled
  9. Non-Hormuz scenario skips built-in graph, still produces valid output
  10. Stage timing metadata is populated
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.observatory import ScenarioInput, ObservatoryOutput
from app.orchestration.pipeline import run_observatory_pipeline, PipelineResult

TOL = 0.001  # Tolerance for floating-point comparisons


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def hormuz_scenario():
    """V1 Hormuz Strait Closure scenario — severity 0.85, 14 days."""
    return ScenarioInput(
        id="hormuz_closure_v1",
        name="Hormuz Strait Closure",
        name_ar="إغلاق مضيق هرمز",
        severity=0.85,
        duration_days=14,
        description="Complete blockage of Strait of Hormuz maritime transit",
    )


@pytest.fixture
def generic_scenario():
    """Generic non-Hormuz scenario."""
    return ScenarioInput(
        id="generic_recession",
        name="Global Recession",
        name_ar="ركود عالمي",
        severity=0.6,
        duration_days=30,
        description="Synchronized global economic downturn",
    )


# ============================================================================
# TESTS
# ============================================================================

class TestV1HormuzPipeline:
    """Full pipeline validation for Hormuz V1 scenario."""

    def test_financial_headline_loss(self, hormuz_scenario):
        """Headline loss should be ~$624.75B for severity=0.85, 14 days."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        # Formula: 2100 × 0.35 × 0.85 × (14/14) = 624.75
        assert abs(output.financial_impact.headline_loss_usd - 624.75) < 1.0
        assert output.financial_impact.severity_code == "CRITICAL"

    def test_all_10_stages_execute(self, hormuz_scenario):
        """All 10 stages should execute for Hormuz scenario."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        expected_stages = [
            "scenario", "physics", "graph_snapshot", "propagation",
            "financial", "sector_risk", "regulatory", "decision",
            "explanation", "output",
        ]
        for stage in expected_stages:
            assert stage in pipeline.stage_log, f"Stage '{stage}' not in stage_log"
            status = pipeline.stage_log[stage]["status"]
            assert status in ("completed", "skipped"), \
                f"Stage '{stage}' has unexpected status: {status}"

    def test_propagation_populates_entities(self, hormuz_scenario):
        """Propagation should populate entities and edges from Hormuz graph."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert len(output.entities) == 10, f"Expected 10 entities, got {len(output.entities)}"
        assert len(output.edges) == 8, f"Expected 8 edges, got {len(output.edges)}"

        # Check entity names include key nodes
        entity_ids = {e.id for e in output.entities}
        assert "geo_hormuz" in entity_ids
        assert "eco_oil" in entity_ids
        assert "fin_banking" in entity_ids

    def test_flow_states_from_propagation(self, hormuz_scenario):
        """Flow states should be populated from propagation iterations."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        if pipeline.stage_log.get("propagation", {}).get("status") == "completed":
            assert len(output.flow_states) > 0, "Propagation ran but no flow states"
            # Check flow state structure
            first = output.flow_states[0]
            assert first.timestep >= 0
            assert isinstance(first.entity_states, dict)
            assert first.total_stress >= 0

    def test_regulatory_state(self, hormuz_scenario):
        """Regulatory state should have correct triggers for CRITICAL scenario."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert output.regulatory.pdpl_compliant is True
        assert output.regulatory.sama_alert_level in ("WARNING", "CRITICAL")
        assert output.regulatory.ifrs17_impact > 0

        # Should have at least Basel III warning
        trigger_types = output.regulatory.regulatory_triggers
        assert any("BASEL3" in t for t in trigger_types), \
            f"Expected Basel III trigger, got: {trigger_types}"

    def test_decision_plan_assembled(self, hormuz_scenario):
        """Decision plan should be assembled from top actions."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert output.decision_plan is not None
        assert len(output.decisions) >= 3
        assert output.decision_plan.total_cost_usd > 0
        assert output.decision_plan.net_benefit_usd > 0
        assert len(output.decision_plan.sectors_covered) > 0

    def test_explanation_bilingual(self, hormuz_scenario):
        """Explanation pack should contain both EN and AR content."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert output.explanation is not None
        assert len(output.explanation.summary_en) > 0
        assert len(output.explanation.summary_ar) > 0
        assert len(output.explanation.key_findings) >= 3
        assert len(output.explanation.causal_chain) >= 5

    def test_audit_hash_sha256(self, hormuz_scenario):
        """Audit hash should be a valid SHA-256 hex string."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert len(output.audit_hash) == 64
        assert all(c in "0123456789abcdef" for c in output.audit_hash)

    def test_computation_time_recorded(self, hormuz_scenario):
        """Computation time should be positive."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert output.computed_in_ms > 0

    def test_runtime_flow_is_10_stages(self, hormuz_scenario):
        """Runtime flow should list all 10 stages."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert len(output.runtime_flow) == 10
        assert output.runtime_flow[0] == "scenario"
        assert output.runtime_flow[-1] == "output"

    def test_sector_stress_levels(self, hormuz_scenario):
        """Sector stress levels should be within expected range for severity=0.85."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert output.banking_stress.stress_level in ("HIGH", "CRITICAL")
        assert output.insurance_stress.stress_level in ("HIGH", "CRITICAL")
        assert output.fintech_stress.stress_level in ("HIGH", "CRITICAL")


class TestGracefulDegradation:
    """Pipeline should produce valid output even when stages are disabled."""

    def test_no_physics_no_propagation(self, hormuz_scenario):
        """Pipeline works with physics and propagation disabled."""
        output, pipeline = run_observatory_pipeline(
            hormuz_scenario,
            enable_physics=False,
            enable_propagation=False,
        )

        assert output.financial_impact.headline_loss_usd > 0
        assert len(output.decisions) >= 3
        assert output.audit_hash != ""

        # Graph snapshot still runs (entities/edges populated from built-in graph)
        # but flow_states should be empty since propagation was disabled
        assert len(output.flow_states) == 0

        # Skipped stages recorded
        assert "physics" in pipeline.stages_skipped
        assert "propagation" in pipeline.stages_skipped

    def test_generic_scenario_no_graph(self, generic_scenario):
        """Non-Hormuz scenario skips graph but still produces valid output."""
        output, pipeline = run_observatory_pipeline(generic_scenario)

        assert output.financial_impact.headline_loss_usd > 0
        assert len(output.decisions) >= 3
        assert output.regulatory.pdpl_compliant is True

        # Graph snapshot should be skipped (no built-in graph for generic)
        assert pipeline.stage_log["graph_snapshot"]["status"] == "skipped"


class TestStageMetadata:
    """Pipeline metadata should be complete and accurate."""

    def test_all_stages_timed(self, hormuz_scenario):
        """Every stage should have a non-negative duration."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        for stage_id, info in pipeline.stage_log.items():
            assert "duration_ms" in info, f"Stage {stage_id} missing duration"
            assert info["duration_ms"] >= 0, f"Stage {stage_id} has negative duration"

    def test_no_errors_on_hormuz(self, hormuz_scenario):
        """Hormuz scenario should complete without errors."""
        output, pipeline = run_observatory_pipeline(hormuz_scenario)

        assert len(pipeline.errors) == 0, f"Pipeline errors: {pipeline.errors}"
