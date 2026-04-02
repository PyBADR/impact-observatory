"""
NormalizationService - Unified data pipeline orchestration for all connectors.

Manages connector registration, pipeline execution, and result aggregation for the
Impact Observatory Engine. Provides unified error handling, logging, and
metrics collection across all data sources.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from app.connectors.base.connector import BaseConnector, IngestResult
from app.connectors import (
    ACLEDConnector,
    AviationConnector,
    MaritimeConnector,
    CSVImportConnector,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Aggregated metrics from pipeline execution."""
    
    total_duration: float
    fetch_duration: float
    normalize_duration: float
    store_duration: float
    total_records_fetched: int
    total_records_normalized: int
    total_records_stored: int
    total_errors: int
    errors_by_connector: Dict[str, int] = field(default_factory=dict)
    execution_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "total_duration": self.total_duration,
            "fetch_duration": self.fetch_duration,
            "normalize_duration": self.normalize_duration,
            "store_duration": self.store_duration,
            "total_records_fetched": self.total_records_fetched,
            "total_records_normalized": self.total_records_normalized,
            "total_records_stored": self.total_records_stored,
            "total_errors": self.total_errors,
            "errors_by_connector": self.errors_by_connector,
            "execution_timestamp": self.execution_timestamp.isoformat(),
        }


