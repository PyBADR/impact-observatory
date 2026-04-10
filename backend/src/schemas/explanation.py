"""Schema 11: ExplanationPack — bilingual causal chain explanation."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class CausalStep(VersionedModel):
    """One step in the causal chain."""
    step: int
    entity_id: str
    entity_label: str
    entity_label_ar: str | None = None
    event: str
    event_ar: str | None = None
    impact_usd: float = 0.0
    stress_delta: float = 0.0
    mechanism: str = Field("", description="How this step propagates")


class ExplanationPack(VersionedModel):
    """Full explainability output for a run."""
    run_id: str
    scenario_label: str | None = None
    narrative_en: str = Field("", description="English narrative summary")
    narrative_ar: str = Field("", description="Arabic narrative summary")
    causal_chain: list[CausalStep] = Field(default_factory=list)
    total_steps: int = 0
    headline_loss_usd: float = 0.0
    peak_day: int = 0
    confidence: float = 0.5
    methodology: str = Field("deterministic_propagation", description="Model methodology used")
