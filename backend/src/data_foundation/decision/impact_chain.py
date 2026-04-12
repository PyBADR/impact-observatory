"""
P1 Decision Layer — Impact Chain Model
=========================================

Defines the Signal → Transmission → Exposure → Decision → Outcome chain
as typed Pydantic models. This is the data contract for the entire
decision intelligence flow.

Architecture:
  1. SIGNAL:       An event or indicator change detected by the ingestion layer
  2. TRANSMISSION: How the signal propagates through the GCC economic graph
  3. EXPOSURE:     Which entities/sectors are exposed and by how much
  4. DECISION:     What action the decision rules engine prescribes
  5. OUTCOME:      What happened after the decision was executed (post-hoc)

Each stage produces a typed record that chains to the next via foreign keys.
The full chain is auditable: every decision can be traced back to the
originating signal through deterministic linkage.

KG Mapping:
  (:Signal)-[:TRANSMITS_VIA]->(:Transmission)-[:EXPOSES]->(:Exposure)
    -[:TRIGGERS]->(:Decision)-[:PRODUCES]->(:Outcome)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.data_foundation.schemas.enums import (
    DecisionAction,
    DecisionStatus,
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)

__all__ = [
    "SignalDetection",
    "TransmissionPath",
    "ExposureAssessment",
    "DecisionProposal",
    "OutcomeRecord",
    "ImpactChain",
]


class SignalDetection(BaseModel):
    """Stage 1: A signal detected by the ingestion layer.

    Links to: event_signals, macro_indicators, interest_rate_signals,
    oil_energy_signals, fx_signals, cbk_indicators.
    """
    signal_ref_id: str = Field(
        ...,
        description="FK to the originating signal record (event_id, indicator_id, signal_id).",
    )
    signal_dataset: str = Field(
        ...,
        description="Dataset the signal came from.",
        examples=["p1_event_signals", "p1_oil_energy_signals", "p1_interest_rate_signals"],
    )
    signal_type: str = Field(
        ...,
        description="Classification of the signal.",
        examples=["GEOPOLITICAL_EVENT", "OIL_PRICE_SHOCK", "RATE_CHANGE", "FX_PEG_DEVIATION"],
    )
    severity: SignalSeverity = Field(...)
    severity_score: float = Field(..., ge=0.0, le=1.0)
    detected_at: datetime = Field(...)
    countries_affected: List[GCCCountry] = Field(default_factory=list)
    sectors_affected: List[Sector] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)


class TransmissionPath(BaseModel):
    """Stage 2: How the signal propagates through the economic graph.

    Describes the causal chain from the originating signal to downstream
    effects. Aligned with the simulation engine's propagation model
    (X_(t+1) = beta*P*X_t + (1-beta)*X_t + S_t from config.py).
    """
    transmission_id: str = Field(...)
    signal_ref_id: str = Field(..., description="FK to SignalDetection.")
    mechanism: str = Field(
        ...,
        description="How the signal propagates.",
        examples=[
            "SUPPLY_CHAIN_DISRUPTION",    # Port closure → shipping delay → inventory shortfall
            "CREDIT_CHANNEL",             # Rate change → cost of funding → lending contraction
            "MARKET_CONTAGION",           # Asset price shock → portfolio losses → liquidity squeeze
            "REGULATORY_CASCADE",         # New regulation → compliance cost → operational impact
            "CROSS_BORDER_SPILLOVER",     # Country shock → trade partner exposure → GDP drag
            "INSURANCE_LOSS_CASCADE",     # Event → claims spike → reserve depletion → reinsurance
        ],
    )
    source_entity_ids: List[str] = Field(
        default_factory=list,
        description="Originating entities (FK to entity_registry).",
    )
    intermediate_entity_ids: List[str] = Field(
        default_factory=list,
        description="Entities in the transmission path.",
    )
    affected_entity_ids: List[str] = Field(
        default_factory=list,
        description="Terminal entities affected.",
    )
    propagation_hops: int = Field(
        default=1,
        ge=1,
        description="Number of hops in the propagation graph.",
    )
    attenuation_factor: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Signal attenuation per hop (from config.py EXPOSURE_V_* constants).",
    )
    estimated_lag_hours: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated time for the effect to materialize.",
    )


class ExposureAssessment(BaseModel):
    """Stage 3: Quantified exposure for a specific entity.

    One ExposureAssessment per affected entity. Aligned with the
    simulation engine's sector exposure model:
    Exposure_j = alpha_j * Es * V_j * C_j
    """
    exposure_id: str = Field(...)
    transmission_id: str = Field(..., description="FK to TransmissionPath.")
    entity_id: str = Field(..., description="FK to entity_registry.")
    entity_name: str = Field(...)
    country: GCCCountry = Field(...)
    sector: Sector = Field(...)
    exposure_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized exposure [0.0–1.0].",
    )
    exposure_type: str = Field(
        default="DIRECT",
        description="DIRECT, INDIRECT, SECOND_HOP — maps to V_j constants in config.py.",
        examples=["DIRECT", "INDIRECT", "SECOND_HOP"],
    )
    estimated_financial_impact: Optional[float] = Field(
        default=None,
        description="Estimated financial impact in local currency (millions).",
    )
    risk_level: RiskLevel = Field(...)
    key_metrics_at_risk: List[str] = Field(
        default_factory=list,
        description="Which metrics are at risk for this entity.",
        examples=["npl_ratio_pct", "car_pct", "combined_ratio_pct", "throughput_teu"],
    )


class DecisionProposal(BaseModel):
    """Stage 4: A decision proposed by the rule engine.

    Maps to decision_rules (the trigger) and decision_logs (the record).
    """
    proposal_id: str = Field(...)
    exposure_ids: List[str] = Field(
        ...,
        description="FK to ExposureAssessments that triggered this decision.",
    )
    rule_id: str = Field(..., description="FK to decision_rules.")
    rule_version: int = Field(..., ge=1)
    action: DecisionAction = Field(...)
    action_params: Optional[Dict[str, Any]] = Field(default=None)
    risk_level: RiskLevel = Field(...)
    requires_approval: bool = Field(default=True)
    status: DecisionStatus = Field(default=DecisionStatus.PROPOSED)
    proposed_at: datetime = Field(...)
    rationale: str = Field(
        ...,
        description="Human-readable explanation of why this decision was proposed.",
    )
    affected_entity_ids: List[str] = Field(default_factory=list)
    affected_countries: List[GCCCountry] = Field(default_factory=list)


class OutcomeRecord(BaseModel):
    """Stage 5: Post-hoc outcome tracking.

    Records what actually happened after a decision was executed.
    Used for decision quality analysis and model calibration.
    """
    outcome_id: str = Field(...)
    proposal_id: str = Field(..., description="FK to DecisionProposal.")
    decision_log_id: str = Field(..., description="FK to decision_logs.")
    actual_impact: Optional[float] = Field(
        default=None,
        description="Actual financial impact observed (millions).",
    )
    predicted_impact: Optional[float] = Field(
        default=None,
        description="Predicted impact at decision time.",
    )
    accuracy_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How accurate was the prediction [0.0–1.0].",
    )
    was_correct_action: Optional[bool] = Field(
        default=None,
        description="Post-hoc assessment: was the prescribed action correct?",
    )
    review_notes: Optional[str] = Field(default=None)
    reviewed_at: Optional[datetime] = Field(default=None)


class ImpactChain(BaseModel):
    """Complete chain: Signal → Transmission → Exposure → Decision → Outcome.

    Used for full-chain auditing and explainability.
    """
    chain_id: str = Field(...)
    signal: SignalDetection = Field(...)
    transmissions: List[TransmissionPath] = Field(default_factory=list)
    exposures: List[ExposureAssessment] = Field(default_factory=list)
    decisions: List[DecisionProposal] = Field(default_factory=list)
    outcomes: List[OutcomeRecord] = Field(default_factory=list)
    created_at: datetime = Field(...)
    chain_status: str = Field(
        default="ACTIVE",
        examples=["ACTIVE", "RESOLVED", "SUPERSEDED", "FALSE_ALARM"],
    )
