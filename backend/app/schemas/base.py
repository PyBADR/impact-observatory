"""Base schema for all Impact Observatory Pydantic v2 models.

Provides VersionedModel — a BaseModel subclass that adds schema_version
for audit traceability and contract evolution. All domain models that
participate in the observatory output contract should inherit from this.
"""

from pydantic import BaseModel, Field


class VersionedModel(BaseModel):
    """
    Base model for all IO schemas.

    Adds schema_version for audit traceability across pipeline stages.
    Frozen to prevent mutation after construction.
    """
    schema_version: str = Field(default="v1", frozen=True, description="Schema version identifier")

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
    }
