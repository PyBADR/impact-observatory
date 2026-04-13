"""
Impact Observatory | مرصد الأثر — Phase 3 Decision Analysis API Route

POST /api/v1/decisions/analyze/{slug}  → Full decision analysis with ownership + escalation
GET  /api/v1/decisions/ownership       → List all decision ownership mappings
GET  /api/v1/decisions/escalation-rules → List escalation threshold rules

Decision analysis runs the Phase 3 pipeline and returns decision-focused output:
  - Each decision mapped to institutional owner with deadline
  - Escalation alerts sorted by urgency
  - Authority hierarchy for the response chain
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.domain.simulation.escalation_engine import (
    MULTI_COUNTRY_CASCADE_MIN,
    SECTOR_ELEVATED_THRESHOLD,
    SECTOR_SEVERE_THRESHOLD,
    SOVEREIGN_BUFFER_CRITICAL,
    SYSTEMIC_AGGREGATE_THRESHOLD,
)
from app.domain.simulation.graph_runner import GraphRunner
from app.domain.simulation.ownership_engine import (
    AuthorityLevel,
    _OWNERSHIP_RULES,
)

logger = logging.getLogger("observatory.phase3_decisions")

router = APIRouter(
    prefix="/decisions",
    tags=["decisions-phase3"],
)

_runner = GraphRunner()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionAnalysisRequest(BaseModel):
    """Input for decision analysis."""
    severity: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Override default severity.",
    )
    horizon_hours: Optional[int] = Field(
        default=None, ge=1, le=8760,
        description="Override default horizon.",
    )
    country_code: Optional[str] = Field(
        default=None,
        description="Focus on specific GCC country (ISO alpha-3).",
    )
    extra_params: dict[str, Any] = Field(
        default_factory=dict,
    )


class DecisionOwnershipItem(BaseModel):
    """Single ownership mapping for documentation."""
    action: str
    sector: str
    owner_entity_type: str
    owner_role: str
    owner_role_ar: str
    authority_level: str
    deadline_hours: float
    escalation_path: list[str]
    regulatory_reference: str
    failure_consequence: str


class OwnershipRegistryResponse(BaseModel):
    """All ownership mappings."""
    total_rules: int
    rules: list[DecisionOwnershipItem]


class EscalationRuleResponse(BaseModel):
    """Escalation threshold documentation."""
    rule_name: str
    threshold_value: float | int
    description: str
    authority_required: str


class EscalationRulesResponse(BaseModel):
    """All escalation rules."""
    rules: list[EscalationRuleResponse]


class DecisionDetail(BaseModel):
    """Single decision with full ownership context."""
    action: str
    owner: str
    timing: str
    value_avoided_usd: float
    downside_risk: str
    owner_entity_type: str
    owner_role: str
    owner_role_ar: str
    authority_level: str
    deadline_hours: float
    escalation_path: list[str]
    regulatory_reference: str
    failure_consequence: str
    country_entity_name: str
    country_entity_name_ar: str


class EscalationDetail(BaseModel):
    """Single escalation alert."""
    trigger: str
    severity: str
    authority_required: str
    headline: str
    headline_ar: str
    affected_entities: list[str]
    affected_countries: list[str]
    affected_sectors: list[str]
    time_to_act_hours: float
    narrative: str
    recommended_actions: list[str]


class DecisionAnalysisResponse(BaseModel):
    """Full decision analysis output."""
    scenario_slug: str
    model_version: str
    timestamp: str
    sha256_digest: str

    # Stress context
    total_loss_usd: float
    risk_level: str

    # Decisions
    total_decisions: int
    decisions: list[DecisionDetail]

    # Escalations
    total_escalations: int
    sovereign_alerts: int
    escalations: list[EscalationDetail]

    # Entity breach summary
    entities_breached: int
    breached_entities: list[str]

    # Decision urgency summary
    immediate_actions: int     # deadline <= 4h
    urgent_actions: int        # deadline <= 12h
    standard_actions: int      # deadline > 12h


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/analyze/{slug}",
    response_model=DecisionAnalysisResponse,
    summary="Run decision analysis with ownership and escalation",
)
async def analyze_decisions(slug: str, body: DecisionAnalysisRequest):
    """Execute Phase 3 simulation and return decision-focused analysis.

    Each decision includes:
    - Institutional owner with Arabic role name
    - Deadline in hours from trigger
    - Escalation path if deadline is missed
    - Regulatory reference for audit trail
    - Failure consequence narrative
    """
    try:
        result = _runner.run(
            slug=slug,
            severity=body.severity,
            horizon_hours=body.horizon_hours,
            country_code=body.country_code,
            **body.extra_params,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario '{slug}' not found.")
    except Exception as e:
        logger.error("Decision analysis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")

    prop = result.propagation

    decisions = [
        DecisionDetail(
            action=d.action,
            owner=d.owner,
            timing=d.timing,
            value_avoided_usd=d.value_avoided_usd,
            downside_risk=d.downside_risk,
            owner_entity_type=d.owner_entity_type,
            owner_role=d.owner_role,
            owner_role_ar=d.owner_role_ar,
            authority_level=d.authority_level,
            deadline_hours=d.deadline_hours,
            escalation_path=d.escalation_path,
            regulatory_reference=d.regulatory_reference,
            failure_consequence=d.failure_consequence,
            country_entity_name=d.country_entity_name,
            country_entity_name_ar=d.country_entity_name_ar,
        )
        for d in result.enriched_decisions
    ]

    escalations = [
        EscalationDetail(**a) for a in result.escalation_alerts
    ]

    # Urgency classification
    immediate = sum(1 for d in decisions if d.deadline_hours <= 4.0)
    urgent = sum(1 for d in decisions if 4.0 < d.deadline_hours <= 12.0)
    standard = sum(1 for d in decisions if d.deadline_hours > 12.0)

    # Breached entity IDs
    breached = [e.entity_id for e in result.entity_states if e.breached]

    risk_level = (
        prop.country_impacts[0].risk_level.value
        if prop.country_impacts
        else "NOMINAL"
    )

    return DecisionAnalysisResponse(
        scenario_slug=result.scenario_slug,
        model_version=result.model_version,
        timestamp=result.timestamp,
        sha256_digest=result.sha256_digest,
        total_loss_usd=round(prop.total_loss_usd, 2),
        risk_level=risk_level,
        total_decisions=len(decisions),
        decisions=decisions,
        total_escalations=len(escalations),
        sovereign_alerts=result.sovereign_alerts,
        escalations=escalations,
        entities_breached=result.entities_breached,
        breached_entities=breached,
        immediate_actions=immediate,
        urgent_actions=urgent,
        standard_actions=standard,
    )


@router.get(
    "/ownership",
    response_model=OwnershipRegistryResponse,
    summary="List all decision ownership mappings",
)
async def list_ownership():
    """Return the complete decision-to-owner mapping registry.

    Each rule maps a decision action to its institutional owner,
    authority level, deadline, and escalation path.
    """
    rules = [
        DecisionOwnershipItem(
            action=r.action,
            sector=r.sector,
            owner_entity_type=r.owner_entity_type.value,
            owner_role=r.owner_role,
            owner_role_ar=r.owner_role_ar,
            authority_level=r.authority_level.value,
            deadline_hours=r.deadline_hours,
            escalation_path=r.escalation_path,
            regulatory_reference=r.regulatory_reference,
            failure_consequence=r.failure_consequence,
        )
        for r in _OWNERSHIP_RULES
    ]
    return OwnershipRegistryResponse(
        total_rules=len(rules),
        rules=rules,
    )


@router.get(
    "/escalation-rules",
    response_model=EscalationRulesResponse,
    summary="List escalation threshold rules",
)
async def list_escalation_rules():
    """Return all escalation threshold definitions.

    These thresholds trigger automatic authority elevation
    from operational → tactical → strategic → sovereign.
    """
    return EscalationRulesResponse(
        rules=[
            EscalationRuleResponse(
                rule_name="Sector SEVERE Threshold",
                threshold_value=SECTOR_SEVERE_THRESHOLD,
                description="Sector stress at or above this level is classified SEVERE. "
                            "SEVERE in 2+ countries triggers sector cascade escalation.",
                authority_required="sovereign",
            ),
            EscalationRuleResponse(
                rule_name="Sector ELEVATED Threshold",
                threshold_value=SECTOR_ELEVATED_THRESHOLD,
                description="Sector stress at or above this level is classified ELEVATED. "
                            f"ELEVATED in {MULTI_COUNTRY_CASCADE_MIN}+ countries triggers "
                            "multi-country cascade alert.",
                authority_required="strategic",
            ),
            EscalationRuleResponse(
                rule_name="Systemic Aggregate Threshold",
                threshold_value=SYSTEMIC_AGGREGATE_THRESHOLD,
                description="GDP-weighted average stress across all GCC countries. "
                            "Breaching this threshold indicates GCC-wide systemic risk.",
                authority_required="sovereign",
            ),
            EscalationRuleResponse(
                rule_name="Sovereign Buffer Critical",
                threshold_value=SOVEREIGN_BUFFER_CRITICAL,
                description="Sovereign wealth fund remaining capacity below this level "
                            "triggers emergency sovereign intervention alert.",
                authority_required="sovereign",
            ),
            EscalationRuleResponse(
                rule_name="Multi-Country Cascade Minimum",
                threshold_value=MULTI_COUNTRY_CASCADE_MIN,
                description="Minimum number of GCC countries with ELEVATED+ stress "
                            "required to trigger multi-country cascade alert.",
                authority_required="strategic",
            ),
        ],
    )
