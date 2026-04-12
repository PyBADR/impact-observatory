"""
Enforcement Engine — Deterministic Policy Evaluation
=====================================================

Pure functions. No DB access. No side effects.
Reads governance state and enforcement policies, produces
an immutable EnforcementDecision.

Evaluation order:
  1. Rule lifecycle status check
  2. Truth validation check
  3. Calibration status check
  4. Performance threshold check
  5. Confidence threshold check
  6. Policy-driven enforcement (priority-ordered)

First non-ALLOW policy wins (strictest enforcement).
If no policy triggers, decision is ALLOW.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .schemas import (
    EnforcementAction,
    EnforcementDecision,
    EnforcementPolicy,
    EnforcementTriggerType,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Context — everything the engine needs to evaluate
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class EnforcementContext:
    """Frozen snapshot of governance state for a decision candidate.

    All fields are pre-fetched by the caller. The engine never
    touches the database.
    """

    decision_log_id: str
    rule_id: str
    spec_id: Optional[str] = None

    # Decision metadata
    decision_action: Optional[str] = None
    decision_risk_level: Optional[str] = None
    decision_country: Optional[str] = None
    decision_sector: Optional[str] = None
    decision_confidence: float = 0.5

    # Governance state
    rule_status: Optional[str] = None          # e.g., "ACTIVE", "REVIEW", "DRAFT"
    truth_valid: Optional[bool] = None         # latest truth validation result
    unresolved_calibrations: int = 0           # count of TRIGGERED calibration events
    latest_correctness_score: Optional[float] = None  # from RulePerformanceSnapshot


# ═══════════════════════════════════════════════════════════════════════════════
# Scope matching
# ═══════════════════════════════════════════════════════════════════════════════


def _scope_matches(
    policy: EnforcementPolicy,
    context: EnforcementContext,
) -> bool:
    """Check whether the policy's scope covers the decision context.

    Empty scope = applies to all. Non-empty scope = must match.
    """
    if policy.scope_risk_levels and context.decision_risk_level:
        if context.decision_risk_level not in policy.scope_risk_levels:
            return False

    if policy.scope_actions and context.decision_action:
        if context.decision_action not in policy.scope_actions:
            return False

    if policy.scope_countries and context.decision_country:
        if context.decision_country not in policy.scope_countries:
            return False

    if policy.scope_sectors and context.decision_sector:
        if context.decision_sector not in policy.scope_sectors:
            return False

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Condition evaluation
# ═══════════════════════════════════════════════════════════════════════════════

# Minimum acceptable statuses (ordered by maturity)
_STATUS_RANK: Dict[str, int] = {
    "DRAFT": 0,
    "REVIEW": 1,
    "APPROVED": 2,
    "ACTIVE": 3,
}


def _check_conditions(
    policy: EnforcementPolicy,
    context: EnforcementContext,
) -> tuple[bool, str]:
    """Check whether the policy's conditions are met (i.e., the policy FIRES).

    Returns (fires, reason). fires=True means enforcement should apply.
    """

    # Rule lifecycle status
    if policy.min_rule_status:
        min_rank = _STATUS_RANK.get(policy.min_rule_status, 0)
        actual_rank = _STATUS_RANK.get(context.rule_status or "", -1)
        if actual_rank < min_rank:
            return True, f"Rule status '{context.rule_status}' below minimum '{policy.min_rule_status}'"

    # Truth validation
    if policy.require_truth_validation and context.truth_valid is False:
        return True, "Truth validation failed for underlying data"

    # Calibration events
    if policy.max_unresolved_calibrations is not None:
        if context.unresolved_calibrations > policy.max_unresolved_calibrations:
            return True, (
                f"Unresolved calibrations ({context.unresolved_calibrations}) "
                f"exceeds max ({policy.max_unresolved_calibrations})"
            )

    # Correctness score
    if policy.min_correctness_score is not None and context.latest_correctness_score is not None:
        if context.latest_correctness_score < policy.min_correctness_score:
            return True, (
                f"Correctness score ({context.latest_correctness_score:.3f}) "
                f"below minimum ({policy.min_correctness_score})"
            )

    # Confidence threshold
    if policy.min_confidence_score is not None:
        if context.decision_confidence < policy.min_confidence_score:
            return True, (
                f"Decision confidence ({context.decision_confidence:.3f}) "
                f"below minimum ({policy.min_confidence_score})"
            )

    return False, ""


# ═══════════════════════════════════════════════════════════════════════════════
# Trigger type resolution
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_trigger_type(
    policy: EnforcementPolicy,
    context: EnforcementContext,
) -> str:
    """Determine which trigger type caused the policy to fire."""
    action = policy.enforcement_action

    if policy.min_rule_status:
        status = context.rule_status or ""
        min_rank = _STATUS_RANK.get(policy.min_rule_status, 0)
        actual_rank = _STATUS_RANK.get(status, -1)
        if actual_rank < min_rank:
            if status in ("DRAFT", "REVIEW"):
                return EnforcementTriggerType.RULE_IN_REVIEW
            return EnforcementTriggerType.RULE_NOT_ACTIVE

    if policy.require_truth_validation and context.truth_valid is False:
        return EnforcementTriggerType.TRUTH_VALIDATION_FAILED

    if (policy.max_unresolved_calibrations is not None
            and context.unresolved_calibrations > policy.max_unresolved_calibrations):
        return EnforcementTriggerType.CALIBRATION_UNRESOLVED

    if (policy.min_correctness_score is not None
            and context.latest_correctness_score is not None
            and context.latest_correctness_score < policy.min_correctness_score):
        return EnforcementTriggerType.PERFORMANCE_BELOW_THRESHOLD

    if (policy.min_confidence_score is not None
            and context.decision_confidence < policy.min_confidence_score):
        return EnforcementTriggerType.CONFIDENCE_TOO_LOW

    # Fall through to policy-type trigger
    _action_trigger_map = {
        EnforcementAction.BLOCK: EnforcementTriggerType.POLICY_BLOCK,
        EnforcementAction.ESCALATE: EnforcementTriggerType.POLICY_ESCALATE,
        EnforcementAction.REQUIRE_APPROVAL: EnforcementTriggerType.POLICY_REQUIRE_APPROVAL,
        EnforcementAction.SHADOW_ONLY: EnforcementTriggerType.POLICY_SHADOW,
        EnforcementAction.FALLBACK: EnforcementTriggerType.POLICY_FALLBACK,
        EnforcementAction.DEGRADE_CONFIDENCE: EnforcementTriggerType.POLICY_DEGRADE,
    }
    return _action_trigger_map.get(action, EnforcementTriggerType.NO_TRIGGER)


# ═══════════════════════════════════════════════════════════════════════════════
# Action priority (strictest wins)
# ═══════════════════════════════════════════════════════════════════════════════

_ACTION_SEVERITY: Dict[str, int] = {
    EnforcementAction.BLOCK: 100,
    EnforcementAction.ESCALATE: 90,
    EnforcementAction.REQUIRE_APPROVAL: 80,
    EnforcementAction.SHADOW_ONLY: 70,
    EnforcementAction.FALLBACK: 60,
    EnforcementAction.DEGRADE_CONFIDENCE: 50,
    EnforcementAction.ALLOW: 0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def evaluate_enforcement(
    policies: List[EnforcementPolicy],
    context: EnforcementContext,
) -> EnforcementDecision:
    """Evaluate all enforcement policies against a decision context.

    Policies are evaluated in priority order (lowest number first).
    If multiple policies fire, the strictest action wins.

    Returns an immutable EnforcementDecision with computed hash.
    """
    # Sort by priority (lower = higher priority)
    sorted_policies = sorted(policies, key=lambda p: p.priority)

    triggered_policy_ids: List[str] = []
    trigger_reasons: List[str] = []
    blocking_reasons: List[str] = []
    worst_action = EnforcementAction.ALLOW
    worst_severity = 0
    fallback_action: Optional[str] = None
    required_approver: Optional[str] = None
    degradation_factor: Optional[float] = None

    for policy in sorted_policies:
        if not policy.is_active:
            continue

        if not _scope_matches(policy, context):
            continue

        fires, reason = _check_conditions(policy, context)
        if not fires:
            continue

        # Policy fires
        action = policy.enforcement_action
        severity = _ACTION_SEVERITY.get(action, 0)

        triggered_policy_ids.append(policy.policy_id)
        trigger_type = _resolve_trigger_type(policy, context)
        trigger_reasons.append(trigger_type)
        blocking_reasons.append(reason)

        if severity > worst_severity:
            worst_severity = severity
            worst_action = action
            fallback_action = policy.fallback_action
            required_approver = policy.required_approver_role

        # Accumulate degradation (multiply)
        if action == EnforcementAction.DEGRADE_CONFIDENCE and policy.confidence_degradation_factor is not None:
            if degradation_factor is None:
                degradation_factor = policy.confidence_degradation_factor
            else:
                degradation_factor *= policy.confidence_degradation_factor

    # Compute effective confidence
    effective_confidence = context.decision_confidence
    if degradation_factor is not None and worst_action == EnforcementAction.DEGRADE_CONFIDENCE:
        effective_confidence = max(0.0, min(1.0, context.decision_confidence * degradation_factor))

    is_executable = worst_action in EnforcementAction.EXECUTABLE

    decision = EnforcementDecision(
        decision_log_id=context.decision_log_id,
        rule_id=context.rule_id,
        spec_id=context.spec_id,
        enforcement_action=worst_action,
        is_executable=is_executable,
        triggered_policy_ids=triggered_policy_ids,
        trigger_reasons=trigger_reasons,
        blocking_reasons=blocking_reasons,
        original_confidence=context.decision_confidence,
        effective_confidence=effective_confidence,
        fallback_action=fallback_action,
        required_approver=required_approver,
        rule_status=context.rule_status,
        truth_valid=context.truth_valid,
        unresolved_calibrations=context.unresolved_calibrations,
        latest_correctness_score=context.latest_correctness_score,
    )
    decision.compute_hash()
    return decision
