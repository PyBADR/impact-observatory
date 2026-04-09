"""Audit hasher — SHA-256 digest generation for IFRS-17 audit trail.

Produces immutable hash chain: impact_hash + decision_hash → combined_hash.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from src.utils import now_utc

logger = logging.getLogger(__name__)


def _stable_json(obj: Any) -> str:
    """Produce stable JSON for hashing (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def compute_audit_digest(
    impact_assessment: dict[str, Any],
    decision_output: dict[str, Any],
) -> dict[str, Any]:
    """Compute SHA-256 audit digest for impact + decision.

    Returns AuditDigest-compatible dict.
    Never raises — returns ERROR hash on failure.
    """
    timestamp = now_utc()

    try:
        impact_json = _stable_json(impact_assessment)
        impact_hash = hashlib.sha256(impact_json.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.warning("[AuditHasher] impact hash failed: %s", e)
        impact_hash = f"ERROR:{e}"

    try:
        decision_json = _stable_json(decision_output)
        decision_hash = hashlib.sha256(decision_json.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.warning("[AuditHasher] decision hash failed: %s", e)
        decision_hash = f"ERROR:{e}"

    try:
        combined_input = f"{impact_hash}:{decision_hash}"
        combined_hash = hashlib.sha256(combined_input.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.warning("[AuditHasher] combined hash failed: %s", e)
        combined_hash = f"ERROR:{e}"

    return {
        "impact_hash": impact_hash,
        "decision_hash": decision_hash,
        "combined_hash": combined_hash,
        "timestamp": timestamp,
        "pipeline_version": "2.1.0",
        "pack_version": "3.0.0",
    }
