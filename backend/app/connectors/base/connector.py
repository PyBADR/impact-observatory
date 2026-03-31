"""
Abstract base connector for data source integration.
All data source connectors inherit from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import time


@dataclass
class IngestResult:
    """Result of a data ingestion operation."""

    records_fetched: int = 0
    records_normalized: int = 0
    records_stored: int = 0
    errors: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    ingestion_timestamp: datetime = field(default_factory=datetime.utcnow)
    source_id: Optional[str] = None
    source_type: Optional[str] = None

    def add_error(self, error_msg: str, record: Optional[dict] = None):
        """Add error to errors list."""
        self.errors.append(
            {
                "message": error_msg,
                "record": record,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.records_fetched == 0:
            return 0.0
        return (self.records_stored / self.records_fetched) * 100


class BaseEntity:
    """Base class for entities in canonical schema."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """Convert entity to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class BaseConnector(ABC):
    """
    Abstract base class for all data source connectors.

    Connectors are responsible for:
    1. Fetching raw data from a source (fetch_raw)
    2. Normalizing raw data to canonical schema (normalize)
    3. Full ingestion pipeline (ingest)
    """

    def __init__(self, source_id: str, source_type: str):
        """
        Initialize connector.

        Args:
            source_id: Unique identifier for the source
            source_type: Type of source (e.g., "acled", "gdelt", "custom_api")
        """
        self.source_id = source_id
        self.source_type = source_type

    @abstractmethod
    async def fetch_raw(self, params: dict) -> list[dict]:
        """
        Fetch raw data from source.

        Args:
            params: Query parameters (date range, filters, pagination, etc.)

        Returns:
            List of raw record dictionaries from source

        Raises:
            Exception: If API call fails or network error occurs
        """
        pass

    @abstractmethod
    def normalize(self, raw: dict) -> Optional[BaseEntity]:
        """
        Normalize raw source record to canonical schema.

        Args:
            raw: Raw record from source

        Returns:
            Normalized entity in canonical schema, or None if validation fails

        Raises:
            ValueError: If normalization/validation fails
        """
        pass

    @abstractmethod
    async def ingest(self, params: dict) -> IngestResult:
        """
        Full data ingestion pipeline.

        Steps:
        1. Fetch raw data
        2. Normalize each record
        3. Store in database
        4. Return ingestion result

        Args:
            params: Query parameters for fetch_raw

        Returns:
            IngestResult with statistics and error tracking
        """
        pass

    def validate_raw_record(self, record: dict) -> tuple[bool, Optional[str]]:
        """
        Validate raw record before normalization.

        Args:
            record: Raw record to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(record, dict):
            return False, "Record is not a dictionary"
        return True, None

    async def _measure_duration(self, operation_name: str):
        """Context manager to measure operation duration."""
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def measure():
            start = time.time()
            try:
                yield
            finally:
                duration_ms = (time.time() - start) * 1000

        return measure()


class Event(BaseEntity):
    """Canonical Event entity."""

    def __init__(
        self,
        event_id: str,
        event_date: datetime,
        event_type: str,
        location_name: str,
        country: str,
        description: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        fatalities: int = 0,
        wounded: int = 0,
        **kwargs
    ):
        self.event_id = event_id
        self.event_date = event_date
        self.event_type = event_type
        self.location_name = location_name
        self.country = country
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.fatalities = fatalities
        self.wounded = wounded
        for key, value in kwargs.items():
            setattr(self, key, value)


class Incident(BaseEntity):
    """Canonical Incident entity."""

    def __init__(
        self,
        incident_code: str,
        incident_type: str,
        title: str,
        description: str,
        start_date: datetime,
        countries: list[str],
        **kwargs
    ):
        self.incident_code = incident_code
        self.incident_type = incident_type
        self.title = title
        self.description = description
        self.start_date = start_date
        self.countries = countries
        for key, value in kwargs.items():
            setattr(self, key, value)


class Alert(BaseEntity):
    """Canonical Alert entity."""

    def __init__(
        self,
        alert_code: str,
        alert_type: str,
        title: str,
        description: str,
        severity: str,
        triggered_at: datetime,
        **kwargs
    ):
        self.alert_code = alert_code
        self.alert_type = alert_type
        self.title = title
        self.description = description
        self.severity = severity
        self.triggered_at = triggered_at
        for key, value in kwargs.items():
            setattr(self, key, value)


class Signal(BaseEntity):
    """Canonical Signal entity."""

    def __init__(
        self,
        signal_code: str,
        signal_type: str,
        indicator: str,
        value: float,
        signal_date: datetime,
        **kwargs
    ):
        self.signal_code = signal_code
        self.signal_type = signal_type
        self.indicator = indicator
        self.value = value
        self.signal_date = signal_date
        for key, value in kwargs.items():
            setattr(self, key, value)


class Actor(BaseEntity):
    """Canonical Actor entity."""

    def __init__(
        self,
        actor_code: str,
        name: str,
        actor_type: str,
        **kwargs
    ):
        self.actor_code = actor_code
        self.name = name
        self.actor_type = actor_type
        for key, value in kwargs.items():
            setattr(self, key, value)
