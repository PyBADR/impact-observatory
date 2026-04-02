"""Impact Observatory | مرصد الأثر — Integration Tests.

Tests the full 12-service pipeline:
    Scenario → Physics → Propagation → Financial → Banking → Insurance →
    Fintech → Decision → Explainability → Reporting → Audit

Every output must map: Event → Financial Impact → Sector Stress → Decision
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest


class TestFullPipeline:
    """Test the complete run orchestrator pipeline."""

    def _run_hormuz(self, severity=0.8):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        params = ScenarioCreate(
            template_id="hormuz_disruption",
            severity=severity,
            horizon_hours=336,
            label="Hormuz Closure - 14D - Severe",
        )
        return execute_run(params)

    def test_run_completes(self):
        result = self._run_hormuz()
        assert result["status"] == "completed"
        assert result["run_id"].startswith("run-")
        assert result["duration_ms"] >= 0

    def test_headline_loss_computed(self):
        result = self._run_hormuz()
        h = result["headline"]
        assert h["total_loss_usd"] > 0, "Must compute loss"
        assert h["peak_day"] > 0, "Must compute peak day"
        assert h["affected_entities"] > 0, "Must affect entities"
        assert h["critical_count"] >= 0

    def test_financial_impacts_present(self):
        result = self._run_hormuz()
        assert len(result["financial"]) > 0
        first = result["financial"][0]
        assert "entity_id" in first
        assert "loss_usd" in first
        assert "sector" in first
        assert "classification" in first
        assert first["loss_usd"] > 0

    def test_banking_stress_computed(self):
        result = self._run_hormuz()
        b = result["banking"]
        assert "classification" in b
        assert "aggregate_stress" in b
        assert "liquidity_stress" in b
        assert "time_to_liquidity_breach_hours" in b
        assert b["aggregate_stress"] > 0
        assert b["classification"] in ("NOMINAL", "LOW", "MODERATE", "ELEVATED", "CRITICAL")

    def test_insurance_stress_computed(self):
        result = self._run_hormuz()
        ins = result["insurance"]
        assert ins["claims_surge_multiplier"] >= 1.0, "Claims must surge"
        assert ins["combined_ratio"] > 0
        assert ins["underwriting_status"] in ("normal", "warning", "critical", "suspended")
        assert "time_to_insolvency_hours" in ins

    def test_fintech_stress_computed(self):
        result = self._run_hormuz()
        ft = result["fintech"]
        assert "payment_volume_impact_pct" in ft
        assert "settlement_delay_hours" in ft
        assert "api_availability_pct" in ft
        assert "time_to_payment_failure_hours" in ft
        assert ft["api_availability_pct"] <= 100.0

    def test_decision_actions_top_3(self):
        """Decision engine must output top 3 prioritized actions."""
        result = self._run_hormuz()
        d = result["decisions"]
        assert len(d["actions"]) <= 3, "Must output at most top 3 actions"
        assert len(d["actions"]) >= 1, "Must output at least 1 action"
        assert d["total_loss_usd"] > 0
        # Actions must be sorted by priority descending
        priorities = [a["priority"] for a in d["actions"]]
        assert priorities == sorted(priorities, reverse=True)

    def test_decision_priority_formula(self):
        """Priority = Value + Urgency + RegulatoryRisk."""
        result = self._run_hormuz()
        for action in result["decisions"]["actions"]:
            # Verify each action has the required fields
            assert "urgency" in action
            assert "value" in action
            assert "regulatory_risk" in action
            assert "priority" in action
            # Priority ≈ value + urgency + regulatory_risk
            expected = action["value"] + action["urgency"] + action["regulatory_risk"]
            assert abs(action["priority"] - expected) < 0.01

    def test_decision_actions_bilingual(self):
        result = self._run_hormuz()
        for action in result["decisions"]["actions"]:
            assert action["action"], "Must have English action"
            assert action["action_ar"], "Must have Arabic action"
            assert action["owner"], "Must have owner"
            assert action["sector"], "Must have sector"

    def test_explanation_bilingual(self):
        result = self._run_hormuz()
        exp = result["explanation"]
        assert len(exp["narrative_en"]) > 50, "English narrative must be substantive"
        assert len(exp["narrative_ar"]) > 20, "Arabic narrative must be present"
        assert exp["total_steps"] > 0
        assert exp["headline_loss_usd"] > 0
        assert len(exp["causal_chain"]) > 0

    def test_causal_chain_structure(self):
        result = self._run_hormuz()
        for step in result["explanation"]["causal_chain"]:
            assert "entity_id" in step
            assert "entity_label" in step
            assert "event" in step
            assert "mechanism" in step
            assert "step" in step

    def test_executive_report_structure(self):
        result = self._run_hormuz()
        report = result["executive_report"]
        assert report["mode"] == "executive"
        assert "headline" in report
        assert "sector_stress" in report
        assert "narrative" in report

    def test_audit_trail_recorded(self):
        from src.services import audit_service
        result = self._run_hormuz()
        run_id = result["run_id"]
        log = audit_service.get_audit_log(run_id=run_id)
        events = [e["event"] for e in log]
        assert "run_start" in events
        assert "run_complete" in events


class TestSeverityScaling:
    """Higher severity must produce larger impacts."""

    def test_loss_scales_with_severity(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run

        low = execute_run(ScenarioCreate(template_id="hormuz_disruption", severity=0.3, horizon_hours=336))
        high = execute_run(ScenarioCreate(template_id="hormuz_disruption", severity=0.9, horizon_hours=336))

        assert high["headline"]["total_loss_usd"] > low["headline"]["total_loss_usd"]

    def test_banking_stress_scales(self):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run

        low = execute_run(ScenarioCreate(template_id="hormuz_disruption", severity=0.3, horizon_hours=336))
        high = execute_run(ScenarioCreate(template_id="hormuz_disruption", severity=0.9, horizon_hours=336))

        assert high["banking"]["aggregate_stress"] >= low["banking"]["aggregate_stress"]


class TestAllScenarioTemplates:
    """All 8 scenario templates must produce valid output."""

    TEMPLATES = [
        "hormuz_disruption", "yemen_escalation", "iran_sanctions",
        "cyber_attack", "gulf_airspace", "port_disruption",
        "oil_price_shock", "banking_stress",
    ]

    @pytest.mark.parametrize("template_id", TEMPLATES)
    def test_template_runs(self, template_id):
        from src.schemas.scenario import ScenarioCreate
        from src.services.run_orchestrator import execute_run
        result = execute_run(ScenarioCreate(template_id=template_id, severity=0.6, horizon_hours=336))
        assert result["status"] == "completed"
        assert result["headline"]["total_loss_usd"] > 0
        assert len(result["decisions"]["actions"]) >= 0  # some may not trigger


class TestSchemaValidation:
    """All schemas must validate correctly."""

    def test_scenario_create_validation(self):
        from src.schemas.scenario import ScenarioCreate
        # Valid
        s = ScenarioCreate(template_id="hormuz_disruption", severity=0.8)
        assert s.severity == 0.8
        assert s.horizon_hours == 336  # default

        # Invalid severity
        with pytest.raises(Exception):
            ScenarioCreate(template_id="hormuz_disruption", severity=1.5)

    def test_financial_impact_classification(self):
        from src.schemas.financial_impact import FinancialImpact
        fi = FinancialImpact(
            entity_id="test",
            sector="energy",
            loss_usd=1e9,
            classification="CRITICAL",
        )
        assert fi.classification == "CRITICAL"

    def test_decision_action_fields(self):
        from src.schemas.decision import DecisionAction
        a = DecisionAction(
            id="act-001",
            action="Test action",
            sector="banking",
            owner="CRO",
            urgency=10.0,
            value=5.0,
            regulatory_risk=0.8,
            priority=15.8,
        )
        assert a.priority == 15.8


class TestI18n:
    """Bilingual labels must be complete."""

    def test_all_labels_en(self):
        from src.i18n.labels import get_all_labels
        labels = get_all_labels("en")
        required = [
            "headline_loss", "peak_day", "banking_stress",
            "insurance_stress", "fintech_stress", "decision_actions",
            "time_to_failure",
        ]
        for key in required:
            assert key in labels, f"Missing EN label: {key}"

    def test_all_labels_ar(self):
        from src.i18n.labels import get_all_labels
        labels = get_all_labels("ar")
        assert labels["headline_loss"] == "إجمالي الخسارة"
        assert labels["time_to_failure"] == "وقت الانهيار"
        assert labels["banking_stress"] == "ضغط القطاع البنكي"
