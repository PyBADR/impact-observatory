"""
Scenario Enforcement Engine — strict taxonomy enforcement.

Guarantees that:
  - Every scenario has a resolved type
  - No UNKNOWN scenarios pass through unclassified
  - Fallback classification is explicit and confidence-scored
  - Pipeline can flag unclassified scenarios for operator review

Resolution strategy for unmapped scenarios:
  1. Check SCENARIO_TAXONOMY directly
  2. If missing, infer from scenario_id keywords
  3. If still unresolved, infer from SCENARIO_CATALOG sectors_affected
  4. If all fail, classify as REGULATORY with low confidence

Known unmapped scenarios (in SCENARIO_CATALOG but not SCENARIO_TAXONOMY):
  - gcc_power_grid_failure          → inferred CYBER (infrastructure)
  - difc_financial_contagion        → inferred LIQUIDITY (banking)
  - gcc_insurance_reserve_shortfall → inferred LIQUIDITY (insurance)
  - gcc_fintech_payment_outage      → inferred CYBER (fintech)
  - saudi_vision_mega_project_halt  → inferred ENERGY (mega-project)
  - gcc_sovereign_debt_crisis       → inferred LIQUIDITY (sovereign)

Consumed by: Stage 80 pipeline (runs FIRST, before all other engines)
Input: scenario_id + SCENARIO_CATALOG context
Output: ScenarioValidation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.config import SCENARIO_TAXONOMY

logger = logging.getLogger(__name__)

# ── Keyword → scenario type inference ─────────────────────────────────────

_KEYWORD_INFERENCE: list[tuple[list[str], str]] = [
    (["cyber", "grid", "outage", "infrastructure"], "CYBER"),
    (["banking", "financial", "liquidity", "reserve", "debt", "contagion", "sovereign"], "LIQUIDITY"),
    (["oil", "energy", "lng", "fuel", "power", "mega_project"], "ENERGY"),
    (["port", "maritime", "shipping", "hormuz", "sea", "trade_corridor"], "MARITIME"),
    (["regulation", "escalation", "sanctions", "geopolitical"], "REGULATORY"),
]

# ── Sector-majority inference ─────────────────────────────────────────────

_SECTOR_TO_TYPE: dict[str, str] = {
    "maritime":       "MARITIME",
    "logistics":      "MARITIME",
    "energy":         "ENERGY",
    "banking":        "LIQUIDITY",
    "fintech":        "CYBER",
    "insurance":      "LIQUIDITY",
    "infrastructure": "CYBER",
    "government":     "REGULATORY",
}

# ── Explicit fallback map for known unmapped scenarios ────────────────────

_EXPLICIT_FALLBACKS: dict[str, str] = {
    "gcc_power_grid_failure":          "CYBER",
    "difc_financial_contagion":        "LIQUIDITY",
    "gcc_insurance_reserve_shortfall": "LIQUIDITY",
    "gcc_fintech_payment_outage":      "CYBER",
    "saudi_vision_mega_project_halt":  "ENERGY",
    "gcc_sovereign_debt_crisis":       "LIQUIDITY",
}


@dataclass(frozen=True, slots=True)
class ScenarioValidation:
    """Scenario taxonomy enforcement result."""
    scenario_id: str

    # Resolved type
    scenario_type: str                  # Never empty — always resolved
    scenario_type_ar: str

    # Taxonomy status
    taxonomy_valid: bool                # True if found in SCENARIO_TAXONOMY
    fallback_applied: bool              # True if inferred/fallback was used
    fallback_method: str                # "none" | "explicit_map" | "keyword" | "sector_majority" | "default"

    # Classification confidence
    classification_confidence: float    # [0-1]: 1.0 = taxonomy, 0.80 = explicit, 0.60 = keyword, 0.40 = sector, 0.20 = default

    # Notes
    enforcement_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "scenario_type_ar": self.scenario_type_ar,
            "taxonomy_valid": self.taxonomy_valid,
            "fallback_applied": self.fallback_applied,
            "fallback_method": self.fallback_method,
            "classification_confidence": round(self.classification_confidence, 4),
            "enforcement_notes": self.enforcement_notes,
        }


# ── Type → Arabic label ──────────────────────────────────────────────────

_TYPE_AR: dict[str, str] = {
    "MARITIME":   "بحري",
    "ENERGY":     "طاقة",
    "LIQUIDITY":  "سيولة",
    "CYBER":      "سيبراني",
    "REGULATORY": "تنظيمي",
}


def enforce_scenario_taxonomy(
    scenario_id: str,
    scenario_catalog_entry: dict[str, Any] | None = None,
) -> ScenarioValidation:
    """
    Enforce strict scenario taxonomy — resolve type or apply fallback.

    Args:
        scenario_id:            The scenario ID to validate.
        scenario_catalog_entry: Optional SCENARIO_CATALOG dict for sector inference.

    Returns:
        ScenarioValidation — always has a resolved scenario_type (never empty).
    """
    notes: list[dict[str, str]] = []

    # ── Step 1: Direct taxonomy lookup ────────────────────────────────────
    direct_type = SCENARIO_TAXONOMY.get(scenario_id)
    if direct_type:
        return ScenarioValidation(
            scenario_id=scenario_id,
            scenario_type=direct_type,
            scenario_type_ar=_TYPE_AR.get(direct_type, "غير معروف"),
            taxonomy_valid=True,
            fallback_applied=False,
            fallback_method="none",
            classification_confidence=1.0,
            enforcement_notes=[{
                "type": "TAXONOMY_HIT",
                "message_en": f"Scenario '{scenario_id}' found in SCENARIO_TAXONOMY as {direct_type}",
                "message_ar": f"السيناريو '{scenario_id}' موجود في التصنيف كـ {direct_type}",
                "severity": "info",
            }],
        )

    # ── Step 2: Explicit fallback map ─────────────────────────────────────
    explicit = _EXPLICIT_FALLBACKS.get(scenario_id)
    if explicit:
        notes.append({
            "type": "EXPLICIT_FALLBACK",
            "message_en": f"Scenario '{scenario_id}' not in taxonomy — resolved via explicit fallback to {explicit}",
            "message_ar": f"السيناريو '{scenario_id}' غير موجود في التصنيف — تم حله عبر الخريطة الصريحة إلى {explicit}",
            "severity": "warning",
        })
        return ScenarioValidation(
            scenario_id=scenario_id,
            scenario_type=explicit,
            scenario_type_ar=_TYPE_AR.get(explicit, "غير معروف"),
            taxonomy_valid=False,
            fallback_applied=True,
            fallback_method="explicit_map",
            classification_confidence=0.85,
            enforcement_notes=notes,
        )

    # ── Step 3: Keyword inference from scenario_id ────────────────────────
    keyword_type = _infer_from_keywords(scenario_id)
    if keyword_type:
        notes.append({
            "type": "KEYWORD_INFERENCE",
            "message_en": f"Scenario '{scenario_id}' inferred as {keyword_type} from ID keywords",
            "message_ar": f"السيناريو '{scenario_id}' تم استنتاجه كـ {keyword_type} من كلمات المعرّف",
            "severity": "warning",
        })
        return ScenarioValidation(
            scenario_id=scenario_id,
            scenario_type=keyword_type,
            scenario_type_ar=_TYPE_AR.get(keyword_type, "غير معروف"),
            taxonomy_valid=False,
            fallback_applied=True,
            fallback_method="keyword",
            classification_confidence=0.65,
            enforcement_notes=notes,
        )

    # ── Step 4: Sector-majority inference from catalog ────────────────────
    if scenario_catalog_entry:
        sectors = scenario_catalog_entry.get("sectors_affected", [])
        sector_type = _infer_from_sectors(sectors)
        if sector_type:
            notes.append({
                "type": "SECTOR_INFERENCE",
                "message_en": f"Scenario '{scenario_id}' inferred as {sector_type} from affected sectors {sectors}",
                "message_ar": f"السيناريو '{scenario_id}' تم استنتاجه كـ {sector_type} من القطاعات المتأثرة",
                "severity": "warning",
            })
            return ScenarioValidation(
                scenario_id=scenario_id,
                scenario_type=sector_type,
                scenario_type_ar=_TYPE_AR.get(sector_type, "غير معروف"),
                taxonomy_valid=False,
                fallback_applied=True,
                fallback_method="sector_majority",
                classification_confidence=0.45,
                enforcement_notes=notes,
            )

    # ── Step 5: Default fallback ──────────────────────────────────────────
    notes.append({
        "type": "DEFAULT_FALLBACK",
        "message_en": f"Scenario '{scenario_id}' completely unresolved — defaulting to REGULATORY",
        "message_ar": f"السيناريو '{scenario_id}' غير قابل للحل — الافتراضي تنظيمي",
        "severity": "critical",
    })
    return ScenarioValidation(
        scenario_id=scenario_id,
        scenario_type="REGULATORY",
        scenario_type_ar="تنظيمي",
        taxonomy_valid=False,
        fallback_applied=True,
        fallback_method="default",
        classification_confidence=0.20,
        enforcement_notes=notes,
    )


def _infer_from_keywords(scenario_id: str) -> str | None:
    """Infer scenario type from ID keywords."""
    sid_lower = scenario_id.lower()
    for keywords, stype in _KEYWORD_INFERENCE:
        if any(kw in sid_lower for kw in keywords):
            return stype
    return None


def _infer_from_sectors(sectors: list[str]) -> str | None:
    """Infer scenario type from sector majority."""
    if not sectors:
        return None
    type_votes: dict[str, int] = {}
    for sector in sectors:
        stype = _SECTOR_TO_TYPE.get(sector)
        if stype:
            type_votes[stype] = type_votes.get(stype, 0) + 1
    if not type_votes:
        return None
    return max(type_votes, key=type_votes.get)
