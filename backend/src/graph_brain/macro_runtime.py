"""Graph Brain Integration Pack A2 — Unified Macro Runtime Adapter.

Single entry point that unifies the macro causal→propagation pipeline
with Graph Brain enrichment. This module resolves the Lane A / Lane B
split by making the primary macro runtime path graph-aware.

Runtime flow:
  NormalizedSignal
  → MacroGraphAdapter.ensure_ingested()     (idempotent)
  → map_signal_to_causal_graph_aware()      (Pack 2 + graph channel hints)
  → propagate_graph_enriched()              (Pack 2 + graph explanation)
  → MacroRuntimeResult                      (backward-compatible output)

Architecture rules:
  - Pack 2 contracts (CausalMapping, PropagationResult) remain canonical
  - Graph enrichment is ADDITIVE metadata — never replaces Pack 2 fields
  - If graph is off/unavailable, behavior is identical to raw Pack 2
  - This module is the ONLY caller of graph-aware variants
  - PropagationService delegates here for its graph-aware path

Wiring alignment (A2):
  - Step 2: Causal mapping uses map_signal_to_causal_graph_aware()
  - Step 3: Propagation uses propagate_graph_enriched()
  - Step 4: Explanation is built into propagate_graph_enriched()
  - Step 5: Any failure falls back to vanilla Pack 2 functions

Backward compatibility:
  - MacroRuntimeResult.propagation_result is always a valid PropagationResult
  - MacroRuntimeResult.causal_mapping is always a valid CausalMapping
  - graph_metadata is Optional and can be safely ignored
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.macro.macro_schemas import NormalizedSignal
from src.macro.causal.causal_mapper import (
    map_signal_to_causal,
    map_signal_to_causal_graph_aware,
)
from src.macro.causal.causal_schemas import CausalMapping
from src.macro.propagation.propagation_engine import (
    MAX_PROPAGATION_DEPTH,
    MIN_SEVERITY_THRESHOLD,
    propagate,
    propagate_graph_enriched,
)
from src.macro.propagation.propagation_schemas import PropagationResult

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Graph Metadata — Additive, Optional, Backward-Compatible
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraphEnrichmentMetrics:
    """Metrics from a single graph-enriched macro run.

    All fields are metadata — none affect Pack 2 contracts.
    Safe to serialize, safe to ignore.
    """
    graph_available: bool = False
    signal_ingested: bool = False
    ingestion_nodes_created: int = 0
    ingestion_edges_created: int = 0

    # Causal enrichment (Step 2)
    causal_channel_hints_discovered: int = 0
    causal_additional_domains: int = 0
    causal_enrichment_reasoning: str = ""

    # Propagation enrichment (Step 3)
    propagation_weight_enrichments: int = 0

    # Explanation enrichment (Step 4)
    explanation_fragments_count: int = 0
    explanation_hits_enriched: int = 0
    explanation_reasoning_appended: bool = False

    # Safety (Step 5)
    errors: list[str] = field(default_factory=list)
    fallback_used: bool = False

    def to_dict(self) -> dict:
        return {
            "graph_available": self.graph_available,
            "signal_ingested": self.signal_ingested,
            "causal_hints": self.causal_channel_hints_discovered,
            "causal_new_domains": self.causal_additional_domains,
            "propagation_weight_enrichments": self.propagation_weight_enrichments,
            "explanation_fragments": self.explanation_fragments_count,
            "explanation_hits_enriched": self.explanation_hits_enriched,
            "errors": len(self.errors),
            "fallback_used": self.fallback_used,
        }


@dataclass
class MacroRuntimeResult:
    """Unified output from the graph-aware macro runtime.

    The causal_mapping and propagation_result fields are ALWAYS valid
    Pack 2 objects. The graph_metadata field is supplementary.

    Downstream consumers can safely access:
      result.propagation_result  → always PropagationResult
      result.causal_mapping      → always CausalMapping
      result.graph_metadata      → Optional enrichment summary
    """
    propagation_result: PropagationResult
    causal_mapping: CausalMapping
    graph_metadata: Optional[GraphEnrichmentMetrics] = None

    @property
    def is_graph_enriched(self) -> bool:
        """True if any graph enrichment was applied."""
        if self.graph_metadata is None:
            return False
        m = self.graph_metadata
        return (
            m.causal_channel_hints_discovered > 0
            or m.explanation_hits_enriched > 0
            or m.propagation_weight_enrichments > 0
        )


# ══════════════════════════════════════════════════════════════════════════════
# Unified Runtime Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def run_macro_pipeline(
    signal: NormalizedSignal,
    *,
    max_causal_depth: int = 4,
    max_propagation_depth: int = MAX_PROPAGATION_DEPTH,
    min_severity: float = MIN_SEVERITY_THRESHOLD,
    graph_enabled: bool = True,
) -> MacroRuntimeResult:
    """Run the unified graph-aware macro pipeline.

    This is the SINGLE runtime entry point for:
      Signal → Causal → Propagation → Explanation

    When graph_enabled=True and the graph layer is available:
      1. Auto-ingest signal into GraphStore via MacroGraphAdapter
      2. Run graph-aware causal mapping (map_signal_to_causal_graph_aware)
      3. Run graph-enriched propagation (propagate_graph_enriched)
         — includes explanation enrichment (Step 4)
      4. Return MacroRuntimeResult with graph_metadata

    When graph_enabled=False or graph unavailable:
      1. Run vanilla Pack 2 causal mapping
      2. Run vanilla Pack 2 propagation
      3. Return MacroRuntimeResult with graph_metadata=None

    Args:
        signal: NormalizedSignal from Pack 1.
        max_causal_depth: Max BFS depth for channel discovery.
        max_propagation_depth: Max BFS depth for propagation.
        min_severity: Severity floor for propagation.
        graph_enabled: Master switch for graph enrichment.

    Returns:
        MacroRuntimeResult — always valid, always backward-compatible.
    """
    # ── Graph-disabled fast path ──────────────────────────────────────────
    if not graph_enabled:
        return _run_pack2_only(signal, max_causal_depth, max_propagation_depth, min_severity)

    # ── Graph-enabled path ────────────────────────────────────────────────
    metrics = GraphEnrichmentMetrics()

    try:
        return _run_graph_aware(
            signal, max_causal_depth, max_propagation_depth, min_severity, metrics,
        )
    except Exception as e:
        # Step 5: Fallback guarantee — any graph failure → vanilla Pack 2
        err_msg = f"Graph-aware pipeline failed, falling back to Pack 2: {e}"
        logger.warning("A2: %s", err_msg)
        metrics.errors.append(err_msg)
        metrics.fallback_used = True

        mapping = map_signal_to_causal(signal, max_depth=max_causal_depth)
        prop_result = propagate(mapping, max_depth=max_propagation_depth, min_severity=min_severity)
        return MacroRuntimeResult(
            propagation_result=prop_result,
            causal_mapping=mapping,
            graph_metadata=metrics,
        )


def _run_pack2_only(
    signal: NormalizedSignal,
    max_causal_depth: int,
    max_propagation_depth: int,
    min_severity: float,
) -> MacroRuntimeResult:
    """Pure Pack 2 path — no graph, no enrichment."""
    mapping = map_signal_to_causal(signal, max_depth=max_causal_depth)
    prop_result = propagate(mapping, max_depth=max_propagation_depth, min_severity=min_severity)
    return MacroRuntimeResult(
        propagation_result=prop_result,
        causal_mapping=mapping,
        graph_metadata=None,
    )


def _run_graph_aware(
    signal: NormalizedSignal,
    max_causal_depth: int,
    max_propagation_depth: int,
    min_severity: float,
    metrics: GraphEnrichmentMetrics,
) -> MacroRuntimeResult:
    """Graph-enriched path using MacroGraphAdapter + graph-aware Pack 2 variants.

    Steps:
      1. Initialize adapter, check availability
      2. Auto-ingest signal (idempotent)
      3. map_signal_to_causal_graph_aware() — Step 2
      4. propagate_graph_enriched() — Step 3 + Step 4 (explanation)
      5. Collect metrics
    """
    # ── Step 1: Initialize adapter ────────────────────────────────────────
    from src.graph_brain.macro_adapter import MacroGraphAdapter
    adapter = MacroGraphAdapter()

    if not adapter.is_available():
        # Graph not available — pure Pack 2, but mark metrics
        logger.debug("A2: Graph adapter not available, running pure Pack 2")
        mapping = map_signal_to_causal(signal, max_depth=max_causal_depth)
        prop_result = propagate(mapping, max_depth=max_propagation_depth, min_severity=min_severity)
        return MacroRuntimeResult(
            propagation_result=prop_result,
            causal_mapping=mapping,
            graph_metadata=metrics,
        )

    metrics.graph_available = True

    # ── Step 2a: Auto-ingest signal ───────────────────────────────────────
    ingest_summary = adapter.ensure_ingested(signal)
    metrics.signal_ingested = ingest_summary.ingested
    metrics.ingestion_nodes_created = ingest_summary.nodes_created
    metrics.ingestion_edges_created = ingest_summary.edges_created

    # ── Step 2b: Graph-aware causal mapping ───────────────────────────────
    # Delegates to map_signal_to_causal_graph_aware() which runs Pack 2
    # mapping first, then enriches with graph-discovered channel hints.
    graph_service = adapter._service  # Pass the service for graph queries
    mapping, causal_enrichment = map_signal_to_causal_graph_aware(
        signal,
        max_depth=max_causal_depth,
        graph_service=graph_service,
    )

    if causal_enrichment is not None and causal_enrichment.has_enrichment:
        metrics.causal_channel_hints_discovered = len(causal_enrichment.channel_hints)
        metrics.causal_additional_domains = len(causal_enrichment.additional_domains)
        metrics.causal_enrichment_reasoning = causal_enrichment.reasoning
        logger.info(
            "A2: Graph causal enrichment for signal %s: %d hints, %d new domains",
            signal.signal_id,
            metrics.causal_channel_hints_discovered,
            metrics.causal_additional_domains,
        )

    # ── Step 2c: Propagation weight hints ─────────────────────────────────
    try:
        from src.graph_brain.enrichment import (
            compute_blended_weight,
            is_enrichment_active,
        )
        if is_enrichment_active("propagation") and adapter._store is not None:
            weight_count = 0
            for channel in mapping.activated_channels:
                _, enrichment_data = compute_blended_weight(
                    channel.base_weight,
                    adapter._store,
                    channel.from_domain,
                    channel.to_domain,
                )
                if enrichment_data is not None:
                    weight_count += 1
            metrics.propagation_weight_enrichments = weight_count
    except Exception as e:
        logger.debug("A2: Weight enrichment skipped: %s", e)

    # ── Step 3 + 4: Graph-enriched propagation (includes explanation) ─────
    # Delegates to propagate_graph_enriched() which runs Pack 2 propagation
    # first, then appends graph-backed explanation to hit reasoning.
    prop_result, explanation_enrichment = propagate_graph_enriched(
        mapping,
        max_depth=max_propagation_depth,
        min_severity=min_severity,
        graph_service=graph_service,
    )

    if explanation_enrichment is not None and explanation_enrichment.has_enrichment:
        metrics.explanation_fragments_count = len(explanation_enrichment.fragments)
        # Count hits that received graph reasoning
        enriched_count = sum(
            1 for h in prop_result.hits
            if "[Graph Brain]" in h.reasoning
        )
        metrics.explanation_hits_enriched = enriched_count
        metrics.explanation_reasoning_appended = enriched_count > 0
        logger.info(
            "A2: Graph explanation enriched %d/%d hits for signal %s",
            enriched_count, len(prop_result.hits), signal.signal_id,
        )

    return MacroRuntimeResult(
        propagation_result=prop_result,
        causal_mapping=mapping,
        graph_metadata=metrics,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Convenience: Check Graph Availability
# ══════════════════════════════════════════════════════════════════════════════

def is_graph_runtime_available() -> bool:
    """Check if the graph runtime layer is importable and active.

    Use this to gate UI features or API fields that depend on graph data.
    """
    try:
        from src.graph_brain.enrichment import is_enrichment_active
        return is_enrichment_active()
    except ImportError:
        return False
