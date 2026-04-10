"""
Impact Map Engine — builds the unified causal decision surface.

Converts raw simulation results + regime modifiers + GCC graph topology
into a typed ImpactMapResponse with:
  - Typed nodes with stress, state, time-to-breach
  - Typed edges with delay, transfer ratio, breakable points
  - Propagation events ordered by arrival time
  - Aggregate timeline for sparklines
  - Regime influence baked into every node/edge

Data Flow:
  SimulationEngine output
    + GCC_NODES / GCC_ADJACENCY
    + RegimeGraphModifiers
    + TransmissionChain
    → ImpactMapResponse (nodes, edges, events, timeline, headline)

Layer: Engines (Layer 3→4 bridge)
Called by: run_orchestrator after transmission + regime stages complete.
"""
from __future__ import annotations

import logging
import math
from typing import Any, TYPE_CHECKING

from src.config import (
    TX_BASE_DELAY_HOURS,
    TX_SEVERITY_TRANSFER_RATIO,
    TX_BREAKABLE_SEVERITY_THRESHOLD,
    TX_CRITICAL_WINDOW_HOURS,
    TX_SECTOR_DELAY,
    TX_SECTOR_TRANSFER,
)
from src.schemas.impact_map import (
    ImpactMapEdge,
    ImpactMapHeadline,
    ImpactMapNode,
    ImpactMapResponse,
    PropagationEvent,
    RegimeInfluence,
    TimelinePoint,
)

if TYPE_CHECKING:
    from src.regime.regime_graph_adapter import RegimeGraphModifiers

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Sector → NodeType / EdgeType / GraphLayer mapping
# ═══════════════════════════════════════════════════════════════════════════════

_SECTOR_TO_NODE_TYPE: dict[str, str] = {
    "banking":        "BANK",
    "insurance":      "INSURER",
    "fintech":        "FINTECH",
    "energy":         "ENERGY_ASSET",
    "maritime":       "PORT",
    "logistics":      "MARKET_INFRA",
    "infrastructure": "MARKET_INFRA",
    "government":     "REGULATOR",
    "healthcare":     "MARKET_INFRA",
}

_SECTOR_TO_LAYER: dict[str, str] = {
    "maritime":       "INFRASTRUCTURE",
    "energy":         "ENERGY",
    "banking":        "FINANCE",
    "insurance":      "FINANCE",
    "fintech":        "FINANCE",
    "logistics":      "INFRASTRUCTURE",
    "infrastructure": "INFRASTRUCTURE",
    "government":     "SOVEREIGN",
    "healthcare":     "INFRASTRUCTURE",
}

# Sector-pair → edge type inference
_EDGE_TYPE_MAP: dict[tuple[str, str], str] = {
    ("banking", "banking"):       "CORRESPONDENT_BANKING",
    ("banking", "insurance"):     "LIQUIDITY_DEPENDENCY",
    ("banking", "fintech"):       "PAYMENT_DEPENDENCY",
    ("banking", "energy"):        "LIQUIDITY_DEPENDENCY",
    ("banking", "government"):    "REGULATORY_CONTROL",
    ("insurance", "banking"):     "INSURANCE_CLAIMS_LINK",
    ("insurance", "fintech"):     "INSURANCE_CLAIMS_LINK",
    ("insurance", "healthcare"):  "INSURANCE_CLAIMS_LINK",
    ("fintech", "banking"):       "SETTLEMENT_ROUTE",
    ("fintech", "logistics"):     "PAYMENT_DEPENDENCY",
    ("energy", "maritime"):       "ENERGY_SUPPLY",
    ("energy", "banking"):        "TRADE_FLOW",
    ("energy", "logistics"):      "ENERGY_SUPPLY",
    ("maritime", "logistics"):    "TRADE_FLOW",
    ("maritime", "energy"):       "TRADE_FLOW",
    ("maritime", "banking"):      "TRADE_FLOW",
    ("maritime", "insurance"):    "TRADE_FLOW",
    ("logistics", "maritime"):    "TRADE_FLOW",
    ("logistics", "energy"):      "TRADE_FLOW",
    ("government", "banking"):    "REGULATORY_CONTROL",
    ("government", "infrastructure"): "REGULATORY_CONTROL",
}


