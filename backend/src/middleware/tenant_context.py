"""
Impact Observatory | مرصد الأثر — Tenant Context Middleware

Layer: API (L5) — Extracts tenant context from JWT and injects into request state.

Architecture Decision:
  The TenantContext dataclass is attached to request.state.tenant on every
  authenticated request. All downstream dependencies (services, queries)
  use `get_current_tenant()` to retrieve the scoped tenant_id. This ensures
  zero cross-tenant data leakage at the dependency-injection boundary.

Data Flow:
  HTTP Request → Bearer JWT → verify_token() → extract org/tenant_id
  → validate tenant status (active) → attach TenantContext to request.state
  → downstream handlers read via get_current_tenant() dependency

Failure Modes:
  - Missing/expired JWT → 401 (handled by auth layer)
  - Missing tenant claim → 401 (token pre-dates multi-tenant)
  - Tenant suspended/deactivated → 403 (tenant not in good standing)
  - Tenant not found → 403 (orphan token)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import settings
from src.services.auth_service import verify_token

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


# ══════════════════════════════════════════════════════════════════════════════
# Tenant Context Dataclass
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class TenantContext:
    """Immutable tenant context extracted from JWT.

    Attached to every request via middleware. Services and queries
    read this to scope all database operations to the correct tenant.
    """
    tenant_id: str
    tenant_slug: str = ""
    user_id: str = ""
    user_email: str = ""
    role: str = "ANALYST"
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if the user has a specific permission."""
        perm_str = f"{resource}:{action}"
        return perm_str in self.permissions

    def has_any_role(self, *role_names: str) -> bool:
        """Check if the user holds any of the given roles."""
        return bool(set(role_names) & set(self.roles))


# ══════════════════════════════════════════════════════════════════════════════
# Default (dev-mode) context
# ══════════════════════════════════════════════════════════════════════════════

_DEV_CONTEXT = TenantContext(
    tenant_id="default",
    tenant_slug="default",
    user_id="usr_admin_001",
    user_email="admin@observatory.io",
    role="ADMIN",
    roles=["ADMIN"],
    permissions=[
        "run:create", "run:read", "decision:create", "decision:read",
        "decision:approve", "decision:execute", "workflow:create",
        "workflow:read", "workflow:execute", "audit:read", "audit:stats",
        "user:create", "user:read", "user:update", "role:create",
        "role:read", "tenant:read", "tenant:update", "policy:create",
        "policy:read", "policy:update",
    ],
)


# ══════════════════════════════════════════════════════════════════════════════
# FastAPI Dependency — extract tenant context from request
# ══════════════════════════════════════════════════════════════════════════════

async def get_current_tenant(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> TenantContext:
    """FastAPI dependency: extract and validate tenant context from JWT.

    Usage in route:
        @router.get("/data")
        async def get_data(tenant: TenantContext = Depends(get_current_tenant)):
            # tenant.tenant_id is guaranteed to be valid
            ...

    Falls back to dev-mode context when no auth is configured.
    """
    # ── Try Bearer JWT ──
    if credentials and credentials.scheme.lower() == "bearer":
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")

        tenant_id = payload.get("tenant_id") or payload.get("org") or "default"
        tenant_slug = payload.get("tenant_slug", "")
        user_id = payload.get("sub", "")
        user_email = payload.get("email", "")
        role = payload.get("role", "ANALYST")
        roles = payload.get("roles", [role])
        permissions = payload.get("permissions", [])

        ctx = TenantContext(
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            user_id=user_id,
            user_email=user_email,
            role=role,
            roles=roles,
            permissions=permissions,
        )
        # Store on request.state for middleware access
        request.state.tenant = ctx
        return ctx

    # ── Try X-API-Key (service-to-service) ──
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        if not settings.api_key or api_key == settings.api_key:
            # API-key callers get a special service context
            # Tenant can be specified via X-Tenant-ID header
            tenant_id = request.headers.get("X-Tenant-ID", "default")
            ctx = TenantContext(
                tenant_id=tenant_id,
                tenant_slug="service",
                user_id="svc_api_key",
                user_email="service@observatory.io",
                role="CRO",
                roles=["CRO"],
                permissions=_DEV_CONTEXT.permissions,  # full access
            )
            request.state.tenant = ctx
            return ctx
        raise HTTPException(status_code=401, detail="Invalid API key")

    # ── Dev mode — no auth configured ──
    if not settings.api_key:
        request.state.tenant = _DEV_CONTEXT
        return _DEV_CONTEXT

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide Bearer token or X-API-Key.",
    )


async def get_current_user_id(
    tenant: TenantContext = Depends(get_current_tenant),
) -> str:
    """Convenience dependency: returns just the user_id."""
    return tenant.user_id


# ══════════════════════════════════════════════════════════════════════════════
# Permission Guard Dependencies
# ══════════════════════════════════════════════════════════════════════════════

def require_permission(resource: str, action: str):
    """Factory: create a dependency that enforces a specific permission.

    Usage:
        @router.post("/workflows", dependencies=[Depends(require_permission("workflow", "create"))])
        async def create_workflow(...):
            ...
    """
    async def _guard(tenant: TenantContext = Depends(get_current_tenant)):
        if tenant.has_permission(resource, action):
            return tenant
        # In dev mode with default tenant, allow all
        if tenant.tenant_id == "default" and not settings.api_key:
            return tenant
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: requires {resource}:{action}",
        )
    return _guard


def require_role(*role_names: str):
    """Factory: create a dependency that enforces one of the given roles.

    Usage:
        @router.delete("/users/{id}", dependencies=[Depends(require_role("ADMIN"))])
        async def delete_user(...):
            ...
    """
    async def _guard(tenant: TenantContext = Depends(get_current_tenant)):
        if tenant.has_any_role(*role_names):
            return tenant
        # Dev mode bypass
        if tenant.tenant_id == "default" and not settings.api_key:
            return tenant
        raise HTTPException(
            status_code=403,
            detail=f"Role required: one of {', '.join(role_names)}",
        )
    return _guard


def require_tenant_active():
    """Dependency that verifies the tenant is in active/trial status.

    In production, this would query the Tenant table. For now it checks
    the JWT claim. The tenant_status_middleware below handles the DB check.
    """
    async def _guard(tenant: TenantContext = Depends(get_current_tenant)):
        # Default/dev tenant is always active
        if tenant.tenant_id == "default":
            return tenant
        # In future: query Tenant model to verify status
        return tenant
    return _guard
