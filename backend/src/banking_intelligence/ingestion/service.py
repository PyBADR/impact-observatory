"""
Banking Intelligence — Ingestion Service
==========================================
Validation-first ingestion pipeline that:
1. Validates incoming data against Pydantic schemas
2. Computes dedup keys
3. Checks for duplicates
4. Writes to graph (Neo4j) and optionally to tabular store (PostgreSQL)
5. Returns structured ingestion results with lineage

Every ingestion preserves source lineage and is fully auditable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.banking_intelligence.schemas.entities import (
    BaseEntity,
    ENTITY_TYPE_MAP,
    ValidationStatus,
)
from src.banking_intelligence.schemas.edges import BaseEdge, EDGE_TYPE_MAP, EdgeType
from src.banking_intelligence.ingestion.dedup import DedupRegistry


# ─── Ingestion Result ──────────────────────────────────────────────────────

class IngestionAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    REJECTED_VALIDATION = "rejected_validation"


class IngestionResult(BaseModel):
    """Result of a single entity or edge ingestion."""
    canonical_id: str
    entity_type: str
    action: IngestionAction
    dedup_key: str
    validation_errors: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source_system: Optional[str] = None


class BatchIngestionResult(BaseModel):
    """Summary of a batch ingestion operation."""
    total_submitted: int
    created: int = 0
    updated: int = 0
    skipped_duplicate: int = 0
    rejected_validation: int = 0
    results: list[IngestionResult] = Field(default_factory=list)
    duration_ms: Optional[float] = None


# ─── Ingestion Service ─────────────────────────────────────────────────────

class IngestionService:
    """
    Validation-first ingestion pipeline.

    Usage:
        service = IngestionService(graph_writer=writer)
        result = await service.ingest_entity("bank", raw_data)
    """

    def __init__(
        self,
        graph_writer=None,
        dedup_registry: Optional[DedupRegistry] = None,
    ):
        self._writer = graph_writer
        self._dedup = dedup_registry or DedupRegistry()

    # ── Entity Ingestion ────────────────────────────────────────────────

    async def ingest_entity(
        self,
        entity_type: str,
        data: dict[str, Any],
    ) -> IngestionResult:
        """
        Validate, deduplicate, and persist a single entity.

        Steps:
          1. Resolve schema class from entity_type
          2. Validate data against Pydantic schema
          3. Compute dedup key
          4. Check for existing entity with same dedup key
          5. Write to graph (MERGE = create or update)
          6. Return structured result
        """
        # Step 1: Resolve schema
        schema_cls = ENTITY_TYPE_MAP.get(entity_type)
        if not schema_cls:
            return IngestionResult(
                canonical_id=data.get("canonical_id", "unknown"),
                entity_type=entity_type,
                action=IngestionAction.REJECTED_VALIDATION,
                dedup_key="",
                validation_errors=[f"Unknown entity type: {entity_type}"],
            )

        # Step 2: Validate
        try:
            entity = schema_cls.model_validate(data)
        except Exception as e:
            return IngestionResult(
                canonical_id=data.get("canonical_id", "unknown"),
                entity_type=entity_type,
                action=IngestionAction.REJECTED_VALIDATION,
                dedup_key="",
                validation_errors=[str(e)],
            )

        # Step 3+4: Dedup check
        is_new = self._dedup.register(entity_type, entity.dedup_key)
        action = IngestionAction.CREATED if is_new else IngestionAction.UPDATED

        # Step 5: Write to graph
        if self._writer:
            try:
                await self._writer.write_entity(entity)
            except Exception as e:
                return IngestionResult(
                    canonical_id=entity.canonical_id,
                    entity_type=entity_type,
                    action=IngestionAction.REJECTED_VALIDATION,
                    dedup_key=entity.dedup_key,
                    validation_errors=[f"Graph write failed: {e}"],
                )

        # Step 6: Return result
        return IngestionResult(
            canonical_id=entity.canonical_id,
            entity_type=entity_type,
            action=action,
            dedup_key=entity.dedup_key,
            source_system=entity.source_metadata.source_system,
        )

    # ── Edge Ingestion ──────────────────────────────────────────────────

    async def ingest_edge(
        self,
        edge_type: str,
        data: dict[str, Any],
    ) -> IngestionResult:
        """Validate and persist a single edge."""
        try:
            et = EdgeType(edge_type)
        except ValueError:
            return IngestionResult(
                canonical_id=f"{data.get('from_entity_id', '?')}→{data.get('to_entity_id', '?')}",
                entity_type=edge_type,
                action=IngestionAction.REJECTED_VALIDATION,
                dedup_key="",
                validation_errors=[f"Unknown edge type: {edge_type}"],
            )

        schema_cls = EDGE_TYPE_MAP.get(et)
        if not schema_cls:
            return IngestionResult(
                canonical_id=f"{data.get('from_entity_id', '?')}→{data.get('to_entity_id', '?')}",
                entity_type=edge_type,
                action=IngestionAction.REJECTED_VALIDATION,
                dedup_key="",
                validation_errors=[f"No schema for edge type: {edge_type}"],
            )

        try:
            edge = schema_cls.model_validate(data)
        except Exception as e:
            return IngestionResult(
                canonical_id=f"{data.get('from_entity_id', '?')}→{data.get('to_entity_id', '?')}",
                entity_type=edge_type,
                action=IngestionAction.REJECTED_VALIDATION,
                dedup_key="",
                validation_errors=[str(e)],
            )

        is_new = self._dedup.register("edge", edge.merge_key)
        action = IngestionAction.CREATED if is_new else IngestionAction.UPDATED

        if self._writer:
            try:
                await self._writer.write_edge(edge)
            except Exception as e:
                return IngestionResult(
                    canonical_id=f"{edge.from_entity_id}→{edge.to_entity_id}",
                    entity_type=edge_type,
                    action=IngestionAction.REJECTED_VALIDATION,
                    dedup_key=edge.merge_key,
                    validation_errors=[f"Graph write failed: {e}"],
                )

        return IngestionResult(
            canonical_id=f"{edge.from_entity_id}→{edge.to_entity_id}",
            entity_type=edge_type,
            action=action,
            dedup_key=edge.merge_key,
        )

    # ── Batch Ingestion ─────────────────────────────────────────────────

    async def ingest_entities_batch(
        self,
        entity_type: str,
        records: list[dict[str, Any]],
    ) -> BatchIngestionResult:
        """Ingest a batch of entities of the same type."""
        import time
        start = time.monotonic()

        results: list[IngestionResult] = []
        for record in records:
            result = await self.ingest_entity(entity_type, record)
            results.append(result)

        elapsed = (time.monotonic() - start) * 1000

        return BatchIngestionResult(
            total_submitted=len(records),
            created=sum(1 for r in results if r.action == IngestionAction.CREATED),
            updated=sum(1 for r in results if r.action == IngestionAction.UPDATED),
            skipped_duplicate=sum(1 for r in results if r.action == IngestionAction.SKIPPED_DUPLICATE),
            rejected_validation=sum(1 for r in results if r.action == IngestionAction.REJECTED_VALIDATION),
            results=results,
            duration_ms=elapsed,
        )