def _infer_edge_type(src_sector: str, tgt_sector: str) -> str:
    """Infer typed edge type from sector pair."""
    return _EDGE_TYPE_MAP.get(
        (src_sector, tgt_sector),
        "LIQUIDITY_DEPENDENCY",  # safe default
    )


def _classify_stress(stress: float) -> str:
    """Map stress [0–1] to StressLevel label."""
    if stress >= 0.80:
        return "CRITICAL"
    if stress >= 0.65:
        return "SEVERE"
    if stress >= 0.50:
        return "HIGH"
    if stress >= 0.35:
        return "ELEVATED"
    if stress >= 0.20:
        return "MODERATE"
    if stress >= 0.10:
        return "LOW"
    return "NOMINAL"


def _classify_state(stress: float, time_to_breach: float | None) -> str:
    """Map stress + breach timing to NodeState."""
    if time_to_breach is not None and time_to_breach <= 0:
        return "BREACHED"
    if stress >= 0.80:
        return "FAILING"
    if stress >= 0.60:
        return "DEGRADED"
    if stress >= 0.30:
        return "STRESSED"
    return "NOMINAL"


def _format_usd(v: float) -> str:
    """Format USD for display."""
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"


def _estimate_time_to_breach(
    stress: float,
    criticality: float,
    regime_threshold_shift: float,
) -> float | None:
    """Estimate hours until breach based on current stress trajectory.

    Breach threshold = 0.85 + regime_threshold_shift (regime tightens/loosens).
    Returns None if stress is below 40% of threshold (no projected breach).
    """
    threshold = max(0.3, 0.85 + regime_threshold_shift)
    if stress < threshold * 0.4:
        return None  # too far from breach to project

    if stress >= threshold:
        return 0.0  # already breached

    # Simple linear projection: hours = remaining_gap / rate
    # Rate influenced by criticality (higher criticality → faster breach)
    rate = max(0.001, stress * criticality * 0.1)
    gap = threshold - stress
    hours = gap / rate
    return round(min(hours, 8760.0), 1)  # cap at 1 year


