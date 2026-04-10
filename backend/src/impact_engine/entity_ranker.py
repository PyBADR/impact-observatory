"""Entity ranker — ranks affected entities by loss + stress for impact assessment.

Merges financial_impacts (top entities) with propagation chain to produce
a unified entity impact list.
"""
from __future__ import annotations

from typing import Any

from src.config import IE_ENTITY_STRESS_THRESHOLD


def rank_entities(
    financial_impacts: list[dict[str, Any]],
    propagation_chain: list[dict[str, Any]],
    shock_nodes: list[str],
    node_sectors: dict[str, str],
) -> list[dict[str, Any]]:
    """Rank affected entities by composite impact.

    Returns list of AffectedEntity-compatible dicts, sorted by loss descending.
    """
    shock_set = set(shock_nodes)

    # Build propagation lookup: entity_id → {mechanism, hop, propagation_score}
    prop_lookup: dict[str, dict[str, Any]] = {}
    for idx, step in enumerate(propagation_chain):
        eid = step.get("entity_id", "")
        if eid and eid not in prop_lookup:
            prop_lookup[eid] = {
                "mechanism": step.get("mechanism", ""),
                "hop": idx,
                "propagation_score": float(step.get("propagation_score", step.get("impact", 0.0))),
            }

    entities: list[dict[str, Any]] = []
    seen: set[str] = set()

    for fi in financial_impacts:
        eid = fi.get("entity_id", "")
        if not eid or eid in seen:
            continue

        stress = float(fi.get("stress_score", 0.0))
        if stress < IE_ENTITY_STRESS_THRESHOLD and eid not in shock_set:
            continue

        prop_info = prop_lookup.get(eid, {})

        entities.append({
            "entity_id": eid,
            "entity_label": fi.get("entity_label", ""),
            "entity_label_ar": fi.get("entity_label_ar", ""),
            "sector": fi.get("sector", "unknown"),
            "loss_usd": round(float(fi.get("loss_usd", 0.0)), 2),
            "stress_score": round(stress, 4),
            "classification": fi.get("classification", "NOMINAL"),
            "propagation_factor": round(float(fi.get("propagation_factor", 1.0)), 4),
            "is_shock_origin": eid in shock_set,
            "hop_distance": 0 if eid in shock_set else prop_info.get("hop", 99),
            "impact_mechanism": prop_info.get("mechanism", "direct_shock" if eid in shock_set else "propagation"),
        })
        seen.add(eid)

    # Sort by loss descending
    entities.sort(key=lambda e: -e["loss_usd"])

    return entities
