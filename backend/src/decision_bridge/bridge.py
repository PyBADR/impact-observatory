"""Decision Bridge — assembles final DecisionEnvelope with audit + graph + explainability.

Wraps ImpactAssessment + DecisionOutput into a decision-ready envelope.
Generates SHA-256 audit digest, annotates graph, merges reasoning chain.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.config import BRIDGE_MIN_CONFIDENCE, BRIDGE_MIN_ACTIONS, BRIDGE_MIN_REASONING_STEPS
from src.decision_bridge.audit_hasher import compute_audit_digest
from src.decision_bridge.graph_annotator import annotate_graph
from src.decision_bridge.explainability_merger import merge_reasoning_chains

logger = logging.getLogger(__name__)


def _check_decision_readiness(
    impact_assessment: dict[str, Any],
    decision_output: dict[str, Any],
) -> tuple[bool, str]:
    """Check if output meets decision-readiness criteria.

    Returns (is_ready, reason).
    """
    reasons: list[str] = []

    # Confidence check
    confidence = float(impact_assessment.get("confidence", 0.0))
    if confidence < BRIDGE_MIN_CONFIDENCE:
        reasons.append(f"confidence {confidence:.2f} < {BRIDGE_MIN_CONFIDENCE}")

    # Actions check
    actions = decision_output.get("recommended_actions", [])
    if len(actions) < BRIDGE_MIN_ACTIONS:
        reasons.append(f"actions count {len(actions)} < {BRIDGE_MIN_ACTIONS}")

    # Reasoning steps check
    total_steps = sum(len(a.get("reasoning_chain", [])) for a in actions)
    if total_steps < BRIDGE_MIN_REASONING_STEPS:
        reasons.append(f"reasoning steps {total_steps} < {BRIDGE_MIN_REASONING_STEPS}")

    # Domain check
    domains = impact_assessment.get("affected_domains", [])
    if not domains:
        reasons.append("no affected domains")

    if reasons:
        return False, "; ".join(reasons)

    return True, "all criteria met"


def assemble_decision_envelope(
    impact_assessment: dict[str, Any],
    decision_output: dict[str, Any],
    pipeline_output: dict[str, Any],
    graph_store: Optional[Any] = None,
) -> dict[str, Any]:
    """Assemble final decision envelope.

    CONTRACT: Returns dict that passes DecisionEnvelope.model_validate().
    AUDIT: Generates SHA-256 hashes.
    GRAPH: Annotates graph store if available (fail-safe).
    """
    run_id = pipeline_output.get("run_id", "")
    scenario_id = pipeline_output.get("scenario_id", "")

    # ── Audit digest ──────────────────────────────────────────────────────
    audit_digest = compute_audit_digest(
        impact_assessment=impact_assessment,
        decision_output=decision_output,
    )

    # ── Graph annotation ──────────────────────────────────────────────────
    graph_status = annotate_graph(
        impact_assessment=impact_assessment,
        decision_output=decision_output,
        graph_store=graph_store,
    )

    # ── Merge reasoning chains ────────────────────────────────────────────
    existing_causal = pipeline_output.get("explainability", {}).get("causal_chain", [])
    merged_chain = merge_reasoning_chains(
        impact_assessment=impact_assessment,
        decision_output=decision_output,
        existing_causal_chain=existing_causal,
    )

    # ── Decision readiness ────────────────────────────────────────────────
    is_ready, ready_reason = _check_decision_readiness(
        impact_assessment=impact_assessment,
        decision_output=decision_output,
    )

    envelope = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "envelope_version": "1.0.0",

        "impact_assessment": impact_assessment,
        "decision_output": decision_output,

        "audit_digest": audit_digest,
        "graph_annotation_status": graph_status,

        "merged_reasoning_chain": merged_chain,

        "decision_ready": is_ready,
        "decision_ready_reason": ready_reason,
    }

    logger.info(
        "[DecisionBridge] run=%s ready=%s graph=%s hash=%s",
        run_id, is_ready, graph_status, audit_digest.get("combined_hash", "")[:16],
    )

    return envelope
