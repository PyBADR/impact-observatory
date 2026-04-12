"""
Dataset A: Dataset Registry
============================

Catalog of all datasets in the Impact Observatory data platform.
Each record describes a dataset's purpose, schema location, owner,
refresh cadence, and build priority.

KG Mapping: (:Dataset) node
Consumers: Data catalog UI, ingestion scheduler, lineage tracker
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    DatasetPriority,
    DatasetStatus,
    IngestionFrequency,
    Sector,
)

__all__ = ["DatasetRegistryEntry"]


class DatasetRegistryEntry(FoundationModel):
    """A registered dataset in the Impact Observatory platform."""

    dataset_id: str = Field(
        ...,
        description="Unique dataset identifier (e.g., 'p1_macro_indicators').",
        examples=["p1_macro_indicators", "p1_banking_sector_profiles"],
    )
    dataset_name: str = Field(
        ...,
        description="Human-readable dataset name.",
        examples=["GCC Macro Indicators"],
    )
    dataset_name_ar: Optional[str] = Field(
        default=None,
        description="Arabic dataset name.",
        examples=["مؤشرات الاقتصاد الكلي لدول الخليج"],
    )
    description: str = Field(
        ...,
        description="What this dataset contains and why it exists.",
    )
    priority: DatasetPriority = Field(
        ...,
        description="Build priority phase.",
    )
    status: DatasetStatus = Field(
        default=DatasetStatus.DRAFT,
        description="Current lifecycle status.",
    )
    owner: str = Field(
        ...,
        description="Team or person responsible for this dataset.",
        examples=["data-engineering", "macro-intelligence-team"],
    )
    schema_module: str = Field(
        ...,
        description="Python module path to the Pydantic schema.",
        examples=["src.data_foundation.schemas.macro_indicators"],
    )
    primary_sectors: List[Sector] = Field(
        default_factory=list,
        description="Sectors this dataset primarily serves.",
    )
    ingestion_frequency: IngestionFrequency = Field(
        default=IngestionFrequency.ON_DEMAND,
        description="Expected refresh cadence.",
    )
    source_ids: List[str] = Field(
        default_factory=list,
        description="IDs of sources feeding this dataset (FK to source_registry).",
    )
    row_count_estimate: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated row count at steady state.",
    )
    retention_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Data retention policy in days. Null = indefinite.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Searchable tags for catalog discovery.",
    )
