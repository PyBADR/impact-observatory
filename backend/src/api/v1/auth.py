"""v1 Auth API — JWT login/refresh endpoints.

POST /api/v1/auth/login     — email + password → JWT token
POST /api/v1/auth/refresh   — existing token → new token
GET  /api/v1/auth/me        — current user info
GET  /api/v1/auth/roles     — available roles and permissions
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.auth_service import authenticate_user, create_token, verify_token, ROLE_PERMISSIONS

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["cro@observatory.io"])
    password: str = Field(..., examples=["demo"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    name: str
    expires_in: int = 86400  # 24 hours in seconds


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    org: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate with email + password, receive JWT.

    Demo credentials:
    - cro@observatory.io / demo       (full access)
    - analyst@observatory.io / demo   (run + read)
    - regulator@observatory.io / demo (read-only regulatory)
    - admin@observatory.io / demo     (admin)
    """
    user = authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        org=user["org"],
    )

    return LoginResponse(
        access_token=token,
        role=user["role"],
        email=user["email"],
        name=user["name"],
    )


@router.post("/refresh")
async def refresh_token(body: dict):
    """Refresh an existing token. Accepts {"token": "..."}."""
    token = body.get("token", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    new_token = create_token(
        user_id=payload["sub"],
        email=payload["email"],
        role=payload["role"],
        org=payload.get("org", "default"),
    )
    return {"access_token": new_token, "token_type": "bearer"}


@router.get("/me")
async def me(token: str):
    """Get current user info from token. Pass as query param ?token=... for simplicity."""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "role": payload["role"],
        "org": payload.get("org"),
        "permissions": list(ROLE_PERMISSIONS.get(payload["role"], set())),
    }


@router.get("/roles")
async def list_roles():
    """List all roles and their permissions."""
    return {
        "roles": {
            role: {
                "permissions": sorted(list(perms)),
                "description": {
                    "ADMIN": "Platform administrator — full access + user management",
                    "CRO": "Chief Risk Officer — full access to all risk reports and decisions",
                    "ANALYST": "Risk Analyst — run scenarios + view executive and analyst reports",
                    "REGULATOR": "External Regulator — read-only access to regulatory reports",
                }.get(role, ""),
            }
            for role, perms in ROLE_PERMISSIONS.items()
        }
    }
