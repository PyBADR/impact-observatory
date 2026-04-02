"""X-API-Key header authentication for the GCC Decision Intelligence API."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.core.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """Dependency that validates the X-API-Key header.

    If settings.api_key is empty/unset, auth is disabled (dev mode).
    """
    if not settings.api_key:
        return "dev-mode"
    if api_key is None or api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
