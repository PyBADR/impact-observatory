"""Fallback path — produces valid decision output when graph is unavailable.

Uses propagation chain as sole evidence source.
Ensures every signal still produces a decision-ready output.
"""
from __future__ import annotations

from typing import Any


def build_fallback_reasoning(
    action_sector: str,
    composite_severity: float,
    propagation_chain: list[dict[str, Any]],
    confidence: float,
) -> list[dict[str, Any]]:
    """Build minimal reasoning chain from propagation only (no graph).

    Returns list of ReasoningStep-compatible dicts with at least 1 step.
    """
    steps: list[dict[str, Any]] = []
    step_idx = 0

    # Find best propagation evidence for this sector
    best_prop = None
    for p in propagation_chain:
        eid = p.get("entity_id", "")
        mech = p.get("mechanism", "")
        if action_sector in eid or action_sector in mech.lower():
            best_prop = p
            break

    if best_prop is None and propagation_chain:
        best_prop = propagation_chain[0]

    if best_prop:
        step_idx += 1
        steps.append({
            "step": step_idx,
            "layer": "propagation",
            "source_entity": best_prop.get("entity_id", ""),
            "mechanism": best_prop.get("mechanism", "propagation"),
            "evidence_value": round(float(best_prop.get("impact", 0.0)), 4),
            "evidence_label": (
                f"Propagation evidence: {best_prop.get('entity_label', 'entity')} "
                f"impact {float(best_prop.get('impact', 0)):,.4f}"
            ),
            "confidence": round(float(best_prop.get("propagation_score",
                                      best_prop.get("impact", confidence))), 4),
        })

    # Always add rule-based step
    step_idx += 1
    steps.append({
        "step": step_idx,
        "layer": "rule",
        "source_entity": "fallback_engine",
        "mechanism": "severity_threshold_rule",
        "evidence_value": round(composite_severity, 4),
        "evidence_label": (
            f"Severity {composite_severity:.2%} triggers {action_sector} sector monitoring "
            f"(graph unavailable — fallback mode)"
        ),
        "confidence": round(confidence * 0.85, 4),  # slight confidence reduction for fallback
    })

    return steps
