"""
Impact Observatory | مرصد الأثر — Event Normalization (Stage 3)

Maps validated events to canonical schema.
Resolves sector aliases, standardizes severity scale, assigns geographic scope.

Geographic scope is derived exclusively from the canonical governance registry
(app.governance.registry.require_entry). There is NO fallback and NO alias logic.

If template_id is absent or not in the canonical registry, normalize_event()
raises ValueError — this is a HARD_FAIL. The pipeline must reject runs with
unknown scenario IDs at Stage 3, not silently default to ["SA", "UAE"].

Valid scenario IDs: see backend/app/governance/registry.py CANONICAL_REGISTRY.
"""

import uuid
from app.domain.models.raw_event import ValidatedEvent, NormalizedEvent
from app.graph.bridge import get_scenario_shock_vector
from app.governance.registry import require_entry as _require_registry_entry

# Sector alias resolution
SECTOR_ALIASES: dict[str, str] = {
    "bank": "banking",
    "banks": "banking",
    "finance": "banking",
    "insure": "insurance",
    "reinsurance": "insurance",
    "fintech_payments": "fintech",
    "payments": "fintech",
    "oil": "energy",
    "gas": "energy",
    "petroleum": "energy",
    "airline": "aviation",
    "airlines": "aviation",
    "air": "aviation",
    "port": "ports",
    "maritime": "shipping",
    "sea": "shipping",
    "food": "food_security",
    "water": "utilities",
    "power": "utilities",
    "electricity": "utilities",
    "telecom": "telecom",
    "communications": "telecom",
}

# Event type normalization
TYPE_ALIASES: dict[str, str] = {
    "geo": "geopolitical",
    "political": "geopolitical",
    "military": "geopolitical",
    "market": "economic",
    "financial": "economic",
    "climate": "natural",
    "weather": "natural",
    "earthquake": "natural",
    "hack": "cyber",
    "attack": "cyber",
}


def normalize_sector(sector: str) -> str:
    """Resolve sector aliases to canonical name."""
    return SECTOR_ALIASES.get(sector.lower(), sector.lower())


def normalize_event_type(event_type: str) -> str:
    """Resolve event type aliases to canonical name."""
    return TYPE_ALIASES.get(event_type.lower(), event_type.lower())


def normalize_event(validated: ValidatedEvent) -> NormalizedEvent:
    """Normalize a validated event to canonical schema.

    - Resolves sector aliases
    - Assigns geographic scope from template
    - Builds shock vector from template if available
    - Computes initial confidence
    """
    # Resolve sectors
    sectors = [normalize_sector(s) for s in validated.sectors_affected]

    # Get shock vector from scenario template
    shock_vector: list[dict] = []
    if validated.template_id:
        raw_shocks = get_scenario_shock_vector(validated.template_id)
        shock_vector = [
            {"node_id": s["node_id"], "impact": s["impact"] * validated.severity}
            for s in raw_shocks
        ]

    # Geographic scope — STRICT, no fallback.
    # require_entry() raises ValueError for any template_id not in CANONICAL_REGISTRY.
    # This is a Stage 3 HARD_FAIL: a run with an unknown scenario ID must be
    # rejected here, not silently assigned a wrong geographic scope.
    try:
        _registry_entry = _require_registry_entry(validated.template_id or "")
        geo_scope = list(_registry_entry.geographic_scope)
    except ValueError as _geo_err:
        raise ValueError(
            f"[Stage 3 HARD_FAIL] Geographic scope resolution failed: {_geo_err}. "
            f"template_id must be one of the 8 canonical scenario IDs in "
            f"backend/app/governance/registry.py CANONICAL_REGISTRY. "
            f"There is no fallback. Register the scenario or correct the template_id."
        ) from _geo_err

    # Initial confidence = validation_score (will be adjusted by enrich stage)
    confidence = validated.validation_score

    return NormalizedEvent(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        canonical_type=normalize_event_type("geopolitical"),
        severity=validated.severity,
        shock_vector=shock_vector,
        geographic_scope=geo_scope,
        confidence=confidence,
        provenance_chain=["ingest", "validate", "normalize"],
    )
