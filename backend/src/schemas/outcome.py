"""
Outcome Tracking Schema — C5 Activation Layer.

Tracks what ACTUALLY happened after a decision was made,
enabling a feedback loop back into ROI computation and
future decision confidence calibration.

Architecture Layer: Governance (C5 feedback loop)
Data Flow: DecisionObject → OutcomeRecord → ROI feedback → confidence recalibration
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OutcomeStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    PARTIALLY_CONFIRMED = "PARTIALLY_CONFIRMED"
    EXPIRED = "EXPIRED"


class OutcomeRecord(BaseModel):
    """Single outcome observation for a decision."""

    outcome_id: str = Field(..., description="Unique outcome ID, e.g. OUT-001")
    decision_id: str = Field(..., description="Linked decision ID, e.g. DEC-001")
    scenario_id: str = Field(..., description="Originating scenario")
    run_id: str = Field(default="", description="Run that generated the decision")

    # Status lifecycle
    status: OutcomeStatus = Field(default=OutcomeStatus.PENDING)

    # Value tracking
    expected_value_usd: float = Field(default=0.0, description="Predicted loss avoided")
    real_value_usd: float = Field(default=0.0, description="Actually observed value")
    value_delta_usd: float = Field(default=0.0, description="real - expected")

    # Confidence feedback
    predicted_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    actual_accuracy: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How accurate was the prediction (0=wrong, 1=exact)"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confirmed_at: Optional[datetime] = Field(default=None)

    # Evidence
    notes: str = Field(default="", description="Analyst notes on outcome")
    evidence_sources: list[str] = Field(default_factory=list)

    @field_validator("value_delta_usd", mode="before")
    @classmethod
    def compute_delta(cls, v, info):
        data = info.data
        if v == 0.0 and "real_value_usd" in data and "expected_value_usd" in data:
            return data["real_value_usd"] - data["expected_value_usd"]
        return v


class OutcomeStore(BaseModel):
    """In-memory outcome store with scenario-scoped feedback."""

    outcomes: dict[str, OutcomeRecord] = Field(
        default_factory=dict,
        description="outcome_id → record"
    )

    def record_outcome(self, outcome: OutcomeRecord) -> None:
        """Record a new outcome observation."""
        self.outcomes[outcome.outcome_id] = outcome

    def confirm(
        self, outcome_id: str, real_value_usd: float, notes: str = ""
    ) -> Optional[OutcomeRecord]:
        """Confirm an outcome with the real observed value."""
        rec = self.outcomes.get(outcome_id)
        if not rec:
            return None
        rec.status = OutcomeStatus.CONFIRMED
        rec.real_value_usd = real_value_usd
        rec.value_delta_usd = real_value_usd - rec.expected_value_usd
        rec.confirmed_at = datetime.now(timezone.utc)
        if notes:
            rec.notes = notes
        # Compute accuracy: how close was prediction to reality
        if rec.expected_value_usd != 0:
            ratio = min(abs(real_value_usd), abs(rec.expected_value_usd)) / max(
                abs(real_value_usd), abs(rec.expected_value_usd), 1.0
            )
            rec.actual_accuracy = max(0.0, min(1.0, ratio))
        return rec

    def reject(
        self, outcome_id: str, notes: str = ""
    ) -> Optional[OutcomeRecord]:
        """Reject an outcome (prediction was wrong)."""
        rec = self.outcomes.get(outcome_id)
        if not rec:
            return None
        rec.status = OutcomeStatus.REJECTED
        rec.confirmed_at = datetime.now(timezone.utc)
        if notes:
            rec.notes = notes
        return rec

    def get_roi_feedback(self, scenario_id: str) -> dict:
        """Compute ROI feedback for a specific scenario from confirmed outcomes."""
        confirmed = [
            o for o in self.outcomes.values()
            if o.scenario_id == scenario_id and o.status == OutcomeStatus.CONFIRMED
        ]
        if not confirmed:
            return {
                "scenario_id": scenario_id,
                "confirmed_count": 0,
                "total_delta_usd": 0.0,
                "avg_accuracy": 0.0,
                "total_expected_usd": 0.0,
                "total_real_usd": 0.0,
            }

        total_delta = sum(o.value_delta_usd for o in confirmed)
        avg_accuracy = sum(o.actual_accuracy for o in confirmed) / len(confirmed)

        return {
            "scenario_id": scenario_id,
            "confirmed_count": len(confirmed),
            "total_delta_usd": round(total_delta, 2),
            "avg_accuracy": round(avg_accuracy, 4),
            "total_expected_usd": round(
                sum(o.expected_value_usd for o in confirmed), 2
            ),
            "total_real_usd": round(sum(o.real_value_usd for o in confirmed), 2),
        }
