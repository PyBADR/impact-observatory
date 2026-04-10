"""
Action Quality Audit Engine — validates contextual correctness of decisions.

Validates that each decision is appropriate for:
  - scenario type (MARITIME action on MARITIME scenario)
  - affected sectors (action sector matches impacted nodes)
  - propagation pattern (action targets propagation sources)
  - regime state (action doesn't contradict regime)

Rules:
  - Wrong scenario type → category_error_flag = true
  - Action doesn't affect impacted nodes → penalize
  - Action contradicts regime → penalize

Output: list[ActionAuditResult] with adjusted action_quality_score
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.schemas.impact_map import ImpactMapResponse
from src.config import SCENARIO_TAXONOMY

logger = logging.getLogger(__name__)

# ── Scenario type → allowed action sectors ─────────────────────────────────

_SCENARIO_SECTOR_ALIGNMENT: dict[str, set[str]] = {
    "MARITIME":    {"maritime", "logistics", "insurance", "government"},
    "ENERGY":      {"energy", "maritime", "logistics", "government", "insurance"},
    "LIQUIDITY":   {"banking", "insurance", "fintech", "government"},
    "CYBER":       {"fintech", "infrastructure", "banking", "government"},
    "REGULATORY":  {"government", "banking", "insurance", "energy"},
}

# ── Sector → propagation relevance weight ──────────────────────────────────

_SECTOR_PROPAGATION_WEIGHT: dict[str, float] = {
    "maritime":       0.90,
    "energy":         0.85,
    "banking":        0.80,
    "logistics":      0.75,
    "insurance":      0.65,
    "fintech":        0.60,
    "infrastructure": 0.55,
    "government":     0.50,
    "healthcare":     0.30,
}


@dataclass(frozen=True, slots=True)
class ActionAuditResult:
    """Quality audit result for a single decision."""
    decision_id: str
    action_id: str

    # Scores [0-1]
    scenario_match_score: float       # does action match scenario type?
    sector_alignment_score: float     # does action sector match impacted sectors?
    propagation_relevance_score: float  # does action target propagation sources?
    regime_consistency_score: float    # does action align with current regime?

    # Composite
    action_quality_score: float       # weighted composite of above

    # Flags
    category_error_flag: bool         # true if action is wrong for this scenario
    category_error_reason: str
    category_error_reason_ar: str

    # Notes
    audit_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "scenario_match_score": round(self.scenario_match_score, 4),
            "sector_alignment_score": round(self.sector_alignment_score, 4),
            "propagation_relevance_score": round(self.propagation_relevance_score, 4),
            "regime_consistency_score": round(self.regime_consistency_score, 4),
            "action_quality_score": round(self.action_quality_score, 4),
            "category_error_flag": self.category_error_flag,
            "category_error_reason": self.category_error_reason,
            "category_error_reason_ar": self.category_error_reason_ar,
            "audit_notes": self.audit_notes,
        }


def audit_decision_quality(
    decisions: list[FormattedExecutiveDecision],
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
) -> list[ActionAuditResult]:
    """
    Audit each decision for contextual correctness.

    Args:
        decisions:               FormattedExecutiveDecision list from Stage 60.
        impact_map:              ImpactMapResponse for node/edge context.
        scenario_id:             Current scenario ID.
        action_registry_lookup:  dict[action_id → ActionTemplate dict].

    Returns:
        list[ActionAuditResult] — one per decision.
    """
    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "")
    impacted_sectors = _get_impacted_sectors(impact_map)
    high_stress_nodes = _get_high_stress_node_ids(impact_map)
    regime_amplifier = impact_map.regime.propagation_amplifier

    results: list[ActionAuditResult] = []

    for dec in decisions:
        meta = action_registry_lookup.get(dec.action_id, {})
        action_sector = dec.sector or meta.get("sector", "")
        allowed_types = meta.get("allowed_scenario_types", set())
        # TypedDict with set — handle both set and list
        if isinstance(allowed_types, list):
            allowed_types = set(allowed_types)

        notes: list[dict[str, str]] = []

        # ── 1. Scenario match ─────────────────────────────────────────────
        scenario_match = _score_scenario_match(
            scenario_type, allowed_types, action_sector, notes,
        )

        # ── 2. Sector alignment ───────────────────────────────────────────
        sector_alignment = _score_sector_alignment(
            action_sector, impacted_sectors, notes,
        )

        # ── 3. Propagation relevance ──────────────────────────────────────
        propagation_relevance = _score_propagation_relevance(
            dec, impact_map, high_stress_nodes, notes,
        )

        # ── 4. Regime consistency ─────────────────────────────────────────
        regime_consistency = _score_regime_consistency(
            dec, regime_amplifier, notes,
        )

        # ── Category error detection ──────────────────────────────────────
        category_error = False
        error_reason = ""
        error_reason_ar = ""

        if scenario_type and scenario_type not in allowed_types and allowed_types:
            category_error = True
            error_reason = (
                f"Action {dec.action_id} ({action_sector}) is scoped to "
                f"{sorted(allowed_types)} but scenario is {scenario_type}"
            )
            error_reason_ar = (
                f"الإجراء {dec.action_id} ({action_sector}) مخصص لـ "
                f"{sorted(allowed_types)} لكن السيناريو هو {scenario_type}"
            )
            notes.append({
                "type": "CATEGORY_ERROR",
                "message_en": error_reason,
                "message_ar": error_reason_ar,
                "severity": "critical",
            })

        # ── Composite score ───────────────────────────────────────────────
        # Weights: scenario=0.35, sector=0.25, propagation=0.25, regime=0.15
        quality = (
            0.35 * scenario_match
            + 0.25 * sector_alignment
            + 0.25 * propagation_relevance
            + 0.15 * regime_consistency
        )

        # Category error hard penalty: cap at 0.30
        if category_error:
            quality = min(quality, 0.30)

        results.append(ActionAuditResult(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            scenario_match_score=scenario_match,
            sector_alignment_score=sector_alignment,
            propagation_relevance_score=propagation_relevance,
            regime_consistency_score=regime_consistency,
            action_quality_score=quality,
            category_error_flag=category_error,
            category_error_reason=error_reason,
            category_error_reason_ar=error_reason_ar,
            audit_notes=notes,
        ))

    logger.info(
        "[AuditEngine] Audited %d decisions: %d category errors",
        len(results), sum(1 for r in results if r.category_error_flag),
    )
    return results


# ── Scoring helpers ────────────────────────────────────────────────────────

def _score_scenario_match(
    scenario_type: str,
    allowed_types: set[str],
    action_sector: str,
    notes: list[dict[str, str]],
) -> float:
    """Score how well the action matches the scenario type."""
    if not scenario_type:
        # Unknown scenario type — give benefit of the doubt
        return 0.70

    if scenario_type in allowed_types:
        return 1.0

    if not allowed_types:
        # Cross-type action — moderate match
        return 0.60

    # Check sector alignment as fallback
    aligned_sectors = _SCENARIO_SECTOR_ALIGNMENT.get(scenario_type, set())
    if action_sector in aligned_sectors:
        notes.append({
            "type": "PARTIAL_MATCH",
            "message_en": f"Action not explicitly for {scenario_type} but sector {action_sector} is aligned",
            "message_ar": f"الإجراء ليس صريحاً لـ {scenario_type} لكن القطاع {action_sector} متوافق",
            "severity": "info",
        })
        return 0.50

    return 0.15


def _score_sector_alignment(
    action_sector: str,
    impacted_sectors: dict[str, float],
    notes: list[dict[str, str]],
) -> float:
    """Score how well the action sector matches impacted sectors."""
    if not impacted_sectors:
        return 0.50

    if action_sector in impacted_sectors:
        # Direct match — score proportional to sector's stress level
        stress = impacted_sectors[action_sector]
        score = min(1.0, 0.5 + stress * 0.5)
        return score

    # Action doesn't directly target an impacted sector
    notes.append({
        "type": "SECTOR_MISMATCH",
        "message_en": f"Action sector '{action_sector}' not in impacted sectors: {sorted(impacted_sectors.keys())}",
        "message_ar": f"قطاع الإجراء '{action_sector}' ليس ضمن القطاعات المتأثرة",
        "severity": "warning",
    })
    return 0.25


def _score_propagation_relevance(
    dec: FormattedExecutiveDecision,
    impact_map: ImpactMapResponse,
    high_stress_nodes: set[str],
    notes: list[dict[str, str]],
) -> float:
    """Score how well the action targets propagation sources."""
    if not impact_map.propagation_events:
        return 0.50

    # Check if action's sector has propagation relevance
    sector_weight = _SECTOR_PROPAGATION_WEIGHT.get(dec.sector, 0.40)

    # Check if there are high-stress nodes in the action's sector
    sector_nodes = {
        n.id for n in impact_map.nodes
        if n.sector == dec.sector and n.id in high_stress_nodes
    }

    if sector_nodes:
        # Action targets high-stress nodes in its sector
        node_ratio = min(1.0, len(sector_nodes) / 5)
        return min(1.0, sector_weight * 0.6 + node_ratio * 0.4)

    return sector_weight * 0.5


def _score_regime_consistency(
    dec: FormattedExecutiveDecision,
    regime_amplifier: float,
    notes: list[dict[str, str]],
) -> float:
    """Score whether the action is consistent with the current regime."""
    # In crisis regimes (amplifier > 1.3), fast-acting decisions are preferred
    if regime_amplifier > 1.3:
        # Emergency actions are regime-consistent
        if dec.decision_type == "emergency":
            return 1.0
        if dec.decision_type == "operational":
            return 0.75
        # Strategic decisions are slow in a crisis
        notes.append({
            "type": "REGIME_MISMATCH",
            "message_en": "Strategic action in escalated regime — may be too slow",
            "message_ar": "إجراء استراتيجي في نظام متصاعد — قد يكون بطيئاً جداً",
            "severity": "warning",
        })
        return 0.40

    # Stable regime — all types are fine
    return 0.85


# ── Data extraction helpers ────────────────────────────────────────────────

def _get_impacted_sectors(impact_map: ImpactMapResponse) -> dict[str, float]:
    """Extract sectors with non-trivial stress from impact map."""
    sectors: dict[str, float] = {}
    for node in impact_map.nodes:
        if node.stress_level > 0.10:
            if node.sector not in sectors or node.stress_level > sectors[node.sector]:
                sectors[node.sector] = node.stress_level
    return sectors


def _get_high_stress_node_ids(impact_map: ImpactMapResponse) -> set[str]:
    """Get IDs of nodes with stress ≥ 0.40."""
    return {n.id for n in impact_map.nodes if n.stress_level >= 0.40}