# ═══════════════════════════════════════════════════════════════════════════════
# Main builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_impact_map(
    result: dict[str, Any],
    gcc_nodes: list[dict[str, Any]],
    gcc_adjacency: dict[str, list[str]],
    regime_modifiers: "RegimeGraphModifiers | None" = None,
    transmission_chain: dict[str, Any] | None = None,
    scenario_id: str = "",
    run_id: str = "",
) -> ImpactMapResponse:
    """
    Build the unified ImpactMapResponse from simulation output.

    Args:
        result:              Full simulation result dict from SimulationEngine.
        gcc_nodes:           GCC_NODES list (43 nodes with lat/lng/sector).
        gcc_adjacency:       GCC_ADJACENCY dict (node_id → [neighbor_ids]).
        regime_modifiers:    RegimeGraphModifiers from regime_graph_adapter.
        transmission_chain:  TransmissionChain from transmission_engine.
        scenario_id:         Active scenario identifier.
        run_id:              Unique run identifier.

    Returns:
        ImpactMapResponse — fully typed, validated, regime-aware.
    """
    node_map: dict[str, dict] = {n["id"]: n for n in gcc_nodes}
    severity = float(result.get("event_severity", result.get("severity", 0.5)))

    # ── Regime influence ────────────────────────────────────────────────────
    regime_info = _build_regime_influence(regime_modifiers)
    threshold_shift = regime_info.failure_threshold_shift

    # ── Node stress from multiple sources ───────────────────────────────────
    node_stress = _collect_node_stress(result, gcc_nodes, severity, regime_modifiers)

    # ── Build typed nodes ───────────────────────────────────────────────────
    nodes: list[ImpactMapNode] = []
    node_loss_map = _collect_node_losses(result, node_map)

    for n in gcc_nodes:
        nid = n["id"]
        sector = n.get("sector", "unknown")
        stress = node_stress.get(nid, 0.0)
        criticality = n.get("criticality", 0.5)
        ttb = _estimate_time_to_breach(stress, criticality, threshold_shift)

        # Regime sensitivity
        regime_sens = 1.0
        if regime_modifiers is not None:
            regime_sens = regime_modifiers.node_sensitivity.get(nid, 1.0)

        nodes.append(ImpactMapNode(
            id=nid,
            label=n.get("label", nid),
            label_ar=n.get("label_ar", ""),
            type=_SECTOR_TO_NODE_TYPE.get(sector, "MARKET_INFRA"),
            sector=sector,
            layer=_SECTOR_TO_LAYER.get(sector, "INFRASTRUCTURE"),
            state=_classify_state(stress, ttb),
            stress_level=round(stress, 4),
            stress_classification=_classify_stress(stress),
            time_to_breach_hours=ttb,
            lat=n.get("lat", 0.0),
            lng=n.get("lng", 0.0),
            criticality=criticality,
            is_bottleneck=nid in _collect_bottleneck_ids(result),
            regime_sensitivity=round(regime_sens, 4),
            loss_usd=round(node_loss_map.get(nid, 0.0), 2),
        ))

    # ── Build typed edges ───────────────────────────────────────────────────
    edges = _build_typed_edges(gcc_adjacency, node_map, node_stress, severity, regime_modifiers)

    # ── Build propagation events ────────────────────────────────────────────
    prop_events = _build_propagation_events(
        result, node_map, severity, regime_modifiers, threshold_shift,
    )

    # ── Build aggregate timeline ────────────────────────────────────────────
    timeline = _build_timeline(prop_events, nodes, severity)

    # ── Build propagation headline ─────────────────────────────────────────
    from src.engines.propagation_headline_engine import build_propagation_headline
    prop_hl = build_propagation_headline(
        result.get("propagation_chain", []),
        gcc_nodes,
        scenario_id,
    )

    # ── Build headline ──────────────────────────────────────────────────────
    headline = _build_headline(
        result, nodes, prop_events,
        propagation_headline_en=prop_hl.get("propagation_headline_en", ""),
        propagation_headline_ar=prop_hl.get("propagation_headline_ar", ""),
    )

    # ── Categories ──────────────────────────────────────────────────────────
    categories = sorted({n.layer for n in nodes})

    # ── Scenario label ──────────────────────────────────────────────────────
    scenario_label = result.get("scenario_name", scenario_id.replace("_", " ").title())

    impact_map = ImpactMapResponse(
        run_id=run_id,
        scenario_id=scenario_id,
        scenario_label=scenario_label,
        nodes=nodes,
        edges=edges,
        categories=categories,
        propagation_events=prop_events,
        timeline=timeline,
        decision_overlays=[],  # populated by decision_overlay_engine
        regime=regime_info,
        headline=headline,
        validation_flags=[],   # populated by impact_map_validator
    )

    logger.info(
        "[ImpactMapEngine] Built: %d nodes, %d edges, %d events, %d timeline pts",
        impact_map.node_count, impact_map.edge_count,
        impact_map.propagation_event_count, len(timeline),
    )

    return impact_map


# ═══════════════════════════════════════════════════════════════════════════════
# Internal builders
# ═══════════════════════════════════════════════════════════════════════════════

def _build_regime_influence(
    modifiers: "RegimeGraphModifiers | None",
) -> RegimeInfluence:
    """Extract regime influence from modifiers."""
    if modifiers is None:
        return RegimeInfluence()

    from src.regime.regime_types import REGIME_DEFINITIONS
    defn = REGIME_DEFINITIONS.get(modifiers.regime_id, {})

    return RegimeInfluence(
        regime_id=modifiers.regime_id,
        regime_label=defn.get("label", modifiers.regime_id),
        regime_label_ar=defn.get("label_ar", ""),
        propagation_amplifier=modifiers.propagation_amplifier,
        delay_compression=modifiers.delay_compression,
        failure_threshold_shift=modifiers.failure_threshold_shift,
        persistence=defn.get("persistence", 0.9),
    )


