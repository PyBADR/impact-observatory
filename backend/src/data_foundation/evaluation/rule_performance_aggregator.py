"""
Evaluation Layer — Rule Performance Aggregator
================================================

Aggregates DecisionEvaluation + AnalystFeedbackRecord into
RulePerformanceSnapshot records for a given time window.

Pure function: (evaluations, feedbacks) → snapshot.
No DB access — callers query and pass data in.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .schemas import (
    DecisionEvaluation,
    AnalystFeedbackRecord,
    RulePerformanceSnapshot,
    AnalystVerdict,
    FailureMode,
)

__all__ = [
    "aggregate_rule_performance",
    "aggregate_all_rules",
]


def aggregate_rule_performance(
    rule_id: str,
    evaluations: List[DecisionEvaluation],
    feedbacks: List[AnalystFeedbackRecord],
    period_start: datetime,
    period_end: datetime,
    spec_id: Optional[str] = None,
) -> RulePerformanceSnapshot:
    """Aggregate evaluations and feedbacks into a performance snapshot.

    Args:
        rule_id: The rule being aggregated.
        evaluations: All DecisionEvaluations for this rule in the window.
        feedbacks: All AnalystFeedbackRecords linked to these evaluations.
        period_start: Window start.
        period_end: Window end.
        spec_id: Optional RuleSpec ID.

    Returns:
        RulePerformanceSnapshot with all counts and averages computed.
    """
    n = len(evaluations)

    if n == 0:
        snapshot = RulePerformanceSnapshot(
            rule_id=rule_id,
            spec_id=spec_id,
            period_start=period_start,
            period_end=period_end,
        )
        snapshot.compute_hash()
        return snapshot

    # ── Count triggers ─────────────────────────────────────────────────────
    # All evaluations imply the rule triggered (you only evaluate after trigger)
    total_triggered = n

    # ── Aggregate scores ───────────────────────────────────────────────────
    sum_correctness = sum(e.correctness_score for e in evaluations)
    sum_severity = sum(e.severity_alignment_score for e in evaluations)
    sum_entity = sum(e.entity_alignment_score for e in evaluations)
    sum_timing = sum(e.timing_alignment_score for e in evaluations)
    sum_confidence_gap = sum(e.confidence_gap for e in evaluations)
    sum_explainability = sum(e.explainability_completeness_score for e in evaluations)

    # ── Count verdicts from feedbacks ──────────────────────────────────────
    # Build evaluation_id → latest feedback mapping
    feedback_by_eval: Dict[str, AnalystFeedbackRecord] = {}
    for fb in sorted(feedbacks, key=lambda f: f.submitted_at):
        feedback_by_eval[fb.evaluation_id] = fb  # last wins

    confirmed_correct = 0
    confirmed_partially = 0
    confirmed_incorrect = 0
    fp_count = 0
    fn_count = 0

    for fb in feedback_by_eval.values():
        if fb.verdict == AnalystVerdict.CORRECT:
            confirmed_correct += 1
        elif fb.verdict == AnalystVerdict.PARTIALLY_CORRECT:
            confirmed_partially += 1
        elif fb.verdict == AnalystVerdict.INCORRECT:
            confirmed_incorrect += 1

        if fb.failure_mode == FailureMode.FALSE_POSITIVE:
            fp_count += 1
        elif fb.failure_mode == FailureMode.FALSE_NEGATIVE:
            fn_count += 1

    # Also count verdicts from evaluations that have analyst_verdict set
    # (analyst_verdict on DecisionEvaluation is set directly too)
    eval_ids_with_feedback = set(feedback_by_eval.keys())
    for e in evaluations:
        if e.evaluation_id not in eval_ids_with_feedback and e.analyst_verdict:
            if e.analyst_verdict == AnalystVerdict.CORRECT:
                confirmed_correct += 1
            elif e.analyst_verdict == AnalystVerdict.PARTIALLY_CORRECT:
                confirmed_partially += 1
            elif e.analyst_verdict == AnalystVerdict.INCORRECT:
                confirmed_incorrect += 1

    snapshot = RulePerformanceSnapshot(
        rule_id=rule_id,
        spec_id=spec_id,
        period_start=period_start,
        period_end=period_end,
        total_evaluations=n,
        total_triggered=total_triggered,
        confirmed_correct=confirmed_correct,
        confirmed_partially_correct=confirmed_partially,
        confirmed_incorrect=confirmed_incorrect,
        false_positive_count=fp_count,
        false_negative_count=fn_count,
        avg_correctness_score=round(sum_correctness / n, 6),
        avg_severity_alignment=round(sum_severity / n, 6),
        avg_entity_alignment=round(sum_entity / n, 6),
        avg_timing_alignment=round(sum_timing / n, 6),
        avg_confidence_gap=round(sum_confidence_gap / n, 6),
        avg_explainability_completeness=round(sum_explainability / n, 6),
    )
    snapshot.compute_hash()
    return snapshot


def aggregate_all_rules(
    evaluations_by_rule: Dict[str, List[DecisionEvaluation]],
    feedbacks_by_evaluation: Dict[str, List[AnalystFeedbackRecord]],
    period_start: datetime,
    period_end: datetime,
    spec_ids_by_rule: Optional[Dict[str, str]] = None,
) -> List[RulePerformanceSnapshot]:
    """Aggregate performance for all rules in a time window.

    Args:
        evaluations_by_rule: Dict[rule_id → List[DecisionEvaluation]].
        feedbacks_by_evaluation: Dict[evaluation_id → List[AnalystFeedbackRecord]].
        period_start: Window start.
        period_end: Window end.
        spec_ids_by_rule: Optional Dict[rule_id → spec_id].

    Returns:
        List of RulePerformanceSnapshot, one per rule.
    """
    snapshots = []

    for rule_id, evals in evaluations_by_rule.items():
        # Collect feedbacks for these evaluations
        rule_feedbacks = []
        for e in evals:
            rule_feedbacks.extend(feedbacks_by_evaluation.get(e.evaluation_id, []))

        spec_id = (spec_ids_by_rule or {}).get(rule_id)

        snapshot = aggregate_rule_performance(
            rule_id=rule_id,
            evaluations=evals,
            feedbacks=rule_feedbacks,
            period_start=period_start,
            period_end=period_end,
            spec_id=spec_id,
        )
        snapshots.append(snapshot)

    return snapshots
