"""
Decision Intelligence Pipeline — chains all 7 engines into Stage 50.

Flow:
  ImpactMap → Triggers → Breakpoints → ActionSim → Counterfactual → ROI → Executive

Single entry point: run_decision_intelligence_pipeline()
Returns: DecisionIntelligenceResult (full output of all 7 engines)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.schemas.impact_map import ImpactMapResponse
from src.decision_intelligence.trigger_engine import GraphDecisionTrigger, build_graph_triggers
from src.decision_intelligence.breakpoint_engine import Breakpoint, detect_breakpoints
from src.decision_intelligence.action_simulation_engine import ActionSimResult, simulate_action_effects
from src.decision_intelligence.counterfactual_engine import CounterfactualResult, compare_counterfactuals
from src.decision_intelligence.roi_engine import DecisionROI, compute_decision_roi
from src.decision_intelligence.executive_output import ExecutiveDecision, build_executive_decisions

logger = logging.getLogger(__name__)


@dataclass
class DecisionIntelligenceResult:
    """Full output of the Decision Intelligence pipeline."""
    triggers: list[GraphDecisionTrigger] = field(default_factory=list)
    breakpoints: list[Breakpoint] = field(default_factory=list)
    action_simulations: list[ActionSimResult] = field(default_factory=list)
    counterfactual: CounterfactualResult | None = None
    roi: list[DecisionROI] = field(default_factory=list)
    executive_decisions: list[ExecutiveDecision] = field(default_factory=list)
    stage_timings: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "triggers": [t.to_dict() for t in self.triggers],
            "breakpoints": [b.to_dict() for b in self.breakpoints],
            "action_simulations": [s.to_dict() for s in self.action_simulations],
            "counterfactual": self.counterfactual.to_dict() if self.counterfactual else None,
            "roi": [r.to_dict() for r in self.roi],
            "executive_decisions": [d.to_dict() for d in self.executive_decisions],
            "stage_timings": self.stage_timings,
            "trigger_count": len(self.triggers),
            "breakpoint_count": len(self.breakpoints),
            "executive_decision_count": len(self.executive_decisions),
        }


def run_decision_intelligence_pipeline(
    impact_map: ImpactMapResponse,
    action_costs: dict[str, float] | None = None,
    action_registry_lookup: dict[str, dict[str, Any]] | None = None,
) -> DecisionIntelligenceResult:
    """
    Run the full Decision Intelligence pipeline.

    Args:
        impact_map:              ImpactMapResponse from Stage 42.
        action_costs:            dict[action_id → cost_usd].
        action_registry_lookup:  dict[action_id → ActionTemplate dict].

    Returns:
        DecisionIntelligenceResult with all 7 engine outputs.
    """
    result = DecisionIntelligenceResult()
    if action_costs is None:
        action_costs = {}
    if action_registry_lookup is None:
        action_registry_lookup = {}

    # ── Step 1: Decision Triggers ───────────────────────────────────────────
    t0 = time.monotonic()
    result.triggers = build_graph_triggers(impact_map)
    result.stage_timings["trigger_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 2: Breakpoint Detection ────────────────────────────────────────
    t0 = time.monotonic()
    result.breakpoints = detect_breakpoints(impact_map)
    result.stage_timings["breakpoint_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 3: Action Effect Simulation ────────────────────────────────────
    t0 = time.monotonic()
    if impact_map.decision_overlays:
        result.action_simulations = simulate_action_effects(
            impact_map, impact_map.decision_overlays,
        )
    result.stage_timings["action_simulation"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 4: Counterfactual Comparison ───────────────────────────────────
    t0 = time.monotonic()
    result.counterfactual = compare_counterfactuals(
        impact_map, result.action_simulations, action_costs,
    )
    result.stage_timings["counterfactual_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 5: ROI Computation ─────────────────────────────────────────────
    t0 = time.monotonic()
    if result.action_simulations and result.counterfactual:
        result.roi = compute_decision_roi(
            run_id=impact_map.run_id,
            scenario_id=impact_map.scenario_id,
            sim_results=result.action_simulations,
            counterfactual=result.counterfactual,
            action_costs=action_costs,
        )
    result.stage_timings["roi_engine"] = round((time.monotonic() - t0) * 1000, 2)

    # ── Step 6: Executive Decision Output ───────────────────────────────────
    t0 = time.monotonic()
    result.executive_decisions = build_executive_decisions(
        triggers=result.triggers,
        breakpoints=result.breakpoints,
        sim_results=result.action_simulations,
        counterfactual=result.counterfactual,
        rois=result.roi,
        action_registry_lookup=action_registry_lookup,
    )
    result.stage_timings["executive_output"] = round((time.monotonic() - t0) * 1000, 2)

    total_ms = sum(result.stage_timings.values())
    logger.info(
        "[DecisionIntelligence] Pipeline complete: %d triggers, %d breakpoints, "
        "%d sims, %d ROIs, %d exec decisions (%.1fms total)",
        len(result.triggers), len(result.breakpoints),
        len(result.action_simulations), len(result.roi),
        len(result.executive_decisions), total_ms,
    )

    return result
