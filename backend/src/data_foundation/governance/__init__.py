"""Governance & Calibration Layer — package root.

Exports all schemas, engines, and key functions.
"""

from src.data_foundation.governance.schemas import (
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationPolicy,
    TruthValidationResult,
    CalibrationTrigger,
    CalibrationEvent,
    GovernanceAuditEntry,
)
from src.data_foundation.governance.rule_lifecycle import (
    TRANSITION_MAP,
    TERMINAL_STATES,
    validate_transition,
    execute_transition,
    build_event_chain,
)
from src.data_foundation.governance.truth_validation import (
    check_freshness,
    check_completeness,
    check_corroboration,
    check_field_rules,
    validate_record,
    resolve_source_priority,
)
from src.data_foundation.governance.calibration_triggers import (
    extract_metric,
    evaluate_threshold,
    evaluate_trigger,
    evaluate_triggers_batch,
)
from src.data_foundation.governance.governance_audit import (
    compute_hash,
    create_audit_entry,
    verify_chain,
)

__all__ = [
    # Schemas
    "GovernancePolicy",
    "RuleLifecycleEvent",
    "TruthValidationPolicy",
    "TruthValidationResult",
    "CalibrationTrigger",
    "CalibrationEvent",
    "GovernanceAuditEntry",
    # Lifecycle
    "TRANSITION_MAP",
    "TERMINAL_STATES",
    "validate_transition",
    "execute_transition",
    "build_event_chain",
    # Truth validation
    "check_freshness",
    "check_completeness",
    "check_corroboration",
    "check_field_rules",
    "validate_record",
    "resolve_source_priority",
    # Calibration
    "extract_metric",
    "evaluate_threshold",
    "evaluate_trigger",
    "evaluate_triggers_batch",
    # Audit
    "compute_hash",
    "create_audit_entry",
    "verify_chain",
]
