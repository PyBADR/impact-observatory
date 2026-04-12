"""
Enforcement Layer — ORM Table Definitions
===========================================

4 tables for enforcement policies, decisions, execution gates,
and approval requests.  Mirrors schemas.py 1:1.

Follows existing conventions:
  - _FoundationMixin for shared columns
  - JSONB for flexible nested data
  - VARCHAR(64) for enums
  - Strategic composite indexes on query patterns
  - Natural primary keys

Table naming: df_enf_* prefix.
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

from src.data_foundation.models.tables import _FoundationMixin
from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. df_enf_policies — Enforcement policy definitions
# ═══════════════════════════════════════════════════════════════════════════════


class EnforcementPolicyORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_policies"

    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(256), nullable=False)
    policy_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)

    enforcement_action: Mapped[str] = mapped_column(String(64), nullable=False)

    # Conditions
    min_rule_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    require_truth_validation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_unresolved_calibrations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_degradation_factor: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Scope (JSONB arrays)
    scope_risk_levels: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    scope_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    scope_countries: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    scope_sectors: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Fallback
    fallback_action: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Approval
    required_approver_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_timeout_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Priority + activation
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Audit
    authored_by: Mapped[str] = mapped_column(String(128), nullable=False)

    __table_args__ = (
        Index("ix_enf_pol_action_active", "enforcement_action", "is_active"),
        Index("ix_enf_pol_priority", "priority"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. df_enf_decisions — Enforcement evaluation records
# ═══════════════════════════════════════════════════════════════════════════════


class EnforcementDecisionORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_decisions"

    decision_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    spec_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    enforcement_action: Mapped[str] = mapped_column(String(64), nullable=False)
    is_executable: Mapped[bool] = mapped_column(Boolean, nullable=False)

    triggered_policy_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    trigger_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    blocking_reasons: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    original_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    effective_confidence: Mapped[float] = mapped_column(Float, nullable=False)

    fallback_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    required_approver: Mapped[str | None] = mapped_column(String(128), nullable=True)

    rule_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    truth_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    unresolved_calibrations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latest_correctness_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    __table_args__ = (
        Index("ix_enf_dec_dlog", "decision_log_id"),
        Index("ix_enf_dec_action", "enforcement_action"),
        Index("ix_enf_dec_eval_at", "evaluated_at"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. df_enf_execution_gates — Final gate resolution
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutionGateResultORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_execution_gates"

    gate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    enforcement_decision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    gate_outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    may_execute: Mapped[bool] = mapped_column(Boolean, nullable=False)

    approval_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    applied_fallback_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    applied_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_shadow_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    resolved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )

    __table_args__ = (
        Index("ix_enf_gate_outcome", "gate_outcome"),
        Index("ix_enf_gate_dlog", "decision_log_id"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. df_enf_approval_requests — Pending approvals
# ═══════════════════════════════════════════════════════════════════════════════


class ApprovalRequestORM(_FoundationMixin, Base):
    __tablename__ = "df_enf_approval_requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    enforcement_decision_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_log_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    gate_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    required_approver_role: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="PENDING")
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    timeout_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_enf_areq_status", "status"),
        Index("ix_enf_areq_dlog", "decision_log_id"),
        Index("ix_enf_areq_role_status", "required_approver_role", "status"),
    )
