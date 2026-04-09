"""Macro Intelligence Layer — Propagation API Routes (v1).

Endpoints:
  POST   /api/v1/macro/propagate                  — propagate a signal by registry_id
  POST   /api/v1/macro/propagate/inline            — submit + propagate in one call
  GET    /api/v1/macro/propagation/{result_id}     — get propagation result
  GET    /api/v1/macro/propagation/signal/{sig_id} — get result by signal_id
  GET    /api/v1/macro/propagation                 — list propagation results
  GET    /api/v1/macro/propagation/stats            — propagation statistics
  POST   /api/v1/macro/causal/{registry_id}        — get causal mapping only (no propagation)

No business logic here. Routes delegate to PropagationService + MacroSignalService.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.macro.macro_enums import SignalStatus
from src.macro.macro_schemas import MacroSignalInput
from src.macro.macro_signal_service import MacroSignalService, get_signal_service
from src.macro.causal.causal_schemas import CausalMapping
from src.macro.propagation.propagation_schemas import (
    PropagationResponse,
    PropagationResult,
    PropagationSummary,
)
from src.macro.propagation.propagation_service import (
    PropagationService,
    get_propagation_service,
)

router = APIRouter(prefix="/api/v1/macro", tags=["macro-propagation"])


# ── Request/Response Models ──────────────────────────────────────────────────

class PropagateByIdRequest(BaseModel):
    registry_id: UUID = Field(..., description="Signal registry ID to propagate")
    max_depth: int = Field(default=5, ge=1, le=8)
    min_severity: float = Field(default=0.05, ge=0.0, le=1.0)


class PropagateInlineRequest(BaseModel):
    signal: MacroSignalInput
    max_depth: int = Field(default=5, ge=1, le=8)
    min_severity: float = Field(default=0.05, ge=0.0, le=1.0)


class PropagationListResponse(BaseModel):
    total: int
    offset: int
    limit: int
    results: list[PropagationSummary]


class CausalMappingResponse(BaseModel):
    mapping: CausalMapping
    message: str = "Causal mapping complete"


# ── POST /propagate — Propagate by Registry ID ──────────────────────────────

@router.post(
    "/propagate",
    response_model=PropagationResponse,
    status_code=200,
    summary="Propagate a registered signal through the causal graph",
)
async def propagate_signal(
    req: PropagateByIdRequest,
    signal_svc: MacroSignalService = Depends(get_signal_service),
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    entry = signal_svc.get_by_registry_id(req.registry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Signal not found in registry")

    if entry.status == SignalStatus.REJECTED:
        raise HTTPException(status_code=422, detail="Cannot propagate a rejected signal")

    result = prop_svc.propagate_signal(
        entry.signal,
        max_depth=req.max_depth,
        min_severity=req.min_severity,
    )
    return PropagationResponse(result=result)


# ── POST /propagate/inline — Submit + Propagate ─────────────────────────────
# NOTE: Literal path MUST be declared before /propagate/{signal_id} to avoid
# FastAPI matching "inline" as a UUID path parameter.

@router.post(
    "/propagate/inline",
    response_model=PropagationResponse,
    status_code=201,
    summary="Submit a signal and propagate in one call",
)
async def propagate_inline(
    req: PropagateInlineRequest,
    signal_svc: MacroSignalService = Depends(get_signal_service),
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    # Step 1: Ingest signal
    entry, rejection, warnings = signal_svc.ingest_signal(req.signal)
    if rejection is not None:
        raise HTTPException(
            status_code=422,
            detail={
                "rejection_id": str(rejection.rejection_id),
                "errors": rejection.errors,
                "message": "Signal rejected — cannot propagate",
            },
        )

    assert entry is not None

    # Step 2: Propagate
    result = prop_svc.propagate_signal(
        entry.signal,
        max_depth=req.max_depth,
        min_severity=req.min_severity,
    )
    return PropagationResponse(result=result)


# ── POST /propagate/{signal_id} — Propagate by Signal ID ────────────────────

@router.post(
    "/propagate/{signal_id}",
    response_model=PropagationResponse,
    status_code=200,
    summary="Propagate a signal by its signal_id (looks up registry entry)",
)
async def propagate_by_signal_id(
    signal_id: UUID,
    max_depth: int = Query(5, ge=1, le=8),
    min_severity: float = Query(0.05, ge=0.0, le=1.0),
    signal_svc: MacroSignalService = Depends(get_signal_service),
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    entry = signal_svc.get_by_signal_id(signal_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Signal not found in registry")

    if entry.status == SignalStatus.REJECTED:
        raise HTTPException(status_code=422, detail="Cannot propagate a rejected signal")

    result = prop_svc.propagate_signal(
        entry.signal,
        max_depth=max_depth,
        min_severity=min_severity,
    )
    return PropagationResponse(result=result)


# ── GET /propagation/stats — Statistics ──────────────────────────────────────
# NOTE: Literal paths MUST be declared before parameterized paths to avoid
# FastAPI matching "stats" as a {result_id} UUID.

@router.get(
    "/propagation/stats",
    summary="Propagation layer statistics",
)
async def get_propagation_stats(
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    return prop_svc.get_stats()


# ── GET /propagation — List Results ──────────────────────────────────────────

@router.get(
    "/propagation",
    response_model=PropagationListResponse,
    summary="List propagation results",
)
async def list_propagation_results(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    summaries, total = prop_svc.list_results(offset=offset, limit=limit)
    return PropagationListResponse(
        total=total, offset=offset, limit=limit, results=summaries,
    )


# ── GET /propagation/by-signal/{signal_id} — Get Result by Signal ───────────

@router.get(
    "/propagation/by-signal/{signal_id}",
    response_model=PropagationResponse,
    summary="Get propagation result by source signal ID",
)
async def get_propagation_by_signal(
    signal_id: UUID,
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    result = prop_svc.get_result_by_signal(signal_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No propagation result for this signal")
    return PropagationResponse(result=result)


# ── GET /propagation/{result_id} — Get Result ───────────────────────────────

@router.get(
    "/propagation/{result_id}",
    response_model=PropagationResponse,
    summary="Get propagation result by ID",
)
async def get_propagation_result(
    result_id: UUID,
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    result = prop_svc.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Propagation result not found")
    return PropagationResponse(result=result)


# ── POST /causal/{registry_id} — Causal Mapping Only ────────────────────────

@router.post(
    "/causal/{registry_id}",
    response_model=CausalMappingResponse,
    summary="Get causal mapping for a signal (no propagation)",
)
async def get_causal_mapping(
    registry_id: UUID,
    signal_svc: MacroSignalService = Depends(get_signal_service),
    prop_svc: PropagationService = Depends(get_propagation_service),
):
    entry = signal_svc.get_by_registry_id(registry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Signal not found in registry")

    mapping = prop_svc.get_causal_mapping(entry.signal)
    return CausalMappingResponse(mapping=mapping)
