"""
Evaluation Layer — ORM Table Definitions
==========================================

7 tables for outcome tracking, decision evaluation, analyst feedback,
replay, and rule performance. Mirrors schemas.py 1:1.

Follows existing P2 conventions:
  - _FoundationMixin for shared columns (schema_version, tenant_id, etc.)
  - JSONB for flexible nested data
  - VARCHAR(64) for enums (not Postgres native ENUMs)
  - Strategic composite indexes on query patterns
  - Primary keys as natural identifiers (not synthetic UUIDs)

Table naming: df_eval_* prefix to distinguish from existing df_* tables.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# Mixin: same as tables.py _FoundationMixin
# ═══════════════════════════════════════════════════════════════════════════════

class _FoundationMixin:
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    provenance_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. df_eval_expected_outcomes
# ═══════════════════════════════════════════════════════════════════════════════

class ExpectedOutcomeORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_expected_outcomes"

    expected_outcome_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    expected_severity: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_risk_level: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_affected_entity_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expected_affected_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expected_affected_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    expected_financial_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_mitigation_effect: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    data_state_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    data_state_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_eval_exout_dlog_rule", "decision_log_id", "rule_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. df_eval_actual_outcomes
# ═══════════════════════════════════════════════════════════════════════════════

class ActualOutcomeORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_actual_outcomes"

    actual_outcome_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    expected_outcome_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_log_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    actual_severity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actual_risk_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actual_affected_entity_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actual_affected_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actual_affected_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actual_financial_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    observation_source: Mapped[str] = mapped_column(String(64), nullable=False, default="ANALYST_REVIEW")
    observation_completeness: Mapped[str] = mapped_column(String(64), nullable=False, default="PRELIMINARY")
    observation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    data_sources_used: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_eval_acout_exout_completeness", "expected_outcome_id", "observation_completeness"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. df_eval_decision_evaluations
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionEvaluationORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_decision_evaluations"

    evaluation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    expected_outcome_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actual_outcome_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_log_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Scoring
    correctness_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    entity_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    timing_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    sector_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_gap: Mapped[float] = mapped_column(Float, nullable=False)
    explainability_completeness_score: Mapped[float] = mapped_column(Float, nullable=False)

    analyst_verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scoring_method_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0.0")
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_eval_de_rule_score", "rule_id", "correctness_score"),
        Index("ix_eval_de_verdict", "analyst_verdict"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. df_eval_analyst_feedback
# ═══════════════════════════════════════════════════════════════════════════════

class AnalystFeedbackORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_analyst_feedback"

    feedback_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    evaluation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_log_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    analyst_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    verdict: Mapped[str] = mapped_column(String(64), nullable=False)
    override_correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    failure_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    override_reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_eval_afbk_eval_analyst", "evaluation_id", "analyst_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. df_eval_replay_runs
# ═══════════════════════════════════════════════════════════════════════════════

class ReplayRunORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_replay_runs"

    replay_run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    original_decision_log_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    original_event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    replay_data_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    replay_data_state_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rule_set_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rule_set_source: Mapped[str] = mapped_column(String(64), nullable=False, default="CURRENT_ACTIVE")
    replay_scenario_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    initiated_by: Mapped[str] = mapped_column(String(128), nullable=False)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="RUNNING")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_eval_replay_status", "status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. df_eval_replay_results
# ═══════════════════════════════════════════════════════════════════════════════

class ReplayRunResultORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_replay_results"

    replay_result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    replay_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)

    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cooldown_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conditions_met: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    condition_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    matches_original: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    divergence_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_eval_rres_run_rule", "replay_run_id", "rule_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. df_eval_rule_performance
# ═══════════════════════════════════════════════════════════════════════════════

class RulePerformanceORM(_FoundationMixin, Base):
    __tablename__ = "df_eval_rule_performance"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    total_evaluations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_triggered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_partially_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_incorrect: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_positive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    false_negative_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    avg_correctness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_severity_alignment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_entity_alignment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_timing_alignment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_confidence_gap: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_explainability_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_eval_rperf_rule_period", "rule_id", "period_start", "period_end"),
    )
