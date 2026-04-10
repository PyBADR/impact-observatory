"""Explainability merger — merges Pack 3 reasoning into the existing causal chain.

Produces a unified reasoning chain that spans:
graph → propagation → impact → decision
"""
from __future__ import annotations

from typing import Any


def merge_reasoning_chains(
    impact_assessment: dict[str, Any],
    decision_output: dict[str, Any],
    existing_causal_chain: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge existing causal chain with Pack 3 reasoning chains.

    Returns a unified list of reasoning steps, ordered by layer:
    1. existing causal chain (propagation layer)
    2. impact assessment evidence
    3. decision reasoning chains

    Does NOT modify the existing causal chain — creates a new merged list.
    """
    merged: list[dict[str, Any]] = []
    step_idx = 0

    # ── Phase 1: Existing causal chain (propagation layer) ────────────────
    for cc in existing_causal_chain:
        step_idx += 1
        merged.append({
            "step": step_idx,
            "layer": "propagation",
            "source": "causal_chain",
            "entity_id": cc.get("entity_id", ""),
            "entity_label": cc.get("entity_label", ""),
            "mechanism": cc.get("mechanism_en", cc.get("mechanism", "")),
            "impact_usd": float(cc.get("impact_usd", 0.0)),
            "sector": cc.get("sector", ""),
            "confidence": float(cc.get("confidence", 0.0)),
        })

    # ── Phase 2: Impact assessment summary ────────────────────────────────
    step_idx += 1
    merged.append({
        "step": step_idx,
        "layer": "impact",
        "source": "impact_engine",
        "entity_id": "impact_engine",
        "entity_label": "Impact Assessment",
        "mechanism": "composite_severity_computation",
        "impact_usd": float(impact_assessment.get("total_exposure_usd", 0.0)),
        "sector": impact_assessment.get("primary_domain", "cross-sector"),
        "confidence": float(impact_assessment.get("confidence", 0.0)),
        "composite_severity": float(impact_assessment.get("composite_severity", 0.0)),
        "domain_count": int(impact_assessment.get("domain_count", 0)),
        "entity_count": int(impact_assessment.get("entity_count", 0)),
    })

    # ── Phase 3: Decision reasoning (top 3 actions only) ──────────────────
    for action in decision_output.get("recommended_actions", [])[:3]:
        for rs in action.get("reasoning_chain", []):
            step_idx += 1
            merged.append({
                "step": step_idx,
                "layer": f"decision:{rs.get('layer', 'rule')}",
                "source": f"decision_brain:{action.get('action_id', '')}",
                "entity_id": rs.get("source_entity", ""),
                "entity_label": rs.get("evidence_label", ""),
                "mechanism": rs.get("mechanism", ""),
                "impact_usd": 0.0,
                "sector": action.get("sector", ""),
                "confidence": float(rs.get("confidence", 0.0)),
                "action_id": action.get("action_id", ""),
                "action_type": action.get("action_type", ""),
                "urgency": action.get("urgency", ""),
            })

    # ── Phase 4: Decision summary ─────────────────────────────────────────
    step_idx += 1
    merged.append({
        "step": step_idx,
        "layer": "decision",
        "source": "decision_brain",
        "entity_id": "decision_brain",
        "entity_label": "Decision Summary",
        "mechanism": "impact_weighted_ranking",
        "impact_usd": 0.0,
        "sector": "cross-sector",
        "confidence": float(decision_output.get("overall_confidence", 0.0)),
        "primary_action_type": decision_output.get("primary_action_type", "MONITOR"),
        "overall_urgency": decision_output.get("overall_urgency", "MONITOR"),
        "actions_count": len(decision_output.get("recommended_actions", [])),
        "fallback_active": decision_output.get("fallback_active", False),
    })

    return merged
