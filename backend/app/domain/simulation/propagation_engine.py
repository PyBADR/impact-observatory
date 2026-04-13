"""
Impact Observatory | مرصد الأثر — Phase 1 Propagation Engine
Edge-based stress transmission through the GCC macro-financial graph.

Algorithm: Iterative relaxation (modified Bellman-Ford)
  - Each iteration, every edge transmits stress: target += source.stress * weight * damping
  - Damping decreases each round to model decay (stress doesn't amplify forever)
  - Converges when max delta < epsilon or max iterations reached

Design decisions:
  - No numpy/scipy — pure Python for zero-dependency deployment
  - Deterministic — same inputs always produce same outputs
  - O(iterations * |E|) — 5 iterations * ~120 edges = 600 operations
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domain.simulation.graph_types import Edge, NodeId, NodeState, PropagationGraph
from app.domain.simulation.hormuz_dataset import (
    COUNTRY_META,
    SECTOR_META,
    build_edges,
    build_initial_shock_vector,
)
from app.domain.simulation.schemas import (
    CountryImpact,
    GCCCountryCode,
    PropagationEdge,
    RiskLevel,
    SectorCode,
    SectorImpact,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Engine Configuration
# ═══════════════════════════════════════════════════════════════════════════════

MAX_ITERATIONS: int = 5
DAMPING_BASE: float = 0.85      # stress transmission decay per hop
DAMPING_DECAY: float = 0.15     # damping reduces each iteration
EPSILON: float = 1e-4           # convergence threshold


# ═══════════════════════════════════════════════════════════════════════════════
# Risk Level Classification (aligned with URS thresholds from config.py)
# ═══════════════════════════════════════════════════════════════════════════════

def classify_risk(score: float) -> RiskLevel:
    """Map a 0–1 stress score to a RiskLevel enum."""
    if score >= 0.80:
        return RiskLevel.SEVERE
    if score >= 0.65:
        return RiskLevel.HIGH
    if score >= 0.50:
        return RiskLevel.ELEVATED
    if score >= 0.35:
        return RiskLevel.GUARDED
    if score >= 0.20:
        return RiskLevel.LOW
    return RiskLevel.NOMINAL


# ═══════════════════════════════════════════════════════════════════════════════
# Core Propagation
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PropagationResult:
    """Output of the propagation engine."""
    graph: PropagationGraph
    iterations_run: int
    converged: bool
    country_impacts: list[CountryImpact]
    sector_impacts: list[SectorImpact]
    propagation_edges: list[PropagationEdge]
    total_loss_usd: float
    confidence: float


def propagate(
    severity: float,
    transit_reduction_pct: float,
    horizon_hours: int,
) -> PropagationResult:
    """Run the full stress propagation pipeline.

    Steps:
      1. Build initial shock vector from Hormuz dataset
      2. Construct propagation graph (nodes + edges)
      3. Inject shocks into nodes
      4. Iterate: transmit stress through edges with damping
      5. Aggregate into country and sector impact summaries
      6. Compute total financial loss using GDP-weighted exposure
    """
    # ── Step 1: Initial shocks ───────────────────────────────────────────
    shock_vector = build_initial_shock_vector(severity, transit_reduction_pct)

    # ── Step 2: Build graph ──────────────────────────────────────────────
    graph = PropagationGraph()

    # Add all nodes with initial shocks
    for (cc, sc), shock in shock_vector.items():
        graph.add_node(NodeId(cc, sc), initial_shock=shock)

    # Add all edges
    for edge in build_edges(shock_vector):
        graph.add_edge(edge)

    # ── Step 3–4: Iterative relaxation ───────────────────────────────────
    converged = False
    iterations_run = 0

    for i in range(MAX_ITERATIONS):
        iterations_run = i + 1
        damping = DAMPING_BASE * (1.0 - DAMPING_DECAY * i)
        damping = max(damping, 0.1)  # floor

        max_delta = 0.0
        # Collect updates before applying (synchronous relaxation)
        updates: dict[NodeId, float] = {}

        for edge in graph.edges:
            src_state = graph.nodes[edge.source]
            tgt_state = graph.nodes[edge.target]

            transmitted = src_state.stress * edge.weight * damping
            if transmitted > 0.001:  # skip negligible transmissions
                current = updates.get(edge.target, 0.0)
                updates[edge.target] = current + transmitted

        # Apply updates
        for node_id, added_stress in updates.items():
            state = graph.nodes[node_id]
            old_stress = state.stress
            # New stress = max(current, initial_shock + accumulated transmission)
            # Capped at 1.0
            new_stress = min(
                state.initial_shock + added_stress,
                1.0,
            )
            # Only increase — stress doesn't decrease during propagation
            if new_stress > state.stress:
                state.stress = new_stress
                state.peak_stress = max(state.peak_stress, new_stress)
                delta = new_stress - old_stress
                max_delta = max(max_delta, delta)

        if max_delta < EPSILON:
            converged = True
            break

    # ── Step 5: Assign drivers and channels ──────────────────────────────
    _assign_drivers(graph)

    # ── Step 6: Aggregate results ────────────────────────────────────────
    country_impacts = _aggregate_countries(graph, horizon_hours)
    sector_impacts = _aggregate_sectors(graph)
    prop_edges = _extract_significant_edges(graph)
    total_loss = sum(c.loss_usd for c in country_impacts)

    # Confidence based on convergence and severity reasonableness
    confidence = 0.88 if converged else 0.72
    if severity > 0.9:
        confidence -= 0.08  # extreme scenarios are less certain

    return PropagationResult(
        graph=graph,
        iterations_run=iterations_run,
        converged=converged,
        country_impacts=country_impacts,
        sector_impacts=sector_impacts,
        propagation_edges=prop_edges,
        total_loss_usd=total_loss,
        confidence=round(confidence, 2),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _assign_drivers(graph: PropagationGraph) -> None:
    """For each node, find the incoming edge with the highest effective stress."""
    # Build reverse adjacency
    incoming: dict[NodeId, list[Edge]] = {}
    for edge in graph.edges:
        incoming.setdefault(edge.target, []).append(edge)

    for node_id, state in graph.nodes.items():
        edges_in = incoming.get(node_id, [])
        if not edges_in:
            state.primary_driver = "Direct Hormuz exposure"
            state.secondary_risk = "Supply chain propagation"
            state.transmission_channel = "Exogenous shock"
            continue

        # Sort by effective transmission (source stress * weight)
        ranked = sorted(
            edges_in,
            key=lambda e: graph.nodes[e.source].stress * e.weight,
            reverse=True,
        )
        top = ranked[0]
        state.primary_driver = top.channel
        state.transmission_channel = f"{top.source} → {top.target}"
        if len(ranked) > 1:
            state.secondary_risk = ranked[1].channel
        else:
            state.secondary_risk = "No secondary channel identified"


def _aggregate_countries(
    graph: PropagationGraph,
    horizon_hours: int,
) -> list[CountryImpact]:
    """Roll up node-level stress to country-level impact."""
    country_data: dict[str, list[NodeState]] = {}
    for node_id, state in graph.nodes.items():
        country_data.setdefault(node_id.country, []).append(state)

    results: list[CountryImpact] = []
    for cc, states in sorted(country_data.items()):
        meta = COUNTRY_META[cc]
        # Country stress = GDP-weighted average of sector stresses
        total_weight = 0.0
        weighted_stress = 0.0
        dominant_state: NodeState | None = None
        max_stress = -1.0

        for s in states:
            sector_meta = SECTOR_META[s.node_id.sector]
            w = sector_meta["base_sensitivity"]
            weighted_stress += s.stress * w
            total_weight += w
            if s.stress > max_stress:
                max_stress = s.stress
                dominant_state = s

        avg_stress = weighted_stress / total_weight if total_weight > 0 else 0.0

        # Financial loss = GDP * avg_stress * hormuz_dependency * time_factor
        time_factor = min(horizon_hours / 8760.0, 1.0)  # annualize
        loss = (
            meta["gdp_usd"]
            * avg_stress
            * meta["hormuz_dependency"]
            * time_factor
        )

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


def _aggregate_sectors(graph: PropagationGraph) -> list[SectorImpact]:
    """Roll up node-level stress to sector-level impact (across all countries)."""
    sector_data: dict[str, list[NodeState]] = {}
    for node_id, state in graph.nodes.items():
        sector_data.setdefault(node_id.sector, []).append(state)

    results: list[SectorImpact] = []
    for sc, states in sorted(sector_data.items()):
        meta = SECTOR_META[sc]
        avg_stress = sum(s.stress for s in states) / len(states)

        # Find the highest-stress node's drivers
        top = max(states, key=lambda s: s.stress)

        # Recommended lever based on sector
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


def _sector_lever(sector_code: str, stress: float) -> str:
    """Return the recommended intervention lever for a sector."""
    levers: dict[str, dict[str, str]] = {
        "oil_gas": {
            "high": "Activate strategic petroleum reserve drawdown; invoke bilateral swap agreements",
            "medium": "Accelerate pipeline bypass capacity; diversify shipping routes",
            "low": "Monitor spot market differentials; pre-position logistics",
        },
        "banking": {
            "high": "Central bank emergency liquidity facility; suspend interbank rate ceilings",
            "medium": "Expand repo window collateral eligibility; coordinate GCC swap lines",
            "low": "Enhance daily liquidity reporting; stress-test HQLA buffers",
        },
        "insurance": {
            "high": "Invoke catastrophe reinsurance treaties; halt new marine underwriting",
            "medium": "Increase loss reserves; coordinate with Lloyd's war-risk syndicate",
            "low": "Review exposure concentrations; update actuarial assumptions",
        },
        "fintech": {
            "high": "Activate payment system continuity protocols; reroute settlement channels",
            "medium": "Increase transaction monitoring thresholds; pre-fund settlement accounts",
            "low": "Monitor payment velocity metrics; diversify FX corridors",
        },
        "real_estate": {
            "high": "Freeze new project approvals; restructure construction financing",
            "medium": "Delay non-critical infrastructure tenders; review developer credit lines",
            "low": "Monitor materials cost indices; assess supply chain alternatives",
        },
        "government": {
            "high": "Deploy fiscal stabilization package; coordinate GCC sovereign wealth drawdown",
            "medium": "Accelerate budget reallocation; activate bilateral aid agreements",
            "low": "Pre-position fiscal reserves; update contingency spending authority",
        },
    }

    tier = "high" if stress >= 0.6 else "medium" if stress >= 0.3 else "low"
    return levers.get(sector_code, {}).get(tier, "Assess exposure and prepare contingency plan")


def _extract_significant_edges(graph: PropagationGraph) -> list[PropagationEdge]:
    """Return edges with effective transmission above threshold for the response."""
    significant: list[PropagationEdge] = []
    for edge in graph.edges:
        src_stress = graph.nodes[edge.source].stress
        effective = src_stress * edge.weight
        if effective > 0.05:  # only include meaningful transmissions
            significant.append(PropagationEdge(
                source=str(edge.source),
                target=str(edge.target),
                weight=round(effective, 4),
                channel=edge.channel,
            ))
    # Sort by weight descending, limit to top 30 for readability
    significant.sort(key=lambda e: e.weight, reverse=True)
    return significant[:30]
