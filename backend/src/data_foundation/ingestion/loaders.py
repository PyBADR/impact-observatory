"""
P1 Ingestion Loaders — Source Adapters
=========================================

Concrete loader implementations for each ingestion method:
  - APILoader: Fetch from REST/JSON APIs (central banks, OPEC, ACLED)
  - CSVLoader: Parse CSV/TSV files (manual uploads, bulk imports)
  - ManualLoader: Accept analyst-provided dicts (decision rules, overrides)
  - DerivedLoader: Compute derived signals from existing datasets

Each loader produces List[Dict[str, Any]] — the universal raw format
consumed by run_ingestion_pipeline().

Architecture Layer: Data (Layer 1 — source boundary)
Owner: Data Engineering
"""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Loader Base
# ═══════════════════════════════════════════════════════════════════════════════

class LoaderConfig(BaseModel):
    """Configuration for a loader instance."""
    source_id: str = Field(..., description="FK to source_registry.")
    dataset_id: str = Field(..., description="FK to dataset_registry.")
    batch_size: int = Field(default=1000, ge=1)
    timeout_seconds: int = Field(default=30, ge=1)
    retry_count: int = Field(default=3, ge=0)
    retry_delay_seconds: float = Field(default=1.0, ge=0)


class LoaderResult(BaseModel):
    """Result from a loader fetch operation."""
    source_id: str
    dataset_id: str
    records: List[Dict[str, Any]]
    record_count: int
    fetched_at: datetime
    raw_metadata: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)


