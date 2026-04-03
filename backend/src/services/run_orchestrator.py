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

    total_ms = round((time.monotonic() - t_total) * 1000, 1)

    # ── Assemble final unified response ───────────────────────────────────
    response = {
        # Identity
        "schema_version": "v2",
        "run_id": run_id,
        "model_version": result.get("model_version", "2.1.0"),
        "status": "completed",
        "pipeline_stages_completed": 18,
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
        # financial → financial_impact (full dict, per checklist)
        "financial": result.get("financial_impact", {}),
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
    }

    logger.info(json.dumps({
        "event": "pipeline_complete",
        "run_id": run_id,
        "stages_completed": 18,
        "total_ms": total_ms,
        "risk_level": response["risk_level"],
        "total_loss_usd": headline.get("total_loss_usd", 0),
    }))

    return response
