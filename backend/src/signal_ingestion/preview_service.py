"""
Impact Observatory | مرصد الأثر
Snapshot Preview Service — dev/test-only signal snapshot generation.

This service:
  - Explicitly enables the RSS fixture connector in dev mode
  - Loads the local RSS fixture (NO network calls)
  - Returns SignalSnapshot records with freshness/confidence/audit
  - NEVER changes scenario outputs
  - NEVER calls the internet

Usage:
  from src.signal_ingestion.preview_service import get_dev_preview
  result = get_dev_preview()
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.signal_ingestion.connectors.rss_connector import RSSConnector, PILOT_RSS_SOURCE
from src.signal_ingestion.models import SignalSnapshot
from src.signal_ingestion.audit_log import SignalAuditLog
from src.signal_ingestion.feature_flags import is_dev_signal_preview_enabled


# ── Fixture path ─────────────────────────────────────────────────────

_FIXTURE_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"
_RSS_FIXTURE = _FIXTURE_DIR / "sample_rss_feed.xml"


def get_dev_preview(
    *,
    max_snapshots: int = 5,
    ingested_at: str | None = None,
) -> dict[str, Any]:
    """Generate a dev-only signal snapshot preview.

    Returns a dict with snapshots, audit summary, and metadata.
    Returns a disabled/empty response if the feature flag is off.

    This function:
      - Reads from local RSS fixture ONLY
      - Makes ZERO network calls
      - Does NOT modify scenario outputs
    """
    now = ingested_at or datetime.now(timezone.utc).isoformat()

    # Gate: feature flag must be enabled
    if not is_dev_signal_preview_enabled():
        return {
            "enabled": False,
            "reason": "ENABLE_DEV_SIGNAL_PREVIEW is not set to true.",
            "snapshots": [],
            "snapshot_count": 0,
            "audit_summary": {},
            "source_mode": "disabled",
            "generated_at": now,
        }

    # Gate: fixture file must exist
    if not _RSS_FIXTURE.exists():
        return {
            "enabled": True,
            "reason": f"RSS fixture not found at {_RSS_FIXTURE}",
            "snapshots": [],
            "snapshot_count": 0,
            "audit_summary": {},
            "source_mode": "error",
            "generated_at": now,
        }

    # Create connector with explicit dev enable
    connector = RSSConnector(
        fixture_path=_RSS_FIXTURE,
        enabled=True,  # Explicitly enabled for dev preview
    )

    # Run health check
    audit_log = SignalAuditLog()
    health = connector.health_check(audit_log=audit_log)

    # Normalize snapshots
    snapshots = connector.normalize(
        audit_log=audit_log,
        ingested_at=now,
    )

    # Limit output
    limited = snapshots[:max_snapshots]

    return {
        "enabled": True,
        "reason": "Dev fixture preview active.",
        "snapshots": [s.to_dict() for s in limited],
        "snapshot_count": len(snapshots),
        "connector_status": health.value,
        "connector_state": connector.to_dict(),
        "audit_summary": audit_log.summary(),
        "audit_entries": audit_log.to_list(),
        "source_mode": "dev_fixture",
        "fixture_path": str(_RSS_FIXTURE),
        "scoring_impact": "none",
        "generated_at": now,
        "notice": "Dev fixture preview — does not affect scenario scoring. "
                  "Live feeds not connected.",
    }
