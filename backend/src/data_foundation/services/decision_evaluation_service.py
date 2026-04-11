"""Decision Evaluation Service — deterministic scoring of decision quality.

Scoring functions:
  1. severity_alignment_score   — expected vs observed severity
  2. entity_alignment_score     — Jaccard similarity of entity sets
  3. timing_alignment_score     — expected horizon vs actual materialization
  4. confidence_gap             — confidence_at_decision_time - correctness_score
  5. correctness_score          — weighted combination of alignment scores
  6. explainability_completeness_score — presence of audit trail components

All weights are explicit constants defined at module level.
No ML. No hidden logic. Fully deterministic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.models.outcome_tables import (
    DecisionEvaluationORM,
    DecisionExpectedOutcomeORM,
    DecisionActualOutcomeORM,
)
from src.data_foundation.repositories.evaluation_repo import EvaluationRepository
from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
from src.data_foundation.repositories.actual_outcome_repo import ActualOutcomeRepository
from src.data_foundation.schemas.outcome_schemas import (
    DecisionEvaluation,
    EvaluationScores,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring weights — explicit, documented, deterministic
# ═══════════════════════════════════════════════════════════════════════════════

# Correctness score is a weighted average of these components:
WEIGHT_SEVERITY: float = 0.30      # Severity prediction matters most
WEIGHT_ENTITY: float = 0.25        # Getting affected entities right
WEIGHT_TIMING: float = 0.20        # Timing accuracy
WEIGHT_DIRECTION: float = 0.25     # Direction (DETERIORATE/IMPROVE/STABLE) match

# Severity distance map — ordinal distance between severity levels
SEVERITY_ORDER: dict[str, int] = {
    "NOMINAL": 0,
    "LOW": 1,
    "GUARDED": 2,
    "ELEVATED": 3,
    "HIGH": 4,
    "SEVERE": 5,
}
MAX_SEVERITY_DISTANCE: int = 5  # NOMINAL → SEVERE

# Timing tolerance: within 2x of expected is full credit, 4x is partial
TIMING_FULL_CREDIT_RATIO: float = 2.0
TIMING_ZERO_CREDIT_RATIO: float = 4.0

# Explainability checklist fields and their weights (must sum to 1.0)
EXPLAINABILITY_FIELDS: dict[str, float] = {
    "matched_rules": 0.25,
    "source_signals": 0.25,
    "rationale": 0.20,
    "affected_entities": 0.20,
    "limitations": 0.10,
}


def _uuid() -> str:
    return str(uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# Pure scoring functions (no I/O, fully testable)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_severity_alignment(expected_severity: str, observed_severity: str) -> float:
    """Score 0.0–1.0 based on ordinal distance between severity levels.

    Same severity = 1.0. Adjacent = 0.8. Max distance = 0.0.
    """
    exp_ord = SEVERITY_ORDER.get(expected_severity, 3)  # default ELEVATED
    obs_ord = SEVERITY_ORDER.get(observed_severity, 3)
    distance = abs(exp_ord - obs_ord)
    return max(0.0, 1.0 - (distance / MAX_SEVERITY_DISTANCE))


def compute_entity_alignment(expected_entities: list[str], observed_entities: list[str]) -> float:
    """Jaccard similarity between expected and observed entity sets.

    |intersection| / |union|. Empty sets on both sides = 1.0.
    """
    exp_set = set(expected_entities)
    obs_set = set(observed_entities)
    if not exp_set and not obs_set:
        return 1.0
    if not exp_set or not obs_set:
        return 0.0
    intersection = exp_set & obs_set
    union = exp_set | obs_set
    return len(intersection) / len(union)


def compute_timing_alignment(
    expected_hours: float | None,
    actual_hours: float | None,
) -> float:
    """Score 0.0–1.0 based on ratio of actual to expected time.

    - Both None → 1.0 (no timing claim, no penalty)
    - One None → 0.5 (incomplete data, neutral)
    - Within 2x → 1.0 (full credit)
    - Between 2x and 4x → linear decay
    - Beyond 4x → 0.0
    """
    if expected_hours is None and actual_hours is None:
        return 1.0
    if expected_hours is None or actual_hours is None:
        return 0.5
    if expected_hours <= 0.0:
        return 1.0 if actual_hours <= 1.0 else 0.0

    ratio = actual_hours / expected_hours
    # Both too-fast and too-slow degrade the score
    deviation = abs(ratio - 1.0)
    # Full credit within tolerance band
    if deviation <= (TIMING_FULL_CREDIT_RATIO - 1.0):
        return 1.0
    # Linear decay from full credit to zero
    max_deviation = TIMING_ZERO_CREDIT_RATIO - 1.0
    if deviation >= max_deviation:
        return 0.0
    return 1.0 - ((deviation - (TIMING_FULL_CREDIT_RATIO - 1.0)) / (max_deviation - (TIMING_FULL_CREDIT_RATIO - 1.0)))


def compute_direction_alignment(expected_direction: str, observed_direction: str) -> float:
    """Score: 1.0 if match, 0.5 if one is STABLE, 0.0 if opposite."""
    if expected_direction == observed_direction:
        return 1.0
    if expected_direction == "STABLE" or observed_direction == "STABLE":
        return 0.5
    # DETERIORATE vs IMPROVE = 0.0
    return 0.0


def compute_correctness(
    severity_score: float,
    entity_score: float,
    timing_score: float,
    direction_score: float,
) -> float:
    """Weighted combination of alignment scores.

    Weights:
      severity  = 0.30
      entity    = 0.25
      timing    = 0.20
      direction = 0.25
    Total = 1.00
    """
    return (
        WEIGHT_SEVERITY * severity_score
        + WEIGHT_ENTITY * entity_score
        + WEIGHT_TIMING * timing_score
        + WEIGHT_DIRECTION * direction_score
    )


def compute_confidence_gap(confidence_at_decision: float, correctness_score: float) -> float:
    """Difference: confidence - correctness.

    Positive = overconfident (predicted better than reality).
    Negative = underconfident (reality was better than predicted).
    Zero = calibrated.
    """
    return confidence_at_decision - correctness_score


def compute_explainability_completeness(
    decision_log: dict | None,
) -> float:
    """Score 0.0–1.0 based on presence of audit trail components.

    Checks for presence of:
      - matched_rules (or rule_id)        → 0.25
      - source_signals (signal_ids)       → 0.25
      - rationale (review_notes)          → 0.20
      - affected_entities (entity_ids)    → 0.20
      - limitations (execution_result)    → 0.10
    """
    if decision_log is None:
        return 0.0

    score = 0.0

    # matched_rules
    if decision_log.get("rule_id") or decision_log.get("matched_rule_ids"):
        score += EXPLAINABILITY_FIELDS["matched_rules"]

    # source_signals
    trigger = decision_log.get("trigger_context", {})
    if isinstance(trigger, dict) and trigger.get("signal_ids"):
        score += EXPLAINABILITY_FIELDS["source_signals"]

    # rationale
    if decision_log.get("review_notes") or decision_log.get("rationale"):
        score += EXPLAINABILITY_FIELDS["rationale"]

    # affected_entities
    if decision_log.get("entity_ids"):
        score += EXPLAINABILITY_FIELDS["affected_entities"]

    # limitations / exclusions
    if decision_log.get("execution_result") or decision_log.get("limitations"):
        score += EXPLAINABILITY_FIELDS["limitations"]

    return min(score, 1.0)


def evaluate_decision(
    expected: DecisionExpectedOutcomeORM,
    actual: DecisionActualOutcomeORM,
    decision_log: dict | None = None,
) -> EvaluationScores:
    """Compute all evaluation scores from expected + actual outcome ORM objects.

    Returns an EvaluationScores schema with all 6 scores.
    """
    expected_entities = expected.expected_entities or []
    observed_entities = actual.observed_entities or []

    severity_score = compute_severity_alignment(expected.expected_severity, actual.observed_severity)
    entity_score = compute_entity_alignment(expected_entities, observed_entities)
    timing_score = compute_timing_alignment(
        expected.expected_time_horizon_hours,
        actual.observed_time_to_materialization_hours,
    )
    direction_score = compute_direction_alignment(expected.expected_direction, actual.observed_direction)
    correctness = compute_correctness(severity_score, entity_score, timing_score, direction_score)
    gap = compute_confidence_gap(expected.confidence_at_decision_time, correctness)
    explainability = compute_explainability_completeness(decision_log)

    return EvaluationScores(
        correctness_score=round(correctness, 4),
        severity_alignment_score=round(severity_score, 4),
        entity_alignment_score=round(entity_score, 4),
        timing_alignment_score=round(timing_score, 4),
        confidence_gap=round(gap, 4),
        explainability_completeness_score=round(explainability, 4),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Service class (with I/O — uses repos)
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionEvaluationService:
    """Orchestrates evaluation of decision quality using expected + actual outcomes."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.eval_repo = EvaluationRepository(session)
        self.expected_repo = ExpectedOutcomeRepository(session)
        self.actual_repo = ActualOutcomeRepository(session)

    async def run_evaluation(
        self,
        decision_log_id: str,
        expected_outcome_id: str,
        actual_outcome_id: str,
        decision_log_dict: dict | None = None,
    ) -> DecisionEvaluation:
        """Load expected + actual, compute scores, persist evaluation."""
        expected = await self.expected_repo.get_by_pk(expected_outcome_id)
        if expected is None:
            raise ValueError(f"Expected outcome not found: {expected_outcome_id}")

        actual = await self.actual_repo.get_by_pk(actual_outcome_id)
        if actual is None:
            raise ValueError(f"Actual outcome not found: {actual_outcome_id}")

        scores = evaluate_decision(expected, actual, decision_log_dict)

        eval_id = f"EVAL-{_uuid()[:12]}"
        now = datetime.now(timezone.utc)

        orm = DecisionEvaluationORM(
            evaluation_id=eval_id,
            decision_log_id=decision_log_id,
            expected_outcome_id=expected_outcome_id,
            actual_outcome_id=actual_outcome_id,
            correctness_score=scores.correctness_score,
            severity_alignment_score=scores.severity_alignment_score,
            entity_alignment_score=scores.entity_alignment_score,
            timing_alignment_score=scores.timing_alignment_score,
            confidence_gap=scores.confidence_gap,
            explainability_completeness_score=scores.explainability_completeness_score,
            evaluation_status="COMPLETED",
            evaluated_at=now,
        )
        created = await self.eval_repo.create(orm)
        return DecisionEvaluation.model_validate(created)

    async def get_evaluation(self, evaluation_id: str) -> DecisionEvaluation | None:
        orm = await self.eval_repo.get_by_pk(evaluation_id)
        if orm is None:
            return None
        return DecisionEvaluation.model_validate(orm)
