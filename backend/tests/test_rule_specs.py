"""
Rule Specification System — Integration Tests
===============================================

Validates:
  1. All 8 specs instantiate without Pydantic errors
  2. Registry loads all 4 families (8 specs total)
  3. Compiler produces valid DecisionRules from every spec
  4. Validator passes all specs at structural + semantic levels
  5. Spec ID naming convention is enforced
  6. Exclusions compile to negated conditions
"""

from __future__ import annotations

import pytest
from datetime import date


# ═══════════════════════════════════════════════════════════════════════════════
# Import guards — skip if dependencies missing
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from src.data_foundation.rule_specs.registry import SpecRegistry, get_registry
    from src.data_foundation.rule_specs.compiler import compile_spec
    from src.data_foundation.rule_specs.validator import validate_spec
    from src.data_foundation.rule_specs.schema import RuleSpec
    from src.data_foundation.rule_specs.families.oil_shock import OIL_SHOCK_SPECS
    from src.data_foundation.rule_specs.families.rate_shift import RATE_SHIFT_SPECS
    from src.data_foundation.rule_specs.families.logistics_disruption import LOGISTICS_DISRUPTION_SPECS
    from src.data_foundation.rule_specs.families.liquidity_stress import LIQUIDITY_STRESS_SPECS
    HAS_RULE_SPECS = True
except ImportError as e:
    HAS_RULE_SPECS = False
    _IMPORT_ERROR = str(e)

pytestmark = pytest.mark.skipif(
    not HAS_RULE_SPECS,
    reason=f"Rule spec imports failed: {_IMPORT_ERROR if not HAS_RULE_SPECS else ''}",
)


# ═══════════════════════════════════════════════════════════════════════════════
# Family instantiation tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFamilyInstantiation:
    """Verify all family modules export valid RuleSpec lists."""

    def test_oil_shock_family_has_2_specs(self):
        assert len(OIL_SHOCK_SPECS) == 2
        for spec in OIL_SHOCK_SPECS:
            assert isinstance(spec, RuleSpec)
            assert spec.family == "oil-shock"

    def test_rate_shift_family_has_2_specs(self):
        assert len(RATE_SHIFT_SPECS) == 2
        for spec in RATE_SHIFT_SPECS:
            assert isinstance(spec, RuleSpec)
            assert spec.family == "rate-shift"

    def test_logistics_disruption_family_has_2_specs(self):
        assert len(LOGISTICS_DISRUPTION_SPECS) == 2
        for spec in LOGISTICS_DISRUPTION_SPECS:
            assert isinstance(spec, RuleSpec)
            assert spec.family == "logistics-disruption"

    def test_liquidity_stress_family_has_2_specs(self):
        assert len(LIQUIDITY_STRESS_SPECS) == 2
        for spec in LIQUIDITY_STRESS_SPECS:
            assert isinstance(spec, RuleSpec)
            assert spec.family == "liquidity-stress"

    def test_total_specs_across_all_families(self):
        total = (
            len(OIL_SHOCK_SPECS)
            + len(RATE_SHIFT_SPECS)
            + len(LOGISTICS_DISRUPTION_SPECS)
            + len(LIQUIDITY_STRESS_SPECS)
        )
        assert total == 8


# ═══════════════════════════════════════════════════════════════════════════════
# Registry tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegistry:
    """Verify SpecRegistry loads and indexes all specs."""

    def setup_method(self):
        self.registry = SpecRegistry()
        self.registry.load_families()

    def test_registry_loads_8_specs(self):
        assert self.registry.count == 8

    def test_registry_has_4_families(self):
        families = sorted(self.registry.families())
        assert families == [
            "liquidity-stress",
            "logistics-disruption",
            "oil-shock",
            "rate-shift",
        ]

    def test_get_by_spec_id(self):
        spec = self.registry.get("SPEC-OIL-BRENT-DROP-30-v1")
        assert spec is not None
        assert "Brent" in spec.name or "Oil" in spec.name

    def test_get_by_spec_id_liquidity(self):
        spec = self.registry.get("SPEC-LIQUIDITY-KW-LCR-BREACH-v1")
        assert spec is not None
        assert spec.family == "liquidity-stress"
        assert spec.variant == "kw-lcr-breach"

    def test_get_by_spec_id_interbank(self):
        spec = self.registry.get("SPEC-LIQUIDITY-INTERBANK-SPIKE-v1")
        assert spec is not None
        assert spec.family == "liquidity-stress"
        assert spec.variant == "interbank-spike"

    def test_get_family_returns_correct_specs(self):
        oil_specs = self.registry.get_family("oil-shock")
        assert len(oil_specs) == 2
        ids = {s.spec_id for s in oil_specs}
        assert "SPEC-OIL-BRENT-DROP-30-v1" in ids
        assert "SPEC-OIL-SUSTAINED-LOW-60-v1" in ids

    def test_get_family_liquidity_stress(self):
        liq_specs = self.registry.get_family("liquidity-stress")
        assert len(liq_specs) == 2
        ids = {s.spec_id for s in liq_specs}
        assert "SPEC-LIQUIDITY-KW-LCR-BREACH-v1" in ids
        assert "SPEC-LIQUIDITY-INTERBANK-SPIKE-v1" in ids

    def test_all_specs_are_active(self):
        active = self.registry.get_active()
        assert len(active) == 8

    def test_nonexistent_spec_returns_none(self):
        assert self.registry.get("SPEC-DOES-NOT-EXIST-v99") is None


