"""Authentication for the Impact Observatory API.

Supports two auth methods (in priority order):
  1. Bearer JWT token — role-aware, production auth
  2. X-API-Key header — legacy dev/service key

If neither is provided and api_key is unset in settings → dev mode (ANALYST role).
"""

from __future__ import annotations

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.services.auth_service import verify_token, ROLE_PERMISSIONS

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> str:
    """Dependency: validates X-API-Key OR Bearer JWT.

    Returns the role string for use in RBAC checks.
    """
    # 1. Try Bearer JWT first
    if credentials and credentials.scheme.lower() == "bearer":
        payload = verify_token(credentials.credentials)
        if payload:
            return payload.get("role", "ANALYST")
        raise HTTPException(status_code=401, detail="Invalid or expired JWT token")

    # 2. Try X-API-Key
    if api_key:
        if not settings.api_key or api_key == settings.api_key:
            return "CRO"  # API keys get CRO-level access
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 3. Dev mode — no auth configured
    if not settings.api_key:
        return "CRO"  # dev mode full access

    raise HTTPException(status_code=401, detail="Authentication required. Provide Bearer token or X-API-Key.")


def get_role_from_request(request: Request) -> str:
    """Extract role from request state (set by require_api_key dependency)."""
    # Try Authorization header JWT
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = verify_token(token)
        if payload:
            return payload.get("role", "ANALYST")

    # Try X-API-Key
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        if not settings.api_key or api_key == settings.api_key:
            return "CRO"

    # Dev mode
    if not settings.api_key:
        return "CRO"

    return "ANALYST"  # lowest safe default
