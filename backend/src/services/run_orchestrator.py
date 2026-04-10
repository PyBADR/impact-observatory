"""Run Orchestrator — delegates to SimulationEngine v2.1.0.

Pipeline:
  ScenarioCreate  →  SimulationEngine.run()  →  Output mapping  →  Audit

Every output maps: Event → Math Models → Physics → Sector Stress → Decision
MODEL_VERSION: 2.1.0
"""

from __future__ import annotations

import json
import logging
import time

from src.schemas.scenario import ScenarioCreate
from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
from src.services import audit_service
from src.engines.transmission_engine import build_transmission_chain
from src.engines.counterfactual_engine import calibrate_counterfactual
from src.engines.action_pathways_engine import classify_actions
from src.engines.trust_engine import compute_decision_trust
from src.engines.ownership_engine import assign_all_owners
from src.engines.workflow_engine import build_all_workflows
from src.engines.execution_engine import build_all_triggers
from src.engines.lifecycle_engine import track_all_lifecycles
from src.engines.integration_engine import get_integration_status
from src.engines.expected_actual_engine import compute_all_expected_actual
from src.engines.value_attribution_engine import compute_all_attributions
from src.engines.effectiveness_engine import compute_all_effectiveness
from src.engines.portfolio_engine import aggregate_portfolio
from src.engines.evidence_engine import build_all_evidence
from src.engines.policy_engine import evaluate_all_policies
from src.engines.attribution_defense_engine import build_all_attribution_defenses
from src.engines.override_engine import track_all_overrides
from src.engines.pilot_scope_engine import validate_pilot_scope
from src.engines.kpi_engine import compute_pilot_kpi
from src.engines.shadow_engine import run_all_shadow_comparisons
from src.engines.pilot_report_engine import generate_pilot_report
from src.engines.failure_engine import evaluate_failure_modes

logger = logging.getLogger(__name__)

# Singleton engine — instantiated once at module load
_engine = SimulationEngine()


def _log_stage(stage: str, run_id: str, ms: float, n: int) -> None:
    logger.info(json.dumps({
        "event": "stage_complete", "stage": stage,
        "run_id": run_id, "ms": round(ms, 1), "stages_done": n,
    }))


