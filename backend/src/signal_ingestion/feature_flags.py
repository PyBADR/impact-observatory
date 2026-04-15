"""
Impact Observatory | مرصد الأثر
Signal Ingestion Feature Flags — safe dev/test-only activation gates.

All flags default to False. They are read from environment variables
so they can be enabled in development without code changes.

Production deployments must NOT set these to true.
"""
from __future__ import annotations

import os


def _env_bool(key: str, default: bool = False) -> bool:
    """Read a boolean from an environment variable.

    Accepts: "true", "1", "yes" (case-insensitive) → True
    Everything else (including unset) → default.
    """
    val = os.environ.get(key, "").strip().lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


# ═══════════════════════════════════════════════════════════════════════════════
# Feature Flags
# ═══════════════════════════════════════════════════════════════════════════════

def is_dev_signal_preview_enabled() -> bool:
    """Whether the dev signal snapshot preview is active.

    Reads: ENABLE_DEV_SIGNAL_PREVIEW (default: false)

    When true:
      - /internal/signal-snapshots/preview endpoint returns data
      - Frontend dev preview panel is visible
      - RSS fixture connector is temporarily activated

    When false (default, production):
      - Endpoint returns 404
      - Panel is hidden
      - Connector stays disabled
    """
    return _env_bool("ENABLE_DEV_SIGNAL_PREVIEW", default=False)


def is_live_signal_scoring_enabled() -> bool:
    """Whether live signals affect scoring (gated by governance decision gate).

    Reads: ENABLE_SIGNAL_SCORING_V5 (default: false)

    When true: signals may influence scenario metrics (if governance gate passes).
    When false (default, production): signals are advisory-only.

    See docs/GOVERNANCE_DECISION_GATE_V5.md for full policy.
    """
    return _env_bool("ENABLE_SIGNAL_SCORING_V5", default=False)
