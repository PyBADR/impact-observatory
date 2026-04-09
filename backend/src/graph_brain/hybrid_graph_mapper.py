"""Hybrid Graph Mapper — AI + Rule-Based Merge Decision Layer.

Combines the deterministic rule-based mapper (graph_mapper.py) with the
AI entity extractor (ai_entity_extractor.py) into a single unified pipeline.

Architecture Layer: Models → Agents (Layer 3-4 of the 7-layer stack)
Owner: Graph Mapping Engine
Consumers: GraphExpansionService

Decision Flow:
  1. Rule-based mapper executes first (always, deterministic baseline)
  2. AI extractor runs concurrently if enabled and available
  3. Merge logic combines both results using per-entity deduplication
  4. Confidence gating determines which AI entities are promoted vs quarantined
  5. Combined MappingResult returned with full provenance tracking

Merge Strategy:
  - Rule-based nodes are ALWAYS kept (deterministic, auditable baseline)
  - AI nodes that match existing rule-based nodes → skip (rule wins)
  - AI nodes that are novel (no rule-based equivalent) → promoted if confidence >= threshold
  - AI nodes below confidence threshold → quarantined (logged, not persisted)
  - AI edges follow the same logic, with endpoint validation

Confidence Gating (three tiers):
  - STANDARD  (>= 0.70): AI entity promoted directly into the merged result
  - LOW_CONF  (0.30-0.69): AI entity promoted but flagged with quarantine_status="low_confidence"
  - QUARANTINE (< 0.30): AI entity logged in decisions but NOT added to result
"""

import hashlib
import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.graph_brain.ai_entity_extractor import (
    AIEntityExtractor,
    LLMBackend,
    MockLLMBackend,
    OllamaBackend,
)
from src.graph_brain.graph_mapper import (
    MappingDecision,
    MappingResult,
    map_signal_to_graph,
)
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)

logger = logging.getLogger("graph_brain.hybrid_mapper")


# ═══════════════════════════════════════════════════════════════════════════════
# Merge Configuration
# ═══════════════════════════════════════════════════════════════════════════════

class MergeStrategy(str, Enum):
    """How to handle AI-discovered entities during merge."""
    RULE_PRIORITY = "rule_priority"      # Rule-based always wins on conflict
    AI_AUGMENT = "ai_augment"            # AI adds novel entities only
    CONFIDENCE_MAX = "confidence_max"    # Higher-confidence wins on conflict


class ConfidenceTier(str, Enum):
    """Confidence classification for merge decisions."""
    STANDARD = "standard"          # >= 0.70 — promoted directly
    LOW_CONFIDENCE = "low_confidence"  # 0.30 - 0.69 — promoted with flag
    QUARANTINE = "quarantine"      # < 0.30 — logged, not persisted


