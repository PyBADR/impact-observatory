"""Impact Observatory | مرصد الأثر — Versioned Base Model.

All schemas inherit from this base to include schema_version for audit trail.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VersionedModel(BaseModel):
    """Base for all Impact Observatory schemas.

    Adds schema_version field for audit trail and API versioning.
    When cutting v2, change the default here — all schemas update automatically.
    """

    schema_version: str = Field(default="v1", description="Schema version for audit trail")

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
    )
