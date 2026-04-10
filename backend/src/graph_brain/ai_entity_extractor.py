"""AI Entity Extractor — LLM-driven entity and relationship extraction.

Transforms a MacroSignal into AI-inferred GraphNodes and GraphEdges
using a pluggable LLM backend (Ollama local, or any OpenAI-compatible API).

Architecture Layer: Models → Agents (Layer 3-4 of the 7-layer stack)
Owner: AI Graph Mapping Engine
Consumers: HybridGraphMapper

Design Principles:
  1. Output-typed: AI output is validated against GraphEntityType/GraphRelationType enums
  2. Fallback-safe: LLM failures return empty result, never crash the pipeline
  3. Deterministic provenance: every AI-created node/edge carries source_type="ai_extractor"
  4. Constrained generation: system prompt enforces the exact entity/relationship taxonomy
  5. Pluggable: swap LLM backend via LLMBackend protocol (Ollama, OpenAI, mock)

LLM Output Contract (what we ask the model to produce):
  {
    "entities": [{"name": "...", "type": "<GraphEntityType>", "confidence": 0.0-1.0, "properties": {}}],
    "relationships": [{"source": "...", "target": "...", "type": "<GraphRelationType>", "confidence": 0.0-1.0}],
    "reasoning": "...",
    "overall_confidence": 0.0-1.0
  }
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field, field_validator

from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)
from src.graph_brain.graph_mapper import MappingDecision, MappingResult

logger = logging.getLogger("graph_brain.ai_extractor")


# ═══════════════════════════════════════════════════════════════════════════════
# AI Output Schema — strongly typed, validated against our enums
# ═══════════════════════════════════════════════════════════════════════════════

# Build sets of valid enum values for validation
_VALID_ENTITY_TYPES = {e.value for e in GraphEntityType}
_VALID_RELATION_TYPES = {r.value for r in GraphRelationType}


class AIExtractedEntity(BaseModel):
    """A single entity extracted by the LLM. Validated against GraphEntityType."""
    name: str = Field(..., min_length=1, description="Entity name")
    type: str = Field(..., description="Must be a valid GraphEntityType value")
    confidence: float = Field(0.7, ge=0.0, le=1.0)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in _VALID_ENTITY_TYPES:
            # Attempt fuzzy mapping for common LLM outputs
            fuzzy_map = {
                "company": "organization", "corp": "organization", "firm": "organization",
                "bank": "organization", "insurer": "organization",
                "port": "infrastructure", "pipeline": "infrastructure", "refinery": "infrastructure",
                "strait": "chokepoint", "canal": "chokepoint", "passage": "chokepoint",
                "country": "country", "nation": "country", "state": "country",
                "index": "indicator", "metric": "indicator", "price": "indicator",
                "risk": "risk_factor", "threat": "risk_factor", "hazard": "risk_factor",
                "industry": "sector", "domain": "sector",
                "regulation": "regulator", "authority": "regulator",
                "exchange": "market", "bourse": "market",
            }
            mapped = fuzzy_map.get(normalized)
            if mapped:
                return mapped
            raise ValueError(
                f"Invalid entity type '{v}'. Must be one of: {sorted(_VALID_ENTITY_TYPES)}"
            )
        return normalized


class AIExtractedRelationship(BaseModel):
    """A single relationship extracted by the LLM. Validated against GraphRelationType."""
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    type: str = Field(..., description="Must be a valid GraphRelationType value")
    confidence: float = Field(0.6, ge=0.0, le=1.0)

    @field_validator("type")
    @classmethod
    def validate_relation_type(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in _VALID_RELATION_TYPES:
            fuzzy_map = {
                "impacts": "affects", "disrupts": "affects", "damages": "affects",
                "depends": "depends_on", "relies_on": "depends_on",
                "triggers": "triggered_by", "causes": "triggered_by",
                "correlates": "correlated_with", "related": "linked_to",
                "located": "located_in", "in": "located_in",
                "propagates": "propagates_to", "spreads": "propagates_to",
                "influences": "influences", "constrains": "constrained_by",
                "regulates": "regulates", "operates": "operates_in",
                "exposes": "exposed_to", "supplies": "supply_chain",
            }
            mapped = fuzzy_map.get(normalized)
            if mapped:
                return mapped
            raise ValueError(
                f"Invalid relation type '{v}'. Must be one of: {sorted(_VALID_RELATION_TYPES)}"
            )
        return normalized


class AIExtractionResult(BaseModel):
    """Full LLM extraction output — validated and type-safe."""
    entities: list[AIExtractedEntity] = Field(default_factory=list)
    relationships: list[AIExtractedRelationship] = Field(default_factory=list)
    reasoning: str = Field(default="")
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Backend Protocol — pluggable interface
# ═══════════════════════════════════════════════════════════════════════════════

class LLMBackend(ABC):
    """Abstract interface for LLM providers. Implement for Ollama, OpenAI, etc."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Send prompt to LLM, return raw text response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM backend is reachable."""
        ...


