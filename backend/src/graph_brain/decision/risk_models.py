"""Risk Decision Models — Typed contracts for the Decision Layer.

Aligned with:
  - URS 6-tier risk thresholds from src/config.py (NOMINAL → SEVERE)
  - GraphEntityType / GraphConfidence from graph_brain/types.py
  - SECTOR_ALPHA coefficients from src/config.py
  - Cross-sector dependency map from src/risk_models.py

Architecture Layer: Models (Layer 3)
Owner: Decision Layer
Consumers: RiskEngine, RiskService, Risk API
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Risk Level — aligned with URS thresholds from config.py
# ═══════════════════════════════════════════════════════════════════════════════

class RiskLevel(str, Enum):
    """6-tier risk classification matching the simulation engine URS thresholds.

    Thresholds from config.py:
      NOMINAL:  0.00 – 0.20
      LOW:      0.20 – 0.35
      GUARDED:  0.35 – 0.50
      ELEVATED: 0.50 – 0.65
      HIGH:     0.65 – 0.80
      SEVERE:   0.80 – 1.00
    """
    NOMINAL = "NOMINAL"
    LOW = "LOW"
    GUARDED = "GUARDED"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


# ═══════════════════════════════════════════════════════════════════════════════
# Risk Factor — a single contributor to an entity's risk score
# ═══════════════════════════════════════════════════════════════════════════════

class RiskFactorSource(str, Enum):
    """Where the risk factor originated."""
    GRAPH_DIRECT = "graph_direct"         # Direct edge from graph
    GRAPH_PROPAGATED = "graph_propagated" # Multi-hop propagation
    SIGNAL_ACTIVE = "signal_active"       # Active signal attached to entity
    SECTOR_CONTAGION = "sector_contagion" # Cross-sector contagion channel
    SCENARIO_EXPOSURE = "scenario_exposure"  # Scenario-driven exposure


class RiskFactor(BaseModel):
    """A single contributor to an entity's composite risk score.

    Each factor carries a raw weight (from config.py SECTOR_ALPHA or
    graph edge weight), a contribution (weight × confidence × decay),
    and provenance tracking for audit.
    """
    name: str = Field(..., min_length=1, description="Factor identifier")
    description: str = Field("", description="Human-readable explanation")
    source: RiskFactorSource = RiskFactorSource.GRAPH_DIRECT
    source_node_id: str = Field("", description="GraphNode that generated this factor")
    weight: float = Field(0.0, ge=0.0, le=1.0, description="Raw weight from config/graph")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence in this factor")
    temporal_decay: float = Field(1.0, ge=0.0, le=1.0, description="Decay applied (1.0 = no decay)")
    contribution: float = Field(0.0, ge=0.0, description="Final contribution = weight × confidence × decay")
    hop_distance: int = Field(0, ge=0, description="Graph hops from target entity")


# ═══════════════════════════════════════════════════════════════════════════════
# Propagation Path — how risk reaches an entity through the graph
# ═══════════════════════════════════════════════════════════════════════════════

class PropagationPath(BaseModel):
    """A risk propagation path through the knowledge graph."""
    path_description: str = Field("", description="Node chain: A → B → C")
    path_weight: float = Field(0.0, ge=0.0, le=1.0, description="Product of edge weights")
    hops: int = Field(0, ge=0)
    source_entity: str = ""
    target_entity: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Risk Result — full output of risk assessment for a single entity
# ═══════════════════════════════════════════════════════════════════════════════

class RiskResult(BaseModel):
    """Complete risk assessment for a single entity.

    Contains the composite risk score, risk level classification,
    all contributing factors, propagation paths, and recommendations.
    """
    entity_id: str = Field("", description="GraphNode node_id")
    entity_label: str = Field("", description="Human-readable entity name")
    entity_type: str = Field("", description="GraphEntityType value")

    # Core risk metrics
    risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Composite risk score [0.0, 1.0]")
    risk_level: RiskLevel = RiskLevel.NOMINAL
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Assessment confidence")

    # Decomposition
    drivers: list[RiskFactor] = Field(default_factory=list)
    propagation_paths: list[PropagationPath] = Field(default_factory=list)
    exposed_sectors: list[str] = Field(default_factory=list)
    active_scenarios: list[str] = Field(default_factory=list)

    # Recommendations
    recommendations: list[str] = Field(default_factory=list)

    # Metadata
    graph_stats: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    audit_hash: str = ""
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_audit_hash(self) -> str:
        canonical = json.dumps({
            "entity_id": self.entity_id,
            "risk_score": round(self.risk_score, 6),
            "risk_level": self.risk_level.value,
            "driver_count": len(self.drivers),
            "assessed_at": self.assessed_at.isoformat(),
        }, sort_keys=True).encode()
        self.audit_hash = hashlib.sha256(canonical).hexdigest()
        return self.audit_hash


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-Entity Risk Assessment — portfolio/regional view
# ═══════════════════════════════════════════════════════════════════════════════

class PortfolioRiskResult(BaseModel):
    """Aggregated risk assessment across multiple entities."""
    entity_results: list[RiskResult] = Field(default_factory=list)
    portfolio_risk_score: float = Field(0.0, ge=0.0, le=1.0)
    portfolio_risk_level: RiskLevel = RiskLevel.NOMINAL
    top_risks: list[RiskFactor] = Field(default_factory=list)
    systemic_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Interconnection-driven risk")
    contagion_channels: list[str] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    audit_hash: str = ""

    def compute_audit_hash(self) -> str:
        canonical = json.dumps({
            "entity_count": len(self.entity_results),
            "portfolio_score": round(self.portfolio_risk_score, 6),
            "systemic_score": round(self.systemic_risk_score, 6),
        }, sort_keys=True).encode()
        self.audit_hash = hashlib.sha256(canonical).hexdigest()
        return self.audit_hash
