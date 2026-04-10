"""Risk Engine — Graph-aware composite risk computation.

The computational core of the Decision Layer. Traverses the Knowledge Graph
to collect risk factors, applies URS-aligned scoring, and produces
fully decomposed RiskResult outputs.

Architecture Layer: Models → Agents (Layer 3-4)
Owner: Decision Layer
Consumers: RiskService

Scoring Pipeline (per entity):
  1. Direct risk factors: edges incident on the entity node
  2. Propagated risk: multi-hop BFS through graph (with hop-decay)
  3. Cross-sector contagion: sector dependency chains
  4. Scenario exposure: match entity graph neighborhood to active scenarios
  5. Composite score: weighted combination using URS formula weights
  6. Classification: 6-tier URS risk level
  7. Recommendations: context-aware, severity-driven

Key Formulas (from config.py):
  URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropScore + g5*LossNorm
  Vulnerability: direct=1.0, 1st-hop=0.70, 2nd-hop=0.35, else=0.10
"""

import logging
import time
from typing import Any, Optional

from src.graph_brain.query import extract_subgraph, find_downstream, trace_paths
from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
)

from src.graph_brain.decision.risk_models import (
    PropagationPath,
    RiskFactor,
    RiskFactorSource,
    RiskLevel,
    RiskResult,
)
from src.graph_brain.decision.risk_rules import (
    classify_risk_level,
    compute_composite_score,
    compute_temporal_decay,
    generate_recommendations,
    get_dependent_sectors,
    get_sector_sensitivity,
    get_vulnerability_weight,
)

logger = logging.getLogger("graph_brain.decision.risk_engine")


# Relation types that signify risk propagation
RISK_RELATION_TYPES = {
    GraphRelationType.AFFECTS,
    GraphRelationType.PROPAGATES_TO,
    GraphRelationType.EXPOSED_TO,
    GraphRelationType.INFLUENCES,
    GraphRelationType.DEPENDS_ON,
    GraphRelationType.DIRECT_EXPOSURE,
    GraphRelationType.SUPPLY_CHAIN,
    GraphRelationType.MARKET_CONTAGION,
    GraphRelationType.RISK_TRANSFER,
    GraphRelationType.INFRASTRUCTURE_DEP,
}

# Entity types that represent risk sources
RISK_SOURCE_TYPES = {
    GraphEntityType.SIGNAL,
    GraphEntityType.EVENT,
    GraphEntityType.RISK_FACTOR,
    GraphEntityType.CHOKEPOINT,
}

# Known scenario keywords → scenario IDs
SCENARIO_KEYWORDS: dict[str, str] = {
    "hormuz": "hormuz_chokepoint_disruption",
    "oil": "saudi_oil_shock",
    "banking": "uae_banking_crisis",
    "cyber": "gcc_cyber_attack",
    "lng": "qatar_lng_disruption",
    "bahrain": "bahrain_sovereign_stress",
    "kuwait": "kuwait_fiscal_shock",
    "port": "oman_port_closure",
    "red_sea": "red_sea_trade_corridor_instability",
    "energy": "energy_market_volatility_shock",
    "liquidity": "regional_liquidity_stress_event",
    "iran": "iran_regional_escalation",
}


