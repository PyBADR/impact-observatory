"""
Propagation Headline Engine — builds the executive-facing propagation narrative.

The propagation chain is the platform's strongest analytical output.
This engine promotes it from a buried array to the executive headline.

Output:
  propagation_headline_en: "Hormuz blockade → Dubai Port congestion → Banking liquidity
                            freeze: 3 sectors impacted within 72h"
  propagation_headline_ar: Arabic equivalent

Called by run_orchestrator after propagation chain is available.
"""
from __future__ import annotations

from typing import Any


def build_propagation_headline(
    propagation_chain: list[dict[str, Any]],
    gcc_nodes: list[dict[str, Any]],
    scenario_id: str = "",
    max_hops: int = 4,
) -> dict[str, str]:
    """
    Build a single-sentence propagation headline from the chain.

    Extracts the first N hops, maps entity_ids to labels, counts sectors.

    Returns:
        {"propagation_headline_en": str, "propagation_headline_ar": str}
    """
    node_map: dict[str, dict] = {n["id"]: n for n in gcc_nodes}

    if not propagation_chain:
        return {
            "propagation_headline_en": "No propagation chain detected — impact is localized.",
            "propagation_headline_ar": "لم يتم اكتشاف سلسلة انتشار — التأثير محلي.",
        }

    # Extract entity labels from chain (handles both formats)
    entities: list[str] = []
    entities_ar: list[str] = []
    sectors_seen: set[str] = set()

    for step in propagation_chain[:max_hops]:
        if not isinstance(step, dict):
            continue

        # Entity-based format
        if "entity_id" in step:
            eid = step["entity_id"]
            node = node_map.get(eid, {})
            label = node.get("label", eid.replace("_", " ").title())
            label_ar = node.get("label_ar", label)
            sector = node.get("sector", step.get("sector", ""))
            if label not in entities:
                entities.append(label)
                entities_ar.append(label_ar)
                if sector:
                    sectors_seen.add(sector)

        # Path-based format
        elif "path" in step:
            for eid in step["path"]:
                node = node_map.get(eid, {})
                label = node.get("label", eid.replace("_", " ").title())
                label_ar = node.get("label_ar", label)
                sector = node.get("sector", "")
                if label not in entities:
                    entities.append(label)
                    entities_ar.append(label_ar)
                    if sector:
                        sectors_seen.add(sector)
                if len(entities) >= max_hops:
                    break

    if not entities:
        return {
            "propagation_headline_en": "Propagation chain present but entities could not be resolved.",
            "propagation_headline_ar": "سلسلة الانتشار موجودة لكن لم يتم حل الكيانات.",
        }

    # Build chain string
    chain_en = " → ".join(entities[:max_hops])
    chain_ar = " → ".join(entities_ar[:max_hops])

    # Count total unique entities and sectors in full chain
    total_entities = _count_unique_entities(propagation_chain)
    sector_count = len(sectors_seen) if sectors_seen else _count_sectors(propagation_chain, node_map)

    # Estimate time span from chain
    time_span = _estimate_time_span(propagation_chain)

    # Build headline
    if sector_count > 1:
        headline_en = (
            f"{chain_en}: {sector_count} sectors impacted, "
            f"{total_entities} nodes affected within {time_span}"
        )
        headline_ar = (
            f"{chain_ar}: {sector_count} قطاعات متأثرة، "
            f"{total_entities} عقد متأثرة خلال {time_span}"
        )
    else:
        headline_en = (
            f"{chain_en}: {total_entities} nodes affected within {time_span}"
        )
        headline_ar = (
            f"{chain_ar}: {total_entities} عقد متأثرة خلال {time_span}"
        )

    return {
        "propagation_headline_en": headline_en,
        "propagation_headline_ar": headline_ar,
    }


def _count_unique_entities(chain: list[dict]) -> int:
    """Count unique entity IDs in propagation chain."""
    seen: set[str] = set()
    for step in chain:
        if not isinstance(step, dict):
            continue
        if "entity_id" in step:
            seen.add(step["entity_id"])
        elif "path" in step:
            seen.update(step["path"])
    return len(seen) if seen else len(chain)


def _count_sectors(chain: list[dict], node_map: dict) -> int:
    """Count unique sectors in propagation chain."""
    sectors: set[str] = set()
    for step in chain:
        if not isinstance(step, dict):
            continue
        eid = step.get("entity_id", "")
        if eid and eid in node_map:
            s = node_map[eid].get("sector", "")
            if s:
                sectors.add(s)
        for eid in step.get("path", []):
            if eid in node_map:
                s = node_map[eid].get("sector", "")
                if s:
                    sectors.add(s)
    return max(len(sectors), 1)


def _estimate_time_span(chain: list[dict]) -> str:
    """Estimate time span from propagation chain steps."""
    max_step = 0
    for step in chain:
        if isinstance(step, dict):
            s = step.get("step", step.get("hop", 0))
            max_step = max(max_step, int(s) if s else 0)

    # Rough estimate: each hop ≈ 6-12 hours
    estimated_hours = max_step * 8
    if estimated_hours <= 0:
        estimated_hours = len(chain) * 8

    if estimated_hours <= 24:
        return f"{estimated_hours}h"
    else:
        return f"{estimated_hours // 24}d"
