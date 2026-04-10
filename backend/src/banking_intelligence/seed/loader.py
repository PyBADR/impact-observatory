"""
Seed Data Loader for Banking Intelligence

Loads gcc_full_population.json into the in-memory entity store
and ingestion dedup registry. Called at startup and available
as an API endpoint for reloading.
"""

import json
from pathlib import Path
from typing import Any

SEED_DIR = Path(__file__).parent
FULL_POPULATION_FILE = SEED_DIR / "gcc_full_population.json"


def load_seed_data() -> dict[str, Any]:
    """
    Load and return parsed seed data from gcc_full_population.json.

    Returns dict with keys:
        _meta, countries, authorities, banks, fintechs, payment_rails, edges
    """
    if not FULL_POPULATION_FILE.exists():
        return {"error": f"Seed file not found: {FULL_POPULATION_FILE}"}

    with open(FULL_POPULATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_entity_store(entity_store: dict[str, dict]) -> dict[str, int]:
    """
    Populate the in-memory entity store used by the entities API.

    Args:
        entity_store: The _entity_store dict from entities.py

    Returns:
        Dict with counts per entity type loaded
    """
    data = load_seed_data()
    if "error" in data:
        return {"error": 1}

    counts: dict[str, int] = {}

    # Load each entity type
    entity_sections = [
        ("countries", "country"),
        ("authorities", "authority"),
        ("banks", "bank"),
        ("fintechs", "fintech"),
        ("payment_rails", "payment_rail"),
    ]

    for section_key, entity_type in entity_sections:
        items = data.get(section_key, [])
        for item in items:
            canonical_id = item.get("canonical_id", "")
            if canonical_id:
                entity_store[canonical_id] = {
                    "entity_type": entity_type,
                    **item,
                }
        counts[entity_type] = len(items)

    # Store edges separately under a special key
    edges = data.get("edges", [])
    entity_store["__edges__"] = {"items": edges}
    counts["edges"] = len(edges)

    return counts