class BaseLoader(ABC):
    """Abstract base for all ingestion loaders."""

    def __init__(self, config: LoaderConfig):
        self.config = config

    @abstractmethod
    def fetch(self, **kwargs: Any) -> LoaderResult:
        """Fetch raw records from the source. Returns LoaderResult."""
        ...

    def _make_result(
        self,
        records: List[Dict[str, Any]],
        errors: Optional[List[str]] = None,
        raw_metadata: Optional[Dict[str, Any]] = None,
    ) -> LoaderResult:
        return LoaderResult(
            source_id=self.config.source_id,
            dataset_id=self.config.dataset_id,
            records=records,
            record_count=len(records),
            fetched_at=datetime.now(timezone.utc),
            raw_metadata=raw_metadata,
            errors=errors or [],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# API Loader
# ═══════════════════════════════════════════════════════════════════════════════

class APILoader(BaseLoader):
    """Fetch records from a REST/JSON API endpoint.

    Production use: Central bank APIs, OPEC MOMR, ACLED, IMF WEO.
    In P1 this implements the interface contract — actual HTTP calls
    require httpx or aiohttp (added in P2 when real endpoints are connected).

    Usage:
        loader = APILoader(config)
        result = loader.fetch(url="https://api.example.com/data", headers={...})
    """

    def fetch(
        self,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        response_data: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LoaderResult:
        """Fetch from API. If response_data is provided, use that directly
        (for testing and seed loading). Otherwise, this is the integration point
        for httpx in P2.
        """
        if response_data is not None:
            return self._make_result(
                records=response_data,
                raw_metadata={"url": url, "method": "GET", "params": params},
            )

        # P2: Replace with actual HTTP fetch
        # import httpx
        # response = httpx.get(url, headers=headers, params=params, timeout=self.config.timeout_seconds)
        # response.raise_for_status()
        # data = response.json()
        # records = data if isinstance(data, list) else data.get("data", data.get("results", []))

        return self._make_result(
            records=[],
            errors=[f"API fetch not yet connected. URL: {url}. Connect in P2."],
            raw_metadata={"url": url, "status": "not_connected"},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CSV Loader
# ═══════════════════════════════════════════════════════════════════════════════

class CSVLoader(BaseLoader):
    """Parse records from CSV/TSV files.

    Supports:
      - File path on disk
      - Raw string content
      - Custom delimiters
      - Header row mapping

    Usage:
        loader = CSVLoader(config)
        result = loader.fetch(file_path="/data/cbk_bulletin.csv")
        result = loader.fetch(content="col1,col2\nval1,val2", delimiter=",")
    """

    def fetch(
        self,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> LoaderResult:
        try:
            if file_path is not None:
                path = Path(file_path)
                if not path.exists():
                    return self._make_result(
                        records=[],
                        errors=[f"File not found: {file_path}"],
                    )
                text = path.read_text(encoding=encoding)
            elif content is not None:
                text = content
            else:
                return self._make_result(
                    records=[],
                    errors=["No file_path or content provided."],
                )

            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            records = [dict(row) for row in reader]

            return self._make_result(
                records=records,
                raw_metadata={
                    "file_path": file_path,
                    "delimiter": delimiter,
                    "header": reader.fieldnames,
                },
            )
        except Exception as e:
            return self._make_result(
                records=[],
                errors=[f"CSV parse error: {e}"],
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Manual Loader
# ═══════════════════════════════════════════════════════════════════════════════

class ManualLoader(BaseLoader):
    """Accept manually provided records (analyst desk, decision rules, overrides).

    Usage:
        loader = ManualLoader(config)
        result = loader.fetch(records=[{"rule_id": "RULE-001", ...}])
    """

    def fetch(
        self,
        records: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LoaderResult:
        if records is None:
            return self._make_result(
                records=[],
                errors=["No records provided for manual ingestion."],
            )

        return self._make_result(
            records=records,
            raw_metadata={"method": "manual", "record_count": len(records)},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Derived Signal Loader
# ═══════════════════════════════════════════════════════════════════════════════

class DerivedLoader(BaseLoader):
    """Compute derived signals from existing P1 datasets.

    Examples:
      - YoY change computation from macro_indicators
      - FX peg deviation from fx_signals + peg rates
      - Stress index from banking profiles

    Usage:
        loader = DerivedLoader(config)
        result = loader.fetch(
            compute_fn=my_derivation_function,
            input_data=existing_records,
        )
    """

    def fetch(
        self,
        compute_fn: Optional[Any] = None,
        input_data: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LoaderResult:
        if compute_fn is None or input_data is None:
            return self._make_result(
                records=[],
                errors=["DerivedLoader requires compute_fn and input_data."],
            )

        try:
            derived_records = compute_fn(input_data)
            if not isinstance(derived_records, list):
                derived_records = [derived_records]

            return self._make_result(
                records=derived_records,
                raw_metadata={"method": "derived", "input_count": len(input_data)},
            )
        except Exception as e:
            return self._make_result(
                records=[],
                errors=[f"Derivation error: {e}"],
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Loader Factory
# ═══════════════════════════════════════════════════════════════════════════════

LOADER_REGISTRY: Dict[str, type] = {
    "API": APILoader,
    "FEED": APILoader,
    "WEBHOOK": APILoader,
    "CSV_UPLOAD": CSVLoader,
    "RSS": CSVLoader,       # RSS adapts through existing signal layer
    "MANUAL": ManualLoader,
    "GOVERNMENT": APILoader,
    "DATABASE": APILoader,
    "INTERNAL_MODEL": DerivedLoader,
    "SCRAPER": APILoader,
    "SENSOR": APILoader,
    "SATELLITE": APILoader,
}


def get_loader(source_type: str, config: LoaderConfig) -> BaseLoader:
    """Factory: get the appropriate loader for a source type.

    Args:
        source_type: SourceType enum value (e.g., 'API', 'CSV_UPLOAD', 'MANUAL')
        config: LoaderConfig with source_id, dataset_id, etc.

    Returns:
        Concrete loader instance

    Raises:
        ValueError: If source_type is not registered
    """
    loader_cls = LOADER_REGISTRY.get(source_type)
    if loader_cls is None:
        raise ValueError(
            f"No loader registered for source type '{source_type}'. "
            f"Available: {sorted(LOADER_REGISTRY.keys())}"
        )
    return loader_cls(config)
