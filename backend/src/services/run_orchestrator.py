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
from src.policies.executive_policy import classify_executive_status_v2
from src.policies.scenario_policy import resolve_scenario_type
from src.engines.sanity_guard import sanitize_run_result
from src.events.event_store import event_store
from src.validation.contracts import validate_metrics
from src.engines.map_payload_engine import build_map_payload, build_graph_payload, build_propagation_steps
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
from src.engines.propagation_headline_engine import build_propagation_headline
from src.engines.impact_map_engine import build_impact_map
from src.engines.decision_overlay_engine import build_decision_overlays
from src.engines.explanation_engine import generate_explanations
from src.engines.decision_transparency_engine import compute_all_transparencies
from src.engines.range_engine import generate_ranges
from src.engines.sensitivity_engine import generate_sensitivities
from src.engines.outcome_engine import (
    build_outcome_records,
    build_trust_memories_for_run,
    build_confidence_adjustments,
)
from src.engines.impact_map_validator import validate_impact_map
from src.regime.regime_engine import classify_regime_from_result, build_regime_inputs
from src.regime.regime_graph_adapter import apply_regime_to_graph
from src.regime.decision_trigger_engine import build_decision_triggers_from_regime_state
from src.decision_intelligence.pipeline import (
    run_decision_intelligence_pipeline,
    DecisionIntelligenceResult,
)
from src.decision_quality.pipeline import (
    run_decision_quality_pipeline,
    DecisionQualityResult,
)
from src.decision_calibration.pipeline import (
    run_calibration_pipeline,
    CalibrationLayerResult,
)
from src.decision_trust.pipeline import (
    run_trust_pipeline,
    TrustLayerResult,
)
from src.actions.action_registry import get_actions_for_scenario_id
from src.services.institutional_audit import (
    persist_calibration_audit,
    persist_trust_audit,
)
from src.metrics_provenance.pipeline import run_provenance_pipeline

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

    # ── Stage 17a: Early Validation Firewall ──────────────────────────────
    # Catches invalid values BEFORE they propagate through 24+ downstream stages
    t0 = time.monotonic()
    early_validation_flags = validate_metrics(result, scenario_window_hours=float(horizon_hours))
    if early_validation_flags:
        logger.warning(
            "Early validation flags for run %s: %d issues detected (pre-downstream)",
            run_id, len(early_validation_flags),
        )
    stage_timings["early_validation"] = round((time.monotonic() - t0) * 1000, 1)

    # ── Stage 17b: Regime Classification ──────────────────────────────────
    t0 = time.monotonic()
    regime_state = classify_regime_from_result(result)
    regime_inputs = build_regime_inputs(result)
    stage_timings["regime_classification"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("regime_classification", run_id, stage_timings["regime_classification"], 17)

    # ── Stage 17c: Regime Graph Modifiers ──────────────────────────────────
    t0 = time.monotonic()
    try:
        from src.simulation_engine import GCC_NODES as _gcc_nodes_regime
        from src.simulation_engine import GCC_ADJACENCY as _gcc_adj_regime
    except ImportError:
        _gcc_nodes_regime = []
        _gcc_adj_regime = None
    regime_graph_modifiers = apply_regime_to_graph(
        regime_id=regime_state.regime_id,
        gcc_nodes=_gcc_nodes_regime,
        gcc_adjacency=_gcc_adj_regime,
    )
    stage_timings["regime_graph_adapter"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("regime_graph_adapter", run_id, stage_timings["regime_graph_adapter"], 17)

    # ── Stage 17d: Decision Triggers (regime → decisions) ──────────────────
    t0 = time.monotonic()
    decision_triggers = build_decision_triggers_from_regime_state(regime_state, regime_inputs)
    stage_timings["decision_triggers"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_triggers", run_id, stage_timings["decision_triggers"], 17)

    # ── Event: SCENARIO_STARTED ─────────────────────────────────────────────
    event_store.emit(
        "SCENARIO_STARTED", run_id, scenario_id,
        {"severity": severity, "horizon_hours": horizon_hours, "label": label},
    )

    # ── Stage 18: Audit ──────────────────────────────────��────────────────
    t0 = time.monotonic()
    headline = result["headline"]
    # Enrich headline with fields the frontend's UnifiedRunResult expects
    headline.setdefault("total_nodes_impacted", headline.get("affected_entities", 0))
    headline.setdefault("propagation_depth", len(result.get("propagation_chain", result.get("propagation", []))))

    # ── Propagation headline — executive-facing causal narrative ────────────
    try:
        from src.simulation_engine import GCC_NODES as _gcc_nodes_hl
        _prop_hl = build_propagation_headline(
            propagation_chain=result.get("propagation_chain", result.get("propagation", [])),
            gcc_nodes=_gcc_nodes_hl,
            scenario_id=scenario_id,
        )
        headline["propagation_headline_en"] = _prop_hl["propagation_headline_en"]
        headline["propagation_headline_ar"] = _prop_hl["propagation_headline_ar"]
    except Exception as hl_err:
        logger.warning("propagation_headline build failed: %s", hl_err)
        headline.setdefault("propagation_headline_en", "")
        headline.setdefault("propagation_headline_ar", "")

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

    # ── Events: ACTION_RECOMMENDED for top actions ──────────────────────────
    for action in actions[:5]:
        if isinstance(action, dict):
            event_store.emit(
                "ACTION_RECOMMENDED", run_id, scenario_id,
                {
                    "action_id": action.get("action_id", ""),
                    "action": action.get("action", ""),
                    "loss_avoided_usd": action.get("loss_avoided_usd", 0),
                    "cost_usd": action.get("cost_usd", 0),
                    "priority_score": action.get("priority_score", 0),
                    "urgency": action.get("urgency", 0),
                },
            )

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
        scenario_id=scenario_id,
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
        scenario_id=scenario_id,
    )
    stage_timings["value_attribution_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("value_attribution_engine", run_id, stage_timings["value_attribution_engine"], 30)

    # ── Stage 31: Decision Effectiveness ────────────────────────────────────
    t0 = time.monotonic()
    effectiveness_results = compute_all_effectiveness(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        scenario_id=scenario_id,
    )
    stage_timings["effectiveness_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("effectiveness_engine", run_id, stage_timings["effectiveness_engine"], 31)

    # ── Stage 32: Portfolio Value Aggregation ───────────────────────────────
    t0 = time.monotonic()
    portfolio_value = aggregate_portfolio(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
        scenario_id=scenario_id,
        run_id=run_id,
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

    # ── Stage 41a: Metric Explanation Engine (Decision Trust Layer) ────────
    t0 = time.monotonic()
    metric_explanations = generate_explanations(result)
    stage_timings["explanation_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("explanation_engine", run_id, stage_timings["explanation_engine"], "41a")

    # ── Stage 41b: Decision Transparency Engine (Decision Trust Layer) ─────
    t0 = time.monotonic()
    decision_transparency = compute_all_transparencies(result)
    stage_timings["decision_transparency_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_transparency_engine", run_id, stage_timings["decision_transparency_engine"], "41b")

    # ── Stage 41c: Range Engine (Decision Reliability Layer) ──────────────
    t0 = time.monotonic()
    range_estimates = generate_ranges(result)
    stage_timings["range_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("range_engine", run_id, stage_timings["range_engine"], "41c")

    # ── Stage 41d: Sensitivity Engine (Decision Reliability Layer) ────────
    t0 = time.monotonic()
    sensitivity_analyses = generate_sensitivities(result)
    stage_timings["sensitivity_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("sensitivity_engine", run_id, stage_timings["sensitivity_engine"], "41d")

    # ── Stage 41e: Outcome Tracking (Decision Reliability Layer) ──────────
    t0 = time.monotonic()
    outcome_records = build_outcome_records(run_id, result)
    stage_timings["outcome_engine"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("outcome_engine", run_id, stage_timings["outcome_engine"], "41e")

    # ── Stage 41f: Trust Memory (Decision Reliability Layer) ──────────────
    t0 = time.monotonic()
    trust_memories = build_trust_memories_for_run(result)
    stage_timings["trust_memory"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("trust_memory", run_id, stage_timings["trust_memory"], "41f")

    # ── Stage 41g: Confidence Adjustment (Decision Reliability Layer) ─────
    t0 = time.monotonic()
    confidence_adjustments = build_confidence_adjustments(metric_explanations, trust_memories)
    stage_timings["confidence_adjustment"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("confidence_adjustment", run_id, stage_timings["confidence_adjustment"], "41g")

    # ── Stage 42: Impact Intelligence Layer ────────────────────────────────
    t0 = time.monotonic()
    try:
        from src.simulation_engine import GCC_NODES as _gcc_nodes_42, GCC_ADJACENCY as _gcc_adj_42
        impact_map = build_impact_map(
            result=result,
            gcc_nodes=_gcc_nodes_42,
            gcc_adjacency=_gcc_adj_42,
            regime_modifiers=regime_graph_modifiers,
            transmission_chain=transmission_chain,
            scenario_id=scenario_id,
            run_id=run_id,
        )
        # Inject decision overlays from actions
        impact_map_overlays = build_decision_overlays(actions, _gcc_adj_42)
        impact_map.decision_overlays = impact_map_overlays
        # Validate — attaches flags, sanitizes in place
        impact_map = validate_impact_map(impact_map)
    except Exception as im_err:
        logger.warning("Impact map build failed: %s", im_err, exc_info=True)
        from src.schemas.impact_map import ImpactMapResponse as _IMR
        impact_map = _IMR(run_id=run_id, scenario_id=scenario_id)
    stage_timings["impact_intelligence_layer"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("impact_intelligence_layer", run_id, stage_timings["impact_intelligence_layer"], 42)

    # ── Stage 50: Decision Intelligence Pipeline ──────────────────────────
    t0 = time.monotonic()
    try:
        # Build action_costs and action_registry_lookup from the action registry
        _action_templates = get_actions_for_scenario_id(scenario_id)
        _action_costs: dict[str, float] = {
            a["action_id"]: float(a.get("cost_usd", 0))
            for a in _action_templates
        }
        _action_registry_lookup: dict[str, dict] = {
            a["action_id"]: dict(a)
            for a in _action_templates
        }
        di_result = run_decision_intelligence_pipeline(
            impact_map=impact_map,
            action_costs=_action_costs,
            action_registry_lookup=_action_registry_lookup,
        )
    except Exception as di_err:
        logger.warning("Decision Intelligence pipeline failed: %s", di_err, exc_info=True)
        di_result = DecisionIntelligenceResult()
    stage_timings["decision_intelligence"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_intelligence", run_id, stage_timings["decision_intelligence"], 50)

    # ── Stage 60: Decision Quality Layer ──────────────────────────────────
    t0 = time.monotonic()
    try:
        dq_result = run_decision_quality_pipeline(
            di_result=di_result,
            action_registry_lookup=_action_registry_lookup,
        )
    except Exception as dq_err:
        logger.warning("Decision Quality pipeline failed: %s", dq_err, exc_info=True)
        dq_result = DecisionQualityResult()
    stage_timings["decision_quality"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_quality", run_id, stage_timings["decision_quality"], 60)

    # ── Stage 70: Decision Quality Calibration Layer ─────────────────────
    t0 = time.monotonic()
    try:
        cal_result = run_calibration_pipeline(
            dq_result=dq_result,
            impact_map=impact_map,
            scenario_id=scenario_id,
            action_registry_lookup=_action_registry_lookup,
        )
    except Exception as cal_err:
        logger.warning("Calibration pipeline failed: %s", cal_err, exc_info=True)
        cal_result = CalibrationLayerResult()
    stage_timings["decision_calibration"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_calibration", run_id, stage_timings["decision_calibration"], 70)

    # ── Stage 70a: Persist calibration audit trail ───────────────────────
    try:
        persist_calibration_audit(run_id, cal_result.to_dict())
    except Exception as audit_cal_err:
        logger.warning("Calibration audit persistence failed: %s", audit_cal_err)

    # ── Stage 80: Decision Trust Layer ────────────────────────────────────
    t0 = time.monotonic()
    try:
        from src.simulation_engine import SCENARIO_CATALOG as _SC
        _catalog_entry = _SC.get(scenario_id, None)
        trust_result = run_trust_pipeline(
            dq_result=dq_result,
            cal_result=cal_result,
            impact_map=impact_map,
            scenario_id=scenario_id,
            action_registry_lookup=_action_registry_lookup,
            scenario_catalog_entry=_catalog_entry,
        )
    except Exception as trust_err:
        logger.warning("Trust pipeline failed: %s", trust_err, exc_info=True)
        trust_result = TrustLayerResult()
    stage_timings["decision_trust"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("decision_trust", run_id, stage_timings["decision_trust"], 80)

    # ── Stage 80a: Persist trust audit trail ─────────────────────────────
    try:
        persist_trust_audit(run_id, trust_result.to_dict())
    except Exception as audit_trust_err:
        logger.warning("Trust audit persistence failed: %s", audit_trust_err)

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

    # ── Build map / graph payloads for Impact Map frontend ────────────────
    from src.simulation_engine import GCC_NODES
    try:
        from src.simulation_engine import GCC_ADJACENCY as _adj
    except ImportError:
        _adj = None

    _map_result_proxy = {
        "financial": financial_list,
        "bottlenecks": result.get("bottlenecks", []),
        "banking_stress": banking_dict,
        "insurance_stress": insurance_dict,
        "fintech_stress": fintech_dict,
        "propagation_chain": propagation_chain,
        "event_severity": result.get("event_severity", severity),
        "severity": severity,
    }
    try:
        map_payload = build_map_payload(_map_result_proxy, GCC_NODES, scenario_id, regime_graph_modifiers)
    except Exception as map_err:
        logger.warning("map_payload build failed: %s", map_err)
        map_payload = {"impacted_entities": [], "total_estimated_loss_usd": 0}

    try:
        graph_payload = build_graph_payload(_map_result_proxy, GCC_NODES, _adj)
    except Exception as graph_err:
        logger.warning("graph_payload build failed: %s", graph_err)
        graph_payload = {"nodes": [], "edges": [], "categories": []}

    try:
        propagation_steps = build_propagation_steps(_map_result_proxy, GCC_NODES)
    except Exception as prop_err:
        logger.warning("propagation_steps build failed: %s", prop_err)
        propagation_steps = []

    # ── Assemble final unified response ───────────────────────────────────
    response = {
        # Identity
        "schema_version": "v2",
        "run_id": run_id,
        "model_version": result.get("model_version", "2.1.0"),
        "status": "completed",
        "pipeline_stages_completed": 80,
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
                "executive_status": classify_executive_status_v2(
                    severity=result.get("event_severity", 0.0),
                    time_to_first_breach_hours=decision_plan.get("time_to_first_failure_hours"),
                    loss_ratio=headline.get("total_loss_usd", 0.0) / max(scenario_meta.get("base_loss_usd", 1.0), 1.0),
                    propagation_speed=min(1.0, system_stress * 1.2),
                    scenario_type=resolve_scenario_type(scenario_id),
                ),
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

        # ── Decision Trust Layer (Stages 41a–41b) ────────────────────
        "metric_explanations": metric_explanations,
        "decision_transparency": decision_transparency,

        # ── Decision Reliability Layer (Stages 41c–41g) ──────────────
        "reliability": {
            "ranges": range_estimates,
            "sensitivities": sensitivity_analyses,
            "outcome_records": outcome_records,
            "trust_memories": trust_memories,
            "confidence_adjustments": confidence_adjustments,
        },

        # ── Impact Map payloads (graph + geo) ─────────────────────────
        "map_payload": map_payload,
        "graph_payload": graph_payload,
        "propagation_steps": propagation_steps,

        # ── Impact Intelligence Layer (unified causal decision surface) ──
        "impact_map": impact_map.model_dump(),

        # ── Decision Intelligence (Stage 50) ─────────────────────────
        "decision_intelligence": di_result.to_dict(),

        # ── Decision Quality (Stage 60) ──────────────────────────────
        "decision_quality": dq_result.to_dict(),

        # ── Decision Calibration (Stage 70) ──────────────────────────
        "decision_calibration": cal_result.to_dict(),

        # ── Decision Trust (Stage 80) ────────────────────────────────
        "decision_trust": trust_result.to_dict(),

        # ── Regime Layer (system-state intelligence) ─────────────────
        "regime_state": regime_state.to_dict(),
        "regime_graph_modifiers": regime_graph_modifiers.to_dict(),
        "decision_triggers": [dt.to_dict() for dt in decision_triggers],

        # ── UnifiedRunResult compatibility fields for ImpactOverlay ──
        "sector_rollups": {
            "banking": {
                "aggregate_stress": banking_dict.get("aggregate_stress", 0.0),
                "total_loss": sum(
                    fi.get("loss_usd", 0)
                    for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "banking"
                ),
                "node_count": sum(
                    1 for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "banking"
                ),
                "classification": banking_dict.get("classification", "MODERATE"),
            },
            "insurance": {
                "aggregate_stress": insurance_dict.get("aggregate_stress", insurance_dict.get("severity_index", 0.0)),
                "total_loss": sum(
                    fi.get("loss_usd", 0)
                    for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "insurance"
                ),
                "node_count": sum(
                    1 for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "insurance"
                ),
                "classification": insurance_dict.get("classification", "MODERATE"),
            },
            "fintech": {
                "aggregate_stress": fintech_dict.get("aggregate_stress", 0.0),
                "total_loss": sum(
                    fi.get("loss_usd", 0)
                    for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "fintech"
                ),
                "node_count": sum(
                    1 for fi in financial_list
                    if isinstance(fi, dict) and fi.get("sector", "").lower() == "fintech"
                ),
                "classification": fintech_dict.get("classification", "MODERATE"),
            },
        },
        "decision_inputs": {
            "run_id": run_id,
            "total_loss_usd": headline.get("total_loss_usd", 0),
            "actions": [
                {
                    "id": a.get("action_id", f"ACT-{i+1}"),
                    "action": a.get("action", a.get("action_en", "")),
                    "action_ar": a.get("action_ar", ""),
                    "priority": a.get("priority_score", 0),
                    "owner": a.get("owner", ""),
                    "sector": a.get("sector", ""),
                }
                for i, a in enumerate(actions[:5])
                if isinstance(a, dict)
            ],
            "all_actions": [
                {
                    "id": a.get("action_id", f"ACT-{i+1}"),
                    "action": a.get("action", a.get("action_en", "")),
                    "action_ar": a.get("action_ar", ""),
                    "priority": a.get("priority_score", 0),
                    "owner": a.get("owner", ""),
                    "sector": a.get("sector", ""),
                }
                for i, a in enumerate(actions)
                if isinstance(a, dict)
            ],
        },
        "confidence": result.get("confidence_score", 0.85),
        "trust": {
            "audit_hash": run_id,
            "stages_completed": list(stage_timings.keys()),
        },
    }

    logger.info(json.dumps({
        "event": "pipeline_complete",
        "run_id": run_id,
        "stages_completed": 60,
        "total_ms": total_ms,
        "risk_level": response["risk_level"],
        "total_loss_usd": headline.get("total_loss_usd", 0),
    }))

    # ── Stage 85: Metrics Provenance Layer ─────────────────────────────────
    t0 = time.monotonic()
    try:
        prov_result = run_provenance_pipeline(response)
        response["provenance_layer"] = prov_result.to_dict()
        response["pipeline_stages_completed"] = 85
    except Exception as prov_err:
        logger.warning("Provenance pipeline failed: %s", prov_err, exc_info=True)
        response["provenance_layer"] = {}
    stage_timings["provenance_layer"] = round((time.monotonic() - t0) * 1000, 1)
    _log_stage("provenance_layer", run_id, stage_timings["provenance_layer"], 85)

    # ── Validation Contract Layer — detect and flag suspect values BEFORE clamping ──
    # Late validation catches issues introduced by downstream stages (19-41)
    late_validation_flags = validate_metrics(response, scenario_window_hours=float(horizon_hours))
    # Merge early + late flags (deduplicate by field+rule)
    all_flags = list(early_validation_flags) + list(late_validation_flags)
    seen_flag_keys: set[str] = set()
    deduped_flags: list = []
    for f in all_flags:
        key = f"{f.field}:{f.rule}"
        if key not in seen_flag_keys:
            seen_flag_keys.add(key)
            deduped_flags.append(f)
    if deduped_flags:
        response["validation_flags"] = [f.to_dict() for f in deduped_flags]
        logger.warning(
            "Validation flags for run %s: %d issues detected (%d early, %d late)",
            run_id, len(deduped_flags), len(early_validation_flags), len(late_validation_flags),
        )
    else:
        response["validation_flags"] = []

    # ── Final Stage: Data Sanity Guard — prevent invalid values reaching UI ──
    sanitize_run_result(response)

    return response
