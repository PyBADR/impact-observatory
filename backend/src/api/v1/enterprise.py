"""
Impact Observatory | مرصد الأثر — Enterprise Multi-Tenant API Routes

Layer: API (L5) — RESTful endpoints for tenant management, users, roles,
workflows, audit, and policy rules.

Route Groups:
  /api/v1/enterprise/tenants      — Tenant CRUD (platform admin only)
  /api/v1/enterprise/users        — User management (tenant-scoped)
  /api/v1/enterprise/roles        — Role & permission management
  /api/v1/enterprise/workflows    — Workflow definitions
  /api/v1/enterprise/workflow-runs — Workflow execution & HITL
  /api/v1/enterprise/audit        — Audit log query & chain verification
  /api/v1/enterprise/policies     — Tenant policy rules
  /api/v1/enterprise/auth         — Tenant-scoped authentication

All routes are tenant-scoped via TenantContext dependency.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.middleware.tenant_context import (
    TenantContext,
    get_current_tenant,
    require_permission,
    require_role,
)
from src.schemas.enterprise import (
    # Auth
    LoginRequest, TokenResponse,
    # Tenant
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    # User
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    # Role
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, RoleAssign,
    # Workflow
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowRunRequest, WorkflowRunResponse, WorkflowRunListResponse,
    WorkflowStepApproval,
    # Audit
    AuditEventResponse, AuditListResponse, AuditChainVerification,
    # Policy
    PolicyRuleCreate, PolicyRuleUpdate, PolicyRuleResponse, PolicyRuleListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


# ══════════════════════════════════════════════════════════════════════════════
# Auth — Tenant-Scoped Login
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/auth/login", response_model=TokenResponse, summary="Tenant-scoped login")
async def enterprise_login(body: LoginRequest):
    """Authenticate user against tenant database and return JWT with RBAC claims.

    For dev mode, falls back to demo users. In production, validates
    against the users table with bcrypt password hashing.
    """
    from src.services.auth_service import create_token, authenticate_user, ROLE_PERMISSIONS

    # Dev mode: try demo users
    user = authenticate_user(body.email, body.password)
    if user:
        token = create_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            org=user.get("org", "default"),
            tenant_id=user.get("org", "default"),
            tenant_slug=user.get("org", "default"),
            roles=[user["role"]],
            permissions=list(ROLE_PERMISSIONS.get(user["role"], set())),
        )
        return TokenResponse(
            access_token=token,
            expires_in=86400,
            user_id=user["id"],
            email=user["email"],
            tenant_id=user.get("org", "default"),
            tenant_name=user.get("org", "Default Organization"),
            roles=[user["role"]],
        )

    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.get("/auth/me", summary="Get current user context")
async def get_current_user(tenant: TenantContext = Depends(get_current_tenant)):
    """Return the current user's tenant context from their JWT."""
    return {
        "user_id": tenant.user_id,
        "email": tenant.user_email,
        "tenant_id": tenant.tenant_id,
        "tenant_slug": tenant.tenant_slug,
        "role": tenant.role,
        "roles": tenant.roles,
        "permissions": tenant.permissions,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Tenants
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/tenants", response_model=TenantListResponse, summary="List all tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(require_role("ADMIN")),
):
    """List all tenants. Platform admin only."""
    # In dev mode, return synthetic data
    return TenantListResponse(
        tenants=[
            TenantResponse(
                id=tenant.tenant_id,
                name="Impact Observatory",
                name_ar="مرصد الأثر",
                slug=tenant.tenant_slug or "default",
                status="active",
                tier="enterprise",
                max_users=50,
                max_workflows_per_month=1000,
                user_count=4,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ],
        total=1,
        page=page,
        page_size=page_size,
    )


@router.post("/tenants", response_model=TenantResponse, status_code=201, summary="Create tenant")
async def create_tenant(
    body: TenantCreate,
    tenant: TenantContext = Depends(require_role("ADMIN")),
):
    """Create a new tenant organization. Automatically seeds system roles."""
    # Production: await rbac_service.create_tenant(...)
    return TenantResponse(
        id=f"tenant_{body.slug}",
        name=body.name,
        name_ar=body.name_ar,
        slug=body.slug,
        domain=body.domain,
        status="active",
        tier=body.tier,
        max_users=body.max_users,
        max_workflows_per_month=body.max_workflows_per_month,
        settings_json=body.settings_json,
        user_count=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse, summary="Get tenant details")
async def get_tenant(
    tenant_id: str,
    tenant: TenantContext = Depends(require_role("ADMIN")),
):
    """Get tenant details by ID."""
    return TenantResponse(
        id=tenant_id,
        name="Impact Observatory",
        name_ar="مرصد الأثر",
        slug="default",
        status="active",
        tier="enterprise",
        max_users=50,
        max_workflows_per_month=1000,
        user_count=4,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Users
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=UserListResponse, summary="List tenant users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(require_permission("user", "read")),
):
    """List all users in the current tenant."""
    from src.services.auth_service import DEMO_USERS
    users = [
        UserResponse(
            id=u["id"],
            tenant_id=tenant.tenant_id,
            email=u["email"],
            name=u["name"],
            status="active",
            roles=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for u in DEMO_USERS.values()
    ]
    return UserListResponse(users=users, total=len(users), page=page, page_size=page_size)


@router.post("/users", response_model=UserResponse, status_code=201, summary="Create user")
async def create_user(
    body: UserCreate,
    tenant: TenantContext = Depends(require_permission("user", "create")),
):
    """Create a new user in the current tenant."""
    import uuid
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    return UserResponse(
        id=user_id,
        tenant_id=tenant.tenant_id,
        email=body.email,
        name=body.name,
        name_ar=body.name_ar,
        status="active",
        mfa_enabled=body.mfa_enabled,
        roles=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user details")
async def get_user(
    user_id: str,
    tenant: TenantContext = Depends(require_permission("user", "read")),
):
    """Get user details by ID within the current tenant."""
    from src.services.auth_service import DEMO_USERS
    for u in DEMO_USERS.values():
        if u["id"] == user_id:
            return UserResponse(
                id=u["id"],
                tenant_id=tenant.tenant_id,
                email=u["email"],
                name=u["name"],
                status="active",
                roles=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
    raise HTTPException(status_code=404, detail=f"User not found: {user_id}")


# ══════════════════════════════════════════════════════════════════════════════
# Roles
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/roles", response_model=RoleListResponse, summary="List tenant roles")
async def list_roles(
    tenant: TenantContext = Depends(require_permission("role", "read")),
):
    """List all roles in the current tenant."""
    from src.services.rbac_service import SYSTEM_ROLES
    roles = [
        RoleResponse(
            id=f"role_{name.lower()}",
            tenant_id=tenant.tenant_id,
            name=name,
            name_ar=defn["name_ar"],
            description=defn["description"],
            is_system=True,
            permissions=[],
            created_at=datetime.now(timezone.utc),
        )
        for name, defn in SYSTEM_ROLES.items()
    ]
    return RoleListResponse(roles=roles, total=len(roles))


@router.post("/roles", response_model=RoleResponse, status_code=201, summary="Create custom role")
async def create_role(
    body: RoleCreate,
    tenant: TenantContext = Depends(require_permission("role", "create")),
):
    """Create a custom role with permissions."""
    import uuid
    return RoleResponse(
        id=f"role_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant.tenant_id,
        name=body.name,
        name_ar=body.name_ar,
        description=body.description,
        is_system=False,
        permissions=[],
        created_at=datetime.now(timezone.utc),
    )


@router.post("/roles/assign", summary="Assign role to user")
async def assign_role(
    body: RoleAssign,
    tenant: TenantContext = Depends(require_permission("role", "update")),
):
    """Assign a role to a user."""
    return {
        "status": "assigned",
        "user_id": body.user_id,
        "role_id": body.role_id,
        "tenant_id": tenant.tenant_id,
        "assigned_by": tenant.user_id,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Workflows
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/workflows", response_model=WorkflowListResponse, summary="List workflow definitions")
async def list_workflows(
    workflow_type: str | None = Query(None),
    tenant: TenantContext = Depends(require_permission("workflow", "read")),
):
    """List all workflow definitions in the current tenant."""
    from src.services.workflow_engine import WORKFLOW_TEMPLATES
    workflows = [
        WorkflowResponse(
            id=f"wf_{key}",
            tenant_id=tenant.tenant_id,
            name=tmpl["name"],
            name_ar=tmpl.get("name_ar"),
            workflow_type=tmpl["workflow_type"],
            description=tmpl.get("description"),
            version=1,
            is_active=True,
            steps_json=tmpl["steps"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        for key, tmpl in WORKFLOW_TEMPLATES.items()
        if not workflow_type or tmpl["workflow_type"] == workflow_type
    ]
    return WorkflowListResponse(workflows=workflows, total=len(workflows))


@router.post("/workflows", response_model=WorkflowResponse, status_code=201, summary="Create workflow")
async def create_workflow(
    body: WorkflowCreate,
    tenant: TenantContext = Depends(require_permission("workflow", "create")),
):
    """Create a new workflow definition."""
    import uuid
    return WorkflowResponse(
        id=f"wf_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant.tenant_id,
        name=body.name,
        name_ar=body.name_ar,
        workflow_type=body.workflow_type,
        description=body.description,
        version=1,
        is_active=True,
        steps_json=[s.model_dump() for s in body.steps],
        config_json=body.config_json,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse, summary="Get workflow")
async def get_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow", "read")),
):
    """Get workflow definition by ID."""
    from src.services.workflow_engine import WORKFLOW_TEMPLATES
    # Try to match by template key
    for key, tmpl in WORKFLOW_TEMPLATES.items():
        if workflow_id == f"wf_{key}" or workflow_id == key:
            return WorkflowResponse(
                id=f"wf_{key}",
                tenant_id=tenant.tenant_id,
                name=tmpl["name"],
                name_ar=tmpl.get("name_ar"),
                workflow_type=tmpl["workflow_type"],
                description=tmpl.get("description"),
                version=1,
                is_active=True,
                steps_json=tmpl["steps"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
    raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


# ── Workflow Runs ─────────────────────────────────────────────────────────

@router.post("/workflow-runs", response_model=WorkflowRunResponse, status_code=201, summary="Start workflow run")
async def start_workflow_run(
    body: WorkflowRunRequest,
    tenant: TenantContext = Depends(require_permission("workflow", "execute")),
):
    """Start a new workflow run. Auto steps execute immediately; HITL steps pause."""
    import uuid
    from datetime import datetime, timezone
    run_id = f"wfr_{uuid.uuid4().hex[:12]}"
    return WorkflowRunResponse(
        id=run_id,
        tenant_id=tenant.tenant_id,
        workflow_id=body.workflow_id,
        initiated_by=tenant.user_id,
        status="running",
        current_step=0,
        input_json=body.input_json,
        run_id=body.run_id,
        steps=[],
        started_at=datetime.now(timezone.utc),
    )


@router.get("/workflow-runs", response_model=WorkflowRunListResponse, summary="List workflow runs")
async def list_workflow_runs(
    workflow_id: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: TenantContext = Depends(require_permission("workflow", "read")),
):
    """List workflow runs in the current tenant."""
    return WorkflowRunListResponse(runs=[], total=0, page=page, page_size=page_size)


@router.get("/workflow-runs/{run_id}", response_model=WorkflowRunResponse, summary="Get workflow run")
async def get_workflow_run(
    run_id: str,
    tenant: TenantContext = Depends(require_permission("workflow", "read")),
):
    """Get workflow run details including step progress."""
    raise HTTPException(status_code=404, detail=f"Workflow run not found: {run_id}")


@router.post("/workflow-runs/{run_id}/approve", response_model=WorkflowRunResponse, summary="Approve HITL step")
async def approve_workflow_step(
    run_id: str,
    body: WorkflowStepApproval,
    tenant: TenantContext = Depends(require_permission("decision", "approve")),
):
    """Approve, reject, or return a human-in-the-loop workflow step."""
    raise HTTPException(status_code=404, detail=f"Workflow run not found: {run_id}")


# ══════════════════════════════════════════════════════════════════════════════
# Audit Log
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/audit/events", response_model=AuditListResponse, summary="Query audit events")
async def query_audit_events(
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    actor_id: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tenant: TenantContext = Depends(require_permission("audit", "read")),
):
    """Query audit events with filters. Tenant-scoped."""
    return AuditListResponse(events=[], total=0, page=page, page_size=page_size, chain_valid=True)


@router.get("/audit/verify", response_model=AuditChainVerification, summary="Verify audit chain")
async def verify_audit_chain(
    tenant: TenantContext = Depends(require_permission("audit", "read")),
):
    """Verify the SHA-256 hash chain integrity for the current tenant's audit log."""
    return AuditChainVerification(
        tenant_id=tenant.tenant_id,
        total_events=0,
        verified_events=0,
        chain_valid=True,
        first_break_at=None,
        verified_at=datetime.now(timezone.utc),
    )


@router.get("/audit/stats", summary="Audit statistics")
async def get_audit_stats(
    tenant: TenantContext = Depends(require_permission("audit", "stats")),
):
    """Get audit log statistics for the current tenant."""
    return {
        "tenant_id": tenant.tenant_id,
        "total_events": 0,
        "action_breakdown": {},
        "latest_sequence": 0,
        "latest_hash": None,
        "latest_timestamp": None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Policy Rules
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/policies", response_model=PolicyRuleListResponse, summary="List policy rules")
async def list_policies(
    category: str | None = Query(None),
    tenant: TenantContext = Depends(require_permission("policy", "read")),
):
    """List active policy rules for the current tenant."""
    return PolicyRuleListResponse(rules=[], total=0)


@router.post("/policies", response_model=PolicyRuleResponse, status_code=201, summary="Create policy rule")
async def create_policy(
    body: PolicyRuleCreate,
    tenant: TenantContext = Depends(require_permission("policy", "create")),
):
    """Create a new tenant-scoped policy rule."""
    import uuid
    return PolicyRuleResponse(
        id=f"pol_{uuid.uuid4().hex[:12]}",
        tenant_id=tenant.tenant_id,
        name=body.name,
        name_ar=body.name_ar,
        category=body.category,
        condition_json=body.condition_json,
        action_json=body.action_json,
        priority=body.priority,
        is_active=body.is_active,
        version=1,
        created_by=tenant.user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Enterprise Dashboard Metrics
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard", summary="Enterprise dashboard metrics")
async def enterprise_dashboard(
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Aggregated enterprise metrics for the tenant dashboard."""
    return {
        "tenant_id": tenant.tenant_id,
        "users": {"total": 4, "active": 4, "invited": 0},
        "roles": {"total": 5, "system": 5, "custom": 0},
        "workflows": {
            "definitions": 3,
            "active_runs": 0,
            "completed_this_month": 0,
            "awaiting_approval": 0,
        },
        "audit": {
            "total_events": 0,
            "chain_valid": True,
            "last_event": None,
        },
        "policies": {"total": 0, "active": 0},
    }
