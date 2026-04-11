"""Replay Engine — re-run historical events through the current rule engine.

Flow:
  1. Load historical event from df_event_signals
  2. Load all active decision rules
  3. Match event against rule conditions
  4. Generate replayed decision outputs
  5. Persist replay run + results
  6. Optionally compare with stored actual outcome
  7. Return structured ReplayReport
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.models.outcome_tables import (
    ReplayRunORM,
    ReplayRunResultORM,
)
from src.data_foundation.models.tables import (
    DecisionRuleORM,
    EventSignalORM,
)
from src.data_foundation.repositories.actual_outcome_repo import ActualOutcomeRepository
from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
from src.data_foundation.repositories.replay_result_repo import ReplayResultRepository
from src.data_foundation.repositories.replay_run_repo import ReplayRunRepository
from src.data_foundation.repositories.rule_repo import RuleRepository
from src.data_foundation.schemas.outcome_schemas import (
    ReplayReport,
    ReplayRun,
    ReplayRunResult,
)

from sqlalchemy import select


def _uuid() -> str:
    return str(uuid4())


# ═══════════════════════════════════════════════════════════════════════════════
# Rule matching — deterministic condition evaluation
# ═══════════════════════════════════════════════════════════════════════════════

def _evaluate_condition(condition: dict, event_data: dict) -> bool:
    """Evaluate a single rule condition against event data.

    Condition format: {"field": str, "operator": str, "threshold": Any}
    Event data is a flat dict of field → value.
    """
    field = condition.get("field", "")
    operator = condition.get("operator", "")
    threshold = condition.get("threshold")
    value = event_data.get(field)

    if value is None:
        return False

    try:
        if operator == "gt":
            return float(value) > float(threshold)
        elif operator == "gte":
            return float(value) >= float(threshold)
        elif operator == "lt":
            return float(value) < float(threshold)
        elif operator == "lte":
            return float(value) <= float(threshold)
        elif operator == "eq":
            return str(value) == str(threshold)
        elif operator == "neq":
            return str(value) != str(threshold)
        elif operator == "in":
            return value in (threshold if isinstance(threshold, list) else [threshold])
        elif operator == "not_in":
            return value not in (threshold if isinstance(threshold, list) else [threshold])
        elif operator == "between":
            if isinstance(threshold, list) and len(threshold) == 2:
                return float(threshold[0]) <= float(value) <= float(threshold[1])
            return False
        elif operator in ("change_pct_gt", "change_pct_lt"):
            # Delta-based: check change_pct field
            change_val = event_data.get("change_pct", value)
            if operator == "change_pct_gt":
                return float(change_val) > float(threshold)
            return float(change_val) < float(threshold)
    except (TypeError, ValueError):
        return False

    return False


def match_rule_against_event(rule: DecisionRuleORM, event_data: dict) -> bool:
    """Check if a rule's conditions match the given event data.

    Respects condition_logic (AND / OR).
    """
    conditions = rule.conditions
    if not isinstance(conditions, list):
        return False
    if not conditions:
        return False

    logic = (rule.condition_logic or "AND").upper()
    results = [_evaluate_condition(c, event_data) for c in conditions]

    if logic == "OR":
        return any(results)
    return all(results)  # AND is default


def _check_scope(rule: DecisionRuleORM, event_data: dict) -> bool:
    """Check if the event falls within the rule's scope (country, sector, scenario)."""
    # Country check
    countries = rule.applicable_countries
    if countries and isinstance(countries, list):
        event_countries = event_data.get("countries_affected", [])
        if isinstance(event_countries, list):
            if not any(c in countries for c in event_countries):
                return False
        elif event_data.get("country"):
            if event_data["country"] not in countries:
                return False

    # Sector check
    sectors = rule.applicable_sectors
    if sectors and isinstance(sectors, list):
        event_sectors = event_data.get("sectors_affected", [])
        if isinstance(event_sectors, list):
            if not any(s in sectors for s in event_sectors):
                return False

    # Scenario check
    scenarios = rule.applicable_scenarios
    if scenarios and isinstance(scenarios, list):
        event_scenarios = event_data.get("scenario_ids", [])
        if isinstance(event_scenarios, list):
            if not any(s in scenarios for s in event_scenarios):
                return False

    return True


def _event_to_data(event: EventSignalORM) -> dict:
    """Flatten an event ORM object into a dict for rule matching."""
    data: Dict[str, Any] = {
        "event_id": event.event_id,
        "title": event.title,
        "category": event.category,
        "severity": event.severity,
        "severity_score": event.severity_score,
        "countries_affected": event.countries_affected or [],
        "sectors_affected": event.sectors_affected or [],
        "entity_ids_affected": event.entity_ids_affected or [],
        "scenario_ids": event.scenario_ids or [],
        "confidence_score": event.confidence_score,
        "is_ongoing": event.is_ongoing,
    }
    # Include raw_payload fields for condition matching
    if event.raw_payload and isinstance(event.raw_payload, dict):
        for k, v in event.raw_payload.items():
            if k not in data:
                data[k] = v
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# Replay Engine Service
# ═══════════════════════════════════════════════════════════════════════════════

