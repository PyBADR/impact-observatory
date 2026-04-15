"""
Impact Observatory | مرصد الأثر
Signal Preview Endpoint — dev/test-only internal endpoint.

GET /internal/signal-snapshots/preview

Returns signal snapshot preview data from local RSS fixture.
Gated by ENABLE_DEV_SIGNAL_PREVIEW feature flag.

When flag is false (default, production):
  → Returns 404 with explanation.

When flag is true (dev/test):
  → Returns snapshot preview from local fixture.
  → ZERO network calls.
  → ZERO scoring impact.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.signal_ingestion.feature_flags import is_dev_signal_preview_enabled
from src.signal_ingestion.preview_service import get_dev_preview


router = APIRouter(prefix="/internal/signal-snapshots", tags=["internal"])


@router.get("/preview")
async def signal_snapshot_preview():
    """Dev-only signal snapshot preview.

    Returns 404 when ENABLE_DEV_SIGNAL_PREVIEW is not true.
    Returns fixture-based snapshots when enabled.
    """
    if not is_dev_signal_preview_enabled():
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Signal preview is not enabled.",
                "hint": "Set ENABLE_DEV_SIGNAL_PREVIEW=true in your environment for dev/test.",
                "production_safe": True,
            },
        )

    result = get_dev_preview()
    return JSONResponse(content=result)
