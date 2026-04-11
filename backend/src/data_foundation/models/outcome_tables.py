"""Outcome Tracking, Decision Evaluation & Replay — ORM table definitions.

Seven new tables that close the decision feedback loop:

  df_decision_expected_outcomes  — what the rule/decision predicted would happen
  df_decision_actual_outcomes    — what actually happened (observed post-decision)
  df_decision_evaluations        — deterministic scoring of prediction quality
  df_analyst_feedback            — human analyst verdict and failure-mode annotation
  df_replay_runs                 — replay session metadata (re-run historical event)
  df_replay_run_results          — per-event output from a replay run
  df_rule_performance_snapshots  — periodic aggregated rule accuracy metrics

Design:
  - Same _FoundationMixin as all df_* tables (schema_version, tenant_id, timestamps, provenance_hash)
  - JSONB for entity lists, decision snapshots, confidence summaries
  - VARCHAR enums (no Postgres native ENUMs)
  - String PKs (UUID-based, 128-char max)
  - Foreign keys to df_decision_logs, df_decision_rules, df_event_signals
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
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


class _FoundationMixin:
    """Columns present on every data_foundation table."""
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    provenance_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_decision_expected_outcomes
# What the decision rule predicted would happen
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionExpectedOutcomeORM(_FoundationMixin, Base):
    __tablename__ = "df_decision_expected_outcomes"

    expected_outcome_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Prediction fields
    expected_entities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    expected_severity: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_direction: Mapped[str] = mapped_column(String(32), nullable=False)  # DETERIORATE | IMPROVE | STABLE
    expected_time_horizon_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_mitigation_effect: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0–1.0
    expected_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_at_decision_time: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    __table_args__ = (
        Index("ix_df_eo_dlog_rule", "decision_log_id", "rule_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_decision_actual_outcomes
# What was actually observed post-decision
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionActualOutcomeORM(_FoundationMixin, Base):
    __tablename__ = "df_decision_actual_outcomes"

    actual_outcome_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    expected_outcome_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    # Observed fields
    observed_entities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    observed_severity: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_direction: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_time_to_materialization_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_effect_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    observation_source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    observation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_df_ao_expected", "expected_outcome_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_decision_evaluations
# Deterministic scoring of decision quality
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionEvaluationORM(_FoundationMixin, Base):
    __tablename__ = "df_decision_evaluations"

    evaluation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    expected_outcome_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actual_outcome_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Scores (all 0.0–1.0)
    correctness_score: Mapped[float] = mapped_column(Float, nullable=False)
    severity_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    entity_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    timing_alignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_gap: Mapped[float] = mapped_column(Float, nullable=False)
    explainability_completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    # Verdict
    analyst_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)  # CORRECT | PARTIALLY_CORRECT | INCORRECT | INCONCLUSIVE
    evaluation_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_df_eval_dlog", "decision_log_id"),
        Index("ix_df_eval_status_score", "evaluation_status", "correctness_score"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_analyst_feedback
# Human analyst verdicts and failure-mode annotation
# ═══════════════════════════════════════════════════════════════════════════════

class AnalystFeedbackRecordORM(_FoundationMixin, Base):
    __tablename__ = "df_analyst_feedback"

    feedback_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    evaluation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    analyst_name: Mapped[str] = mapped_column(String(256), nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)  # CORRECT | PARTIALLY_CORRECT | INCORRECT | INCONCLUSIVE
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)  # MISSED_SIGNAL | WRONG_SEVERITY | WRONG_ENTITY | TIMING_OFF | RULE_GAP | FALSE_POSITIVE | OTHER
    feedback_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_df_fb_dlog", "decision_log_id"),
        Index("ix_df_fb_verdict", "verdict"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_replay_runs
# Replay session metadata — re-running historical events through current rules
# ═══════════════════════════════════════════════════════════════════════════════

class ReplayRunORM(_FoundationMixin, Base):
    __tablename__ = "df_replay_runs"

    replay_run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_event_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    replay_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(256), nullable=False)
    replay_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replay_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)  # PENDING | RUNNING | COMPLETED | FAILED

    __table_args__ = (
        Index("ix_df_replay_event_status", "source_event_id", "replay_status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_replay_run_results
# Per-event output from a replay run
# ═══════════════════════════════════════════════════════════════════════════════

class ReplayRunResultORM(_FoundationMixin, Base):
    __tablename__ = "df_replay_run_results"

    replay_result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    replay_run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    matched_rule_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    replayed_entities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    replayed_decisions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[dict] — decision snapshots
    replayed_confidence_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {rule_id: confidence}
    actual_outcome_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evaluation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_df_rr_run_event", "replay_run_id", "event_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_rule_performance_snapshots
# Periodic aggregated rule accuracy metrics
# ═══════════════════════════════════════════════════════════════════════════════

class RulePerformanceSnapshotORM(_FoundationMixin, Base):
    __tablename__ = "df_rule_performance_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # Counts
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirmed_correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    false_positive_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    false_negative_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Averages
    average_correctness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_confidence_gap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    __table_args__ = (
        Index("ix_df_rps_rule_date", "rule_id", "snapshot_date"),
    )
