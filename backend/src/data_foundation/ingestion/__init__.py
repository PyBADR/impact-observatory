"""P1 Data Foundation — Ingestion Layer.

Complete ingestion pipeline: contracts (WHAT) + pipeline (HOW) + loaders (WHERE FROM).

Data Flow:
  Source → Loader → Raw Records → Pipeline (map → validate → dedup → tag) → Normalized Records

NOTE: Import modules directly to avoid circular dependency with validation.
  - from src.data_foundation.ingestion.contracts import ...
  - from src.data_foundation.ingestion.pipeline import ...
  - from src.data_foundation.ingestion.loaders import ...
"""

# Only export contracts from __init__ (no circular dep).
# pipeline.py and loaders.py import from validation, so re-exporting them
# here would create: ingestion.__init__ → pipeline → validation → ingestion.contracts → cycle.
from src.data_foundation.ingestion.contracts import *  # noqa: F401,F403
