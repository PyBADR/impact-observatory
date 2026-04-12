"""
Dataset B: Source Registry
===========================

Catalog of all external and internal data sources.
Each source has a reliability score, access method, and compliance metadata.

KG Mapping: (:Source) node with -[:FEEDS]-> (:Dataset)
Consumers: Ingestion scheduler, trust scoring engine, compliance audit
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    GCCCountry,
    IngestionFrequency,
    SourceReliability,
    SourceType,
)

__all__ = ["SourceRegistryEntry"]


class SourceRegistryEntry(FoundationModel):
    """A registered data source feeding the Impact Observatory."""

    source_id: str = Field(
        ...,
        description="Unique source identifier (e.g., 'cbk-statistical-bulletin').",
        examples=["cbk-statistical-bulletin", "reuters-eikon-gcc"],
    )
    source_name: str = Field(
        ...,
        description="Human-readable source name.",
        examples=["Central Bank of Kuwait Statistical Bulletin"],
    )
    source_name_ar: Optional[str] = Field(
        default=None,
        description="Arabic source name.",
    )
    source_type: SourceType = Field(
        ...,
        description="How data is acquired from this source.",
    )
    reliability: SourceReliability = Field(
        ...,
        description="Assessed reliability tier.",
    )
    trust_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Numeric trust score [0.0–1.0]. Derived from reliability tier + track record.",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="API base URL or documentation URL.",
    )
    api_version: Optional[str] = Field(
        default=None,
        description="API version string.",
    )
    auth_method: Optional[str] = Field(
        default=None,
        description="Authentication method (e.g., 'api_key', 'oauth2', 'none').",
    )
    ingestion_frequency: IngestionFrequency = Field(
        default=IngestionFrequency.ON_DEMAND,
    )
    countries_covered: List[GCCCountry] = Field(
        default_factory=list,
        description="GCC countries this source covers.",
    )
    dataset_ids: List[str] = Field(
        default_factory=list,
        description="Datasets this source feeds (FK to dataset_registry).",
    )
    data_sovereignty_jurisdiction: Optional[str] = Field(
        default=None,
        description="Legal jurisdiction for data residency (ISO 3166-1 alpha-2).",
    )
    pdpl_compliant: Optional[bool] = Field(
        default=None,
        description="Whether source meets Saudi PDPL requirements.",
    )
    license_type: Optional[str] = Field(
        default=None,
        description="Data license (e.g., 'proprietary', 'open-data', 'government-open').",
    )
    contact_email: Optional[str] = Field(
        default=None,
        description="Technical contact for this source.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Operational notes about this source.",
    )