def _collect_node_stress(
    result: dict,
    gcc_nodes: list[dict],
    severity: float,
    regime_modifiers: "RegimeGraphModifiers | None",
) -> dict[str, float]:
    """Collect stress for every node from all available sources."""
    stress: dict[str, float] = {}

    # Source 1: propagation chain
    for step in result.get("propagation_chain", result.get("propagation", [])):
        if not isinstance(step, dict):
            continue
        nids = step.get("path", [])
        if not nids and "entity_id" in step:
            nids = [step["entity_id"]]
        hop = step.get("hop", step.get("step", 1))
        for nid in nids:
            s = max(0.05, severity * (0.85 ** hop))
            stress[nid] = max(stress.get(nid, 0.0), s)

    # Source 2: financial entity stress
    financial = result.get("financial", [])
    if isinstance(financial, dict):
        financial = financial.get("top_entities", [])
    if isinstance(financial, list):
        for fi in financial:
            if isinstance(fi, dict):
                eid = fi.get("entity_id", "")
                ss = float(fi.get("stress_score", 0) or 0)
                if eid and ss > 0:
                    stress[eid] = max(stress.get(eid, 0.0), ss)

    # Source 3: sector-level stress blocks → distribute to sector nodes
    _sector_stress: dict[str, float] = {}
    for block_key in ("banking_stress", "insurance_stress", "fintech_stress"):
        block = result.get(block_key, {})
        if isinstance(block, dict):
            s = float(block.get("aggregate_stress", 0.0))
            sector = block_key.replace("_stress", "")
            if s > 0:
                _sector_stress[sector] = s

    for n in gcc_nodes:
        nid = n["id"]
        sector = n.get("sector", "")
        if nid not in stress and sector in _sector_stress:
            stress[nid] = _sector_stress[sector] * n.get("criticality", 0.5)

    # Apply regime modifiers
    if regime_modifiers is not None:
        from src.regime.regime_graph_adapter import compute_regime_adjusted_stress
        for nid in list(stress.keys()):
            stress[nid] = compute_regime_adjusted_stress(stress[nid], nid, regime_modifiers)

    # Clamp all to [0, 1]
    for nid in stress:
        stress[nid] = round(min(max(stress[nid], 0.0), 1.0), 4)

    return stress


def _collect_node_losses(result: dict, node_map: dict[str, dict]) -> dict[str, float]:
    """Collect per-node loss from financial impact data."""
    losses: dict[str, float] = {}
    financial = result.get("financial_impact", result.get("financial", []))
    if isinstance(financial, dict):
        financial = financial.get("top_entities", [])
    if isinstance(financial, list):
        for fi in financial:
            if isinstance(fi, dict):
                eid = fi.get("entity_id", "")
                loss = float(fi.get("loss_usd", 0) or 0)
                if eid and loss > 0:
                    losses[eid] = losses.get(eid, 0.0) + loss
    return losses


def _collect_bottleneck_ids(result: dict) -> set[str]:
    """Collect bottleneck node IDs from result."""
    ids: set[str] = set()
    for b in result.get("bottlenecks", []):
        bid = b.get("node_id") if isinstance(b, dict) else ""
        if bid:
            ids.add(bid)
    return ids


