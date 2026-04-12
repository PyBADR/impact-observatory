"""
Rule Spec Validator | مدقق المواصفات
======================================

Validates a RuleSpec for internal consistency, referential
integrity, and policy compliance before it can be approved.

Validation levels:
  STRUCTURAL  — Schema well-formedness (Pydantic handles most of this)
  REFERENTIAL — FKs point to valid datasets, entities, scenarios
  SEMANTIC    — Thresholds make sense, exclusions don't conflict with triggers
  POLICY      — Governance requirements met (audit trail, approval authority)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from src.data_foundation.rule_specs.schema import RuleSpec

__all__ = ["validate_spec", "ValidationResult", "ValidationError"]


@dataclass
class ValidationError:
    level: str      # STRUCTURAL | REFERENTIAL | SEMANTIC | POLICY
    field: str      # Dot-path to the problematic field
    message: str    # Human-readable error
    severity: str   # ERROR | WARN


@dataclass
class ValidationResult:
    spec_id: str
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


# Known dataset IDs from P1
_VALID_DATASETS: Set[str] = {
    "p1_entity_registry", "p1_source_registry", "p1_dataset_registry",
    "p1_macro_indicators", "p1_interest_rate_signals", "p1_oil_energy_signals",
    "p1_fx_signals", "p1_cbk_indicators", "p1_event_signals",
    "p1_banking_sector_profiles", "p1_insurance_sector_profiles",
    "p1_logistics_nodes", "p1_decision_rules", "p1_decision_logs",
}

# Known DataState field namespaces (must match rule_engine.py conventions)
_VALID_NAMESPACES: Set[str] = {
    "oil_energy_signals", "macro_indicators", "interest_rate_signals",
    "fx_signals", "cbk_indicators", "event_signals",
    "banking_sector_profiles", "insurance_sector_profiles",
    "logistics_nodes",
}

# Known simulation scenario IDs (from CLAUDE.md)
_VALID_SCENARIOS: Set[str] = {
    "hormuz_chokepoint_disruption", "hormuz_full_closure",
    "saudi_oil_shock", "uae_banking_crisis", "gcc_cyber_attack",
    "qatar_lng_disruption", "bahrain_sovereign_stress",
    "kuwait_fiscal_shock", "oman_port_closure",
    "red_sea_trade_corridor_instability", "energy_market_volatility_shock",
    "regional_liquidity_stress_event", "critical_port_throughput_disruption",
    "financial_infrastructure_cyber_disruption", "iran_regional_escalation",
}


def validate_spec(
    spec: RuleSpec,
    strict: bool = False,
) -> ValidationResult:
    """Validate a RuleSpec for consistency and completeness.

    Args:
        spec: The rule specification to validate.
        strict: If True, warnings are promoted to errors.

    Returns:
        ValidationResult with errors and warnings.
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []

    def _err(level: str, fld: str, msg: str) -> None:
        errors.append(ValidationError(level=level, field=fld, message=msg, severity="ERROR"))

    def _warn(level: str, fld: str, msg: str) -> None:
        target = errors if strict else warnings
        target.append(ValidationError(level=level, field=fld, message=msg, severity="WARN"))

    # ── STRUCTURAL ──────────────────────────────────────────────────────
    if not spec.spec_id.startswith("SPEC-"):
        _err("STRUCTURAL", "spec_id", "spec_id must start with 'SPEC-'")

    if not spec.spec_id.endswith(f"-v{spec.spec_version.split('.')[0]}"):
        _warn("STRUCTURAL", "spec_id",
              f"spec_id should end with '-v{spec.spec_version.split('.')[0]}' to match version")

    if len(spec.thresholds) != len(spec.trigger_signals):
        _warn("STRUCTURAL", "thresholds",
              f"Threshold count ({len(spec.thresholds)}) != signal count ({len(spec.trigger_signals)}). "
              "Usually 1:1 mapping expected.")

    # ── REFERENTIAL ─────────────────────────────────────────────────────
    for i, sig in enumerate(spec.trigger_signals):
        ns = sig.signal_field.split(".")[0] if "." in sig.signal_field else ""
        if ns and ns not in _VALID_NAMESPACES:
            _warn("REFERENTIAL", f"trigger_signals[{i}].signal_field",
                  f"Namespace '{ns}' not in known DataState namespaces: {_VALID_NAMESPACES}")

        if sig.source_dataset not in _VALID_DATASETS:
            _warn("REFERENTIAL", f"trigger_signals[{i}].source_dataset",
                  f"Dataset '{sig.source_dataset}' not in known P1 datasets")

    for ds_id in spec.source_dataset_ids:
        if ds_id not in _VALID_DATASETS:
            _warn("REFERENTIAL", "source_dataset_ids",
                  f"Dataset '{ds_id}' not in known P1 datasets")

    for scenario_id in spec.applicable_scenarios:
        if scenario_id not in _VALID_SCENARIOS:
            _warn("REFERENTIAL", "applicable_scenarios",
                  f"Scenario '{scenario_id}' not in known scenarios")

    # ── SEMANTIC ────────────────────────────────────────────────────────
    threshold_fields = {t.field for t in spec.thresholds}
    signal_fields = {s.signal_field for s in spec.trigger_signals}
    unmatched = threshold_fields - signal_fields
    if unmatched:
        _warn("SEMANTIC", "thresholds",
              f"Threshold fields {unmatched} have no matching trigger signal")

    for i, excl in enumerate(spec.exclusions):
        if excl.condition_field in threshold_fields:
            if excl.condition_operator in ("eq", "in"):
                _warn("SEMANTIC", f"exclusions[{i}]",
                      f"Exclusion on '{excl.condition_field}' may conflict with threshold condition")

    if spec.decision.escalation_level.value in ("NOMINAL", "LOW") and spec.decision.requires_human_approval:
        _warn("SEMANTIC", "decision.requires_human_approval",
              "Low-risk rules rarely need human approval — consider auto-approve")

    if not spec.transmission_paths:
        _warn("SEMANTIC", "transmission_paths",
              "No transmission paths defined. Impact chain will be incomplete.")

    if not spec.affected_entities:
        _warn("SEMANTIC", "affected_entities",
              "No affected entities defined. Entity-level impact tracking will be empty.")

    # ── POLICY ──────────────────────────────────────────────────────────
    if not spec.audit.authored_by:
        _err("POLICY", "audit.authored_by", "Spec must have an author")

    if spec.status == "ACTIVE" and not spec.audit.approved_by:
        _err("POLICY", "audit.approved_by", "Active spec must have approval")

    if spec.status == "ACTIVE" and not spec.audit.reviewed_by:
        _warn("POLICY", "audit.reviewed_by", "Active spec should have a reviewer")

    if not spec.confidence.next_review_date:
        _warn("POLICY", "confidence.next_review_date",
              "No review date set. Specs should be periodically re-evaluated.")

    if spec.decision.requires_human_approval and not spec.decision.approval_authority:
        _warn("POLICY", "decision.approval_authority",
              "Human approval required but no approval authority specified")

    return ValidationResult(
        spec_id=spec.spec_id,
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
