"""
Decision Trust Pipeline — Stage 80 orchestrator.

Chains all 6 trust engines in order:
  1. ScenarioEnforcementEngine — resolve/enforce taxonomy (runs FIRST)
  2. ActionValidationEngine    — structural action validation
  3. AuthorityRealismEngine    — country-level governance realism
  4. ExplainabilityEngine      — causal explanations
  5. LearningClosureEngine     — feedback loop signals
  6. TrustOverrideEngine       — final safety gate (runs LAST)

Consumed by: run_orchestrator.py (Stage 80 block)
Input: Stage 60 decisions + Stage 70 calibration outputs + impact_map + scenario context
Output: TrustLayerResult
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.pipeline import DecisionQualityResult
from src.decision_calibration.pipeline import CalibrationLayerResult
from src.schemas.impact_map import ImpactMapResponse

from src.decision_trust.scenario_enforcement_engine import ScenarioValidation, enforce_scenario_taxonomy
from src.decision_trust.validation_engine import ValidationResult, validate_actions
from src.decision_trust.authority_realism_engine import AuthorityProfile, refine_authority_realism
from src.decision_trust.explainability_engine import DecisionExplanation, explain_decisions
from src.decision_trust.learning_closure_engine import LearningUpdate, compute_learning_updates
from src.decision_trust.trust_override_engine import OverrideResult, apply_trust_overrides

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TrustLayerResult:
    """Aggregated result from the Stage 80 trust pipeline."""
    scenario_validation: ScenarioValidation | None = None
    validation_results: list[ValidationResult] = field(default_factory=list)
    authority_profiles: list[AuthorityProfile] = field(default_factory=list)
    explanations: list[DecisionExplanation] = field(default_factory=list)
    learning_updates: list[LearningUpdate] = field(default_factory=list)
    override_results: list[OverrideResult] = field(default_factory=list)

    # Timing
    stage_timings: dict[str, float] = field(default_factory=dict)
    total_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_validation": self.scenario_validation.to_dict() if self.scenario_validation else {},
            "validation_results": [v.to_dict() for v in self.validation_results],
            "authority_profiles": [a.to_dict() for a in self.authority_profiles],
            "explanations": [e.to_dict() for e in self.explanations],
            "learning_updates": [l.to_dict() for l in self.learning_updates],
            "override_results": [o.to_dict() for o in self.override_results],
            "stage_timings": {k: round(v, 4) for k, v in self.stage_timings.items()},
            "total_time_ms": round(self.total_time_ms, 4),
            "counts": {
                "validated": len(self.validation_results),
                "valid": sum(1 for v in self.validation_results if v.validation_status == "VALID"),
                "conditionally_valid": sum(1 for v in self.validation_results if v.validation_status == "CONDITIONALLY_VALID"),
                "rejected": sum(1 for v in self.validation_results if v.validation_status == "REJECTED"),
                "authorities_refined": len(self.authority_profiles),
                "explanations_generated": len(self.explanations),
                "learning_updates": len(self.learning_updates),
                "blocked": sum(1 for o in self.override_results if o.final_status == "BLOCKED"),
                "human_required": sum(1 for o in self.override_results if o.final_status == "HUMAN_REQUIRED"),
                "conditional": sum(1 for o in self.override_results if o.final_status == "CONDITIONAL"),
                "auto_executable": sum(1 for o in self.override_results if o.final_status == "AUTO_EXECUTABLE"),
                "taxonomy_valid": self.scenario_validation.taxonomy_valid if self.scenario_validation else False,
                "taxonomy_confidence": self.scenario_validation.classification_confidence if self.scenario_validation else 0.0,
            },
        }


def run_trust_pipeline(
    dq_result: DecisionQualityResult,
    cal_result: CalibrationLayerResult,
    impact_map: ImpactMapResponse,
    scenario_id: str,
    action_registry_lookup: dict[str, dict[str, Any]],
    scenario_catalog_entry: dict[str, Any] | None = None,
) -> TrustLayerResult:
    """
    Run the full Stage 80 trust pipeline.

    Args:
        dq_result:              DecisionQualityResult from Stage 60.
        cal_result:             CalibrationLayerResult from Stage 70.
        impact_map:             ImpactMapResponse for context.
        scenario_id:            Current scenario ID.
        action_registry_lookup: dict[action_id → ActionTemplate dict].
        scenario_catalog_entry: Optional SCENARIO_CATALOG dict for fallback inference.

    Returns:
        TrustLayerResult — all 6 engine outputs + timing.
    """
    result = TrustLayerResult()
    pipeline_start = time.perf_counter()

    decisions = dq_result.executive_decisions
    if not decisions:
        result.total_time_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.info("[TrustPipeline] No decisions to process — returning empty result")
        return result

    # ── Step 1: Scenario Enforcement (FIRST — resolves type for all others) ──
    t0 = time.perf_counter()
    result.scenario_validation = enforce_scenario_taxonomy(
        scenario_id, scenario_catalog_entry,
    )
    result.stage_timings["scenario_enforcement"] = (time.perf_counter() - t0) * 1000
    resolved_type = result.scenario_validation.scenario_type

    # ── Step 2: Action Validation ─────────────────────────────────────────
    t0 = time.perf_counter()
    result.validation_results = validate_actions(
        decisions, impact_map, scenario_id, action_registry_lookup,
    )
    result.stage_timings["validation"] = (time.perf_counter() - t0) * 1000

    # ── Step 3: Authority Realism ─────────────────────────────────────────
    t0 = time.perf_counter()
    result.authority_profiles = refine_authority_realism(
        decisions, cal_result.authority_assignments,
        scenario_id, resolved_type,
    )
    result.stage_timings["authority_realism"] = (time.perf_counter() - t0) * 1000

    # ── Step 4: Explainability ────────────────────────────────────────────
    t0 = time.perf_counter()
    result.explanations = explain_decisions(
        decisions, impact_map, result.validation_results,
        cal_result.ranked_decisions, result.scenario_validation,
    )
    result.stage_timings["explainability"] = (time.perf_counter() - t0) * 1000

    # ── Step 5: Learning Closure ──────────────────────────────────────────
    t0 = time.perf_counter()
    result.learning_updates = compute_learning_updates(
        decisions, cal_result.calibration_results,
        cal_result.audit_results, cal_result.ranked_decisions,
    )
    result.stage_timings["learning_closure"] = (time.perf_counter() - t0) * 1000

    # ── Step 6: Trust Override (LAST — final safety gate) ─────────────────
    t0 = time.perf_counter()
    result.override_results = apply_trust_overrides(
        decisions, result.validation_results,
        cal_result.trust_results, cal_result.calibration_results,
        result.learning_updates, result.scenario_validation,
        cal_result.authority_assignments,
    )
    result.stage_timings["trust_override"] = (time.perf_counter() - t0) * 1000

    result.total_time_ms = (time.perf_counter() - pipeline_start) * 1000

    logger.info(
        "[TrustPipeline] Stage 80 complete in %.2fms: "
        "%d validated, %d explained, %d overrides (%d blocked, %d auto)",
        result.total_time_ms,
        len(result.validation_results),
        len(result.explanations),
        len(result.override_results),
        sum(1 for o in result.override_results if o.final_status == "BLOCKED"),
        sum(1 for o in result.override_results if o.final_status == "AUTO_EXECUTABLE"),
    )
    return result