# ═══════════════════════════════════════════════════════════════════════════════
# Compiler tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompiler:
    """Verify compile_spec produces valid DecisionRules."""

    def setup_method(self):
        self.all_specs = (
            OIL_SHOCK_SPECS
            + RATE_SHIFT_SPECS
            + LOGISTICS_DISRUPTION_SPECS
            + LIQUIDITY_STRESS_SPECS
        )

    def test_every_spec_compiles_without_error(self):
        for spec in self.all_specs:
            rules = compile_spec(spec)
            assert len(rules) >= 1, f"{spec.spec_id} compiled to 0 rules"

    def test_compiled_rules_have_conditions(self):
        for spec in self.all_specs:
            rules = compile_spec(spec)
            for rule in rules:
                assert len(rule.conditions) >= 1, (
                    f"{spec.spec_id} → rule with 0 conditions"
                )

    def test_compiled_rule_id_format(self):
        """Rule IDs should be RULE-{FAMILY}-{VARIANT} (no version suffix)."""
        for spec in self.all_specs:
            rules = compile_spec(spec)
            for rule in rules:
                assert rule.rule_id.startswith("RULE-"), (
                    f"Bad rule_id prefix: {rule.rule_id}"
                )
                # Should NOT contain version suffix
                assert not rule.rule_id.endswith("-v1"), (
                    f"Rule ID should not have version suffix: {rule.rule_id}"
                )

    def test_compiled_rules_carry_action(self):
        for spec in self.all_specs:
            rules = compile_spec(spec)
            for rule in rules:
                assert rule.action == spec.decision.action

    def test_exclusions_compiled_as_conditions(self):
        """Specs with exclusions should have more conditions than thresholds."""
        for spec in self.all_specs:
            if spec.exclusions:
                rules = compile_spec(spec)
                for rule in rules:
                    assert len(rule.conditions) > len(spec.thresholds), (
                        f"{spec.spec_id}: exclusions not compiled into conditions"
                    )

    def test_lcr_breach_compiles_with_exclusions(self):
        spec = [s for s in self.all_specs if s.spec_id == "SPEC-LIQUIDITY-KW-LCR-BREACH-v1"][0]
        rules = compile_spec(spec)
        assert len(rules) == 1
        rule = rules[0]
        # 2 thresholds + 2 exclusions = 4 conditions
        assert len(rule.conditions) == 4

    def test_interbank_spike_compiles_with_exclusions(self):
        spec = [s for s in self.all_specs if s.spec_id == "SPEC-LIQUIDITY-INTERBANK-SPIKE-v1"][0]
        rules = compile_spec(spec)
        assert len(rules) == 1
        rule = rules[0]
        # 1 threshold + 2 exclusions = 3 conditions
        assert len(rule.conditions) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Validator tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidator:
    """Verify validate_spec catches issues and passes clean specs."""

    def setup_method(self):
        self.all_specs = (
            OIL_SHOCK_SPECS
            + RATE_SHIFT_SPECS
            + LOGISTICS_DISRUPTION_SPECS
            + LIQUIDITY_STRESS_SPECS
        )

    def test_all_specs_pass_standard_validation(self):
        for spec in self.all_specs:
            result = validate_spec(spec)
            assert result.valid, (
                f"{spec.spec_id} failed validation: "
                f"{[e.message for e in result.errors]}"
            )

    def test_all_specs_have_audit_records(self):
        for spec in self.all_specs:
            assert spec.audit.authored_by, f"{spec.spec_id}: missing authored_by"
            assert spec.audit.authored_at, f"{spec.spec_id}: missing authored_at"

    def test_all_active_specs_have_approval(self):
        for spec in self.all_specs:
            if spec.status == "ACTIVE":
                assert spec.audit.approved_by, (
                    f"{spec.spec_id}: ACTIVE but no approved_by"
                )
                assert spec.audit.approved_at, (
                    f"{spec.spec_id}: ACTIVE but no approved_at"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Spec ID naming convention tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestNamingConvention:
    """Verify spec_id follows SPEC-{FAMILY}-{VARIANT}-v{MAJOR} format."""

    def setup_method(self):
        self.all_specs = (
            OIL_SHOCK_SPECS
            + RATE_SHIFT_SPECS
            + LOGISTICS_DISRUPTION_SPECS
            + LIQUIDITY_STRESS_SPECS
        )

    def test_all_spec_ids_start_with_SPEC(self):
        for spec in self.all_specs:
            assert spec.spec_id.startswith("SPEC-"), (
                f"Bad spec_id: {spec.spec_id}"
            )

    def test_all_spec_ids_end_with_version(self):
        for spec in self.all_specs:
            assert spec.spec_id.endswith("-v1"), (
                f"Spec ID should end with version: {spec.spec_id}"
            )

    def test_spec_version_is_semver(self):
        for spec in self.all_specs:
            parts = spec.spec_version.split(".")
            assert len(parts) == 3, (
                f"{spec.spec_id}: version {spec.spec_version} is not SemVer"
            )

    def test_all_specs_have_unique_ids(self):
        ids = [s.spec_id for s in self.all_specs]
        assert len(ids) == len(set(ids)), "Duplicate spec IDs found"


# ═══════════════════════════════════════════════════════════════════════════════
# Content integrity tests — liquidity stress specifics
# ═══════════════════════════════════════════════════════════════════════════════


class TestLiquidityStressContent:
    """Verify liquidity stress specs have correct domain content."""

    def setup_method(self):
        self.lcr_spec = [
            s for s in LIQUIDITY_STRESS_SPECS
            if s.variant == "kw-lcr-breach"
        ][0]
        self.interbank_spec = [
            s for s in LIQUIDITY_STRESS_SPECS
            if s.variant == "interbank-spike"
        ][0]

    def test_lcr_breach_is_kuwait_specific(self):
        from src.data_foundation.schemas.enums import GCCCountry
        assert self.lcr_spec.applicable_countries == [GCCCountry.KW]

    def test_interbank_spike_is_gcc_wide(self):
        assert len(self.interbank_spec.applicable_countries) == 6

    def test_lcr_breach_threshold_is_100pct(self):
        threshold = self.lcr_spec.thresholds[0]
        assert threshold.value == 100
        assert threshold.operator == "lt"

    def test_interbank_spike_threshold_is_150bps(self):
        threshold = self.interbank_spec.thresholds[0]
        assert threshold.value == 150
        assert threshold.operator == "gte"

    def test_lcr_breach_requires_human_approval(self):
        assert self.lcr_spec.decision.requires_human_approval is True
        assert self.lcr_spec.decision.approval_authority == "CRO"

    def test_interbank_spike_auto_approve(self):
        assert self.interbank_spec.decision.requires_human_approval is False

    def test_lcr_breach_has_transmission_paths(self):
        assert len(self.lcr_spec.transmission_paths) == 3

    def test_interbank_spike_has_transmission_paths(self):
        assert len(self.interbank_spec.transmission_paths) == 2

    def test_lcr_breach_has_exclusions(self):
        assert len(self.lcr_spec.exclusions) == 2

    def test_interbank_spike_has_exclusions(self):
        assert len(self.interbank_spec.exclusions) == 2

    def test_lcr_breach_confidence_above_90(self):
        assert self.lcr_spec.confidence.confidence_score >= 0.90

    def test_lcr_breach_has_arabic_names(self):
        assert self.lcr_spec.name_ar is not None
        assert self.lcr_spec.rationale.summary_ar is not None
        assert self.lcr_spec.rationale.dashboard_label_ar is not None

    def test_interbank_spike_has_arabic_names(self):
        assert self.interbank_spec.name_ar is not None
        assert self.interbank_spec.rationale.summary_ar is not None

    def test_lcr_breach_escalation_is_severe(self):
        from src.data_foundation.schemas.enums import RiskLevel, DecisionAction
        assert self.lcr_spec.decision.escalation_level == RiskLevel.SEVERE
        assert self.lcr_spec.decision.action == DecisionAction.ESCALATE

    def test_interbank_spike_is_monitor_action(self):
        from src.data_foundation.schemas.enums import DecisionAction
        assert self.interbank_spec.decision.action == DecisionAction.MONITOR
