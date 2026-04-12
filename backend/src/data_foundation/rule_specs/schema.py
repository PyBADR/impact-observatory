"""
Rule Specification Schema | مخطط مواصفات القواعد
===================================================

The RuleSpec is the policy-grade specification for a decision rule.
It captures the full reasoning chain from trigger signal to decision
proposal — everything an analyst needs to understand, a governance
board needs to approve, and an auditor needs to trace.

This schema is SEPARATE from DecisionRule (the execution model).
A RuleSpec compiles to one or more DecisionRules via compiler.py.

Design principles:
  1. A spec is a DOCUMENT, not code. It must be readable by non-engineers.
  2. Every field answers a specific governance question:
       - TriggerSignalSpec  → "What are we watching?"
       - ThresholdSpec       → "When does it matter?"
       - TransmissionSpec    → "How does the shock propagate?"
       - AffectedEntitySpec  → "Who gets hurt?"
       - SectorImpactSpec    → "Which sectors are exposed?"
       - DecisionProposalSpec→ "What should we do?"
       - ConfidenceBasis     → "Why should we trust this?"
       - RationaleTemplate   → "How do we explain it?"
       - Exclusion           → "When should we NOT trigger?"
       - SpecAuditRecord     → "Who wrote/approved this and when?"
  3. Specs are immutable once published. Changes create new versions.
  4. The spec_id encodes family, variant, and version for traceability.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.data_foundation.schemas.enums import (
    DecisionAction,
    EventCategory,
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)

__all__ = [
    "RuleSpec",
    "TriggerSignalSpec",
    "ThresholdSpec",
    "TransmissionSpec",
    "AffectedEntitySpec",
    "SectorImpactSpec",
    "DecisionProposalSpec",
    "ConfidenceBasis",
    "RationaleTemplate",
    "Exclusion",
    "SpecAuditRecord",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Component schemas — each answers one governance question
# ═══════════════════════════════════════════════════════════════════════════════


class TriggerSignalSpec(BaseModel):
    """What are we watching?

    Defines the data signals that this rule monitors.
    Multiple signals can be specified — the rule triggers when
    the combination (AND/OR) of signal conditions is met.
    """

    signal_field: str = Field(
        ...,
        description=(
            "Dot-notation path to the data field being monitored. "
            "Must match a field in the DataState namespace. "
            "Format: {dataset}.{field}"
        ),
        examples=[
            "oil_energy_signals.change_pct",
            "cbk_indicators.CBK_DISCOUNT_RATE",
            "interest_rate_signals.rate_value_bps",
            "logistics_nodes.utilization_pct",
            "macro_indicators.GDP_REAL",
            "banking_sector_profiles.lcr_pct",
        ],
    )
    signal_name: str = Field(
        ...,
        description="Human-readable signal name for reports and dashboards.",
        examples=["Brent Crude Daily Change %", "CBK Discount Rate (bps)"],
    )
    signal_name_ar: Optional[str] = Field(
        default=None,
        description="Arabic signal name.",
    )
    source_dataset: str = Field(
        ...,
        description="P1 dataset this signal originates from.",
        examples=[
            "p1_oil_energy_signals",
            "p1_cbk_indicators",
            "p1_interest_rate_signals",
            "p1_logistics_nodes",
            "p1_macro_indicators",
            "p1_banking_sector_profiles",
        ],
    )
    unit: str = Field(
        ...,
        description="Unit of measurement for the signal value.",
        examples=["percent", "basis_points", "usd_per_barrel", "teu", "ratio"],
    )
    monitoring_frequency: str = Field(
        default="DAILY",
        description="How often this signal should be checked.",
        examples=["REAL_TIME", "HOURLY", "DAILY", "WEEKLY", "MONTHLY"],
    )
    baseline_value: Optional[float] = Field(
        default=None,
        description=(
            "Normal/expected value under stable conditions. "
            "Used to compute deviation magnitude."
        ),
    )
    baseline_source: Optional[str] = Field(
        default=None,
        description="Where the baseline comes from (e.g., '5Y rolling average').",
    )


class ThresholdSpec(BaseModel):
    """When does it matter?

    Defines the condition that must be met for this signal
    to contribute to a rule trigger. Maps directly to a
    RuleCondition in the execution model.
    """

    field: str = Field(
        ...,
        description="Same as TriggerSignalSpec.signal_field — repeated for compiler clarity.",
    )
    operator: str = Field(
        ...,
        description="Comparison operator.",
        examples=["gt", "gte", "lt", "lte", "eq", "neq", "between", "exceeds_threshold"],
    )
    value: Any = Field(
        ...,
        description="Threshold value. Numeric for comparisons, list for 'between'.",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of the threshold value (for documentation).",
    )
    severity_at_threshold: SignalSeverity = Field(
        ...,
        description="What severity level does this threshold represent?",
    )
    historical_frequency: Optional[str] = Field(
        default=None,
        description=(
            "How often this threshold has been breached historically. "
            "Informs false-positive expectation."
        ),
        examples=[
            "~2 times per decade (oil shocks)",
            "Never breached since CBK founding (1968)",
            "3-4 times per year during volatility cycles",
        ],
    )
    calibration_note: Optional[str] = Field(
        default=None,
        description="Why this specific threshold was chosen. Analyst rationale.",
    )


class TransmissionSpec(BaseModel):
    """How does the shock propagate?

    Describes the causal mechanism from the trigger signal
    to downstream effects. Aligns with ImpactChain.TransmissionPath.
    """

    mechanism: str = Field(
        ...,
        description="Propagation mechanism identifier.",
        examples=[
            "SUPPLY_CHAIN_DISRUPTION",
            "CREDIT_CHANNEL",
            "MARKET_CONTAGION",
            "REGULATORY_CASCADE",
            "CROSS_BORDER_SPILLOVER",
            "INSURANCE_LOSS_CASCADE",
            "FISCAL_CHANNEL",
            "LIQUIDITY_SQUEEZE",
        ],
    )
    description: str = Field(
        ...,
        description="Plain-language explanation of the causal chain.",
    )
    description_ar: Optional[str] = Field(
        default=None,
        description="Arabic description.",
    )
    propagation_hops: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Expected number of hops in the propagation graph.",
    )
    attenuation_per_hop: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Signal attenuation per hop [0.0–1.0]. "
            "1.0 = no attenuation, 0.5 = halves each hop."
        ),
    )
    estimated_lag_hours: float = Field(
        default=24.0,
        ge=0.0,
        description="Expected time for the effect to materialize (hours).",
    )
    intermediate_entities: List[str] = Field(
        default_factory=list,
        description="Entity IDs in the transmission path (FK → entity_registry).",
    )
    evidence_basis: Optional[str] = Field(
        default=None,
        description=(
            "Historical or theoretical basis for this transmission path. "
            "Cite specific events, papers, or regulatory guidance."
        ),
    )


class AffectedEntitySpec(BaseModel):
    """Who gets hurt?

    Identifies a specific entity or entity pattern that is
    affected when this rule triggers.
    """

    entity_id: Optional[str] = Field(
        default=None,
        description="Specific entity ID (FK → entity_registry). Null = pattern-based.",
    )
    entity_pattern: Optional[str] = Field(
        default=None,
        description=(
            "Entity selection pattern when specific ID is not known. "
            "The evaluation engine resolves this at runtime."
        ),
        examples=[
            "entity_type:COMMERCIAL_BANK AND country:KW",
            "sector:ENERGY AND country:SA",
            "entity_type:PORT AND chokepoint_dependency:STRAIT_OF_HORMUZ",
            "is_dsib:True AND country:KW",
        ],
    )
    exposure_type: str = Field(
        default="DIRECT",
        description="How this entity is exposed.",
        examples=["DIRECT", "INDIRECT", "SECOND_HOP"],
    )
    impact_description: str = Field(
        ...,
        description="Plain-language description of what happens to this entity.",
    )
    key_metrics_at_risk: List[str] = Field(
        default_factory=list,
        description="Which metrics of this entity are threatened.",
        examples=["npl_ratio_pct", "car_pct", "throughput_teu", "combined_ratio_pct"],
    )


class SectorImpactSpec(BaseModel):
    """Which sectors are exposed?

    Defines sector-level impact when the rule triggers.
    Maps to SECTOR_ALPHA weights in config.py.
    """

    sector: Sector = Field(
        ...,
        description="Sector affected.",
    )
    impact_magnitude: str = Field(
        ...,
        description="Qualitative magnitude.",
        examples=["CRITICAL", "HIGH", "MODERATE", "LOW", "NEGLIGIBLE"],
    )
    impact_channel: str = Field(
        ...,
        description="Through what channel this sector is affected.",
        examples=[
            "Revenue disruption (oil-dependent fiscal)",
            "Cost of funding increase",
            "Supply chain throughput reduction",
            "Claims surge + reserve adequacy",
            "Cross-border credit exposure",
        ],
    )
    estimated_gdp_drag_pct: Optional[float] = Field(
        default=None,
        description="Estimated GDP drag in percentage points (if quantifiable).",
    )


class DecisionProposalSpec(BaseModel):
    """What should we do?

    The prescribed action and its parameters. The spec layer
    carries the full rationale — the execution layer carries
    just the action enum and params dict.
    """

    action: DecisionAction = Field(
        ...,
        description="Primary action to propose.",
    )
    action_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured parameters for the action.",
    )
    escalation_level: RiskLevel = Field(
        ...,
        description="Risk level for escalation routing.",
    )
    requires_human_approval: bool = Field(
        default=True,
        description="Whether a human must approve before execution.",
    )
    approval_authority: Optional[str] = Field(
        default=None,
        description="Who has authority to approve (role or individual).",
        examples=["CRO", "Risk Committee", "Board", "Compliance Officer"],
    )
    time_to_act_hours: Optional[float] = Field(
        default=None,
        description="Recommended window for action (hours). Null = no urgency.",
    )
    fallback_action: Optional[DecisionAction] = Field(
        default=None,
        description="Action to take if primary action is rejected or expires.",
    )
    related_scenario_ids: List[str] = Field(
        default_factory=list,
        description="Simulation scenarios relevant to this action.",
    )


class ConfidenceBasis(BaseModel):
    """Why should we trust this?

    Documents the evidentiary basis for the rule's thresholds,
    transmission paths, and expected outcomes.
    """

    methodology: str = Field(
        ...,
        description="How thresholds and impacts were determined.",
        examples=[
            "Historical back-test against 2014-2016 oil price collapse",
            "Basel III regulatory minimum + CBK prudential buffer",
            "Actuarial loss modeling (Shift Technology methodology)",
            "Expert judgment — GCC risk committee consensus",
        ],
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Source IDs or references used for calibration.",
    )
    back_test_period: Optional[str] = Field(
        default=None,
        description="Period used for historical validation.",
        examples=["2014-01 to 2024-12", "2020-03 (COVID shock)", "2022-02 (Ukraine crisis)"],
    )
    false_positive_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated false positive rate based on back-testing [0.0–1.0].",
    )
    false_negative_rate: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated false negative rate [0.0–1.0].",
    )
    confidence_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Overall confidence in this rule spec [0.0–1.0].",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Known limitations and blind spots.",
    )
    next_review_date: Optional[date] = Field(
        default=None,
        description="When this rule spec should be re-evaluated.",
    )


class RationaleTemplate(BaseModel):
    """How do we explain it?

    Template for generating human-readable decision rationale
    when the rule triggers. Uses {placeholder} substitution
    from the DataState at trigger time.
    """

    summary_en: str = Field(
        ...,
        description=(
            "English rationale template with {placeholders}. "
            "Placeholders are resolved from DataState values at trigger time."
        ),
        examples=[
            "Brent crude dropped {oil_energy_signals.change_pct}% in a single day, "
            "breaching the {threshold}% contingency threshold. "
            "GCC fiscal exposure is elevated due to {macro_indicators.FISCAL_BALANCE_PCT_GDP}% "
            "fiscal-to-GDP ratio.",
        ],
    )
    summary_ar: Optional[str] = Field(
        default=None,
        description="Arabic rationale template.",
    )
    detail_en: Optional[str] = Field(
        default=None,
        description="Extended rationale with full context (for reports/audit).",
    )
    detail_ar: Optional[str] = Field(
        default=None,
        description="Arabic extended rationale.",
    )
    dashboard_label: str = Field(
        ...,
        description="Short label for dashboard display (max 60 chars).",
    )
    dashboard_label_ar: Optional[str] = Field(
        default=None,
    )


class Exclusion(BaseModel):
    """When should we NOT trigger?

    Disqualifiers that prevent the rule from firing even if
    all threshold conditions are met. These are evaluated
    AFTER condition matching and BEFORE proposal generation.
    """

    exclusion_id: str = Field(
        ...,
        description="Unique exclusion identifier within this spec.",
    )
    description: str = Field(
        ...,
        description="Plain-language explanation of why this exclusion exists.",
    )
    condition_field: str = Field(
        ...,
        description="DataState field to check.",
    )
    condition_operator: str = Field(
        ...,
        description="Operator for the disqualifier check.",
        examples=["eq", "gt", "lt", "in", "not_in"],
    )
    condition_value: Any = Field(
        ...,
        description="Value that disqualifies the trigger.",
    )
    reason_code: str = Field(
        ...,
        description="Machine-readable reason for audit trail.",
        examples=[
            "SCHEDULED_MAINTENANCE",
            "OPEC_PLANNED_CUT",
            "REGULATORY_HOLIDAY",
            "DATA_STALE",
            "ALREADY_ESCALATED",
        ],
    )


class SpecAuditRecord(BaseModel):
    """Who wrote/approved this and when?

    Immutable audit metadata for the spec lifecycle.
    """

    authored_by: str = Field(
        ...,
        description="Person or team that authored this spec.",
    )
    authored_at: datetime = Field(
        ...,
        description="When the spec was authored (UTC).",
    )
    reviewed_by: Optional[str] = Field(
        default=None,
        description="Person or committee that reviewed.",
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Person or authority that approved for production.",
    )
    approved_at: Optional[datetime] = Field(
        default=None,
    )
    change_summary: str = Field(
        default="",
        description="What changed from the previous version.",
    )
    supersedes: Optional[str] = Field(
        default=None,
        description="spec_id of the version this replaces.",
    )
    superseded_by: Optional[str] = Field(
        default=None,
        description="spec_id that replaced this version (set when deprecated).",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Root specification model
# ═══════════════════════════════════════════════════════════════════════════════


class RuleSpec(BaseModel):
    """Complete policy-grade rule specification.

    This is the top-level document that an analyst authors, a governance
    board reviews, and an auditor traces. It compiles to one or more
    DecisionRules for the execution engine.

    Lifecycle:
        DRAFT → REVIEW → APPROVED → ACTIVE → SUPERSEDED | RETIRED

    Naming:
        spec_id: SPEC-{FAMILY}-{VARIANT}-v{MAJOR}
        Example: SPEC-OIL-BRENT-DROP-30-v1
    """

    # ── Identity ────────────────────────────────────────────────────────────
    spec_id: str = Field(
        ...,
        description="Unique specification ID. Format: SPEC-{FAMILY}-{VARIANT}-v{MAJOR}",
        examples=["SPEC-OIL-BRENT-DROP-30-v1", "SPEC-RATE-CBK-HIKE-SURPRISE-v1"],
    )
    spec_version: str = Field(
        default="1.0.0",
        description="SemVer version of this specification.",
    )
    family: str = Field(
        ...,
        description="Rule family identifier (lowercase hyphenated).",
        examples=["oil-shock", "rate-shift", "logistics-disruption", "liquidity-stress"],
    )
    variant: str = Field(
        ...,
        description="Specific variant within the family.",
        examples=["brent-drop-30", "cbk-hike-surprise", "hormuz-closure", "kw-lcr-breach"],
    )

    # ── Metadata ────────────────────────────────────────────────────────────
    name: str = Field(..., description="Human-readable spec name.")
    name_ar: Optional[str] = Field(default=None, description="Arabic spec name.")
    description: str = Field(..., description="Full description of what this rule detects and why.")
    description_ar: Optional[str] = Field(default=None)
    status: str = Field(
        default="DRAFT",
        description="Lifecycle status.",
        examples=["DRAFT", "REVIEW", "APPROVED", "ACTIVE", "SUPERSEDED", "RETIRED"],
    )
    effective_date: Optional[date] = Field(
        default=None,
        description="Date this spec becomes active (null = immediately upon approval).",
    )
    expiry_date: Optional[date] = Field(
        default=None,
        description="Date this spec auto-expires (null = no expiry).",
    )

    # ── Trigger signals ─────────────────────────────────────────────────────
    trigger_signals: List[TriggerSignalSpec] = Field(
        ...,
        min_length=1,
        description="Signals this rule monitors. At least one required.",
    )
    trigger_logic: str = Field(
        default="AND",
        description="How multiple trigger thresholds combine.",
        examples=["AND", "OR"],
    )

    # ── Thresholds ──────────────────────────────────────────────────────────
    thresholds: List[ThresholdSpec] = Field(
        ...,
        min_length=1,
        description="Threshold conditions. Each maps to one RuleCondition.",
    )

    # ── Transmission paths ──────────────────────────────────────────────────
    transmission_paths: List[TransmissionSpec] = Field(
        default_factory=list,
        description="How the shock propagates through the economic graph.",
    )

    # ── Affected entities ───────────────────────────────────────────────────
    affected_entities: List[AffectedEntitySpec] = Field(
        default_factory=list,
        description="Entities affected when this rule triggers.",
    )

    # ── Sector impact ───────────────────────────────────────────────────────
    sector_impacts: List[SectorImpactSpec] = Field(
        default_factory=list,
        description="Sector-level impact assessment.",
    )

    # ── Decision proposal ───────────────────────────────────────────────────
    decision: DecisionProposalSpec = Field(
        ...,
        description="The proposed action when this rule triggers.",
    )

    # ── Confidence basis ────────────────────────────────────────────────────
    confidence: ConfidenceBasis = Field(
        ...,
        description="Evidentiary basis for this rule specification.",
    )

    # ── Rationale template ──────────────────────────────────────────────────
    rationale: RationaleTemplate = Field(
        ...,
        description="Template for generating human-readable decision rationale.",
    )

    # ── Exclusions / disqualifiers ──────────────────────────────────────────
    exclusions: List[Exclusion] = Field(
        default_factory=list,
        description="Conditions that prevent the rule from firing.",
    )

    # ── Scope ───────────────────────────────────────────────────────────────
    applicable_countries: List[GCCCountry] = Field(
        default_factory=list,
        description="GCC countries in scope. Empty = all.",
    )
    applicable_sectors: List[Sector] = Field(
        default_factory=list,
        description="Sectors in scope. Empty = all.",
    )
    applicable_scenarios: List[str] = Field(
        default_factory=list,
        description="Simulation scenario IDs this spec is designed for.",
    )
    applicable_event_categories: List[EventCategory] = Field(
        default_factory=list,
        description="Event categories that can trigger this rule.",
    )

    # ── Governance ──────────────────────────────────────────────────────────
    cooldown_minutes: int = Field(
        default=60,
        ge=0,
        description="Minimum time between consecutive triggers.",
    )
    max_concurrent_triggers: int = Field(
        default=1,
        ge=1,
        description="Max number of active (non-resolved) triggers from this spec.",
    )

    # ── Audit ───────────────────────────────────────────────────────────────
    audit: SpecAuditRecord = Field(
        ...,
        description="Authorship, review, and approval audit trail.",
    )

    # ── Tags ────────────────────────────────────────────────────────────────
    tags: List[str] = Field(
        default_factory=list,
        description="Free-form tags for classification and search.",
    )
    source_dataset_ids: List[str] = Field(
        default_factory=list,
        description="P1 dataset IDs this spec depends on.",
    )
