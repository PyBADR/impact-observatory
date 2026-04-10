"""
Impact Observatory | مرصد الأثر
Outcome Tracking + Trust Memory + Confidence Adjustment
Sprint 2, Phases 3-5 of Decision Reliability Layer.

Phase 3 (Outcome Tracking):
  Store predicted values at decision time.
  Allow update with actual outcomes.
  Compute deviation = actual - predicted.

Phase 4 (Trust Memory):
  Maintain per-action success/failure counts.
  Compute trust_score from success rate + average deviation.

Phase 5 (Confidence Adjustment):
  Adjust Sprint 1.5 confidence using trust memory.
  Poor track record → lower confidence.

Storage: in-memory dict (per-process). Production would use PostgreSQL.
Thread-safe via simple locking since FastAPI is single-process in dev.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# In-Memory Storage
# ═══════════════════════════════════════════════════════════════════════════════

_lock = threading.Lock()

# outcome_store: { "run_id::action_id" → OutcomeRecord }
_outcome_store: dict[str, dict] = {}

# trust_memory_store: { "action_template_key" → TrustMemory }
# action_template_key = f"{scenario_type}::{sector}::{action_hash}"
_trust_memory_store: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Outcome Record Contract
# ═══════════════════════════════════════════════════════════════════════════════

def _outcome_record(
    action_id: str,
    scenario_id: str,
    predicted_value: float,
    actual_value: float | None = None,
    deviation: float | None = None,
    status: str = "PENDING",
    timestamp: str | None = None,
) -> dict:
    """Build an OutcomeRecord dict."""
    assert status in ("PENDING", "CONFIRMED", "FAILED"), f"Invalid status: {status}"
    return {
        "action_id": action_id,
        "scenario_id": scenario_id,
        "predicted_value": round(predicted_value, 2),
        "actual_value": round(actual_value, 2) if actual_value is not None else None,
        "deviation": round(deviation, 2) if deviation is not None else None,
        "deviation_pct": round((deviation / max(abs(predicted_value), 1)) * 100, 1) if deviation is not None and predicted_value != 0 else None,
        "status": status,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }


def store_prediction(
    run_id: str,
    action_id: str,
    scenario_id: str,
    predicted_loss_avoided: float,
) -> dict:
    """Store a prediction at decision time. Returns the OutcomeRecord."""
    key = f"{run_id}::{action_id}"
    record = _outcome_record(
        action_id=action_id,
        scenario_id=scenario_id,
        predicted_value=predicted_loss_avoided,
        status="PENDING",
    )
    with _lock:
        _outcome_store[key] = record
    logger.info("Stored prediction: %s → %s", key, predicted_loss_avoided)
    return record


def update_outcome(
    run_id: str,
    action_id: str,
    actual_value: float,
    status: str = "CONFIRMED",
) -> dict | None:
    """Update an existing prediction with actual outcome.

    Returns updated OutcomeRecord or None if not found.
    """
    key = f"{run_id}::{action_id}"
    with _lock:
        record = _outcome_store.get(key)
        if record is None:
            logger.warning("Outcome record not found: %s", key)
            return None

        record["actual_value"] = round(actual_value, 2)
        record["deviation"] = round(actual_value - record["predicted_value"], 2)
        if record["predicted_value"] != 0:
            record["deviation_pct"] = round(
                (record["deviation"] / abs(record["predicted_value"])) * 100, 1
            )
        record["status"] = status
        record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Update trust memory
        _update_trust_memory(record)

    logger.info("Updated outcome: %s → actual=%s, deviation=%s", key, actual_value, record["deviation"])
    return record


def get_outcome(run_id: str, action_id: str) -> dict | None:
    """Retrieve an outcome record."""
    key = f"{run_id}::{action_id}"
    with _lock:
        return _outcome_store.get(key)


def get_all_outcomes(run_id: str) -> list[dict]:
    """Retrieve all outcomes for a given run."""
    prefix = f"{run_id}::"
    with _lock:
        return [v for k, v in _outcome_store.items() if k.startswith(prefix)]


def build_outcome_records(run_id: str, result: dict) -> list[dict]:
    """
    Build OutcomeRecords for all actions in a simulation result.
    Stores predictions and returns the records.

    Called during pipeline execution (stage 41c).
    """
    scenario_id = result.get("scenario_id", "unknown")
    decision_plan = result.get("decision_plan", {})
    actions = decision_plan.get("actions", [])
    if not actions:
        actions = result.get("actions", [])

    records: list[dict] = []
    for action in actions:
        action_id = action.get("action_id", "")
        predicted = action.get("loss_avoided_usd", 0)
        record = store_prediction(run_id, action_id, scenario_id, predicted)
        records.append(record)

    logger.info("Built %d outcome records for run %s", len(records), run_id)
    return records


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Trust Memory
# ═══════════════════════════════════════════════════════════════════════════════

def _action_template_key(record: dict) -> str:
    """Generate a stable key for an action template (across runs)."""
    # Use action_id prefix (e.g., "ACT-001") + scenario_id
    action_prefix = record.get("action_id", "").split("-")[0] if "-" in record.get("action_id", "") else record.get("action_id", "")
    return f"{record.get('scenario_id', 'unknown')}::{action_prefix}"


def _trust_memory(
    action_id: str,
    total_runs: int,
    success_count: int,
    failure_count: int,
    average_deviation: float,
    trust_score: int,
) -> dict:
    return {
        "action_id": action_id,
        "total_runs": total_runs,
        "success_count": success_count,
        "failure_count": failure_count,
        "average_deviation": round(average_deviation, 2),
        "trust_score": max(0, min(100, trust_score)),
    }


def _compute_trust_score(success_rate: float, avg_deviation_pct: float) -> int:
    """
    Compute trust score from success rate and deviation history.

    trust_score = 60 × success_rate + 40 × accuracy_factor
    where accuracy_factor = max(0, 1 - |avg_deviation_pct| / 50)

    Perfect: 100% success + 0% deviation → 100
    50% success + 25% deviation → 30 + 20 = 50
    0% success → 0 + accuracy bonus (up to 40)
    """
    accuracy_factor = max(0.0, 1.0 - abs(avg_deviation_pct) / 50.0)
    score = 60.0 * success_rate + 40.0 * accuracy_factor
    return max(0, min(100, int(round(score))))


def _update_trust_memory(record: dict) -> None:
    """Update trust memory after outcome confirmation. Called under _lock."""
    key = _action_template_key(record)
    memory = _trust_memory_store.get(key)

    is_success = record["status"] == "CONFIRMED" and record.get("deviation_pct") is not None and abs(record["deviation_pct"]) <= 25
    deviation_pct = record.get("deviation_pct", 0) or 0

    if memory is None:
        _trust_memory_store[key] = _trust_memory(
            action_id=record["action_id"],
            total_runs=1,
            success_count=1 if is_success else 0,
            failure_count=0 if is_success else 1,
            average_deviation=deviation_pct,
            trust_score=_compute_trust_score(1.0 if is_success else 0.0, deviation_pct),
        )
    else:
        memory["total_runs"] += 1
        if is_success:
            memory["success_count"] += 1
        else:
            memory["failure_count"] += 1

        # Running average deviation
        n = memory["total_runs"]
        memory["average_deviation"] = round(
            (memory["average_deviation"] * (n - 1) + deviation_pct) / n, 2
        )

        success_rate = memory["success_count"] / max(memory["total_runs"], 1)
        memory["trust_score"] = _compute_trust_score(success_rate, memory["average_deviation"])
        memory["action_id"] = record["action_id"]  # latest action_id


def get_trust_memory(action_id: str, scenario_id: str) -> dict | None:
    """Retrieve trust memory for an action template."""
    # Try exact key
    prefix = action_id.split("-")[0] if "-" in action_id else action_id
    key = f"{scenario_id}::{prefix}"
    with _lock:
        return _trust_memory_store.get(key)


def get_all_trust_memories() -> dict[str, dict]:
    """Retrieve all trust memories."""
    with _lock:
        return dict(_trust_memory_store)


def build_trust_memories_for_run(result: dict) -> list[dict]:
    """
    Build TrustMemory lookups for all actions in a simulation result.
    Returns existing trust memories (from previous runs).

    Called during pipeline execution (stage 41d).
    """
    scenario_id = result.get("scenario_id", "unknown")
    decision_plan = result.get("decision_plan", {})
    actions = decision_plan.get("actions", [])
    if not actions:
        actions = result.get("actions", [])

    memories: list[dict] = []
    for action in actions:
        action_id = action.get("action_id", "")
        memory = get_trust_memory(action_id, scenario_id)
        if memory:
            memories.append(memory)
        else:
            # No history yet — create a default
            memories.append(_trust_memory(
                action_id=action_id,
                total_runs=0,
                success_count=0,
                failure_count=0,
                average_deviation=0,
                trust_score=50,  # neutral default
            ))

    return memories


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5: Confidence Adjustment
# ═══════════════════════════════════════════════════════════════════════════════

def adjust_confidence(
    base_confidence: int,
    trust_score: int,
    total_runs: int,
) -> tuple[int, str]:
    """
    Adjust metric/action confidence based on trust memory.

    Logic:
      - If no history (total_runs == 0): return base_confidence unchanged
      - If trust_score >= 80: boost by +5
      - If trust_score >= 60: no change
      - If trust_score >= 40: penalize by -10
      - If trust_score < 40: penalize by -20

    The penalty/boost scales with history depth:
      - < 3 runs: half-weight adjustment (insufficient data)
      - >= 3 runs: full-weight adjustment

    Returns: (adjusted_confidence, reason_string)
    """
    if total_runs == 0:
        return base_confidence, "No historical data — base confidence unchanged"

    # Compute raw adjustment
    if trust_score >= 80:
        adjustment = +5
        reason_base = f"Strong track record (trust score {trust_score}/100 over {total_runs} runs)"
    elif trust_score >= 60:
        adjustment = 0
        reason_base = f"Adequate track record (trust score {trust_score}/100 over {total_runs} runs)"
    elif trust_score >= 40:
        adjustment = -10
        reason_base = f"Mixed track record (trust score {trust_score}/100 over {total_runs} runs)"
    else:
        adjustment = -20
        reason_base = f"Poor track record (trust score {trust_score}/100 over {total_runs} runs)"

    # Scale by history depth
    if total_runs < 3:
        adjustment = adjustment // 2
        reason_base += " — limited history, half-weight adjustment"

    adjusted = max(5, min(99, base_confidence + adjustment))

    if adjustment > 0:
        reason = f"↑ Confidence boosted: {reason_base}"
    elif adjustment < 0:
        reason = f"↓ Confidence reduced: {reason_base}"
    else:
        reason = f"= Confidence stable: {reason_base}"

    return adjusted, reason


def build_confidence_adjustments(
    metric_explanations: list[dict],
    trust_memories: list[dict],
) -> list[dict]:
    """
    Apply confidence adjustments to all metric explanations based on trust memory.

    Returns list of ConfidenceAdjustment dicts:
      { metric_id, original_confidence, adjusted_confidence, adjustment_reason }
    """
    # Build average trust score across all action memories
    if trust_memories:
        valid_memories = [m for m in trust_memories if m["total_runs"] > 0]
        if valid_memories:
            avg_trust = sum(m["trust_score"] for m in valid_memories) / len(valid_memories)
            avg_runs = sum(m["total_runs"] for m in valid_memories) / len(valid_memories)
        else:
            avg_trust = 50
            avg_runs = 0
    else:
        avg_trust = 50
        avg_runs = 0

    adjustments: list[dict] = []
    for exp in metric_explanations:
        metric_id = exp.get("metric_id", "")
        original = exp.get("confidence", 75)

        adjusted, reason = adjust_confidence(original, int(avg_trust), int(avg_runs))

        adjustments.append({
            "metric_id": metric_id,
            "original_confidence": original,
            "adjusted_confidence": adjusted,
            "adjustment_reason": reason,
        })

    return adjustments


# ═══════════════════════════════════════════════════════════════════════════════
# Store management (for testing)
# ═══════════════════════════════════════════════════════════════════════════════

def clear_stores() -> None:
    """Clear all in-memory stores. For testing only."""
    with _lock:
        _outcome_store.clear()
        _trust_memory_store.clear()
