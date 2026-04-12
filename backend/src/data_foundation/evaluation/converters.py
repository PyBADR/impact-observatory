"""
Evaluation Layer — Pydantic ↔ ORM Converters
==============================================

14 functions: to_orm and from_orm for each of the 7 domain models.
Follows the same pattern as models/converters.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from src.data_foundation.schemas.enums import RiskLevel, SignalSeverity

from .schemas import (
    ExpectedOutcome,
    ActualOutcome,
    DecisionEvaluation,
    AnalystFeedbackRecord,
    ReplayRun,
    ReplayRunResult,
    RulePerformanceSnapshot,
)
from .orm_models import (
    ExpectedOutcomeORM,
    ActualOutcomeORM,
    DecisionEvaluationORM,
    AnalystFeedbackORM,
    ReplayRunORM,
    ReplayRunResultORM,
    RulePerformanceORM,
)


def _enum_val(v) -> Optional[str]:
    return v.value if hasattr(v, "value") else v


def _to_severity(v: Optional[str]) -> Optional[SignalSeverity]:
    if v is None:
        return None
    return SignalSeverity(v)


def _to_risk_level(v: Optional[str]) -> Optional[RiskLevel]:
    if v is None:
        return None
    return RiskLevel(v)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ExpectedOutcome
# ═══════════════════════════════════════════════════════════════════════════════

def expected_outcome_to_orm(e: ExpectedOutcome) -> ExpectedOutcomeORM:
    return ExpectedOutcomeORM(
        expected_outcome_id=e.expected_outcome_id,
        decision_log_id=e.decision_log_id,
        rule_id=e.rule_id,
        spec_id=e.spec_id,
        expected_severity=_enum_val(e.expected_severity),
        expected_risk_level=_enum_val(e.expected_risk_level),
        expected_affected_entity_ids=e.expected_affected_entity_ids,
        expected_affected_sectors=e.expected_affected_sectors,
        expected_affected_countries=e.expected_affected_countries,
        expected_financial_impact=e.expected_financial_impact,
        expected_mitigation_effect=e.expected_mitigation_effect,
        expected_resolution_hours=e.expected_resolution_hours,
        data_state_snapshot=e.data_state_snapshot,
        data_state_hash=e.data_state_hash,
        created_at=e.created_at,
        provenance_hash=e.provenance_hash,
    )


def expected_outcome_from_orm(row: ExpectedOutcomeORM) -> ExpectedOutcome:
    return ExpectedOutcome(
        expected_outcome_id=row.expected_outcome_id,
        decision_log_id=row.decision_log_id,
        rule_id=row.rule_id,
        spec_id=row.spec_id,
        expected_severity=SignalSeverity(row.expected_severity),
        expected_risk_level=RiskLevel(row.expected_risk_level),
        expected_affected_entity_ids=row.expected_affected_entity_ids or [],
        expected_affected_sectors=row.expected_affected_sectors or [],
        expected_affected_countries=row.expected_affected_countries or [],
        expected_financial_impact=row.expected_financial_impact,
        expected_mitigation_effect=row.expected_mitigation_effect,
        expected_resolution_hours=row.expected_resolution_hours,
        data_state_snapshot=row.data_state_snapshot or {},
        data_state_hash=row.data_state_hash or "",
        created_at=row.created_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ActualOutcome
# ═══════════════════════════════════════════════════════════════════════════════

def actual_outcome_to_orm(a: ActualOutcome) -> ActualOutcomeORM:
    return ActualOutcomeORM(
        actual_outcome_id=a.actual_outcome_id,
        expected_outcome_id=a.expected_outcome_id,
        decision_log_id=a.decision_log_id,
        actual_severity=_enum_val(a.actual_severity) if a.actual_severity else None,
        actual_risk_level=_enum_val(a.actual_risk_level) if a.actual_risk_level else None,
        actual_affected_entity_ids=a.actual_affected_entity_ids,
        actual_affected_sectors=a.actual_affected_sectors,
        actual_affected_countries=a.actual_affected_countries,
        actual_financial_impact=a.actual_financial_impact,
        actual_resolution_hours=a.actual_resolution_hours,
        observation_source=a.observation_source,
        observation_completeness=a.observation_completeness,
        observation_notes=a.observation_notes,
        observed_at=a.observed_at,
        data_sources_used=a.data_sources_used,
        provenance_hash=a.provenance_hash,
    )


def actual_outcome_from_orm(row: ActualOutcomeORM) -> ActualOutcome:
    return ActualOutcome(
        actual_outcome_id=row.actual_outcome_id,
        expected_outcome_id=row.expected_outcome_id,
        decision_log_id=row.decision_log_id,
        actual_severity=_to_severity(row.actual_severity),
        actual_risk_level=_to_risk_level(row.actual_risk_level),
        actual_affected_entity_ids=row.actual_affected_entity_ids or [],
        actual_affected_sectors=row.actual_affected_sectors or [],
        actual_affected_countries=row.actual_affected_countries or [],
        actual_financial_impact=row.actual_financial_impact,
        actual_resolution_hours=row.actual_resolution_hours,
        observation_source=row.observation_source,
        observation_completeness=row.observation_completeness,
        observation_notes=row.observation_notes,
        observed_at=row.observed_at,
        data_sources_used=row.data_sources_used or [],
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DecisionEvaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluation_to_orm(e: DecisionEvaluation) -> DecisionEvaluationORM:
    return DecisionEvaluationORM(
        evaluation_id=e.evaluation_id,
        expected_outcome_id=e.expected_outcome_id,
        actual_outcome_id=e.actual_outcome_id,
        decision_log_id=e.decision_log_id,
        rule_id=e.rule_id,
        spec_id=e.spec_id,
        correctness_score=e.correctness_score,
        severity_alignment_score=e.severity_alignment_score,
        entity_alignment_score=e.entity_alignment_score,
        timing_alignment_score=e.timing_alignment_score,
        sector_alignment_score=e.sector_alignment_score,
        confidence_gap=e.confidence_gap,
        explainability_completeness_score=e.explainability_completeness_score,
        analyst_verdict=e.analyst_verdict,
        scoring_method_version=e.scoring_method_version,
        evaluated_at=e.evaluated_at,
        provenance_hash=e.provenance_hash,
    )


def evaluation_from_orm(row: DecisionEvaluationORM) -> DecisionEvaluation:
    return DecisionEvaluation(
        evaluation_id=row.evaluation_id,
        expected_outcome_id=row.expected_outcome_id,
        actual_outcome_id=row.actual_outcome_id,
        decision_log_id=row.decision_log_id,
        rule_id=row.rule_id,
        spec_id=row.spec_id,
        correctness_score=row.correctness_score,
        severity_alignment_score=row.severity_alignment_score,
        entity_alignment_score=row.entity_alignment_score,
        timing_alignment_score=row.timing_alignment_score,
        sector_alignment_score=row.sector_alignment_score,
        confidence_gap=row.confidence_gap,
        explainability_completeness_score=row.explainability_completeness_score,
        analyst_verdict=row.analyst_verdict,
        scoring_method_version=row.scoring_method_version,
        evaluated_at=row.evaluated_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AnalystFeedbackRecord
# ═══════════════════════════════════════════════════════════════════════════════

def feedback_to_orm(f: AnalystFeedbackRecord) -> AnalystFeedbackORM:
    return AnalystFeedbackORM(
        feedback_id=f.feedback_id,
        evaluation_id=f.evaluation_id,
        decision_log_id=f.decision_log_id,
        analyst_id=f.analyst_id,
        verdict=f.verdict,
        override_correctness_score=f.override_correctness_score,
        failure_mode=f.failure_mode,
        override_reason=f.override_reason,
        recommendations=f.recommendations,
        submitted_at=f.submitted_at,
        provenance_hash=f.provenance_hash,
    )


def feedback_from_orm(row: AnalystFeedbackORM) -> AnalystFeedbackRecord:
    return AnalystFeedbackRecord(
        feedback_id=row.feedback_id,
        evaluation_id=row.evaluation_id,
        decision_log_id=row.decision_log_id,
        analyst_id=row.analyst_id,
        verdict=row.verdict,
        override_correctness_score=row.override_correctness_score,
        failure_mode=row.failure_mode,
        override_reason=row.override_reason,
        recommendations=row.recommendations,
        submitted_at=row.submitted_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ReplayRun
# ═══════════════════════════════════════════════════════════════════════════════

def replay_run_to_orm(r: ReplayRun) -> ReplayRunORM:
    return ReplayRunORM(
        replay_run_id=r.replay_run_id,
        original_decision_log_id=r.original_decision_log_id,
        original_event_id=r.original_event_id,
        replay_data_state=r.replay_data_state,
        replay_data_state_hash=r.replay_data_state_hash,
        rule_set_snapshot=r.rule_set_snapshot,
        rule_set_source=r.rule_set_source,
        replay_scenario_id=r.replay_scenario_id,
        initiated_by=r.initiated_by,
        initiated_at=r.initiated_at,
        completed_at=r.completed_at,
        status=r.status,
        error_message=r.error_message,
        provenance_hash=r.provenance_hash,
    )


def replay_run_from_orm(row: ReplayRunORM) -> ReplayRun:
    return ReplayRun(
        replay_run_id=row.replay_run_id,
        original_decision_log_id=row.original_decision_log_id,
        original_event_id=row.original_event_id,
        replay_data_state=row.replay_data_state or {},
        replay_data_state_hash=row.replay_data_state_hash or "",
        rule_set_snapshot=row.rule_set_snapshot or {},
        rule_set_source=row.rule_set_source,
        replay_scenario_id=row.replay_scenario_id,
        initiated_by=row.initiated_by,
        initiated_at=row.initiated_at,
        completed_at=row.completed_at,
        status=row.status,
        error_message=row.error_message,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ReplayRunResult
# ═══════════════════════════════════════════════════════════════════════════════

def replay_result_to_orm(r: ReplayRunResult) -> ReplayRunResultORM:
    return ReplayRunResultORM(
        replay_result_id=r.replay_result_id,
        replay_run_id=r.replay_run_id,
        rule_id=r.rule_id,
        rule_version=r.rule_version,
        triggered=r.triggered,
        cooldown_blocked=r.cooldown_blocked,
        action=r.action,
        conditions_met=r.conditions_met,
        condition_details=r.condition_details,
        matches_original=r.matches_original,
        divergence_reason=r.divergence_reason,
        provenance_hash=r.provenance_hash,
    )


def replay_result_from_orm(row: ReplayRunResultORM) -> ReplayRunResult:
    return ReplayRunResult(
        replay_result_id=row.replay_result_id,
        replay_run_id=row.replay_run_id,
        rule_id=row.rule_id,
        rule_version=row.rule_version,
        triggered=row.triggered,
        cooldown_blocked=row.cooldown_blocked,
        action=row.action,
        conditions_met=row.conditions_met or [],
        condition_details=row.condition_details or [],
        matches_original=row.matches_original,
        divergence_reason=row.divergence_reason,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. RulePerformanceSnapshot
# ═══════════════════════════════════════════════════════════════════════════════

def performance_to_orm(p: RulePerformanceSnapshot) -> RulePerformanceORM:
    return RulePerformanceORM(
        snapshot_id=p.snapshot_id,
        rule_id=p.rule_id,
        spec_id=p.spec_id,
        period_start=p.period_start,
        period_end=p.period_end,
        total_evaluations=p.total_evaluations,
        total_triggered=p.total_triggered,
        confirmed_correct=p.confirmed_correct,
        confirmed_partially_correct=p.confirmed_partially_correct,
        confirmed_incorrect=p.confirmed_incorrect,
        false_positive_count=p.false_positive_count,
        false_negative_count=p.false_negative_count,
        avg_correctness_score=p.avg_correctness_score,
        avg_severity_alignment=p.avg_severity_alignment,
        avg_entity_alignment=p.avg_entity_alignment,
        avg_timing_alignment=p.avg_timing_alignment,
        avg_confidence_gap=p.avg_confidence_gap,
        avg_explainability_completeness=p.avg_explainability_completeness,
        computed_at=p.computed_at,
        provenance_hash=p.provenance_hash,
    )


def performance_from_orm(row: RulePerformanceORM) -> RulePerformanceSnapshot:
    return RulePerformanceSnapshot(
        snapshot_id=row.snapshot_id,
        rule_id=row.rule_id,
        spec_id=row.spec_id,
        period_start=row.period_start,
        period_end=row.period_end,
        total_evaluations=row.total_evaluations,
        total_triggered=row.total_triggered,
        confirmed_correct=row.confirmed_correct,
        confirmed_partially_correct=row.confirmed_partially_correct,
        confirmed_incorrect=row.confirmed_incorrect,
        false_positive_count=row.false_positive_count,
        false_negative_count=row.false_negative_count,
        avg_correctness_score=row.avg_correctness_score,
        avg_severity_alignment=row.avg_severity_alignment,
        avg_entity_alignment=row.avg_entity_alignment,
        avg_timing_alignment=row.avg_timing_alignment,
        avg_confidence_gap=row.avg_confidence_gap,
        avg_explainability_completeness=row.avg_explainability_completeness,
        computed_at=row.computed_at,
        provenance_hash=row.provenance_hash or "",
    )
