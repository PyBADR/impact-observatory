"""Transport models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import FlightStatus, VesselType
from .geo import GeoPoint


class Operator(BaseEntity):
    """An operator of transport assets (airline, shipping company, etc.)."""

    name: str = Field(description="Operator name")
    name_ar: Optional[str] = Field(default=None, description="Operator name in Arabic")
    type: str = Field(description="Type of operator (airline, shipping_company, etc.)")
    callsign: Optional[str] = Field(default=None, description="Radio callsign")
    icao_code: Optional[str] = Field(default=None, description="ICAO code (for airlines)")
    iata_code: Optional[str] = Field(default=None, description="IATA code (for airlines)")
    imo_number: Optional[str] = Field(default=None, description="IMO number (for shipping)")
    country_code: str = Field(description="ISO 3166-1 alpha-3 country code of registration")
    fleet_size: Optional[int] = Field(default=None, description="Size of managed fleet")
    established_year: Optional[int] = Field(default=None, description="Year operator was established")
    website: Optional[str] = Field(default=None, description="Operator website")
    active: bool = Field(default=True, description="Whether operator is currently active")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Ensure type is valid."""
        valid_types = ["airline", "shipping_company", "logistics_company", "railway_operator", "trucking_company"]
        if v not in valid_types:
            raise ValueError(f"Operator type must be one of: {valid_types}")
        return v

    @field_validator("fleet_size")
    @classmethod
    def validate_fleet_size(cls, v: int | None) -> int | None:
        """Ensure fleet size is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Fleet size cannot be negative")
        return v


class Flight(BaseEntity):
    """A flight record."""

    flight_number: str = Field(description="Flight number")
    operator_id: str = Field(description="ID of operator/airline")
    operator_name: str = Field(description="Name of operator/airline")
    departure_airport_id: str = Field(description="ICAO code of departure airport")
    arrival_airport_id: str = Field(description="ICAO code of arrival airport")
    departure_airport_name: Optional[str] = Field(
        default=None, description="Name of departure airport"
    )
    arrival_airport_name: Optional[str] = Field(
        default=None, description="Name of arrival airport"
    )
    scheduled_departure: datetime = Field(description="Scheduled departure time (UTC)")
    scheduled_arrival: datetime = Field(description="Scheduled arrival time (UTC)")
    actual_departure: Optional[datetime] = Field(
        default=None, description="Actual departure time (UTC)"
    )
    actual_arrival: Optional[datetime] = Field(
        default=None, description="Actual arrival time (UTC)"
    )
    status: FlightStatus = Field(
        default=FlightStatus.SCHEDULED, description="Current flight status"
    )
    aircraft_type: str = Field(description="Aircraft type (e.g., Boeing 777)")
    aircraft_registration: Optional[str] = Field(
        default=None, description="Aircraft registration/tail number"
    )
    current_position: Optional[GeoPoint] = Field(
        default=None, description="Current aircraft position"
    )
    current_altitude_feet: Optional[int] = Field(
        default=None, description="Current altitude in feet"
    )
    current_speed_knots: Optional[float] = Field(
        default=None, description="Current speed in knots"
    )
    heading: Optional[float] = Field(
        default=None, ge=0.0, le=360.0, description="Current heading in degrees (0-360)"
    )
    distance_flown_nm: Optional[float] = Field(
        default=None, description="Distance flown in nautical miles"
    )
    distance_remaining_nm: Optional[float] = Field(
        default=None, description="Distance remaining in nautical miles"
    )
    estimated_arrival: Optional[datetime] = Field(
        default=None, description="Estimated arrival time (UTC)"
    )
    delay_minutes: Optional[int] = Field(
        default=None, description="Delay in minutes from scheduled time"
    )
    cancellation_reason: Optional[str] = Field(
        default=None, description="Reason for cancellation if applicable"
    )
    diversion_airport_id: Optional[str] = Field(
        default=None, description="Diverted airport ICAO code if applicable"
    )

    @field_validator("heading")
    @classmethod
    def validate_heading(cls, v: float | None) -> float | None:
        """Ensure heading is valid."""
        if v is not None and not 0.0 <= v <= 360.0:
            raise ValueError("Heading must be between 0 and 360 degrees")
        return v

    @field_validator("scheduled_arrival")
    @classmethod
    def validate_arrival_after_departure(cls, v: datetime, info) -> datetime:
        """Ensure arrival is after departure."""
        if "scheduled_departure" in info.data:
            if v <= info.data["scheduled_departure"]:
                raise ValueError("Scheduled arrival must be after scheduled departure")
        return v


class Vessel(BaseEntity):
    """A vessel (ship) record."""

    mmsi: str = Field(description="Maritime Mobile Service Identity")
    imo: Optional[str] = Field(default=None, description="International Maritime Organization number")
    vessel_name: str = Field(description="Name of the vessel")
    callsign: Optional[str] = Field(default=None, description="Radio callsign")
    vessel_type: VesselType = Field(description="Type of vessel")
    flag_state: str = Field(description="ISO 3166-1 alpha-3 code of flag state")
    owner_id: Optional[str] = Field(default=None, description="Owner entity ID")
    operator_id: Optional[str] = Field(default=None, description="Operator entity ID")
    operator_name: Optional[str] = Field(default=None, description="Operator name")
    year_built: Optional[int] = Field(default=None, description="Year vessel was built")
    length_meters: Optional[float] = Field(default=None, description="Length in meters")
    beam_meters: Optional[float] = Field(default=None, description="Beam (width) in meters")
    draft_meters: Optional[float] = Field(default=None, description="Draft in meters")
    gross_tonnage: Optional[float] = Field(default=None, description="Gross tonnage")
    deadweight_tonnage: Optional[float] = Field(
        default=None, description="Deadweight tonnage"
    )
    teu_capacity: Optional[int] = Field(
        default=None, description="Container capacity in TEU (for container ships)"
    )
    current_position: GeoPoint = Field(description="Current vessel position")
    destination_port_id: Optional[str] = Field(
        default=None, description="ID of destination port"
    )
    destination_port_name: Optional[str] = Field(
        default=None, description="Name of destination port"
    )
    estimated_arrival: Optional[datetime] = Field(
        default=None, description="Estimated arrival at destination (UTC)"
    )
    speed_knots: Optional[float] = Field(
        default=None, ge=0.0, description="Current speed in knots"
    )
    heading: Optional[float] = Field(
        default=None, ge=0.0, le=360.0, description="Current heading in degrees (0-360)"
    )
    status: str = Field(
        default="underway", description="Vessel status (underway, anchored, moored, etc.)"
    )
    cargo_description: Optional[str] = Field(
        default=None, description="Description of cargo"
    )
    imo_hazmat: bool = Field(default=False, description="Whether carrying hazardous materials")

    @field_validator("heading")
    @classmethod
    def validate_heading(cls, v: float | None) -> float | None:
        """Ensure heading is valid."""
        if v is not None and not 0.0 <= v <= 360.0:
            raise ValueError("Heading must be between 0 and 360 degrees")
        return v

    @field_validator("speed_knots")
    @classmethod
    def validate_speed(cls, v: float | None) -> float | None:
        """Ensure speed is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Speed cannot be negative")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid."""
        valid_statuses = ["underway", "anchored", "moored", "docked", "in_port", "restricted_maneuverability"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v
