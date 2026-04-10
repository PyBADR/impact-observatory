"""Decision Brain — produces structured decision output with reasoning chains.

Consumes ImpactAssessment + PipelineOutput, re-ranks actions, attaches reasoning.
Deterministic. Fail-safe (works without graph via fallback path).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.config import DB_GRAPH_CONTRIBUTION_BASE
from src.utils import clamp
from src.decision_brain.action_synthesizer import synthesize_actions

logger = logging.getLogger(__name__)


def _build_reasoning_summary(
    recommended_actions: list[dict[str, Any]],
    impact_assessment: dict[str, Any],
    risk_level: str,
    graph_available: bool,
) -> tuple[str, str]:
    """Build bilingual reasoning summary from top actions.

    Returns (summary_en, summary_ar).
    """
    composite = impact_assessment.get("composite_severity", 0.0)
    severity_class = impact_assessment.get("severity_classification", "NOMINAL")
    primary_domain = impact_assessment.get("primary_domain", "cross-sector")
    domain_count = impact_assessment.get("domain_count", 0)
    total_loss = impact_assessment.get("total_exposure_usd", 0.0)

    top_action = recommended_actions[0] if recommended_actions else {}
    action_type = top_action.get("action_type", "MONITOR")
    urgency = top_action.get("urgency", "MONITOR")

    graph_note = " Graph topology analysis contributed to reasoning." if graph_available else ""

    summary_en = (
        f"Decision analysis indicates {severity_class} composite severity ({composite:.1%}) "
        f"across {domain_count} domain(s), with {primary_domain} as primary affected domain. "
        f"Total exposure: ${total_loss:,.0f}. "
        f"Risk level: {risk_level}. "
        f"Primary recommendation: {action_type} action with {urgency} urgency. "
        f"{len(recommended_actions)} actions ranked by impact-weighted priority.{graph_note}"
    )

    summary_ar = (
        f"تحليل القرار يشير إلى شدة مركبة {severity_class} ({composite:.1%}) "
        f"عبر {domain_count} مجال(ات)، مع {primary_domain} كمجال متأثر رئيسي. "
        f"إجمالي التعرض: ${total_loss:,.0f}. "
        f"مستوى المخاطر: {risk_level}. "
        f"التوصية الرئيسية: إجراء {action_type} بدرجة إلحاح {urgency}. "
        f"تم ترتيب {len(recommended_actions)} إجراء حسب الأولوية المرجحة بالأثر."
    )

    return summary_en, summary_ar


def compute_decision_output(
    impact_assessment: dict[str, Any],
    pipeline_output: dict[str, Any],
    existing_actions: list[dict[str, Any]],
    graph_store: Optional[Any] = None,
) -> dict[str, Any]:
    """Compute structured decision output from impact assessment.

    DETERMINISTIC: Same input → same output.
    FAIL-SAFE: Works without graph_store (sets fallback_active=True).
    CONTRACT: Returns dict that passes DecisionBrainOutput.model_validate().
    """
    run_id = pipeline_output.get("run_id", "")
    scenario_id = pipeline_output.get("scenario_id", "")
    risk_level = pipeline_output.get("risk_level", "NOMINAL")
    confidence = float(impact_assessment.get("confidence", 0.0))

    graph_available = graph_store is not None

    # ── Synthesize actions ────────────────────────────────────────────────
    recommended_actions = synthesize_actions(
        existing_actions=existing_actions,
        impact_assessment=impact_assessment,
        pipeline_output=pipeline_output,
        graph_store=graph_store,
    )

    # ── Primary action ────────────────────────────────────────────────────
    top = recommended_actions[0] if recommended_actions else {}
    primary_action = top.get("action", "")
    primary_action_type = top.get("action_type", "MONITOR")
    overall_urgency = top.get("urgency", "MONITOR")

    # ── Overall confidence ────────────────────────────────────────────────
    # Average action confidence weighted by rank inverse
    if recommended_actions:
        weights = [1.0 / r.get("rank", 1) for r in recommended_actions]
        confidences = [float(r.get("confidence", 0.0)) for r in recommended_actions]
        total_w = sum(weights)
        overall_confidence = sum(c * w for c, w in zip(confidences, weights)) / max(total_w, 0.01)
    else:
        overall_confidence = confidence * 0.5

    overall_confidence = clamp(overall_confidence, 0.0, 1.0)

    # ── Reasoning chain length ────────────────────────────────────────────
    total_steps = sum(
        len(a.get("reasoning_chain", []))
        for a in recommended_actions
    )

    # ── Contribution percentages ──────────────────────────────────────────
    if graph_available:
        graph_pct = DB_GRAPH_CONTRIBUTION_BASE
        prop_pct = 1.0 - graph_pct - 0.25
        rule_pct = 0.25
    else:
        graph_pct = 0.0
        prop_pct = 0.75
        rule_pct = 0.25

    # ── Reasoning summary ─────────────────────────────────────────────────
    summary_en, summary_ar = _build_reasoning_summary(
        recommended_actions=recommended_actions,
        impact_assessment=impact_assessment,
        risk_level=risk_level,
        graph_available=graph_available,
    )

    # ── Fallback status ───────────────────────────────────────────────────
    fallback_active = not graph_available
    fallback_reason = "graph_store not available — using propagation-only reasoning" if fallback_active else ""

    output = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "decision_version": "1.0.0",

        "primary_action": primary_action,
        "primary_action_type": primary_action_type,
        "overall_urgency": overall_urgency,
        "overall_confidence": round(overall_confidence, 4),

        "recommended_actions": recommended_actions,

        "reasoning_summary_en": summary_en,
        "reasoning_summary_ar": summary_ar,
        "reasoning_chain_length": total_steps,

        "decision_basis": "graph_enriched" if graph_available else "deterministic",
        "graph_contribution_pct": round(graph_pct * 100, 1),
        "propagation_contribution_pct": round(prop_pct * 100, 1),
        "rule_contribution_pct": round(rule_pct * 100, 1),

        "fallback_active": fallback_active,
        "fallback_reason": fallback_reason,
    }

    logger.info(
        "[DecisionBrain] actions=%d urgency=%s confidence=%.4f fallback=%s",
        len(recommended_actions), overall_urgency, overall_confidence, fallback_active,
    )

    return output
