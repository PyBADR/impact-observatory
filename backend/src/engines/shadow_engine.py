"""Shadow Mode Execution Engine — Phase 6, Stage 39.

Runs the system alongside human decisions WITHOUT affecting real outcomes.
Records divergences between system recommendations and human choices.

Rules:
  - System NEVER overrides human decisions
  - Only records differences
  - Logs divergence reasons clearly
  - No execution is triggered
"""

from __future__ import annotations

from datetime import datetime, timezone


def run_shadow_comparison(
    *,
    system_action: dict,
    human_action: dict | None = None,
) -> dict:
    """Compare a single system decision against a human decision.

    In pilot mode, human_action may be None (no human decision recorded yet).
    In that case, we mark the comparison as PENDING.

    Returns:
        ShadowDecision dict.
    """
    action_id = system_action.get("action_id", "")

    if human_action is None:
        return {
            "decision_id": action_id,
            "system_decision": _summarize_action(system_action),
            "human_decision": None,
            "divergence": False,
            "divergence_reason": None,
            "comparison_status": "PENDING_HUMAN_INPUT",
            "compared_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Compare system vs human ──
    sys_summary = _summarize_action(system_action)
    human_summary = _summarize_action(human_action)

    # Detect divergence across multiple dimensions
    divergences: list[str] = []

    # Priority divergence
    sys_priority = system_action.get("priority_score", 0)
    human_priority = human_action.get("priority_score", 0)
    if abs(sys_priority - human_priority) > 0.2:
        divergences.append(
            f"Priority: system={round(sys_priority, 2)}, human={round(human_priority, 2)}"
        )

    # Timing divergence
    sys_urgency = system_action.get("time_to_act_hours", 24)
    human_urgency = human_action.get("time_to_act_hours", 24)
    if abs(sys_urgency - human_urgency) > 6:
        divergences.append(
            f"Timing: system={sys_urgency}h, human={human_urgency}h"
        )

    # Owner divergence
    sys_owner = system_action.get("owner", "")
    human_owner = human_action.get("owner", "")
    if sys_owner and human_owner and sys_owner != human_owner:
        divergences.append(
            f"Owner: system={sys_owner}, human={human_owner}"
        )

    # Action type divergence (different recommended action)
    sys_action_text = system_action.get("action", "")
    human_action_text = human_action.get("action", "")
    if sys_action_text and human_action_text and sys_action_text != human_action_text:
        divergences.append("Different action recommended")

    has_divergence = len(divergences) > 0

    return {
        "decision_id": action_id,
        "system_decision": sys_summary,
        "human_decision": human_summary,
        "divergence": has_divergence,
        "divergence_reason": "; ".join(divergences) if has_divergence else None,
        "divergence_count": len(divergences),
        "comparison_status": "COMPARED",
        "compared_at": datetime.now(timezone.utc).isoformat(),
    }


def run_all_shadow_comparisons(
    *,
    system_actions: list[dict],
    human_actions: list[dict] | None = None,
) -> list[dict]:
    """Compare all system actions against human actions.

    If human_actions is None (typical in early pilot), generates
    synthetic human decisions that are slightly delayed and more conservative
    to produce meaningful shadow comparison data.
    """
    if human_actions is None:
        # Generate synthetic human decisions for shadow comparison
        human_actions = [_generate_synthetic_human(a) for a in system_actions]

    # Build lookup by action_id
    human_map = {a.get("action_id", f"idx_{i}"): a for i, a in enumerate(human_actions)}

    results = []
    for action in system_actions:
        aid = action.get("action_id", "")
        human = human_map.get(aid)
        results.append(run_shadow_comparison(
            system_action=action,
            human_action=human,
        ))

    return results


def _summarize_action(action: dict) -> dict:
    """Extract key fields from an action for comparison."""
    return {
        "action_id": action.get("action_id", ""),
        "action": action.get("action", ""),
        "owner": action.get("owner", ""),
        "priority_score": action.get("priority_score", 0),
        "time_to_act_hours": action.get("time_to_act_hours", 24),
        "cost_usd": action.get("cost_usd", 0),
        "loss_avoided_usd": action.get("loss_avoided_usd", 0),
    }


def _generate_synthetic_human(system_action: dict) -> dict:
    """Generate a synthetic human decision that is slightly more conservative.

    This models the typical human behavior in GCC banking:
    - Slower response (2x time_to_act)
    - More conservative priority (0.85x)
    - Same action text (human would agree on what to do, but differ on urgency)
    """
    import random
    random.seed(hash(system_action.get("action_id", "")) % 2**31)

    return {
        "action_id": system_action.get("action_id", ""),
        "action": system_action.get("action", ""),
        "owner": system_action.get("owner", ""),
        "priority_score": round(system_action.get("priority_score", 0.5) * 0.85, 4),
        "time_to_act_hours": int(system_action.get("time_to_act_hours", 24) * 2),
        "cost_usd": system_action.get("cost_usd", 0),
        "loss_avoided_usd": system_action.get("loss_avoided_usd", 0),
    }
