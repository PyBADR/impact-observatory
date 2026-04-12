"""
Evaluation Layer — Replay Engine
==================================

Replays a historical data state through the current (or specified) rule set.
Produces deterministic results: same DataState + same rules → same output.

The replay engine is a pure function pipeline:
  1. Accept frozen DataState and rule list
  2. Evaluate every rule against the DataState
  3. Compare results against original decisions (if provided)
  4. Return ReplayRun + List[ReplayRunResult]

No DB access in core replay — callers handle persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from src.data_foundation.decision.rule_engine import (
    DataState,
    RuleEvaluationResult,
    RuleEngineOutput,
    evaluate_all_rules,
)
from src.data_foundation.schemas.decision_rules import DecisionRule

from .schemas import (
    ReplayRun,
    ReplayRunResult,
    ReplayStatus,
    RuleSetSource,
)

__all__ = [
    "replay_event",
    "compare_replay_to_original",
]


def replay_event(
    data_state: DataState,
    rules: List[DecisionRule],
    initiated_by: str,
    original_decision_log_id: Optional[str] = None,
    original_event_id: Optional[str] = None,
    replay_scenario_id: Optional[str] = None,
    rule_set_source: str = RuleSetSource.CURRENT_ACTIVE,
    original_triggered_rule_ids: Optional[Dict[str, bool]] = None,
) -> Tuple[ReplayRun, List[ReplayRunResult]]:
    """Replay a historical data state through a rule set.

    This is the core replay function. It is deterministic:
    same data_state + same rules → same results.

    Args:
        data_state: Frozen DataState to replay.
        rules: List of DecisionRules to evaluate.
        initiated_by: Who triggered the replay.
        original_decision_log_id: If replaying a specific past decision.
        original_event_id: If replaying a specific event signal.
        replay_scenario_id: If replaying a scenario.
        rule_set_source: Where the rules came from.
        original_triggered_rule_ids: Map of rule_id → triggered (bool)
            from the original run. Used for divergence detection.

    Returns:
        (ReplayRun, List[ReplayRunResult])
    """
    # Build rule set snapshot
    rule_snapshot = {
        r.rule_id: {"version": r.version, "is_active": r.is_active}
        for r in rules
    }

    # Create ReplayRun
    replay_run = ReplayRun(
        original_decision_log_id=original_decision_log_id,
        original_event_id=original_event_id,
        replay_data_state=data_state.values,
        rule_set_snapshot=rule_snapshot,
        rule_set_source=rule_set_source,
        replay_scenario_id=replay_scenario_id,
        initiated_by=initiated_by,
        status=ReplayStatus.RUNNING,
    )
    replay_run.compute_hashes()

    # Execute replay — no cooldown enforcement (replays ignore cooldown)
    try:
        engine_output: RuleEngineOutput = evaluate_all_rules(
            rules=rules,
            data_state=data_state,
            last_trigger_times=None,  # No cooldown for replays
        )
    except Exception as exc:
        replay_run.status = ReplayStatus.FAILED
        replay_run.error_message = str(exc)
        replay_run.completed_at = datetime.now(timezone.utc)
        return replay_run, []

    # Build per-rule results
    results: List[ReplayRunResult] = []

    for eval_result in engine_output.evaluations:
        # Determine if this matches the original
        matches = None
        divergence_reason = None

        if original_triggered_rule_ids is not None:
            original_triggered = original_triggered_rule_ids.get(eval_result.rule_id)
            if original_triggered is not None:
                matches = eval_result.triggered == original_triggered
                if not matches:
                    if eval_result.triggered and not original_triggered:
                        divergence_reason = (
                            "Rule triggers now but did NOT trigger in original. "
                            "Possible cause: rule conditions changed, thresholds adjusted, "
                            "or exclusions modified."
                        )
                    elif not eval_result.triggered and original_triggered:
                        divergence_reason = (
                            "Rule does NOT trigger now but DID trigger in original. "
                            "Possible cause: new exclusions added, thresholds tightened, "
                            "or rule deactivated."
                        )

        result = ReplayRunResult(
            replay_run_id=replay_run.replay_run_id,
            rule_id=eval_result.rule_id,
            rule_version=eval_result.rule_version,
            triggered=eval_result.triggered,
            cooldown_blocked=eval_result.cooldown_blocked,
            action=eval_result.action.value if eval_result.action else None,
            conditions_met=eval_result.conditions_met,
            condition_details=eval_result.condition_details,
            matches_original=matches,
            divergence_reason=divergence_reason,
        )
        result.compute_hash()
        results.append(result)

    # Mark complete
    replay_run.status = ReplayStatus.COMPLETED
    replay_run.completed_at = datetime.now(timezone.utc)

    return replay_run, results


def compare_replay_to_original(
    replay_results: List[ReplayRunResult],
) -> Dict[str, any]:
    """Produce a summary comparison of replay vs original.

    Returns a dict with:
      - total_rules: int
      - total_matching: int
      - total_divergent: int
      - total_unknown: int (no original to compare)
      - divergent_rules: List[dict] with rule_id and reason
      - match_rate: float [0-1] (among those with comparison data)
    """
    total = len(replay_results)
    matching = 0
    divergent = 0
    unknown = 0
    divergent_rules = []

    for r in replay_results:
        if r.matches_original is None:
            unknown += 1
        elif r.matches_original:
            matching += 1
        else:
            divergent += 1
            divergent_rules.append({
                "rule_id": r.rule_id,
                "triggered_in_replay": r.triggered,
                "divergence_reason": r.divergence_reason,
            })

    comparable = matching + divergent
    match_rate = matching / comparable if comparable > 0 else 1.0

    return {
        "total_rules": total,
        "total_matching": matching,
        "total_divergent": divergent,
        "total_unknown": unknown,
        "divergent_rules": divergent_rules,
        "match_rate": round(match_rate, 4),
    }
