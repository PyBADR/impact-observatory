"""
Impact Observatory | مرصد الأثر
Governance Decision Gate — policy constants and validators for signal scoring.

This module defines the mandatory rules that govern whether a signal
may influence scenario metrics. It does NOT implement scoring — it
only provides the policy checks that v5 scoring must pass through.

Current state: all validators enforce OFF or ADVISORY mode.
SCORING mode is blocked until ENABLE_SIGNAL_SCORING_V5=true and
all governance checks pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from src.signal_ingestion.models import SnapshotFreshness, SignalSourceType
from src.signal_ingestion.feature_flags import (
    is_dev_signal_preview_enabled,
    is_live_signal_scoring_enabled,
)


# ═══════════════════════════════════════════════════════════════════════════════
# A. Minimum Confidence Constants
# ═══════════════════════════════════════════════════════════════════════════════

MIN_SOURCE_CONFIDENCE: float = 0.60
"""Source confidence_weight must be ≥ this to be trusted."""

MIN_SNAPSHOT_CONFIDENCE: float = 0.40
"""Snapshot confidence_score must be ≥ this for advisory mode."""

MIN_SCORING_CONFIDENCE: float = 0.50
"""Combined confidence must be ≥ this to enter scoring pipeline."""


# ═══════════════════════════════════════════════════════════════════════════════
# B. Freshness Thresholds (minutes)
# ═══════════════════════════════════════════════════════════════════════════════

FRESHNESS_WINDOWS: dict[str, dict[str, int]] = {
    "rss": {"fresh": 60, "recent": 120, "stale": 300},
    "api": {"fresh": 30, "recent": 60, "stale": 150},
    "market": {"fresh": 15, "recent": 30, "stale": 75},
    "government": {"fresh": 10080, "recent": 20160, "stale": 50400},  # 7d, 14d, 35d
    "manual": {"fresh": 0, "recent": 0, "stale": 0},  # always UNKNOWN
}


# ═══════════════════════════════════════════════════════════════════════════════
# C. Signal Adjustment Bounds
# ═══════════════════════════════════════════════════════════════════════════════

MAX_ADJUSTMENT_FACTOR: float = 0.15
"""Maximum ±15% adjustment a signal can apply to a scenario value."""


# ═══════════════════════════════════════════════════════════════════════════════
# D. Auto-Kill Triggers
# ═══════════════════════════════════════════════════════════════════════════════

MAX_CONSECUTIVE_FAILURES: int = 3
"""Disable source after this many consecutive failures."""


# ═══════════════════════════════════════════════════════════════════════════════
# E. Impact Mode
# ═══════════════════════════════════════════════════════════════════════════════

class ImpactMode(str, Enum):
    """Operating mode for signal impact on scenario metrics."""
    OFF = "off"              # Signals displayed only (dev preview)
    ADVISORY = "advisory"    # Signals explain risk but do not change metrics
    SCORING = "scoring"      # Signals can influence metrics (behind flag)


# ═══════════════════════════════════════════════════════════════════════════════
# F. Governance Decision
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceDecision(str, Enum):
    """Outcome of a governance gate evaluation."""
    ALLOWED = "allowed"
    BLOCKED_LOW_CONFIDENCE = "blocked_low_confidence"
    BLOCKED_STALE = "blocked_stale"
    BLOCKED_EXPIRED = "blocked_expired"
    ADVISORY_ONLY = "advisory_only"
    BLOCKED_KILL_SWITCH = "blocked_kill_switch"
    BLOCKED_FLAG_OFF = "blocked_flag_off"
    BLOCKED_BOUNDS_EXCEEDED = "blocked_bounds_exceeded"


@dataclass(frozen=True)
class GovernanceVerdict:
    """Result of evaluating the governance gate for a signal."""
    mode: ImpactMode
    decision: GovernanceDecision
    reason: str
    fallback_used: bool
    approved_by: str
    adjustment_allowed: float       # 0.0 if blocked

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "decision": self.decision.value,
            "reason": self.reason,
            "fallback_used": self.fallback_used,
            "approved_by": self.approved_by,
            "adjustment_allowed": self.adjustment_allowed,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# G. Validators
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_impact_mode() -> ImpactMode:
    """Determine the current impact mode from feature flags.

    OFF → ADVISORY → SCORING (progressive, flag-gated)
    """
    if not is_dev_signal_preview_enabled():
        return ImpactMode.OFF
    if not is_live_signal_scoring_enabled():
        return ImpactMode.ADVISORY
    return ImpactMode.SCORING


def evaluate_governance_gate(
    *,
    source_confidence: float,
    snapshot_confidence: float,
    freshness: SnapshotFreshness,
    adjustment_factor: float = 0.0,
) -> GovernanceVerdict:
    """Evaluate whether a signal passes the governance gate.

    This is the single entry point for all governance decisions.
    It checks mode, confidence, freshness, and bounds.

    Returns a GovernanceVerdict with the decision and context.
    """
    mode = resolve_impact_mode()

    # Gate 1: Mode OFF → everything blocked
    if mode == ImpactMode.OFF:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.BLOCKED_FLAG_OFF,
            reason="Signal preview is OFF. ENABLE_DEV_SIGNAL_PREVIEW not set.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 2: Expired signal → always blocked
    if freshness == SnapshotFreshness.EXPIRED:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.BLOCKED_EXPIRED,
            reason=f"Signal expired. Freshness={freshness.value}.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 3: Source confidence too low → blocked
    if source_confidence < MIN_SOURCE_CONFIDENCE:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.BLOCKED_LOW_CONFIDENCE,
            reason=f"Source confidence {source_confidence:.2f} < minimum {MIN_SOURCE_CONFIDENCE}.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 4: Snapshot confidence too low → advisory only
    if snapshot_confidence < MIN_SNAPSHOT_CONFIDENCE:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.ADVISORY_ONLY,
            reason=f"Snapshot confidence {snapshot_confidence:.2f} < minimum {MIN_SNAPSHOT_CONFIDENCE}. Advisory only.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 5: Stale signal → advisory only
    if freshness == SnapshotFreshness.STALE:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.ADVISORY_ONLY,
            reason=f"Signal is stale. Freshness={freshness.value}. Advisory only.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 6: Mode ADVISORY → display but don't score
    if mode == ImpactMode.ADVISORY:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.ADVISORY_ONLY,
            reason="Mode is ADVISORY. Signal displayed but does not affect scoring.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 7: Mode SCORING — check bounds
    if abs(adjustment_factor) > MAX_ADJUSTMENT_FACTOR:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.BLOCKED_BOUNDS_EXCEEDED,
            reason=f"Adjustment {adjustment_factor:.3f} exceeds ±{MAX_ADJUSTMENT_FACTOR} bounds.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # Gate 8: Scoring confidence check
    if snapshot_confidence < MIN_SCORING_CONFIDENCE:
        return GovernanceVerdict(
            mode=mode,
            decision=GovernanceDecision.ADVISORY_ONLY,
            reason=f"Snapshot confidence {snapshot_confidence:.2f} < scoring minimum {MIN_SCORING_CONFIDENCE}.",
            fallback_used=True,
            approved_by="system_rule",
            adjustment_allowed=0.0,
        )

    # All gates passed → ALLOWED
    clamped = max(-MAX_ADJUSTMENT_FACTOR, min(MAX_ADJUSTMENT_FACTOR, adjustment_factor))
    return GovernanceVerdict(
        mode=mode,
        decision=GovernanceDecision.ALLOWED,
        reason="All governance gates passed. Signal may influence scoring.",
        fallback_used=False,
        approved_by="feature_flag",
        adjustment_allowed=clamped,
    )
