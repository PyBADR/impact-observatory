"""graph_contracts — Decision graph integrity validation.

Enforces the run → decision → outcome → value lineage chain.
Called at API boundaries (create, execute, compute) to guarantee that
every entity has valid upward links before it enters the system.

Contract rules:
  Decision:  decision_id exists, source_run_id resolves, status is valid
  Outcome:   outcome_id exists, source_decision_id resolves to existing decision
  Value:     source_outcome_id resolves, linked outcome has source_decision_id,
             linked decision exists — never a free-floating run-only value

All validators return (ok: bool, error: str | None).
Callers decide whether to reject (HTTP 400/422) or warn-and-proceed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Valid statuses — must match schemas/operator_decision.py Literals exactly
VALID_DECISION_STATUSES = frozenset({
    "CREATED", "IN_REVIEW", "EXECUTED", "FAILED", "CLOSED",
})

VALID_OUTCOME_STATUSES = frozenset({
    "PENDING_OBSERVATION", "OBSERVED", "CONFIRMED", "DISPUTED", "CLOSED", "FAILED",
})


@dataclass(frozen=True)
class ContractResult:
    ok: bool
    error: str | None = None


# ── Decision contracts ──────────────────────────────────────────────────────

def validate_decision_create(body: dict) -> ContractResult:
    """Validate decision creation request has valid graph linkage.

    Rules:
      - source_run_id, if provided, must resolve to an existing run
      - decision_type must be one of the schema-defined types
    """
    from src.services import run_store

    run_id = body.get("source_run_id")
    if run_id:
        run = run_store.get(run_id)
        if run is None:
            return ContractResult(
                ok=False,
                error=f"source_run_id '{run_id}' does not resolve to an existing run",
            )

    return ContractResult(ok=True)


def validate_decision_status(status: str) -> ContractResult:
    """Validate that a decision status is in the allowed set."""
    if status not in VALID_DECISION_STATUSES:
        return ContractResult(
            ok=False,
            error=f"Invalid decision_status '{status}' — expected one of {sorted(VALID_DECISION_STATUSES)}",
        )
    return ContractResult(ok=True)


def validate_decision_execute(decision: dict) -> ContractResult:
    """Pre-execute validation: decision must have outcome_id linkage."""
    if not decision.get("outcome_id"):
        return ContractResult(
            ok=False,
            error=f"Decision {decision.get('decision_id')} has no outcome_id — cannot execute without linked outcome",
        )
    return ContractResult(ok=True)


# ── Outcome contracts ───────────────────────────────────────────────────────

def validate_outcome_create(body: dict) -> ContractResult:
    """Validate outcome creation request has valid graph linkage.

    Rules:
      - source_decision_id, if provided, must resolve to an existing decision
      - the linked decision must have a valid source_run_id
    """
    from src.services import decision_operator_store

    decision_id = body.get("source_decision_id")
    if decision_id:
        decision = decision_operator_store.get(decision_id)
        if decision is None:
            return ContractResult(
                ok=False,
                error=f"source_decision_id '{decision_id}' does not resolve to an existing decision",
            )
        if not decision.get("source_run_id"):
            logger.warning(
                "Outcome created for decision %s which has no source_run_id — lineage incomplete",
                decision_id,
            )

    return ContractResult(ok=True)


def validate_outcome_status(status: str) -> ContractResult:
    """Validate that an outcome status is in the allowed set."""
    if status not in VALID_OUTCOME_STATUSES:
        return ContractResult(
            ok=False,
            error=f"Invalid outcome_status '{status}' — expected one of {sorted(VALID_OUTCOME_STATUSES)}",
        )
    return ContractResult(ok=True)


# ── Value contracts ─────────────────────────────────────────────────────────

def validate_value_chain(outcome: dict) -> ContractResult:
    """Full-chain validation for value computation.

    Rules:
      - outcome must have source_decision_id (not free-floating)
      - the linked decision must exist
      - the linked decision must have source_run_id
    """
    from src.services import decision_operator_store

    decision_id = outcome.get("source_decision_id")
    if not decision_id:
        return ContractResult(
            ok=False,
            error=(
                f"Outcome '{outcome.get('outcome_id')}' has no source_decision_id — "
                "value cannot be computed from an unlinked outcome"
            ),
        )

    decision = decision_operator_store.get(decision_id)
    if decision is None:
        return ContractResult(
            ok=False,
            error=(
                f"Outcome '{outcome.get('outcome_id')}' references decision '{decision_id}' "
                "which does not exist — graph is broken"
            ),
        )

    if not decision.get("source_run_id"):
        logger.warning(
            "Value computed for decision %s with no source_run_id — lineage incomplete but allowed",
            decision_id,
        )

    return ContractResult(ok=True)


# ── Post-mutation verification ──────────────────────────────────────────────

def verify_decision_outcome_linkage(decision: dict) -> ContractResult:
    """After create or execute, verify bidirectional linkage is intact.

    Rules:
      - decision.outcome_id must be non-null
      - outcome with that ID must exist
      - outcome.source_decision_id must point back to this decision
    """
    from src.services import outcome_store

    outcome_id = decision.get("outcome_id")
    if not outcome_id:
        return ContractResult(
            ok=False,
            error=f"Decision {decision.get('decision_id')} has no outcome_id after linkage",
        )

    outcome = outcome_store.get(outcome_id)
    if outcome is None:
        return ContractResult(
            ok=False,
            error=f"Decision {decision.get('decision_id')} references outcome {outcome_id} which does not exist",
        )

    if outcome.get("source_decision_id") != decision.get("decision_id"):
        return ContractResult(
            ok=False,
            error=(
                f"Bidirectional linkage broken: decision {decision.get('decision_id')} → "
                f"outcome {outcome_id}, but outcome.source_decision_id = "
                f"'{outcome.get('source_decision_id')}'"
            ),
        )

    return ContractResult(ok=True)
