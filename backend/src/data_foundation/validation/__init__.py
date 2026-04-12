"""P1 Data Foundation — Validation Framework.

Three validation layers:
  1. validators.py  — Quality gate evaluation (per-record, per-contract)
  2. integrity.py   — Referential integrity (cross-dataset FK checks)
  3. entrypoint.py  — Single-call full P1 validation

NOTE: Import modules directly for pipeline/loader use:
  - from src.data_foundation.validation.validators import validate_record
  - from src.data_foundation.validation.integrity import check_referential_integrity
  - from src.data_foundation.validation.entrypoint import validate_all_p1
"""

from src.data_foundation.validation.validators import *  # noqa: F401,F403
from src.data_foundation.validation.integrity import *  # noqa: F401,F403
