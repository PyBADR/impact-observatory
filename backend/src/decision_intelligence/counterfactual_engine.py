"""
Counterfactual Comparison Engine — compares scenarios with/without actions.

Three scenarios compared:
  A) Baseline — no action taken (current ImpactMapResponse as-is)
  B) Recommended — top action applied (from ActionSimResult)
  C) Alternative — second-best action applied

Output: CounterfactualResult with loss deltas, risk reduction, time gain.

Strict rule: per-run, per-scenario only. No cross-run contamination.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.schemas.impact_map import ImpactMapResponse
from src.decision_intelligence.action_simulation_engine import ActionSimResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    """Comparison of baseline vs action vs alternative."""
    run_id: str
    scenario_id: str

    # Scenario A: no action
    baseline_loss_usd: float
    baseline_breached_nodes: int
    baseline_risk_level: str

    # Scenario B: recommended action
    action_id: str
    action_label: str
    action_loss_usd: float
    action_breached_prevented: int

    # Scenario C: alternative action (or N/A if only 1 action)
    alt_action_id: str
    alt_action_label: str
    alt_loss_usd: float

    # Deltas
    delta_loss_usd: float          # baseline - action (positive = saved)
    delta_loss_pct: float           # percentage reduction
    risk_reduction: float           # [0-1] how much risk was reduced
    time_gain_hours: float          # additional hours before first breach
    alt_delta_loss_usd: float      # baseline - alternative

    # Meta
    confidence: float               # [0-1] confidence in counterfactual
    narrative_en: str
    narrative_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "baseline_loss_usd": round(self.baseline_loss_usd, 2),
            "baseline_breached_nodes": self.baseline_breached_nodes,
            "baseline_risk_level": self.baseline_risk_level,
            "action_id": self.action_id,
            "action_label": self.action_label,
            "action_loss_usd": round(self.action_loss_usd, 2),
            "action_breached_prevented": self.action_breached_prevented,
            "alt_action_id": self.alt_action_id,
            "alt_action_label": self.alt_action_label,
            "alt_loss_usd": round(self.alt_loss_usd, 2),
            "delta_loss_usd": round(self.delta_loss_usd, 2),
            "delta_loss_pct": round(self.delta_loss_pct, 2),
            "risk_reduction": round(self.risk_reduction, 4),
            "time_gain_hours": round(self.time_gain_hours, 1),
            "alt_delta_loss_usd": round(self.alt_delta_loss_usd, 2),
            "confidence": round(self.confidence, 4),
            "narrative_en": self.narrative_en,
            "narrative_ar": self.narrative_ar,
        }


def compare_counterfactuals(
    impact_map: ImpactMapResponse,
    sim_results: list[ActionSimResult],
    action_costs: dict[str, float] | None = None,
) -> CounterfactualResult:
    """
    Compare no-action baseline vs recommended vs alternative.

    Args:
        impact_map:     Current ImpactMapResponse (baseline state).
        sim_results:    ActionSimResult list from action_simulation_engine
                       (sorted by propagation_reduction descending).
        action_costs:   Optional dict[action_id → cost_usd] for ROI inputs.

    Returns:
        CounterfactualResult — single result for this run.
    """
    # ── Baseline (Scenario A) ───────────────────────────────────────────────
    baseline_loss = sum(n.loss_usd for n in impact_map.nodes)
    baseline_breached = sum(1 for n in impact_map.nodes if n.state == "BREACHED")
    baseline_risk = impact_map.headline.risk_level

    # Baseline time-to-first-breach
    breach_times = [
        n.time_to_breach_hours for n in impact_map.nodes
        if n.time_to_breach_hours is not None and n.time_to_breach_hours > 0
    ]
    baseline_ttfb = min(breach_times) if breach_times else 9999.0

    # ── Recommended action (Scenario B) ─────────────────────────────────────
    if sim_results:
        recommended = sim_results[0]
        action_loss = recommended.mitigated_loss_usd
        action_prevented = recommended.failure_prevention_count
        # Time gain from delay changes
        time_gain = max(0, recommended.delay_change_hours) if recommended.delay_change_hours > 0 else (
            recommended.propagation_reduction * baseline_ttfb * 0.3
        )
    else:
        recommended = None
        action_loss = baseline_loss
        action_prevented = 0
        time_gain = 0.0

    # ── Alternative action (Scenario C) ─────────────────────────────────────
    if len(sim_results) >= 2:
        alternative = sim_results[1]
        alt_loss = alternative.mitigated_loss_usd
    else:
        alternative = None
        alt_loss = baseline_loss

    # ── Deltas ──────────────────────────────────────────────────────────────
    delta_loss = baseline_loss - action_loss
    delta_pct = (delta_loss / max(baseline_loss, 1.0)) * 100.0
    alt_delta = baseline_loss - alt_loss

    # Risk reduction: normalized from propagation_reduction
    risk_reduction = recommended.propagation_reduction if recommended else 0.0

    # Confidence: based on data quality and simulation coverage
    prop_event_count = impact_map.propagation_event_count
    node_coverage = sum(1 for n in impact_map.nodes if n.stress_level > 0) / max(len(impact_map.nodes), 1)
    confidence = min(1.0, 0.5 + node_coverage * 0.3 + min(prop_event_count / 20, 0.2))

    # ── Narrative ───────────────────────────────────────────────────────────
    narrative_en, narrative_ar = _build_narrative(
        impact_map, recommended, alternative, delta_loss, delta_pct,
        time_gain, baseline_loss, baseline_breached,
    )

    result = CounterfactualResult(
        run_id=impact_map.run_id,
        scenario_id=impact_map.scenario_id,
        baseline_loss_usd=baseline_loss,
        baseline_breached_nodes=baseline_breached,
        baseline_risk_level=baseline_risk,
        action_id=recommended.action_id if recommended else "",
        action_label=recommended.action_label if recommended else "No action available",
        action_loss_usd=action_loss,
        action_breached_prevented=action_prevented,
        alt_action_id=alternative.action_id if alternative else "",
        alt_action_label=alternative.action_label if alternative else "No alternative",
        alt_loss_usd=alt_loss,
        delta_loss_usd=delta_loss,
        delta_loss_pct=delta_pct,
        risk_reduction=risk_reduction,
        time_gain_hours=time_gain,
        alt_delta_loss_usd=alt_delta,
        confidence=confidence,
        narrative_en=narrative_en,
        narrative_ar=narrative_ar,
    )

    logger.info(
        "[CounterfactualEngine] Baseline=$%.0f Action=$%.0f Delta=$%.0f (%.1f%%)",
        baseline_loss, action_loss, delta_loss, delta_pct,
    )
    return result


def _build_narrative(
    impact_map, recommended, alternative,
    delta_loss, delta_pct, time_gain,
    baseline_loss, baseline_breached,
) -> tuple[str, str]:
    """Build counterfactual narrative in EN/AR."""
    if recommended and delta_loss > 0:
        en = (
            f"Executing '{recommended.action_label}' reduces projected loss by "
            f"${delta_loss:,.0f} ({delta_pct:.1f}%), protects {recommended.nodes_protected} nodes, "
            f"and gains {time_gain:.1f}h before first breach. "
            f"Without action: ${baseline_loss:,.0f} loss, {baseline_breached} breached nodes."
        )
        ar = (
            f"تنفيذ '{recommended.action_label}' يقلل الخسارة المتوقعة بمقدار "
            f"${delta_loss:,.0f} ({delta_pct:.1f}%)، يحمي {recommended.nodes_protected} عقد، "
            f"ويكسب {time_gain:.1f} ساعة قبل أول اختراق."
        )
    else:
        en = (
            f"No effective action identified. Baseline loss: ${baseline_loss:,.0f}, "
            f"{baseline_breached} nodes breached."
        )
        ar = (
            f"لم يتم تحديد إجراء فعال. خسارة أساسية: ${baseline_loss:,.0f}، "
            f"{baseline_breached} عقد مخترقة."
        )
    return en, ar