class ReplayEngine:
    """Replays historical events through the current rule engine."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.run_repo = ReplayRunRepository(session)
        self.result_repo = ReplayResultRepository(session)
        self.rule_repo = RuleRepository(session)
        self.expected_repo = ExpectedOutcomeRepository(session)
        self.actual_repo = ActualOutcomeRepository(session)

    async def _load_event(self, event_id: str) -> EventSignalORM | None:
        stmt = select(EventSignalORM).where(EventSignalORM.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def run_replay(
        self,
        source_event_id: str,
        initiated_by: str,
        replay_reason: str | None = None,
    ) -> ReplayReport:
        """Execute a full replay of a historical event."""
        now = datetime.now(timezone.utc)

        # Determine replay version
        latest_version = await self.run_repo.get_latest_version(source_event_id)
        replay_version = latest_version + 1

        # Create replay run
        run_id = f"REPLAY-{_uuid()[:12]}"
        run_orm = ReplayRunORM(
            replay_run_id=run_id,
            source_event_id=source_event_id,
            replay_version=replay_version,
            initiated_by=initiated_by,
            replay_reason=replay_reason,
            started_at=now,
            replay_status="RUNNING",
        )
        await self.run_repo.create(run_orm)

        try:
            # Load the historical event
            event = await self._load_event(source_event_id)
            if event is None:
                run_orm.replay_status = "FAILED"
                run_orm.completed_at = datetime.now(timezone.utc)
                await self.session.flush()
                return ReplayReport(
                    replay_run=ReplayRun.model_validate(run_orm),
                    results=[],
                    comparison_available=False,
                )

            event_data = _event_to_data(event)

            # Load all active rules
            active_rules = await self.rule_repo.find_active()

            # Match rules against event
            matched_rules: List[DecisionRuleORM] = []
            for rule in active_rules:
                if _check_scope(rule, event_data) and match_rule_against_event(rule, event_data):
                    matched_rules.append(rule)

            # Build replayed decisions
            replayed_decisions: List[Dict[str, Any]] = []
            confidence_summary: Dict[str, float] = {}
            matched_rule_ids: List[str] = []

            for rule in matched_rules:
                matched_rule_ids.append(rule.rule_id)
                decision = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "action": rule.action,
                    "escalation_level": rule.escalation_level,
                    "condition_logic": rule.condition_logic,
                    "requires_human_approval": rule.requires_human_approval,
                }
                replayed_decisions.append(decision)
                confidence_summary[rule.rule_id] = event_data.get("confidence_score", 0.5)

            # Determine affected entities from the event
            replayed_entities = event_data.get("entity_ids_affected", [])

            # Check for existing actual outcome for comparison
            actual_outcome_id: Optional[str] = None
            evaluation_id: Optional[str] = None
            comparison_available = False
            comparison_summary: Optional[Dict[str, Any]] = None

            expected_outcomes = await self.expected_repo.find_by_event(source_event_id)
            if expected_outcomes:
                for eo in expected_outcomes:
                    actual = await self.actual_repo.find_by_expected_outcome(eo.expected_outcome_id)
                    if actual:
                        actual_outcome_id = actual.actual_outcome_id
                        comparison_available = True
                        # Build comparison summary
                        original_rule_ids = [eo.rule_id for eo in expected_outcomes]
                        comparison_summary = {
                            "original_matched_rules": original_rule_ids,
                            "replay_matched_rules": matched_rule_ids,
                            "rules_added": [r for r in matched_rule_ids if r not in original_rule_ids],
                            "rules_removed": [r for r in original_rule_ids if r not in matched_rule_ids],
                            "original_severity": expected_outcomes[0].expected_severity if expected_outcomes else None,
                            "observed_severity": actual.observed_severity,
                        }
                        break

            # Persist replay result
            result_id = f"RR-{_uuid()[:12]}"
            result_orm = ReplayRunResultORM(
                replay_result_id=result_id,
                replay_run_id=run_id,
                event_id=source_event_id,
                matched_rule_ids=matched_rule_ids,
                replayed_entities=replayed_entities,
                replayed_decisions=replayed_decisions,
                replayed_confidence_summary=confidence_summary,
                actual_outcome_id=actual_outcome_id,
                evaluation_id=evaluation_id,
            )
            await self.result_repo.create(result_orm)

            # Mark run completed
            run_orm.replay_status = "COMPLETED"
            run_orm.completed_at = datetime.now(timezone.utc)
            await self.session.flush()

            return ReplayReport(
                replay_run=ReplayRun.model_validate(run_orm),
                results=[ReplayRunResult.model_validate(result_orm)],
                comparison_available=comparison_available,
                comparison_summary=comparison_summary,
            )

        except Exception:
            run_orm.replay_status = "FAILED"
            run_orm.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
            raise

    async def get_replay(self, replay_run_id: str) -> ReplayReport | None:
        """Load a completed replay run with its results."""
        run = await self.run_repo.get_by_pk(replay_run_id)
        if run is None:
            return None

        results_orm = await self.result_repo.find_by_run(replay_run_id)
        results = [ReplayRunResult.model_validate(r) for r in results_orm]

        return ReplayReport(
            replay_run=ReplayRun.model_validate(run),
            results=results,
            comparison_available=any(r.actual_outcome_id for r in results),
        )
