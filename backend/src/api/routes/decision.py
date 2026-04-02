"""Decision output endpoint — answers the 5 mandatory domain questions.

- What happened?
- What is the impact?
- What is affected?
- How big is the risk?
- What is the recommended action?

Returns the full GCC Decision Intelligence JSON contract with scores on 0-100
scale, affected infrastructure arrays, insurance impact, and full explanation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

import numpy as np

from src.engines.math.propagation import (
    build_adjacency_matrix,
    propagate_multi_step,
    compute_system_energy,
    compute_sector_impacts,
)
from src.engines.math_core.risk import ThreatSource, NodeContext, compute_risk_vector
from src.engines.math_core.disruption import compute_disruption_vector
from src.engines.math_core.confidence import compute_confidence_vector
from src.engines.math_core.gcc_weights import AssetClass
from src.engines.insurance_intelligence.claims_surge import compute_claims_surge
from src.engines.insurance_intelligence.portfolio_exposure import compute_portfolio_exposure
from src.engines.physics.system_stress import compute_system_stress
from src.services.state import get_state

router = APIRouter(prefix="/decision", tags=["decision"])


LAYER_TO_ASSET_CLASS = {
    "geography": AssetClass.INFRASTRUCTURE,
    "infrastructure": AssetClass.AIRPORT,
    "economy": AssetClass.ECONOMY,
    "finance": AssetClass.FINANCE,
    "society": AssetClass.SOCIETY,
}

# Classify node IDs by infrastructure type
AIRPORT_IDS = {"riyadh_apt", "dubai_apt", "kuwait_apt", "doha_apt", "muscat_apt", "bahrain_apt"}
PORT_IDS = {"jebel_ali", "ras_tanura", "shuwaikh", "hamad_port"}
CORRIDOR_IDS = {"hormuz", "shipping", "airspace"}


class DecisionRequest(BaseModel):
    shock_node_ids: list[str] = Field(default_factory=list)
    severity: float = Field(0.5, ge=0, le=1)
    event_type: str = "military_exercise"
    include_insurance: bool = True
    scenario_horizon: str = Field("72h", pattern=r"^(24h|72h|7d)$")


@router.post("/output")
async def decision_output(req: DecisionRequest):
    """Full decision intelligence output — matches mandatory JSON contract."""
    state = get_state()

    node_ids = state.node_ids
    node_map = {n["id"]: n for n in state.node_ids_full}
    n = len(node_ids)
    idx_map = {nid: i for i, nid in enumerate(node_ids)}

    # Build adjacency
    adjacency = build_adjacency_matrix(node_ids, state.edges)

    # Build threat sources from events
    threats = []
    for ev in state.events:
        if ev.get("lat") and ev.get("lng"):
            threats.append(ThreatSource(
                event_type=ev.get("event_type", "diplomatic_tension"),
                severity=ev.get("severity_score", 0.5),
                confidence=0.7,
                lat=ev["lat"],
                lng=ev["lng"],
                hours_ago=1.0,
                is_kinetic=ev.get("event_type") in ("military", "security"),
            ))

    # Build node contexts for GCC risk scoring
    node_contexts = []
    for nid in node_ids:
        nd = node_map.get(nid, {})
        layer = nd.get("layer", "infrastructure")
        ac = LAYER_TO_ASSET_CLASS.get(layer, AssetClass.INFRASTRUCTURE)
        node_contexts.append(NodeContext(
            node_id=nid,
            asset_class=ac,
            lat=nd.get("lat", 25.0),
            lng=nd.get("lng", 52.0),
        ))

    # Compute GCC risk vector
    risk_vector, risk_breakdowns = compute_risk_vector(node_contexts, threats)

    # Apply shock propagation
    shock = np.zeros(n)
    for sid in req.shock_node_ids:
        if sid in idx_map:
            shock[idx_map[sid]] = req.severity

    propagated, steps, _ = propagate_multi_step(adjacency, risk_vector, shock)

    # Disruption
    disruption_vec, disruption_bds = compute_disruption_vector(node_ids, propagated)

    # Confidence
    conf_vec, conf_bds = compute_confidence_vector(node_ids)

    # System stress
    stress = compute_system_stress(
        risk_vector=propagated,
        node_sectors=state.node_labels,
    )

    # Sector impacts
    sector_impacts = compute_sector_impacts(propagated, state.node_labels)

    # ---------------------------------------------------------------------------
    # Build affected infrastructure arrays (0-100 scale)
    # ---------------------------------------------------------------------------
    affected_airports = []
    affected_ports = []
    affected_corridors = []
    affected_routes = []
    top_affected = []

    sorted_indices = np.argsort(propagated)[::-1]
    for idx in sorted_indices:
        nid = node_ids[idx]
        nd = node_map.get(nid, {})
        risk_100 = round(float(propagated[idx]) * 100, 2)
        disruption_100 = round(float(disruption_vec[idx]) * 100, 2)
        entry = {
            "node_id": nid,
            "label": nd.get("label", nid),
            "label_ar": nd.get("label_ar", ""),
            "risk_score": risk_100,
            "disruption_score": disruption_100,
            "sector": nd.get("layer", "unknown"),
        }

        if risk_100 > 1.0:  # only include entities with non-trivial risk
            top_affected.append(entry)
            if nid in AIRPORT_IDS:
                affected_airports.append(entry)
            elif nid in PORT_IDS:
                affected_ports.append(entry)
            elif nid in CORRIDOR_IDS:
                affected_corridors.append(entry)

    # Routes = edges connecting affected nodes
    affected_node_set = {e["node_id"] for e in top_affected[:20]}
    for edge in state.edges:
        if edge["source"] in affected_node_set and edge["target"] in affected_node_set:
            affected_routes.append({
                "from": edge["source"],
                "to": edge["target"],
                "weight": edge.get("weight", 0.5),
                "category": edge.get("category", ""),
            })

    # ---------------------------------------------------------------------------
    # Insurance impact
    # ---------------------------------------------------------------------------
    insurance_impact = None
    if req.include_insurance:
        ins_results = []
        for idx in sorted_indices[:10]:
            nid = node_ids[idx]
            if propagated[idx] < 0.01:
                continue
            r = compute_claims_surge(
                nid, float(propagated[idx]), float(disruption_vec[idx]),
                0.5, 0.5, 1_000_000,
                stress.total_stress, float(1 - conf_vec[idx]),
            )
            ins_results.append({
                "entity_id": r.entity_id,
                "surge_score": r.surge_score,
                "uplift_pct": r.claims_uplift_pct,
                "classification": r.classification,
            })

        # Portfolio-level exposure
        portfolio_exposure = compute_portfolio_exposure(
            portfolio_id="gcc_aggregate",
            tiv_normalized=min(stress.total_stress + 0.3, 1.0),
            route_dependency=0.7 if any(nid in CORRIDOR_IDS for nid in req.shock_node_ids) else 0.3,
            region_risk=stress.total_stress,
            claims_elasticity=0.6,
        )

        # Determine underwriting class from top surge score
        max_surge = max((r["surge_score"] for r in ins_results), default=0.0)
        if max_surge >= 0.7:
            uw_class = "escalation"
        elif max_surge >= 0.5:
            uw_class = "restricted"
        elif max_surge >= 0.25:
            uw_class = "monitored"
        else:
            uw_class = "standard"

        insurance_impact = {
            "exposure_score": round(portfolio_exposure.exposure_score * 100, 2),
            "claims_surge_potential": round(max_surge * 100, 2),
            "underwriting_class": uw_class,
            "expected_claims_uplift": round(
                max((r["uplift_pct"] for r in ins_results), default=0.0), 2
            ),
            "flagged_entities": ins_results,
            "system_stress": round(stress.total_stress * 100, 2),
        }

    # ---------------------------------------------------------------------------
    # Build the 5 answers
    # ---------------------------------------------------------------------------
    what_happened = {
        "event": req.event_type,
        "shock_nodes": req.shock_node_ids,
        "active_events": len(state.events),
        "event_summary": [
            {"id": e.get("id"), "title": e.get("title"), "severity": e.get("severity_score")}
            for e in state.events[:5]
        ],
    }

    what_impact = {
        "system_stress": round(stress.total_stress * 100, 2),
        "stress_class": stress.stress_classification,
        "disrupted_nodes": int(np.sum(disruption_vec > 0.3)),
        "total_nodes": n,
        "disruption_pct": round(100 * int(np.sum(disruption_vec > 0.3)) / max(n, 1), 1),
        "sector_impacts": sector_impacts,
    }

    what_affected = {
        "count": len(top_affected),
        "top_entities": top_affected[:10],
        "sectors_hit": list({a["sector"] for a in top_affected}),
    }

    how_big = {
        "max_risk": round(float(np.max(propagated)) * 100, 2) if len(propagated) > 0 else 0,
        "mean_risk": round(float(np.mean(propagated)) * 100, 2) if len(propagated) > 0 else 0,
        "high_risk_count": int(np.sum(propagated > 0.5)),
        "critical_risk_count": int(np.sum(propagated > 0.7)),
        "system_classification": stress.stress_classification,
    }

    what_to_do = stress.recommendations

    # Economic impact estimate
    base_gdp_daily = 5_500_000_000  # ~$2T GCC GDP / 365
    economic_impact_usd = base_gdp_daily * stress.total_stress * req.severity
    if economic_impact_usd > 1_000_000_000:
        econ_str = f"${economic_impact_usd / 1_000_000_000:.1f}B estimated daily GDP impact"
    elif economic_impact_usd > 1_000_000:
        econ_str = f"${economic_impact_usd / 1_000_000:.0f}M estimated daily GDP impact"
    else:
        econ_str = f"${economic_impact_usd:,.0f} estimated daily GDP impact"

    # Propagation path (top causal chain)
    propagation_path = []
    for sid in req.shock_node_ids:
        if sid in idx_map:
            chain = [sid]
            for edge in state.edges:
                if edge["source"] == sid and edge["target"] in affected_node_set:
                    chain.append(edge["target"])
            propagation_path.append(chain)

    # Explanation
    explanation = {
        "top_causal_factors": [
            {"node_id": e["node_id"], "label": e["label"], "risk_score": e["risk_score"]}
            for e in top_affected[:5]
        ],
        "propagation_path": propagation_path,
        "confidence_breakdown": {
            "mean_confidence": round(float(np.mean(conf_vec)), 4),
            "min_confidence": round(float(np.min(conf_vec)), 4),
            "low_confidence_nodes": int(np.sum(conf_vec < 0.5)),
        },
        "weight_config_used": "GCC_ASSET_CLASS_DEFAULTS",
    }

    # ---------------------------------------------------------------------------
    # Full response matching mandatory JSON contract
    # ---------------------------------------------------------------------------
    return {
        # Top-level contract fields
        "event": req.event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_score": round(float(np.max(propagated)) * 100, 2),
        "disruption_score": round(float(np.max(disruption_vec)) * 100, 2),
        "confidence_score": round(float(np.mean(conf_vec)), 4),
        "system_stress": round(stress.total_stress * 100, 2),
        "affected_airports": affected_airports,
        "affected_ports": affected_ports,
        "affected_corridors": affected_corridors,
        "affected_routes": affected_routes[:20],
        "economic_impact_estimate": econ_str,
        "insurance_impact": insurance_impact,
        "recommended_action": what_to_do[0] if what_to_do else "Monitor situation",
        "scenario_horizon": req.scenario_horizon,
        "explanation": explanation,

        # Extended decision object (preserves backward compat)
        "decision": {
            "what_happened": what_happened,
            "what_is_the_impact": what_impact,
            "what_is_affected": what_affected,
            "how_big_is_the_risk": how_big,
            "recommended_actions": what_to_do,
        },
        "system_state": {
            "total_stress": stress.total_stress,
            "stress_classification": stress.stress_classification,
            "system_energy": stress.energy,
            "confidence": stress.confidence,
            "propagation_stage": stress.propagation_stage,
            "dominant_sector": stress.dominant_sector,
        },
        "top_affected": top_affected[:15],
        "sector_impacts": sector_impacts,
        "risk_vector": propagated.tolist(),
        "metadata": {
            "n_nodes": n,
            "n_events": len(state.events),
            "n_flights": len(state.flights),
            "n_vessels": len(state.vessels),
            "propagation_steps": steps,
            "equation": "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U",
        },
    }
