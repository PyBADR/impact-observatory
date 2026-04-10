"""
Impact Observatory | مرصد الأثر — Enterprise Multi-Tenant Pydantic Schemas

Layer: API (L5) — Request/response validation for multi-tenant SaaS endpoints.

All schemas follow Pydantic v2 conventions. Response models use model_config
with from_attributes=True for ORM compatibility.

Data Contract:
  - Tenant schemas: create, update, response, list
  - User schemas: create, invite, update, response, list
  - Role/Permission schemas: create, assign, response
  - Workflow schemas: create, update, run request, step approval
  - Audit schemas: event response, query params, chain verification
  - Auth schemas: login, token response, tenant-scoped JWT payload
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from pydantic import EmailStr
except ImportError:
    # Fallback when email-validator is not installed (dev sandbox)
    EmailStr = str  # type: ignore[misc,assignment]


# ══════════════════════════════════════════════════════════════════════════════
# Auth Schemas
# ══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    tenant_slug: str | None = Field(None, description="Tenant slug for multi-tenant login")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token TTL in seconds")
    user_id: str
    email: str
    tenant_id: str
    tenant_name: str
    roles: list[str] = []


class JWTPayload(BaseModel):
    """Decoded JWT claim structure — tenant-scoped."""
    sub: str  # user_id
    email: str
    role: str  # legacy role field (backward compat)
    org: str  # tenant_id
    tenant_id: str
    tenant_slug: str
    roles: list[str] = []
    permissions: list[str] = []
    iat: int
    exp: int


# ══════════════════════════════════════════════════════════════════════════════
# Tenant Schemas
# ══════════════════════════════════════════════════════════════════════════════

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    name_ar: str | None = Field(None, max_length=256)
    slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")
    domain: str | None = Field(None, max_length=256)
    tier: str = Field("standard", pattern=r"^(trial|standard|enterprise)$")
    max_users: int = Field(50, ge=1, le=10000)
    max_workflows_per_month: int = Field(1000, ge=1, le=100000)
    settings_json: dict[str, Any] | None = None


class TenantUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=256)
    name_ar: str | None = Field(None, max_length=256)
    domain: str | None = None
    status: str | None = Field(None, pattern=r"^(active|suspended|trial|deactivated)$")
    tier: str | None = Field(None, pattern=r"^(trial|standard|enterprise)$")
    max_users: int | None = Field(None, ge=1, le=10000)
    max_workflows_per_month: int | None = Field(None, ge=1, le=100000)
    settings_json: dict[str, Any] | None = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    name_ar: str | None = None
    slug: str
    domain: str | None = None
    status: str
    tier: str
    max_users: int
    max_workflows_per_month: int
    settings_json: dict[str, Any] | None = None
    user_count: int = 0
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    tenants: list[TenantResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ══════════════════════════════════════════════════════════════════════════════
# User Schemas
# ══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=256)
    name_ar: str | None = Field(None, max_length=256)
    password: str = Field(..., min_length=8, max_length=128)
    role_names: list[str] = Field(default_factory=list, description="Role names to assign")
    mfa_enabled: bool = False
    metadata_json: dict[str, Any] | None = None


class UserInvite(BaseModel):
    """Invite a user by email — password is set later via activation link."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=256)
    name_ar: str | None = None
    role_names: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    name_ar: str | None = None
    status: str | None = Field(None, pattern=r"^(active|invited|suspended|deactivated)$")
    mfa_enabled: bool | None = None
    metadata_json: dict[str, Any] | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    email: str
    name: str
    name_ar: str | None = None
    status: str
    mfa_enabled: bool = False
    last_login_at: datetime | None = None
    roles: list[RoleResponse] = []
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ══════════════════════════════════════════════════════════════════════════════
# Role & Permission Schemas
# ══════════════════════════════════════════════════════════════════════════════

class PermissionSpec(BaseModel):
    resource: str = Field(..., max_length=128)
    action: str = Field(..., max_length=64)


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    name_ar: str | None = Field(None, max_length=128)
    description: str | None = None
    permissions: list[PermissionSpec] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    name_ar: str | None = None
    description: str | None = None
    permissions: list[PermissionSpec] | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource: str
    action: str


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    name_ar: str | None = None
    description: str | None = None
    is_system: bool = False
    permissions: list[PermissionResponse] = []
    created_at: datetime


