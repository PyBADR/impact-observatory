"""Macro Decision Service — Pack 3 service wrapper.

Thin service layer over the Pack 3 impact + decision pipeline:
  PropagationResult → MacroImpact → DecisionOutput

Responsibilities:
  - Accept a PropagationResult and return a DecisionOutput
  - Cache results in-memory by signal_id for repeated lookups
  - Expose MacroImpact separately for callers that need the intermediate result
  - Follow the singleton + dependency-injection pattern of causal_service.py

This service does NOT contain impact or decision logic — it delegates to:
  src.macro.impact.impact_engine.compute_impact()
  src.macro.decision.decision_engine.map_impact_to_decision()
"""

from __future__ import annotations

import logging
from uuid import UUID

from src.macro.impact.impact_engine import compute_impact
from src.macro.impact.impact_models import MacroImpact
from src.macro.decision.decision_engine import map_impact_to_decision
from src.macro.decision.decision_models import DecisionOutput
from src.macro.propagation.propagation_schemas import PropagationResult

logger = logging.getLogger("services.macro_decision")


# ── Result Stores ─────────────────────────────────────────────────────────────

class ImpactResultStore:
    """In-memory store for MacroImpact results, keyed by signal_id."""

    def __init__(self) -> None:
        self._impacts: dict[UUID, MacroImpact] = {}

    @property
    def size(self) -> int:
        return len(self._impacts)

    def get(self, signal_id: UUID) -> MacroImpact | None:
        return self._impacts.get(signal_id)

    def put(self, signal_id: UUID, impact: MacroImpact) -> None:
        self._impacts[signal_id] = impact

    def all(self) -> list[MacroImpact]:
        return list(self._impacts.values())

    def clear(self) -> None:
        self._impacts.clear()


class DecisionResultStore:
    """In-memory store for DecisionOutput results, keyed by signal_id."""

    def __init__(self) -> None:
        self._decisions: dict[UUID, DecisionOutput] = {}

    @property
    def size(self) -> int:
        return len(self._decisions)

    def get(self, signal_id: UUID) -> DecisionOutput | None:
        return self._decisions.get(signal_id)

    def put(self, signal_id: UUID, decision: DecisionOutput) -> None:
        self._decisions[signal_id] = decision

    def all(self) -> list[DecisionOutput]:
        return list(self._decisions.values())

    def clear(self) -> None:
        self._decisions.clear()


# ── Service ───────────────────────────────────────────────────────────────────

class MacroDecisionService:
    """Service wrapper for the Pack 3 impact + decision pipeline.

    Usage:
        svc = MacroDecisionService()

        # Full pipeline
        decision = svc.run(propagation_result)

        # Intermediate access
        impact = svc.get_impact(signal_id)
        decision = svc.get_decision(signal_id)

    Thread safety: single-process FastAPI only (no lock needed).
    For multi-process deployments, replace stores with a shared cache.
    """

    def __init__(self) -> None:
        self._impacts = ImpactResultStore()
        self._decisions = DecisionResultStore()

    # ── Full pipeline ──────────────────────────────────────────────────────────

    def run(self, propagation_result: PropagationResult) -> DecisionOutput:
        """Run the full PropagationResult → MacroImpact → DecisionOutput pipeline.

        Results are cached by signal_id. Repeated calls for the same signal_id
        return the cached result without recomputing.

        Args:
            propagation_result: Output from the propagation engine.

        Returns:
            DecisionOutput — always valid.
        """
        sid = propagation_result.signal_id

        # Return cached decision if available
        existing = self._decisions.get(sid)
        if existing is not None:
            logger.debug("MacroDecisionService.run: cache hit for signal %s", sid)
            return existing

        # Compute impact
        impact = compute_impact(propagation_result)
        self._impacts.put(sid, impact)
        logger.info(
            "MacroDecisionService: computed impact for signal %s — "
            "severity=%s, domains=%d",
            sid, impact.overall_severity_level.value, impact.total_domains_reached,
        )

        # Compute decision
        decision = map_impact_to_decision(impact)
        self._decisions.put(sid, decision)
        logger.info(
            "MacroDecisionService: computed decision for signal %s — "
            "priority=%s, actions=%d, escalation=%s",
            sid, decision.priority.value,
            len(decision.recommended_actions), decision.requires_escalation,
        )

        return decision

    # ── Step-by-step accessors ─────────────────────────────────────────────────

    def compute_impact_only(self, propagation_result: PropagationResult) -> MacroImpact:
        """Compute and cache only the MacroImpact (skip decision step).

        Useful when the caller needs the intermediate impact without a decision.
        """
        sid = propagation_result.signal_id
        existing = self._impacts.get(sid)
        if existing is not None:
            return existing
        impact = compute_impact(propagation_result)
        self._impacts.put(sid, impact)
        return impact

    # ── Lookups ────────────────────────────────────────────────────────────────

    def get_impact(self, signal_id: UUID) -> MacroImpact | None:
        """Return cached MacroImpact for signal_id, or None."""
        return self._impacts.get(signal_id)

    def get_decision(self, signal_id: UUID) -> DecisionOutput | None:
        """Return cached DecisionOutput for signal_id, or None."""
        return self._decisions.get(signal_id)

    def list_impacts(self) -> list[MacroImpact]:
        return self._impacts.all()

    def list_decisions(self) -> list[DecisionOutput]:
        return self._decisions.all()

    # ── Stats ──────────────────────────────────────────────────────────────────

    @property
    def impact_count(self) -> int:
        return self._impacts.size

    @property
    def decision_count(self) -> int:
        return self._decisions.size

    def clear(self) -> None:
        """Clear all cached results. Primarily for tests."""
        self._impacts.clear()
        self._decisions.clear()


# ── Singleton + FastAPI DI ────────────────────────────────────────────────────

_service_instance: MacroDecisionService | None = None


def get_macro_decision_service() -> MacroDecisionService:
    """Return the module-level singleton MacroDecisionService.

    Thread-safe for single-process FastAPI. Resettable for tests by
    setting `src.services.macro_decision_service._service_instance = None`.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = MacroDecisionService()
    return _service_instance
