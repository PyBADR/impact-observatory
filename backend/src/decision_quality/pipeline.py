"""
Decision Quality Pipeline — Stage 60.

Chains all 7 engines:
  Anchoring → Pathway → Gate → Confidence → Outcome → Formatter

Single entry point: run_decision_quality_pipeline()
Input: DecisionIntelligenceResult (Stage 50) + action_registry_lookup
Output: DecisionQualityResult
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.decision_intelligence.pipeline import DecisionIntelligenceResult
from src.decision_quality.anchoring_engine import AnchoredDecision, anchor_decisions
from src.decision_quality.pathway_engine import ActionPathway, build_action_pathways
from src.decision_quality.gate_engine import DecisionGate, apply_decision_gates
from src.decision_quality.confidence_engine import DecisionConfidence, compute_decision_confidence
from src.decision_quality.outcome_engine import DecisionOutcome, build_outcome_expectations
from src.decision_quality.formatter_engine import FormattedExecutiveDecision, format_executive_decisions

logger = logging.getLogger(__name__)


@dataclass
class DecisionQualityResult:
    """Full output of the Decision Quality pipeline (Stage 60)."""
    anchored_decisions: list[AnchoredDecision] = field(default_factory=list)
    action_pathways: list[ActionPathway] = field(default_factory=list)
    decision_gates: list[DecisionGate] = field(default_factory=list)
    confidences: list[DecisionConfidence] = field(default_factory=list)
    outcomes: list[DecisionOutcome] = field(default_factory=list)
    executive_decisions: list[FormattedExecutiveDecision] = field(default_factory=list)
    stage_timings: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchored_decisions": [a.to_dict() for a in self.anchored_decisions],
            "action_pathways": [p.to_dict() for p in self.action_pathways],
            "decision_gates": [g.to_dict() for g in self.decision_gates],
            "confidences": [c.to_dict() for c in self.confidences],
            "outcomes": [o.to_dict() for o in self.outcomes],
            "executive_decisions": [d.to_dict() for d in self.executive_decisions],
            "stage_timings": self.stage_timings,
            "anchored_count": len(self.anchored_decisions),
            "valid_count": sum(1 for a in self.anchored_decisions if a.is_valid),
            "pathway_count": len(self.action_pathways),
            "gate_count": len(self.decision_gates),
            "executive_decision_count": len(self.executive_decisions),
        }


def run_decision_quality_pipeline(
    di_result: DecisionIntelligenceResult,
    action_registry_lookup: dict[str, dict[str, Any]] | None = None,
    run_timestamp: datetime | None = None,
) -> DecisionQualityResult:
    """
    Run the full Decision Quality pipeline (Stage 60).

    Args:
        di_result:               DecisionIntelligenceResult from Stage 50.
        action_registry_lookup:  dict[action_id → ActionTemplate dict].
        run_timestamp:           Base timestamp for deadline computation.

    Returns:
        DecisionQualityResult with all engine outputs.
    """
    result = DecisionQualityResult()
    if action_registry_lookup is None:
        action_registry_lookup = {}
    if run_timestamp is None:
        run_timestamp = datetime.now(timezone.utc)

    if not di_result.executive_decisions:
        logger.warning("[DecisionQuality] No executive decisions from Stage 50 — returning empty")
        return result

    # ── Step 1: Decision Anchoring ─────────────────────────────────────────
    t0 = time.monotonic()
    result.anchored_decisions = anchor_decisions(
        executive_decisions=di_result.executive_decisions,
        action_registry_lookup=action_registry_lookup,
        run_timestamp=run_timestamp,
    )
    result.stage_timings["anchoring_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 2: Action Pathways ────────────────────────────────────────────
    t0 = time.monotonic()
    result.action_pathways = build_action_pathways(
        anchored_decisions=result.anchored_decisions,
        action_registry_lookup=action_registry_lookup,
        triggers=di_result.triggers,
        breakpoints=di_result.breakpoints,
    )
    result.stage_timings["pathway_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 3: Decision Gates ─────────────────────────────────────────────
    t0 = time.monotonic()
    result.decision_gates = apply_decision_gates(
        anchored_decisions=result.anchored_decisions,
        triggers=di_result.triggers,
    )
    result.stage_timings["gate_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 4: Decision Confidence ────────────────────────────────────────
    t0 = time.monotonic()
    result.confidences = compute_decision_confidence(
        anchored_decisions=result.anchored_decisions,
        counterfactual=di_result.counterfactual,
        sim_results=di_result.action_simulations,
    )
    result.stage_timings["confidence_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 5: Outcome Expectations ───────────────────────────────────────
    t0 = time.monotonic()
    result.outcomes = build_outcome_expectations(
        anchored_decisions=result.anchored_decisions,
        sim_results=di_result.action_simulations,
        counterfactual=di_result.counterfactual,
    )
    result.stage_timings["outcome_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 6: Executive Decision Formatter ───────────────────────────────
    t0 = time.monotonic()
    result.executive_decisions = format_executive_decisions(
        anchored=result.anchored_decisions,
        gates=result.decision_gates,
        confidences=result.confidences,
        pathways=result.action_pathways,
        outcomes=result.outcomes,
    )
    result.stage_timings["formatter_engine"] = round((time.monotonic() - t0) * 1000, 2)

    total_ms = sum(result.stage_timings.values())
    logger.info(
        "[DecisionQuality] Pipeline complete: %d anchored, %d pathways, %d gates, "
        "%d exec decisions (%.1fms total)",
        len(result.anchored_decisions), len(result.action_pathways),
        len(result.decision_gates), len(result.executive_decisions), total_ms,
    )

    return result
