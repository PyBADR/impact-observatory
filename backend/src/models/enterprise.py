"""
Impact Observatory | مرصد الأثر — Enterprise Multi-Tenant ORM Models

Layer: Data (L1) — Relational storage for multi-tenant SaaS platform.

Tables:
  - tenants: Organizations / insurance companies
  - users: Users belonging to tenants
  - roles: Role definitions per tenant
  - permissions: Permission grants per role  
  - user_roles: User-role junction table
  - workflows: Workflow definitions (underwriting, claims, etc.)
  - workflow_runs: Execution instances of workflows
  - workflow_steps: Individual step results within a run
  - audit_events: Immutable audit log with SHA-256 hash chain
  - policies: Tenant-scoped policy rules
"""

from __future__ import annotations

import uuid
import hashlib
import json
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Enums ──

class TenantStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    DEACTIVATED = "deactivated"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class WorkflowType(StrEnum):
    UNDERWRITING = "underwriting"
    CLAIMS = "claims"
    RISK_ASSESSMENT = "risk_assessment"
    POLICY_RENEWAL = "policy_renewal"
    FRAUD_REVIEW = "fraud_review"
    CUSTOM = "custom"


class WorkflowRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    AWAITING_INPUT = "awaiting_input"


class AuditAction(StrEnum):
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    # Tenant
    TENANT_CREATED = "tenant_created"
    TENANT_UPDATED = "tenant_updated"
    TENANT_SUSPENDED = "tenant_suspended"
    # User
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_ROLE_ASSIGNED = "user_role_assigned"
    USER_ROLE_REVOKED = "user_role_revoked"
    USER_SUSPENDED = "user_suspended"
    # Workflow
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    # Decision
    DECISION_CREATED = "decision_created"
    DECISION_EXECUTED = "decision_executed"
    DECISION_OVERRIDDEN = "decision_overridden"
    # Policy
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_ACTIVATED = "policy_activated"
    POLICY_DEACTIVATED = "policy_deactivated"
    # Simulation
    SIMULATION_RUN = "simulation_run"
    # Admin
    PERMISSION_CHANGED = "permission_changed"
    SETTINGS_CHANGED = "settings_changed"


# ══════════════════════════════════════════════════════════════════════════════
# Tenant (Organization)
# ══════════════════════════════════════════════════════════════════════════════

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=TenantStatus.ACTIVE)
    tier: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")  # trial, standard, enterprise
    settings_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_workflows_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", lazy="selectin")
    roles: Mapped[list["Role"]] = relationship("Role", back_populates="tenant", lazy="selectin")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="tenant", lazy="selectin")


# ══════════════════════════════════════════════════════════════════════════════
# User
# ══════════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=UserStatus.ACTIVE)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="user", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_email", "email"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Role & Permissions
# ══════════════════════════════════════════════════════════════════════════════

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # True = cannot be deleted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="role", lazy="selectin")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    role_id: Mapped[str] = mapped_column(String(64), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "decision", "policy", "workflow"
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "create", "view", "edit", "approve", "delete"

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "resource", "action", name="uq_perms_role_resource_action"),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[str] = mapped_column(String(64), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    assigned_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Workflow Engine
# ══════════════════════════════════════════════════════════════════════════════

class Workflow(Base):
    """Workflow definition (template). E.g. "Motor Underwriting", "Marine Claims"."""
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(64), nullable=False, default=WorkflowType.CUSTOM)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    steps_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # Step definitions
    config_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Thresholds, auto-approval rules
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="workflows")
    runs: Mapped[list["WorkflowRun"]] = relationship("WorkflowRun", back_populates="workflow", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_workflows_tenant_name_ver"),
    )


class WorkflowRun(Base):
    """A single execution of a Workflow. Tracks progress through steps."""
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(64), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    initiated_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=WorkflowRunStatus.PENDING)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Application/claim data
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Final result
    context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Accumulated context
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Link to simulation run
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="runs")
    steps: Mapped[list["WorkflowStep"]] = relationship("WorkflowStep", back_populates="workflow_run", lazy="selectin")

    __table_args__ = (
        Index("ix_wf_runs_tenant_status", "tenant_id", "status"),
        Index("ix_wf_runs_created", "started_at"),
    )


class WorkflowStep(Base):
    """Individual step result within a WorkflowRun."""
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    workflow_run_id: Mapped[str] = mapped_column(String(64), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    step_type: Mapped[str] = mapped_column(String(64), nullable=False)  # "auto", "hitl", "conditional", "api_call"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=WorkflowStepStatus.PENDING)
    input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    decision_by: Mapped[str | None] = mapped_column(String(64), nullable=True)  # User who approved/rejected (HITL)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    workflow_run: Mapped["WorkflowRun"] = relationship("WorkflowRun", back_populates="steps")

    __table_args__ = (
        UniqueConstraint("workflow_run_id", "step_index", name="uq_wf_step_run_idx"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Audit Events (Immutable, SHA-256 Hash Chain)
# ══════════════════════════════════════════════════════════════════════════════

class AuditEvent(Base):
    """
    Immutable audit log. Every row chains to its predecessor via prev_hash,
    forming a tamper-evident ledger per tenant.
    """
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # User who performed the action
    actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # "workflow", "decision", "policy", etc.
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # State before change
    after_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # State after change
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Hash chain
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False)  # SHA-256 of this event
    prev_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)  # Hash of previous event in tenant chain
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_tenant_seq", "tenant_id", "sequence"),
        Index("ix_audit_actor", "actor_id"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_action", "action"),
    )

    @staticmethod
    def compute_hash(
        tenant_id: str,
        actor_id: str | None,
        action: str,
        resource_type: str | None,
        resource_id: str | None,
        prev_hash: str | None,
        timestamp: str,
    ) -> str:
        payload = json.dumps({
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "prev_hash": prev_hash,
            "timestamp": timestamp,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# Tenant-Scoped Policies
# ══════════════════════════════════════════════════════════════════════════════

class PolicyRule(Base):
    """Tenant-scoped policy rules that the workflow engine evaluates."""
    __tablename__ = "policy_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # "underwriting", "claims", "risk", "compliance"
    condition_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Rule condition expression
    action_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # What to do when triggered
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_policy_tenant_category", "tenant_id", "category"),
    )
