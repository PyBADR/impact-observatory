"""
Rule Spec Compiler | مترجم المواصفات
======================================

Compiles a RuleSpec (policy document) into one or more
DecisionRules (execution records) for the rule engine.

The compiler is a pure function: RuleSpec → List[DecisionRule].
No side effects, no DB access, no state.

Invariants:
  - Every compiled DecisionRule.rule_id is derivable from the spec_id
  - Every compiled DecisionRule.description contains the spec_id for traceability
  - Exclusions are compiled as negated conditions appended to the rule
  - The spec's rationale template is stored in action_params for runtime resolution
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from src.data_foundation.schemas.decision_rules import DecisionRule, RuleCondition
from src.data_foundation.rule_specs.schema import RuleSpec, Exclusion


__all__ = ["compile_spec", "compile_exclusion"]


def _spec_id_to_rule_id(spec_id: str) -> str:
    """Derive rule_id from spec_id.

    SPEC-OIL-BRENT-DROP-30-v1 → RULE-OIL-BRENT-DROP-30
    """
    parts = spec_id.replace("SPEC-", "RULE-", 1)
    # Strip version suffix: -v1, -v2, etc.
    if parts.rfind("-v") > 0:
        parts = parts[:parts.rfind("-v")]
    return parts


def _negate_operator(op: str) -> str:
    """Negate an operator for exclusion compilation."""
    negations = {
        "eq": "neq", "neq": "eq",
        "gt": "lte", "lte": "gt",
        "gte": "lt", "lt": "gte",
        "in": "not_in", "not_in": "in",
    }
    return negations.get(op, op)


def compile_exclusion(exclusion: Exclusion) -> RuleCondition:
    """Compile an Exclusion into a negated RuleCondition.

    The exclusion says "do NOT trigger when X". We negate it
    into "ONLY trigger when NOT X" and add it to the AND chain.
    """
    return RuleCondition(
        field=exclusion.condition_field,
        operator=_negate_operator(exclusion.condition_operator),
        threshold=exclusion.condition_value,
        unit=None,
    )


def compile_spec(spec: RuleSpec) -> List[DecisionRule]:
    """Compile a RuleSpec into executable DecisionRules.

    Returns a list because a single spec could theoretically
    produce multiple rules (e.g., tiered thresholds). In practice,
    most specs produce exactly one rule.

    The compiled rule carries:
      - Threshold conditions from spec.thresholds
      - Negated exclusion conditions appended to the condition list
      - The spec_id in description for audit traceability
      - The rationale template in action_params for runtime resolution
      - All scope fields (countries, sectors, scenarios) passed through
    """
    rule_id = _spec_id_to_rule_id(spec.spec_id)

    # 1. Compile threshold conditions
    conditions: List[RuleCondition] = []
    for threshold in spec.thresholds:
        conditions.append(RuleCondition(
            field=threshold.field,
            operator=threshold.operator,
            threshold=threshold.value,
            unit=threshold.unit,
        ))

    # 2. Compile exclusions as negated conditions
    for exclusion in spec.exclusions:
        conditions.append(compile_exclusion(exclusion))

    # 3. Build action_params with spec metadata for runtime resolution
    action_params = dict(spec.decision.action_params) if spec.decision.action_params else {}
    action_params["_spec_id"] = spec.spec_id
    action_params["_spec_version"] = spec.spec_version
    action_params["_rationale_template"] = spec.rationale.summary_en
    action_params["_dashboard_label"] = spec.rationale.dashboard_label
    if spec.decision.approval_authority:
        action_params["_approval_authority"] = spec.decision.approval_authority
    if spec.decision.time_to_act_hours is not None:
        action_params["_time_to_act_hours"] = spec.decision.time_to_act_hours
    if spec.decision.fallback_action:
        action_params["_fallback_action"] = spec.decision.fallback_action.value
    if spec.decision.related_scenario_ids:
        action_params["_related_scenario_ids"] = spec.decision.related_scenario_ids

    # 4. Build the description with spec traceability
    description = (
        f"[{spec.spec_id}] {spec.description} "
        f"| Family: {spec.family} | Variant: {spec.variant}"
    )

    # 5. Assemble the DecisionRule
    rule = DecisionRule(
        rule_id=rule_id,
        rule_name=spec.name,
        rule_name_ar=spec.name_ar,
        description=description,
        version=int(spec.spec_version.split(".")[0]),  # MAJOR version
        is_active=(spec.status == "ACTIVE"),
        conditions=conditions,
        condition_logic=spec.trigger_logic,
        action=spec.decision.action,
        action_params=action_params,
        escalation_level=spec.decision.escalation_level,
        applicable_countries=list(spec.applicable_countries),
        applicable_sectors=list(spec.applicable_sectors),
        applicable_scenarios=list(spec.applicable_scenarios),
        requires_human_approval=spec.decision.requires_human_approval,
        cooldown_minutes=spec.cooldown_minutes,
        expiry_date=(
            datetime.combine(spec.expiry_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            if spec.expiry_date else None
        ),
        source_dataset_ids=list(spec.source_dataset_ids),
        tags=list(spec.tags),
        created_by=spec.audit.authored_by,
        approved_by=spec.audit.approved_by,
        audit_notes=spec.audit.change_summary or f"Compiled from {spec.spec_id}",
    )

    return [rule]
