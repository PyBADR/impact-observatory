"""Infrastructure and asset models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import AssetType, TransportMode
from .geo import City, GeoPoint, GeoZone


class Infrastructure(BaseEntity):
    """An infrastructure asset or facility."""

    name: str = Field(description="Name of the infrastructure")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    asset_type: AssetType = Field(description="Type of infrastructure asset")
    description: Optional[str] = Field(default=None, description="Description")
    location: GeoPoint = Field(description="Geographic location")
    country_code: str = Field(description="ISO 3166-1 alpha-3 country code")
    operational_status: str = Field(
        default="operational", description="Current operational status"
    )
    capacity: Optional[str] = Field(
        default=None, description="Asset capacity (units depend on type)"
    )
    critical_infrastructure: bool = Field(
        default=False, description="Whether this is critical infrastructure"
    )
    last_inspection_date: Optional[str] = Field(
        default=None, description="Last inspection date (ISO format)"
    )
    maintenance_schedule: Optional[str] = Field(
        default=None, description="Maintenance schedule information"
    )

    @field_validator("operational_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid."""
        valid_statuses = ["operational", "degraded", "non-operational", "maintenance", "unknown"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class Asset(BaseEntity):
    """A moveable or fixed asset."""

    name: str = Field(description="Asset name")
    asset_type: AssetType = Field(description="Type of asset")
    identifier: str = Field(description="Unique identifier (e.g., ICAO, MMSI)")
    owner_id: Optional[str] = Field(default=None, description="Owner entity ID")
    owner_name: Optional[str] = Field(default=None, description="Owner name")
    current_location: GeoPoint = Field(description="Current location")
    last_location_update: Optional[str] = Field(
        default=None, description="ISO timestamp of last location update"
    )
    status: str = Field(default="operational", description="Asset operational status")
    health_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Asset health score (0-1)"
    )
    associated_infrastructure_ids: list[str] = Field(
        default_factory=list, description="IDs of associated infrastructure"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid."""
        valid_statuses = ["operational", "degraded", "maintenance", "damaged", "lost", "unknown"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v

    @field_validator("health_score")
    @classmethod
    def validate_health_score(cls, v: float | None) -> float | None:
        """Ensure health score is valid."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Health score must be between 0 and 1")
        return v


class Airport(Infrastructure):
    """An airport facility."""

    icao_code: str = Field(description="ICAO 4-letter airport code")
    iata_code: Optional[str] = Field(default=None, description="IATA 3-letter airport code")
    city: Optional[City] = Field(default=None, description="City information")
    runways: int = Field(default=1, ge=1, description="Number of runways")
    elevation_meters: Optional[float] = Field(default=None, description="Elevation in meters")
    max_capacity_daily: Optional[int] = Field(
        default=None, description="Maximum daily flight capacity"
    )
    airlines: list[str] = Field(
        default_factory=list, description="List of operating airlines"
    )
    international_airport: bool = Field(
        default=False, description="Whether international flights operate"
    )

    @field_validator("runways")
    @classmethod
    def validate_runways(cls, v: int) -> int:
        """Ensure runway count is valid."""
        if v < 1:
            raise ValueError("Must have at least 1 runway")
        return v


class Port(Infrastructure):
    """A seaport facility."""

    port_code: str = Field(description="International port code (usually UN/LOCODE)")
    un_locode: Optional[str] = Field(default=None, description="UN Location Code")
    berth_count: int = Field(default=1, ge=1, description="Number of berths")
    max_draft_meters: Optional[float] = Field(
        default=None, description="Maximum draft in meters"
    )
    annual_throughput_teu: Optional[int] = Field(
        default=None, description="Annual throughput in TEU (containers)"
    )
    annual_throughput_tons: Optional[int] = Field(
        default=None, description="Annual throughput in tons"
    )
    container_capable: bool = Field(
        default=False, description="Whether port handles containers"
    )
    ro_ro_capable: bool = Field(
        default=False, description="Whether port handles RO-RO cargo"
    )
    bulk_capable: bool = Field(
        default=False, description="Whether port handles bulk cargo"
    )

    @field_validator("berth_count")
    @classmethod
    def validate_berth_count(cls, v: int) -> int:
        """Ensure berth count is valid."""
        if v < 1:
            raise ValueError("Must have at least 1 berth")
        return v


class Corridor(BaseEntity):
    """A transportation corridor (e.g., shipping route, air lane)."""

    name: str = Field(description="Corridor name")
    description: Optional[str] = Field(default=None, description="Corridor description")
    corridor_type: str = Field(description="Type of corridor (e.g., sea_route, air_lane, land_route)")
    origin_location: GeoPoint = Field(description="Starting point")
    destination_location: GeoPoint = Field(description="Ending point")
    waypoints: list[GeoPoint] = Field(
        default_factory=list, description="Intermediate waypoints"
    )
    distance_nm: Optional[float] = Field(
        default=None, description="Distance in nautical miles"
    )
    distance_km: Optional[float] = Field(
        default=None, description="Distance in kilometers"
    )
    expected_transit_hours: Optional[float] = Field(
        default=None, description="Expected transit time in hours"
    )
    annual_traffic_volume: Optional[int] = Field(
        default=None, description="Annual traffic volume (units depend on corridor type)"
    )
    critical_corridor: bool = Field(
        default=False, description="Whether this is a critical corridor"
    )
    bottleneck_zones: list[GeoZone] = Field(
        default_factory=list, description="Geographic zones with capacity constraints"
    )

    @field_validator("corridor_type")
    @classmethod
    def validate_corridor_type(cls, v: str) -> str:
        """Ensure corridor type is valid."""
        valid_types = ["sea_route", "air_lane", "land_route", "rail_route", "pipeline_route"]
        if v not in valid_types:
            raise ValueError(f"Corridor type must be one of: {valid_types}")
        return v


class Route(BaseEntity):
    """A specific route (instance of a corridor)."""

    name: str = Field(description="Route name")
    corridor_id: str = Field(description="ID of parent corridor")
    origin_id: str = Field(description="ID of origin location")
    destination_id: str = Field(description="ID of destination location")
    transport_mode: TransportMode = Field(description="Transport mode")
    active: bool = Field(default=True, description="Whether route is currently active")
    current_utilization: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Current capacity utilization (0-1)"
    )
    average_delay_hours: Optional[float] = Field(
        default=None, description="Average delay in hours"
    )
    last_updated: Optional[str] = Field(
        default=None, description="Last update timestamp (ISO format)"
    )

    @field_validator("current_utilization")
    @classmethod
    def validate_utilization(cls, v: float | None) -> float | None:
        """Ensure utilization is valid."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Utilization must be between 0 and 1")
        return v
