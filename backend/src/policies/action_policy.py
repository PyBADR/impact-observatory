"""
Action Policy — filters and scores candidate actions against scenario context.

Replaces the inline SCENARIO_ACTION_MATRIX filtering in decision_layer.py
with a single policy evaluation that:
  1. Checks action eligibility by scenario type
  2. Applies urgency escalation rules based on breach timing
  3. Returns structured allow/deny with audit reason

Pure function. No side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import SCENARIO_ACTION_MATRIX
from src.policies.scenario_policy import PolicyContext


@dataclass(frozen=True, slots=True)
class ActionPolicyResult:
    """
    Per-action policy evaluation result.

    allowed:        Whether this action should be included in the candidate set.
    reason:         Why it was allowed or denied (audit trail).
    urgency_boost:  Additional urgency modifier from policy rules (0.0 - 0.3).
    warnings:       Non-blocking advisory messages.
    """

    allowed: bool
    reason: str
    urgency_boost: float = 0.0
    warnings: list[str] = field(default_factory=list)


def evaluate_action_policy(
    context: PolicyContext,
    action_index: int,
    base_urgency: float = 0.0,
    time_to_act_hours: float = 24.0,
) -> ActionPolicyResult:
    """
    Evaluate whether a specific action template is allowed for the given context.

    Rules:
      R1. If scenario_type is known AND action_index is in the matrix,
          the action is only allowed if scenario_type is in the allowed set.
      R2. If scenario_type is unknown (empty), allow all actions (no filtering).
      R3. If action_index is NOT in the matrix, allow it (unconstrained action).
      R4. Urgency escalation: if time_to_first_breach < 12h AND action time_to_act ≤ 6h,
          boost urgency by +0.15 (IMMEDIATE actions get priority in imminent breaches).
      R5. If breach is imminent (<6h) and base_urgency ≥ 0.7, add +0.10 more.

    Args:
        context:           PolicyContext for the current run.
        action_index:      Index into _ACTION_TEMPLATES (0-15).
        base_urgency:      The action's base urgency from the template.
        time_to_act_hours: Hours until action must be taken.

    Returns:
        ActionPolicyResult with allow/deny and urgency modifiers.
    """
    warnings: list[str] = []
    urgency_boost = 0.0
    scenario_type = context.scenario_type

    # ── R1/R2/R3: Scenario-type filtering ───────────────────────────────────
    if scenario_type and action_index in SCENARIO_ACTION_MATRIX:
        allowed_types = SCENARIO_ACTION_MATRIX[action_index]
        if scenario_type not in allowed_types:
            return ActionPolicyResult(
                allowed=False,
                reason=(
                    f"Action template {action_index} not allowed for "
                    f"scenario type '{scenario_type}' "
                    f"(allowed: {sorted(allowed_types)})"
                ),
            )

    # ── R4: Urgency escalation for imminent breach ──────────────────────────
    breach_hours = context.time_to_first_breach_hours
    if breach_hours is not None and breach_hours < 12.0 and time_to_act_hours <= 6.0:
        urgency_boost += 0.15
        warnings.append(
            f"Urgency +0.15: breach imminent ({breach_hours:.1f}h) "
            f"and action is IMMEDIATE (≤6h)"
        )

    # ── R5: Critical escalation ─────────────────────────────────────────────
    if (
        breach_hours is not None
        and breach_hours < 6.0
        and base_urgency >= 0.7
    ):
        urgency_boost += 0.10
        warnings.append(
            f"Urgency +0.10: breach critical ({breach_hours:.1f}h) "
            f"and base urgency high ({base_urgency:.2f})"
        )

    # ── Build reason ────────────────────────────────────────────────────────
    if scenario_type:
        reason = (
            f"Action {action_index} allowed for scenario type '{scenario_type}'"
        )
    else:
        reason = (
            f"Action {action_index} allowed (no scenario type filtering applied)"
        )

    return ActionPolicyResult(
        allowed=True,
        reason=reason,
        urgency_boost=round(urgency_boost, 4),
        warnings=warnings,
    )
