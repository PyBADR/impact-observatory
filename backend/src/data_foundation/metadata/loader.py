"""
P1 Data Foundation — Seed Data Loader
=======================================

Utility to load, validate, and return typed seed data from JSON files.
Used by tests, development server, and initial database seeding.

Usage:
    from src.data_foundation.metadata.loader import load_seed_data
    entities = load_seed_data("entity_registry", EntityRegistryEntry)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

SEED_DIR = Path(__file__).parent.parent / "seed"

# Map dataset shortname → seed filename
SEED_FILE_MAP: Dict[str, str] = {
    "dataset_registry": "dataset_registry_seed.json",
    "source_registry": "source_registry_seed.json",
    "entity_registry": "entity_registry_seed.json",
    "macro_indicators": "macro_indicators_seed.json",
    "interest_rate_signals": "interest_rate_signals_seed.json",
    "oil_energy_signals": "oil_energy_signals_seed.json",
    "fx_signals": "fx_signals_seed.json",
    "cbk_indicators": "cbk_indicators_seed.json",
    "event_signals": "event_signals_seed.json",
    "banking_profiles": "banking_profiles_seed.json",
    "insurance_profiles": "insurance_profiles_seed.json",
    "logistics_nodes": "logistics_nodes_seed.json",
    "decision_rules": "decision_rules_seed.json",
    "decision_logs": "decision_logs_seed.json",
}


def load_seed_json(dataset_name: str) -> List[dict]:
    """Load raw JSON seed data for a dataset."""
    filename = SEED_FILE_MAP.get(dataset_name)
    if filename is None:
        raise ValueError(
            f"Unknown dataset '{dataset_name}'. "
            f"Available: {sorted(SEED_FILE_MAP.keys())}"
        )
    filepath = SEED_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Seed file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Seed file must contain a JSON array: {filepath}")
    return data


def load_seed_data(dataset_name: str, model_class: Type[T]) -> List[T]:
    """Load and validate seed data into Pydantic model instances.

    Args:
        dataset_name: Short name from SEED_FILE_MAP (e.g., 'entity_registry')
        model_class: Pydantic model class to validate against

    Returns:
        List of validated model instances

    Raises:
        ValueError: If dataset name unknown or data fails validation
        FileNotFoundError: If seed file missing
    """
    raw_data = load_seed_json(dataset_name)
    validated: List[T] = []
    errors: List[str] = []

    for i, record in enumerate(raw_data):
        try:
            validated.append(model_class.model_validate(record))
        except Exception as e:
            errors.append(f"Record {i}: {e}")

    if errors:
        error_summary = "\n".join(errors[:10])  # Show first 10
        raise ValueError(
            f"Seed data validation failed for '{dataset_name}' "
            f"({len(errors)}/{len(raw_data)} records):\n{error_summary}"
        )

    return validated


def load_all_seeds() -> Dict[str, List[dict]]:
    """Load all available seed files as raw dicts (no validation)."""
    result = {}
    for name in SEED_FILE_MAP:
        try:
            result[name] = load_seed_json(name)
        except (FileNotFoundError, ValueError):
            result[name] = []
    return result
