"""
Impact Observatory | مرصد الأثر
Signal Advisory Model — typed advisory output for v5 advisory-only mode.

A SignalAdvisory captures the result of interpreting a signal snapshot
in the context of a specific scenario. It is READ-ONLY:
  - metric_after MUST equal metric_before (no scoring)
  - scoring_applied MUST be False
  - It explains context — it does not change outcomes

This model is the contract between the advisory service and the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from src.signal_ingestion.models import SnapshotFreshness


@dataclass(frozen=True)
class SignalAdvisory:
    """An advisory interpretation of a signal snapshot for a scenario.

    Hard rules (enforced by advisory service):
      - metric_after == metric_before (always)
      - scoring_applied == False (always)
    """
    advisory_id: str
    scenario_id: str
    snapshot_id: str
    source_id: str
    confidence: float                        # 0.0–1.0 combined confidence
    freshness_status: SnapshotFreshness
    advisory_text: str                       # Human-readable advisory explanation
    risk_context: str                        # What the signal suggests about risk
    suggested_review: str                    # What the analyst should consider
    metric_before: float                     # Scenario metric at evaluation time
    metric_after: float                      # Must equal metric_before
    scoring_applied: bool                    # Must always be False
    fallback_used: bool                      # True if signal was low-confidence/stale
    timestamp: str                           # ISO-8601 evaluation time

    def to_dict(self) -> dict[str, Any]:
        return {
            "advisory_id": self.advisory_id,
            "scenario_id": self.scenario_id,
            "snapshot_id": self.snapshot_id,
            "source_id": self.source_id,
            "confidence": round(self.confidence, 4),
            "freshness_status": self.freshness_status.value,
            "advisory_text": self.advisory_text,
            "risk_context": self.risk_context,
            "suggested_review": self.suggested_review,
            "metric_before": round(self.metric_before, 6),
            "metric_after": round(self.metric_after, 6),
            "scoring_applied": self.scoring_applied,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp,
        }
