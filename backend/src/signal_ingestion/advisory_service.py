"""
Impact Observatory | مرصد الأثر
Advisory Service — v5 advisory-only signal interpretation.

This service:
  - Takes a SignalSnapshot + scenario_id
  - Evaluates the governance gate
  - Produces an advisory explanation ONLY
  - Does NOT change any scenario value
  - Does NOT call scoring functions
  - Does NOT modify SCENARIO_CATALOG
  - Returns fallback advisory if signal is low confidence or stale

Hard rules:
  - metric_after == metric_before (always)
  - scoring_applied == False (always)
  - SCENARIO_CATALOG is read, never written
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from src.signal_ingestion.models import SignalSnapshot, SnapshotFreshness
from src.signal_ingestion.advisory_model import SignalAdvisory
from src.signal_ingestion.audit_log import SignalAuditLog, SignalAuditAction
from src.signal_ingestion.governance import (
    evaluate_governance_gate,
    GovernanceDecision,
    ImpactMode,
    MIN_SOURCE_CONFIDENCE,
    MIN_SNAPSHOT_CONFIDENCE,
)
from src.signal_ingestion.feature_flags import is_signal_advisory_v5_enabled
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# Advisory text generation (template-based, no LLM)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_advisory_text(snapshot: SignalSnapshot, scenario_name: str) -> str:
    """Generate advisory explanation text from snapshot context."""
    return (
        f'Signal "{snapshot.title}" provides context for the '
        f"{scenario_name} scenario. This is advisory only — "
        f"no metrics have been changed."
    )


def _build_risk_context(snapshot: SignalSnapshot, scenario_name: str) -> str:
    """Generate risk context text from snapshot."""
    sectors = ", ".join(snapshot.related_sectors) if snapshot.related_sectors else "general"
    return (
        f"This signal relates to the {sectors} sector(s) and "
        f"may provide additional context for assessing the "
        f"{scenario_name} scenario."
    )


def _build_suggested_review(snapshot: SignalSnapshot, fallback: bool) -> str:
    """Generate suggested review text."""
    if fallback:
        return (
            "Signal confidence is below threshold or data is stale. "
            "Treat as background context only. No action required."
        )
    return (
        "Review this signal alongside scenario outputs for additional "
        "context. Signal is advisory only — metrics are unchanged."
    )


def _build_fallback_advisory_text(snapshot: SignalSnapshot, reason: str) -> str:
    """Generate fallback advisory text for low-confidence/stale signals."""
    return (
        f'Signal "{snapshot.title}" was evaluated but did not meet '
        f"confidence or freshness thresholds ({reason}). "
        f"Displayed as background context only — no metrics changed."
    )


def _generate_advisory_id(snapshot_id: str, scenario_id: str) -> str:
    """Generate a deterministic advisory ID."""
    raw = f"advisory|{snapshot_id}|{scenario_id}"
    return f"adv_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Core advisory evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_advisory(
    snapshot: SignalSnapshot,
    scenario_id: str,
    *,
    source_confidence: float = 0.0,
    audit_log: Optional[SignalAuditLog] = None,
) -> Optional[SignalAdvisory]:
    """Evaluate a signal snapshot and produce an advisory interpretation.

    This function:
      - Checks that the advisory feature flag is enabled
      - Validates the scenario exists in SCENARIO_CATALOG (read-only)
      - Evaluates the governance gate
      - Produces a SignalAdvisory with metric_after == metric_before
      - Never calls scoring, never modifies SCENARIO_CATALOG

    Parameters
    ----------
    snapshot : SignalSnapshot
        The signal snapshot to interpret.
    scenario_id : str
        The scenario to interpret the signal against.
    source_confidence : float
        Base confidence weight of the signal source (0.0–1.0).
    audit_log : SignalAuditLog | None
        Optional audit log to record the evaluation.

    Returns
    -------
    SignalAdvisory | None
        Advisory interpretation, or None if flag is disabled or scenario
        does not exist.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Gate 1: feature flag must be enabled
    if not is_signal_advisory_v5_enabled():
        if audit_log:
            audit_log.record(
                action=SignalAuditAction.FALLBACK_USED,
                source_id=snapshot.source_id,
                snapshot_id=snapshot.snapshot_id,
                detail="Advisory v5 flag is disabled. No advisory generated.",
            )
        return None

    # Gate 2: scenario must exist (read-only lookup)
    scenario = SCENARIO_CATALOG.get(scenario_id)
    if scenario is None:
        if audit_log:
            audit_log.record(
                action=SignalAuditAction.FALLBACK_USED,
                source_id=snapshot.source_id,
                snapshot_id=snapshot.snapshot_id,
                detail=f"Scenario '{scenario_id}' not found in SCENARIO_CATALOG.",
            )
        return None

    # Read the current metric (base_loss_usd) — never modify it
    metric_before = float(scenario.get("base_loss_usd", 0.0))

    # Evaluate governance gate
    verdict = evaluate_governance_gate(
        source_confidence=source_confidence or snapshot.confidence_score,
        snapshot_confidence=snapshot.confidence_score,
        freshness=snapshot.freshness_status,
        adjustment_factor=0.0,  # Advisory mode — no adjustment
    )

    # Determine if this is a fallback advisory
    is_fallback = verdict.decision != GovernanceDecision.ALLOWED and \
                  verdict.decision != GovernanceDecision.ADVISORY_ONLY

    # For advisory mode, ADVISORY_ONLY is the expected successful outcome
    # Only truly blocked signals get fallback treatment
    if verdict.decision in (
        GovernanceDecision.BLOCKED_LOW_CONFIDENCE,
        GovernanceDecision.BLOCKED_EXPIRED,
        GovernanceDecision.BLOCKED_KILL_SWITCH,
        GovernanceDecision.BLOCKED_FLAG_OFF,
    ):
        is_fallback = True

    scenario_name = scenario.get("name", scenario_id)

    # Build advisory text
    if is_fallback:
        advisory_text = _build_fallback_advisory_text(snapshot, verdict.reason)
    else:
        advisory_text = _build_advisory_text(snapshot, scenario_name)

    risk_context = _build_risk_context(snapshot, scenario_name)
    suggested_review = _build_suggested_review(snapshot, is_fallback)

    advisory = SignalAdvisory(
        advisory_id=_generate_advisory_id(snapshot.snapshot_id, scenario_id),
        scenario_id=scenario_id,
        snapshot_id=snapshot.snapshot_id,
        source_id=snapshot.source_id,
        confidence=snapshot.confidence_score,
        freshness_status=snapshot.freshness_status,
        advisory_text=advisory_text,
        risk_context=risk_context,
        suggested_review=suggested_review,
        metric_before=metric_before,
        metric_after=metric_before,  # HARD RULE: metric_after == metric_before
        scoring_applied=False,        # HARD RULE: always False
        fallback_used=is_fallback,
        timestamp=now,
    )

    # Record audit entry
    if audit_log:
        audit_log.record(
            action=SignalAuditAction.SNAPSHOT_CREATED,
            source_id=snapshot.source_id,
            snapshot_id=snapshot.snapshot_id,
            detail=(
                f"Advisory generated: scenario={scenario_id}, "
                f"confidence={snapshot.confidence_score:.4f}, "
                f"freshness={snapshot.freshness_status.value}, "
                f"metric_before={metric_before}, "
                f"metric_after={metric_before}, "
                f"scoring_applied=False, "
                f"fallback_used={is_fallback}, "
                f"governance_decision={verdict.decision.value}"
            ),
        )

    return advisory


# ═══════════════════════════════════════════════════════════════════════════════
# Batch advisory evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_advisories(
    snapshots: list[SignalSnapshot],
    scenario_id: str,
    *,
    source_confidence: float = 0.0,
    audit_log: Optional[SignalAuditLog] = None,
) -> list[SignalAdvisory]:
    """Evaluate multiple snapshots and return advisory interpretations.

    Returns only non-None advisories. Skips snapshots that fail
    feature flag or scenario validation.
    """
    results: list[SignalAdvisory] = []
    for snapshot in snapshots:
        advisory = evaluate_advisory(
            snapshot,
            scenario_id,
            source_confidence=source_confidence,
            audit_log=audit_log,
        )
        if advisory is not None:
            results.append(advisory)
    return results
