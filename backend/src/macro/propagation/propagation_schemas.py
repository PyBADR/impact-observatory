"""Macro Intelligence Layer — Propagation Domain Models.

Source-of-truth Pydantic contracts for the propagation sublayer.

Domain types:
  PropagationNode   — a node in the propagation graph (one per domain)
  PropagationEdge   — a traversed edge in the propagation path
  PropagationHit    — impact record for a single reached domain
  PropagationPath   — full ordered path from entry to a terminal node
  PropagationResult — complete propagation output for one signal
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalSeverity,
)
from src.macro.macro_validators import severity_from_score


class NodeState(str, Enum):
    """Operational state of a propagation node."""
    NOMINAL = "nominal"       # no significant stress
    STRESSED = "stressed"     # under stress but functioning
    DEGRADED = "degraded"     # partially impaired operations
    CRITICAL = "critical"     # severe impairment
    FAILED = "failed"         # operational failure


def _state_from_severity(severity: float) -> NodeState:
    """Map severity score to node operational state."""
    if severity < 0.20:
        return NodeState.NOMINAL
    elif severity < 0.45:
        return NodeState.STRESSED
    elif severity < 0.65:
        return NodeState.DEGRADED
    elif severity < 0.80:
        return NodeState.CRITICAL
    else:
        return NodeState.FAILED


class PropagationNode(BaseModel):
    """A domain node in the propagation graph.

    Each node represents one ImpactDomain at a specific propagation depth.
    """
    node_id: str = Field(
        ..., description="Stable node key (e.g. 'oil_gas' or 'banking@depth_2')"
    )
    domain: ImpactDomain
    depth: int = Field(
        ..., ge=0,
        description="Hop distance from the causal entry point. 0 = entry domain."
    )
    severity_at_node: float = Field(
        ..., ge=0.0, le=1.0,
        description="Severity after decay at this depth"
    )
    severity_level: SignalSeverity = Field(
        ..., description="Discrete severity level at this node"
    )
    state: NodeState = Field(
        ..., description="Operational state of this domain node"
    )
    is_entry: bool = Field(
        default=False,
        description="True if this is a direct causal entry domain (depth=0)"
    )
    regions: list[GCCRegion] = Field(
        default_factory=list,
        description="Regions affected at this node"
    )

    @model_validator(mode="after")
    def sync_derived_fields(self) -> "PropagationNode":
        """Ensure severity_level and state match severity_at_node."""
        expected_level = severity_from_score(self.severity_at_node)
        if self.severity_level != expected_level:
            self.severity_level = expected_level
        expected_state = _state_from_severity(self.severity_at_node)
        if self.state != expected_state:
            self.state = expected_state
        return self


class PropagationEdge(BaseModel):
    """A traversed edge in the propagation graph.

    Records the causal channel that was activated and the severity
    transmitted through it.
    """
    edge_id: str = Field(
        ..., description="Stable edge key (e.g. 'oil_gas→banking')"
    )
    from_domain: ImpactDomain
    to_domain: ImpactDomain
    channel_id: str = Field(
        ..., description="Reference to the CausalChannel that defines this edge"
    )
    transmission_label: str = Field(
        ..., description="Human-readable mechanism label"
    )
    weight_applied: float = Field(
        ..., ge=0.0, le=1.0,
        description="Effective transmission weight used"
    )
    decay_applied: float = Field(
        ..., ge=0.0, le=1.0,
        description="Decay factor applied at this hop"
    )
    lag_hours: int = Field(
        default=0, ge=0,
        description="Estimated propagation delay in hours from the causal channel"
    )
    severity_in: float = Field(
        ..., ge=0.0, le=1.0,
        description="Severity entering this edge"
    )
    severity_out: float = Field(
        ..., ge=0.0, le=1.0,
        description="Severity after weight × decay"
    )


class PropagationHit(BaseModel):
    """Impact record for a single domain reached by propagation.

    This is the per-node output that feeds the downstream impact assessment layer.
    """
    hit_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    domain: ImpactDomain
    depth: int = Field(ge=0)
    severity_at_hit: float = Field(ge=0.0, le=1.0)
    severity_level: SignalSeverity
    regions: list[GCCRegion]
    path_description: str = Field(
        ..., description="Human-readable path from entry to this domain"
    )
    reasoning: str = Field(
        ..., description="Explainability: why this domain was hit and how"
    )


class PropagationPath(BaseModel):
    """An ordered path from a causal entry domain to a terminal domain.

    Captures every node and edge traversed, plus cumulative decay.
    """
    path_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    nodes: list[PropagationNode] = Field(
        ..., min_length=1,
        description="Ordered list of nodes traversed (entry → terminal)"
    )
    edges: list[PropagationEdge] = Field(
        default_factory=list,
        description="Ordered list of edges traversed (len = len(nodes) - 1)"
    )
    entry_domain: ImpactDomain
    terminal_domain: ImpactDomain
    total_hops: int = Field(ge=0)
    entry_severity: float = Field(ge=0.0, le=1.0)
    terminal_severity: float = Field(ge=0.0, le=1.0)
    cumulative_decay: float = Field(
        ge=0.0, le=1.0,
        description="Total severity retained: terminal_severity / entry_severity"
    )
    path_description: str = Field(
        ..., description="Human-readable path: 'oil_gas → banking → capital_markets'"
    )


class PropagationResult(BaseModel):
    """Complete propagation output for one signal.

    This is the top-level result that the impact assessment layer consumes.
    Includes all paths, all hits, and full explainability.
    """
    result_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    signal_title: str
    entry_domains: list[ImpactDomain]
    paths: list[PropagationPath] = Field(default_factory=list)
    hits: list[PropagationHit] = Field(default_factory=list)
    total_domains_reached: int = Field(default=0)
    max_depth: int = Field(default=0)
    propagated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    audit_hash: str = Field(default="")

    @model_validator(mode="after")
    def compute_audit_hash(self) -> "PropagationResult":
        if not self.audit_hash:
            canonical = json.dumps({
                "result_id": str(self.result_id),
                "signal_id": str(self.signal_id),
                "total_domains_reached": self.total_domains_reached,
                "max_depth": self.max_depth,
                "propagated_at": self.propagated_at.isoformat(),
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self


# ── API Response Wrappers ────────────────────────────────────────────────────

class PropagationResponse(BaseModel):
    """API response for a propagation request."""
    result: PropagationResult
    message: str = "Propagation complete"


class PropagationSummary(BaseModel):
    """Lightweight summary for list endpoints."""
    result_id: UUID
    signal_id: UUID
    signal_title: str
    total_domains_reached: int
    max_depth: int
    entry_domains: list[ImpactDomain]
    propagated_at: datetime
