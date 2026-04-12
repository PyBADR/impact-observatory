"""
Governance Layer — ORM Table Definitions
==========================================

7 tables for governance policies, rule lifecycle events, truth validation,
calibration triggers/events, and unified audit chain. Mirrors schemas.py 1:1.

Follows existing P2 conventions:
  - _FoundationMixin for shared columns (schema_version, tenant_id, etc.)
  - JSONB for flexible nested data
  - VARCHAR(64) for enums (not Postgres native ENUMs)
  - Strategic composite indexes on query patterns
  - Primary keys as natural identifiers (not synthetic UUIDs)

Table naming: df_gov_* prefix to distinguish from df_* and df_eval_* tables.
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
# 1. df_gov_policies — GovernancePolicy
# ═══════════════════════════════════════════════════════════════════════════════

class GovernancePolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_policies"

    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)
    policy_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Scope
    scope_risk_levels: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scope_actions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scope_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scope_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Configuration
    policy_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Activation
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)

    # Audit
    authored_by: Mapped[str] = mapped_column(String(128), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_gov_pol_type_active", "policy_type", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. df_gov_lifecycle_events — RuleLifecycleEvent
# ═══════════════════════════════════════════════════════════════════════════════

class RuleLifecycleEventORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_lifecycle_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    spec_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    transition_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # Actor
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Context
    validation_result_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    policy_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    supersedes_spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Audit chain
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    previous_event_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_gov_lce_spec_occurred", "spec_id", "occurred_at"),
        Index("ix_gov_lce_transition", "transition_type"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. df_gov_truth_policies — TruthValidationPolicy
# ═══════════════════════════════════════════════════════════════════════════════

class TruthValidationPolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_truth_policies"

    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_dataset: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)

    # Source ranking
    source_priority_order: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Freshness
    freshness_max_hours: Mapped[float] = mapped_column(Float, nullable=False, default=24.0)

    # Completeness
    completeness_min_fields: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Corroboration
    corroboration_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corroboration_min_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    deviation_max_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Field-level validation
    validation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Meta
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    authored_by: Mapped[str] = mapped_column(String(128), nullable=False)

    __table_args__ = (
        Index("ix_gov_tvp_dataset_active", "target_dataset", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. df_gov_truth_results — TruthValidationResult
# ═══════════════════════════════════════════════════════════════════════════════

class TruthValidationResultORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_truth_results"

    result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_dataset: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Check results
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    freshness_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    completeness_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    corroboration_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    field_checks_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    field_checks_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Meta
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("ix_gov_tvr_policy_valid", "policy_id", "is_valid"),
        Index("ix_gov_tvr_dataset_record", "target_dataset", "record_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. df_gov_calibration_triggers — CalibrationTrigger
# ═══════════════════════════════════════════════════════════════════════════════

class CalibrationTriggerORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_calibration_triggers"

    trigger_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger_name: Mapped[str] = mapped_column(String(256), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_metric: Mapped[str] = mapped_column(String(128), nullable=False)
    threshold_operator: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    lookback_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    min_evaluations: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Meta
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    authored_by: Mapped[str] = mapped_column(String(128), nullable=False)

    __table_args__ = (
        Index("ix_gov_ctrig_type_active", "trigger_type", "is_active"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. df_gov_calibration_events — CalibrationEvent
# ═══════════════════════════════════════════════════════════════════════════════

class CalibrationEventORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_calibration_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trigger_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Trigger context
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
    lookback_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lookback_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Resolution
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="TRIGGERED")
    resolved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_gov_calev_rule_status", "rule_id", "status"),
        Index("ix_gov_calev_trigger_status", "trigger_id", "status"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. df_gov_audit_entries — GovernanceAuditEntry
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceAuditEntryORM(_FoundationMixin, Base):
    __tablename__ = "df_gov_audit_entries"

    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Actor
    actor: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Payload
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Audit chain
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    previous_audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_gov_aud_subject", "subject_type", "subject_id"),
        Index("ix_gov_aud_event_occurred", "event_type", "occurred_at"),
        Index("ix_gov_aud_actor_occurred", "actor", "occurred_at"),
    )
