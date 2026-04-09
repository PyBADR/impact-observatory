"""Graph Expansion Service — Orchestrates signal-to-KG transformation.

Connects the Graph Mapper (pure mapping logic) with the Graph Writer
(Neo4j or in-memory persistence) and the existing GraphBrainService.

Now supports HYBRID mode: rule-based + AI-driven mapping via HybridGraphMapper.
The AI path is off by default and controlled via Settings.ai_extraction_enabled.

Architecture Layer: Features → Models (Layer 2-3)
Owner: Graph Expansion Pipeline
Consumers: Signal Ingestion API, Batch Processor

Integration Points:
  - Input:  MacroSignal (v1 schema from schemas/macro_signal_schema.py)
  - Output: GraphExpansionResult (mapping + write results for API response)
  - Store:  In-memory GraphStore (existing) + Neo4j (optional)
  - AI:     HybridGraphMapper (optional, config-driven)

This service is backward-compatible with the existing GraphBrainService.
It does NOT replace it — it extends the ingestion path with richer mapping.
"""

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.graph_brain.graph_mapper import MappingResult, map_signal_to_graph
from src.graph_brain.neo4j_graph_writer import InMemoryGraphWriter, WriteResult
from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.graph_brain.types import GraphEntityType

logger = logging.getLogger("graph_brain.expansion")


# ═══════════════════════════════════════════════════════════════════════════════
# Expansion Result — full pipeline output
# ═══════════════════════════════════════════════════════════════════════════════

class GraphExpansionResult(BaseModel):
    """Full output of the graph expansion pipeline.

    Combines mapping decisions with write results for API transparency.
    """
    signal_id: str = ""
    mapping: dict = Field(default_factory=dict, description="MappingResult.summary()")
    write: dict = Field(default_factory=dict, description="WriteResult.summary()")
    store_stats: dict = Field(default_factory=dict, description="Current graph store stats")
    hybrid_stats: dict = Field(default_factory=dict, description="Hybrid merge stats (if AI enabled)")
    total_duration_ms: float = 0.0
    success: bool = True
    errors: list[str] = Field(default_factory=list)
    ai_enabled: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Service
# ═══════════════════════════════════════════════════════════════════════════════

