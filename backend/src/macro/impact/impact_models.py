"""Macro Intelligence Layer — Impact Models (Pack 3).

Source-of-truth Pydantic contracts for the impact assessment layer.

Domain types:
  DomainImpact   — per-domain impact record derived from a PropagationHit
  MacroImpact    — aggregate impact assessment for one signal

Design rules:
  - MacroImpact is always backward-compatible with PropagationResult
  - All fields are deterministic: same PropagationResult → same MacroImpact
  - No ML, no LLM, no external state — pure computation
  - audit_hash covers all deterministic fields for integrity tracing
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalSeverity,
)


class DomainImpact(BaseModel):
    """Impact record for a single domain, derived from a PropagationHit.

    Augments PropagationHit with exposure weight and weighted_impact.
    Preserves the full reasoning chain from the propagation layer.
    """
    domain: ImpactDomain
    severity_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Raw severity at this domain (from PropagationHit.severity_at_hit)"
    )
    severity_level: SignalSeverity
    exposure_weight: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Domain-specific GCC exposure weight [0.0, 1.0]. "
            "Reflects intrinsic systemic importance in GCC economy. "
            "Static, deterministic — see DOMAIN_EXPOSURE_WEIGHTS in impact_engine."
        )
    )
    weighted_impact: float = Field(
        ..., ge=0.0, le=1.0,
        description="Composite impact: severity_score × exposure_weight"
    )
    depth: int = Field(
        ge=0,
        description="Propagation depth from the causal entry point"
    )
    path_description: str = Field(
        ...,
        description="Human-readable path from entry to this domain"
    )
    reasoning: str = Field(
        ...,
        description=(
            "Full reasoning chain from PropagationHit.reasoning. "
            "May include [Graph Brain] annotation if graph-enriched."
        )
    )
    is_entry_domain: bool = Field(
        default=False,
        description="True if this domain was a direct causal entry point (depth=0)"
    )
    regions: list[GCCRegion] = Field(
        default_factory=list,
        description="GCC regions affected at this domain"
    )


class MacroImpact(BaseModel):
    """Aggregate impact assessment for a single signal.

    Computed deterministically from PropagationResult.
    Canonical input for the Decision Brain (decision_engine).

    Backward compatibility:
      - signal_id and signal_title always match the source PropagationResult
      - domain_impacts preserves every PropagationHit — no data is dropped
      - audit_hash provides integrity across the impact→decision pipeline

    Field semantics:
      overall_severity     — max severity across all domain hits
      total_exposure_score — mean(severity × exposure_weight) across hits
      confidence           — derived from domain coverage (not signal confidence)
    """
    impact_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    signal_title: str

    # ── Aggregate scores ──────────────────────────────────────────────────────
    overall_severity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Maximum severity score across all domain hits"
    )
    overall_severity_level: SignalSeverity
    total_exposure_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Mean weighted impact: mean(severity × exposure_weight) across all hits. "
            "Represents the aggregate economic exposure considering domain weights."
        )
    )
    confidence: SignalConfidence = Field(
        ...,
        description=(
            "Confidence derived from propagation coverage: "
            "more domains reached → higher confidence the impact is real. "
            "NOT the source signal's confidence level."
        )
    )

    # ── Domain-level breakdown ────────────────────────────────────────────────
    domain_impacts: list[DomainImpact] = Field(
        default_factory=list,
        description="Per-domain impact records (one per PropagationHit)"
    )
    affected_domains: list[ImpactDomain] = Field(
        default_factory=list,
        description="All domains reached by propagation (ordered by severity desc)"
    )
    entry_domains: list[ImpactDomain] = Field(
        default_factory=list,
        description="Direct causal entry domains (depth=0)"
    )

    # ── Structural counts ─────────────────────────────────────────────────────
    total_domains_reached: int = Field(default=0)
    max_depth: int = Field(default=0)

    # ── Explainability ────────────────────────────────────────────────────────
    impact_reasoning: str = Field(
        default="",
        description=(
            "Composed reasoning summary. Includes propagation reasoning from hits "
            "and, where present, [Graph Brain] graph-backed explanation fragments."
        )
    )
    graph_enriched: bool = Field(
        default=False,
        description="True if any domain impact carries [Graph Brain] reasoning"
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    audit_hash: str = Field(default="")

    @model_validator(mode="after")
    def _compute_audit_hash(self) -> "MacroImpact":
        if not self.audit_hash:
            canonical = json.dumps({
                "impact_id": str(self.impact_id),
                "signal_id": str(self.signal_id),
                "overall_severity": self.overall_severity,
                "total_exposure_score": self.total_exposure_score,
                "total_domains_reached": self.total_domains_reached,
                "max_depth": self.max_depth,
                "computed_at": self.computed_at.isoformat(),
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self

    @property
    def critical_domains(self) -> list[DomainImpact]:
        """Domains with weighted_impact >= 0.60 (DEGRADED+ threshold)."""
        return [d for d in self.domain_impacts if d.weighted_impact >= 0.60]

    @property
    def high_severity_domains(self) -> list[DomainImpact]:
        """Domains with severity_score >= 0.65 (HIGH+ threshold)."""
        return [d for d in self.domain_impacts if d.severity_score >= 0.65]