class NormalizationService:
    """
    Unified data pipeline orchestration for Impact Observatory.

    Manages all data connectors, coordinates pipeline execution, aggregates results,
    and provides error handling and metrics collection across all data sources
    (ACLED, Aviation, Maritime, CSV imports).
    """
    
    def __init__(self):
        """Initialize the NormalizationService with all available connectors."""
        self.connectors: Dict[str, BaseConnector] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._register_default_connectors()
    
    def _register_default_connectors(self) -> None:
        """Register the default production connectors."""
        self.register_connector("acled", ACLEDConnector())
        self.register_connector("aviation", AviationConnector())
        self.register_connector("maritime", MaritimeConnector())
        self.register_connector("csv_import", CSVImportConnector())
        logger.info("NormalizationService initialized with 4 default connectors")
    
    def register_connector(self, name: str, connector: BaseConnector) -> None:
        """
        Register a connector with the pipeline.
        
        Args:
            name: Unique identifier for the connector
            connector: Instantiated connector implementing BaseConnector
            
        Raises:
            ValueError: If connector doesn't implement BaseConnector interface
        """
        if not isinstance(connector, BaseConnector):
            raise ValueError(
                f"Connector '{name}' must implement BaseConnector interface"
            )
        
        self.connectors[name] = connector
        logger.info(f"Registered connector: {name}")
    
    async def run_pipeline(
        self,
        connector_name: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> IngestResult:
        """
        Execute a single connector's pipeline (fetch → normalize → ingest).
        
        Args:
            connector_name: Name of the registered connector to execute
            params: Optional parameters to pass to the connector
            
        Returns:
            IngestResult with metrics from the pipeline execution
            
        Raises:
            ValueError: If connector not found
            Exception: Propagated from connector execution with logging
        """
        if connector_name not in self.connectors:
            raise ValueError(
                f"Connector '{connector_name}' not registered. "
                f"Available: {list(self.connectors.keys())}"
            )
        
        connector = self.connectors[connector_name]
        params = params or {}
        
        try:
            logger.info(
                f"Starting pipeline for connector '{connector_name}' "
                f"with params: {params}"
            )
            result = await connector.ingest(params)
            
            logger.info(
                f"Pipeline '{connector_name}' completed: "
                f"fetched={result.records_fetched}, "
                f"normalized={result.records_normalized}, "
                f"stored={result.records_stored}, "
                f"errors={len(result.errors)}, "
                f"duration={result.total_duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Pipeline execution failed for '{connector_name}': {str(e)}",
                exc_info=True,
            )
            raise
    
    async def run_all(
        self,
        params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute all registered connectors in parallel.
        
        Orchestrates concurrent execution of all connectors, aggregates results,
        and provides comprehensive metrics and error reporting.
        
        Args:
            params: Optional dict mapping connector names to their parameters.
                   Example: {"acled": {"start_date": "2024-01-01"}, ...}
        
        Returns:
            Dictionary containing:
                - "results": Dict[str, IngestResult] for each connector
                - "metrics": PipelineMetrics with aggregated statistics
                - "success": Boolean indicating if all connectors succeeded
                - "execution_timestamp": When the pipeline executed
        """
        params = params or {}
        
        logger.info(f"Starting parallel execution of {len(self.connectors)} connectors")
        start_time = datetime.utcnow()
        
        # Create tasks for all connectors
        tasks = {
            name: self.run_pipeline(name, params.get(name))
            for name in self.connectors
        }
        
        # Execute all tasks concurrently
        results = {}
        errors_by_connector = {}
        
        for connector_name, task in tasks.items():
            try:
                results[connector_name] = await task
            except Exception as e:
                error_msg = str(e)
                errors_by_connector[connector_name] = 1
                results[connector_name] = IngestResult(
                    records_fetched=0,
                    records_normalized=0,
                    records_stored=0,
                    errors=[error_msg],
                    fetch_duration=0.0,
                    normalize_duration=0.0,
                    store_duration=0.0,
                )
                logger.error(
                    f"Connector '{connector_name}' failed: {error_msg}",
                    exc_info=True,
                )
        
        # Aggregate metrics
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        
        metrics = PipelineMetrics(
            total_duration=total_duration,
            fetch_duration=sum(r.fetch_duration for r in results.values()),
            normalize_duration=sum(r.normalize_duration for r in results.values()),
            store_duration=sum(r.store_duration for r in results.values()),
            total_records_fetched=sum(r.records_fetched for r in results.values()),
            total_records_normalized=sum(
                r.records_normalized for r in results.values()
            ),
            total_records_stored=sum(r.records_stored for r in results.values()),
            total_errors=sum(len(r.errors) for r in results.values()),
            errors_by_connector=errors_by_connector,
        )
        
        success = all(len(r.errors) == 0 for r in results.values())
        
        execution_summary = {
            "results": {
                name: {
                    "records_fetched": result.records_fetched,
                    "records_normalized": result.records_normalized,
                    "records_stored": result.records_stored,
                    "errors": result.errors,
                    "fetch_duration": result.fetch_duration,
                    "normalize_duration": result.normalize_duration,
                    "store_duration": result.store_duration,
                    "total_duration": result.total_duration,
                }
                for name, result in results.items()
            },
            "metrics": metrics.to_dict(),
            "success": success,
            "execution_timestamp": start_time.isoformat(),
        }
        
        self.execution_history.append(execution_summary)
        
        logger.info(
            f"Pipeline execution completed: "
            f"success={success}, "
            f"total_records_stored={metrics.total_records_stored}, "
            f"total_errors={metrics.total_errors}, "
            f"total_duration={metrics.total_duration:.2f}s"
        )
        
        return execution_summary
    
    def get_execution_history(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve execution history.
        
        Args:
            limit: Maximum number of recent executions to return.
                   If None, returns all history.
        
        Returns:
            List of execution summaries in reverse chronological order.
        """
        history = self.execution_history
        if limit:
            history = history[-limit:]
        return list(reversed(history))
    
    def get_connector_stats(self, connector_name: str) -> Dict[str, Any]:
        """
        Get aggregated statistics for a specific connector from execution history.
        
        Args:
            connector_name: Name of the connector to get stats for
            
        Returns:
            Dictionary with aggregated statistics across all executions
        """
        if not self.execution_history:
            return {"error": "No execution history available"}
        
        connector_results = []
        for execution in self.execution_history:
            if connector_name in execution["results"]:
                connector_results.append(execution["results"][connector_name])
        
        if not connector_results:
            return {"error": f"No results found for connector '{connector_name}'"}
        
        return {
            "executions": len(connector_results),
            "total_records_fetched": sum(
                r["records_fetched"] for r in connector_results
            ),
            "total_records_normalized": sum(
                r["records_normalized"] for r in connector_results
            ),
            "total_records_stored": sum(
                r["records_stored"] for r in connector_results
            ),
            "total_errors": sum(len(r["errors"]) for r in connector_results),
            "avg_total_duration": sum(
                r["total_duration"] for r in connector_results
            ) / len(connector_results),
        }
    
    def clear_history(self) -> None:
        """Clear all execution history."""
        self.execution_history.clear()
        logger.info("Execution history cleared")
