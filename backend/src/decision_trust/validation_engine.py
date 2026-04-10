"""
Action Validation Engine — structural correctness verification.

Validates every action against 4 dimensions:
  1. scenario_valid — action's allowed_scenario_types includes current scenario type
  2. sector_valid — action sector matches sectors affected by scenario
  3. node_coverage_valid — action targets nodes that are stressed in the impact map
  4. operational_feasibility — action is executable given regime + timing constraints

Validation status:
  VALID              — all 4 checks pass
  CONDITIONALLY_VALID — minor issues (sector mismatch, low coverage)
  REJECTED           — category error or operationally infeasible

Differences from Stage 70 AuditEngine:
  - AuditEngine computes soft SCORES for ranking
  - ValidationEngine computes hard PASS/FAIL gates for blocking

Consumed by: Stage 80 pipeline
Input: decisions + impact_map + scenario_id + action_registry
Output: list[ValidationResult]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.schemas.impact_map import ImpactMapResponse
from src.config import SCENARIO_TAXONOMY

logger = logging.getLogger(__name__)

# ── Scenario type → required operational sectors ──────────────────────────

_SCENARIO_REQUIRED_SECTORS: dict[str, set[str]] = {
    "MARITIME":    {"maritime", "logistics"},
    "ENERGY":      {"energy"},
    "LIQUIDITY":   {"banking", "fintech"},
    "CYBER":       {"fintech", "infrastructure", "banking"},
    "REGULATORY":  {"government"},
}

# ── Scenario type → all valid action sectors ──────────────────────────────

_SCENARIO_VALID_SECTORS: dict[str, set[str]] = {
    "MARITIME":    {"maritime", "logistics", "insurance", "government", "energy"},
    "ENERGY":      {"energy", "maritime", "logistics", "government", "insurance", "banking"},
    "LIQUIDITY":   {"banking", "insurance", "fintech", "government"},
    "CYBER":       {"fintech", "infrastructure", "banking", "government", "insurance"},
    "REGULATORY":  {"government", "banking", "insurance", "energy", "maritime"},
}

# ── Feasibility hard-fail thresholds ──────────────────────────────────────

_MIN_FEASIBILITY: float = 0.30
_MAX_TIME_TO_ACT_HOURS: float = 168.0  # 7 days


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Structural validation result for a single decision."""
    decision_id: str
    action_id: str

    # Dimension pass/fail
    scenario_valid: bool
    sector_valid: bool
    node_coverage_valid: bool
    operational_feasibility: bool

    # Category error detection
    category_error_flag: bool

    # Final verdict
    validation_status: str              # "VALID" | "CONDITIONALLY_VALID" | "REJECTED"
    validation_status_ar: str

    # Rejection/condition reasons
    rejection_reasons: list[dict[str, str]] = field(default_factory=list)

    # Metadata
    scenario_type_resolved: str = ""
    affected_node_count: int = 0
    covered_node_count: int = 0
    coverage_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "scenario_valid": self.scenario_valid,
            "sector_valid": self.sector_valid,
            "node_coverage_valid": self.node_coverage_valid,
            "operational_feasibility": self.operational_feasibility,
            "category_error_flag": self.category_error_flag,
            "validation_status": self.validation_status,
            "validation_status_ar": self.validation_status_ar,
            "rejection_reasons": self.rejection_reasons,
            "scenario_type_resolved": self.scenario_type_resolved,
            "affected_node_count": self.affected_node_count,
            "covered_node_count": self.covered_node_count,
            "coverage_ratio": round(self.coverage_ratio, 4),
        }


