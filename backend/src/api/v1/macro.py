"""Macro Intelligence Layer — API Routes (v1).

Endpoints:
  POST   /api/v1/macro/signals          — submit a new signal
  GET    /api/v1/macro/signals           — list signals (filtered, paginated)
  GET    /api/v1/macro/signals/{id}      — get signal by registry_id
  GET    /api/v1/macro/rejections        — list recent rejections (audit)
  GET    /api/v1/macro/stats             — registry statistics
  POST   /api/v1/macro/expire            — trigger expiration sweep

No business logic here. Routes delegate entirely to MacroSignalService.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalSeverity,
    SignalSource,
    SignalStatus,
)
from src.macro.macro_schemas import (
    MacroSignalInput,
    SignalIntakeResponse,
    SignalListResponse,
    SignalQueryResponse,
    SignalRejection,
    SignalRejectionResponse,
    SignalRegistryEntry,
)
from src.macro.macro_signal_service import MacroSignalService, get_signal_service

router = APIRouter(prefix="/api/v1/macro", tags=["macro-intelligence"])


# ── POST /signals — Submit Signal ────────────────────────────────────────────

@router.post(
    "/signals",
    response_model=SignalIntakeResponse | SignalRejectionResponse,
    status_code=201,
    summary="Submit a macro signal for intake",
    description="Validates, normalizes, and registers a signal. Returns 201 on success, 422 on rejection.",
)
async def submit_signal(
    payload: MacroSignalInput,
    service: MacroSignalService = Depends(get_signal_service),
):
    entry, rejection, warnings = service.ingest_signal(payload)

    if rejection is not None:
        raise HTTPException(
            status_code=422,
            detail={
                "rejection_id": str(rejection.rejection_id),
                "errors": rejection.errors,
                "message": "Signal rejected — validation failed",
            },
        )

    # entry is guaranteed non-None here
    assert entry is not None
    return SignalIntakeResponse(
        signal_id=entry.signal.signal_id,
        registry_id=entry.registry_id,
        status=entry.status,
        severity_level=entry.signal.severity_level,
        content_hash=entry.signal.content_hash,
        message=(
            "Signal accepted and registered"
            + (f" | warnings: {warnings}" if warnings else "")
        ),
    )


# ── GET /signals — List Signals ──────────────────────────────────────────────

@router.get(
    "/signals",
    response_model=SignalListResponse,
    summary="List registered signals",
    description="Filtered, paginated listing of signals in the registry.",
)
async def list_signals(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    source: Optional[SignalSource] = Query(None),
    severity: Optional[SignalSeverity] = Query(None),
    region: Optional[GCCRegion] = Query(None),
    domain: Optional[ImpactDomain] = Query(None),
    status: Optional[SignalStatus] = Query(None),
    service: MacroSignalService = Depends(get_signal_service),
):
    entries, total = service.list_signals(
        offset=offset,
        limit=limit,
        source=source,
        severity=severity,
        region=region,
        domain=domain,
        status=status,
    )
    return SignalListResponse(
        total=total,
        offset=offset,
        limit=limit,
        entries=entries,
    )


# ── GET /signals/{registry_id} — Get Signal ─────────────────────────────────

@router.get(
    "/signals/{registry_id}",
    response_model=SignalQueryResponse,
    summary="Get signal by registry ID",
)
async def get_signal(
    registry_id: UUID,
    service: MacroSignalService = Depends(get_signal_service),
):
    entry = service.get_by_registry_id(registry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalQueryResponse(entry=entry)


# ── GET /rejections — Audit Trail ────────────────────────────────────────────

@router.get(
    "/rejections",
    response_model=list[SignalRejection],
    summary="List recent signal rejections",
    description="Returns recent rejections for audit purposes.",
)
async def list_rejections(
    limit: int = Query(50, ge=1, le=200),
    service: MacroSignalService = Depends(get_signal_service),
):
    return service.get_rejections(limit=limit)


# ── GET /stats — Registry Health ─────────────────────────────────────────────

@router.get(
    "/stats",
    summary="Registry statistics",
    description="Counts by status, severity, and source.",
)
async def get_stats(
    service: MacroSignalService = Depends(get_signal_service),
):
    return service.get_stats()


# ── POST /expire — Trigger Expiration ────────────────────────────────────────

@router.post(
    "/expire",
    summary="Expire stale signals",
    description="Marks signals past their TTL as expired. Returns count.",
)
async def expire_signals(
    service: MacroSignalService = Depends(get_signal_service),
):
    count = service.expire_stale_signals()
    return {"expired_count": count, "message": f"{count} signal(s) expired"}
