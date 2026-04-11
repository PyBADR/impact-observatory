"""Rule Performance Service — compute aggregated rule accuracy snapshots.

Gathers data from:
  - Decision evaluations (correctness scores, confidence gaps)
  - Analyst feedback (verdicts: CORRECT, INCORRECT, etc.)
  - Replay results (for delta detection)

Produces a RulePerformanceSnapshot per rule at a given point in time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.models.outcome_tables import (
    RulePerformanceSnapshotORM,
)
from src.data_foundation.repositories.evaluation_repo import EvaluationRepository
from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
from src.data_foundation.repositories.feedback_repo import FeedbackRepository
from src.data_foundation.repositories.rule_performance_repo import RulePerformanceRepository
from src.data_foundation.schemas.outcome_schemas import RulePerformanceSnapshot


def _uuid() -> str:
    return str(uuid4())


class RulePerformanceService:
    """Computes and persists rule performance snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.perf_repo = RulePerformanceRepository(session)
        self.eval_repo = EvaluationRepository(session)
        self.expected_repo = ExpectedOutcomeRepository(session)
        self.feedback_repo = FeedbackRepository(session)

    async def compute_snapshot(
        self,
        rule_id: str,
        snapshot_date: datetime,
    ) -> RulePerformanceSnapshot:
        """Compute a performance snapshot for a rule from all available evaluations and feedback.

        Algorithm:
          1. Find all evaluations linked to this rule (via expected outcomes)
          2. Count match/correct/false-positive/false-negative from analyst verdicts
          3. Average correctness scores and confidence gaps
          4. Persist snapshot
        """
        # Get all evaluations for this rule
        evaluations = await self.eval_repo.find_by_rule(rule_id, limit=10000)

        match_count = len(evaluations)
        confirmed_correct = 0
        false_positive = 0
        false_negative = 0
        total_correctness = 0.0
        total_confidence_gap = 0.0

        for ev in evaluations:
            total_correctness += ev.correctness_score
            total_confidence_gap += ev.confidence_gap

            verdict = ev.analyst_verdict
            if verdict == "CORRECT":
                confirmed_correct += 1
            elif verdict == "INCORRECT":
                # Check feedback for failure mode to distinguish FP vs FN
                feedbacks = await self.feedback_repo.find_by_evaluation(ev.evaluation_id)
                is_false_positive = any(
                    f.failure_mode == "FALSE_POSITIVE" for f in feedbacks
                )
                if is_false_positive:
                    false_positive += 1
                else:
                    false_negative += 1
            elif verdict == "PARTIALLY_CORRECT":
                # Count as partial correct — doesn't increment FP or FN
                confirmed_correct += 1

        # Also check feedback records that override evaluations
        all_expected = await self.expected_repo.find_by_rule(rule_id, limit=10000)
        for eo in all_expected:
            feedbacks = await self.feedback_repo.find_by_decision_log(eo.decision_log_id)
            for fb in feedbacks:
                if fb.evaluation_id is None:
                    # Feedback without evaluation — standalone analyst override
                    match_count += 1
                    if fb.verdict == "CORRECT" or fb.verdict == "PARTIALLY_CORRECT":
                        confirmed_correct += 1
                    elif fb.verdict == "INCORRECT":
                        if fb.failure_mode == "FALSE_POSITIVE":
                            false_positive += 1
                        else:
                            false_negative += 1

        avg_correctness = total_correctness / match_count if match_count > 0 else 0.0
        avg_gap = total_confidence_gap / match_count if match_count > 0 else 0.0

        snapshot_id = f"SNAP-{_uuid()[:12]}"
        orm = RulePerformanceSnapshotORM(
            snapshot_id=snapshot_id,
            rule_id=rule_id,
            snapshot_date=snapshot_date,
            match_count=match_count,
            confirmed_correct_count=confirmed_correct,
            false_positive_count=false_positive,
            false_negative_count=false_negative,
            average_correctness_score=round(avg_correctness, 4),
            average_confidence_gap=round(avg_gap, 4),
        )
        created = await self.perf_repo.create(orm)
        return RulePerformanceSnapshot.model_validate(created)

    async def get_latest_snapshot(self, rule_id: str) -> RulePerformanceSnapshot | None:
        orm = await self.perf_repo.get_latest_for_rule(rule_id)
        if orm is None:
            return None
        return RulePerformanceSnapshot.model_validate(orm)
