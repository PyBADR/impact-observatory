"""
Executive Decision Formatter — produces the final structured output.

Rules:
  - Return ONLY top 3 decisions
  - Sort by: urgency, impact, time_to_failure
  - NO dashboards, ONLY decisions
  - Every decision fully enriched with gate, confidence, pathway, tradeoffs

Consumed by: Stage 60 pipeline (final output step)
Input: All Stage 60 engine outputs
Output: list[FormattedExecutiveDecision]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.anchoring_engine import AnchoredDecision
from src.decision_quality.gate_engine import DecisionGate
from src.decision_quality.confidence_engine import DecisionConfidence
from src.decision_quality.pathway_engine import ActionPathway
from src.decision_quality.outcome_engine import DecisionOutcome

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FormattedExecutiveDecision:
    """Final formatted executive decision — fully enriched and validated."""
    # Identity
    decision_id: str
    rank: int

    # Action
    action_id: str
    action_en: str
    action_ar: str
    sector: str

    # Ownership
    decision_owner: str
    decision_owner_ar: str
    decision_type: str
    decision_type_ar: str

    # Timing
    decision_deadline: str
    time_window_hours: float
    created_at: str

    # Scores
    urgency: float
    impact: float
    downside_risk: float

    # Loss
    loss_avoided_usd: float
    loss_avoided_formatted: str
    roi_ratio: float

    # Confidence (multi-dimensional)
    confidence_composite: float
    confidence_dimensions: list[dict[str, Any]] = field(default_factory=list)
    model_dependency: str = "moderate"
    external_validation_required: bool = False

    # Gate
    gate_status: str = "DRAFT"
    approval_required: bool = False
    approver: str = ""

    # Pathway
    pathway_type: str = "IMMEDIATE"
    trigger_condition: str = ""
    reversibility: str = "partially_reversible"

    # Tradeoffs
    tradeoffs: list[dict[str, str]] = field(default_factory=list)

    # Outcome expectations
    expected_loss_reduction_pct: float = 0.0
    measurable_kpi: str = ""
    measurable_kpi_ar: str = ""

    # Warnings
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "rank": self.rank,
            "action_id": self.action_id,
            "action_en": self.action_en,
            "action_ar": self.action_ar,
            "sector": self.sector,
            "decision_owner": self.decision_owner,
            "decision_owner_ar": self.decision_owner_ar,
            "decision_type": self.decision_type,
            "decision_type_ar": self.decision_type_ar,
            "decision_deadline": self.decision_deadline,
            "time_window_hours": round(self.time_window_hours, 1),
            "created_at": self.created_at,
            "urgency": round(self.urgency, 4),
            "impact": round(self.impact, 4),
            "downside_risk": round(self.downside_risk, 4),
            "loss_avoided_usd": round(self.loss_avoided_usd, 2),
            "loss_avoided_formatted": self.loss_avoided_formatted,
            "roi_ratio": round(self.roi_ratio, 4),
            "confidence_composite": round(self.confidence_composite, 4),
            "confidence_dimensions": self.confidence_dimensions,
            "model_dependency": self.model_dependency,
            "external_validation_required": self.external_validation_required,
            "gate_status": self.gate_status,
            "approval_required": self.approval_required,
            "approver": self.approver,
            "pathway_type": self.pathway_type,
            "trigger_condition": self.trigger_condition,
            "reversibility": self.reversibility,
            "tradeoffs": self.tradeoffs,
            "expected_loss_reduction_pct": round(self.expected_loss_reduction_pct, 2),
            "measurable_kpi": self.measurable_kpi,
            "measurable_kpi_ar": self.measurable_kpi_ar,
            "warnings": self.warnings,
        }


def format_executive_decisions(
    anchored: list[AnchoredDecision],
    gates: list[DecisionGate],
    confidences: list[DecisionConfidence],
    pathways: list[ActionPathway],
    outcomes: list[DecisionOutcome],
) -> list[FormattedExecutiveDecision]:
    """
    Merge all quality-layer outputs into final executive decisions.

    Args:
        anchored:     From anchoring_engine.
        gates:        From gate_engine.
        confidences:  From confidence_engine.
        pathways:     From pathway_engine.
        outcomes:     From outcome_engine.

    Returns:
        list[FormattedExecutiveDecision] — top 3 ONLY, sorted by urgency × impact.
    """
    # Build lookup maps
    gate_map: dict[str, DecisionGate] = {g.decision_id: g for g in gates}
    conf_map: dict[str, DecisionConfidence] = {c.decision_id: c for c in confidences}
    outcome_map: dict[str, DecisionOutcome] = {o.decision_id: o for o in outcomes}

    # Build action_id → pathway detail lookup
    pathway_detail_map: dict[str, dict[str, Any]] = {}
    for pw in pathways:
        for act in pw.actions:
            pathway_detail_map[act.action_id] = {
                "pathway_type": pw.pathway_type,
                "trigger_condition": act.trigger_condition,
                "reversibility": act.reversibility,
            }

    formatted: list[FormattedExecutiveDecision] = []

    for ad in anchored:
        if not ad.is_valid:
            continue

        gate = gate_map.get(ad.decision_id)
        conf = conf_map.get(ad.decision_id)
        outcome = outcome_map.get(ad.decision_id)
        pw_detail = pathway_detail_map.get(ad.action_id, {})

        # Collect warnings from confidence engine
        warnings = list(conf.warnings) if conf else []

        formatted.append(FormattedExecutiveDecision(
            decision_id=ad.decision_id,
            rank=ad.rank,
            action_id=ad.action_id,
            action_en=ad.action_en,
            action_ar=ad.action_ar,
            sector=ad.sector,
            decision_owner=ad.decision_owner,
            decision_owner_ar=ad.decision_owner_ar,
            decision_type=ad.decision_type,
            decision_type_ar=ad.decision_type_ar,
            decision_deadline=ad.decision_deadline,
            time_window_hours=ad.time_window_hours,
            created_at=ad.created_at,
            urgency=ad.urgency,
            impact=ad.impact,
            downside_risk=ad.downside_risk,
            loss_avoided_usd=ad.loss_avoided_usd,
            loss_avoided_formatted=ad.loss_avoided_formatted,
            roi_ratio=ad.roi_ratio,
            confidence_composite=conf.composite_score if conf else ad.confidence,
            confidence_dimensions=[d.to_dict() for d in conf.dimensions] if conf else [],
            model_dependency=conf.model_dependency if conf else "moderate",
            external_validation_required=conf.external_validation_required if conf else False,
            gate_status=gate.current_status if gate else "DRAFT",
            approval_required=gate.approval_required if gate else False,
            approver=gate.approver_en if gate else "",
            pathway_type=pw_detail.get("pathway_type", "IMMEDIATE"),
            trigger_condition=pw_detail.get("trigger_condition", ""),
            reversibility=pw_detail.get("reversibility", "partially_reversible"),
            tradeoffs=ad.tradeoffs,
            expected_loss_reduction_pct=outcome.expected_loss_reduction_pct if outcome else 0.0,
            measurable_kpi=outcome.measurable_kpi_en if outcome else "",
            measurable_kpi_ar=outcome.measurable_kpi_ar if outcome else "",
            warnings=warnings,
        ))

    # Sort by urgency × impact descending, take top 3
    formatted.sort(key=lambda d: -(d.urgency * 0.5 + d.impact * 0.3 + (1.0 - d.downside_risk) * 0.2))
    formatted = formatted[:3]

    # Re-rank
    final: list[FormattedExecutiveDecision] = []
    for i, f in enumerate(formatted):
        # Create new instance with updated rank
        final.append(FormattedExecutiveDecision(
            decision_id=f.decision_id,
            rank=i + 1,
            action_id=f.action_id,
            action_en=f.action_en,
            action_ar=f.action_ar,
            sector=f.sector,
            decision_owner=f.decision_owner,
            decision_owner_ar=f.decision_owner_ar,
            decision_type=f.decision_type,
            decision_type_ar=f.decision_type_ar,
            decision_deadline=f.decision_deadline,
            time_window_hours=f.time_window_hours,
            created_at=f.created_at,
            urgency=f.urgency,
            impact=f.impact,
            downside_risk=f.downside_risk,
            loss_avoided_usd=f.loss_avoided_usd,
            loss_avoided_formatted=f.loss_avoided_formatted,
            roi_ratio=f.roi_ratio,
            confidence_composite=f.confidence_composite,
            confidence_dimensions=f.confidence_dimensions,
            model_dependency=f.model_dependency,
            external_validation_required=f.external_validation_required,
            gate_status=f.gate_status,
            approval_required=f.approval_required,
            approver=f.approver,
            pathway_type=f.pathway_type,
            trigger_condition=f.trigger_condition,
            reversibility=f.reversibility,
            tradeoffs=f.tradeoffs,
            expected_loss_reduction_pct=f.expected_loss_reduction_pct,
            measurable_kpi=f.measurable_kpi,
            measurable_kpi_ar=f.measurable_kpi_ar,
            warnings=f.warnings,
        ))

    logger.info("[FormatterEngine] Formatted %d executive decisions", len(final))
    return final