class OllamaBackend(LLMBackend):
    """Ollama local LLM backend — optimized for Mac M4 Max GPU inference.

    Uses the Ollama HTTP API (no pip dependency required).
    Default model: llama3.1:8b (fast, good at structured extraction).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        timeout_seconds: int = 30,
        temperature: float = 0.1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds
        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama /api/generate endpoint."""
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 2048,
            },
            "format": "json",
        }).encode("utf-8")

        req = Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return body.get("response", "")
        except Exception as exc:
            logger.error("Ollama request failed: %s", exc)
            raise

    def is_available(self) -> bool:
        try:
            req = Request(f"{self.base_url}/api/tags", method="GET")
            with urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False


class MockLLMBackend(LLMBackend):
    """Mock backend for testing — returns deterministic extraction based on signal domain."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Return a plausible extraction based on signal keywords."""
        prompt_lower = prompt.lower()

        entities = []
        relationships = []
        reasoning = "Mock extraction based on signal keywords"

        # Domain-aware mock extraction
        if "oil" in prompt_lower or "crude" in prompt_lower or "energy" in prompt_lower:
            entities = [
                {"name": "Brent Crude", "type": "indicator", "confidence": 0.9, "properties": {"unit": "USD/bbl"}},
                {"name": "OPEC+", "type": "organization", "confidence": 0.85, "properties": {}},
                {"name": "Energy Sector", "type": "sector", "confidence": 0.9, "properties": {}},
            ]
            relationships = [
                {"source": "OPEC+", "target": "Brent Crude", "type": "influences", "confidence": 0.85},
                {"source": "Brent Crude", "target": "Energy Sector", "type": "affects", "confidence": 0.8},
            ]
            reasoning = "Oil price signal: extracted OPEC+ as key actor, Brent Crude as indicator, with influence and impact relationships"

        elif "port" in prompt_lower or "closure" in prompt_lower or "maritime" in prompt_lower:
            entities = [
                {"name": "Port Facility", "type": "infrastructure", "confidence": 0.9, "properties": {}},
                {"name": "Maritime Logistics", "type": "sector", "confidence": 0.85, "properties": {}},
                {"name": "Supply Chain Disruption", "type": "risk_factor", "confidence": 0.8, "properties": {}},
            ]
            relationships = [
                {"source": "Port Facility", "target": "Maritime Logistics", "type": "affects", "confidence": 0.85},
                {"source": "Supply Chain Disruption", "target": "Port Facility", "type": "triggered_by", "confidence": 0.8},
            ]
            reasoning = "Port disruption signal: infrastructure impact with supply chain propagation"

        elif "insurance" in prompt_lower or "claims" in prompt_lower or "reinsurance" in prompt_lower:
            entities = [
                {"name": "Marine Cargo Insurance", "type": "sector", "confidence": 0.9, "properties": {}},
                {"name": "Claims Surge Event", "type": "event", "confidence": 0.85, "properties": {}},
                {"name": "Reinsurance Market", "type": "market", "confidence": 0.8, "properties": {}},
            ]
            relationships = [
                {"source": "Claims Surge Event", "target": "Marine Cargo Insurance", "type": "affects", "confidence": 0.85},
                {"source": "Marine Cargo Insurance", "target": "Reinsurance Market", "type": "risk_transfer", "confidence": 0.8},
            ]
            reasoning = "Insurance claims signal: sector stress with reinsurance market exposure"

        else:
            entities = [
                {"name": "Unknown Domain Event", "type": "event", "confidence": 0.5, "properties": {}},
            ]
            reasoning = "Unrecognized domain — minimal extraction"

        return json.dumps({
            "entities": entities,
            "relationships": relationships,
            "reasoning": reasoning,
            "overall_confidence": 0.75 if entities else 0.0,
        })

    def is_available(self) -> bool:
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompt — constrains LLM to our exact taxonomy
# ═══════════════════════════════════════════════════════════════════════════════