def execute_run(params: ScenarioCreate) -> dict:
    """Execute a full scenario run through SimulationEngine v2.1.0.

    Returns the complete result dict with all 16 mandatory output fields
    plus backward-compatible aliases for existing API consumers.
    """
    t_total = time.monotonic()

    # ── Stage 1: Validate scenario ID ────────────────────────���───────────
    t0 = time.monotonic()
    scenario_id = params.scenario_id
    if scenario_id not in SCENARIO_CATALOG:
        raise ValueError(
            f"Unknown scenario_id '{scenario_id}'. "
            f"Available: {sorted(SCENARIO_CATALOG.keys())}"
        )
    scenario_meta = SCENARIO_CATALOG[scenario_id]
    severity = float(params.severity)
    horizon_hours = int(params.horizon_hours or 336)
    label = params.label or scenario_meta.get("label_en") or scenario_meta.get("name", scenario_id)
    label_ar = scenario_meta.get("label_ar") or scenario_meta.get("name_ar", "")
    stage_timings: dict[str, float] = {}
    stage_timings["scenario"] = round((time.monotonic() - t0) * 1000, 1)

    # ── Stage 2–17: Full simulation pipeline ───────────────────────────��─
    t0 = time.monotonic()
    result = _engine.run(
        scenario_id=scenario_id,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    stage_timings["simulation_engine"] = round((time.monotonic() - t0) * 1000, 1)
    run_id = result["run_id"]
    _log_stage("simulation_engine", run_id, stage_timings["simulation_engine"], 17)

    # ── Stage 18: Audit ──────────────────────────────────��────────────────
    t0 = time.monotonic()
    headline = result["headline"]
    decision_plan = result.get("decision_plan", {})
    actions = decision_plan.get("actions", [])

    audit_service.record_run_start(
        run_id=run_id,
        template_id=scenario_id,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    audit_service.record_run_complete(
        run_id=run_id,
        total_loss_usd=headline.get("total_loss_usd", 0),
        critical_count=headline.get("critical_count", 0),
        actions_count=len(actions),
        duration_ms=result.get("duration_ms", 0),
    )
    for action in actions[:3]:
        if isinstance(action, dict):
            audit_service.record_decision_action(
                run_id=run_id,
                action_id=str(action.get("action_id", action.get("rank", ""))),
                action=action.get("action", action.get("action_en", "")),
                owner=action.get("owner", ""),
                priority=float(action.get("priority_score", 0)),
            )
    stage_timings["audit"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("audit", run_id, stage_timings["audit"], 18)

    # ── Stage 19: Transmission Path Engine ───────────────────────────────
    t0 = time.monotonic()
    scenario_meta_inner = SCENARIO_CATALOG.get(scenario_id, {})
    try:
        from src.simulation_engine import GCC_ADJACENCY
        adjacency_for_tx = GCC_ADJACENCY
    except ImportError:
        adjacency_for_tx = None

    transmission_chain = build_transmission_chain(
        scenario_id=scenario_id,
        propagation_chain=result.get("propagation_chain", []),
        sector_analysis=result.get("sector_analysis", []),
        sectors_affected=scenario_meta_inner.get("sectors_affected", []),
        severity=severity,
        adjacency=adjacency_for_tx,
    )
    stage_timings["transmission_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("transmission_engine", run_id, stage_timings["transmission_engine"], 19)

    # ── Stage 20: Counterfactual Calibration Engine ──────────────────────
    t0 = time.monotonic()
    counterfactual = calibrate_counterfactual(
        scenario_id=scenario_id,
        severity=severity,
        total_loss_usd=headline.get("total_loss_usd", 0.0),
        decision_plan=decision_plan,
        headline=headline,
        risk_level=result.get("risk_level", "MODERATE"),
        confidence_score=result.get("confidence_score", 0.85),
    )
    stage_timings["counterfactual_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("counterfactual_engine", run_id, stage_timings["counterfactual_engine"], 20)

    # ── Stage 21: Action Pathways Engine ─────────────────────────────────
    t0 = time.monotonic()
    action_pathways = classify_actions(
        actions=actions,
        scenario_id=scenario_id,
        severity=severity,
        risk_level=result.get("risk_level", "MODERATE"),
        liquidity_stress=result.get("banking_stress", {}),
        insurance_stress=result.get("insurance_stress", {}),
    )
    stage_timings["action_pathways_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("action_pathways_engine", run_id, stage_timings["action_pathways_engine"], 21)

    # ── Stage 22–23: Decision Trust System ──────────────────────────────────
    t0 = time.monotonic()
    decision_trust = compute_decision_trust(
        actions=actions,
        scenario_id=scenario_id,
        severity=severity,
        total_loss_usd=headline.get("total_loss_usd", 0.0),
        global_confidence=result.get("confidence_score", 0.85),
        propagation_score=result.get("propagation_score", 0.0),
        risk_level=result.get("risk_level", "MODERATE"),
        sectors_affected=scenario_meta_inner.get("sectors_affected", []),
        counterfactual_consistency=counterfactual.get("consistency_flag", "CONSISTENT"),
        transmission_total_delay=transmission_chain.get("total_delay", 24.0),
        action_pathways=action_pathways,
    )
    stage_timings["trust_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("trust_engine", run_id, stage_timings["trust_engine"], 23)

    # ── Stage 24: Decision Ownership ────────────────────────────────────────
    t0 = time.monotonic()
    scenario_domain = scenario_meta_inner.get("domain", "")
    decision_ownership = assign_all_owners(
        actions=actions,
        scenario_id=scenario_id,
        scenario_domain=scenario_domain,
        risk_level=result.get("risk_level", "MODERATE"),
        severity=severity,
    )
    stage_timings["ownership_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("ownership_engine", run_id, stage_timings["ownership_engine"], 24)

    # ── Stage 25: Decision Workflows ────────────────────────────────────────
    t0 = time.monotonic()
    decision_workflows = build_all_workflows(
        actions=actions,
        ownerships=decision_ownership,
        trust=decision_trust,
        risk_level=result.get("risk_level", "MODERATE"),
        severity=severity,
    )
    stage_timings["workflow_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("workflow_engine", run_id, stage_timings["workflow_engine"], 25)

    # ── Stage 26: Execution Triggers ────────────────────────────────────────
    t0 = time.monotonic()
    execution_triggers = build_all_triggers(
        actions=actions,
        workflows=decision_workflows,
        action_pathways=action_pathways,
    )
    stage_timings["execution_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("execution_engine", run_id, stage_timings["execution_engine"], 26)

    # ── Stage 27: Decision Lifecycle ────────────────────────────────────────
    t0 = time.monotonic()
    decision_lifecycle = track_all_lifecycles(
        actions=actions,
        workflows=decision_workflows,
        executions=execution_triggers,
    )
    stage_timings["lifecycle_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("lifecycle_engine", run_id, stage_timings["lifecycle_engine"], 27)

    # ── Stage 28: Integration Status ────────────────────────────────────────
    t0 = time.monotonic()
    integration_status = get_integration_status()
    stage_timings["integration_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("integration_engine", run_id, stage_timings["integration_engine"], 28)

    # ── Stage 29: Expected vs Actual ────────────────────────────────────────
    t0 = time.monotonic()
    expected_actuals = compute_all_expected_actual(
        actions=actions,
        counterfactual=counterfactual,
        lifecycles=decision_lifecycle,
        total_loss_usd=headline.get("total_loss_usd", 0.0),
        severity=severity,
    )
    stage_timings["expected_actual_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("expected_actual_engine", run_id, stage_timings["expected_actual_engine"], 29)

    # ── Stage 30: Value Attribution ─────────────────────────────────────────
    t0 = time.monotonic()
    value_attributions = compute_all_attributions(
        expected_actuals=expected_actuals,
        actions=actions,
        action_confidences=decision_trust.get("action_confidence", []),
        data_completeness=decision_trust.get("model_dependency", {}).get("data_completeness", 0.70),
    )
    stage_timings["value_attribution_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("value_attribution_engine", run_id, stage_timings["value_attribution_engine"], 30)

    # ── Stage 31: Decision Effectiveness ────────────────────────────────────
    t0 = time.monotonic()
    effectiveness_results = compute_all_effectiveness(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
    )
    stage_timings["effectiveness_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("effectiveness_engine", run_id, stage_timings["effectiveness_engine"], 31)

    # ── Stage 32: Portfolio Value Aggregation ───────────────────────────────
    t0 = time.monotonic()
    portfolio_value = aggregate_portfolio(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
    )
    stage_timings["portfolio_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("portfolio_engine", run_id, stage_timings["portfolio_engine"], 32)

    # ── Stage 33: Decision Evidence Packs ──────────────────────────────────
    t0 = time.monotonic()
    decision_evidence = build_all_evidence(
        actions=actions,
        transmission_chain=transmission_chain,
        counterfactual=counterfactual,
        trust=decision_trust,
        ownerships=decision_ownership,
        workflows=decision_workflows,
        execution_triggers=execution_triggers,
        lifecycles=decision_lifecycle,
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
        scenario_id=scenario_id,
        severity=severity,
        run_id=run_id,
    )
    stage_timings["evidence_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("evidence_engine", run_id, stage_timings["evidence_engine"], 33)

    # ── Stage 34: Policy Engine ────────────────────────────────────────────
    t0 = time.monotonic()
    policy_evaluations = evaluate_all_policies(
        actions=actions,
        trust=decision_trust,
        ownerships=decision_ownership,
        scenario_id=scenario_id,
        risk_level=result.get("risk_level", "MODERATE"),
        severity=severity,
    )
    stage_timings["policy_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("policy_engine", run_id, stage_timings["policy_engine"], 34)

    # ── Stage 35: Attribution Defensibility ────────────────────────────────
    t0 = time.monotonic()
    attribution_defenses = build_all_attribution_defenses(
        value_attributions=value_attributions,
        actions=actions,
        scenario_id=scenario_id,
        severity=severity,
        data_completeness=decision_trust.get("model_dependency", {}).get("data_completeness", 0.70),
    )
    stage_timings["attribution_defense_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("attribution_defense_engine", run_id, stage_timings["attribution_defense_engine"], 35)

    # ── Stage 36: Override & Exception Tracking ────────────────────────────
    t0 = time.monotonic()
    override_records = track_all_overrides(
        actions=actions,
        policies=policy_evaluations,
        workflows=decision_workflows,
    )
    stage_timings["override_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("override_engine", run_id, stage_timings["override_engine"], 36)

    # ── Stage 37: Pilot Scope Validation ──────────────────────────────────
    t0 = time.monotonic()
    pilot_scope_result = validate_pilot_scope(scenario_id)
    stage_timings["pilot_scope_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("pilot_scope_engine", run_id, stage_timings["pilot_scope_engine"], 37)

    # ── Stage 38: Shadow Mode Execution ───────────────────────────────────
    t0 = time.monotonic()
    shadow_comparisons = run_all_shadow_comparisons(system_actions=actions)
    stage_timings["shadow_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("shadow_engine", run_id, stage_timings["shadow_engine"], 38)

    # ── Stage 39: KPI Measurement ─────────────────────────────────────────
    t0 = time.monotonic()
    pilot_kpi = compute_pilot_kpi(
        actions=actions,
        shadow_comparisons=shadow_comparisons,
        portfolio_value=portfolio_value,
        policy_evaluations=policy_evaluations,
    )
    stage_timings["kpi_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("kpi_engine", run_id, stage_timings["kpi_engine"], 39)

    # ── Stage 40: Pilot Report (single-run report) ────────────────────────
    t0 = time.monotonic()
    single_run_report_data = {
        "pilot_kpi": pilot_kpi,
        "shadow_comparisons": shadow_comparisons,
        "pilot_scope": pilot_scope_result,
    }
    pilot_report = generate_pilot_report(runs=[single_run_report_data], period="single_run")
    stage_timings["pilot_report_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("pilot_report_engine", run_id, stage_timings["pilot_report_engine"], 40)

    # ── Stage 41: Failure & Fallback Evaluation ───────────────────────────
    t0 = time.monotonic()
    failure_modes = evaluate_failure_modes(
        confidence_score=result.get("confidence_score", 0.85),
        data_completeness=decision_trust.get("model_dependency", {}).get("data_completeness", 0.70),
        duration_ms=int(round((time.monotonic() - t_total) * 1000)),
        policy_evaluations=policy_evaluations,
        pilot_scope_result=pilot_scope_result,
        shadow_comparisons=shadow_comparisons,
        portfolio_value=portfolio_value,
        actions=actions,
    )
    stage_timings["failure_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("failure_engine", run_id, stage_timings["failure_engine"], 41)

    # ── Map engine output → unified API response format ───────────────────
    financial_list = result.get("financial_impact", {}).get("top_entities", [])
    banking_dict = result.get("banking_stress", {})
    insurance_dict = result.get("insurance_stress", {})
    fintech_dict = result.get("fintech_stress", {})
    explainability = result.get("explainability", {})
    system_stress = result.get("unified_risk_score", 0.0)
    propagation_chain = result.get("propagation_chain", [])

    # decisions block — shape expected by frontend
    decisions_dict = {
        "actions": actions[:3],
        "escalation_triggers": decision_plan.get("escalation_triggers", []),
        "monitoring_priorities": decision_plan.get("monitoring_priorities", []),
        "business_severity": decision_plan.get("business_severity", ""),
        "system_time_to_first_failure_hours": decision_plan.get(
            "time_to_first_failure_hours"
        ),
    }

    # explanation block — shape expected by frontend
    explanation_dict = {
        "narrative_en": explainability.get("narrative_en", ""),
        "narrative_ar": explainability.get("narrative_ar", ""),
        "causal_chain": explainability.get("causal_chain", []),
        "methodology": "deterministic_propagation",
        "model_equation": explainability.get(
            "model_equation",
            "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U",
        ),
        "confidence_score": result.get("confidence_score", 0.85),
        "sensitivity": explainability.get("sensitivity", {}),
        "uncertainty_bands": explainability.get("uncertainty_bands", {}),
        "source": "deterministic",
    }

    # impacts list — for scenario engine API compat
    impacts_list = [
        {
            "target_entity_id": step.get("entity_id", ""),
            "entity_label": step.get("entity_label", ""),
            "baseline_score": 0.0,
            "post_scenario_score": step.get("impact", 0.0),
            "delta": step.get("impact", 0.0),
            "factors": [step.get("mechanism_en", "propagation")],
            "sector": step.get("sector", ""),
        }
        for step in propagation_chain
    ]

    total_ms = int(round((time.monotonic() - t_total) * 1000))

    # ── Assemble final unified response ───────────────────────────────────
    response = {
        # Identity
        "schema_version": "v2",
        "run_id": run_id,
        "model_version": result.get("model_version", "2.1.0"),
        "status": "completed",
        "pipeline_stages_completed": 41,
        "stage_timings": stage_timings,
        "duration_ms": total_ms,

        # Scenario context
        "scenario": {
            "scenario_id": scenario_id,
            "label": label,
            "label_ar": label_ar,
            "severity": severity,
            "horizon_hours": horizon_hours,
        },
        "scenario_id": scenario_id,
        "severity": severity,
        "horizon_hours": horizon_hours,
        "time_horizon_days": max(1, horizon_hours // 24),

        # ── 16 Mandatory output fields ───────────────���─────────────────
        "event_severity": result.get("event_severity", severity),
        "peak_day": headline.get("peak_day", result.get("peak_day", 0)),
        "confidence_score": result.get("confidence_score", 0.85),

        "financial_impact": result.get("financial_impact", {}),
        "sector_analysis": result.get("sector_analysis", []),
        "propagation_score": result.get("propagation_score", 0.0),
        "unified_risk_score": system_stress,
        "risk_level": result.get("risk_level", "MODERATE"),

        "physical_system_status": result.get("physical_system_status", {}),
        "bottlenecks": result.get("bottlenecks", []),
        "congestion_score": result.get("congestion_score", 0.0),
        "recovery_score": result.get("recovery_score", 0.0),
        "recovery_trajectory": result.get("recovery_trajectory", []),

        "explainability": explainability,
        "decision_plan": decision_plan,
        "flow_analysis": result.get("flow_analysis", {}),

        # Headline KPI block
        "headline": headline,

        # Sector stress blocks
        "banking_stress": banking_dict,
        "insurance_stress": insurance_dict,
        "fintech_stress": fintech_dict,

        # ── Backward-compatible aliases ─────────────────────────────────
        # financial → top_entities list (FinancialImpact[]) expected by ExecutiveDashboard
        # IMPORTANT: must be a list — frontend calls financial.reduce(...) to build sector_exposure
        # financial_impact (full dict) is still available under its own key above
        "financial": financial_list if isinstance(financial_list, list) else [],
        "financial_impacts": financial_list,   # entity-level list (legacy)
        # banking/insurance/fintech → stress dicts
        "banking": banking_dict,          # alias for banking_stress
        "insurance": insurance_dict,       # alias for insurance_stress
        "fintech": fintech_dict,           # alias for fintech_stress
        # decisions → decision_plan (per checklist)
        "decisions": decisions_dict,
        # explanation → explainability (per checklist)
        "explanation": explanation_dict,
        "propagation": propagation_chain,
        "flow_states": [],

        # Scenario-engine compat
        # system_stress → physical_system_status (per checklist); raw score kept as system_stress_score
        "system_stress": result.get("physical_system_status", {}),
        "system_stress_score": system_stress,  # numeric alias kept for dashboards
        # impacts → sector_analysis (per checklist)
        "impacts": result.get("sector_analysis", []),
        "propagation_impacts": impacts_list,   # propagation-chain entities (legacy)
        # recommendations → immediate_actions from decision_plan (per checklist)
        "recommendations": decision_plan.get("immediate_actions", [
            a.get("action", a.get("action_en", ""))
            for a in actions[:3]
            if isinstance(a, dict)
        ]),
        "narrative": explainability.get("narrative_en", ""),
        "top_impacted_entities": [
            fi.get("entity_id", "")
            for fi in financial_list
            if fi.get("classification") in ("CRITICAL", "SEVERE", "HIGH")
        ][:5],
        "methodology": "deterministic_propagation",

        # Headline aliases for dashboard
        "headline_loss_usd": headline.get("total_loss_usd", 0),
        "severity_pct": round(severity * 100, 1),
        "decision_actions": actions[:3],

        # Executive report block
        "executive_report": {
            "headline": headline,
            "top_actions": actions[:3],
            "risk_level": result.get("risk_level", "MODERATE"),
            "narrative_en": explainability.get("narrative_en", ""),
            "narrative_ar": explainability.get("narrative_ar", ""),
        },

        # Business impact
        "business_impact": {
            "summary": {
                "business_severity": decision_plan.get("business_severity", "moderate"),
                "peak_cumulative_loss": headline.get("total_loss_usd", 0),
                "peak_loss_timestamp": f"Day {headline.get('peak_day', 0)}",
                "executive_status": "escalate" if system_stress >= 0.65 else "monitor",
            },
            "regulatory_breach_events": [],
        },

        # Timeline
        "timeline": {
            "horizon_days": max(1, horizon_hours // 24),
            "recovery_trajectory": result.get("recovery_trajectory", []),
        },

        # Regulatory state
        "regulatory_state": {
            "lcr_breached": banking_dict.get("lcr_ratio", 1.2) < 1.0,
            "car_breached": banking_dict.get("car_ratio", 0.12) < 0.105,
            "combined_ratio_breached": insurance_dict.get("combined_ratio", 0.95) > 1.10,
            "classification": result.get("risk_level", "MODERATE"),
        },

        # ── Phase 1 Execution Engines (stages 19–21) ─────────────────────
        "transmission_chain": transmission_chain,
        "counterfactual": counterfactual,
        "action_pathways": action_pathways,

        # ── Phase 2 Decision Trust System (stages 22–23) ────────────────
        "action_confidence": decision_trust["action_confidence"],
        "model_dependency": decision_trust["model_dependency"],
        "validation": decision_trust["validation"],
        "confidence_breakdown": decision_trust["confidence_breakdown"],
        "risk_profile": decision_trust["risk_profile"],

        # ── Phase 3 Decision Integration Layer (stages 24–28) ──────────
        "decision_ownership": decision_ownership,
        "decision_workflows": decision_workflows,
        "execution_triggers": execution_triggers,
        "decision_lifecycle": decision_lifecycle,
        "integration": integration_status,

        # ── Phase 4 Value Engine (stages 29–32) ────────────────────────
        "expected_actual": expected_actuals,
        "value_attribution": value_attributions,
        "effectiveness": effectiveness_results,
        "portfolio_value": portfolio_value,

        # ── Phase 5 Evidence & Governance (stages 33–36) ──────────────
        "decision_evidence": decision_evidence,
        "policy": policy_evaluations,
        "attribution_defense": attribution_defenses,
        "overrides": override_records,

        # ── Phase 6 Pilot Readiness (stages 37–41) ───────────────────
        "pilot_scope": pilot_scope_result,
        "pilot_kpi": pilot_kpi,
        "shadow_comparisons": shadow_comparisons,
        "pilot_report": pilot_report,
        "failure_modes": failure_modes,
    }

    logger.info(json.dumps({
        "event": "pipeline_complete",
        "run_id": run_id,
        "stages_completed": 41,
        "total_ms": total_ms,
        "risk_level": response["risk_level"],
        "total_loss_usd": headline.get("total_loss_usd", 0),
    }))

    return response
