"""
Impact Observatory | مرصد الأثر — Phase 3 Graph API Route

GET  /api/v1/graph/entities            → List all institutional entities
GET  /api/v1/graph/entities/{country}  → List entities for a specific country
POST /api/v1/graph/run/{slug}          → Run Phase 3 graph simulation

Returns entity graph overlay, country-sector matrix interactions,
and full node/edge state for CesiumJS / force-graph visualization.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.domain.simulation.entity_graph import (
    build_entity_links,
    build_entity_registry,
)
from app.domain.simulation.graph_runner import GraphRunner, Phase3RunResult

logger = logging.getLogger("observatory.phase3_graph")

router = APIRouter(
    prefix="/graph",
    tags=["graph-phase3"],
)

_runner = GraphRunner()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class GraphRunRequest(BaseModel):
    """Input for Phase 3 graph simulation."""
    severity: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Override default severity (0.0–1.0).",
    )
    horizon_hours: Optional[int] = Field(
        default=None,
        ge=1, le=8760,
        description="Override default horizon in hours.",
    )
    country_code: Optional[str] = Field(
        default=None,
        description="Optional: focus results on a single GCC country (ISO alpha-3).",
    )
    extra_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Scenario-specific overrides.",
    )


class EntityResponse(BaseModel):
    """Single entity in the registry."""
    entity_id: str
    entity_type: str
    country_code: str
    name: str
    name_ar: str
    absorber_capacity: float


class EntityLinkResponse(BaseModel):
    """Single entity link."""
    entity_id: str
    country_code: str
    sector_code: str
    link_type: str
    weight: float
    channel: str


class EntityRegistryResponse(BaseModel):
    """Full entity registry response."""
    total_entities: int
    total_links: int
    entities: list[EntityResponse]
    links: list[EntityLinkResponse]


class EntityStateResponse(BaseModel):
    """Entity state after simulation."""
    entity_id: str
    entity_type: str
    country_code: str
    name: str
    name_ar: str
    absorber_capacity: float
    current_utilization: float
    stress: float
    breached: bool
    remaining_capacity: float


class EscalationAlertResponse(BaseModel):
    """Escalation alert."""
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


class EnrichedDecisionResponse(BaseModel):
    """Decision with ownership enrichment."""
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


class GraphRunResponse(BaseModel):
    """Full Phase 3 graph simulation response."""
    scenario_slug: str
    model_version: str
    timestamp: str
    severity: float
    horizon_hours: int
    sha256_digest: str

    # Core metrics
    total_loss_usd: float
    risk_level: str
    confidence: float
    converged: bool
    iterations_run: int

    # Phase 3 overlay
    entity_states: list[EntityStateResponse]
    escalation_alerts: list[EscalationAlertResponse]
    enriched_decisions: list[EnrichedDecisionResponse]

    # Summary
    entities_breached: int
    escalation_count: int
    sovereign_alerts: int

    # Pathway headlines
    pathway_headlines: list[str]

    # Explainability
    explainability: dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/entities",
    response_model=EntityRegistryResponse,
    summary="List all institutional entities and links",
)
async def list_entities():
    """Return the full GCC institutional entity registry.

    42 entities (7 types × 6 countries) and 96 typed links
    connecting entities to country-sector nodes.
    """
    entities = build_entity_registry()
    links = build_entity_links()

    return EntityRegistryResponse(
        total_entities=len(entities),
        total_links=len(links),
        entities=[
            EntityResponse(
                entity_id=e.entity_id,
                entity_type=e.entity_type.value,
                country_code=e.country_code,
                name=e.name,
                name_ar=e.name_ar,
                absorber_capacity=e.absorber_capacity,
            )
            for e in entities.values()
        ],
        links=[
            EntityLinkResponse(
                entity_id=l.entity_id,
                country_code=l.country_code,
                sector_code=l.sector_code,
                link_type=l.link_type,
                weight=l.weight,
                channel=l.channel,
            )
            for l in links
        ],
    )


@router.get(
    "/entities/{country_code}",
    response_model=EntityRegistryResponse,
    summary="List entities for a specific GCC country",
)
async def list_country_entities(country_code: str):
    """Return entities and links for a single GCC country."""
    cc = country_code.upper()
    valid_countries = {"KWT", "SAU", "UAE", "QAT", "BHR", "OMN"}
    if cc not in valid_countries:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid country code '{country_code}'. Must be one of: {', '.join(sorted(valid_countries))}",
        )

    entities = build_entity_registry()
    links = build_entity_links()

    filtered_entities = {k: v for k, v in entities.items() if v.country_code == cc}
    filtered_links = [l for l in links if l.country_code == cc]

    return EntityRegistryResponse(
        total_entities=len(filtered_entities),
        total_links=len(filtered_links),
        entities=[
            EntityResponse(
                entity_id=e.entity_id,
                entity_type=e.entity_type.value,
                country_code=e.country_code,
                name=e.name,
                name_ar=e.name_ar,
                absorber_capacity=e.absorber_capacity,
            )
            for e in filtered_entities.values()
        ],
        links=[
            EntityLinkResponse(
                entity_id=l.entity_id,
                country_code=l.country_code,
                sector_code=l.sector_code,
                link_type=l.link_type,
                weight=l.weight,
                channel=l.channel,
            )
            for l in filtered_links
        ],
    )


@router.post(
    "/run/{slug}",
    response_model=GraphRunResponse,
    summary="Run Phase 3 entity-aware graph simulation",
)
async def run_graph_simulation(slug: str, body: GraphRunRequest):
    """Execute Phase 3 simulation with entity graph overlay.

    Extends Phase 2 propagation with:
    - Institutional entity absorber/amplifier effects
    - Government and real estate transmission rules
    - Escalation threshold detection
    - Ownership-enriched decisions
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
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{slug}' not found in registry.",
        )
    except Exception as e:
        logger.error("Phase 3 simulation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")

    prop = result.propagation
    risk_level = (
        prop.country_impacts[0].risk_level.value
        if prop.country_impacts
        else "NOMINAL"
    )

    return GraphRunResponse(
        scenario_slug=result.scenario_slug,
        model_version=result.model_version,
        timestamp=result.timestamp,
        severity=result.severity,
        horizon_hours=result.horizon_hours,
        sha256_digest=result.sha256_digest,
        total_loss_usd=round(prop.total_loss_usd, 2),
        risk_level=risk_level,
        confidence=prop.confidence,
        converged=prop.converged,
        iterations_run=prop.iterations_run,
        entity_states=[
            EntityStateResponse(
                entity_id=e.entity_id,
                entity_type=e.entity_type,
                country_code=e.country_code,
                name=e.name,
                name_ar=e.name_ar,
                absorber_capacity=e.absorber_capacity,
                current_utilization=e.current_utilization,
                stress=e.stress,
                breached=e.breached,
                remaining_capacity=e.remaining_capacity,
            )
            for e in result.entity_states
        ],
        escalation_alerts=[
            EscalationAlertResponse(**a) for a in result.escalation_alerts
        ],
        enriched_decisions=[
            EnrichedDecisionResponse(
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
        ],
        entities_breached=result.entities_breached,
        escalation_count=result.escalation_count,
        sovereign_alerts=result.sovereign_alerts,
        pathway_headlines=prop.pathway_headlines,
        explainability={
            "why_total_loss": result.explainability.why_total_loss,
            "why_country": result.explainability.why_country,
            "why_sector": result.explainability.why_sector,
            "why_act_now": result.explainability.why_act_now,
        },
    )
