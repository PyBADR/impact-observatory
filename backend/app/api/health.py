"""Health check endpoints"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from app.api.models import HealthResponse, VersionResponse
from app.api.auth import api_key_auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service_name="Impact Observatory",
        version="1.0.0"
    )


@router.get("/version", response_model=VersionResponse, tags=["Health"])
async def get_version(api_key: str = Depends(api_key_auth)):
    """
    Get API version information
    
    Args:
        api_key: API key for authentication
        
    Returns:
        VersionResponse with version details
    """
    return VersionResponse(
        version="1.0.0",
        service="Impact Observatory",
        timestamp=datetime.utcnow(),
        build_date="2026-03-31",
        environment="production"
    )
