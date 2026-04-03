"""RBAC — Role-Based Access Control.

Roles: ADMIN, CRO, ANALYST, REGULATOR
"""
from __future__ import annotations

from fastapi import HTTPException
from src.services.auth_service import ROLE_PERMISSIONS


def enforce_permission(role: str, permission: str) -> None:
    """Raise 403 if role lacks the required permission."""
    perms = ROLE_PERMISSIONS.get(role.upper(), set())
    if permission not in perms:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' does not have permission '{permission}'",
        )


def get_role_from_request(request) -> str:
    """Alias — delegates to auth module."""
    from src.api.auth import get_role_from_request as _get
    return _get(request)
