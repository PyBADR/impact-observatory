"""
Rule Spec Registry | سجل المواصفات
====================================

In-memory registry of all rule specifications. Loads specs
from family modules and provides lookup, search, and
compilation to DecisionRules.

The registry is the single entry point for all spec operations:
  - Load all families on startup
  - Look up spec by ID, family, or status
  - Compile specs to execution rules
  - Validate specs before activation
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from src.data_foundation.rule_specs.schema import RuleSpec
from src.data_foundation.rule_specs.compiler import compile_spec
from src.data_foundation.rule_specs.validator import validate_spec, ValidationResult
from src.data_foundation.schemas.decision_rules import DecisionRule

__all__ = ["SpecRegistry", "get_registry"]


class SpecRegistry:
    """In-memory rule specification registry."""

    def __init__(self) -> None:
        self._specs: Dict[str, RuleSpec] = {}
        self._by_family: Dict[str, List[str]] = {}  # family → [spec_id, ...]

    @property
    def count(self) -> int:
        return len(self._specs)

    def register(self, spec: RuleSpec) -> None:
        """Register a spec. Overwrites if spec_id already exists."""
        self._specs[spec.spec_id] = spec
        family_list = self._by_family.setdefault(spec.family, [])
        if spec.spec_id not in family_list:
            family_list.append(spec.spec_id)

    def register_many(self, specs: Sequence[RuleSpec]) -> int:
        """Register multiple specs. Returns count registered."""
        for spec in specs:
            self.register(spec)
        return len(specs)

    def get(self, spec_id: str) -> Optional[RuleSpec]:
        """Look up a spec by ID."""
        return self._specs.get(spec_id)

    def get_family(self, family: str) -> List[RuleSpec]:
        """Get all specs in a family."""
        ids = self._by_family.get(family, [])
        return [self._specs[sid] for sid in ids if sid in self._specs]

    def get_active(self) -> List[RuleSpec]:
        """Get all specs with status ACTIVE."""
        return [s for s in self._specs.values() if s.status == "ACTIVE"]

    def get_all(self) -> List[RuleSpec]:
        """Get all registered specs."""
        return list(self._specs.values())

    def families(self) -> List[str]:
        """List all registered family names."""
        return list(self._by_family.keys())

    def compile(self, spec_id: str) -> List[DecisionRule]:
        """Compile a single spec to execution rules."""
        spec = self._specs.get(spec_id)
        if spec is None:
            raise KeyError(f"Spec not found: {spec_id}")
        return compile_spec(spec)

    def compile_all_active(self) -> List[DecisionRule]:
        """Compile all active specs to execution rules."""
        rules: List[DecisionRule] = []
        for spec in self.get_active():
            rules.extend(compile_spec(spec))
        return rules

    def compile_family(self, family: str) -> List[DecisionRule]:
        """Compile all specs in a family to execution rules."""
        rules: List[DecisionRule] = []
        for spec in self.get_family(family):
            rules.extend(compile_spec(spec))
        return rules

    def validate(self, spec_id: str, strict: bool = False) -> ValidationResult:
        """Validate a single spec."""
        spec = self._specs.get(spec_id)
        if spec is None:
            raise KeyError(f"Spec not found: {spec_id}")
        return validate_spec(spec, strict=strict)

    def validate_all(self, strict: bool = False) -> Dict[str, ValidationResult]:
        """Validate all registered specs."""
        return {
            spec_id: validate_spec(spec, strict=strict)
            for spec_id, spec in self._specs.items()
        }

    def load_families(self) -> int:
        """Load all built-in rule families. Returns total specs loaded."""
        from src.data_foundation.rule_specs.families.oil_shock import OIL_SHOCK_SPECS
        from src.data_foundation.rule_specs.families.rate_shift import RATE_SHIFT_SPECS
        from src.data_foundation.rule_specs.families.logistics_disruption import LOGISTICS_DISRUPTION_SPECS
        from src.data_foundation.rule_specs.families.liquidity_stress import LIQUIDITY_STRESS_SPECS

        total = 0
        total += self.register_many(OIL_SHOCK_SPECS)
        total += self.register_many(RATE_SHIFT_SPECS)
        total += self.register_many(LOGISTICS_DISRUPTION_SPECS)
        total += self.register_many(LIQUIDITY_STRESS_SPECS)
        return total


# Module-level singleton
_registry: Optional[SpecRegistry] = None


def get_registry() -> SpecRegistry:
    """Get or create the global spec registry."""
    global _registry
    if _registry is None:
        _registry = SpecRegistry()
        _registry.load_families()
    return _registry
