"""
Impact Observatory | مرصد الأثر
Signal Connectors — pluggable source connectors for signal ingestion.

v3 pilot: one RSS connector using static fixture data.
No live network calls. No secrets required.
"""
from __future__ import annotations

from src.signal_ingestion.connectors.base import BaseConnector, ConnectorStatus
from src.signal_ingestion.connectors.rss_connector import RSSConnector

__all__ = [
    "BaseConnector",
    "ConnectorStatus",
    "RSSConnector",
]
