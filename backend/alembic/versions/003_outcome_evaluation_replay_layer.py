"""Outcome Tracking, Decision Evaluation & Replay — 7 new tables.

df_decision_expected_outcomes, df_decision_actual_outcomes,
df_decision_evaluations, df_analyst_feedback,
df_replay_runs, df_replay_run_results, df_rule_performance_snapshots.

Revision ID: 003_outcome_eval_replay
Revises: 002_data_reality
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_outcome_eval_replay"
down_revision: Union[str, None] = "002_data_reality"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _foundation_cols():
    """Columns shared by every df_ table (mirrors FoundationModel)."""
    return [
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("tenant_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("provenance_hash", sa.String(128), nullable=True),
    ]


def upgrade() -> None:
    # ── df_decision_expected_outcomes ────────────────────────────────────
    op.create_table(
        "df_decision_expected_outcomes",
        sa.Column("expected_outcome_id", sa.String(128), primary_key=True),
        sa.Column("decision_log_id", sa.String(128), nullable=False, index=True),
        sa.Column("event_id", sa.String(128), nullable=True, index=True),
        sa.Column("rule_id", sa.String(128), nullable=False, index=True),
        sa.Column("expected_entities", postgresql.JSONB(), nullable=True),
        sa.Column("expected_severity", sa.String(32), nullable=False),
        sa.Column("expected_direction", sa.String(32), nullable=False),
        sa.Column("expected_time_horizon_hours", sa.Float(), nullable=True),
        sa.Column("expected_mitigation_effect", sa.Float(), nullable=True),
        sa.Column("expected_notes", sa.Text(), nullable=True),
        sa.Column("confidence_at_decision_time", sa.Float(), nullable=False, server_default="0.5"),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_eo_dlog_rule",
        "df_decision_expected_outcomes",
        ["decision_log_id", "rule_id"],
    )

    # ── df_decision_actual_outcomes ─────────────────────────────────────
    op.create_table(
        "df_decision_actual_outcomes",
        sa.Column("actual_outcome_id", sa.String(128), primary_key=True),
        sa.Column("expected_outcome_id", sa.String(128), nullable=False, index=True),
        sa.Column("event_id", sa.String(128), nullable=True, index=True),
        sa.Column("observed_entities", postgresql.JSONB(), nullable=True),
        sa.Column("observed_severity", sa.String(32), nullable=False),
        sa.Column("observed_direction", sa.String(32), nullable=False),
        sa.Column("observed_time_to_materialization_hours", sa.Float(), nullable=True),
        sa.Column("actual_effect_value", sa.Float(), nullable=True),
        sa.Column("observation_source", sa.String(256), nullable=True),
        sa.Column("observation_notes", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_ao_expected",
        "df_decision_actual_outcomes",
        ["expected_outcome_id"],
    )

    # ── df_decision_evaluations ─────────────────────────────────────────
    op.create_table(
        "df_decision_evaluations",
        sa.Column("evaluation_id", sa.String(128), primary_key=True),
        sa.Column("decision_log_id", sa.String(128), nullable=False, index=True),
        sa.Column("expected_outcome_id", sa.String(128), nullable=False, index=True),
        sa.Column("actual_outcome_id", sa.String(128), nullable=False, index=True),
        sa.Column("correctness_score", sa.Float(), nullable=False),
        sa.Column("severity_alignment_score", sa.Float(), nullable=False),
        sa.Column("entity_alignment_score", sa.Float(), nullable=False),
        sa.Column("timing_alignment_score", sa.Float(), nullable=False),
        sa.Column("confidence_gap", sa.Float(), nullable=False),
        sa.Column("explainability_completeness_score", sa.Float(), nullable=False),
        sa.Column("analyst_verdict", sa.String(32), nullable=True),
        sa.Column("evaluation_status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_eval_dlog",
        "df_decision_evaluations",
        ["decision_log_id"],
    )
    op.create_index(
        "ix_df_eval_status_score",
        "df_decision_evaluations",
        ["evaluation_status", "correctness_score"],
    )

    # ── df_analyst_feedback ─────────────────────────────────────────────
    op.create_table(
        "df_analyst_feedback",
        sa.Column("feedback_id", sa.String(128), primary_key=True),
        sa.Column("decision_log_id", sa.String(128), nullable=False, index=True),
        sa.Column("evaluation_id", sa.String(128), nullable=True, index=True),
        sa.Column("analyst_name", sa.String(256), nullable=False),
        sa.Column("verdict", sa.String(32), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("failure_mode", sa.String(64), nullable=True),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_fb_dlog", "df_analyst_feedback", ["decision_log_id"])
    op.create_index("ix_df_fb_verdict", "df_analyst_feedback", ["verdict"])

    # ── df_replay_runs ──────────────────────────────────────────────────
    op.create_table(
        "df_replay_runs",
        sa.Column("replay_run_id", sa.String(128), primary_key=True),
        sa.Column("source_event_id", sa.String(128), nullable=False, index=True),
        sa.Column("replay_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("initiated_by", sa.String(256), nullable=False),
        sa.Column("replay_reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replay_status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_replay_event_status",
        "df_replay_runs",
        ["source_event_id", "replay_status"],
    )

    # ── df_replay_run_results ───────────────────────────────────────────
    op.create_table(
        "df_replay_run_results",
        sa.Column("replay_result_id", sa.String(128), primary_key=True),
        sa.Column("replay_run_id", sa.String(128), nullable=False, index=True),
        sa.Column("event_id", sa.String(128), nullable=False, index=True),
        sa.Column("matched_rule_ids", postgresql.JSONB(), nullable=True),
        sa.Column("replayed_entities", postgresql.JSONB(), nullable=True),
        sa.Column("replayed_decisions", postgresql.JSONB(), nullable=True),
        sa.Column("replayed_confidence_summary", postgresql.JSONB(), nullable=True),
        sa.Column("actual_outcome_id", sa.String(128), nullable=True),
        sa.Column("evaluation_id", sa.String(128), nullable=True),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_rr_run_event",
        "df_replay_run_results",
        ["replay_run_id", "event_id"],
    )

    # ── df_rule_performance_snapshots ───────────────────────────────────
    op.create_table(
        "df_rule_performance_snapshots",
        sa.Column("snapshot_id", sa.String(128), primary_key=True),
        sa.Column("rule_id", sa.String(128), nullable=False, index=True),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("false_positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("false_negative_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_correctness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("average_confidence_gap", sa.Float(), nullable=False, server_default="0.0"),
        *_foundation_cols(),
    )
    op.create_index(
        "ix_df_rps_rule_date",
        "df_rule_performance_snapshots",
        ["rule_id", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_table("df_rule_performance_snapshots")
    op.drop_table("df_replay_run_results")
    op.drop_table("df_replay_runs")
    op.drop_table("df_analyst_feedback")
    op.drop_table("df_decision_evaluations")
    op.drop_table("df_decision_actual_outcomes")
    op.drop_table("df_decision_expected_outcomes")
