"""
Decision ROI Engine — strict per-run, per-scenario ROI computation.

Formula:
  ROI = (baseline_loss - action_loss) - cost

Rules:
  - Per run only. No cross-run contamination.
  - Per scenario only. No cross-scenario blending.
  - ROI can be negative (action costs more than it saves).
  - All inputs must come from THIS run's simulation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.decision_intelligence.action_simulation_engine import ActionSimResult
from src.decision_intelligence.counterfactual_engine import CounterfactualResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DecisionROI:
    """ROI for a single decision action in a single run."""
    run_id: str
    scenario_id: str
    action_id: str
    action_label: str

    # Core ROI components
    baseline_loss_usd: float       # loss without action
    action_loss_usd: float         # loss with action
    loss_avoided_usd: float        # baseline - action
    action_cost_usd: float         # cost to execute action
    net_benefit_usd: float         # loss_avoided - cost
    roi_ratio: float               # net_benefit / cost (or inf if cost=0)

    # Per-scenario isolation
    scenario_contribution: float   # [0-1] what fraction of ROI is from this scenario

    # Risk-adjusted ROI
    risk_adjusted_roi: float       # roi_ratio × confidence
    confidence: float              # [0-1] from counterfactual

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "action_id": self.action_id,
            "action_label": self.action_label,
            "baseline_loss_usd": round(self.baseline_loss_usd, 2),
            "action_loss_usd": round(self.action_loss_usd, 2),
            "loss_avoided_usd": round(self.loss_avoided_usd, 2),
            "action_cost_usd": round(self.action_cost_usd, 2),
            "net_benefit_usd": round(self.net_benefit_usd, 2),
            "roi_ratio": round(self.roi_ratio, 4),
            "scenario_contribution": round(self.scenario_contribution, 4),
            "risk_adjusted_roi": round(self.risk_adjusted_roi, 4),
            "confidence": round(self.confidence, 4),
        }


def compute_decision_roi(
    run_id: str,
    scenario_id: str,
    sim_results: list[ActionSimResult],
    counterfactual: CounterfactualResult,
    action_costs: dict[str, float],
) -> list[DecisionROI]:
    """
    Compute ROI for each simulated action.

    Args:
        run_id:          This run's ID.
        scenario_id:     This scenario's ID.
        sim_results:     ActionSimResult list from simulation.
        counterfactual:  CounterfactualResult for baseline reference.
        action_costs:    dict[action_id → cost_usd] from action_registry.

    Returns:
        list[DecisionROI] sorted by net_benefit descending.
    """
    rois: list[DecisionROI] = []
    baseline_loss = counterfactual.baseline_loss_usd

    for sim in sim_results:
        cost = action_costs.get(sim.action_id, 0.0)
        loss_avoided = max(0, baseline_loss - sim.mitigated_loss_usd)
        net_benefit = loss_avoided - cost

        # ROI ratio: net_benefit / cost
        if cost > 0:
            roi_ratio = net_benefit / cost
        elif loss_avoided > 0:
            roi_ratio = float("inf")  # free action with positive return
        else:
            roi_ratio = 0.0

        # Scenario contribution: 1.0 (strict per-scenario isolation)
        scenario_contribution = 1.0

        # Risk-adjusted ROI
        risk_adjusted = roi_ratio * counterfactual.confidence if roi_ratio != float("inf") else roi_ratio

        rois.append(DecisionROI(
            run_id=run_id,
            scenario_id=scenario_id,
            action_id=sim.action_id,
            action_label=sim.action_label,
            baseline_loss_usd=baseline_loss,
            action_loss_usd=sim.mitigated_loss_usd,
            loss_avoided_usd=loss_avoided,
            action_cost_usd=cost,
            net_benefit_usd=net_benefit,
            roi_ratio=roi_ratio,
            scenario_contribution=scenario_contribution,
            risk_adjusted_roi=risk_adjusted,
            confidence=counterfactual.confidence,
        ))

    # Sort by net_benefit descending
    rois.sort(key=lambda r: -r.net_benefit_usd)

    logger.info("[ROIEngine] Computed ROI for %d actions (top: $%.0f net benefit)",
                len(rois), rois[0].net_benefit_usd if rois else 0)
    return rois
