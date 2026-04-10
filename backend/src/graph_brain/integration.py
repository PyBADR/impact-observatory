"""Graph Brain Integration Pack A — Pipeline Orchestrator.

Top-level integration module that wires Graph Brain into the
existing causal→propagation pipeline. This is the ONLY module
that Pack 2 callers need to interact with.

Data flow:
  NormalizedSignal
  → [Auto-ingest into Graph]
  → map_signal_to_causal_entry()                    (Pack 2, unchanged)
  → [Graph enrich causal entry]
  → discover_activated_channels()                    (Pack 2, unchanged)
  → propagate()                                      (Pack 2, unchanged)
  → [Graph enrich propagation result]
  → GraphEnrichedPropagationResult                   (new wrapper)

Architecture:
  - DOES NOT modify Pack 2 functions
  - Wraps existing pipeline with optional graph enrichment
  - Feature-flagged: disable graph = exact Pack 2 behavior
  - Fail-safe: any graph error → fallback to pure Pack 2 output

Usage:
  from src.graph_brain.integration import graph_enriched_pipeline

  result = graph_enriched_pipeline(signal)
  # result.propagation_result — always present (Pack 2)
  # result.graph_enrichment   — present if graph enrichment succeeded
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.graph_brain.enrichment import (
    CausalEntryEnrichment,
    ExplanationEnrichment,
    PropagationWeightEnrichment,
    enrich_causal_entry,
    enrich_explanation,
    ensure_signal_ingested,
    is_enrichment_active,
)
from src.graph_brain.ingestion import IngestionResult
from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.macro.causal.causal_mapper import (
    discover_activated_channels,
    map_signal_to_causal,
    map_signal_to_causal_entry,
)
from src.macro.causal.causal_schemas import CausalMapping
from src.macro.macro_enums import ImpactDomain
from src.macro.macro_schemas import NormalizedSignal
from src.macro.propagation.propagation_engine import propagate
from src.macro.propagation.propagation_schemas import PropagationResult

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Enriched Result Wrapper
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraphEnrichmentMetadata:
    """Metadata about what graph enrichment was applied."""
    graph_enabled: bool = False
    signal_ingested: bool = False
    ingestion_result: Optional[IngestionResult] = None
    causal_enrichment: Optional[CausalEntryEnrichment] = None
    explanation_enrichment: Optional[ExplanationEnrichment] = None
    weight_enrichments: list[PropagationWeightEnrichment] = field(default_factory=list)
    graph_reasoning_appended: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def has_enrichment(self) -> bool:
        """True if any graph enrichment was successfully applied."""
        ce = self.causal_enrichment is not None and self.causal_enrichment.has_enrichment
        ee = self.explanation_enrichment is not None and self.explanation_enrichment.has_enrichment
        return ce or ee or len(self.weight_enrichments) > 0

    def summary(self) -> dict:
        """Return a JSON-safe summary of enrichment metadata."""
        return {
            "graph_enabled": self.graph_enabled,
            "signal_ingested": self.signal_ingested,
            "causal_hints_count": (
                len(self.causal_enrichment.channel_hints)
                if self.causal_enrichment else 0
            ),
            "weight_enrichments_count": len(self.weight_enrichments),
            "explanation_fragments_count": (
                len(self.explanation_enrichment.fragments)
                if self.explanation_enrichment else 0
            ),
            "graph_reasoning_appended": self.graph_reasoning_appended,
            "errors_count": len(self.errors),
            "has_enrichment": self.has_enrichment,
        }


@dataclass
class GraphEnrichedResult:
    """Wrapper around PropagationResult with optional graph enrichment.

    The propagation_result field is ALWAYS present and is always a
    valid Pack 2 PropagationResult. The graph_enrichment field provides
    optional supplementary metadata from Graph Brain.

    API consumers can safely ignore graph_enrichment — the core result
    is self-contained.
    """
    propagation_result: PropagationResult
    causal_mapping: CausalMapping
    graph_enrichment: GraphEnrichmentMetadata = field(
        default_factory=GraphEnrichmentMetadata,
    )

    def to_api_dict(self) -> dict:
        """Convert to API-friendly dict, including graph metadata."""
        result_dict = self.propagation_result.model_dump(mode="json")
        result_dict["graph_enrichment"] = self.graph_enrichment.summary()
        return result_dict


# ══════════════════════════════════════════════════════════════════════════════
# Main Integration Pipeline
# ══════════════════════════════════════════════════════════════════════════════

def graph_enriched_pipeline(
    signal: NormalizedSignal,
    max_causal_depth: int = 4,
    max_propagation_depth: int = 5,
    min_severity: float = 0.05,
    graph_service: Optional[GraphBrainService] = None,
) -> GraphEnrichedResult:
    """Run the full causal→propagation pipeline with optional graph enrichment.

    This is the primary integration entry point. It:
      1. Runs Pack 2 causal mapping (unchanged)
      2. Optionally ingests the signal into Graph Brain
      3. Optionally enriches the causal entry with graph hints
      4. Runs Pack 2 propagation (unchanged)
      5. Optionally enriches the propagation result with graph reasoning
      6. Returns a GraphEnrichedResult wrapping everything

    If graph enrichment is disabled or fails at any step,
    the pure Pack 2 result is returned unchanged.

    Args:
        signal: The NormalizedSignal to process.
        max_causal_depth: Max depth for causal channel discovery.
        max_propagation_depth: Max depth for BFS propagation.
        min_severity: Minimum severity threshold for propagation.
        graph_service: Optional GraphBrainService instance.
            If None, uses the singleton.

    Returns:
        GraphEnrichedResult with propagation result + graph metadata.
    """
    metadata = GraphEnrichmentMetadata()

    # ── Step 1: Pack 2 Causal Mapping (always runs) ────────────────────────
    mapping = map_signal_to_causal(signal, max_depth=max_causal_depth)

    # ── Step 2: Graph enrichment (if enabled) ──────────────────────────────
    if is_enrichment_active():
        metadata.graph_enabled = True

        try:
            service = graph_service or get_graph_brain_service()
            store = service.store

            # 2a. Auto-ingest signal into graph
            ingest_result = ensure_signal_ingested(signal, store)
            if ingest_result is not None:
                metadata.signal_ingested = True
                metadata.ingestion_result = ingest_result

            # 2b. Enrich causal entry with graph hints
            existing_pairs = {
                (ch.from_domain.value, ch.to_domain.value)
                for ch in mapping.activated_channels
            }
            causal_enrichment = enrich_causal_entry(
                store, signal, mapping.entry_point, existing_pairs,
            )
            metadata.causal_enrichment = causal_enrichment

            if causal_enrichment.has_enrichment:
                logger.info(
                    "Graph enriched causal entry for signal %s: %s",
                    signal.signal_id, causal_enrichment,
                )

        except Exception as e:
            err_msg = f"Graph pre-propagation enrichment failed: {e}"
            logger.warning(err_msg)
            metadata.errors.append(err_msg)

    # ── Step 3: Pack 2 Propagation (always runs, uses original mapping) ────
    prop_result = propagate(
        mapping,
        max_depth=max_propagation_depth,
        min_severity=min_severity,
    )

    # ── Step 4: Post-propagation graph enrichment ──────────────────────────
    if metadata.graph_enabled:
        try:
            service = graph_service or get_graph_brain_service()
            store = service.store

            # 4a. Enrich explanation with graph reasoning
            reached_domains = [h.domain for h in prop_result.hits]
            explanation_enrichment = enrich_explanation(
                store,
                signal_id=str(signal.signal_id),
                reached_domains=reached_domains,
            )
            metadata.explanation_enrichment = explanation_enrichment

            # 4b. Append graph reasoning to hit descriptions
            if explanation_enrichment.has_enrichment:
                _append_graph_reasoning_to_hits(prop_result, explanation_enrichment, metadata)

        except Exception as e:
            err_msg = f"Graph post-propagation enrichment failed: {e}"
            logger.warning(err_msg)
            metadata.errors.append(err_msg)

    return GraphEnrichedResult(
        propagation_result=prop_result,
        causal_mapping=mapping,
        graph_enrichment=metadata,
    )


def _append_graph_reasoning_to_hits(
    result: PropagationResult,
    enrichment: ExplanationEnrichment,
    metadata: GraphEnrichmentMetadata,
) -> None:
    """Append graph reasoning to PropagationHit reasoning fields.

    This APPENDS to existing reasoning — never replaces it.
    Modifies hits in-place (PropagationResult is already created).
    """
    count = 0
    for hit in result.hits:
        fragment = enrichment.get_fragment_for_domain(hit.domain)
        if fragment is not None:
            # Append graph reasoning as a supplementary paragraph
            hit.reasoning = (
                f"{hit.reasoning}\n"
                f"  {fragment.reasoning}"
            )
            count += 1

    metadata.graph_reasoning_appended = count
    if count > 0:
        logger.info(
            "Appended graph reasoning to %d/%d propagation hits",
            count, len(result.hits),
        )


# ══════════════════════════════════════════════════════════════════════════════
# Convenience: standalone functions for partial integration
# ══════════════════════════════════════════════════════════════════════════════

def graph_enrich_causal_mapping(
    signal: NormalizedSignal,
    mapping: CausalMapping,
    graph_service: Optional[GraphBrainService] = None,
) -> CausalEntryEnrichment:
    """Standalone: enrich an existing CausalMapping with graph hints.

    Use this if you want to enrich at the causal layer only,
    without running the full pipeline.
    """
    if not is_enrichment_active("causal_entry"):
        return CausalEntryEnrichment([], [], "Causal entry enrichment disabled")

    try:
        service = graph_service or get_graph_brain_service()
        store = service.store
        ensure_signal_ingested(signal, store)

        existing_pairs = {
            (ch.from_domain.value, ch.to_domain.value)
            for ch in mapping.activated_channels
        }
        return enrich_causal_entry(store, signal, mapping.entry_point, existing_pairs)

    except Exception as e:
        logger.warning("Standalone causal enrichment failed: %s", e)
        return CausalEntryEnrichment([], [], f"Enrichment failed: {e}")


def graph_enrich_propagation_result(
    signal_id: str,
    prop_result: PropagationResult,
    graph_service: Optional[GraphBrainService] = None,
) -> ExplanationEnrichment:
    """Standalone: enrich an existing PropagationResult with graph reasoning.

    Use this if you want to add graph explanation to an already-computed
    propagation result.
    """
    if not is_enrichment_active("explanation"):
        return ExplanationEnrichment([], "Explanation enrichment disabled")

    try:
        service = graph_service or get_graph_brain_service()
        store = service.store
        reached_domains = [h.domain for h in prop_result.hits]
        return enrich_explanation(store, signal_id, reached_domains)

    except Exception as e:
        logger.warning("Standalone explanation enrichment failed: %s", e)
        return ExplanationEnrichment([], f"Enrichment failed: {e}")
