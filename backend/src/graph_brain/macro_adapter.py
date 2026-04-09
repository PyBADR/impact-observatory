"""Graph Brain Integration Pack A2 — Macro Graph Adapter.

Clean adapter/service that lets Pack 2 (causal mapper, propagation engine,
explanation layer) consume Graph Brain data safely. This is the SINGLE
interface between macro-layer code and the graph substrate.

Capabilities:
  1. graph_available    — check if graph is importable + active
  2. ensure_ingested    — auto-ingest signal into GraphStore (idempotent)
  3. connected_entities — retrieve entities connected to a domain
  4. graph_dependencies — retrieve graph-derived cross-domain dependencies
  5. explanation_fragments — retrieve graph-backed explanation reasoning

Design rules:
  - Every public method is fail-safe (try/except → neutral fallback)
  - Adapter is stateless per-call; GraphStore is the single mutable state
  - If graph is unavailable, every method returns empty/None — zero side effects
  - No Pack 2 types are modified — adapter returns its own typed outputs
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from src.macro.macro_enums import ImpactDomain
from src.macro.macro_schemas import NormalizedSignal

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Adapter Output Types
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ConnectedEntity:
    """A graph entity connected to a domain."""
    node_id: str
    entity_type: str
    label: str
    relation: str
    weight: float = 0.0
    confidence: str = "moderate"


@dataclass(frozen=True)
class GraphDependency:
    """A graph-derived cross-domain dependency."""
    from_domain: str
    to_domain: str
    weight: float
    confidence: str
    reasoning: str
    hops: int = 1


@dataclass
class IngestionSummary:
    """Summary of signal ingestion into the graph."""
    ingested: bool = False
    nodes_created: int = 0
    edges_created: int = 0
    already_existed: bool = False


# ══════════════════════════════════════════════════════════════════════════════
# MacroGraphAdapter
# ══════════════════════════════════════════════════════════════════════════════

class MacroGraphAdapter:
    """Clean adapter for Pack 2 to consume Graph Brain data.

    Instantiation is fail-safe: if Graph Brain is not importable,
    all methods return neutral values.

    Usage:
        adapter = MacroGraphAdapter()
        if adapter.is_available():
            adapter.ensure_ingested(signal)
            deps = adapter.graph_dependencies(entry_domains)
            frags = adapter.explanation_fragments(signal_id, reached_domains)
    """

    def __init__(self) -> None:
        self._store = None
        self._service = None
        self._available = False
        try:
            from src.graph_brain.enrichment import is_enrichment_active
            if is_enrichment_active():
                from src.graph_brain.service import get_graph_brain_service
                self._service = get_graph_brain_service()
                self._store = self._service.store
                self._available = True
        except ImportError:
            logger.debug("MacroGraphAdapter: Graph Brain not importable")
        except Exception as e:
            logger.warning("MacroGraphAdapter: init failed: %s", e)

    # ── 1. Availability Check ──────────────────────────────────────────────

    def is_available(self) -> bool:
        """Check if graph is importable, active, and initialized."""
        return self._available and self._store is not None

    # ── 2. Signal Ingestion ────────────────────────────────────────────────

    def ensure_ingested(self, signal: NormalizedSignal) -> IngestionSummary:
        """Ensure signal is ingested into GraphStore. Idempotent.

        Returns IngestionSummary. On failure, returns summary with ingested=False.
        """
        summary = IngestionSummary()
        if not self.is_available():
            return summary

        try:
            from src.graph_brain.enrichment import ensure_signal_ingested
            result = ensure_signal_ingested(signal, self._store)
            if result is None:
                summary.already_existed = True
                summary.ingested = True
            else:
                summary.ingested = True
                summary.nodes_created = len(result.nodes_created)
                summary.edges_created = len(result.edges_created)
        except Exception as e:
            logger.warning("MacroGraphAdapter.ensure_ingested failed: %s", e)

        return summary

    # ── 3. Connected Entities ──────────────────────────────────────────────

    def connected_entities(
        self,
        domain: ImpactDomain,
        max_depth: int = 3,
    ) -> list[ConnectedEntity]:
        """Retrieve entities connected to a domain in the graph.

        Returns empty list if graph is unavailable or domain has no graph presence.
        """
        if not self.is_available():
            return []

        try:
            from src.graph_brain.query import find_connected
            from src.graph_brain.bridge import _domain_to_graph_id

            node_id = _domain_to_graph_id(domain)
            if not self._store.has_node(node_id):
                return []

            nodes = find_connected(self._store, node_id, max_depth=max_depth)
            entities = []
            for node in nodes:
                # Get the edge connecting start to this node for relation info
                edges = self._store.get_edges_from(node_id)
                rel = "connected"
                weight = 0.0
                for e in edges:
                    if e.target_id == node.node_id:
                        rel = e.relation_type.value
                        weight = e.weight
                        break

                entities.append(ConnectedEntity(
                    node_id=node.node_id,
                    entity_type=node.entity_type.value,
                    label=node.label,
                    relation=rel,
                    weight=weight,
                    confidence=getattr(node, "confidence", "moderate"),
                ))
            return entities

        except Exception as e:
            logger.warning("MacroGraphAdapter.connected_entities failed: %s", e)
            return []

    # ── 4. Graph-Derived Dependencies ──────────────────────────────────────

    def graph_dependencies(
        self,
        entry_domains: list[ImpactDomain],
        existing_pairs: set[tuple[str, str]] | None = None,
        max_depth: int = 3,
    ) -> list[GraphDependency]:
        """Retrieve graph-derived cross-domain dependencies.

        Discovers domain→domain paths in the graph that may not exist
        in the static causal graph. Excludes pairs already known.

        Returns empty list if graph is unavailable.
        """
        if not self.is_available():
            return []

        try:
            from src.graph_brain.bridge import discover_graph_channel_hints

            hints = discover_graph_channel_hints(
                self._store,
                signal_id="",  # discovery doesn't need signal_id
                entry_domains=entry_domains,
                max_depth=max_depth,
            )

            deps = []
            for h in hints:
                pair = (h.from_domain.value, h.to_domain.value)
                if existing_pairs and pair in existing_pairs:
                    continue
                deps.append(GraphDependency(
                    from_domain=h.from_domain.value,
                    to_domain=h.to_domain.value,
                    weight=h.graph_weight,
                    confidence=h.graph_confidence.value,
                    reasoning=h.reasoning,
                ))
            return deps

        except Exception as e:
            logger.warning("MacroGraphAdapter.graph_dependencies failed: %s", e)
            return []

    # ── 5. Explanation Fragments ───────────────────────────────────────────

    def explanation_fragments(
        self,
        signal_id: str,
        reached_domains: list[ImpactDomain],
        max_depth: int = 4,
    ) -> list[dict]:
        """Retrieve graph-backed explanation fragments for reached domains.

        Returns list of dicts with keys: domain, reasoning, confidence,
        graph_paths_count. Empty list if graph is unavailable.
        """
        if not self.is_available():
            return []

        try:
            from src.graph_brain.enrichment import enrich_explanation

            enrichment = enrich_explanation(
                self._store,
                signal_id=signal_id,
                reached_domains=reached_domains,
                max_depth=max_depth,
            )

            if not enrichment.has_enrichment:
                return []

            return [
                {
                    "domain": f.domain.value,
                    "reasoning": f.reasoning,
                    "confidence": f.confidence.value,
                    "graph_paths_count": f.graph_paths_count,
                }
                for f in enrichment.fragments
            ]

        except Exception as e:
            logger.warning("MacroGraphAdapter.explanation_fragments failed: %s", e)
            return []

    # ── 6. Graph Confidence / Provenance ───────────────────────────────────

    def path_provenance(
        self,
        from_domain: ImpactDomain,
        to_domain: ImpactDomain,
        max_depth: int = 4,
    ) -> Optional[dict]:
        """Retrieve path provenance between two domains.

        Returns dict with path_description, weight, confidence, hops,
        source_refs. None if no path exists or graph is unavailable.
        """
        if not self.is_available():
            return None

        try:
            from src.graph_brain.bridge import _domain_to_graph_id
            from src.graph_brain.query import trace_paths

            from_id = _domain_to_graph_id(from_domain)
            to_id = _domain_to_graph_id(to_domain)

            if not self._store.has_node(from_id) or not self._store.has_node(to_id):
                return None

            paths = trace_paths(self._store, from_id, to_id, max_depth=max_depth, max_paths=1)
            if not paths:
                return None

            best = paths[0]
            return {
                "path_description": best.path_description,
                "weight": best.total_weight,
                "hops": best.total_hops,
                "confidence": min(
                    (e.confidence.value for e in best.edges),
                    default="moderate",
                ),
                "source_refs": [
                    {"label": r.label, "uri": r.uri}
                    for n in best.nodes for r in n.source_refs
                ],
            }

        except Exception as e:
            logger.warning("MacroGraphAdapter.path_provenance failed: %s", e)
            return None
