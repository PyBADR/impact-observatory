"""
Health check endpoints — V1 (no auth dependency).
Auth guard deferred to V2 RBAC implementation.
"""

import logging
from datetime import datetime

from fastapi import APIRouter
from app.api.models import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service_name="Impact Observatory",
        version="4.0.0",
    )


@router.get("/version", tags=["Health"])
async def get_version():
    """
    Get API version information.
    V1: no auth guard — deferred to V2 RBAC.
    """
    return {
        "version": "4.0.0",
        "service": "Impact Observatory | مرصد الأثر",
        "timestamp": datetime.utcnow().isoformat(),
        "build_date": "2026-04-02",
        "environment": "v1-in-memory",
    }