class RiskEngine:
    """Graph-aware risk computation engine.

    Traverses the GraphStore to collect risk factors incident on an entity,
    applies URS-aligned scoring with vulnerability hop-decay, and returns
    fully decomposed RiskResult objects.

    Args:
        store: GraphStore instance to query
        max_depth: Maximum graph traversal depth for risk propagation
        signal_half_life_hours: Temporal decay half-life for signal freshness
    """

    def __init__(
        self,
        store: GraphStore,
        max_depth: int = 3,
        signal_half_life_hours: float = 168.0,
    ) -> None:
        self._store = store
        self._max_depth = max_depth
        self._half_life = signal_half_life_hours

    def assess(self, entity_id: str) -> RiskResult:
        """Compute full risk assessment for a single entity.

        Steps:
          1. Resolve entity node from store
          2. Collect direct risk factors (incident edges)
          3. Collect propagated risk (multi-hop BFS)
          4. Detect cross-sector contagion channels
          5. Match active scenarios
          6. Compute composite URS score
          7. Classify risk level
          8. Generate recommendations
        """
        t0 = time.monotonic()

        node = self._store.get_node(entity_id)
        if node is None:
            result = RiskResult(
                entity_id=entity_id,
                risk_score=0.0,
                risk_level=RiskLevel.NOMINAL,
                recommendations=["Entity not found in knowledge graph"],
            )
            result.duration_ms = (time.monotonic() - t0) * 1000
            result.compute_audit_hash()
            return result

        result = RiskResult(
            entity_id=entity_id,
            entity_label=node.label,
            entity_type=node.entity_type.value,
        )

        # Step 1: Direct risk factors (incoming edges)
        direct_factors = self._collect_direct_factors(node)
        result.drivers.extend(direct_factors)

        # Step 2: Propagated risk (multi-hop)
        propagated_factors, prop_paths = self._collect_propagated_factors(node)
        result.drivers.extend(propagated_factors)
        result.propagation_paths = prop_paths

        # Step 3: Cross-sector contagion
        contagion_factors, exposed_sectors = self._detect_contagion(node)
        result.drivers.extend(contagion_factors)
        result.exposed_sectors = exposed_sectors

        # Step 4: Scenario matching
        active_scenarios = self._match_scenarios(node, result.drivers)
        result.active_scenarios = active_scenarios

        # Step 5: Compute composite score
        result.risk_score, result.confidence = self._compute_score(result.drivers)

        # Step 6: Classify
        result.risk_level = classify_risk_level(result.risk_score)

        # Step 7: Recommendations
        result.recommendations = generate_recommendations(
            risk_level=result.risk_level,
            entity_type=node.entity_type.value,
            exposed_sectors=result.exposed_sectors,
            active_scenarios=result.active_scenarios,
        )

        # Metadata
        result.graph_stats = {
            "direct_factors": len(direct_factors),
            "propagated_factors": len(propagated_factors),
            "contagion_factors": len(contagion_factors),
            "propagation_paths": len(prop_paths),
            "exposed_sectors": len(exposed_sectors),
            "active_scenarios": len(active_scenarios),
        }
        result.duration_ms = (time.monotonic() - t0) * 1000
        result.compute_audit_hash()

        logger.info(
            "Risk assessment for %s (%s): score=%.3f, level=%s, %d drivers (%.1fms)",
            entity_id, node.label, result.risk_score, result.risk_level.value,
            len(result.drivers), result.duration_ms,
        )
        return result

    # ── Step 1: Direct Risk Factors ───────────────────────────────────────

    def _collect_direct_factors(self, node: GraphNode) -> list[RiskFactor]:
        """Collect risk factors from edges directly connected to the entity."""
        factors: list[RiskFactor] = []

        # Incoming edges: something affects/propagates_to this entity
        for edge in self._store.get_incoming_edges(node.node_id):
            if edge.relation_type not in RISK_RELATION_TYPES:
                continue

            source_node = self._store.get_node(edge.source_id)
            if source_node is None:
                continue

            conf = CONFIDENCE_WEIGHTS.get(edge.confidence, 0.5)
            contribution = edge.weight * conf

            factors.append(RiskFactor(
                name=f"{source_node.label} → {edge.relation_type.value}",
                description=edge.label,
                source=RiskFactorSource.GRAPH_DIRECT,
                source_node_id=edge.source_id,
                weight=edge.weight,
                confidence=conf,
                temporal_decay=1.0,
                contribution=round(contribution, 4),
                hop_distance=1,
            ))

        # Check for active signals attached to this entity
        for edge in self._store.get_incoming_edges(node.node_id):
            source = self._store.get_node(edge.source_id)
            if source and source.entity_type in RISK_SOURCE_TYPES:
                severity = source.properties.get("severity_score", 0.5)
                factors.append(RiskFactor(
                    name=f"Active: {source.label}",
                    description=f"{source.entity_type.value} signal with severity {severity:.2f}",
                    source=RiskFactorSource.SIGNAL_ACTIVE,
                    source_node_id=source.node_id,
                    weight=severity,
                    confidence=CONFIDENCE_WEIGHTS.get(source.confidence, 0.5),
                    temporal_decay=1.0,
                    contribution=round(severity * 0.8, 4),
                    hop_distance=0,
                ))

        return factors

    # ── Step 2: Propagated Risk ───────────────────────────────────────────

    def _collect_propagated_factors(
        self, node: GraphNode,
    ) -> tuple[list[RiskFactor], list[PropagationPath]]:
        """Collect risk factors from multi-hop graph traversal."""
        factors: list[RiskFactor] = []
        paths: list[PropagationPath] = []

        # Find all risk source nodes in the graph
        risk_sources: list[GraphNode] = []
        for risk_type in RISK_SOURCE_TYPES:
            risk_sources.extend(self._store.get_nodes_by_type(risk_type))

        # Trace paths from risk sources to this entity
        for source in risk_sources[:20]:  # cap to avoid combinatorial explosion
            if source.node_id == node.node_id:
                continue

            traced = trace_paths(
                self._store,
                source.node_id,
                node.node_id,
                max_depth=self._max_depth,
                max_paths=2,
            )

            for path in traced:
                hops = path.total_hops
                if hops <= 1:
                    continue  # already captured in direct factors

                vuln = get_vulnerability_weight(hops)
                contribution = path.total_weight * vuln

                factors.append(RiskFactor(
                    name=f"Propagated: {source.label} ({hops} hops)",
                    description=path.path_description,
                    source=RiskFactorSource.GRAPH_PROPAGATED,
                    source_node_id=source.node_id,
                    weight=path.total_weight,
                    confidence=vuln,
                    temporal_decay=1.0,
                    contribution=round(contribution, 4),
                    hop_distance=hops,
                ))

                paths.append(PropagationPath(
                    path_description=path.path_description,
                    path_weight=round(path.total_weight, 4),
                    hops=hops,
                    source_entity=source.node_id,
                    target_entity=node.node_id,
                ))

        return factors, paths

    # ── Step 3: Cross-Sector Contagion ────────────────────────────────────

    def _detect_contagion(
        self, node: GraphNode,
    ) -> tuple[list[RiskFactor], list[str]]:
        """Detect cross-sector contagion channels affecting the entity."""
        factors: list[RiskFactor] = []
        exposed: set[str] = set()

        # Find sector nodes in the entity's neighborhood
        neighbors = self._store.get_neighbors(node.node_id, direction="both")
        for neighbor in neighbors:
            if neighbor.entity_type == GraphEntityType.SECTOR:
                sector_name = neighbor.label.lower().replace(" sector", "").strip()
                exposed.add(sector_name)

                # Check if this sector has dependents that are also in the graph
                dependents = get_dependent_sectors(sector_name)
                for dep in dependents:
                    sensitivity = get_sector_sensitivity(dep)
                    if sensitivity > 0.05:
                        factors.append(RiskFactor(
                            name=f"Contagion: {sector_name} → {dep}",
                            description=f"Cross-sector contagion via {sector_name} dependency chain",
                            source=RiskFactorSource.SECTOR_CONTAGION,
                            source_node_id=neighbor.node_id,
                            weight=sensitivity,
                            confidence=0.65,
                            temporal_decay=1.0,
                            contribution=round(sensitivity * 0.65, 4),
                            hop_distance=2,
                        ))
                        exposed.add(dep)

        # Also check entity type itself
        if node.entity_type == GraphEntityType.SECTOR:
            sector_name = node.label.lower().replace(" sector", "").strip()
            exposed.add(sector_name)

        return factors, sorted(exposed)

    # ── Step 4: Scenario Matching ─────────────────────────────────────────

    def _match_scenarios(
        self, node: GraphNode, drivers: list[RiskFactor],
    ) -> list[str]:
        """Match entity and its risk drivers to known GCC scenarios."""
        matched: set[str] = set()

        # Check entity label/type against scenario keywords
        check_text = f"{node.label} {node.entity_type.value}".lower()
        for driver in drivers:
            check_text += f" {driver.name}".lower()

        for keyword, scenario_id in SCENARIO_KEYWORDS.items():
            if keyword in check_text:
                matched.add(scenario_id)

        return sorted(matched)

    # ── Step 5: Composite Scoring ─────────────────────────────────────────

    def _compute_score(
        self, drivers: list[RiskFactor],
    ) -> tuple[float, float]:
        """Compute composite URS-aligned risk score from all drivers.

        Maps driver factors into the 5 URS components:
          - severity: max contribution from direct/signal sources
          - exposure: weighted average of sector-connected factors
          - stress: max contagion contribution
          - propagation: normalized propagation path strength
          - loss: severity² proxy

        Returns:
            (risk_score, confidence) both [0.0, 1.0]
        """
        if not drivers:
            return 0.0, 0.5

        # Decompose drivers by source type
        direct = [d for d in drivers if d.source in (
            RiskFactorSource.GRAPH_DIRECT, RiskFactorSource.SIGNAL_ACTIVE,
        )]
        propagated = [d for d in drivers if d.source == RiskFactorSource.GRAPH_PROPAGATED]
        contagion = [d for d in drivers if d.source == RiskFactorSource.SECTOR_CONTAGION]

        # Severity component: max contribution from direct sources
        severity = max((d.contribution for d in direct), default=0.0)
        severity = min(1.0, severity)

        # Exposure component: mean contribution from all factors
        all_contributions = [d.contribution for d in drivers if d.contribution > 0]
        exposure = sum(all_contributions) / len(all_contributions) if all_contributions else 0.0
        exposure = min(1.0, exposure)

        # Stress component: max contagion contribution
        stress = max((d.contribution for d in contagion), default=0.0)
        stress = min(1.0, stress)

        # Propagation component: normalized sum of propagated contributions
        prop_sum = sum(d.contribution for d in propagated)
        propagation = min(1.0, prop_sum / max(len(propagated), 1))

        # Loss component: severity² proxy
        loss = severity * severity

        composite = compute_composite_score(
            severity_component=severity,
            exposure_component=exposure,
            stress_component=stress,
            propagation_component=propagation,
            loss_component=loss,
        )

        # Confidence: average confidence of all drivers
        confidences = [d.confidence for d in drivers if d.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        return round(composite, 4), round(avg_confidence, 4)