class HybridMergeConfig(BaseModel):
    """Configuration for the hybrid merge behavior."""
    strategy: MergeStrategy = MergeStrategy.AI_AUGMENT
    standard_threshold: float = Field(0.70, ge=0.0, le=1.0)
    low_confidence_threshold: float = Field(0.30, ge=0.0, le=1.0)
    max_ai_nodes_per_signal: int = Field(25, ge=1, le=100)
    max_ai_edges_per_signal: int = Field(50, ge=1, le=200)
    dedup_by_label_similarity: bool = True
    label_similarity_threshold: float = Field(0.85, ge=0.0, le=1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Hybrid Merge Result — extended observability
# ═══════════════════════════════════════════════════════════════════════════════

class HybridMergeStats(BaseModel):
    """Statistics about the merge operation."""
    rule_nodes: int = 0
    rule_edges: int = 0
    ai_nodes_total: int = 0
    ai_edges_total: int = 0
    ai_nodes_promoted: int = 0
    ai_nodes_deduplicated: int = 0
    ai_nodes_quarantined: int = 0
    ai_edges_promoted: int = 0
    ai_edges_deduplicated: int = 0
    ai_edges_quarantined: int = 0
    rule_duration_ms: float = 0.0
    ai_duration_ms: float = 0.0
    merge_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    ai_available: bool = False
    ai_enabled: bool = False

    def summary(self) -> dict[str, Any]:
        return self.model_dump()


class HybridMappingResult(BaseModel):
    """Extended mapping result with hybrid merge metadata."""
    mapping: MappingResult = Field(default_factory=MappingResult)
    merge_stats: HybridMergeStats = Field(default_factory=HybridMergeStats)
    quarantined_nodes: list[dict] = Field(
        default_factory=list,
        description="AI nodes that failed confidence gating (for audit)",
    )
    quarantined_edges: list[dict] = Field(
        default_factory=list,
        description="AI edges that failed confidence gating (for audit)",
    )
    audit_hash: str = ""

    def compute_audit_hash(self) -> str:
        """SHA-256 hash of the merge decision for PDPL audit trail."""
        canonical = {
            "signal_id": self.mapping.signal_id,
            "rule_nodes": self.merge_stats.rule_nodes,
            "ai_promoted": self.merge_stats.ai_nodes_promoted,
            "ai_quarantined": self.merge_stats.ai_nodes_quarantined,
            "total_nodes": self.mapping.node_count,
            "total_edges": self.mapping.edge_count,
        }
        import json
        blob = json.dumps(canonical, sort_keys=True).encode()
        self.audit_hash = hashlib.sha256(blob).hexdigest()
        return self.audit_hash


# ═══════════════════════════════════════════════════════════════════════════════
# Hybrid Graph Mapper — the main class
# ═══════════════════════════════════════════════════════════════════════════════

class HybridGraphMapper:
    """Merges rule-based and AI-driven graph mapping into a single pipeline.

    Usage:
        mapper = HybridGraphMapper(ai_enabled=True, backend=OllamaBackend())
        result = mapper.map_signal(signal_dict)
        # result.mapping is a standard MappingResult
        # result.merge_stats has full observability
    """

    def __init__(
        self,
        ai_enabled: bool = False,
        backend: Optional[LLMBackend] = None,
        merge_config: Optional[HybridMergeConfig] = None,
        min_entity_confidence: float = 0.50,
        min_relationship_confidence: float = 0.45,
    ) -> None:
        self._ai_enabled = ai_enabled
        self._merge_config = merge_config or HybridMergeConfig()

        # AI extractor — initialized lazily or with provided backend
        self._ai_extractor: Optional[AIEntityExtractor] = None
        if ai_enabled:
            _backend = backend or MockLLMBackend()
            self._ai_extractor = AIEntityExtractor(
                backend=_backend,
                min_entity_confidence=min_entity_confidence,
                min_relationship_confidence=min_relationship_confidence,
            )

    @property
    def ai_enabled(self) -> bool:
        return self._ai_enabled

    @property
    def ai_available(self) -> bool:
        if self._ai_extractor is None:
            return False
        return self._ai_extractor.is_available

    def map_signal(self, signal_dict: dict) -> HybridMappingResult:
        """Execute the full hybrid mapping pipeline.

        Steps:
          1. Run rule-based mapper (always)
          2. Run AI extractor (if enabled and available)
          3. Merge results with confidence gating
          4. Return HybridMappingResult with full provenance

        Args:
            signal_dict: MacroSignal serialized via .model_dump()

        Returns:
            HybridMappingResult with merged mapping + observability stats
        """
        t0 = time.monotonic()
        signal_id = signal_dict.get("signal_id", "unknown")
        stats = HybridMergeStats(
            ai_enabled=self._ai_enabled,
            ai_available=self.ai_available,
        )

        # ── Step 1: Rule-based mapping (always runs) ──────────────────────
        t_rule = time.monotonic()
        rule_result: MappingResult = map_signal_to_graph(signal_dict)
        stats.rule_duration_ms = (time.monotonic() - t_rule) * 1000
        stats.rule_nodes = rule_result.node_count
        stats.rule_edges = rule_result.edge_count

        # If AI is disabled or unavailable, return rule-based result directly
        if not self._ai_enabled or not self.ai_available:
            stats.total_duration_ms = (time.monotonic() - t0) * 1000
            result = HybridMappingResult(
                mapping=rule_result,
                merge_stats=stats,
            )
            result.compute_audit_hash()

            logger.info(
                "Hybrid map for %s: rule-only mode (%d nodes, %d edges, %.1fms)",
                signal_id, rule_result.node_count, rule_result.edge_count,
                stats.total_duration_ms,
            )
            return result

        # ── Step 2: AI extraction ─────────────────────────────────────────
        t_ai = time.monotonic()
        ai_result: MappingResult = self._ai_extractor.extract(signal_dict)  # type: ignore[union-attr]
        stats.ai_duration_ms = (time.monotonic() - t_ai) * 1000
        stats.ai_nodes_total = ai_result.node_count
        stats.ai_edges_total = ai_result.edge_count

        # ── Step 3: Merge ─────────────────────────────────────────────────
        t_merge = time.monotonic()
        merged = self._merge_results(rule_result, ai_result, stats)
        stats.merge_duration_ms = (time.monotonic() - t_merge) * 1000
        stats.total_duration_ms = (time.monotonic() - t0) * 1000

        result = HybridMappingResult(
            mapping=merged,
            merge_stats=stats,
            quarantined_nodes=self._last_quarantined_nodes,
            quarantined_edges=self._last_quarantined_edges,
        )
        result.compute_audit_hash()

        logger.info(
            "Hybrid map for %s: %d rule + %d AI promoted (%d dedup, %d quarantine) "
            "= %d nodes, %d edges (%.1fms total)",
            signal_id,
            stats.rule_nodes, stats.ai_nodes_promoted,
            stats.ai_nodes_deduplicated, stats.ai_nodes_quarantined,
            merged.node_count, merged.edge_count,
            stats.total_duration_ms,
        )
        return result

    # ── Merge Logic ───────────────────────────────────────────────────────

    # Temporary storage for quarantined items (reset each merge)
    _last_quarantined_nodes: list[dict] = []
    _last_quarantined_edges: list[dict] = []

    def _merge_results(
        self,
        rule: MappingResult,
        ai: MappingResult,
        stats: HybridMergeStats,
    ) -> MappingResult:
        """Merge rule-based and AI mapping results.

        Rule-based nodes/edges are always the baseline.
        AI nodes/edges are conditionally promoted based on:
          1. Deduplication (no overlap with rule-based)
          2. Confidence gating (three tiers)
          3. Capacity limits (max_ai_nodes_per_signal)
        """
        self._last_quarantined_nodes = []
        self._last_quarantined_edges = []

        merged = MappingResult(
            signal_id=rule.signal_id,
            payload_type=rule.payload_type,
        )

        # Start with all rule-based elements
        merged.nodes.extend(rule.nodes)
        merged.edges.extend(rule.edges)
        merged.decisions.extend(rule.decisions)
        merged.warnings.extend(rule.warnings)

        # Build indexes for deduplication
        rule_node_ids = {n.node_id for n in rule.nodes}
        rule_labels_normalized = {
            _normalize_label(n.label): n.node_id for n in rule.nodes
        }
        rule_edge_ids = {e.edge_id for e in rule.edges}
        rule_edge_pairs = {
            (e.source_id, e.target_id, e.relation_type) for e in rule.edges
        }

        # Process AI nodes
        ai_promoted_count = 0
        ai_node_id_map: dict[str, str] = {}  # original AI node_id → final node_id

        for ai_node in ai.nodes:
            # Check capacity limit
            if ai_promoted_count >= self._merge_config.max_ai_nodes_per_signal:
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="skip",
                    element_id=ai_node.node_id,
                    reason=f"AI node capacity limit reached ({self._merge_config.max_ai_nodes_per_signal})",
                ))
                break

            # Deduplication check 1: exact node_id match
            if ai_node.node_id in rule_node_ids:
                stats.ai_nodes_deduplicated += 1
                ai_node_id_map[ai_node.node_id] = ai_node.node_id  # maps to rule version
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="skip",
                    element_id=ai_node.node_id,
                    reason="Duplicate: exact node_id match with rule-based entity",
                    confidence="high",
                ))
                continue

            # Deduplication check 2: label similarity
            norm_label = _normalize_label(ai_node.label)
            if (
                self._merge_config.dedup_by_label_similarity
                and norm_label in rule_labels_normalized
            ):
                existing_id = rule_labels_normalized[norm_label]
                stats.ai_nodes_deduplicated += 1
                ai_node_id_map[ai_node.node_id] = existing_id
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="skip",
                    element_id=ai_node.node_id,
                    reason=f"Duplicate: label '{ai_node.label}' matches rule-based '{existing_id}'",
                    confidence="high",
                ))
                continue

            # Confidence gating
            ai_conf_score = ai_node.properties.get("ai_confidence", 0.0)
            tier = self._classify_confidence(ai_conf_score)

            if tier == ConfidenceTier.QUARANTINE:
                stats.ai_nodes_quarantined += 1
                self._last_quarantined_nodes.append({
                    "node_id": ai_node.node_id,
                    "label": ai_node.label,
                    "entity_type": ai_node.entity_type.value,
                    "confidence": ai_conf_score,
                    "reason": "Below quarantine threshold",
                })
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="quarantine",
                    element_id=ai_node.node_id,
                    reason=f"AI confidence {ai_conf_score:.2f} < {self._merge_config.low_confidence_threshold} — quarantined",
                    confidence="speculative",
                ))
                continue

            # Promote: add to merged result
            if tier == ConfidenceTier.LOW_CONFIDENCE:
                ai_node.properties["quarantine_status"] = "low_confidence"
                ai_node.properties["requires_review"] = True

            # Tag with provenance
            ai_node.properties["merge_source"] = "ai_extractor"
            ai_node.properties["merge_tier"] = tier.value

            merged.nodes.append(ai_node)
            ai_node_id_map[ai_node.node_id] = ai_node.node_id
            ai_promoted_count += 1
            stats.ai_nodes_promoted += 1

            merged.decisions.append(MappingDecision(
                stage="hybrid_merge",
                action="promote",
                element_id=ai_node.node_id,
                reason=f"AI entity promoted ({tier.value}): conf={ai_conf_score:.2f}",
                confidence=ai_node.confidence.value,
            ))

        # Process AI edges
        ai_edges_promoted = 0
        for ai_edge in ai.edges:
            if ai_edges_promoted >= self._merge_config.max_ai_edges_per_signal:
                break

            # Remap edge endpoints if they were deduplicated to rule-based IDs
            src_id = ai_node_id_map.get(ai_edge.source_id, ai_edge.source_id)
            tgt_id = ai_node_id_map.get(ai_edge.target_id, ai_edge.target_id)

            # Validate both endpoints exist in merged result
            merged_node_ids = {n.node_id for n in merged.nodes}
            if src_id not in merged_node_ids or tgt_id not in merged_node_ids:
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="skip",
                    element_id=ai_edge.edge_id,
                    reason=f"AI edge endpoint missing: src={src_id} in={src_id in merged_node_ids}, "
                           f"tgt={tgt_id} in={tgt_id in merged_node_ids}",
                ))
                continue

            # Skip self-loops
            if src_id == tgt_id:
                continue

            # Deduplication: exact edge_id or (src, tgt, type) triple
            edge_triple = (src_id, tgt_id, ai_edge.relation_type)
            if ai_edge.edge_id in rule_edge_ids or edge_triple in rule_edge_pairs:
                stats.ai_edges_deduplicated += 1
                merged.decisions.append(MappingDecision(
                    stage="hybrid_merge",
                    action="skip",
                    element_id=ai_edge.edge_id,
                    reason="Duplicate: edge matches rule-based relationship",
                ))
                continue

            # Confidence gating for edges
            ai_edge_conf = ai_edge.properties.get("ai_confidence", ai_edge.weight)
            tier = self._classify_confidence(ai_edge_conf)

            if tier == ConfidenceTier.QUARANTINE:
                stats.ai_edges_quarantined += 1
                self._last_quarantined_edges.append({
                    "edge_id": ai_edge.edge_id,
                    "source": src_id,
                    "target": tgt_id,
                    "type": ai_edge.relation_type.value,
                    "confidence": ai_edge_conf,
                })
                continue

            # Remap endpoints if needed
            if src_id != ai_edge.source_id or tgt_id != ai_edge.target_id:
                # Build a new edge with corrected endpoints
                ai_edge = GraphEdge(
                    edge_id=f"{src_id}--{ai_edge.relation_type.value}-->{tgt_id}",
                    source_id=src_id,
                    target_id=tgt_id,
                    relation_type=ai_edge.relation_type,
                    label=ai_edge.label,
                    weight=ai_edge.weight,
                    confidence=ai_edge.confidence,
                    properties={
                        **ai_edge.properties,
                        "merge_source": "ai_extractor",
                        "merge_tier": tier.value,
                    },
                    source_refs=ai_edge.source_refs,
                )
            else:
                ai_edge.properties["merge_source"] = "ai_extractor"
                ai_edge.properties["merge_tier"] = tier.value

            merged.edges.append(ai_edge)
            rule_edge_pairs.add(edge_triple)  # prevent further duplication
            ai_edges_promoted += 1
            stats.ai_edges_promoted += 1

            merged.decisions.append(MappingDecision(
                stage="hybrid_merge",
                action="promote",
                element_id=ai_edge.edge_id,
                reason=f"AI edge promoted ({tier.value}): {src_id} --[{ai_edge.relation_type.value}]--> {tgt_id}",
                confidence=ai_edge.confidence.value,
            ))

        # Carry over AI warnings
        if ai.warnings:
            merged.warnings.extend([f"[AI] {w}" for w in ai.warnings])

        # Add AI decisions for observability
        merged.decisions.extend(ai.decisions)

        return merged

    def _classify_confidence(self, score: float) -> ConfidenceTier:
        """Classify a confidence score into a merge tier."""
        if score >= self._merge_config.standard_threshold:
            return ConfidenceTier.STANDARD
        if score >= self._merge_config.low_confidence_threshold:
            return ConfidenceTier.LOW_CONFIDENCE
        return ConfidenceTier.QUARANTINE


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_label(label: str) -> str:
    """Normalize a label for deduplication comparison.

    Strips, lowercases, removes common suffixes and whitespace.
    """
    return (
        label.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace(",", "")
    )
