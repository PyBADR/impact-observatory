"""
Impact Observatory | مرصد الأثر — Phase 2 Simulation Runner
Reusable, scenario-agnostic simulation orchestrator.

Replaces the hardcoded hormuz-only `propagate()` call with a generic runner
that resolves a scenario slug → dataset → propagation → decisions → explain.

Architecture layer: Orchestration (Layer 5 — APIs)

Usage:
    from app.domain.simulation.runner import SimulationRunner
    runner = SimulationRunner()
    result = runner.run("hormuz", severity=0.72, horizon_hours=168)
    result = runner.run("liquidity_stress", severity=0.65, horizon_hours=336)
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.simulation.decision_engine import generate_decisions
from app.domain.simulation.graph_types import Edge, NodeId, NodeState, PropagationGraph
from app.domain.simulation.pathway_explain import generate_pathway_headlines
from app.domain.simulation.scenario_registry import ScenarioSpec, get_scenario
from app.domain.simulation.schemas import (
    CountryImpact,
    DecisionAction,
    Explainability,
    GCCCountryCode,
    HormuzRunResult,
    PropagationEdge,
    RiskLevel,
    SectorCode,
    SectorImpact,
)

logger = logging.getLogger("observatory.runner")

# ═══════════════════════════════════════════════════════════════════════════════
# Engine Configuration (shared across all scenarios)
# ═══════════════════════════════════════════════════════════════════════════════

MAX_ITERATIONS: int = 5
DAMPING_BASE: float = 0.85
DAMPING_DECAY: float = 0.15
EPSILON: float = 1e-4

MODEL_VERSION: str = "3.0.0-phase2"


# ═══════════════════════════════════════════════════════════════════════════════
# Risk Classification (same thresholds as Phase 1 — single source of truth)
# ═══════════════════════════════════════════════════════════════════════════════

def classify_risk(score: float) -> RiskLevel:
    if score >= 0.80: return RiskLevel.SEVERE
    if score >= 0.65: return RiskLevel.HIGH
    if score >= 0.50: return RiskLevel.ELEVATED
    if score >= 0.35: return RiskLevel.GUARDED
    if score >= 0.20: return RiskLevel.LOW
    return RiskLevel.NOMINAL


# ═══════════════════════════════════════════════════════════════════════════════
# Propagation Result (scenario-agnostic)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GenericPropagationResult:
    """Output of the scenario-agnostic propagation engine."""
    graph: PropagationGraph
    spec: ScenarioSpec
    iterations_run: int
    converged: bool
    country_impacts: list[CountryImpact]
    sector_impacts: list[SectorImpact]
    propagation_edges: list[PropagationEdge]
    total_loss_usd: float
    confidence: float
    pathway_headlines: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Simulation Runner
# ═══════════════════════════════════════════════════════════════════════════════

class SimulationRunner:
    """Reusable simulation orchestrator. Stateless — safe for concurrent use."""

    def run(
        self,
        slug: str,
        severity: float | None = None,
        horizon_hours: int | None = None,
        **extra_params: Any,
    ) -> GenericPropagationResult:
        """Execute a full simulation for the given scenario slug.

        Steps:
          1. Resolve scenario spec from registry
          2. Build shock vector using scenario-specific factory
          3. Construct propagation graph
          4. Iterative relaxation (Bellman-Ford-like)
          5. Assign drivers + aggregate
          6. Generate pathway headlines
        """
        spec = get_scenario(slug)

        # Merge defaults with overrides
        sev = severity if severity is not None else spec.default_severity
        hrs = horizon_hours if horizon_hours is not None else spec.default_horizon_hours
        merged_params = {**spec.extra_param_defaults, **extra_params}

        logger.info("Running scenario '%s': severity=%.2f, horizon=%dh", slug, sev, hrs)

        # ── Step 1: Build shock vector ───────────────────────────────────
        shock_vector = spec.build_shock_vector(sev, **merged_params)

        # ── Step 2: Build graph ──────────────────────────────────────────
        graph = PropagationGraph()
        for (cc, sc), shock in shock_vector.items():
            graph.add_node(NodeId(cc, sc), initial_shock=shock)
        for edge in spec.build_edges(shock_vector):
            graph.add_edge(edge)

        # ── Step 3: Iterative relaxation ─────────────────────────────────
        converged, iterations_run = self._relax(graph)

        # ── Step 4: Assign drivers ───────────────────────────────────────
        self._assign_drivers(graph, spec)

        # ── Step 5: Aggregate ────────────────────────────────────────────
        country_impacts = self._aggregate_countries(graph, hrs, spec)
        sector_impacts = self._aggregate_sectors(graph, spec)
        prop_edges = self._extract_significant_edges(graph)
        total_loss = sum(c.loss_usd for c in country_impacts)

        confidence = 0.88 if converged else 0.72
        if sev > 0.9:
            confidence -= 0.08

        # ── Step 6: Pathway headlines ────────────────────────────────────
        headlines = generate_pathway_headlines(graph, spec, country_impacts, sector_impacts)

        return GenericPropagationResult(
            graph=graph,
            spec=spec,
            iterations_run=iterations_run,
            converged=converged,
            country_impacts=country_impacts,
            sector_impacts=sector_impacts,
            propagation_edges=prop_edges,
            total_loss_usd=total_loss,
            confidence=round(confidence, 2),
            pathway_headlines=headlines,
        )

    # ─── Internal: Relaxation ────────────────────────────────────────────

    def _relax(self, graph: PropagationGraph) -> tuple[bool, int]:
        """Run iterative relaxation. Returns (converged, iterations_run)."""
        converged = False
        iterations_run = 0

        for i in range(MAX_ITERATIONS):
            iterations_run = i + 1
            damping = max(DAMPING_BASE * (1.0 - DAMPING_DECAY * i), 0.1)

            max_delta = 0.0
            updates: dict[NodeId, float] = {}

            for edge in graph.edges:
                src_state = graph.nodes[edge.source]
                transmitted = src_state.stress * edge.weight * damping
                if transmitted > 0.001:
                    updates[edge.target] = updates.get(edge.target, 0.0) + transmitted

            for node_id, added_stress in updates.items():
                state = graph.nodes[node_id]
                old_stress = state.stress
                new_stress = min(state.initial_shock + added_stress, 1.0)
                if new_stress > state.stress:
                    state.stress = new_stress
                    state.peak_stress = max(state.peak_stress, new_stress)
                    max_delta = max(max_delta, new_stress - old_stress)

            if max_delta < EPSILON:
                converged = True
                break

        return converged, iterations_run

    # ─── Internal: Driver Assignment ─────────────────────────────────────

    def _assign_drivers(self, graph: PropagationGraph, spec: ScenarioSpec) -> None:
        incoming: dict[NodeId, list[Edge]] = {}
        for edge in graph.edges:
            incoming.setdefault(edge.target, []).append(edge)

        for node_id, state in graph.nodes.items():
            edges_in = incoming.get(node_id, [])
            if not edges_in:
                state.primary_driver = f"Direct {spec.shock_origin_label}"
                state.secondary_risk = "Cross-sector propagation"
                state.transmission_channel = "Exogenous shock"
                continue

            ranked = sorted(
                edges_in,
                key=lambda e: graph.nodes[e.source].stress * e.weight,
                reverse=True,
            )
            state.primary_driver = ranked[0].channel
            state.transmission_channel = f"{ranked[0].source} → {ranked[0].target}"
            state.secondary_risk = (
                ranked[1].channel if len(ranked) > 1
                else "No secondary channel identified"
            )

    # ─── Internal: Country Aggregation ───────────────────────────────────

    def _aggregate_countries(
        self,
        graph: PropagationGraph,
        horizon_hours: int,
        spec: ScenarioSpec,
    ) -> list[CountryImpact]:
        country_data: dict[str, list[NodeState]] = {}
        for node_id, state in graph.nodes.items():
            country_data.setdefault(node_id.country, []).append(state)

        results: list[CountryImpact] = []
        for cc, states in sorted(country_data.items()):
            meta = spec.country_meta[cc]
            total_weight = 0.0
            weighted_stress = 0.0
            dominant_state: NodeState | None = None
            max_stress = -1.0

            for s in states:
                sector_meta = spec.sector_meta[s.node_id.sector]
                w = sector_meta["base_sensitivity"]
                weighted_stress += s.stress * w
                total_weight += w
                if s.stress > max_stress:
                    max_stress = s.stress
                    dominant_state = s

            avg_stress = weighted_stress / total_weight if total_weight > 0 else 0.0

            # Loss formula adapts to scenario type
            time_factor = min(horizon_hours / 8760.0, 1.0)
            if spec.scenario_type == "energy_disruption":
                exposure_key = meta.get("hormuz_dependency", 0.5)
            elif spec.scenario_type == "liquidity_stress":
                exposure_key = meta.get("interbank_exposure", 0.5)
            else:
                exposure_key = 0.5

            loss = meta["gdp_usd"] * avg_stress * exposure_key * time_factor

            assert dominant_state is not None
            results.append(CountryImpact(
                country_code=GCCCountryCode(cc),
                country_name=meta["name"],
                loss_usd=round(loss, 2),
                dominant_sector=SectorCode(dominant_state.node_id.sector),
                primary_driver=dominant_state.primary_driver,
                transmission_channel=dominant_state.transmission_channel,
                risk_level=classify_risk(avg_stress),
                stress_score=round(avg_stress, 4),
            ))

        return sorted(results, key=lambda c: c.loss_usd, reverse=True)

    # ─── Internal: Sector Aggregation ────────────────────────────────────

    def _aggregate_sectors(
        self,
        graph: PropagationGraph,
        spec: ScenarioSpec,
    ) -> list[SectorImpact]:
        from app.domain.simulation.propagation_engine import _sector_lever

        sector_data: dict[str, list[NodeState]] = {}
        for node_id, state in graph.nodes.items():
            sector_data.setdefault(node_id.sector, []).append(state)

        results: list[SectorImpact] = []
        for sc, states in sorted(sector_data.items()):
            meta = spec.sector_meta[sc]
            avg_stress = sum(s.stress for s in states) / len(states)
            top = max(states, key=lambda s: s.stress)
            lever = _sector_lever(sc, avg_stress)

            results.append(SectorImpact(
                sector=SectorCode(sc),
                sector_label=meta["label"],
                stress=round(avg_stress, 4),
                primary_driver=top.primary_driver,
                secondary_risk=top.secondary_risk,
                recommended_lever=lever,
                risk_level=classify_risk(avg_stress),
            ))

        return sorted(results, key=lambda s: s.stress, reverse=True)

    # ─── Internal: Edge Extraction ───────────────────────────────────────

    def _extract_significant_edges(self, graph: PropagationGraph) -> list[PropagationEdge]:
        significant: list[PropagationEdge] = []
        for edge in graph.edges:
            effective = graph.nodes[edge.source].stress * edge.weight
            if effective > 0.05:
                significant.append(PropagationEdge(
                    source=str(edge.source),
                    target=str(edge.target),
                    weight=round(effective, 4),
                    channel=edge.channel,
                ))
        significant.sort(key=lambda e: e.weight, reverse=True)
        return significant[:30]


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: build full HormuzRunResult-compatible response
# ═══════════════════════════════════════════════════════════════════════════════

def build_run_result(
    prop: GenericPropagationResult,
    severity: float,
    horizon_hours: int,
    extra_params: dict[str, Any],
    decisions: list[DecisionAction],
    explainability: Explainability,
) -> HormuzRunResult:
    """Assemble a complete API response with SHA-256 audit trail."""
    result = HormuzRunResult(
        scenario_id=prop.spec.slug,
        model_version=MODEL_VERSION,
        timestamp=datetime.utcnow(),
        severity=severity,
        horizon_hours=horizon_hours,
        transit_reduction_pct=extra_params.get("transit_reduction_pct", 0.0),
        total_loss_usd=round(prop.total_loss_usd, 2),
        risk_level=prop.country_impacts[0].risk_level if prop.country_impacts else RiskLevel.NOMINAL,
        confidence=prop.confidence,
        countries=prop.country_impacts,
        sectors=prop.sector_impacts,
        propagation_edges=prop.propagation_edges,
        decisions=decisions,
        explainability=explainability,
    )

    payload_json = result.model_dump_json(exclude={"sha256_digest"})
    result.sha256_digest = hashlib.sha256(payload_json.encode()).hexdigest()
    return result
