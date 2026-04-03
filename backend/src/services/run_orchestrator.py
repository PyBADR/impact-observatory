"""Run Orchestrator — chains all 12 services in sequence.

Pipeline: Scenario → Entity Graph → Physics → Propagation → Financial →
          Banking → Insurance → Fintech → Decision → Explainability →
          Reporting → Audit

Every output maps: Event → Financial Impact → Sector Stress → Decision
"""

from __future__ import annotations

import json
import logging
import time

from src.schemas.scenario import ScenarioCreate
from src.services import (
    scenario_service,
    physics_service,
    propagation_service,
    entity_graph_service,
    financial_service,
    banking_service,
    insurance_service,
    fintech_service,
    decision_service,
    explainability_service,
    reporting_service,
    audit_service,
    business_impact_service,
    timeline_service,
    regulatory_service,
)

logger = logging.getLogger(__name__)


def _log_stage(stage: str, run_id: str, ms: float, stages_done: int) -> None:
    """Emit structured JSON log after each pipeline stage."""
    logger.info(json.dumps({
        "event": "stage_complete",
        "stage": stage,
        "run_id": run_id,
        "ms": round(ms, 1),
        "stages_done": stages_done,
    }))


def execute_run(params: ScenarioCreate) -> dict:
    """Execute a full scenario run through all 12 services.

    Returns the complete run result with all sector outputs,
    stage_timings dict, and pipeline_stages_completed count.
    """
    run_start = time.monotonic()
    start_ms = time.time() * 1000
    stage_timings: dict[str, float] = {}
    stages_completed = 0

    # ── Step 1: Scenario Service ──────────────────────────────────
    t0 = time.monotonic()
    run = scenario_service.create_run(params)
    run_id = run["run_id"]
    template = run["template"]
    severity = params.severity
    horizon_hours = params.horizon_hours
    stage_timings["scenario"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("scenario", run_id, stage_timings["scenario"], stages_completed)

    # Audit: record start
    audit_service.record_run_start(
        run_id=run_id,
        template_id=params.scenario_id,
        severity=severity,
        horizon_hours=horizon_hours,
    )

    # ── Step 2: Entity Graph ──────────────────────────────────────
    t0 = time.monotonic()
    entities = entity_graph_service.get_entities()
    edges = entity_graph_service.get_edges()
    shock_nodes = template["shock_nodes"]
    stage_timings["entity_graph"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("entity_graph", run_id, stage_timings["entity_graph"], stages_completed)

    # ── Step 3: Physics Service ───────────────────────────────────
    t0 = time.monotonic()
    flow_states = physics_service.compute_flow_states(
        entities=entities,
        edges=edges,
        shock_nodes=shock_nodes,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    stage_timings["physics"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("physics", run_id, stage_timings["physics"], stages_completed)

    # ── Step 4: Propagation Service ───────────────────────────────
    t0 = time.monotonic()
    propagation_results = propagation_service.propagate_impacts(
        entities=entities,
        edges=edges,
        shock_nodes=shock_nodes,
        severity=severity,
    )
    stage_timings["propagation"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("propagation", run_id, stage_timings["propagation"], stages_completed)

    # ── Step 5: Financial Service ─────────────────────────────────
    t0 = time.monotonic()
    financial_impacts = financial_service.compute_financial_impacts(
        entities=entities,
        propagation_results=propagation_results,
        severity=severity,
        horizon_hours=horizon_hours,
        base_loss_usd=template["base_loss_usd"],
        peak_day_offset=template["peak_day_offset"],
        recovery_base_days=template["recovery_base_days"],
    )
    headline = financial_service.compute_headline_loss(financial_impacts)
    stage_timings["financial"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("financial", run_id, stage_timings["financial"], stages_completed)

    # ── Step 6: Banking Service ───────────────────────────────────
    t0 = time.monotonic()
    banking = banking_service.compute_banking_stress(
        run_id=run_id,
        financial_impacts=financial_impacts,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    stage_timings["banking"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("banking", run_id, stage_timings["banking"], stages_completed)

    # ── Step 7: Insurance Service ─────────────────────────────────
    t0 = time.monotonic()
    insurance = insurance_service.compute_insurance_stress(
        run_id=run_id,
        financial_impacts=financial_impacts,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    stage_timings["insurance"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("insurance", run_id, stage_timings["insurance"], stages_completed)

    # ── Step 8: Fintech Service ───────────────────────────────────
    t0 = time.monotonic()
    fintech = fintech_service.compute_fintech_stress(
        run_id=run_id,
        financial_impacts=financial_impacts,
        severity=severity,
        horizon_hours=horizon_hours,
    )
    stage_timings["fintech"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("fintech", run_id, stage_timings["fintech"], stages_completed)

    # ── Step 9: Decision Service ──────────────────────────────────
    t0 = time.monotonic()
    decision_plan = decision_service.compute_decision_plan(
        run_id=run_id,
        financial_impacts=financial_impacts,
        banking=banking,
        insurance=insurance,
        fintech=fintech,
        scenario_label=run["label"],
    )
    stage_timings["decision"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("decision", run_id, stage_timings["decision"], stages_completed)

    # ── Step 10: Explainability Service ───────────────────────────
    t0 = time.monotonic()
    explanation = explainability_service.generate_explanation(
        run_id=run_id,
        entities=entities,
        edges=edges,
        propagation_results=propagation_results,
        financial_impacts=financial_impacts,
        scenario_label=run["label"],
        severity=severity,
    )
    stage_timings["explainability"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("explainability", run_id, stage_timings["explainability"], stages_completed)

    # ── Step 11: Reporting Service ────────────────────────────────
    t0 = time.monotonic()
    executive_report = reporting_service.generate_executive_report(
        run_id=run_id,
        financial_impacts=financial_impacts,
        banking=banking,
        insurance=insurance,
        fintech=fintech,
        decision_plan=decision_plan,
        explanation=explanation,
        lang="en",
    )
    stage_timings["reporting"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("reporting", run_id, stage_timings["reporting"], stages_completed)

    # ── Step 12: Audit ────────────────────────────────────────────
    t0 = time.monotonic()
    duration_ms = time.time() * 1000 - start_ms
    audit_service.record_run_complete(
        run_id=run_id,
        total_loss_usd=headline["total_loss_usd"],
        critical_count=headline["critical_count"],
        actions_count=len(decision_plan.actions),
        duration_ms=duration_ms,
    )

    # Record each decision action
    for action in decision_plan.actions:
        audit_service.record_decision_action(
            run_id=run_id,
            action_id=action.id,
            action=action.action,
            owner=action.owner,
            priority=action.priority,
        )

    # Mark run complete
    scenario_service.complete_run(run_id, {"headline": headline})
    stage_timings["audit"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("audit", run_id, stage_timings["audit"], stages_completed)

    total_ms = round((time.monotonic() - run_start) * 1000, 1)
    logger.info(json.dumps({
        "event": "pipeline_complete",
        "run_id": run_id,
        "stages_completed": stages_completed,
        "total_ms": total_ms,
    }))

    # ── Assemble full result ──────────────────────────────────────
    financial_list = [i.model_dump() for i in financial_impacts]
    banking_dict = banking.model_dump()
    insurance_dict = insurance.model_dump()
    fintech_dict = fintech.model_dump()
    decisions_dict = decision_plan.model_dump()
    explanation_dict = explanation.model_dump()

    result = {
        "schema_version": "v1",
        "run_id": run_id,
        "status": "completed",
        "pipeline_stages_completed": stages_completed,
        "stage_timings": stage_timings,
        "scenario": {
            "scenario_id": params.scenario_id,
            "label": run["label"],
            "label_ar": run.get("label_ar"),
            "severity": severity,
            "horizon_hours": horizon_hours,
        },
        # Canonical keys
        "headline": headline,
        "financial": financial_list,
        "banking": banking_dict,
        "insurance": insurance_dict,
        "fintech": fintech_dict,
        "decisions": decisions_dict,
        "explanation": explanation_dict,
        "executive_report": executive_report,
        "flow_states": [f.model_dump() for f in flow_states[:10]],
        "propagation": propagation_results[:15],
        "duration_ms": round(duration_ms, 1),
        # Top-level fields for run_store persistence
        "scenario_id": params.scenario_id,
        "severity": severity,
        "horizon_hours": horizon_hours,
        # Frontend backward-compatible aliases
        "headline_loss_usd": headline["total_loss_usd"],
        "severity_pct": round(severity * 100, 1),
        "peak_day": headline.get("peak_day", 0),
        "financial_impacts": financial_list,
        "banking_stress": banking_dict,
        "insurance_stress": insurance_dict,
        "fintech_stress": fintech_dict,
        "decision_actions": decisions_dict.get("actions", []),
        "narrative": explanation_dict.get("narrative_en", ""),
        "methodology": explanation_dict.get("methodology", "deterministic_propagation"),
    }

    # ── Step 13: Business Impact Service ─────────────────────────
    t0 = time.monotonic()
    impact_input = {
        "run_id": run_id,
        "scenario": result["scenario"],
        "financial_impacts": result["financial"],
        "headline_loss_usd": headline["total_loss_usd"],
        "banking_stress": banking_dict,
        "insurance_stress": insurance_dict,
        "fintech_stress": fintech_dict,
    }
    business_impact = business_impact_service.compute_business_impact(impact_input)
    result["business_impact"] = business_impact
    stage_timings["business_impact"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("business_impact", run_id, stage_timings["business_impact"], stages_completed)

    # ── Step 14: Timeline Service ────────────────────────────────
    t0 = time.monotonic()
    timeline = timeline_service.compute_timeline(impact_input)
    result["timeline"] = timeline
    stage_timings["timeline"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("timeline", run_id, stage_timings["timeline"], stages_completed)

    # ── Step 15: Regulatory Service ──────────────────────────────
    t0 = time.monotonic()
    regulatory_state = regulatory_service.compute_regulatory_state(
        run_id=run_id,
        banking=banking_dict,
        insurance=insurance_dict,
        fintech=fintech_dict,
    )
    result["regulatory_state"] = regulatory_state
    stage_timings["regulatory"] = round((time.monotonic() - t0) * 1000, 1)
    stages_completed += 1
    _log_stage("regulatory", run_id, stage_timings["regulatory"], stages_completed)

    result["pipeline_stages_completed"] = stages_completed
    return result
