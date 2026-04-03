"""JWT Authentication Service — Impact Observatory.

Roles:
    CRO        — Chief Risk Officer: full access (all runs, all reports, approve/reject)
    ANALYST    — Risk Analyst: run scenarios, view all reports
    REGULATOR  — External Regulator: read-only regulatory reports only
    ADMIN      — Platform Admin: user management + full access

Token format:
    {
        "sub": "user_id",
        "email": "user@example.com",
        "role": "CRO|ANALYST|REGULATOR|ADMIN",
        "org": "organization_id",
        "exp": unix_timestamp,
        "iat": unix_timestamp
    }
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Literal

logger = logging.getLogger(__name__)

Role = Literal["CRO", "ANALYST", "REGULATOR", "ADMIN"]

# Permissions per role
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "ADMIN": {
        "run:create", "run:read", "run:financial", "run:banking",
        "run:insurance", "run:fintech", "run:decision", "run:explanation",
        "run:business_impact", "run:timeline", "run:regulatory",
        "report:executive", "report:analyst", "report:regulatory",
        "action:approve", "action:reject",
        "audit:read", "audit:stats",
        "admin:users",
    },
    "CRO": {
        "run:create", "run:read", "run:financial", "run:banking",
        "run:insurance", "run:fintech", "run:decision", "run:explanation",
        "run:business_impact", "run:timeline", "run:regulatory",
        "report:executive", "report:analyst", "report:regulatory",
        "action:approve", "action:reject",
        "audit:stats",
    },
    "ANALYST": {
        "run:create", "run:read", "run:financial", "run:banking",
        "run:insurance", "run:fintech", "run:decision", "run:explanation",
        "run:business_impact", "run:timeline", "run:regulatory",
        "report:executive", "report:analyst",
    },
    "REGULATOR": {
        "run:read",
        "run:banking", "run:insurance",
        "report:regulatory",
        "audit:read", "audit:stats",
    },
}

# JWT config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "io-dev-secret-change-in-prod-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def _try_import_jwt():
    """Try jose first, fallback to PyJWT."""
    try:
        from jose import jwt as jose_jwt, JWTError
        return "jose", jose_jwt, JWTError
    except ImportError:
        pass
    try:
        import jwt as pyjwt
        return "pyjwt", pyjwt, Exception
    except ImportError:
        return None, None, None


def create_token(
    user_id: str,
    email: str,
    role: Role,
    org: str = "default",
    expire_hours: int = JWT_EXPIRE_HOURS,
) -> str:
    """Create a signed JWT token."""
    lib, jwt_lib, _ = _try_import_jwt()
    if not lib:
        raise RuntimeError("No JWT library available. Install python-jose or PyJWT.")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "org": org,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expire_hours)).timestamp()),
    }

    if lib == "jose":
        return jwt_lib.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    else:
        return jwt_lib.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT. Returns payload or None if invalid."""
    lib, jwt_lib, JWTError = _try_import_jwt()
    if not lib:
        return None
    try:
        if lib == "jose":
            return jwt_lib.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        else:
            return jwt_lib.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        logger.debug("JWT verify failed: %s", e)
        return None


def get_permissions(role: str) -> set[str]:
    """Get permission set for a role."""
    return ROLE_PERMISSIONS.get(role.upper(), set())


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_permissions(role)


# ── Demo users (dev mode — replace with DB in production) ──────────────────────
DEMO_USERS: dict[str, dict] = {
    "cro@observatory.io": {
        "id": "usr_cro_001",
        "email": "cro@observatory.io",
        "password_hash": "demo",  # plaintext for dev — use bcrypt in prod
        "role": "CRO",
        "org": "gcc_observatory",
        "name": "Chief Risk Officer",
    },
    "analyst@observatory.io": {
        "id": "usr_analyst_001",
        "email": "analyst@observatory.io",
        "password_hash": "demo",
        "role": "ANALYST",
        "org": "gcc_observatory",
        "name": "Risk Analyst",
    },
    "regulator@observatory.io": {
        "id": "usr_reg_001",
        "email": "regulator@observatory.io",
        "password_hash": "demo",
        "role": "REGULATOR",
        "org": "gcc_observatory",
        "name": "Regulatory Observer",
    },
    "admin@observatory.io": {
        "id": "usr_admin_001",
        "email": "admin@observatory.io",
        "password_hash": "demo",
        "role": "ADMIN",
        "org": "gcc_observatory",
        "name": "Platform Admin",
    },
}


def authenticate_user(email: str, password: str) -> dict | None:
    """Authenticate user by email+password. Returns user dict or None."""
    user = DEMO_USERS.get(email)
    if not user:
        return None
    # Dev mode: accept "demo" password for all users
    # Production: use bcrypt.checkpw(password.encode(), user["password_hash"])
    if password != user["password_hash"]:
        return None
    return user
