"""DecisionReasoningEngine — explains WHY a decision is recommended,
WHY it ranks where it does, and WHY now.

Ties reasoning to: propagation, time-to-breach, regime, trust,
and explicit tradeoff analysis.
"""

from __future__ import annotations

from typing import Any


def build_decision_reasonings(run_result: dict) -> list[dict]:
    """Build reasoning explanations for all decisions in a run.

    Sources:
      - decision_quality.executive_decisions (Stage 60)
      - decision_calibration (Stage 70): ranked_decisions, trust_results
      - decision_trust (Stage 80): explanations, override_results

    Returns list of dicts matching DecisionReasoning model.
    """
    dq = run_result.get("decision_quality", {})
    cal = run_result.get("decision_calibration", {})
    trust = run_result.get("decision_trust", {})

    # Index Stage 70 outputs
    ranked_by_id: dict[str, dict] = {
        r.get("decision_id", ""): r
        for r in cal.get("ranked_decisions", [])
    }
    trust70_by_id: dict[str, dict] = {
        t.get("decision_id", ""): t
        for t in cal.get("trust_results", [])
    }

    # Index Stage 80 outputs
    expl_by_id: dict[str, dict] = {
        e.get("decision_id", ""): e
        for e in trust.get("explanations", [])
    }
    override_by_id: dict[str, dict] = {
        o.get("decision_id", ""): o
        for o in trust.get("override_results", [])
    }

    # Regime context
    regime = run_result.get("regime_state", {})
    regime_id = regime.get("regime_id", "STABLE")
    regime_amp = regime.get("propagation_amplifier", 1.0)

    # Scenario context
    scenario_id = run_result.get("scenario_id", "")
    severity = run_result.get("severity", 0.5)
    prop_score = run_result.get("propagation_score", 0.0)
    ttf = run_result.get("decision_plan", {}).get("time_to_first_failure_hours")

    reasonings: list[dict] = []

    # Iterate over executive decisions (Stage 60)
    exec_decisions = dq.get("executive_decisions", [])
    for dec in exec_decisions:
        did = dec.get("decision_id", "")
        aid = dec.get("action_id", "")
        action_en = dec.get("action_en", dec.get("action", ""))
        action_ar = dec.get("action_ar", "")
        sector = dec.get("sector", "")
        urgency = dec.get("urgency", dec.get("base_urgency", 0.5))
        feasibility = dec.get("feasibility", 0.5)
        cost = dec.get("cost_usd", 0)
        time_to_act = dec.get("time_to_act_hours", 0)

        ranked = ranked_by_id.get(did, {})
        trust70 = trust70_by_id.get(did, {})
        expl = expl_by_id.get(did, {})
        override = override_by_id.get(did, {})

        rank = ranked.get("calibrated_rank", 0)
        rank_score = ranked.get("ranking_score", 0.0)
        crisis_boost = ranked.get("crisis_boost", 0.0)
        trust_level = override.get("trust_level", trust70.get("trust_level", "MEDIUM"))
        trust_score = override.get("trust_score", trust70.get("trust_composite", 0.0))
        exec_mode = override.get("final_status", trust70.get("execution_mode", "HUMAN_REQUIRED"))

        # Build WHY THIS DECISION
        why_decision = expl.get("trigger_reason_en", "")
        if not why_decision:
            why_decision = (
                f"Action '{action_en}' addresses {sector} sector stress "
                f"caused by {scenario_id.replace('_', ' ')} at severity {severity:.0%}."
            )

        # Build WHY NOW
        why_now_parts = []
        if ttf and time_to_act:
            if time_to_act < float(ttf):
                why_now_parts.append(
                    f"Time-to-act ({time_to_act}h) is within time-to-first-breach ({ttf}h)"
                )
            else:
                why_now_parts.append(
                    f"Time-to-act ({time_to_act}h) exceeds time-to-first-breach ({ttf}h) — delayed response risk"
                )
        if urgency >= 0.85:
            why_now_parts.append(f"High urgency ({urgency:.2f}) requires immediate action")
        if regime_id in ("CRISIS", "VOLATILE"):
            why_now_parts.append(f"Regime is {regime_id} — delays amplify losses by {regime_amp:.1f}×")
        if not why_now_parts:
            why_now_parts.append(f"Urgency {urgency:.2f} within normal response window")
        why_now = ". ".join(why_now_parts) + "."

        # Build WHY THIS RANK
        rank_parts = []
        if rank > 0:
            rank_parts.append(f"Ranked #{rank} with composite score {rank_score:.3f}")
        if crisis_boost > 0:
            rank_parts.append(f"Crisis regime boost: +{crisis_boost:.3f}")

        # Check for tradeoffs — high ROI but ranked lower
        factors = ranked.get("factors", [])
        for f in factors:
            if isinstance(f, dict):
                fname = f.get("factor_name", f.get("name", ""))
                fval = f.get("weighted_value", f.get("value", 0))
                if fname == "downside_safety" and fval < 0.05:
                    rank_parts.append("Penalized for high downside risk despite potential ROI")
                if fname == "regulatory_simplicity" and fval < 0.03:
                    rank_parts.append("Regulatory complexity reduces practical ranking")

        if feasibility < 0.50:
            rank_parts.append(f"Low feasibility ({feasibility:.2f}) limits ranking")
        if not rank_parts:
            rank_parts.append("Ranked by 8-factor multi-criteria model")
        why_rank = ". ".join(rank_parts) + "."

        # Affected entities from propagation
        affected = []
        prop_chain = run_result.get("propagation", run_result.get("propagation_chain", []))
        for step in prop_chain[:5]:
            if isinstance(step, dict):
                entity = step.get("entity_label", step.get("entity_id", ""))
                if entity:
                    affected.append(entity)

        # Propagation link
        prop_link = expl.get("propagation_summary_en", "")
        if not prop_link:
            prop_link = (
                f"Propagation score {prop_score:.2f} across 43 GCC nodes; "
                f"{len(prop_chain)} entities in transmission chain."
            )

        # Regime link
        regime_link = expl.get("regime_context_en", "")
        if not regime_link:
            regime_link = f"Regime: {regime_id} (amplifier: {regime_amp:.2f})"

        # Trust link
        trust_link = (
            f"Trust: {trust_level} ({trust_score:.2f}). "
            f"Execution mode: {exec_mode}."
        )
        if exec_mode == "BLOCKED":
            trust_link += f" Blocked by: {override.get('override_rule', 'unknown')}."
        elif exec_mode == "HUMAN_REQUIRED":
            trust_link += f" Requires human review: {override.get('override_reason_en', '')}."

        # Tradeoff summary
        tradeoff_parts = []
        if cost > 0:
            tradeoff_parts.append(f"Cost: ${cost:,.0f}")
        if feasibility < 0.70:
            tradeoff_parts.append(f"Feasibility: {feasibility:.0%} (moderate risk)")
        if exec_mode == "CONDITIONAL":
            tradeoff_parts.append("Conditional execution — monitoring required")
        tradeoff = "; ".join(tradeoff_parts) if tradeoff_parts else "No significant tradeoffs identified."

        reasonings.append({
            "decision_id": did,
            "action_id": aid,
            "why_this_decision_en": why_decision,
            "why_this_decision_ar": expl.get("trigger_reason_ar", ""),
            "why_now_en": why_now,
            "why_now_ar": "",
            "why_this_rank_en": why_rank,
            "why_this_rank_ar": "",
            "affected_entities": affected[:10],
            "propagation_link_en": prop_link,
            "propagation_link_ar": expl.get("propagation_summary_ar", ""),
            "regime_link_en": regime_link,
            "regime_link_ar": expl.get("regime_context_ar", ""),
            "trust_link_en": trust_link,
            "trust_link_ar": "",
            "tradeoff_summary_en": tradeoff,
            "tradeoff_summary_ar": "",
        })

    return reasonings