class RoleAssign(BaseModel):
    """Assign/revoke role for a user."""
    user_id: str
    role_id: str


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]
    total: int


# ══════════════════════════════════════════════════════════════════════════════
# Workflow Schemas
# ══════════════════════════════════════════════════════════════════════════════

class WorkflowStepDef(BaseModel):
    """Step definition within a workflow template."""
    step_name: str = Field(..., max_length=128)
    step_type: str = Field(..., pattern=r"^(auto|hitl|conditional|api_call)$")
    config: dict[str, Any] | None = None
    timeout_seconds: int | None = Field(None, ge=0, le=86400)
    required_permission: str | None = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    name_ar: str | None = None
    workflow_type: str = Field("custom", pattern=r"^(underwriting|claims|risk_assessment|policy_renewal|fraud_review|custom)$")
    description: str | None = None
    steps: list[WorkflowStepDef] = Field(default_factory=list)
    config_json: dict[str, Any] | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=256)
    name_ar: str | None = None
    description: str | None = None
    is_active: bool | None = None
    steps: list[WorkflowStepDef] | None = None
    config_json: dict[str, Any] | None = None


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    name_ar: str | None = None
    workflow_type: str
    description: str | None = None
    version: int
    is_active: bool
    steps_json: list[dict[str, Any]] | None = None
    config_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowResponse]
    total: int


class WorkflowRunRequest(BaseModel):
    """Start a new workflow run."""
    workflow_id: str
    input_json: dict[str, Any] = Field(default_factory=dict)
    run_id: str | None = Field(None, description="Link to simulation run_id")


class WorkflowStepApproval(BaseModel):
    """Human-in-the-loop step decision."""
    decision: str = Field(..., pattern=r"^(approve|reject|return)$")
    reason: str | None = None
    metadata: dict[str, Any] | None = None


class WorkflowStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_index: int
    step_name: str
    step_type: str
    status: str
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    decision_by: str | None = None
    decision_reason: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    workflow_id: str
    initiated_by: str
    status: str
    current_step: int
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    context_json: dict[str, Any] | None = None
    error_message: str | None = None
    run_id: str | None = None
    steps: list[WorkflowStepResponse] = []
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None


class WorkflowRunListResponse(BaseModel):
    runs: list[WorkflowRunResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ══════════════════════════════════════════════════════════════════════════════
# Audit Schemas
# ══════════════════════════════════════════════════════════════════════════════

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    actor_id: str | None = None
    actor_email: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    description: str | None = None
    before_json: dict[str, Any] | None = None
    after_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    ip_address: str | None = None
    event_hash: str
    prev_hash: str | None = None
    sequence: int
    created_at: datetime


class AuditQueryParams(BaseModel):
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    actor_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)


class AuditListResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int
    page: int = 1
    page_size: int = 50
    chain_valid: bool = True


class AuditChainVerification(BaseModel):
    tenant_id: str
    total_events: int
    verified_events: int
    chain_valid: bool
    first_break_at: int | None = None
    verified_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# Policy Rule Schemas
# ══════════════════════════════════════════════════════════════════════════════

class PolicyRuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    name_ar: str | None = None
    category: str = Field(..., pattern=r"^(underwriting|claims|risk|compliance|fraud)$")
    condition_json: dict[str, Any] | None = None
    action_json: dict[str, Any] | None = None
    priority: int = Field(100, ge=0, le=9999)
    is_active: bool = True


class PolicyRuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=256)
    name_ar: str | None = None
    category: str | None = None
    condition_json: dict[str, Any] | None = None
    action_json: dict[str, Any] | None = None
    priority: int | None = Field(None, ge=0, le=9999)
    is_active: bool | None = None


class PolicyRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    name_ar: str | None = None
    category: str
    condition_json: dict[str, Any] | None = None
    action_json: dict[str, Any] | None = None
    priority: int
    is_active: bool
    version: int
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


class PolicyRuleListResponse(BaseModel):
    rules: list[PolicyRuleResponse]
    total: int


# ══════════════════════════════════════════════════════════════════════════════
# Forward reference resolution
# ══════════════════════════════════════════════════════════════════════════════

# Pydantic v2 forward ref rebuild
UserResponse.model_rebuild()
UserListResponse.model_rebuild()
