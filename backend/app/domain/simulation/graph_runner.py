"""
Impact Observatory | مرصد الأثر — Phase 3 Graph Runner

Orchestrator that integrates the Phase 3 entity graph overlay, country-sector
matrix, and government/real-estate transmission rules into the Phase 2
simulation pipeline.

Architecture layer: Orchestration (Layer 5)

This runner EXTENDS the Phase 2 SimulationRunner by:
  1. Applying entity absorber/amplifier effects during propagation
  2. Injecting government and real estate transmission edges dynamically
  3. Evaluating escalation thresholds post-propagation
  4. Resolving decision ownership

The result is a Phase3RunResult that wraps GenericPropagationResult with
entity states, escalation alerts, and ownership-enriched decisions.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.simulation.decision_engine import generate_decisions
from app.domain.simulation.entity_graph import (
    EntityLink,
    EntityNode,
    EntityType,
    build_entity_links,
    build_entity_registry,
)
from app.domain.simulation.escalation_engine import (
    EscalationAlert,
    evaluate_escalations,
)
from app.domain.simulation.explain import generate_explanations
from app.domain.simulation.government_real_estate_rules import (
    TransmissionEdge,
    collect_all_transmission_edges,
)
from app.domain.simulation.graph_types import Edge, NodeId, PropagationGraph
from app.domain.simulation.ownership_engine import (
    OwnershipRecord,
    get_ownership_fuzzy,
    resolve_country_owner,
)
from app.domain.simulation.runner import (
    GenericPropagationResult,
    SimulationRunner,
    classify_risk,
)
from app.domain.simulation.schemas import (
    DecisionAction,
    Explainability,
    RiskLevel,
)

logger = logging.getLogger("observatory.graph_runner")

MODEL_VERSION: str = "3.1.0-phase3"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3 Result
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EntityState:
    """Snapshot of entity state after Phase 3 processing."""
    entity_id: str
    entity_type: str
    country_code: str
    name: str
    name_ar: str
    absorber_capacity: float
    current_utilization: float
    stress: float
    breached: bool
    remaining_capacity: float


@dataclass
class EnrichedDecision:
    """A decision action enriched with ownership and entity context."""
    action: str
    owner: str
    timing: str
    value_avoided_usd: float
    downside_risk: str
    # Phase 3 enrichments
    owner_entity_type: str
    owner_role: str
    owner_role_ar: str
    authority_level: str
    deadline_hours: float
    escalation_path: list[str]
    regulatory_reference: str
    failure_consequence: str
    country_entity_name: str
    country_entity_name_ar: str


@dataclass
class Phase3RunResult:
    """Complete Phase 3 simulation result with entity graph overlay."""
    # Core propagation (from Phase 2)
    scenario_slug: str
    model_version: str
    timestamp: str
    severity: float
    horizon_hours: int
    propagation: GenericPropagationResult

    # Phase 3 additions
    entity_states: list[EntityState]
    escalation_alerts: list[dict]
    enriched_decisions: list[EnrichedDecision]
    decisions: list[DecisionAction]
    explainability: Explainability

    # Audit
    sha256_digest: str = ""

    # Summary metrics
    entities_breached: int = 0
    escalation_count: int = 0
    sovereign_alerts: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3 Graph Runner
# ═══════════════════════════════════════════════════════════════════════════════

class GraphRunner:
    """Phase 3 orchestrator — entity-aware, matrix-enhanced simulation.

    Stateless and concurrent-safe.
    """

    def __init__(self) -> None:
        self._base_runner = SimulationRunner()

    def run(
        self,
        slug: str,
        severity: float | None = None,
        horizon_hours: int | None = None,
        country_code: str | None = None,
        **extra_params: Any,
    ) -> Phase3RunResult:
        """Execute Phase 3 simulation pipeline.

        Steps:
          1. Run Phase 2 base propagation
          2. Build entity registry and links
          3. Apply entity absorber/amplifier effects to node stresses
          4. Inject government/real-estate transmission edges
          5. Re-relax with enhanced edges (1 additional pass)
          6. Update entity states from final node stresses
          7. Evaluate escalation thresholds
          8. Generate decisions with ownership enrichment
          9. Package result with SHA-256 digest

        Args:
            slug: Scenario slug from registry
            severity: Override scenario default severity
            horizon_hours: Override scenario default horizon
            country_code: Optional filter — focus on single country
            **extra_params: Scenario-specific parameters
        """
        # ── Step 1: Base propagation ─────────────────────────────────────
        prop = self._base_runner.run(slug, severity, horizon_hours, **extra_params)
        actual_sev = severity if severity is not None else prop.spec.default_severity
        actual_hrs = horizon_hours if horizon_hours is not None else prop.spec.default_horizon_hours

        logger.info(
            "Phase 3 overlay: %s severity=%.2f horizon=%dh",
            slug, actual_sev, actual_hrs,
        )

        # ── Step 2: Entity registry ──────────────────────────────────────
        entities = build_entity_registry()
        entity_links = build_entity_links()

        # ── Step 3: Apply entity effects ─────────────────────────────────
        node_stresses = self._extract_node_stresses(prop.graph)
        self._apply_entity_effects(entities, entity_links, node_stresses, prop.graph)

        # ── Step 4: Inject Phase 3 transmission edges ────────────────────
        p3_edges = collect_all_transmission_edges(node_stresses)
        injected = self._inject_transmission_edges(prop.graph, p3_edges)
        logger.info("Injected %d Phase 3 transmission edges", injected)

        # ── Step 5: One additional relaxation pass ───────────────────────
        self._rerelax(prop.graph)

        # ── Step 6: Update entity states ─────────────────────────────────
        updated_stresses = self._extract_node_stresses(prop.graph)
        self._update_entity_stress(entities, entity_links, updated_stresses)

        # ── Step 7: Evaluate escalations ─────────────────────────────────
        alerts = evaluate_escalations(entities, updated_stresses)

        # ── Step 8: Decisions with ownership ─────────────────────────────
        # Re-aggregate after Phase 3 overlay
        base_decisions = generate_decisions(prop)
        enriched = self._enrich_decisions(base_decisions, country_code)

        # Explainability
        explainability = generate_explanations(prop)

        # ── Step 9: Package result ───────────────────────────────────────
        entity_snapshots = self._snapshot_entities(entities, country_code)

        alert_dicts = [
            {
                "trigger": a.trigger.value,
                "severity": a.severity.value,
                "authority_required": a.authority_required.value,
                "headline": a.headline,
                "headline_ar": a.headline_ar,
                "affected_entities": a.affected_entities,
                "affected_countries": a.affected_countries,
                "affected_sectors": a.affected_sectors,
                "time_to_act_hours": a.time_to_act_hours,
                "narrative": a.narrative,
                "recommended_actions": a.recommended_actions,
            }
            for a in alerts
        ]

        result = Phase3RunResult(
            scenario_slug=slug,
            model_version=MODEL_VERSION,
            timestamp=datetime.utcnow().isoformat() + "Z",
            severity=actual_sev,
            horizon_hours=actual_hrs,
            propagation=prop,
            entity_states=entity_snapshots,
            escalation_alerts=alert_dicts,
            enriched_decisions=enriched,
            decisions=base_decisions,
            explainability=explainability,
            entities_breached=sum(1 for e in entities.values() if e.breached),
            escalation_count=len(alerts),
            sovereign_alerts=sum(
                1 for a in alerts if a.authority_required.value == "sovereign"
            ),
        )

        # SHA-256 digest
        digest_payload = json.dumps({
            "scenario_slug": result.scenario_slug,
            "model_version": result.model_version,
            "timestamp": result.timestamp,
            "severity": result.severity,
            "total_loss_usd": prop.total_loss_usd,
            "entities_breached": result.entities_breached,
            "escalation_count": result.escalation_count,
        }, sort_keys=True)
        result.sha256_digest = hashlib.sha256(digest_payload.encode()).hexdigest()

        return result

    # ─── Internal: Extract node stresses ────────────────────────────────

    def _extract_node_stresses(
        self, graph: PropagationGraph,
    ) -> dict[tuple[str, str], float]:
        """Extract current stress from all graph nodes."""
        return {
            (nid.country, nid.sector): state.stress
            for nid, state in graph.nodes.items()
        }

    # ─── Internal: Entity absorber/amplifier effects ────────────────────

    def _apply_entity_effects(
        self,
        entities: dict[str, EntityNode],
        links: list[EntityLink],
        node_stresses: dict[tuple[str, str], float],
        graph: PropagationGraph,
    ) -> None:
        """Apply entity absorber and amplifier effects to node stresses.

        - "absorbs" links: reduce target node stress by entity's remaining capacity
        - "amplifies" links: increase target node stress proportionally
        """
        for link in links:
            entity = entities.get(link.entity_id)
            if entity is None:
                continue

            node_key = (link.country_code, link.sector_code)
            node_id = NodeId(link.country_code, link.sector_code)
            if node_id not in graph.nodes:
                continue

            current_stress = graph.nodes[node_id].stress

            if link.link_type == "absorbs":
                # Entity absorbs stress proportional to its remaining capacity
                absorption = current_stress * link.weight * entity.remaining_capacity
                new_stress = max(current_stress - absorption, 0.0)
                graph.nodes[node_id].stress = new_stress
                # Track utilization
                entity.current_utilization += absorption * 0.3

            elif link.link_type == "amplifies":
                # Entity amplifies stress — pass-through increases stress
                amplification = current_stress * link.weight * 0.2
                new_stress = min(current_stress + amplification, 1.0)
                graph.nodes[node_id].stress = new_stress

    # ─── Internal: Inject transmission edges ────────────────────────────

    def _inject_transmission_edges(
        self,
        graph: PropagationGraph,
        p3_edges: list[TransmissionEdge],
    ) -> int:
        """Inject Phase 3 transmission edges into the propagation graph."""
        count = 0
        for te in p3_edges:
            src = NodeId(te.source_country, te.source_sector)
            tgt = NodeId(te.target_country, te.target_sector)
            if src in graph.nodes and tgt in graph.nodes:
                graph.add_edge(Edge(
                    source=src,
                    target=tgt,
                    weight=te.weight,
                    channel=te.channel,
                    delay_hours=te.lag_hours,
                ))
                count += 1
        return count

    # ─── Internal: Re-relaxation pass ───────────────────────────────────

    def _rerelax(self, graph: PropagationGraph) -> None:
        """Run one additional relaxation pass with Phase 3 edges."""
        damping = 0.60  # Lower damping for the overlay pass

        updates: dict[NodeId, float] = {}
        for edge in graph.edges:
            src_state = graph.nodes[edge.source]
            transmitted = src_state.stress * edge.weight * damping
            if transmitted > 0.001:
                updates[edge.target] = updates.get(edge.target, 0.0) + transmitted

        for node_id, added_stress in updates.items():
            state = graph.nodes[node_id]
            new_stress = min(state.initial_shock + added_stress, 1.0)
            if new_stress > state.stress:
                state.stress = new_stress
                state.peak_stress = max(state.peak_stress, new_stress)

    # ─── Internal: Update entity stress from final node stresses ────────

    def _update_entity_stress(
        self,
        entities: dict[str, EntityNode],
        links: list[EntityLink],
        node_stresses: dict[tuple[str, str], float],
    ) -> None:
        """Compute entity-level stress from connected sector nodes."""
        # Accumulate weighted stress from connected nodes
        entity_stress_acc: dict[str, list[float]] = {}
        for link in links:
            node_stress = node_stresses.get(
                (link.country_code, link.sector_code), 0.0,
            )
            weighted = node_stress * link.weight
            entity_stress_acc.setdefault(link.entity_id, []).append(weighted)

        for eid, stress_list in entity_stress_acc.items():
            entity = entities.get(eid)
            if entity is None:
                continue
            entity.stress = min(sum(stress_list) / len(stress_list), 1.0)
            entity.breached = entity.stress > entity.absorber_capacity

    # ─── Internal: Enrich decisions with ownership ──────────────────────

    def _enrich_decisions(
        self,
        decisions: list[DecisionAction],
        country_code: str | None = None,
    ) -> list[EnrichedDecision]:
        """Enrich each decision with ownership, deadline, and escalation info."""
        enriched: list[EnrichedDecision] = []

        # Determine target country (use top-impacted or specified)
        target_cc = country_code or "SAU"  # Default to SAU as largest economy

        for d in decisions:
            # Find sector from decision context
            sector = self._infer_sector_from_decision(d)
            record = get_ownership_fuzzy(sector, d.action)

            if record is None:
                # Fallback — create minimal enrichment
                enriched.append(EnrichedDecision(
                    action=d.action,
                    owner=d.owner,
                    timing=d.timing,
                    value_avoided_usd=d.value_avoided_usd,
                    downside_risk=d.downside_risk,
                    owner_entity_type="unknown",
                    owner_role=d.owner,
                    owner_role_ar="غير محدد",
                    authority_level="tactical",
                    deadline_hours=24.0,
                    escalation_path=[],
                    regulatory_reference="N/A",
                    failure_consequence=d.downside_risk,
                    country_entity_name="Unknown",
                    country_entity_name_ar="غير معروف",
                ))
                continue

            owner_info = resolve_country_owner(record, target_cc)

            enriched.append(EnrichedDecision(
                action=d.action,
                owner=d.owner,
                timing=d.timing,
                value_avoided_usd=d.value_avoided_usd,
                downside_risk=d.downside_risk,
                owner_entity_type=record.owner_entity_type.value,
                owner_role=record.owner_role,
                owner_role_ar=record.owner_role_ar,
                authority_level=record.authority_level.value,
                deadline_hours=record.deadline_hours,
                escalation_path=record.escalation_path,
                regulatory_reference=record.regulatory_reference,
                failure_consequence=record.failure_consequence,
                country_entity_name=owner_info["entity_name"],
                country_entity_name_ar=owner_info["entity_name_ar"],
            ))

        return enriched

    def _infer_sector_from_decision(self, d: DecisionAction) -> str:
        """Infer sector from decision action text."""
        action_lower = d.action.lower()
        sector_keywords = {
            "oil_gas": ["petroleum", "oil", "energy", "export", "port", "routing"],
            "banking": ["liquidity", "interbank", "bank", "credit"],
            "insurance": ["reinsurance", "underwriting", "claims", "treaty"],
            "fintech": ["payment", "settlement", "digital", "fintech"],
            "real_estate": ["project", "mortgage", "construction", "real estate"],
            "government": ["sovereign", "fiscal", "spending", "budget"],
        }
        for sector, keywords in sector_keywords.items():
            if any(kw in action_lower for kw in keywords):
                return sector
        return "government"  # default fallback

    # ─── Internal: Entity snapshots ─────────────────────────────────────

    def _snapshot_entities(
        self,
        entities: dict[str, EntityNode],
        country_code: str | None = None,
    ) -> list[EntityState]:
        """Create serializable snapshots of entity states."""
        snapshots: list[EntityState] = []
        for eid, entity in sorted(entities.items()):
            if country_code and entity.country_code != country_code:
                continue
            snapshots.append(EntityState(
                entity_id=entity.entity_id,
                entity_type=entity.entity_type.value,
                country_code=entity.country_code,
                name=entity.name,
                name_ar=entity.name_ar,
                absorber_capacity=round(entity.absorber_capacity, 4),
                current_utilization=round(entity.current_utilization, 4),
                stress=round(entity.stress, 4),
                breached=entity.breached,
                remaining_capacity=round(entity.remaining_capacity, 4),
            ))
        return snapshots
