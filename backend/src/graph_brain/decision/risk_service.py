"""Risk Service — Orchestration layer connecting Graph + Insights + Risk.

Provides a unified interface for risk assessment that combines:
  1. RiskEngine (graph-traversal scoring)
  2. InsightsAgent (optional LLM-enhanced analysis)
  3. GraphBrainService (node/edge queries)

Architecture Layer: Agents → APIs (Layer 4-5)
Owner: Decision Layer
Consumers: Risk API routes

Usage:
    service = get_risk_service()
    result = service.assess_entity("chokepoint:hormuz_strait")
    portfolio = service.assess_portfolio(["country:SA", "sector:energy"])
"""

import logging
import time
from typing import Any, Optional

from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.graph_brain.types import GraphEntityType

from src.graph_brain.decision.risk_engine import RiskEngine
from src.graph_brain.decision.risk_models import (
    PortfolioRiskResult,
    RiskLevel,
    RiskResult,
)
from src.graph_brain.decision.risk_rules import classify_risk_level

logger = logging.getLogger("graph_brain.decision.risk_service")


class RiskService:
    """Orchestrates risk assessment across Graph + Insights + Engine.

    Provides:
      - Single entity assessment
      - Multi-entity portfolio assessment with systemic risk
      - Entity type-wide assessment (all countries, all sectors, etc.)

    Args:
        graph_brain: GraphBrainService instance
        max_depth: Graph traversal depth for risk propagation
        signal_half_life_hours: Temporal decay half-life
    """

    def __init__(
        self,
        graph_brain: Optional[GraphBrainService] = None,
        max_depth: int = 3,
        signal_half_life_hours: float = 168.0,
    ) -> None:
        self._graph_brain = graph_brain or get_graph_brain_service()
        self._engine = RiskEngine(
            store=self._graph_brain.store,
            max_depth=max_depth,
            signal_half_life_hours=signal_half_life_hours,
        )

    @property
    def graph_brain(self) -> GraphBrainService:
        return self._graph_brain

    # ── Single Entity Assessment ──────────────────────────────────────────

    def assess_entity(self, entity_id: str) -> RiskResult:
        """Assess risk for a single entity by node_id.

        Delegates to RiskEngine.assess() which performs:
          1. Direct factor collection (incident edges)
          2. Multi-hop propagation scoring
          3. Cross-sector contagion detection
          4. Scenario matching
          5. URS composite scoring
          6. Recommendation generation

        Args:
            entity_id: GraphNode node_id (e.g., "chokepoint:hormuz_strait")

        Returns:
            RiskResult with full decomposition
        """
        return self._engine.assess(entity_id)

    # ── Portfolio Assessment ──────────────────────────────────────────────

    def assess_portfolio(
        self,
        entity_ids: list[str],
    ) -> PortfolioRiskResult:
        """Assess risk across multiple entities with systemic risk overlay.

        Beyond individual entity scores, this computes:
          - Portfolio-weighted average risk score
          - Systemic risk (how interconnected are the entities)
          - Common contagion channels
          - Top risk drivers across the portfolio

        Args:
            entity_ids: List of GraphNode node_ids

        Returns:
            PortfolioRiskResult with entity results + systemic metrics
        """
        t0 = time.monotonic()
        result = PortfolioRiskResult()

        # Assess each entity
        for eid in entity_ids:
            entity_result = self._engine.assess(eid)
            result.entity_results.append(entity_result)

        if not result.entity_results:
            result.total_duration_ms = (time.monotonic() - t0) * 1000
            result.compute_audit_hash()
            return result

        # Portfolio risk score: weighted average (higher-risk entities weighted more)
        scores = [r.risk_score for r in result.entity_results]
        if scores:
            # Weight by score itself (risk-weighted average)
            total_weight = sum(s + 0.1 for s in scores)  # +0.1 to avoid zero-weight
            result.portfolio_risk_score = round(
                sum(s * (s + 0.1) for s in scores) / total_weight, 4
            )
        result.portfolio_risk_level = classify_risk_level(result.portfolio_risk_score)

        # Systemic risk: proportion of shared contagion channels
        all_sectors: set[str] = set()
        shared_sectors: set[str] = set()
        sector_counts: dict[str, int] = {}
        for r in result.entity_results:
            for s in r.exposed_sectors:
                sector_counts[s] = sector_counts.get(s, 0) + 1
                all_sectors.add(s)

        for s, count in sector_counts.items():
            if count > 1:
                shared_sectors.add(s)

        if all_sectors:
            result.systemic_risk_score = round(
                len(shared_sectors) / len(all_sectors), 4
            )
        result.contagion_channels = sorted(shared_sectors)

        # Top risk drivers across portfolio
        all_drivers = []
        for r in result.entity_results:
            all_drivers.extend(r.drivers)
        all_drivers.sort(key=lambda d: d.contribution, reverse=True)
        result.top_risks = all_drivers[:10]

        result.total_duration_ms = (time.monotonic() - t0) * 1000
        result.compute_audit_hash()

        logger.info(
            "Portfolio risk: %d entities, score=%.3f (%s), "
            "systemic=%.3f, %d contagion channels (%.1fms)",
            len(entity_ids), result.portfolio_risk_score,
            result.portfolio_risk_level.value,
            result.systemic_risk_score, len(result.contagion_channels),
            result.total_duration_ms,
        )
        return result

    # ── Type-Wide Assessment ──────────────────────────────────────────────

    def assess_by_type(self, entity_type: str) -> PortfolioRiskResult:
        """Assess all entities of a given type.

        Args:
            entity_type: GraphEntityType value (e.g., "country", "sector", "chokepoint")

        Returns:
            PortfolioRiskResult for all entities of that type
        """
        try:
            et = GraphEntityType(entity_type)
        except ValueError:
            return PortfolioRiskResult()

        nodes = self._graph_brain.get_nodes_by_type(et)
        entity_ids = [n.node_id for n in nodes]
        return self.assess_portfolio(entity_ids)

    # ── Risk Heatmap Data ─────────────────────────────────────────────────

    def risk_heatmap(self) -> dict[str, Any]:
        """Generate risk heatmap data for all entity types.

        Returns a dict mapping entity_type → list of {id, label, score, level}.
        """
        heatmap: dict[str, list[dict]] = {}
        for et in GraphEntityType:
            nodes = self._graph_brain.get_nodes_by_type(et)
            if not nodes:
                continue
            entries = []
            for node in nodes[:20]:  # cap per type
                result = self._engine.assess(node.node_id)
                entries.append({
                    "id": node.node_id,
                    "label": node.label,
                    "risk_score": result.risk_score,
                    "risk_level": result.risk_level.value,
                    "driver_count": len(result.drivers),
                })
            entries.sort(key=lambda e: e["risk_score"], reverse=True)
            heatmap[et.value] = entries
        return heatmap


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[RiskService] = None


def get_risk_service() -> RiskService:
    """Get or create the global RiskService singleton."""
    global _instance
    if _instance is None:
        _instance = RiskService()
    return _instance
