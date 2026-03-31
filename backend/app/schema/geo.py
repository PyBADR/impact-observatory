"""Geospatial models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import SourceType


class GeoPoint(BaseEntity):
    """A geographic point with latitude and longitude."""

    latitude: float = Field(description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(description="Longitude coordinate (-180 to 180)")
    altitude: Optional[float] = Field(
        default=None, description="Altitude in meters above sea level"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="Timestamp for the position"
    )
    accuracy: Optional[float] = Field(
        default=None, description="Accuracy of the position in meters"
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Ensure latitude is between -90 and 90."""
        if not -90.0 <= v <= 90.0:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Ensure longitude is between -180 and 180."""
        if not -180.0 <= v <= 180.0:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class GeoZone(BaseEntity):
    """A geographic zone (polygon or buffer around a point)."""

    name: str = Field(description="Name of the zone")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    description: Optional[str] = Field(default=None, description="Description of the zone")
    center_point: GeoPoint = Field(description="Center point of the zone")
    radius_km: Optional[float] = Field(
        default=None, description="Radius in kilometers if zone is circular"
    )
    polygon_coordinates: Optional[list[tuple[float, float]]] = Field(
        default=None, description="List of (lat, lon) tuples defining a polygon boundary"
    )
    area_km2: Optional[float] = Field(default=None, description="Area in square kilometers")
    zone_type: str = Field(default="custom", description="Type of zone")

    @field_validator("polygon_coordinates")
    @classmethod
    def validate_polygon(cls, v: list[tuple[float, float]] | None) -> list[tuple[float, float]] | None:
        """Validate polygon coordinates."""
        if v is not None:
            if len(v) < 3:
                raise ValueError("Polygon must have at least 3 coordinates")
            for lat, lon in v:
                if not -90.0 <= lat <= 90.0:
                    raise ValueError("Polygon latitude must be between -90 and 90")
                if not -180.0 <= lon <= 180.0:
                    raise ValueError("Polygon longitude must be between -180 and 180")
        return v

    @field_validator("radius_km")
    @classmethod
    def validate_radius(cls, v: float | None) -> float | None:
        """Ensure radius is positive."""
        if v is not None and v <= 0:
            raise ValueError("Radius must be positive")
        return v


class Region(BaseEntity):
    """A geographic region."""

    name: str = Field(description="Name of the region")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    region_code: str = Field(description="ISO or custom region code")
    description: Optional[str] = Field(default=None, description="Description of the region")
    center_point: GeoPoint = Field(description="Center point of the region")
    boundary: Optional[GeoZone] = Field(
        default=None, description="Geographic boundary of the region"
    )
    parent_region_id: Optional[str] = Field(
        default=None, description="ID of parent region if hierarchical"
    )
    area_km2: Optional[float] = Field(default=None, description="Total area in square kilometers")
    population: Optional[int] = Field(default=None, description="Population estimate")

    @field_validator("area_km2")
    @classmethod
    def validate_area(cls, v: float | None) -> float | None:
        """Ensure area is positive."""
        if v is not None and v <= 0:
            raise ValueError("Area must be positive")
        return v

    @field_validator("population")
    @classmethod
    def validate_population(cls, v: int | None) -> int | None:
        """Ensure population is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Population cannot be negative")
        return v


class Country(BaseEntity):
    """A country entity."""

    name: str = Field(description="Country name")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    iso_alpha_2: str = Field(description="ISO 3166-1 alpha-2 code")
    iso_alpha_3: str = Field(description="ISO 3166-1 alpha-3 code")
    iso_numeric: str = Field(description="ISO 3166-1 numeric code")
    region: Region = Field(description="Region/continent information")
    capital: Optional[str] = Field(default=None, description="Capital city")
    area_km2: Optional[float] = Field(default=None, description="Total area in square kilometers")
    population: Optional[int] = Field(default=None, description="Population estimate")
    gdp_usd_billions: Optional[float] = Field(default=None, description="GDP in billions USD")
    borders: list[str] = Field(
        default_factory=list, description="List of ISO codes of bordering countries"
    )

    @field_validator("iso_alpha_2")
    @classmethod
    def validate_iso_alpha_2(cls, v: str) -> str:
        """Ensure ISO alpha-2 code is exactly 2 characters."""
        if len(v) != 2:
            raise ValueError("ISO alpha-2 must be exactly 2 characters")
        return v.upper()

    @field_validator("iso_alpha_3")
    @classmethod
    def validate_iso_alpha_3(cls, v: str) -> str:
        """Ensure ISO alpha-3 code is exactly 3 characters."""
        if len(v) != 3:
            raise ValueError("ISO alpha-3 must be exactly 3 characters")
        return v.upper()


class City(BaseEntity):
    """A city entity."""

    name: str = Field(description="City name")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    country_code: str = Field(description="ISO 3166-1 alpha-3 country code")
    country_name: str = Field(description="Country name")
    location: GeoPoint = Field(description="Geographic location of the city")
    population: Optional[int] = Field(default=None, description="Population estimate")
    time_zone: Optional[str] = Field(default=None, description="IANA time zone identifier")
    is_major_hub: bool = Field(default=False, description="Whether city is a major transport hub")

    @field_validator("population")
    @classmethod
    def validate_population(cls, v: int | None) -> int | None:
        """Ensure population is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Population cannot be negative")
        return v
