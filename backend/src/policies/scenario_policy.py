"""
Scenario Policy — validates scenario context and resolves canonical type.

Pure function. No side effects. No external dependencies beyond config.py.

Replaces ad-hoc SCENARIO_TAXONOMY lookups scattered across the codebase with
a single policy evaluation point that also captures denial reasons.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config import SCENARIO_TAXONOMY, SCENARIO_TYPES


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """
    Input context for all policy evaluations.

    Constructed once per run and passed through the pipeline.
    Every policy layer reads from this; none mutates it.
    """

    scenario_id: str
    scenario_type: str = ""          # resolved from SCENARIO_TAXONOMY
    severity: float = 0.0            # event magnitude 0-1
    time_to_first_breach_hours: float | None = None
    loss_ratio: float = 0.0          # peak_loss / base_loss
    propagation_speed: float = 0.0   # velocity of contagion 0-1
    system_stress: float = 0.0       # aggregate system stress 0-1
    risk_level: str = "NOMINAL"      # current URS risk level


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """
    Output of a policy evaluation.

    allowed: Whether the scenario/action is permitted to proceed.
    reason:  Human-readable explanation (for audit trail).
    resolved_type: Canonical scenario type (MARITIME/ENERGY/etc.) or "" if unknown.
    warnings: Non-blocking advisory messages.
    """

    allowed: bool
    reason: str
    resolved_type: str = ""
    warnings: list[str] = field(default_factory=list)


def resolve_scenario_type(scenario_id: str) -> str:
    """Resolve canonical scenario type from SCENARIO_TAXONOMY."""
    return SCENARIO_TAXONOMY.get(scenario_id, "")


def evaluate_scenario_policy(context: PolicyContext) -> PolicyDecision:
    """
    Evaluate scenario-level policy.

    Rules:
      1. scenario_id must be non-empty
      2. scenario_id should map to a known type in SCENARIO_TAXONOMY
      3. If unmapped, allow with warning (forward-compatible for new scenarios)

    Returns PolicyDecision with resolved_type populated.
    """
    warnings: list[str] = []

    # Rule 1: scenario_id required
    if not context.scenario_id:
        return PolicyDecision(
            allowed=False,
            reason="scenario_id is required but was empty",
            resolved_type="",
        )

    # Rule 2: resolve type
    resolved = context.scenario_type or resolve_scenario_type(context.scenario_id)

    # Rule 3: unknown scenario → allow with warning
    if not resolved:
        warnings.append(
            f"scenario_id '{context.scenario_id}' not in SCENARIO_TAXONOMY — "
            f"known types: {sorted(SCENARIO_TYPES)}. Actions will not be filtered by type."
        )
        return PolicyDecision(
            allowed=True,
            reason="Unknown scenario type — proceeding without type-based filtering",
            resolved_type="",
            warnings=warnings,
        )

    if resolved not in SCENARIO_TYPES:
        warnings.append(
            f"Resolved type '{resolved}' not in canonical SCENARIO_TYPES set"
        )

    return PolicyDecision(
        allowed=True,
        reason=f"Scenario '{context.scenario_id}' resolved to type '{resolved}'",
        resolved_type=resolved,
    )


def build_policy_context(
    scenario_id: str,
    severity: float = 0.0,
    time_to_first_breach_hours: float | None = None,
    loss_ratio: float = 0.0,
    propagation_speed: float = 0.0,
    system_stress: float = 0.0,
    risk_level: str = "NOMINAL",
) -> PolicyContext:
    """
    Factory: build a PolicyContext with auto-resolved scenario_type.

    Use this instead of constructing PolicyContext directly — it ensures
    scenario_type is always resolved from SCENARIO_TAXONOMY.
    """
    return PolicyContext(
        scenario_id=scenario_id,
        scenario_type=resolve_scenario_type(scenario_id),
        severity=severity,
        time_to_first_breach_hours=time_to_first_breach_hours,
        loss_ratio=loss_ratio,
        propagation_speed=propagation_speed,
        system_stress=system_stress,
        risk_level=risk_level,
    )
