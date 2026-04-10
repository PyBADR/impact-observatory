"""Impact Observatory | مرصد الأثر — Orchestration.

Re-exports run_orchestrator for clean import paths.
"""
from src.services.run_orchestrator import execute_run

__all__ = ["execute_run"]