def _build_typed_edges(
    gcc_adjacency: dict[str, list[str]],
    node_map: dict[str, dict],
    node_stress: dict[str, float],
    severity: float,
    regime_modifiers: "RegimeGraphModifiers | None",
) -> list[ImpactMapEdge]:
    """Build typed edges from GCC_ADJACENCY with regime modifiers applied."""
    edges: list[ImpactMapEdge] = []

    for src_id, neighbors in gcc_adjacency.items():
        src_node = node_map.get(src_id)
        if not src_node:
            continue
        src_sector = src_node.get("sector", "unknown")

        for tgt_id in neighbors:
            tgt_node = node_map.get(tgt_id)
            if not tgt_node:
                continue
            tgt_sector = tgt_node.get("sector", "unknown")

            # Base delay from sector config
            base_delay = TX_BASE_DELAY_HOURS * TX_SECTOR_DELAY.get(src_sector, 1.0)
            transfer = TX_SECTOR_TRANSFER.get(src_sector, TX_SEVERITY_TRANSFER_RATIO)

            # Regime compression
            regime_mod = 1.0
            if regime_modifiers is not None:
                base_delay *= regime_modifiers.delay_compression
                transfer = min(1.0, transfer * regime_modifiers.propagation_amplifier)
                edge_key = f"{src_id}→{tgt_id}"
                regime_mod = regime_modifiers.edge_modifiers.get(edge_key, 1.0)
                transfer = min(1.0, transfer * regime_mod)

            # Breakable point detection
            src_stress = node_stress.get(src_id, 0.0)
            sev_at_target = src_stress * transfer
            breakable = (
                sev_at_target > TX_BREAKABLE_SEVERITY_THRESHOLD
                and base_delay < TX_CRITICAL_WINDOW_HOURS
            )

            # Active if source has meaningful stress
            is_active = src_stress > 0.05

            edge_type = _infer_edge_type(src_sector, tgt_sector)

            edges.append(ImpactMapEdge(
                source=src_id,
                target=tgt_id,
                type=edge_type,
                weight=round(min(1.0, sev_at_target), 4) if is_active else 0.0,
                delay_hours=round(base_delay, 2),
                transfer_ratio=round(transfer, 4),
                is_breakable=breakable,
                is_active=is_active,
                regime_modifier=round(regime_mod, 4),
                mechanism=f"{src_sector}→{tgt_sector}",
            ))

    return edges


def _build_propagation_events(
    result: dict,
    node_map: dict[str, dict],
    severity: float,
    regime_modifiers: "RegimeGraphModifiers | None",
    threshold_shift: float,
) -> list[PropagationEvent]:
    """Build ordered propagation events from chain data."""
    events: list[PropagationEvent] = []
    chain = result.get("propagation_chain", result.get("propagation", []))
    if not isinstance(chain, list):
        return events

    breach_threshold = max(0.3, 0.85 + threshold_shift)
    delay_compression = 1.0
    if regime_modifiers is not None:
        delay_compression = regime_modifiers.delay_compression

    # Group by step for ordering
    for step in chain:
        if not isinstance(step, dict):
            continue

        hop = int(step.get("step", step.get("hop", 0)))
        impact = float(step.get("impact", 0.0))

        # Entity-based format
        if "entity_id" in step:
            eid = step["entity_id"]
            node = node_map.get(eid, {})
            sector = node.get("sector", "unknown")
            arrival = hop * TX_BASE_DELAY_HOURS * TX_SECTOR_DELAY.get(sector, 1.0) * delay_compression

            sev = max(0.05, severity * (0.85 ** hop)) if impact <= 0 else min(1.0, impact)
            is_failure = sev >= breach_threshold

            events.append(PropagationEvent(
                event_id=f"PE-{eid}-h{hop}",
                hop=hop,
                source_id=step.get("source_id", ""),
                target_id=eid,
                arrival_hour=round(arrival, 2),
                severity_at_arrival=round(sev, 4),
                mechanism=step.get("mechanism_en", step.get("mechanism", "propagation")),
                mechanism_ar=step.get("mechanism_ar", ""),
                is_failure_event=is_failure,
                failure_type="threshold_breach" if is_failure else "",
            ))

        # Path-based format
        elif "path" in step:
            path = step["path"]
            for i, eid in enumerate(path):
                node = node_map.get(eid, {})
                sector = node.get("sector", "unknown")
                sub_hop = hop + i
                arrival = sub_hop * TX_BASE_DELAY_HOURS * TX_SECTOR_DELAY.get(sector, 1.0) * delay_compression
                sev = max(0.05, severity * (0.85 ** sub_hop))
                is_failure = sev >= breach_threshold

                events.append(PropagationEvent(
                    event_id=f"PE-{eid}-h{sub_hop}",
                    hop=sub_hop,
                    source_id=path[i - 1] if i > 0 else "",
                    target_id=eid,
                    arrival_hour=round(arrival, 2),
                    severity_at_arrival=round(sev, 4),
                    mechanism=step.get("mechanism_en", step.get("mechanism", "propagation")),
                    mechanism_ar=step.get("mechanism_ar", ""),
                    is_failure_event=is_failure,
                    failure_type="threshold_breach" if is_failure else "",
                ))

    # Sort by arrival time
    events.sort(key=lambda e: (e.arrival_hour, e.hop))

    # Deduplicate by event_id (keep earliest)
    seen: set[str] = set()
    deduped: list[PropagationEvent] = []
    for e in events:
        if e.event_id not in seen:
            seen.add(e.event_id)
            deduped.append(e)

    return deduped


