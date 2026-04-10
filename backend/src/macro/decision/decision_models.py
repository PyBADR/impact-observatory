"""Macro Intelligence Layer — Decision Models (Pack 3).

Source-of-truth Pydantic contracts for the Decision Brain.

Domain types:
  ActionType      — classification of a recommended action
  DecisionPriority — overall priority tier
  DecisionAction  — a single recommended action for a domain
  DecisionOutput  — full decision output for one signal's MacroImpact

Design rules:
  - All enums are string-valued for JSON serialization
  - DecisionOutput.decision_reasoning includes propagation + graph reasoning
  - Backward-compatible: signal_id always traces back to the source signal
  - audit_hash covers all deterministic fields
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from src.macro.macro_enums import (
    ImpactDomain,
    SignalConfidence,
    SignalSeverity,
)


class ActionType(str, Enum):
    """Classification of a recommended decision action.

    Ordered roughly by escalation level.
    """
    NO_ACTION            = "no_action"             # no response needed
    MONITOR              = "monitor"               # passive watch
    REVIEW               = "review"                # active review of positions/exposures
    HEDGE                = "hedge"                 # hedge or reduce exposure
    ALERT_STAKEHOLDERS   = "alert_stakeholders"    # issue formal alert
    PAUSE_OPERATIONS     = "pause_operations"      # halt non-critical operations
    ESCALATE             = "escalate"              # escalate to senior decision makers
    ACTIVATE_CONTINGENCY = "activate_contingency"  # activate contingency / recovery plans


class DecisionPriority(str, Enum):
    """Overall decision priority tier.

    Maps to signal severity: NOMINAL→ROUTINE, LOW→WATCH,
    GUARDED→WATCH, ELEVATED→ADVISORY, HIGH→ALERT, SEVERE→CRITICAL.
    """
    ROUTINE  = "routine"   # no material action required
    WATCH    = "watch"     # elevated monitoring
    ADVISORY = "advisory"  # proactive review and hedging
    ALERT    = "alert"     # formal alert, senior awareness
    CRITICAL = "critical"  # immediate response, contingency activation


class DecisionAction(BaseModel):
    """A single recommended action targeting a specific domain.

    Generated deterministically from DomainImpact severity and domain type.
    """
    action_id: str = Field(
        ...,
        description="Stable composite key: '{action_type}:{domain}'"
    )
    domain: ImpactDomain
    action_type: ActionType
    description: str = Field(
        ...,
        description="Human-readable action description"
    )
    urgency: str = Field(
        ...,
        description=(
            "Urgency descriptor: 'immediate' | 'within_24h' | 'within_72h' | 'routine'"
        )
    )
    rationale: str = Field(
        ...,
        description=(
            "Why this action is recommended. References the domain's severity score, "
            "exposure weight, and propagation path."
        )
    )


class DecisionOutput(BaseModel):
    """Full decision output for one signal.

    Computed deterministically from MacroImpact.
    Provides prioritized action recommendations with full explainability.

    Backward compatibility:
      - signal_id always traces to the source PropagationResult → MacroImpact chain
      - decision_reasoning includes propagation reasoning (preserves graph fragments)
      - recommended_actions is ordered by action priority (highest urgency first)

    Usage:
      impact = compute_impact(propagation_result)
      decision = map_impact_to_decision(impact)
      # decision.recommended_actions → ordered action list
      # decision.priority → overall priority tier
      # decision.requires_escalation → bool gate for senior routing
    """
    decision_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    signal_title: str

    # ── Priority and escalation ───────────────────────────────────────────────
    priority: DecisionPriority
    requires_escalation: bool = Field(
        default=False,
        description=(
            "True if priority is ALERT or CRITICAL. "
            "Gate for routing to senior decision makers."
        )
    )

    # ── Actions ──────────────────────────────────────────────────────────────
    recommended_actions: list[DecisionAction] = Field(
        default_factory=list,
        description=(
            "Ordered list of recommended actions, highest urgency first. "
            "One action per domain × action_type combination."
        )
    )

    # ── Impact summary ────────────────────────────────────────────────────────
    affected_domains: list[ImpactDomain] = Field(default_factory=list)
    overall_severity: float = Field(ge=0.0, le=1.0)
    overall_severity_level: SignalSeverity
    confidence: SignalConfidence
    total_domains_reached: int = Field(default=0)

    # ── Explainability ────────────────────────────────────────────────────────
    impact_summary: str = Field(
        default="",
        description="One-sentence impact summary for dashboard display"
    )
    decision_reasoning: str = Field(
        default="",
        description=(
            "Full decision reasoning. Composed from: "
            "(1) impact summary; "
            "(2) action rationale; "
            "(3) propagation reasoning from each domain hit; "
            "(4) [Graph Brain] fragments where available."
        )
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    audit_hash: str = Field(default="")

    @model_validator(mode="after")
    def _compute_audit_hash(self) -> "DecisionOutput":
        if not self.audit_hash:
            canonical = json.dumps({
                "decision_id": str(self.decision_id),
                "signal_id": str(self.signal_id),
                "priority": self.priority.value,
                "overall_severity": self.overall_severity,
                "total_domains_reached": self.total_domains_reached,
                "requires_escalation": self.requires_escalation,
                "decided_at": self.decided_at.isoformat(),
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self
