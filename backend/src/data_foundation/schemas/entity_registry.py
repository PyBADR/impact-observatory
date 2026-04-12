"""
Dataset C: Entity Registry
============================

Master registry of all entities in the GCC economic graph: countries,
regulators, banks, insurers, logistics nodes, infrastructure assets.

Extends the existing schemas.entity.Entity with P1 data foundation fields
(provenance, multi-tenant, compliance metadata).

KG Mapping: (:Entity) node — central hub of the knowledge graph
Consumers: Simulation engine, impact map, entity intelligence, decision brain
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel, GeoCoordinate
from src.data_foundation.schemas.enums import (
    EntityType,
    GCCCountry,
    Sector,
)

__all__ = ["EntityRegistryEntry"]


class EntityRegistryEntry(FoundationModel):
    """A node in the GCC economic entity graph."""

    entity_id: str = Field(
        ...,
        description="Unique entity identifier (e.g., 'SA-SAMA', 'KW-NBK').",
        examples=["SA-SAMA", "KW-NBK", "AE-JAFZA"],
    )
    entity_name: str = Field(
        ...,
        description="Official English name.",
        examples=["Saudi Arabian Monetary Authority", "National Bank of Kuwait"],
    )
    entity_name_ar: Optional[str] = Field(
        default=None,
        description="Official Arabic name.",
        examples=["مؤسسة النقد العربي السعودي", "بنك الكويت الوطني"],
    )
    entity_type: EntityType = Field(
        ...,
        description="Classification of this entity.",
    )
    country: GCCCountry = Field(
        ...,
        description="GCC country where this entity is domiciled.",
    )
    sector: Sector = Field(
        ...,
        description="Primary sector classification.",
    )
    parent_entity_id: Optional[str] = Field(
        default=None,
        description="Parent entity ID for hierarchical relationships.",
    )
    geo: Optional[GeoCoordinate] = Field(
        default=None,
        description="Geographic coordinates for map visualization.",
    )
    gdp_weight: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Fractional contribution to national GDP.",
    )
    criticality_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Infrastructure criticality score for risk modeling.",
    )
    systemic_importance: Optional[str] = Field(
        default=None,
        description="Regulatory classification (e.g., 'D-SIB', 'G-SIB', 'critical-infrastructure').",
    )
    regulatory_id: Optional[str] = Field(
        default=None,
        description="Official regulatory identifier (e.g., CBK license number).",
    )
    swift_code: Optional[str] = Field(
        default=None,
        description="SWIFT/BIC code for financial entities.",
    )
    lei_code: Optional[str] = Field(
        default=None,
        description="Legal Entity Identifier (ISO 17442).",
    )
    website: Optional[str] = Field(
        default=None,
        description="Official website URL.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this entity is currently operational.",
    )
    related_entity_ids: List[str] = Field(
        default_factory=list,
        description="IDs of related entities (subsidiaries, partners, regulators).",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags.",
    )
    metadata: Optional[Dict] = Field(
        default=None,
        description="Extensible metadata bucket for entity-specific attributes.",
    )