EXTRACTION_SYSTEM_PROMPT = f"""You are an expert Knowledge Graph entity extraction system for GCC macro intelligence.
You extract entities and relationships from financial, insurance, and geopolitical signals.

STRICT RULES:
1. Entity types MUST be one of: {sorted(_VALID_ENTITY_TYPES)}
2. Relationship types MUST be one of: {sorted(_VALID_RELATION_TYPES)}
3. Confidence scores range from 0.0 (speculative) to 1.0 (definitive)
4. Do NOT invent entity or relationship types outside the allowed lists
5. Focus on GCC-relevant entities: countries, organizations, infrastructure, sectors
6. Extract implicit relationships (e.g., a port closure AFFECTS maritime sector)

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "entities": [
    {{"name": "entity name", "type": "valid_entity_type", "confidence": 0.85, "properties": {{}}}}
  ],
  "relationships": [
    {{"source": "entity name", "target": "entity name", "type": "valid_relation_type", "confidence": 0.8}}
  ],
  "reasoning": "brief explanation of extraction logic",
  "overall_confidence": 0.75
}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# AI Entity Extractor — the main class
# ═══════════════════════════════════════════════════════════════════════════════

class AIEntityExtractor:
    """Extracts entities and relationships from a MacroSignal using an LLM.

    Produces a MappingResult compatible with the existing rule-based mapper,
    enabling seamless merge in the HybridGraphMapper.

    Args:
        backend: LLM backend (OllamaBackend, MockLLMBackend, or any LLMBackend impl)
        min_entity_confidence: Minimum confidence to include an AI-extracted entity
        min_relationship_confidence: Minimum confidence to include an AI-extracted relationship
    """

    def __init__(
        self,
        backend: Optional[LLMBackend] = None,
        min_entity_confidence: float = 0.50,
        min_relationship_confidence: float = 0.45,
    ) -> None:
        self._backend = backend or MockLLMBackend()
        self._min_entity_conf = min_entity_confidence
        self._min_rel_conf = min_relationship_confidence

    @property
    def backend(self) -> LLMBackend:
        return self._backend

    @property
    def is_available(self) -> bool:
        return self._backend.is_available()

    def extract(self, signal_dict: dict) -> MappingResult:
        """Run AI extraction on a MacroSignal dict.

        Returns a MappingResult with AI-inferred nodes and edges.
        On failure, returns an empty MappingResult with warnings.
        """
        t0 = time.monotonic()
        signal_id = signal_dict.get("signal_id", "unknown")
        result = MappingResult(signal_id=signal_id)

        try:
            # Step 1: Build prompt from signal
            prompt = self._build_extraction_prompt(signal_dict)

            # Step 2: Call LLM
            raw_response = self._backend.generate(prompt, EXTRACTION_SYSTEM_PROMPT)

            # Step 3: Parse and validate LLM output
            extraction = self._parse_and_validate(raw_response, result)
            if extraction is None:
                return result

            # Step 4: Convert validated AI output → GraphNode/GraphEdge
            self._build_graph_elements(signal_dict, extraction, result)

            result.decisions.append(MappingDecision(
                stage="ai_extraction",
                action="create_node",
                element_id=f"ai_batch:{signal_id}",
                reason=f"AI extracted {len(extraction.entities)} entities, "
                       f"{len(extraction.relationships)} relationships. "
                       f"Reasoning: {extraction.reasoning[:200]}",
                confidence=str(extraction.overall_confidence),
            ))

        except Exception as exc:
            logger.error("AI extraction failed for %s: %s", signal_id, exc)
            result.warnings.append(f"AI extraction error: {exc}")

        result.duration_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "AI extraction for %s: %d entities, %d rels, confidence=%.2f (%.1fms)",
            signal_id, result.node_count, result.edge_count,
            0.0, result.duration_ms,
        )
        return result

    # ── Prompt Construction ────────────────────────────────────────────────

    def _build_extraction_prompt(self, signal_dict: dict) -> str:
        """Build a concise extraction prompt from the signal.

        We don't dump the entire signal — we extract the fields that matter
        for entity extraction to keep the prompt short and focused.
        """
        payload = signal_dict.get("payload", {})
        geo = signal_dict.get("geo") or {}
        entity_refs = signal_dict.get("entity_refs", [])

        prompt_parts = [
            f"Signal Type: {signal_dict.get('signal_type', 'unknown')}",
            f"Title: {signal_dict.get('title', '')}",
            f"Domain: {signal_dict.get('domain', '')}",
            f"Severity: {signal_dict.get('severity', 'NOMINAL')} (score: {signal_dict.get('severity_score', 0.0)})",
        ]

        desc = signal_dict.get("description")
        if desc:
            prompt_parts.append(f"Description: {desc[:500]}")

        if geo.get("region_code"):
            prompt_parts.append(f"Region: {geo.get('region_name', geo['region_code'])} ({geo['region_code']})")

        if geo.get("affected_zones"):
            prompt_parts.append(f"Affected Zones: {', '.join(geo['affected_zones'])}")

        if payload:
            prompt_parts.append(f"Payload Type: {payload.get('payload_type', 'unknown')}")
            # Include key payload fields (domain-specific)
            for key in ["indicator_code", "value", "unit", "delta_pct",
                        "line_of_business", "estimated_loss_usd", "claims_count",
                        "system_id", "incident_type", "capacity_impact_pct",
                        "event_type", "actors", "affected_trade_routes"]:
                if key in payload and payload[key] is not None:
                    prompt_parts.append(f"  {key}: {payload[key]}")

        if entity_refs:
            refs_str = ", ".join(
                f"{er.get('entity_label', er.get('entity_id', '?'))} ({er.get('entity_type', '?')})"
                for er in entity_refs[:5]
            )
            prompt_parts.append(f"Known Entity References: {refs_str}")

        tags = signal_dict.get("tags", [])
        if tags:
            prompt_parts.append(f"Tags: {', '.join(tags[:10])}")

        return "\n".join(prompt_parts)

    # ── LLM Output Parsing & Validation ────────────────────────────────────

    def _parse_and_validate(
        self,
        raw_response: str,
        result: MappingResult,
    ) -> Optional[AIExtractionResult]:
        """Parse LLM response into a validated AIExtractionResult.

        Returns None if parsing fails (error captured in result.warnings).
        Individual entities/relationships that fail validation are dropped,
        not the entire batch.
        """
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            # Try to extract JSON from markdown fences
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    result.warnings.append(f"AI returned invalid JSON: {exc}")
                    return None
            else:
                result.warnings.append(f"AI returned invalid JSON: {exc}")
                return None

        # Validate entities individually (drop bad ones, keep good ones)
        valid_entities: list[AIExtractedEntity] = []
        for raw_ent in data.get("entities", []):
            try:
                ent = AIExtractedEntity(**raw_ent)
                if ent.confidence >= self._min_entity_conf:
                    valid_entities.append(ent)
                else:
                    result.decisions.append(MappingDecision(
                        stage="ai_validation", action="skip",
                        element_id=f"ai_entity:{raw_ent.get('name', '?')}",
                        reason=f"Below confidence threshold: {ent.confidence:.2f} < {self._min_entity_conf}",
                        confidence=str(ent.confidence),
                    ))
            except Exception as exc:
                result.warnings.append(f"AI entity validation failed: {raw_ent} — {exc}")

        # Validate relationships individually
        valid_rels: list[AIExtractedRelationship] = []
        for raw_rel in data.get("relationships", []):
            try:
                rel = AIExtractedRelationship(**raw_rel)
                if rel.confidence >= self._min_rel_conf:
                    valid_rels.append(rel)
                else:
                    result.decisions.append(MappingDecision(
                        stage="ai_validation", action="skip",
                        element_id=f"ai_rel:{raw_rel.get('source', '?')}->{raw_rel.get('target', '?')}",
                        reason=f"Below confidence threshold: {rel.confidence:.2f} < {self._min_rel_conf}",
                    ))
            except Exception as exc:
                result.warnings.append(f"AI relationship validation failed: {raw_rel} — {exc}")

        return AIExtractionResult(
            entities=valid_entities,
            relationships=valid_rels,
            reasoning=data.get("reasoning", ""),
            overall_confidence=data.get("overall_confidence", 0.0),
        )

    # ── Graph Element Construction ─────────────────────────────────────────

    def _build_graph_elements(
        self,
        signal_dict: dict,
        extraction: AIExtractionResult,
        result: MappingResult,
    ) -> None:
        """Convert validated AIExtractionResult into GraphNodes and GraphEdges."""
        signal_id = signal_dict.get("signal_id", "unknown")
        event_node_id = f"event:{signal_id}"

        ref = GraphSourceRef(
            source_type="ai_extractor",
            source_id=signal_id,
            source_field="llm_extraction",
        )

        # Build a name→node_id map for relationship resolution
        name_to_node_id: dict[str, str] = {}

        # Create entity nodes
        for ent in extraction.entities:
            entity_type = GraphEntityType(ent.type)
            node_id = f"ai_{entity_type.value}:{_slug(ent.name)}"
            name_to_node_id[ent.name] = node_id

            conf = _score_to_graph_confidence(ent.confidence)
            node = GraphNode(
                node_id=node_id,
                entity_type=entity_type,
                label=ent.name,
                confidence=conf,
                properties={
                    **ent.properties,
                    "ai_extracted": True,
                    "ai_confidence": ent.confidence,
                },
                source_refs=[ref],
            )
            result.nodes.append(node)
            result.decisions.append(MappingDecision(
                stage="ai_entity_extraction",
                action="create_node",
                element_id=node_id,
                reason=f"AI extracted entity '{ent.name}' (type={ent.type}, conf={ent.confidence:.2f})",
                confidence=conf.value,
            ))

            # Link event → AI entity
            edge = GraphEdge(
                edge_id=f"{event_node_id}--affects-->{node_id}",
                source_id=event_node_id,
                target_id=node_id,
                relation_type=GraphRelationType.AFFECTS,
                label=f"Event affects AI-extracted {ent.name}",
                weight=ent.confidence,
                confidence=conf,
                source_refs=[ref],
            )
            result.edges.append(edge)

        # Create relationship edges
        for rel in extraction.relationships:
            src_id = name_to_node_id.get(rel.source)
            tgt_id = name_to_node_id.get(rel.target)
            if not src_id or not tgt_id:
                result.decisions.append(MappingDecision(
                    stage="ai_relationship_inference",
                    action="skip",
                    element_id=f"ai_rel:{rel.source}->{rel.target}",
                    reason=f"Endpoint not found in extracted entities (src={src_id}, tgt={tgt_id})",
                ))
                continue
            if src_id == tgt_id:
                continue  # no self-loops

            rel_type = GraphRelationType(rel.type)
            conf = _score_to_graph_confidence(rel.confidence)
            edge = GraphEdge(
                edge_id=f"{src_id}--{rel_type.value}-->{tgt_id}",
                source_id=src_id,
                target_id=tgt_id,
                relation_type=rel_type,
                label=f"AI-inferred: {rel.source} {rel_type.value} {rel.target}",
                weight=rel.confidence,
                confidence=conf,
                properties={"ai_inferred": True, "ai_confidence": rel.confidence},
                source_refs=[ref],
            )
            result.edges.append(edge)
            result.decisions.append(MappingDecision(
                stage="ai_relationship_inference",
                action="create_edge",
                element_id=edge.edge_id,
                reason=f"AI inferred: {rel.source} --[{rel_type.value}]--> {rel.target} (conf={rel.confidence:.2f})",
                confidence=conf.value,
            ))


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _slug(name: str) -> str:
    """Normalize entity name into a stable node ID slug."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _score_to_graph_confidence(score: float) -> GraphConfidence:
    """Map a 0.0-1.0 confidence score to a GraphConfidence tier."""
    if score >= 0.90:
        return GraphConfidence.DEFINITIVE
    if score >= 0.75:
        return GraphConfidence.HIGH
    if score >= 0.55:
        return GraphConfidence.MODERATE
    if score >= 0.30:
        return GraphConfidence.LOW
    return GraphConfidence.SPECULATIVE
