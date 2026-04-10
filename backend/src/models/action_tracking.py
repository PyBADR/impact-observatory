"""
Impact Observatory | مرصد الأثر — Action Tracking ORM Models

Layer: Data (L1) — PostgreSQL persistence for decision authority actions.

Tables:
  - authority_runs:     Decision authority run snapshots
  - tracked_actions:    Recommended actions with execution tracking
  - action_history:     Immutable audit trail for action state changes

Conventions:
  - String(64) UUIDs via _uuid() default
  - DateTime(timezone=True) via _utcnow() default
  - JSONB for flexible payloads
  - tenant_id on every table for multi-tenant isolation
  - Indexes on frequently queried columns
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Authority Runs — decision authority execution snapshots
# ─────────────────────────────────────────────────────────────────────────────

class AuthorityRunRecord(Base):
    """Persisted decision authority run.

    Stores the full directive output for replay, audit, and tenant-scoped
    retrieval without re-running the simulation engine.
    """
    __tablename__ = "authority_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default", index=True)

    # Scenario context
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=336)

    # Decision output
    decision: Mapped[str] = mapped_column(String(32), nullable=False, default="ESCALATE")
    display_decision: Mapped[str] = mapped_column(String(32), nullable=False, default="ESCALATE")
    urgency: Mapped[str] = mapped_column(String(32), nullable=False, default="MODERATE")
    pressure_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Full payloads
    raw_payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Audit
    audit_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="2.1.0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    actions: Mapped[list["TrackedActionRecord"]] = relationship(
        back_populates="authority_run", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_authority_runs_tenant_scenario", "tenant_id", "scenario_id"),
        Index("ix_authority_runs_created", "created_at"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tracked Actions — recommended actions with execution state
# ─────────────────────────────────────────────────────────────────────────────

class TrackedActionRecord(Base):
    """Persisted trackable action from a decision authority run.

    State machine: PENDING → ACKNOWLEDGED → IN_PROGRESS → DONE | BLOCKED
    """
    __tablename__ = "tracked_actions"

    action_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("authority_runs.run_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default", index=True)

    # Action content
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    action_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str] = mapped_column(String(64), nullable=False, default="cross-sector")
    owner: Mapped[str] = mapped_column(String(256), nullable=False, default="Chief Risk Officer")
    owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Financial
    impact_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    impact_formatted: Mapped[str] = mapped_column(String(64), nullable=False, default="$0")
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_formatted: Mapped[str] = mapped_column(String(64), nullable=False, default="$0")
    roi_multiple: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feasibility: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)

    # Tracking state
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    owner_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    execution_progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Notes stored as JSONB array
    notes_json: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    # Audit
    last_update_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    authority_run: Mapped["AuthorityRunRecord"] = relationship(back_populates="actions")
    history: Mapped[list["ActionHistoryRecord"]] = relationship(
        back_populates="tracked_action", cascade="all, delete-orphan",
        order_by="ActionHistoryRecord.timestamp",
    )

    __table_args__ = (
        Index("ix_tracked_actions_tenant_run", "tenant_id", "run_id"),
        Index("ix_tracked_actions_tenant_status", "tenant_id", "status"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Action History — immutable audit trail
# ─────────────────────────────────────────────────────────────────────────────

class ActionHistoryRecord(Base):
    """Immutable audit entry for action state changes.

    Every PATCH / status transition creates one record. Never updated or deleted.
    """
    __tablename__ = "action_history"

    history_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    action_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tracked_actions.action_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default", index=True)

    # State change
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(256), nullable=False, default="system")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changes_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Audit
    audit_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationship
    tracked_action: Mapped["TrackedActionRecord"] = relationship(back_populates="history")

    __table_args__ = (
        Index("ix_action_history_tenant_action", "tenant_id", "action_id"),
    )
