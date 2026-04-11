"""Governance & Calibration Layer — SQLAlchemy ORM table definitions.

Seven tables (df_gov_* prefix):

  df_gov_policies                 — governance meta-rules
  df_gov_rule_lifecycle_events    — rule spec status transitions
  df_gov_truth_validation_policies — what constitutes truth per dataset
  df_gov_truth_validation_results — validation output records
  df_gov_calibration_triggers     — recalibration conditions
  df_gov_calibration_events       — fired calibration records
  df_gov_audit_entries            — SHA-256 hash-chained audit trail

Design:
  - Same _FoundationMixin as all df_* tables
  - JSONB for flexible nested data (policy_params, validation_rules, detail)
  - VARCHAR enums (no Postgres native ENUMs)
  - String PKs (128-char max)
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
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
# Table: df_gov_policies
# ═══════════════════════════════════════════════════════════════════════════════

class GovernancePolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_policies"

    policy_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_risk_levels: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    scope_actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    scope_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    scope_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    policy_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    effective_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    authored_by: Mapped[str] = mapped_column(String(256), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(256), nullable=True)

    __table_args__ = (
        Index("ix_df_gov_pol_type_active", "policy_type", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_rule_lifecycle_events
# ═══════════════════════════════════════════════════════════════════════════════

class RuleLifecycleEventORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_rule_lifecycle_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    spec_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    transition_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    validation_result_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    policy_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    previous_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_df_gov_rle_spec_occurred", "spec_id", "occurred_at"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_truth_validation_policies
# ═══════════════════════════════════════════════════════════════════════════════

class TruthValidationPolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_truth_validation_policies"

    policy_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    target_dataset: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_priority_order: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    freshness_max_hours: Mapped[float] = mapped_column(Float, default=24.0, nullable=False)
    completeness_min_fields: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    corroboration_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corroboration_min_sources: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    deviation_max_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[Dict]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    authored_by: Mapped[str] = mapped_column(String(256), nullable=False)

    __table_args__ = (
        Index("ix_df_gov_tvp_dataset_active", "target_dataset", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_truth_validation_results
# ═══════════════════════════════════════════════════════════════════════════════

class TruthValidationResultORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_truth_validation_results"

    result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_dataset: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    freshness_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    completeness_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    corroboration_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    field_checks_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    field_checks_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[Dict]
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("ix_df_gov_tvr_policy_valid", "policy_id", "is_valid"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_calibration_triggers
# ═══════════════════════════════════════════════════════════════════════════════

class CalibrationTriggerORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_calibration_triggers"

    trigger_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    trigger_name: Mapped[str] = mapped_column(String(256), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_metric: Mapped[str] = mapped_column(String(128), nullable=False)
    threshold_operator: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    lookback_window_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    min_evaluations: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    authored_by: Mapped[str] = mapped_column(String(256), nullable=False)

    __table_args__ = (
        Index("ix_df_gov_ct_type_active", "trigger_type", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_calibration_events
# ═══════════════════════════════════════════════════════════════════════════════

class CalibrationEventORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_calibration_events"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    trigger_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    lookback_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lookback_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="TRIGGERED", nullable=False, index=True)
    resolved_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_df_gov_ce_rule_status", "rule_id", "status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_gov_audit_entries
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceAuditEntryORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_audit_entries"

    entry_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    previous_audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_df_gov_audit_subject", "subject_type", "subject_id"),
        Index("ix_df_gov_audit_type_occurred", "event_type", "occurred_at"),
    )
