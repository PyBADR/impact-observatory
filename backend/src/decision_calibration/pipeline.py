"""
Decision Quality Calibration Pipeline — Stage 70 orchestrator.

Chains all 5 calibration engines in order:
  1. AuditEngine      — contextual correctness validation
  2. RankingEngine     — multi-factor re-ranking
  3. AuthorityEngine   — GCC-realistic authority assignment
  4. CalibrationEngine — outcome prediction calibration
  5. TrustEngine       — institutional trust scoring

Consumed by: run_orchestrator.py (Stage 70 block)
Input: DecisionQualityResult (Stage 60) + ImpactMapResponse + scenario_id + action_registry
Output: CalibrationLayerResult
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.pipeline import DecisionQualityResult
from src.schemas.impact_map import ImpactMapResponse
from src.config import SCENARIO_TAXONOMY

from src.decision_calibration.audit_engine import ActionAuditResult, audit_decision_quality
from src.decision_calibration.ranking_engine import RankedDecision, rank_decisions
from src.decision_calibration.authority_engine import AuthorityAssignment, assign_authorities
from src.decision_calibration.calibration_engine import CalibrationResult, calibrate_outcomes
from src.decision_calibration.trust_engine import TrustResult, compute_trust_scores

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CalibrationLayerResult:
    """Aggregated result from the Stage 70 calibration pipeline."""
    audit_results: list[ActionAuditResult] = field(default_factory=list)
    ranked_decisions: list[RankedDecision] = field(default_factory=list)
    authority_assignments: list[AuthorityAssignment] = field(default_factory=list)
    calibration_results: list[CalibrationResult] = field(default_factory=list)
    trust_results: list[TrustResult] = field(default_factory=list)

    # Timing
    stage_timings: dict[str, float] = field(default_factory=dict)
    total_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_results": [a.to_dict() for a in self.audit_results],
            "ranked_decisions": [r.to_dict() for r in self.ranked_decisions],
            "authority_assignments": [a.to_dict() for a in self.authority_assignments],
            "calibration_results": [c.to_dict() for c in self.calibration_results],
            "trust_results": [t.to_dict() for t in self.trust_results],
            "stage_timings": {k: round(v, 4) for k, v in self.stage_timings.items()},
            "total_time_ms": round(self.total_time_ms, 4),
            "counts": {
                "audited": len(self.audit_results),
                "ranked": len(self.ranked_decisions),
                "authorities_assigned": len(self.authority_assignments),
                "calibrated": len(self.calibration_results),
                "trust_scored": len(self.trust_results),
                "category_errors": sum(1 for a in self.audit_results if a.category_error_flag),
                "high_trust": sum(1 for t in self.trust_results if t.trust_level == "HIGH"),
                "medium_trust": sum(1 for t in self.trust_results if t.trust_level == "MEDIUM"),
                "low_trust": sum(1 for t in self.trust_results if t.trust_level == "LOW"),
                "blocked": sum(1 for t in self.trust_results if t.execution_mode == "BLOCKED"),
                "auto_executable": sum(1 for t in self.trust_results if t.execution_mode == "AUTO_EXECUTABLE"),
            },
        }


def run_calibration_pipeline(
    dq_result: DecisionQualityResult,
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
) -> CalibrationLayerResult:
    """
    Run the full Stage 70 calibration pipeline.

    Args:
        dq_result:              DecisionQualityResult from Stage 60.
        impact_map:             ImpactMapResponse for contextual validation.
        scenario_id:            Current scenario ID.
        action_registry_lookup: dict[action_id → ActionTemplate dict].

    Returns:
        CalibrationLayerResult — all 5 engine outputs + timing.
    """
    result = CalibrationLayerResult()
    pipeline_start = time.perf_counter()

    decisions = dq_result.executive_decisions
    if not decisions:
        result.total_time_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.info("[CalibrationPipeline] No decisions to calibrate — returning empty result")
        return result

    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "")
    regime_amplifier = impact_map.regime.propagation_amplifier

    # ── Step 1: Audit ─────────────────────────────────────────────────────
    t0 = time.perf_counter()
    result.audit_results = audit_decision_quality(
        decisions, impact_map, scenario_id, action_registry_lookup,
    )
    result.stage_timings["audit"] = (time.perf_counter() - t0) * 1000

    # ── Step 2: Ranking ───────────────────────────────────────────────────
    t0 = time.perf_counter()
    result.ranked_decisions = rank_decisions(
        decisions, result.audit_results, regime_amplifier, action_registry_lookup,
    )
    result.stage_timings["ranking"] = (time.perf_counter() - t0) * 1000

    # ── Step 3: Authority ─────────────────────────────────────────────────
    t0 = time.perf_counter()
    result.authority_assignments = assign_authorities(decisions, scenario_type)
    result.stage_timings["authority"] = (time.perf_counter() - t0) * 1000

    # ── Step 4: Calibration ───────────────────────────────────────────────
    t0 = time.perf_counter()
    result.calibration_results = calibrate_outcomes(
        decisions, result.audit_results, result.ranked_decisions,
    )
    result.stage_timings["calibration"] = (time.perf_counter() - t0) * 1000

    # ── Step 5: Trust ─────────────────────────────────────────────────────
    t0 = time.perf_counter()
    result.trust_results = compute_trust_scores(
        decisions, result.audit_results, result.ranked_decisions,
        result.calibration_results, result.authority_assignments,
    )
    result.stage_timings["trust"] = (time.perf_counter() - t0) * 1000

    result.total_time_ms = (time.perf_counter() - pipeline_start) * 1000

    logger.info(
        "[CalibrationPipeline] Stage 70 complete in %.2fms: "
        "%d audited, %d ranked, %d authorities, %d calibrated, %d trust-scored",
        result.total_time_ms,
        len(result.audit_results),
        len(result.ranked_decisions),
        len(result.authority_assignments),
        len(result.calibration_results),
        len(result.trust_results),
    )
    return result
