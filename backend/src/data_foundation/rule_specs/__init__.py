"""
Rule Specification System | نظام مواصفات القواعد
=====================================================

Policy-grade decision logic specification layer for Impact Observatory.
Separates WHAT a rule means (specification) from HOW it executes (engine).

Architecture:
    rule_specs/
    ├── schema.py           ← RuleSpec Pydantic schema (the specification contract)
    ├── registry.py         ← In-memory spec registry + loader
    ├── compiler.py         ← RuleSpec → DecisionRule compiler (spec → execution)
    ├── validator.py        ← Spec integrity validation
    └── families/           ← One file per rule family (the actual policy specs)
        ├── __init__.py
        ├── oil_shock.py
        ├── rate_shift.py
        ├── logistics_disruption.py
        └── liquidity_stress.py

Separation principle:
    RuleSpec  = policy document  (analyst writes, governance reviews, auditor reads)
    DecisionRule = execution record (engine evaluates, DB persists, logs trace)

    A RuleSpec compiles to one or more DecisionRules.
    A DecisionRule always traces back to exactly one RuleSpec via spec_id.

Naming convention:
    spec_id:   SPEC-{FAMILY}-{VARIANT}-{VERSION}
               SPEC-OIL-BRENT-DROP-30-v1
               SPEC-RATE-CBK-HIKE-SURPRISE-v2

    rule_id:   RULE-{FAMILY}-{VARIANT}
               RULE-OIL-BRENT-DROP-30
               RULE-RATE-CBK-HIKE-SURPRISE

    family:    Lower-case hyphenated group name
               oil-shock, rate-shift, logistics-disruption, liquidity-stress

Versioning convention:
    spec_version:  SemVer string "MAJOR.MINOR.PATCH"
        MAJOR: Breaking change (new conditions, removed fields, logic change)
        MINOR: Additive change (new exclusion, updated rationale, added entity)
        PATCH: Cosmetic (typo fix, formatting, audit note update)

    rule_version:  Integer (1, 2, 3...) — increments when compiled spec changes

    Immutability: A published spec is immutable. Changes create a new version.
    The previous version is marked superseded_by → new spec_id.
"""

from src.data_foundation.rule_specs.schema import (  # noqa: F401
    RuleSpec,
    TriggerSignalSpec,
    ThresholdSpec,
    TransmissionSpec,
    AffectedEntitySpec,
    SectorImpactSpec,
    DecisionProposalSpec,
    ConfidenceBasis,
    RationaleTemplate,
    Exclusion,
    SpecAuditRecord,
)