def _build_timeline(
    events: list[PropagationEvent],
    nodes: list[ImpactMapNode],
    severity: float,
) -> list[TimelinePoint]:
    """Build aggregate timeline from propagation events for sparklines."""
    if not events:
        return [TimelinePoint(hour=0, active_nodes=0, breached_nodes=0,
                              aggregate_stress=0.0, cumulative_loss_usd=0.0)]

    # Determine time range
    max_hour = max(e.arrival_hour for e in events)
    max_hour = max(max_hour, 24.0)  # minimum 24h timeline

    # Build timeline at regular intervals
    interval = max(1.0, max_hour / 48)  # ~48 points
    points: list[TimelinePoint] = []

    total_node_loss = sum(n.loss_usd for n in nodes)

    t = 0.0
    while t <= max_hour + interval:
        events_by_t = [e for e in events if e.arrival_hour <= t]
        active_ids = {e.target_id for e in events_by_t}
        breached_ids = {e.target_id for e in events_by_t if e.is_failure_event}

        # Aggregate stress: mean severity of arrived events
        if events_by_t:
            agg_stress = sum(e.severity_at_arrival for e in events_by_t) / len(events_by_t)
        else:
            agg_stress = 0.0

        # Cumulative loss: proportional to fraction of nodes impacted
        frac = len(active_ids) / max(len(nodes), 1)
        cum_loss = total_node_loss * frac

        points.append(TimelinePoint(
            hour=round(t, 1),
            active_nodes=len(active_ids),
            breached_nodes=len(breached_ids),
            aggregate_stress=round(min(1.0, agg_stress), 4),
            cumulative_loss_usd=round(cum_loss, 2),
        ))
        t += interval

    return points


def _build_headline(
    result: dict,
    nodes: list[ImpactMapNode],
    events: list[PropagationEvent],
    propagation_headline_en: str = "",
    propagation_headline_ar: str = "",
) -> ImpactMapHeadline:
    """Build executive headline from nodes + events."""
    # Propagation headline: prefer injected value, then check result headline block
    headline_block = result.get("headline", {}) or {}
    prop_en = propagation_headline_en or headline_block.get("propagation_headline_en", "")
    prop_ar = propagation_headline_ar or headline_block.get("propagation_headline_ar", "")

    total_loss = sum(n.loss_usd for n in nodes)
    sectors = {n.sector for n in nodes if n.stress_level > 0.1}
    breached = [n for n in nodes if n.state == "BREACHED"]

    # Time to first breach
    breach_events = [e for e in events if e.is_failure_event]
    ttfb = min(e.arrival_hour for e in breach_events) if breach_events else None

    # Risk level from URS in result
    urs = float(result.get("unified_risk_score", 0.0))
    if isinstance(urs, dict):
        urs = float(urs.get("score", 0.0))

    if urs >= 0.80:
        risk_level = "SEVERE"
    elif urs >= 0.65:
        risk_level = "HIGH"
    elif urs >= 0.50:
        risk_level = "ELEVATED"
    elif urs >= 0.35:
        risk_level = "GUARDED"
    elif urs >= 0.20:
        risk_level = "LOW"
    else:
        risk_level = "NOMINAL"

    return ImpactMapHeadline(
        propagation_headline_en=prop_en or "No propagation chain detected — impact is localized.",
        propagation_headline_ar=prop_ar or "لم يتم اكتشاف سلسلة انتشار — التأثير محلي.",
        total_loss_usd=round(total_loss, 2),
        total_loss_formatted=_format_usd(total_loss),
        sectors_impacted=len(sectors),
        nodes_breached=len(breached),
        time_to_first_breach_hours=ttfb,
        risk_level=risk_level,
    )
