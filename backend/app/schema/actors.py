"""Actor and organization models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import ActorType
from .geo import GeoPoint, Region


class Actor(BaseEntity):
    """An actor (person, organization, movement, etc.) in the system."""

    name: str = Field(description="Name of the actor")
    name_ar: Optional[str] = Field(default=None, description="Name in Arabic")
    actor_type: ActorType = Field(description="Type of actor")
    description: Optional[str] = Field(default=None, description="Description of the actor")
    description_ar: Optional[str] = Field(default=None, description="Arabic description")
    aliases: list[str] = Field(
        default_factory=list, description="Alternative names or aliases"
    )
    primary_location: Optional[GeoPoint] = Field(
        default=None, description="Primary operating location"
    )
    operational_regions: list[Region] = Field(
        default_factory=list, description="Regions where actor operates"
    )
    objectives: list[str] = Field(
        default_factory=list, description="Primary objectives or goals"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Known capabilities"
    )
    known_affiliations: list[str] = Field(
        default_factory=list, description="IDs of affiliated actors"
    )
    threat_level: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Assessed threat level (0-1)"
    )
    last_activity_date: Optional[str] = Field(
        default=None, description="Last known activity date (ISO format)"
    )
    active: bool = Field(default=True, description="Whether actor is currently active")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("threat_level")
    @classmethod
    def validate_threat_level(cls, v: float | None) -> float | None:
        """Ensure threat level is valid."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise ValueError("Threat level must be between 0 and 1")
        return v


class Organization(BaseEntity):
    """An organization entity."""

    name: str = Field(description="Organization name")
    name_ar: Optional[str] = Field(default=None, description="Organization name in Arabic")
    organization_type: str = Field(
        description="Type of organization (government, corporate, ngo, etc.)"
    )
    description: Optional[str] = Field(default=None, description="Organization description")
    headquarters_location: Optional[GeoPoint] = Field(
        default=None, description="Location of headquarters"
    )
    operational_regions: list[Region] = Field(
        default_factory=list, description="Regions of operation"
    )
    established_year: Optional[int] = Field(
        default=None, description="Year organization was established"
    )
    employee_count: Optional[int] = Field(
        default=None, description="Number of employees"
    )
    annual_revenue_usd_millions: Optional[float] = Field(
        default=None, description="Annual revenue in millions USD"
    )
    leadership: list[str] = Field(
        default_factory=list, description="Names or IDs of key leaders"
    )
    parent_organization_id: Optional[str] = Field(
        default=None, description="ID of parent organization if subsidiary"
    )
    subsidiary_ids: list[str] = Field(
        default_factory=list, description="IDs of subsidiary organizations"
    )
    partner_ids: list[str] = Field(
        default_factory=list, description="IDs of partner organizations"
    )
    contact_email: Optional[str] = Field(default=None, description="Contact email address")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone number")
    website: Optional[str] = Field(default=None, description="Website URL")
    active: bool = Field(default=True, description="Whether organization is currently active")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("organization_type")
    @classmethod
    def validate_org_type(cls, v: str) -> str:
        """Ensure organization type is valid."""
        valid_types = [
            "government",
            "corporate",
            "ngo",
            "international_org",
            "military",
            "law_enforcement",
            "academic",
            "other",
        ]
        if v not in valid_types:
            raise ValueError(f"Organization type must be one of: {valid_types}")
        return v

    @field_validator("employee_count")
    @classmethod
    def validate_employee_count(cls, v: int | None) -> int | None:
        """Ensure employee count is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Employee count cannot be negative")
        return v

    @field_validator("annual_revenue_usd_millions")
    @classmethod
    def validate_revenue(cls, v: float | None) -> float | None:
        """Ensure revenue is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Revenue cannot be negative")
        return v


class Policy(BaseEntity):
    """A policy or regulation that affects the system."""

    name: str = Field(description="Policy name")
    name_ar: Optional[str] = Field(default=None, description="Policy name in Arabic")
    policy_type: str = Field(description="Type of policy (tariff, regulation, restriction, etc.)")
    description: str = Field(description="Full policy description")
    description_ar: Optional[str] = Field(
        default=None, description="Policy description in Arabic"
    )
    issuing_organization_id: str = Field(
        description="ID of organization that issued the policy"
    )
    issuing_country_code: Optional[str] = Field(
        default=None, description="ISO 3166-1 alpha-3 country code of issuing country"
    )
    effective_date: Optional[str] = Field(
        default=None, description="Effective date (ISO format)"
    )
    expiration_date: Optional[str] = Field(
        default=None, description="Expiration date (ISO format)"
    )
    scope: list[str] = Field(
        default_factory=list, description="Scope of policy (e.g., countries, sectors affected)"
    )
    affected_entities: dict[str, list[str]] = Field(
        default_factory=dict, description="Mapping of entity types to affected entity IDs"
    )
    impact: Optional[str] = Field(
        default=None, description="Description of policy impact"
    )
    enforcement_status: str = Field(
        default="active", description="Enforcement status (active, pending, suspended, expired)"
    )
    references: list[str] = Field(
        default_factory=list, description="External references or URLs"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("policy_type")
    @classmethod
    def validate_policy_type(cls, v: str) -> str:
        """Ensure policy type is valid."""
        valid_types = [
            "tariff",
            "regulation",
            "restriction",
            "ban",
            "subsidy",
            "agreement",
            "standard",
            "other",
        ]
        if v not in valid_types:
            raise ValueError(f"Policy type must be one of: {valid_types}")
        return v

    @field_validator("enforcement_status")
    @classmethod
    def validate_enforcement_status(cls, v: str) -> str:
        """Ensure enforcement status is valid."""
        valid_statuses = ["active", "pending", "suspended", "expired", "proposed"]
        if v not in valid_statuses:
            raise ValueError(f"Enforcement status must be one of: {valid_statuses}")
        return v
