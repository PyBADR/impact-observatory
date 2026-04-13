"""
Impact Observatory | مرصد الأثر — Phase 1 Simulation Schemas
Pydantic v2 models for the Hormuz macro-financial simulation.

Contract: these schemas define the wire format for POST /api/v1/simulation/run-hormuz.
Frontend TypeScript types MUST mirror these models exactly.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Enums — source of truth for all categorical fields
# ═══════════════════════════════════════════════════════════════════════════════

class GCCCountryCode(str, Enum):
    """ISO 3166-1 alpha-3 codes for GCC member states."""
    KWT = "KWT"
    SAU = "SAU"
    UAE = "UAE"
    QAT = "QAT"
    BHR = "BHR"
    OMN = "OMN"


class SectorCode(str, Enum):
    """Financial and economic sectors tracked in the simulation."""
    OIL_GAS = "oil_gas"
    BANKING = "banking"
    INSURANCE = "insurance"
    FINTECH = "fintech"
    REAL_ESTATE = "real_estate"
    GOVERNMENT = "government"


class RiskLevel(str, Enum):
    """Unified risk classification aligned with URS thresholds."""
    NOMINAL = "NOMINAL"
    LOW = "LOW"
    GUARDED = "GUARDED"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class Urgency(str, Enum):
    """Decision timing classification."""
    IMMEDIATE = "IMMEDIATE"
    WITHIN_24H = "24H"
    WITHIN_72H = "72H"


# ═══════════════════════════════════════════════════════════════════════════════
# Request
# ═══════════════════════════════════════════════════════════════════════════════

class HormuzRunRequest(BaseModel):
    """Input to POST /api/v1/simulation/run-hormuz."""
    severity: float = Field(
        default=0.72,
        ge=0.0,
        le=1.0,
        description="Shock severity — 0.0 (minimal) to 1.0 (total blockage)",
    )
    horizon_hours: int = Field(
        default=168,
        ge=1,
        le=8760,
        description="Projection horizon in hours (default 7 days)",
    )
    transit_reduction_pct: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Fraction of Hormuz oil transit disrupted",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Response — Country Layer
# ═══════════════════════════════════════════════════════════════════════════════

class CountryImpact(BaseModel):
    """Per-country simulation output."""
    country_code: GCCCountryCode
    country_name: str
    loss_usd: float = Field(description="Estimated financial loss in USD")
    dominant_sector: SectorCode = Field(description="Most-affected sector")
    primary_driver: str = Field(description="Root cause of loss in this country")
    transmission_channel: str = Field(description="How stress reached this country")
    risk_level: RiskLevel
    stress_score: float = Field(ge=0.0, le=1.0, description="Composite stress 0–1")


# ═══════════════════════════════════════════════════════════════════════════════
# Response — Sector Layer
# ═══════════════════════════════════════════════════════════════════════════════

class SectorImpact(BaseModel):
    """Per-sector simulation output."""
    sector: SectorCode
    sector_label: str
    stress: float = Field(ge=0.0, le=1.0, description="Sector stress score 0–1")
    primary_driver: str
    secondary_risk: str
    recommended_lever: str
    risk_level: RiskLevel


# ═══════════════════════════════════════════════════════════════════════════════
# Response — Decision Layer
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionAction(BaseModel):
    """Single actionable decision recommendation."""
    action: str
    owner: str
    timing: Urgency
    value_avoided_usd: float = Field(description="Estimated loss averted if acted upon")
    downside_risk: str = Field(description="Consequence of inaction")


# ═══════════════════════════════════════════════════════════════════════════════
# Response — Explainability Layer
# ═══════════════════════════════════════════════════════════════════════════════

class Explainability(BaseModel):
    """Human-readable causal explanations for the simulation output."""
    why_total_loss: str
    why_country: dict[str, str] = Field(
        description="country_code → why this country is impacted"
    )
    why_sector: dict[str, str] = Field(
        description="sector_code → why this sector is stressed"
    )
    why_act_now: str


# ═══════════════════════════════════════════════════════════════════════════════
# Response — Top-level envelope
# ═══════════════════════════════════════════════════════════════════════════════

class PropagationEdge(BaseModel):
    """Single edge in the stress propagation graph."""
    source: str
    target: str
    weight: float = Field(ge=0.0, le=1.0)
    channel: str


class HormuzRunResult(BaseModel):
    """Complete response from POST /api/v1/simulation/run-hormuz."""
    scenario_id: str = "hormuz_chokepoint_disruption"
    model_version: str = "3.0.0-phase1"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: float
    horizon_hours: int
    transit_reduction_pct: float

    # Aggregate
    total_loss_usd: float
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)

    # Layers
    countries: list[CountryImpact]
    sectors: list[SectorImpact]
    propagation_edges: list[PropagationEdge]
    decisions: list[DecisionAction]
    explainability: Explainability

    # Audit
    sha256_digest: Optional[str] = Field(
        default=None, description="SHA-256 of the serialized result for audit trail"
    )
