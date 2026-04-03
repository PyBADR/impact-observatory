"""Health check endpoint — Impact Observatory | مرصد الأثر."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint — platform identity and quick links."""
    return {
        "platform": "Impact Observatory | مرصد الأثر",
        "description": "Decision Intelligence Platform for GCC Financial Markets",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "scenarios": "/api/v1/scenarios",
            "run_pipeline": "POST /api/v1/runs",
            "docs": "/docs",
        },
    }


@router.get("/health")
async def health_check():
    """Health check for monitoring and Docker healthcheck."""
    return {
        "status": "ok",
        "service": "Impact Observatory",
        "version": "1.0.0",
        "model_version": "2.1.0",
        "engine": "SimulationEngine",
    }


@router.get("/health/feeds")
async def feeds_health():
    """Data feed status — shows ACLED/AIS/OpenSky connectivity."""
    from src.services.data_feeds import get_feed_status
    return get_feed_status()
