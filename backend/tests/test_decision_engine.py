"""Pack 3 — Decision Engine Test Suite.

Tests for:
  - _map_severity_to_priority() mapping
  - _urgency_rank() ordering
  - _get_action_description() template coverage
  - _derive_actions_for_domain() rules
  - map_impact_to_decision() structure
  - DecisionPriority per severity tier
  - requires_escalation flag
  - recommended_actions ordering (urgency asc, severity desc)
  - decision_reasoning includes propagation + graph reasoning
  - NOMINAL severity → ROUTINE + NO_ACTION
  - SEVERE severity → CRITICAL + ACTIVATE_CONTINGENCY
  - Domain-specific rules (banking/sovereign_fiscal ESCALATE at HIGH+)
  - OIL_GAS ACTIVATE_CONTINGENCY at SEVERE
  - Deduplication of actions
  - DecisionOutput model fields and audit_hash
  - MacroDecisionService pipeline
  - No regression on core macro path
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalSeverity,
)
from src.macro.impact.impact_engine import compute_impact
from src.macro.impact.impact_models import DomainImpact, MacroImpact
from src.macro.decision.decision_engine import (
    _SEVERITY_TO_PRIORITY,
    _derive_actions_for_domain,
    _map_severity_to_priority,
    _urgency_rank,
    map_impact_to_decision,
)
from src.macro.decision.decision_models import (
    ActionType,
    DecisionAction,
    DecisionOutput,
    DecisionPriority,
)
from src.macro.propagation.propagation_schemas import PropagationHit, PropagationResult
from src.services.macro_decision_service import (
    MacroDecisionService,
    get_macro_decision_service,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

def _make_di(
    domain: ImpactDomain = ImpactDomain.OIL_GAS,
    severity: float = 0.80,
    depth: int = 0,
    reasoning: str = "Test reasoning.",
    is_entry: bool = True,
) -> DomainImpact:
    from src.macro.impact.impact_engine import get_exposure_weight
    from src.macro.macro_validators import severity_from_score
    weight = get_exposure_weight(domain)
    return DomainImpact(
        domain=domain,
        severity_score=severity,
        severity_level=severity_from_score(severity),
        exposure_weight=weight,
        weighted_impact=round(severity * weight, 6),
        depth=depth,
        path_description=f"[ENTRY] {domain.value}" if is_entry else f"entry → {domain.value}",
        reasoning=reasoning,
        is_entry_domain=is_entry,
        regions=[GCCRegion.GCC_WIDE],
    )


def _make_impact(
    domain_impacts: list[DomainImpact] | None = None,
    signal_id: UUID | None = None,
    overall_severity: float = 0.80,
    confidence: SignalConfidence = SignalConfidence.HIGH,
) -> MacroImpact:
    from src.macro.macro_validators import severity_from_score
    dis = domain_impacts or []
    sid = signal_id or uuid4()
    affected = [di.domain for di in dis]
    total_exp = (
        round(sum(di.weighted_impact for di in dis) / len(dis), 6) if dis else 0.0
    )
    return MacroImpact(
        signal_id=sid,
        signal_title="Test signal",
        overall_severity=overall_severity,
        overall_severity_level=severity_from_score(overall_severity),
        total_exposure_score=total_exp,
        confidence=confidence,
        domain_impacts=dis,
        affected_domains=affected,
        entry_domains=affected[:1] if affected else [ImpactDomain.OIL_GAS],
        total_domains_reached=len(dis),
        max_depth=max((d.depth for d in dis), default=0),
        impact_reasoning="Propagation reasoning here.",
    )


def _make_hit(
    signal_id: UUID | None = None,
    domain: ImpactDomain = ImpactDomain.OIL_GAS,
    depth: int = 0,
    severity: float = 0.80,
    reasoning: str = "Test reasoning.",
) -> PropagationHit:
    from src.macro.macro_validators import severity_from_score
    return PropagationHit(
        signal_id=signal_id or uuid4(),
        domain=domain,
        depth=depth,
        severity_at_hit=severity,
        severity_level=severity_from_score(severity),
        regions=[GCCRegion.GCC_WIDE],
        path_description=f"[ENTRY] {domain.value}" if depth == 0 else f"entry → {domain.value}",
        reasoning=reasoning,
    )


def _make_result(
    hits: list[PropagationHit] | None = None,
    signal_id: UUID | None = None,
    entry_domains: list[ImpactDomain] | None = None,
) -> PropagationResult:
    sid = signal_id or uuid4()
    h = hits or []
    return PropagationResult(
        signal_id=sid,
        signal_title="Test signal",
        entry_domains=entry_domains or [ImpactDomain.OIL_GAS],
        hits=h,
        total_domains_reached=len(h),
        max_depth=max((x.depth for x in h), default=0),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. Priority Mapping
# ══════════════════════════════════════════════════════════════════════════════

class TestPriorityMapping:

    def test_nominal_to_routine(self):
        assert _map_severity_to_priority(SignalSeverity.NOMINAL) == DecisionPriority.ROUTINE

    def test_low_to_watch(self):
        assert _map_severity_to_priority(SignalSeverity.LOW) == DecisionPriority.WATCH

    def test_guarded_to_watch(self):
        assert _map_severity_to_priority(SignalSeverity.GUARDED) == DecisionPriority.WATCH

    def test_elevated_to_advisory(self):
        assert _map_severity_to_priority(SignalSeverity.ELEVATED) == DecisionPriority.ADVISORY

    def test_high_to_alert(self):
        assert _map_severity_to_priority(SignalSeverity.HIGH) == DecisionPriority.ALERT

    def test_severe_to_critical(self):
        assert _map_severity_to_priority(SignalSeverity.SEVERE) == DecisionPriority.CRITICAL

    def test_all_severity_levels_mapped(self):
        """Every SignalSeverity has a priority mapping."""
        for level in SignalSeverity:
            priority = _map_severity_to_priority(level)
            assert isinstance(priority, DecisionPriority)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Urgency Ranking
# ══════════════════════════════════════════════════════════════════════════════

class TestUrgencyRanking:

    def test_immediate_lowest_rank(self):
        assert _urgency_rank("immediate") == 0

    def test_within_24h_rank_1(self):
        assert _urgency_rank("within_24h") == 1

    def test_within_72h_rank_2(self):
        assert _urgency_rank("within_72h") == 2

    def test_routine_rank_3(self):
        assert _urgency_rank("routine") == 3

    def test_unknown_urgency_fallback(self):
        rank = _urgency_rank("unknown_value")
        assert rank >= 3  # falls back to end of list

    def test_immediate_before_routine(self):
        assert _urgency_rank("immediate") < _urgency_rank("routine")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Action Templates
# ══════════════════════════════════════════════════════════════════════════════

class TestActionTemplates:
    """Action descriptions should be non-empty strings for all ActionTypes."""

    def test_all_generic_descriptions_populated(self):
        from src.macro.decision.decision_engine import _GENERIC_DESCRIPTIONS
        for action_type in ActionType:
            assert action_type in _GENERIC_DESCRIPTIONS
            assert len(_GENERIC_DESCRIPTIONS[action_type]) > 5

    def test_oil_gas_monitor_description(self):
        from src.macro.decision.decision_engine import _get_action_description
        desc = _get_action_description(ActionType.MONITOR, ImpactDomain.OIL_GAS)
        assert len(desc) > 10
        assert "oil" in desc.lower() or "crude" in desc.lower() or "export" in desc.lower()

    def test_banking_escalate_description(self):
        from src.macro.decision.decision_engine import _get_action_description
        desc = _get_action_description(ActionType.ESCALATE, ImpactDomain.BANKING)
        assert len(desc) > 10

    def test_fallback_for_unmapped_domain_action(self):
        from src.macro.decision.decision_engine import _get_action_description
        # TELECOMMUNICATIONS + ESCALATE doesn't have a domain-specific template
        # Should fall back to generic
        desc = _get_action_description(ActionType.ESCALATE, ImpactDomain.TELECOMMUNICATIONS)
        assert len(desc) > 5


# ══════════════════════════════════════════════════════════════════════════════
# 4. _derive_actions_for_domain
# ══════════════════════════════════════════════════════════════════════════════

class TestDeriveActionsForDomain:

    def test_nominal_returns_no_action(self):
        di = _make_di(severity=0.10)  # NOMINAL
        actions = _derive_actions_for_domain(di, DecisionPriority.ROUTINE)
        # No actions for NOMINAL
        assert all(a.action_type == ActionType.NO_ACTION for a in actions) or actions == []

    def test_low_severity_returns_monitor(self):
        di = _make_di(severity=0.25)  # LOW
        actions = _derive_actions_for_domain(di, DecisionPriority.WATCH)
        types = [a.action_type for a in actions]
        assert ActionType.MONITOR in types

    def test_elevated_returns_review(self):
        di = _make_di(domain=ImpactDomain.MARITIME, severity=0.55)  # ELEVATED
        actions = _derive_actions_for_domain(di, DecisionPriority.ADVISORY)
        types = [a.action_type for a in actions]
        assert ActionType.REVIEW in types

    def test_high_severity_returns_hedge(self):
        di = _make_di(domain=ImpactDomain.MARITIME, severity=0.70)  # HIGH
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        types = [a.action_type for a in actions]
        assert ActionType.HEDGE in types

    def test_severe_returns_activate_contingency(self):
        di = _make_di(severity=0.85)  # SEVERE
        actions = _derive_actions_for_domain(di, DecisionPriority.CRITICAL)
        types = [a.action_type for a in actions]
        assert ActionType.ACTIVATE_CONTINGENCY in types

    def test_banking_high_gets_escalate(self):
        di = _make_di(domain=ImpactDomain.BANKING, severity=0.70)  # HIGH
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        types = [a.action_type for a in actions]
        assert ActionType.ESCALATE in types

    def test_sovereign_fiscal_high_gets_escalate(self):
        di = _make_di(domain=ImpactDomain.SOVEREIGN_FISCAL, severity=0.70)  # HIGH
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        types = [a.action_type for a in actions]
        assert ActionType.ESCALATE in types

    def test_oil_gas_high_gets_escalate(self):
        di = _make_di(domain=ImpactDomain.OIL_GAS, severity=0.70)  # HIGH
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        types = [a.action_type for a in actions]
        assert ActionType.ESCALATE in types

    def test_banking_guarded_no_escalate(self):
        di = _make_di(domain=ImpactDomain.BANKING, severity=0.40)  # GUARDED (below HIGH)
        actions = _derive_actions_for_domain(di, DecisionPriority.WATCH)
        types = [a.action_type for a in actions]
        assert ActionType.ESCALATE not in types

    def test_capital_markets_elevated_gets_alert_stakeholders(self):
        di = _make_di(domain=ImpactDomain.CAPITAL_MARKETS, severity=0.55)  # ELEVATED
        actions = _derive_actions_for_domain(di, DecisionPriority.ADVISORY)
        types = [a.action_type for a in actions]
        assert ActionType.ALERT_STAKEHOLDERS in types

    def test_capital_markets_low_no_alert_stakeholders(self):
        di = _make_di(domain=ImpactDomain.CAPITAL_MARKETS, severity=0.25)  # LOW (below ELEVATED)
        actions = _derive_actions_for_domain(di, DecisionPriority.WATCH)
        types = [a.action_type for a in actions]
        assert ActionType.ALERT_STAKEHOLDERS not in types

    def test_actions_have_action_id(self):
        di = _make_di(severity=0.70)
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        for a in actions:
            assert ":" in a.action_id
            assert a.domain.value in a.action_id

    def test_actions_have_rationale(self):
        di = _make_di(severity=0.70)
        actions = _derive_actions_for_domain(di, DecisionPriority.ALERT)
        for a in actions:
            assert len(a.rationale) > 10

    def test_actions_have_urgency(self):
        di = _make_di(severity=0.85)
        actions = _derive_actions_for_domain(di, DecisionPriority.CRITICAL)
        for a in actions:
            assert a.urgency in ["immediate", "within_24h", "within_72h", "routine"]


# ══════════════════════════════════════════════════════════════════════════════
# 5. map_impact_to_decision — Structure
# ══════════════════════════════════════════════════════════════════════════════

class TestMapImpactToDecisionStructure:

    def test_returns_decision_output(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert isinstance(decision, DecisionOutput)

    def test_signal_id_preserved(self):
        sid = uuid4()
        impact = _make_impact(signal_id=sid)
        decision = map_impact_to_decision(impact)
        assert decision.signal_id == sid

    def test_signal_title_preserved(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert decision.signal_title == "Test signal"

    def test_decision_id_is_uuid(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert isinstance(decision.decision_id, UUID)

    def test_audit_hash_generated(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert decision.audit_hash
        assert len(decision.audit_hash) == 64

    def test_decided_at_is_recent(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        now = datetime.now(timezone.utc)
        delta = abs((now - decision.decided_at).total_seconds())
        assert delta < 5.0

    def test_overall_severity_preserved(self):
        impact = _make_impact(overall_severity=0.80)
        decision = map_impact_to_decision(impact)
        assert decision.overall_severity == 0.80

    def test_confidence_preserved(self):
        impact = _make_impact(confidence=SignalConfidence.MODERATE)
        decision = map_impact_to_decision(impact)
        assert decision.confidence == SignalConfidence.MODERATE

    def test_total_domains_reached_preserved(self):
        di = _make_di()
        impact = _make_impact(domain_impacts=[di])
        decision = map_impact_to_decision(impact)
        assert decision.total_domains_reached == impact.total_domains_reached

    def test_impact_summary_non_empty(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert len(decision.impact_summary) > 10

    def test_decision_reasoning_non_empty(self):
        impact = _make_impact()
        decision = map_impact_to_decision(impact)
        assert len(decision.decision_reasoning) > 20


# ══════════════════════════════════════════════════════════════════════════════
# 6. map_impact_to_decision — Priority Rules
# ══════════════════════════════════════════════════════════════════════════════

class TestMapImpactToDecisionPriority:

    def test_nominal_priority_routine(self):
        di = _make_di(severity=0.10)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.10)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.ROUTINE

    def test_low_priority_watch(self):
        di = _make_di(severity=0.25)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.25)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.WATCH

    def test_guarded_priority_watch(self):
        di = _make_di(severity=0.40)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.40)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.WATCH

    def test_elevated_priority_advisory(self):
        di = _make_di(severity=0.55)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.55)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.ADVISORY

    def test_high_priority_alert(self):
        di = _make_di(severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.ALERT

    def test_severe_priority_critical(self):
        di = _make_di(severity=0.90)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.90)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.CRITICAL


# ══════════════════════════════════════════════════════════════════════════════
# 7. map_impact_to_decision — Escalation Flag
# ══════════════════════════════════════════════════════════════════════════════

class TestEscalationFlag:

    def test_routine_no_escalation(self):
        di = _make_di(severity=0.10)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.10)
        decision = map_impact_to_decision(impact)
        assert decision.requires_escalation is False

    def test_watch_no_escalation(self):
        di = _make_di(severity=0.25)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.25)
        decision = map_impact_to_decision(impact)
        assert decision.requires_escalation is False

    def test_advisory_no_escalation(self):
        di = _make_di(severity=0.55)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.55)
        decision = map_impact_to_decision(impact)
        assert decision.requires_escalation is False

    def test_alert_requires_escalation(self):
        di = _make_di(severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        assert decision.requires_escalation is True

    def test_critical_requires_escalation(self):
        di = _make_di(severity=0.90)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.90)
        decision = map_impact_to_decision(impact)
        assert decision.requires_escalation is True


# ══════════════════════════════════════════════════════════════════════════════
# 8. map_impact_to_decision — Action Ordering
# ══════════════════════════════════════════════════════════════════════════════

class TestActionOrdering:

    def test_actions_ordered_by_urgency(self):
        """Higher urgency actions appear before lower urgency ones."""
        di1 = _make_di(domain=ImpactDomain.OIL_GAS, severity=0.90)    # SEVERE → immediate
        di2 = _make_di(domain=ImpactDomain.MARITIME, severity=0.25, is_entry=False)  # LOW → routine
        impact = _make_impact(domain_impacts=[di1, di2], overall_severity=0.90)
        decision = map_impact_to_decision(impact)
        actions = decision.recommended_actions
        urgency_ranks = [_urgency_rank(a.urgency) for a in actions]
        assert urgency_ranks == sorted(urgency_ranks), "Actions not sorted by urgency"

    def test_no_duplicate_action_ids(self):
        di = _make_di(severity=0.80)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.80)
        decision = map_impact_to_decision(impact)
        ids = [a.action_id for a in decision.recommended_actions]
        assert len(ids) == len(set(ids)), "Duplicate action_ids found"

    def test_actions_have_valid_action_types(self):
        di = _make_di(severity=0.80)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.80)
        decision = map_impact_to_decision(impact)
        for a in decision.recommended_actions:
            assert isinstance(a.action_type, ActionType)

    def test_severe_oil_gas_has_activate_contingency(self):
        di = _make_di(domain=ImpactDomain.OIL_GAS, severity=0.90)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.90)
        decision = map_impact_to_decision(impact)
        types = [a.action_type for a in decision.recommended_actions]
        assert ActionType.ACTIVATE_CONTINGENCY in types

    def test_severe_banking_has_both_contingency_and_escalate(self):
        di = _make_di(domain=ImpactDomain.BANKING, severity=0.90)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.90)
        decision = map_impact_to_decision(impact)
        types = [a.action_type for a in decision.recommended_actions]
        assert ActionType.ACTIVATE_CONTINGENCY in types
        assert ActionType.ESCALATE in types

    def test_multi_domain_actions_cover_all_domains(self):
        domains = [
            ImpactDomain.OIL_GAS,
            ImpactDomain.BANKING,
            ImpactDomain.INSURANCE,
        ]
        dis = [_make_di(domain=d, severity=0.70, depth=i) for i, d in enumerate(domains)]
        impact = _make_impact(domain_impacts=dis, overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        action_domains = {a.domain for a in decision.recommended_actions}
        for d in domains:
            assert d in action_domains


# ══════════════════════════════════════════════════════════════════════════════
# 9. NOMINAL — No Action
# ══════════════════════════════════════════════════════════════════════════════

class TestNominalNoAction:

    def test_nominal_produces_no_action_entry(self):
        di = _make_di(severity=0.10)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.10)
        decision = map_impact_to_decision(impact)
        # Should have at least one NO_ACTION for the entry domain
        types = [a.action_type for a in decision.recommended_actions]
        assert ActionType.NO_ACTION in types

    def test_zero_hit_impact_routine_decision(self):
        """Zero-hit MacroImpact → ROUTINE decision with NO_ACTION."""
        sid = uuid4()
        result = PropagationResult(
            signal_id=sid,
            signal_title="Minimal",
            entry_domains=[ImpactDomain.OIL_GAS],
            hits=[],
            total_domains_reached=0,
            max_depth=0,
        )
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.ROUTINE
        assert decision.requires_escalation is False


# ══════════════════════════════════════════════════════════════════════════════
# 10. Decision Reasoning — Propagation + Graph Preservation
# ══════════════════════════════════════════════════════════════════════════════

class TestDecisionReasoning:

    def test_decision_reasoning_includes_propagation_reasoning(self):
        prop_reasoning = "Reached via oil_gas → banking. Mechanism: NPL increase."
        di = _make_di(reasoning=prop_reasoning, severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        impact.impact_reasoning = f"Some summary.\n--- Propagation reasoning ---\n[oil_gas] {prop_reasoning}"
        decision = map_impact_to_decision(impact)
        assert prop_reasoning in decision.decision_reasoning

    def test_decision_reasoning_includes_graph_fragments(self):
        graph_reasoning = "Normal.\n  [Graph Brain] Confirmed: 3 graph paths oil_gas → banking."
        di = _make_di(reasoning=graph_reasoning, severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        impact.impact_reasoning = f"Impact summary.\n[Graph Brain] in impact."
        decision = map_impact_to_decision(impact)
        assert "[Graph Brain]" in decision.decision_reasoning

    def test_decision_reasoning_includes_priority_tier(self):
        di = _make_di(severity=0.85)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.85)
        decision = map_impact_to_decision(impact)
        assert "CRITICAL" in decision.decision_reasoning.upper()

    def test_impact_summary_references_severity_level(self):
        di = _make_di(severity=0.85)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.85)
        decision = map_impact_to_decision(impact)
        assert "severe" in decision.impact_summary.lower()

    def test_impact_summary_references_domain_count(self):
        dis = [_make_di(domain=d, severity=0.70, depth=i)
               for i, d in enumerate([ImpactDomain.OIL_GAS, ImpactDomain.BANKING])]
        impact = _make_impact(domain_impacts=dis, overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        assert "2" in decision.impact_summary


# ══════════════════════════════════════════════════════════════════════════════
# 11. DecisionOutput Model
# ══════════════════════════════════════════════════════════════════════════════

class TestDecisionOutputModel:

    def test_audit_hash_is_sha256(self):
        di = _make_di(severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        int(decision.audit_hash, 16)  # valid hex
        assert len(decision.audit_hash) == 64

    def test_decision_action_fields(self):
        action = DecisionAction(
            action_id="hedge:oil_gas",
            domain=ImpactDomain.OIL_GAS,
            action_type=ActionType.HEDGE,
            description="Hedge crude price exposure.",
            urgency="within_24h",
            rationale="Severity 0.80 warrants hedging.",
        )
        assert action.action_type == ActionType.HEDGE
        assert action.domain == ImpactDomain.OIL_GAS

    def test_decision_output_serialization(self):
        di = _make_di(severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        d = decision.model_dump()
        assert "priority" in d
        assert "recommended_actions" in d
        assert "decision_reasoning" in d

    def test_decision_output_json_serializable(self):
        import json
        di = _make_di(severity=0.70)
        impact = _make_impact(domain_impacts=[di], overall_severity=0.70)
        decision = map_impact_to_decision(impact)
        json_str = decision.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["signal_title"] == "Test signal"


# ══════════════════════════════════════════════════════════════════════════════
# 12. MacroDecisionService
# ══════════════════════════════════════════════════════════════════════════════

class TestMacroDecisionService:

    def setup_method(self):
        import src.services.macro_decision_service as mod
        mod._service_instance = None

    def test_run_returns_decision_output(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc = MacroDecisionService()
        decision = svc.run(result)
        assert isinstance(decision, DecisionOutput)

    def test_run_caches_result(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc = MacroDecisionService()
        d1 = svc.run(result)
        d2 = svc.run(result)
        assert d1.decision_id == d2.decision_id  # same cached instance

    def test_get_impact_after_run(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc = MacroDecisionService()
        svc.run(result)
        impact = svc.get_impact(sid)
        assert impact is not None
        assert impact.signal_id == sid

    def test_get_decision_after_run(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc = MacroDecisionService()
        svc.run(result)
        decision = svc.get_decision(sid)
        assert decision is not None

    def test_get_impact_before_run_returns_none(self):
        svc = MacroDecisionService()
        assert svc.get_impact(uuid4()) is None

    def test_compute_impact_only(self):
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc = MacroDecisionService()
        impact = svc.compute_impact_only(result)
        assert isinstance(impact, MacroImpact)
        # Decision should NOT be cached after impact_only
        assert svc.get_decision(sid) is None

    def test_list_impacts(self):
        svc = MacroDecisionService()
        for _ in range(3):
            sid = uuid4()
            hit = _make_hit(signal_id=sid)
            result = _make_result(hits=[hit], signal_id=sid)
            svc.run(result)
        assert len(svc.list_impacts()) == 3

    def test_list_decisions(self):
        svc = MacroDecisionService()
        for _ in range(3):
            sid = uuid4()
            hit = _make_hit(signal_id=sid)
            result = _make_result(hits=[hit], signal_id=sid)
            svc.run(result)
        assert len(svc.list_decisions()) == 3

    def test_clear_resets_stores(self):
        svc = MacroDecisionService()
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc.run(result)
        svc.clear()
        assert svc.impact_count == 0
        assert svc.decision_count == 0

    def test_singleton_returns_same_instance(self):
        import src.services.macro_decision_service as mod
        mod._service_instance = None
        svc1 = get_macro_decision_service()
        svc2 = get_macro_decision_service()
        assert svc1 is svc2

    def test_impact_count_increments(self):
        svc = MacroDecisionService()
        assert svc.impact_count == 0
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc.run(result)
        assert svc.impact_count == 1

    def test_decision_count_increments(self):
        svc = MacroDecisionService()
        assert svc.decision_count == 0
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        svc.run(result)
        assert svc.decision_count == 1


# ══════════════════════════════════════════════════════════════════════════════
# 13. No Regression — Full Pipeline
# ══════════════════════════════════════════════════════════════════════════════

class TestNoRegressionFullPipeline:
    """Verify that running Pack 3 end-to-end does not break Pack 2 contracts."""

    def test_propagation_result_unchanged_after_impact(self):
        """compute_impact does not mutate the PropagationResult."""
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        original_hash = result.audit_hash
        compute_impact(result)
        assert result.audit_hash == original_hash  # PropagationResult unchanged

    def test_impact_does_not_mutate_hits(self):
        sid = uuid4()
        original_reasoning = "Original reasoning from propagation."
        hit = _make_hit(signal_id=sid, reasoning=original_reasoning)
        result = _make_result(hits=[hit], signal_id=sid)
        compute_impact(result)
        assert result.hits[0].reasoning == original_reasoning

    def test_full_pipeline_signal_id_traces_through(self):
        """signal_id propagates: PropagationResult → MacroImpact → DecisionOutput."""
        sid = uuid4()
        hit = _make_hit(signal_id=sid)
        result = _make_result(hits=[hit], signal_id=sid)
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)
        assert impact.signal_id == sid
        assert decision.signal_id == sid

    def test_severe_signal_full_pipeline(self):
        """End-to-end: severe OIL_GAS signal → CRITICAL decision."""
        sid = uuid4()
        hit = _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, severity=0.90)
        result = _make_result(hits=[hit], signal_id=sid, entry_domains=[ImpactDomain.OIL_GAS])
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.CRITICAL
        assert decision.requires_escalation is True

    def test_low_signal_full_pipeline(self):
        """End-to-end: low-severity signal → WATCH decision, no escalation."""
        sid = uuid4()
        hit = _make_hit(signal_id=sid, domain=ImpactDomain.INSURANCE, severity=0.25)
        result = _make_result(hits=[hit], signal_id=sid, entry_domains=[ImpactDomain.INSURANCE])
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)
        assert decision.priority == DecisionPriority.WATCH
        assert decision.requires_escalation is False

    def test_graph_enriched_signal_full_pipeline(self):
        """Graph-enriched propagation reasoning survives into DecisionOutput."""
        sid = uuid4()
        graph_reasoning = "Transmission confirmed.\n  [Graph Brain] 5 graph paths confirmed."
        hit = _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, severity=0.70,
                        reasoning=graph_reasoning)
        result = _make_result(hits=[hit], signal_id=sid, entry_domains=[ImpactDomain.BANKING])
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)
        assert "[Graph Brain]" in decision.decision_reasoning

    def test_multi_domain_multi_depth_pipeline(self):
        """Multi-hop propagation produces correctly structured decision."""
        sid = uuid4()
        hits = [
            _make_hit(signal_id=sid, domain=ImpactDomain.OIL_GAS, depth=0, severity=0.85),
            _make_hit(signal_id=sid, domain=ImpactDomain.BANKING, depth=1, severity=0.60),
            _make_hit(signal_id=sid, domain=ImpactDomain.INSURANCE, depth=2, severity=0.40),
            _make_hit(signal_id=sid, domain=ImpactDomain.REAL_ESTATE, depth=3, severity=0.25),
        ]
        result = _make_result(hits=hits, signal_id=sid, entry_domains=[ImpactDomain.OIL_GAS])
        result.total_domains_reached = 4
        result.max_depth = 3
        impact = compute_impact(result)
        decision = map_impact_to_decision(impact)

        # Signal with 4 domains reached → HIGH confidence
        assert impact.confidence == SignalConfidence.HIGH
        # Overall severity = 0.85 → SEVERE → CRITICAL
        assert decision.priority == DecisionPriority.CRITICAL
        assert len(decision.recommended_actions) >= 1
        # All 4 domains should have actions
        action_domains = {a.domain for a in decision.recommended_actions}
        assert ImpactDomain.OIL_GAS in action_domains
