"""
Dataset L: Logistics Nodes
============================

GCC ports, airports, free zones, pipeline terminals, and logistics hubs.
Captures throughput capacity, utilization, connectivity, and operational status.

Source: Port authorities, GCAA, national logistics strategies, Lloyd's List
KG Mapping: (:LogisticsNode)-[:CONNECTED_TO]->(:LogisticsNode)
Consumers: Simulation engine (port/chokepoint scenarios), supply chain risk
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel, GeoCoordinate
from src.data_foundation.schemas.enums import (
    ConfidenceMethod,
    GCCCountry,
    PortType,
    TransportMode,
)

__all__ = ["LogisticsNode"]


class LogisticsNode(FoundationModel):
    """A logistics infrastructure node in the GCC network."""

    node_id: str = Field(
        ...,
        description="Unique node identifier.",
        examples=["KW-SHUWAIKH", "AE-JEBEL-ALI", "SA-JUBAIL", "OM-SALALAH"],
    )
    node_name: str = Field(
        ...,
        description="Official English name.",
        examples=["Jebel Ali Port", "King Abdulaziz Port"],
    )
    node_name_ar: Optional[str] = Field(
        default=None,
        description="Official Arabic name.",
    )
    country: GCCCountry = Field(...)
    entity_id: Optional[str] = Field(
        default=None,
        description="FK to entity_registry (parent operating entity).",
    )
    transport_mode: TransportMode = Field(
        ...,
        description="Primary transport mode.",
    )
    port_type: Optional[PortType] = Field(
        default=None,
        description="Port classification (only for maritime nodes).",
    )
    geo: GeoCoordinate = Field(
        ...,
        description="Geographic coordinates.",
    )

    # --- Capacity & throughput ---
    annual_capacity_teu: Optional[int] = Field(
        default=None,
        description="Annual container capacity (TEU). Maritime nodes only.",
    )
    annual_throughput_teu: Optional[int] = Field(
        default=None,
        description="Actual annual throughput (TEU).",
    )
    utilization_pct: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Current utilization (%).",
    )
    annual_cargo_tonnage: Optional[float] = Field(
        default=None,
        description="Annual cargo volume (million tonnes).",
    )
    vessel_calls_annual: Optional[int] = Field(
        default=None,
        description="Annual vessel calls.",
    )
    pax_annual: Optional[int] = Field(
        default=None,
        description="Annual passenger throughput (airports only).",
    )

    # --- Connectivity ---
    connected_node_ids: List[str] = Field(
        default_factory=list,
        description="Directly connected logistics nodes.",
    )
    chokepoint_dependency: Optional[str] = Field(
        default=None,
        description="Critical chokepoint this node depends on.",
        examples=["STRAIT_OF_HORMUZ", "BAB_AL_MANDAB", "SUEZ_CANAL"],
    )
    hinterland_coverage: Optional[List[str]] = Field(
        default=None,
        description="Regions served by this node.",
    )

    # --- Operational status ---
    operational_status: str = Field(
        default="OPERATIONAL",
        description="Current operational status.",
        examples=["OPERATIONAL", "PARTIALLY_DISRUPTED", "CLOSED", "UNDER_CONSTRUCTION"],
    )
    criticality_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Infrastructure criticality for risk modeling.",
    )
    last_disruption_date: Optional[date] = Field(
        default=None,
        description="Date of most recent operational disruption.",
    )

    # --- Metadata ---
    operator: Optional[str] = Field(
        default=None,
        description="Operating company or authority.",
        examples=["DP World", "Kuwait Ports Authority", "Oman Drydock"],
    )
    free_zone_id: Optional[str] = Field(
        default=None,
        description="Associated free zone entity ID.",
    )
    source_id: str = Field(..., description="FK to source_registry.")
    confidence_score: float = Field(default=0.80, ge=0.0, le=1.0)
    confidence_method: ConfidenceMethod = Field(default=ConfidenceMethod.SOURCE_DECLARED)
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict] = Field(default=None)
