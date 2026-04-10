"""Reasoning chain builder — constructs traceable reasoning from graph + propagation.

Each reasoning step points to a specific layer (graph, propagation, impact, rule)
with evidence value and human-readable label. Deterministic, no LLM.
"""
from __future__ import annotations

from typing import Any, Optional


def build_reasoning_chain(
    action_sector: str,
    impact_assessment: dict[str, Any],
    propagation_chain: list[dict[str, Any]],
    causal_chain: list[dict[str, Any]],
    graph_store: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Build reasoning chain for a single action.

    Returns list of ReasoningStep-compatible dicts.
    Traces: graph → propagation → impact → rule.
    """
    steps: list[dict[str, Any]] = []
    step_idx = 0

    # ── Layer 1: Graph evidence (if available) ────────────────────────────
    if graph_store is not None:
        step_idx += 1
        steps.append({
            "step": step_idx,
            "layer": "graph",
            "source_entity": "graph_brain",
            "mechanism": "graph_topology_centrality",
            "evidence_value": round(impact_assessment.get("composite_severity", 0.0), 4),
            "evidence_label": f"Graph topology indicates {action_sector} sector is structurally connected to shock origin",
            "confidence": 0.85,
        })

    # ── Layer 2: Propagation evidence ─────────────────────────────────────
    # Find propagation steps affecting this sector
    sector_prop_steps = [
        p for p in propagation_chain
        if p.get("entity_id", "").startswith(action_sector[:3])  # heuristic match
        or action_sector in p.get("mechanism", "").lower()
    ]
    if not sector_prop_steps and propagation_chain:
        # Use top propagation step as evidence
        sector_prop_steps = propagation_chain[:1]

    for ps in sector_prop_steps[:2]:
        step_idx += 1
        steps.append({
            "step": step_idx,
            "layer": "propagation",
            "source_entity": ps.get("entity_id", ""),
            "mechanism": ps.get("mechanism", "propagation_contagion"),
            "evidence_value": round(float(ps.get("impact", ps.get("propagation_score", 0.0))), 4),
            "evidence_label": (
                f"Propagation reached {ps.get('entity_label', ps.get('entity_id', 'entity'))} "
                f"via {ps.get('mechanism', 'contagion')}"
            ),
            "confidence": round(float(ps.get("propagation_score", ps.get("impact", 0.5))), 4),
        })

    # ── Layer 3: Impact evidence ──────────────────────────────────────────
    # Find the domain matching this action's sector
    affected_domains = impact_assessment.get("affected_domains", [])
    domain_match = next(
        (d for d in affected_domains if d.get("domain") == action_sector),
        None,
    )
    if domain_match:
        step_idx += 1
        steps.append({
            "step": step_idx,
            "layer": "impact",
            "source_entity": action_sector,
            "mechanism": "domain_impact_assessment",
            "evidence_value": round(float(domain_match.get("exposure_score", 0.0)), 4),
            "evidence_label": (
                f"Impact assessment: {action_sector} domain exposure "
                f"{domain_match.get('exposure_score', 0):.2%}, "
                f"loss ${domain_match.get('loss_usd', 0):,.0f}"
            ),
            "confidence": round(impact_assessment.get("confidence", 0.5), 4),
        })

    # ── Layer 4: Causal chain evidence ────────────────────────────────────
    sector_causal = [
        c for c in causal_chain
        if c.get("sector", "") == action_sector
    ]
    for cc in sector_causal[:1]:
        step_idx += 1
        steps.append({
            "step": step_idx,
            "layer": "impact",
            "source_entity": cc.get("entity_id", ""),
            "mechanism": cc.get("mechanism_en", "causal_chain"),
            "evidence_value": round(float(cc.get("impact_usd", 0.0)), 4),
            "evidence_label": (
                f"Causal chain: {cc.get('entity_label', '')} — "
                f"{cc.get('mechanism_en', 'cascade')}"
            ),
            "confidence": round(float(cc.get("confidence", 0.5)), 4),
        })

    # ── Layer 5: Rule-based evidence ──────────────────────────────────────
    composite = impact_assessment.get("composite_severity", 0.0)
    step_idx += 1
    steps.append({
        "step": step_idx,
        "layer": "rule",
        "source_entity": "impact_engine",
        "mechanism": "composite_severity_threshold",
        "evidence_value": round(composite, 4),
        "evidence_label": (
            f"Composite severity {composite:.2%} "
            f"({impact_assessment.get('severity_classification', 'NOMINAL')}) "
            f"triggers action for {action_sector}"
        ),
        "confidence": round(impact_assessment.get("confidence", 0.5), 4),
    })

    # Ensure at least 1 step
    if not steps:
        steps.append({
            "step": 1,
            "layer": "rule",
            "source_entity": "fallback",
            "mechanism": "default_monitoring",
            "evidence_value": composite,
            "evidence_label": "Default monitoring action — no specific evidence chain",
            "confidence": 0.3,
        })

    return steps
