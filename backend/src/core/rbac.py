"""RBAC — Role-Based Access Control for Impact Observatory.

Roles: viewer, analyst, operator, admin, regulator

Permission matrix aligned to v4 engineering specification.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Callable

from fastapi import HTTPException, Request


class Role(StrEnum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    OPERATOR = "operator"
    ADMIN = "admin"
    REGULATOR = "regulator"


# ── Permission Matrix ──────────────────────────────────────────────

PERMISSIONS: dict[str, set[Role]] = {
    # Scenario management
    "scenario:create":   {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "scenario:read":     {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "scenario:archive":  {Role.OPERATOR, Role.ADMIN},

    # Run execution
    "run:create":        {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:read":          {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:financial":     {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:banking":       {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:insurance":     {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:fintech":       {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:decision":      {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:explanation":   {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:business_impact": {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:timeline":      {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "run:regulatory":    {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},

    # Decision actions (human-in-the-loop)
    "action:approve":    {Role.OPERATOR, Role.ADMIN},
    "action:reject":     {Role.OPERATOR, Role.ADMIN},

    # Reports
    "report:executive":  {Role.VIEWER, Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "report:analyst":    {Role.ANALYST, Role.OPERATOR, Role.ADMIN, Role.REGULATOR},
    "report:regulatory": {Role.ADMIN, Role.REGULATOR},

    # Audit
    "audit:read":        {Role.ADMIN, Role.REGULATOR},
    "audit:stats":       {Role.OPERATOR, Role.ADMIN, Role.REGULATOR},

    # Admin
    "config:read":       {Role.ADMIN},
    "config:write":      {Role.ADMIN},
}


def check_permission(role: Role | str, permission: str) -> bool:
    """Check if a role has a specific permission.

    Returns True if allowed, False if denied.
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return False

    allowed_roles = PERMISSIONS.get(permission)
    if allowed_roles is None:
        return False  # Unknown permission = denied

    return role in allowed_roles


def enforce_permission(role: Role | str, permission: str) -> None:
    """Raise HTTPException(403) if the role lacks the required permission."""
    if not check_permission(role, permission):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Insufficient permissions",
                "code": "INSUFFICIENT_ROLE",
                "required_permission": permission,
                "current_role": str(role),
            },
        )


def get_role_from_request(request: Request) -> Role:
    """Extract role from request headers.

    Priority: X-IO-Role header > default to viewer.
    In production, this would be derived from JWT claims.
    """
    role_header = request.headers.get("X-IO-Role", "viewer")
    try:
        return Role(role_header.lower())
    except ValueError:
        return Role.VIEWER


def get_role_permissions(role: Role | str) -> list[str]:
    """Get all permissions for a given role."""
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return []

    return [perm for perm, roles in PERMISSIONS.items() if role in roles]
