"""
Banking Intelligence — Entity API Endpoints
=============================================
CRUD + ingestion endpoints for the 7 entity types.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.banking_intelligence.schemas.entities import (
    ENTITY_TYPE_MAP,
    ValidationStatus,
    GCCCountryCode,
)
from src.banking_intelligence.ingestion.service import (
    IngestionService,
    IngestionResult,
    BatchIngestionResult,
    IngestionAction,
)
from src.banking_intelligence.ingestion.dedup import DedupRegistry

router = APIRouter(prefix="/banking/entities", tags=["banking-entities"])

# ── Service singleton (wired at startup) ────────────────────────────────────
_dedup = DedupRegistry()
_service = IngestionService(graph_writer=None, dedup_registry=_dedup)


def set_graph_writer(writer):
    """Called at app startup to inject the Neo4j writer."""
    global _service
    _service = IngestionService(graph_writer=writer, dedup_registry=_dedup)


# ── In-memory store for non-Neo4j mode ─────────────────────────────────────
_entity_store: dict[str, dict[str, Any]] = {}


class IngestEntityRequest(BaseModel):
    entity_type: str = Field(..., description="One of: country, authority, bank, fintech, payment_rail, scenario_trigger, decision_playbook")
    data: dict[str, Any]


class IngestBatchRequest(BaseModel):
    entity_type: str
    records: list[dict[str, Any]]


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestionResult)
async def ingest_entity(request: IngestEntityRequest):
    """Validate and ingest a single entity."""
    result = await _service.ingest_entity(request.entity_type, request.data)

    if result.action == IngestionAction.REJECTED_VALIDATION:
        raise HTTPException(status_code=422, detail={
            "errors": result.validation_errors,
            "canonical_id": result.canonical_id,
        })

    # Store in memory for retrieval
    _entity_store[result.canonical_id] = request.data
    return result


@router.post("/ingest/batch", response_model=BatchIngestionResult)
async def ingest_entities_batch(request: IngestBatchRequest):
    """Validate and ingest a batch of entities."""
    result = await _service.ingest_entities_batch(
        request.entity_type, request.records
    )

    for r in result.results:
        if r.action in (IngestionAction.CREATED, IngestionAction.UPDATED):
            matching = [
                rec for rec in request.records
                if rec.get("canonical_id") == r.canonical_id
            ]
            if matching:
                _entity_store[r.canonical_id] = matching[0]

    return result


@router.get("/types")
async def list_entity_types():
    """List available entity types and their field schemas."""
    return {
        entity_type: {
            "fields": list(cls.model_fields.keys()),
            "required_fields": [
                name for name, field in cls.model_fields.items()
                if field.is_required()
            ],
        }
        for entity_type, cls in ENTITY_TYPE_MAP.items()
    }


@router.get("/{canonical_id}")
async def get_entity(canonical_id: str):
    """Retrieve an entity by canonical_id."""
    if canonical_id in _entity_store:
        return _entity_store[canonical_id]
    raise HTTPException(status_code=404, detail=f"Entity not found: {canonical_id}")


@router.get("/")
async def list_entities(
    entity_type: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List entities with filtering."""
    results = list(_entity_store.values())

    if entity_type:
        prefix_map = {
            "country": "country:",
            "authority": "authority:",
            "bank": "bank:",
            "fintech": "fintech:",
            "payment_rail": "rail:",
            "scenario_trigger": "trigger:",
            "decision_playbook": "playbook:",
        }
        prefix = prefix_map.get(entity_type, "")
        results = [
            r for r in results
            if r.get("canonical_id", "").startswith(prefix)
        ]

    if country_code:
        results = [
            r for r in results
            if r.get("country_code") == country_code
            or r.get("iso_alpha2") == country_code
        ]

    if validation_status:
        results = [
            r for r in results
            if r.get("validation_status") == validation_status
        ]

    total = len(results)
    results = results[offset:offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": results,
    }


@router.get("/dedup/stats")
async def dedup_stats():
    """Return dedup registry statistics."""
    return _dedup.stats()


@router.post("/seed")
async def seed_entities():
    """Load GCC full population seed data into in-memory store.

    Loads 89 entities (6 countries, 11 authorities, 20 banks,
    14 fintechs, 13 payment rails) and 52 edges from
    gcc_full_population.json.
    """
    from src.banking_intelligence.seed.loader import seed_entity_store
    counts = seed_entity_store(_entity_store)
    if "error" in counts:
        raise HTTPException(status_code=500, detail="Seed file not found")
    total = sum(v for k, v in counts.items() if k != "edges")
    return {
        "status": "seeded",
        "total_entities": total,
        "total_edges": counts.get("edges", 0),
        "breakdown": counts,
    }