def validate_actions(
    decisions: list[FormattedExecutiveDecision],
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
) -> list[ValidationResult]:
    """
    Validate every decision's action against structural correctness rules.

    Args:
        decisions:              FormattedExecutiveDecision list from Stage 60.
        impact_map:             ImpactMapResponse for node stress context.
        scenario_id:            Current scenario ID.
        action_registry_lookup: dict[action_id → ActionTemplate dict].

    Returns:
        list[ValidationResult] — one per decision with VALID/CONDITIONALLY_VALID/REJECTED.
    """
    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "")

    # Build stressed node → sector map from impact map
    stressed_sectors: set[str] = set()
    stressed_node_ids: set[str] = set()
    for node in impact_map.nodes:
        if node.stress_level > 0.10:
            stressed_sectors.add(node.sector)
            stressed_node_ids.add(node.id)

    results: list[ValidationResult] = []

    for dec in decisions:
        meta = action_registry_lookup.get(dec.action_id, {})
        reasons: list[dict[str, str]] = []

        # ── 1. Scenario validity ─────────────────────────────────────────
        allowed_types = meta.get("allowed_scenario_types", set())
        if isinstance(allowed_types, list):
            allowed_types = set(allowed_types)
        scenario_valid = bool(scenario_type and scenario_type in allowed_types)

        category_error = not scenario_valid and bool(scenario_type)
        if category_error:
            reasons.append({
                "code": "CATEGORY_ERROR",
                "reason_en": f"Action {dec.action_id} not allowed for scenario type {scenario_type}",
                "reason_ar": f"الإجراء {dec.action_id} غير مسموح لنوع السيناريو {scenario_type}",
                "severity": "critical",
            })

        # ── 2. Sector validity ───────────────────────────────────────────
        valid_sectors = _SCENARIO_VALID_SECTORS.get(scenario_type, set())
        sector_valid = dec.sector in valid_sectors if valid_sectors else True

        if not sector_valid:
            reasons.append({
                "code": "SECTOR_MISMATCH",
                "reason_en": f"Action sector '{dec.sector}' not aligned with {scenario_type} scenario",
                "reason_ar": f"قطاع الإجراء '{dec.sector}' لا يتوافق مع سيناريو {scenario_type}",
                "severity": "warning",
            })

        # ── 3. Node coverage ─────────────────────────────────────────────
        # Check how many stressed nodes the action's sector covers
        sector_stressed_nodes = {n.id for n in impact_map.nodes
                                 if n.sector == dec.sector and n.stress_level > 0.10}
        affected_count = len(stressed_node_ids)
        covered_count = len(sector_stressed_nodes)
        coverage_ratio = covered_count / max(1, affected_count)

        node_coverage_valid = coverage_ratio > 0.0 or not stressed_node_ids
        if not node_coverage_valid:
            reasons.append({
                "code": "NO_NODE_COVERAGE",
                "reason_en": f"Action sector '{dec.sector}' has no stressed nodes in impact map",
                "reason_ar": f"قطاع الإجراء '{dec.sector}' لا يحتوي على عقد متأثرة في خريطة التأثير",
                "severity": "warning",
            })

        # ── 4. Operational feasibility ───────────────────────────────────
        feasibility = meta.get("feasibility", 0.70)
        time_to_act = meta.get("time_to_act_hours", 24)
        operational_feasibility = (
            feasibility >= _MIN_FEASIBILITY
            and time_to_act <= _MAX_TIME_TO_ACT_HOURS
        )

        if feasibility < _MIN_FEASIBILITY:
            reasons.append({
                "code": "LOW_FEASIBILITY",
                "reason_en": f"Action feasibility ({feasibility:.2f}) below threshold ({_MIN_FEASIBILITY})",
                "reason_ar": f"جدوى الإجراء ({feasibility:.2f}) أقل من الحد ({_MIN_FEASIBILITY})",
                "severity": "critical",
            })
        if time_to_act > _MAX_TIME_TO_ACT_HOURS:
            reasons.append({
                "code": "EXCEEDS_TIME_WINDOW",
                "reason_en": f"Time to act ({time_to_act}h) exceeds maximum ({_MAX_TIME_TO_ACT_HOURS}h)",
                "reason_ar": f"وقت التنفيذ ({time_to_act} ساعة) يتجاوز الحد ({_MAX_TIME_TO_ACT_HOURS} ساعة)",
                "severity": "warning",
            })

        # ── Final verdict ────────────────────────────────────────────────
        status, status_ar = _compute_verdict(
            scenario_valid, sector_valid, node_coverage_valid,
            operational_feasibility, category_error,
        )

        results.append(ValidationResult(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            scenario_valid=scenario_valid,
            sector_valid=sector_valid,
            node_coverage_valid=node_coverage_valid,
            operational_feasibility=operational_feasibility,
            category_error_flag=category_error,
            validation_status=status,
            validation_status_ar=status_ar,
            rejection_reasons=reasons,
            scenario_type_resolved=scenario_type,
            affected_node_count=affected_count,
            covered_node_count=covered_count,
            coverage_ratio=coverage_ratio,
        ))

    valid_count = sum(1 for r in results if r.validation_status == "VALID")
    rejected_count = sum(1 for r in results if r.validation_status == "REJECTED")
    logger.info(
        "[ValidationEngine] Validated %d actions: %d VALID, %d CONDITIONAL, %d REJECTED",
        len(results), valid_count, len(results) - valid_count - rejected_count, rejected_count,
    )
    return results


def _compute_verdict(
    scenario_valid: bool,
    sector_valid: bool,
    node_coverage_valid: bool,
    operational_feasibility: bool,
    category_error: bool,
) -> tuple[str, str]:
    """Compute final validation verdict."""
    # Category error → REJECTED
    if category_error:
        return "REJECTED", "مرفوض"

    # Operationally infeasible → REJECTED
    if not operational_feasibility:
        return "REJECTED", "مرفوض"

    # All pass → VALID
    if scenario_valid and sector_valid and node_coverage_valid:
        return "VALID", "صالح"

    # Partial pass → CONDITIONALLY_VALID
    return "CONDITIONALLY_VALID", "صالح مشروط"
