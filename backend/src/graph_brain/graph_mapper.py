"""Graph Expansion Layer — Signal-to-KG Mapper.

Transforms a MacroSignal (v1 ingestion schema) into a rich set of
GraphNode and GraphEdge instances ready for Neo4j persistence.

Architecture Layer: Features → Models (Layer 2-3 of the 7-layer stack)
Owner: Graph Expansion Pipeline
Consumers: Neo4j Writer, In-Memory GraphStore, Observability

Design Principles:
  1. Pure functions: deterministic mapping (same signal → same graph elements)
  2. Idempotent: re-processing produces identical node/edge IDs
  3. Extensible: new payload types register a mapper via PAYLOAD_MAPPERS dict
  4. Non-destructive: never deletes existing graph elements
  5. Observable: every mapping decision is logged and returned in MappingResult

Mapping Strategy (per signal):
  Signal → (:Signal) node
  Signal → (:Event) node   [promoted from signal]
  (:Signal)-[:TRIGGERS]->(:Event)
  Source  → (:Source) node
  (:Source)-[:EMITTED]->(:Signal)
  Payload → domain-specific entities + relationships
  EntityRefs → pre-linked (:Entity) nodes + edges
  Tags → (:Tag) nodes + edges
  Geo → (:Region)/(:GeoZone) nodes + edges
  Lineage → (:Signal)-[:DERIVED_FROM]->(:Signal)

Node ID conventions:
  signal:{signal_id}
  event:{signal_id}
  source:{source_id}
  tag:{tag_name}
  region:{region_code}
  indicator:{indicator_code}
  org:{entity_id}
  infra:{system_id}
  sector:{sector_name}
  lob:{line_of_business}
  geopolitical_event:{signal_id}
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)

logger = logging.getLogger("graph_brain.mapper")


# ═══════════════════════════════════════════════════════════════════════════════
# Mapping Result — observable output contract
# ═══════════════════════════════════════════════════════════════════════════════

class MappingDecision(BaseModel):
    """A single logged mapping decision for observability."""
    stage: str = Field(..., description="Mapping stage that produced this decision")
    action: str = Field(..., description="create_node | create_edge | skip | infer")
    element_id: str = Field(..., description="Node or edge ID affected")
    reason: str = Field(default="", description="Why this decision was made")
    confidence: str = Field(default="moderate")


class MappingResult(BaseModel):
    """Full output of a signal-to-graph mapping pass.

    Returned to callers for debugging and API response augmentation.
    Does NOT mutate any store — pure data container.
    """
    signal_id: str = ""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    decisions: list[MappingDecision] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    payload_type: str = ""
    duration_ms: float = 0.0

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def node_ids(self) -> list[str]:
        return [n.node_id for n in self.nodes]

    @property
    def edge_ids(self) -> list[str]:
        return [e.edge_id for e in self.edges]

    def summary(self) -> dict[str, Any]:
        """Compact summary for API response embedding."""
        return {
            "signal_id": self.signal_id,
            "nodes_mapped": self.node_count,
            "edges_mapped": self.edge_count,
            "payload_type": self.payload_type,
            "decisions_count": len(self.decisions),
            "warnings": self.warnings,
            "duration_ms": round(self.duration_ms, 2),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — ID generation, provenance, confidence mapping
# ═══════════════════════════════════════════════════════════════════════════════

def _edge_id(source_id: str, relation: str, target_id: str) -> str:
    """Deterministic edge ID: {source}--{relation}-->{target}."""
    return f"{source_id}--{relation}-->{target_id}"


def _source_ref(signal_id: str, field: str = "") -> GraphSourceRef:
    """Create provenance back-reference to the originating MacroSignal."""
    return GraphSourceRef(
        source_type="macro_signal",
        source_id=signal_id,
        source_field=field or None,
    )


def _severity_to_confidence(severity_score: float) -> GraphConfidence:
    """Map numeric severity to graph confidence for inferred entities."""
    if severity_score >= 0.80:
        return GraphConfidence.HIGH
    if severity_score >= 0.50:
        return GraphConfidence.MODERATE
    if severity_score >= 0.20:
        return GraphConfidence.LOW
    return GraphConfidence.SPECULATIVE


def _quality_to_confidence(confidence_score: float) -> GraphConfidence:
    """Map quality.confidence_score to graph confidence."""
    if confidence_score >= 0.85:
        return GraphConfidence.HIGH
    if confidence_score >= 0.60:
        return GraphConfidence.MODERATE
    if confidence_score >= 0.35:
        return GraphConfidence.LOW
    return GraphConfidence.SPECULATIVE


# ═══════════════════════════════════════════════════════════════════════════════
# Core Node Factories (domain-agnostic)
# ═══════════════════════════════════════════════════════════════════════════════

def _signal_node(sig: dict, ref: GraphSourceRef, conf: GraphConfidence) -> GraphNode:
    """(:Signal) node — the raw signal as a graph entity."""
    return GraphNode(
        node_id=f"signal:{sig['signal_id']}",
        entity_type=GraphEntityType.SIGNAL,
        label=sig["title"],
        confidence=conf,
        properties={
            "signal_type": sig.get("signal_type", ""),
            "domain": sig.get("domain", ""),
            "severity": sig.get("severity", "NOMINAL"),
            "severity_score": sig.get("severity_score", 0.0),
            "status": sig.get("status", "RAW"),
            "schema_version": sig.get("schema_version", "1.0.0"),
        },
        source_refs=[ref],
    )


def _event_node(sig: dict, ref: GraphSourceRef, conf: GraphConfidence) -> GraphNode:
    """(:Event) node — the signal promoted to a discrete event."""
    return GraphNode(
        node_id=f"event:{sig['signal_id']}",
        entity_type=GraphEntityType.EVENT,
        label=sig["title"],
        confidence=conf,
        properties={
            "event_type": sig.get("signal_type", ""),
            "domain": sig.get("domain", ""),
            "severity_score": sig.get("severity_score", 0.0),
            "severity_level": sig.get("severity", "NOMINAL"),
            "event_time": sig.get("temporal", {}).get("event_time", ""),
            "source_signal_id": sig["signal_id"],
        },
        source_refs=[ref],
    )


def _source_node(source: dict, ref: GraphSourceRef) -> GraphNode:
    """(:Source) node — the originating system."""
    sid = source.get("source_id", "unknown")
    label = source.get("source_name") or sid
    return GraphNode(
        node_id=f"source:{sid}",
        entity_type=GraphEntityType.ORGANIZATION,
        label=label,
        confidence=GraphConfidence.DEFINITIVE,
        properties={
            "source_type": source.get("source_type", ""),
            "trust_score": source.get("trust_score", 0.5),
            "source_url": source.get("source_url", ""),
            "source_version": source.get("source_version", ""),
        },
        source_refs=[ref],
    )


def _tag_node(tag: str) -> GraphNode:
    """(:Tag) node — free-form classification tag."""
    normalized = tag.strip().lower()
    return GraphNode(
        node_id=f"tag:{normalized}",
        entity_type=GraphEntityType.RISK_FACTOR,
        label=normalized,
        confidence=GraphConfidence.DEFINITIVE,
        properties={"tag_key": normalized},
        source_refs=[],
    )


def _region_node(region_code: str, region_name: str, ref: GraphSourceRef) -> GraphNode:
    """(:Region) or (:Country) node from geo context."""
    normalized = region_code.strip().upper()
    return GraphNode(
        node_id=f"region:{normalized}",
        entity_type=GraphEntityType.COUNTRY,
        label=region_name or normalized,
        confidence=GraphConfidence.DEFINITIVE,
        properties={"region_code": normalized},
        source_refs=[ref],
    )


def _sector_node(sector: str, ref: GraphSourceRef) -> GraphNode:
    """(:Sector) node — economic sector."""
    normalized = sector.strip().lower().replace(" ", "_")
    return GraphNode(
        node_id=f"sector:{normalized}",
        entity_type=GraphEntityType.SECTOR,
        label=sector.strip(),
        confidence=GraphConfidence.HIGH,
        properties={"sector_key": normalized},
        source_refs=[ref],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Core Edge Factories (domain-agnostic)
# ═══════════════════════════════════════════════════════════════════════════════

def _make_edge(
    source_id: str,
    target_id: str,
    relation: GraphRelationType,
    label: str,
    weight: float,
    confidence: GraphConfidence,
    ref: GraphSourceRef,
    properties: Optional[dict[str, Any]] = None,
) -> GraphEdge:
    """Generic edge factory with deterministic ID."""
    return GraphEdge(
        edge_id=_edge_id(source_id, relation.value, target_id),
        source_id=source_id,
        target_id=target_id,
        relation_type=relation,
        label=label,
        weight=min(max(weight, 0.0), 1.0),
        confidence=confidence,
        properties=properties or {},
        source_refs=[ref],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Domain-Specific Payload Mappers
# ═══════════════════════════════════════════════════════════════════════════════

def _map_macroeconomic_payload(
    sig: dict,
    event_node_id: str,
    payload: dict,
    ref: GraphSourceRef,
    result: MappingResult,
) -> None:
    """Extract entities and relationships from MacroeconomicPayload.

    Creates:
      - (:Indicator) node for the economic indicator
      - (:Event)-[:IMPACTS]->(:Indicator)
      - (:Indicator)-[:AFFECTS]->(:Sector) for each affected sector
    """
    indicator_code = payload.get("indicator_code", "")
    if not indicator_code:
        result.warnings.append("MacroeconomicPayload missing indicator_code")
        return

    # Indicator node
    ind_id = f"indicator:{indicator_code.lower()}"
    ind_node = GraphNode(
        node_id=ind_id,
        entity_type=GraphEntityType.INDICATOR,
        label=payload.get("indicator_name", indicator_code),
        confidence=GraphConfidence.DEFINITIVE,
        properties={
            "indicator_code": indicator_code,
            "value": payload.get("value"),
            "unit": payload.get("unit", ""),
            "previous_value": payload.get("previous_value"),
            "delta_pct": payload.get("delta_pct"),
            "surprise_factor": payload.get("surprise_factor"),
            "frequency": payload.get("frequency", ""),
        },
        source_refs=[ref],
    )
    result.nodes.append(ind_node)
    result.decisions.append(MappingDecision(
        stage="macroeconomic_payload", action="create_node",
        element_id=ind_id, reason=f"Indicator {indicator_code} from payload",
        confidence="definitive",
    ))

    # Event → Indicator edge
    severity = sig.get("severity_score", 0.5)
    edge = _make_edge(
        event_node_id, ind_id, GraphRelationType.AFFECTS,
        f"Event impacts {indicator_code}", weight=severity,
        confidence=_severity_to_confidence(severity), ref=ref,
        properties={"delta_pct": payload.get("delta_pct"), "value": payload.get("value")},
    )
    result.edges.append(edge)
    result.decisions.append(MappingDecision(
        stage="macroeconomic_payload", action="create_edge",
        element_id=edge.edge_id, reason=f"Event impacts indicator {indicator_code}",
    ))

    # Indicator → Sector edges for affected sectors
    for sector in payload.get("affected_sectors", []):
        sec_node = _sector_node(sector, ref)
        result.nodes.append(sec_node)
        sec_edge = _make_edge(
            ind_id, sec_node.node_id, GraphRelationType.AFFECTS,
            f"{indicator_code} affects {sector}", weight=severity * 0.85,
            confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(sec_edge)
        result.decisions.append(MappingDecision(
            stage="macroeconomic_payload", action="create_edge",
            element_id=sec_edge.edge_id,
            reason=f"Indicator {indicator_code} propagates to sector {sector}",
        ))


def _map_insurance_payload(
    sig: dict,
    event_node_id: str,
    payload: dict,
    ref: GraphSourceRef,
    result: MappingResult,
) -> None:
    """Extract entities and relationships from InsurancePayload.

    Creates:
      - (:Sector) node for line of business
      - (:Event)-[:AFFECTS]->(:Sector:LOB)
      - (:Organization) nodes for affected entities
      - (:Event)-[:IMPACTS]->(:Organization)
      - If reinsurance_triggered: (:Event)-[:TRIGGERED_BY]->(:RiskFactor:Reinsurance)
    """
    lob = payload.get("line_of_business", "")
    if not lob:
        result.warnings.append("InsurancePayload missing line_of_business")
        return

    severity = sig.get("severity_score", 0.5)

    # Line of business as sector node
    lob_id = f"lob:{lob.lower().replace(' ', '_')}"
    lob_node = GraphNode(
        node_id=lob_id,
        entity_type=GraphEntityType.SECTOR,
        label=f"Insurance - {lob.replace('_', ' ').title()}",
        confidence=GraphConfidence.HIGH,
        properties={
            "line_of_business": lob,
            "estimated_loss_usd": payload.get("estimated_loss_usd", 0),
            "insured_loss_usd": payload.get("insured_loss_usd"),
            "claims_count": payload.get("claims_count"),
            "combined_ratio_impact": payload.get("combined_ratio_impact"),
            "reserve_adequacy_ratio": payload.get("reserve_adequacy_ratio"),
            "ifrs17_impact": payload.get("ifrs17_impact"),
        },
        source_refs=[ref],
    )
    result.nodes.append(lob_node)
    result.decisions.append(MappingDecision(
        stage="insurance_payload", action="create_node",
        element_id=lob_id, reason=f"LOB {lob} from insurance payload",
    ))

    # Event → LOB edge
    edge = _make_edge(
        event_node_id, lob_id, GraphRelationType.AFFECTS,
        f"Event affects {lob}", weight=severity,
        confidence=_severity_to_confidence(severity), ref=ref,
        properties={"estimated_loss_usd": payload.get("estimated_loss_usd", 0)},
    )
    result.edges.append(edge)
    result.decisions.append(MappingDecision(
        stage="insurance_payload", action="create_edge",
        element_id=edge.edge_id, reason=f"Claims event impacts LOB {lob}",
    ))

    # Affected entities → Organization nodes
    for ent_id in payload.get("affected_entities", []):
        org_id = f"org:{ent_id}"
        org_node = GraphNode(
            node_id=org_id,
            entity_type=GraphEntityType.ORGANIZATION,
            label=ent_id.replace("ent_", "").replace("_", " ").title(),
            confidence=GraphConfidence.MODERATE,
            properties={"entity_ref": ent_id},
            source_refs=[ref],
        )
        result.nodes.append(org_node)
        org_edge = _make_edge(
            event_node_id, org_id, GraphRelationType.AFFECTS,
            f"Event impacts {ent_id}", weight=severity * 0.9,
            confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(org_edge)
        result.decisions.append(MappingDecision(
            stage="insurance_payload", action="create_edge",
            element_id=org_edge.edge_id,
            reason=f"Insurance event impacts org {ent_id}",
        ))

    # Reinsurance trigger → risk factor
    if payload.get("reinsurance_triggered"):
        rf_id = "risk_factor:reinsurance_trigger"
        rf_node = GraphNode(
            node_id=rf_id,
            entity_type=GraphEntityType.RISK_FACTOR,
            label="Reinsurance Trigger Activated",
            confidence=GraphConfidence.HIGH,
            properties={"trigger_type": "reinsurance", "ifrs17_impact": payload.get("ifrs17_impact")},
            source_refs=[ref],
        )
        result.nodes.append(rf_node)
        rf_edge = _make_edge(
            event_node_id, rf_id, GraphRelationType.TRIGGERED_BY,
            "Event triggers reinsurance", weight=severity,
            confidence=GraphConfidence.HIGH, ref=ref,
        )
        result.edges.append(rf_edge)
        result.decisions.append(MappingDecision(
            stage="insurance_payload", action="create_edge",
            element_id=rf_edge.edge_id, reason="Reinsurance triggered by claims event",
            confidence="high",
        ))


def _map_operational_payload(
    sig: dict,
    event_node_id: str,
    payload: dict,
    ref: GraphSourceRef,
    result: MappingResult,
) -> None:
    """Extract entities and relationships from OperationalPayload.

    Creates:
      - (:Infrastructure) node for affected system
      - (:Event)-[:DISRUPTS]->(:Infrastructure)
      - (:Infrastructure)-[:DEPENDS_ON]->(:Infrastructure) for upstream
      - (:Infrastructure)-[:PROPAGATES_TO]->(:Infrastructure) for downstream
      - (:Sector) nodes for affected flow types
    """
    system_id = payload.get("system_id", "")
    if not system_id:
        result.warnings.append("OperationalPayload missing system_id")
        return

    severity = payload.get("severity_score", sig.get("severity_score", 0.5))

    # Infrastructure node
    infra_id = f"infra:{system_id}"
    infra_node = GraphNode(
        node_id=infra_id,
        entity_type=GraphEntityType.INFRASTRUCTURE,
        label=payload.get("system_name", system_id),
        confidence=GraphConfidence.HIGH,
        properties={
            "system_id": system_id,
            "incident_type": payload.get("incident_type", ""),
            "capacity_impact_pct": payload.get("capacity_impact_pct"),
            "estimated_downtime_hours": payload.get("estimated_downtime_hours"),
            "estimated_recovery_hours": payload.get("estimated_recovery_hours"),
        },
        source_refs=[ref],
    )
    result.nodes.append(infra_node)
    result.decisions.append(MappingDecision(
        stage="operational_payload", action="create_node",
        element_id=infra_id,
        reason=f"Infrastructure {system_id} from operational payload",
    ))

    # Event → Infrastructure DISRUPTS edge
    edge = _make_edge(
        event_node_id, infra_id, GraphRelationType.AFFECTS,
        f"Event disrupts {system_id}", weight=severity,
        confidence=_severity_to_confidence(severity), ref=ref,
        properties={
            "capacity_impact_pct": payload.get("capacity_impact_pct"),
            "estimated_downtime_hours": payload.get("estimated_downtime_hours"),
        },
    )
    result.edges.append(edge)
    result.decisions.append(MappingDecision(
        stage="operational_payload", action="create_edge",
        element_id=edge.edge_id, reason=f"Event disrupts infrastructure {system_id}",
    ))

    # Upstream dependencies: Infrastructure ← DEPENDS_ON ← upstream
    for up_id in payload.get("upstream_dependencies", []):
        up_node_id = f"infra:{up_id}"
        up_node = GraphNode(
            node_id=up_node_id,
            entity_type=GraphEntityType.INFRASTRUCTURE,
            label=up_id.replace("node_", "").replace("_", " ").title(),
            confidence=GraphConfidence.MODERATE,
            properties={"system_id": up_id, "relationship_context": "upstream_dependency"},
            source_refs=[ref],
        )
        result.nodes.append(up_node)
        dep_edge = _make_edge(
            infra_id, up_node_id, GraphRelationType.DEPENDS_ON,
            f"{system_id} depends on {up_id}", weight=0.8,
            confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(dep_edge)
        result.decisions.append(MappingDecision(
            stage="operational_payload", action="create_edge",
            element_id=dep_edge.edge_id,
            reason=f"Upstream dependency: {system_id} → {up_id}",
        ))

    # Downstream dependents: Infrastructure → PROPAGATES_TO → downstream
    for down_id in payload.get("downstream_dependents", []):
        down_node_id = f"infra:{down_id}" if not down_id.startswith("ent_") else f"org:{down_id}"
        entity_type = GraphEntityType.INFRASTRUCTURE if not down_id.startswith("ent_") else GraphEntityType.ORGANIZATION
        down_node = GraphNode(
            node_id=down_node_id,
            entity_type=entity_type,
            label=down_id.replace("node_", "").replace("ent_", "").replace("_", " ").title(),
            confidence=GraphConfidence.MODERATE,
            properties={"ref_id": down_id, "relationship_context": "downstream_dependent"},
            source_refs=[ref],
        )
        result.nodes.append(down_node)
        prop_edge = _make_edge(
            infra_id, down_node_id, GraphRelationType.PROPAGATES_TO,
            f"Disruption propagates from {system_id} to {down_id}",
            weight=severity * 0.75, confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(prop_edge)
        result.decisions.append(MappingDecision(
            stage="operational_payload", action="create_edge",
            element_id=prop_edge.edge_id,
            reason=f"Downstream propagation: {system_id} → {down_id}",
        ))

    # Affected flow types → Sector nodes
    for flow in payload.get("affected_flow_types", []):
        flow_node = _sector_node(flow, ref)
        result.nodes.append(flow_node)
        flow_edge = _make_edge(
            infra_id, flow_node.node_id, GraphRelationType.AFFECTS,
            f"Infrastructure {system_id} disrupts {flow} flows",
            weight=severity * 0.7, confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(flow_edge)
        result.decisions.append(MappingDecision(
            stage="operational_payload", action="create_edge",
            element_id=flow_edge.edge_id,
            reason=f"Flow type {flow} affected by {system_id} disruption",
        ))


def _map_geopolitical_payload(
    sig: dict,
    event_node_id: str,
    payload: dict,
    ref: GraphSourceRef,
    result: MappingResult,
) -> None:
    """Extract entities and relationships from GeopoliticalPayload.

    Creates:
      - (:Event) already exists — enrich with geopolitical properties
      - (:Organization) or actor nodes for state/non-state actors
      - (:Event)-[:INVOLVES]->(actor)
      - (:Infrastructure:Chokepoint) for affected trade routes
      - (:Event)-[:DISRUPTS]->(:Chokepoint)
    """
    event_type = payload.get("event_type", "")
    severity = sig.get("severity_score", 0.5)

    # Actor nodes
    for actor in payload.get("actors", []):
        actor_normalized = actor.strip().lower().replace(" ", "_")
        actor_id = f"actor:{actor_normalized}"
        actor_node = GraphNode(
            node_id=actor_id,
            entity_type=GraphEntityType.ORGANIZATION,
            label=actor.strip(),
            confidence=GraphConfidence.MODERATE,
            properties={"actor_type": "geopolitical", "event_type": event_type},
            source_refs=[ref],
        )
        result.nodes.append(actor_node)
        actor_edge = _make_edge(
            event_node_id, actor_id, GraphRelationType.INFLUENCES,
            f"Event involves {actor}", weight=severity * 0.9,
            confidence=GraphConfidence.MODERATE, ref=ref,
        )
        result.edges.append(actor_edge)
        result.decisions.append(MappingDecision(
            stage="geopolitical_payload", action="create_edge",
            element_id=actor_edge.edge_id, reason=f"Actor {actor} involved in event",
        ))

    # Affected trade routes → Chokepoint/Infrastructure nodes
    for route in payload.get("affected_trade_routes", []):
        route_normalized = route.strip().lower().replace(" ", "_")
        route_id = f"chokepoint:{route_normalized}"
        route_node = GraphNode(
            node_id=route_id,
            entity_type=GraphEntityType.CHOKEPOINT,
            label=route.strip().replace("_", " ").title(),
            confidence=GraphConfidence.HIGH,
            properties={"route_key": route_normalized, "disruption_context": event_type},
            source_refs=[ref],
        )
        result.nodes.append(route_node)
        route_edge = _make_edge(
            event_node_id, route_id, GraphRelationType.AFFECTS,
            f"Event disrupts trade route {route}",
            weight=severity, confidence=_severity_to_confidence(severity), ref=ref,
        )
        result.edges.append(route_edge)
        result.decisions.append(MappingDecision(
            stage="geopolitical_payload", action="create_edge",
            element_id=route_edge.edge_id,
            reason=f"Trade route {route} disrupted by geopolitical event",
        ))


# ── Payload mapper registry ───────────────────────────────────────────────

PayloadMapperFn = Callable[
    [dict, str, dict, GraphSourceRef, MappingResult], None
]

PAYLOAD_MAPPERS: dict[str, PayloadMapperFn] = {
    "macroeconomic": _map_macroeconomic_payload,
    "insurance": _map_insurance_payload,
    "operational": _map_operational_payload,
    "geopolitical": _map_geopolitical_payload,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Main Mapping Function — the public API
# ═══════════════════════════════════════════════════════════════════════════════

def map_signal_to_graph(signal_dict: dict) -> MappingResult:
    """Transform a MacroSignal dict into a list of GraphNodes and GraphEdges.

    This is the primary entry point for the Graph Expansion Layer.
    Input is the dict form of a MacroSignal (from .model_dump()).

    Args:
        signal_dict: MacroSignal serialized as dict.

    Returns:
        MappingResult containing all nodes, edges, and decisions.

    Design contract:
        - Pure function: no side effects, no store mutations
        - Deterministic: same input → same output
        - Never raises: errors are captured as warnings in MappingResult
    """
    import time
    t0 = time.monotonic()
    result = MappingResult()

    try:
        signal_id = signal_dict.get("signal_id", "")
        result.signal_id = signal_id
        ref = _source_ref(signal_id)

        # Determine confidence from quality indicators
        quality = signal_dict.get("quality", {})
        conf_score = quality.get("confidence_score", 0.5)
        graph_conf = _quality_to_confidence(conf_score)

        # ── 1. Signal node ─────────────────────────────────────────────
        sig_node = _signal_node(signal_dict, ref, graph_conf)
        result.nodes.append(sig_node)
        result.decisions.append(MappingDecision(
            stage="core", action="create_node",
            element_id=sig_node.node_id, reason="Signal identity node",
        ))

        # ── 2. Event node (promoted from signal) ──────────────────────
        evt_node = _event_node(signal_dict, ref, graph_conf)
        result.nodes.append(evt_node)
        result.decisions.append(MappingDecision(
            stage="core", action="create_node",
            element_id=evt_node.node_id, reason="Event promoted from signal",
        ))

        # ── 3. Signal → Event TRIGGERS edge ───────────────────────────
        triggers_edge = _make_edge(
            sig_node.node_id, evt_node.node_id,
            GraphRelationType.TRIGGERED_BY,
            "Signal triggers event",
            weight=1.0, confidence=GraphConfidence.DEFINITIVE, ref=ref,
        )
        result.edges.append(triggers_edge)
        result.decisions.append(MappingDecision(
            stage="core", action="create_edge",
            element_id=triggers_edge.edge_id,
            reason="Signal-to-Event promotion link",
            confidence="definitive",
        ))

        # ── 4. Source node + Source → Signal EMITTED edge ─────────────
        source = signal_dict.get("source", {})
        if source.get("source_id"):
            src_node = _source_node(source, ref)
            result.nodes.append(src_node)
            emitted_edge = _make_edge(
                src_node.node_id, sig_node.node_id,
                GraphRelationType.LINKED_TO,
                f"Source {source['source_id']} emitted signal",
                weight=source.get("trust_score", 0.5),
                confidence=GraphConfidence.HIGH, ref=ref,
            )
            result.edges.append(emitted_edge)
            result.decisions.append(MappingDecision(
                stage="source", action="create_edge",
                element_id=emitted_edge.edge_id,
                reason=f"Source {source['source_id']} emitted this signal",
            ))

        # ── 5. Geo context → Region/Country nodes ────────────────────
        geo = signal_dict.get("geo") or {}
        if geo.get("region_code"):
            region = _region_node(
                geo["region_code"],
                geo.get("region_name", geo["region_code"]),
                ref,
            )
            result.nodes.append(region)
            geo_edge = _make_edge(
                evt_node.node_id, region.node_id,
                GraphRelationType.LOCATED_IN,
                f"Event located in {geo['region_code']}",
                weight=1.0, confidence=GraphConfidence.DEFINITIVE, ref=ref,
            )
            result.edges.append(geo_edge)
            result.decisions.append(MappingDecision(
                stage="geo", action="create_edge",
                element_id=geo_edge.edge_id,
                reason=f"Event geolocated to {geo['region_code']}",
                confidence="definitive",
            ))

        # Affected zones → additional relationships
        for zone in geo.get("affected_zones", []):
            zone_id = f"infra:{zone}"
            zone_node = GraphNode(
                node_id=zone_id,
                entity_type=GraphEntityType.INFRASTRUCTURE,
                label=zone.replace("_", " ").title(),
                confidence=GraphConfidence.MODERATE,
                properties={"zone_key": zone},
                source_refs=[ref],
            )
            result.nodes.append(zone_node)
            zone_edge = _make_edge(
                evt_node.node_id, zone_id, GraphRelationType.AFFECTS,
                f"Event affects zone {zone}",
                weight=signal_dict.get("severity_score", 0.5),
                confidence=GraphConfidence.MODERATE, ref=ref,
            )
            result.edges.append(zone_edge)
            result.decisions.append(MappingDecision(
                stage="geo", action="create_edge",
                element_id=zone_edge.edge_id,
                reason=f"Affected zone {zone} linked to event",
            ))

        # ── 6. Tags → Tag nodes ──────────────────────────────────────
        for tag in signal_dict.get("tags", []):
            t_node = _tag_node(tag)
            result.nodes.append(t_node)
            t_edge = _make_edge(
                evt_node.node_id, t_node.node_id,
                GraphRelationType.LINKED_TO,
                f"Event tagged with '{tag}'",
                weight=0.3, confidence=GraphConfidence.MODERATE, ref=ref,
            )
            result.edges.append(t_edge)

        # ── 7. Entity references → pre-linked entities ───────────────
        for eref in signal_dict.get("entity_refs", []):
            ent_id = eref.get("entity_id", "")
            if not ent_id:
                continue
            ent_type_str = eref.get("entity_type", "Organization")
            # Map entity_type string to GraphEntityType
            type_map = {
                "Organization": GraphEntityType.ORGANIZATION,
                "Port": GraphEntityType.INFRASTRUCTURE,
                "Pipeline": GraphEntityType.INFRASTRUCTURE,
                "Chokepoint": GraphEntityType.CHOKEPOINT,
                "Country": GraphEntityType.COUNTRY,
                "TradeRoute": GraphEntityType.CHOKEPOINT,
                "Regulator": GraphEntityType.REGULATOR,
                "Market": GraphEntityType.MARKET,
            }
            g_type = type_map.get(ent_type_str, GraphEntityType.ORGANIZATION)
            prefix = g_type.value if g_type != GraphEntityType.ORGANIZATION else "org"

            ent_node_id = f"{prefix}:{ent_id}"
            ent_node = GraphNode(
                node_id=ent_node_id,
                entity_type=g_type,
                label=eref.get("entity_label", ent_id),
                confidence=_quality_to_confidence(eref.get("confidence", 0.8)),
                properties={"source_entity_id": ent_id, "entity_type_hint": ent_type_str},
                source_refs=[ref],
            )
            result.nodes.append(ent_node)

            # Map relationship_type string to GraphRelationType
            rel_map = {
                "AFFECTS": GraphRelationType.AFFECTS,
                "MENTIONS": GraphRelationType.LINKED_TO,
                "ORIGINATES_FROM": GraphRelationType.TRIGGERED_BY,
                "DEPENDS_ON": GraphRelationType.DEPENDS_ON,
            }
            rel_type = rel_map.get(
                eref.get("relationship_type", "AFFECTS"),
                GraphRelationType.AFFECTS,
            )
            ent_edge = _make_edge(
                evt_node.node_id, ent_node_id, rel_type,
                f"Event {rel_type.value} {eref.get('entity_label', ent_id)}",
                weight=eref.get("confidence", 0.8),
                confidence=_quality_to_confidence(eref.get("confidence", 0.8)),
                ref=ref,
            )
            result.edges.append(ent_edge)
            result.decisions.append(MappingDecision(
                stage="entity_refs", action="create_edge",
                element_id=ent_edge.edge_id,
                reason=f"Pre-linked entity ref: {ent_id} ({rel_type.value})",
            ))

        # ── 8. Lineage → parent signal derivation chain ──────────────
        lineage = signal_dict.get("lineage", {})
        for parent_id in lineage.get("parent_signal_ids", []):
            parent_node_id = f"signal:{parent_id}"
            derive_edge = _make_edge(
                sig_node.node_id, parent_node_id,
                GraphRelationType.DERIVED_FROM,
                f"Signal derived from {parent_id}",
                weight=1.0, confidence=GraphConfidence.DEFINITIVE, ref=ref,
            )
            result.edges.append(derive_edge)
            result.decisions.append(MappingDecision(
                stage="lineage", action="create_edge",
                element_id=derive_edge.edge_id,
                reason=f"Lineage derivation from parent {parent_id}",
                confidence="definitive",
            ))

        # ── 9. Domain-specific payload mapping ───────────────────────
        payload = signal_dict.get("payload", {})
        payload_type = payload.get("payload_type", "")
        result.payload_type = payload_type

        mapper = PAYLOAD_MAPPERS.get(payload_type)
        if mapper:
            mapper(signal_dict, evt_node.node_id, payload, ref, result)
            result.decisions.append(MappingDecision(
                stage="payload", action="create_node",
                element_id=f"payload:{payload_type}",
                reason=f"Payload mapper '{payload_type}' executed",
            ))
        elif payload_type:
            result.warnings.append(
                f"No payload mapper registered for type '{payload_type}'. "
                f"Domain-specific entities not extracted. "
                f"Signal core mapping still applied."
            )
            result.decisions.append(MappingDecision(
                stage="payload", action="skip",
                element_id=f"payload:{payload_type}",
                reason=f"Unknown payload type '{payload_type}' — skipped",
            ))

        # ── 10. Cross-entity inference: sectors → region ─────────────
        # If we have both sector and region nodes, link them
        region_nodes = [n for n in result.nodes if n.entity_type == GraphEntityType.COUNTRY]
        sector_nodes = [n for n in result.nodes if n.entity_type == GraphEntityType.SECTOR]
        for r_node in region_nodes:
            for s_node in sector_nodes:
                cross_edge = _make_edge(
                    s_node.node_id, r_node.node_id,
                    GraphRelationType.OPERATES_IN,
                    f"{s_node.label} operates in {r_node.label}",
                    weight=0.6, confidence=GraphConfidence.MODERATE, ref=ref,
                )
                result.edges.append(cross_edge)
                result.decisions.append(MappingDecision(
                    stage="cross_entity_inference", action="infer",
                    element_id=cross_edge.edge_id,
                    reason=f"Inferred: {s_node.label} active in {r_node.label}",
                ))

    except Exception as exc:
        logger.error("Signal mapping failed for %s: %s", signal_dict.get("signal_id", "?"), exc)
        result.warnings.append(f"Mapping error: {exc}")

    result.duration_ms = (time.monotonic() - t0) * 1000
    logger.info(
        "Mapped signal %s → %d nodes, %d edges, %d decisions (%.1fms)",
        result.signal_id, result.node_count, result.edge_count,
        len(result.decisions), result.duration_ms,
    )
    return result