class GraphExpansionService:
    """Orchestrates the full signal → graph expansion pipeline.

    Steps:
      1. map_signal_to_graph() — pure mapping, no side effects
         OR HybridGraphMapper.map_signal() — rule + AI merge
      2. InMemoryGraphWriter.write_mapping_result() — persist to in-memory store
      3. (Optional) Neo4jGraphWriter.write_mapping_result() — persist to Neo4j
      4. Return GraphExpansionResult with full observability
    """

    def __init__(
        self,
        graph_brain: Optional[GraphBrainService] = None,
        neo4j_session=None,
    ) -> None:
        self._graph_brain = graph_brain or get_graph_brain_service()
        self._neo4j_session = neo4j_session  # Optional: set if Neo4j available
        self._hybrid_mapper = None

        # Initialize hybrid mapper from config
        self._init_hybrid_mapper()

    def _init_hybrid_mapper(self) -> None:
        """Initialize the HybridGraphMapper from application settings.

        Lazy import to avoid circular dependencies and keep the
        rule-only path zero-cost when AI is disabled.
        """
        try:
            from src.core.config import settings

            if not settings.ai_extraction_enabled:
                logger.info("AI extraction disabled — using rule-only mapper")
                return

            from src.graph_brain.hybrid_graph_mapper import (
                HybridGraphMapper,
                HybridMergeConfig,
            )
            from src.graph_brain.ai_entity_extractor import (
                MockLLMBackend,
                OllamaBackend,
            )

            # Select backend based on config
            if settings.ai_use_mock_backend:
                backend = MockLLMBackend()
                logger.info("AI extraction enabled with MockLLMBackend (test mode)")
            else:
                backend = OllamaBackend(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    timeout_seconds=settings.ollama_timeout_seconds,
                    temperature=settings.ollama_temperature,
                )
                logger.info(
                    "AI extraction enabled: Ollama %s @ %s",
                    settings.ollama_model, settings.ollama_base_url,
                )

            merge_config = HybridMergeConfig(
                standard_threshold=settings.ai_merge_standard_threshold,
                low_confidence_threshold=settings.ai_merge_quarantine_threshold,
                max_ai_nodes_per_signal=settings.ai_max_nodes_per_signal,
            )

            self._hybrid_mapper = HybridGraphMapper(
                ai_enabled=True,
                backend=backend,
                merge_config=merge_config,
                min_entity_confidence=settings.ai_min_entity_confidence,
                min_relationship_confidence=settings.ai_min_relationship_confidence,
            )

        except Exception as exc:
            logger.warning(
                "Failed to initialize hybrid mapper — falling back to rule-only: %s", exc,
            )
            self._hybrid_mapper = None

    @property
    def graph_brain(self) -> GraphBrainService:
        return self._graph_brain

    @property
    def ai_enabled(self) -> bool:
        return self._hybrid_mapper is not None

    def expand_signal(self, signal_dict: dict) -> GraphExpansionResult:
        """Execute the full expansion pipeline for a single MacroSignal.

        Args:
            signal_dict: MacroSignal serialized via .model_dump()

        Returns:
            GraphExpansionResult with mapping decisions, write counts, and store stats.
        """
        t0 = time.monotonic()
        result = GraphExpansionResult(
            signal_id=signal_dict.get("signal_id", ""),
            ai_enabled=self.ai_enabled,
        )

        try:
            # Step 1: Map signal to graph elements (hybrid or rule-only)
            hybrid_result = None
            if self._hybrid_mapper is not None:
                hybrid_result = self._hybrid_mapper.map_signal(signal_dict)
                mapping = hybrid_result.mapping
                result.hybrid_stats = hybrid_result.merge_stats.summary()
            else:
                mapping: MappingResult = map_signal_to_graph(signal_dict)

            result.mapping = mapping.summary()

            if mapping.warnings:
                result.errors.extend(mapping.warnings)

            # Step 2: Write to in-memory GraphStore
            writer = InMemoryGraphWriter(self._graph_brain.store)
            write_result: WriteResult = writer.write_mapping_result(mapping)
            result.write = write_result.summary()

            if write_result.errors:
                result.errors.extend(write_result.errors)

            # Step 3: Optionally write to Neo4j (async not supported in sync call)
            # Neo4j writes happen via the async API route or batch processor
            # This is intentionally left as a hook point

            # Step 4: Capture store stats
            result.store_stats = self._graph_brain.stats()
            result.success = write_result.success and len(mapping.warnings) == 0

        except Exception as exc:
            logger.error("Graph expansion failed for %s: %s", result.signal_id, exc)
            result.errors.append(f"Expansion pipeline error: {exc}")
            result.success = False

        result.total_duration_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "Graph expansion for %s: %s nodes, %s edges, %.1fms — %s%s",
            result.signal_id,
            result.mapping.get("nodes_mapped", 0),
            result.mapping.get("edges_mapped", 0),
            result.total_duration_ms,
            "OK" if result.success else f"{len(result.errors)} errors",
            " [AI+Rule]" if self.ai_enabled else " [Rule-only]",
        )
        return result

    def expand_batch(self, signals: list[dict]) -> list[GraphExpansionResult]:
        """Expand a batch of MacroSignal dicts. Returns one result per signal."""
        return [self.expand_signal(sig) for sig in signals]

    def get_expansion_stats(self) -> dict[str, Any]:
        """Return current expansion pipeline stats."""
        stats: dict[str, Any] = {
            "graph_store": self._graph_brain.stats(),
            "neo4j_connected": self._neo4j_session is not None,
            "ai_enabled": self.ai_enabled,
        }
        if self._hybrid_mapper is not None:
            stats["ai_available"] = self._hybrid_mapper.ai_available
        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[GraphExpansionService] = None


def get_graph_expansion_service() -> GraphExpansionService:
    """Get or create the global GraphExpansionService singleton."""
    global _instance
    if _instance is None:
        _instance = GraphExpansionService()
    return _instance
