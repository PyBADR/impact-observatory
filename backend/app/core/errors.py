"""
Impact Observatory | مرصد الأثر — Global Error System (v4 §5)
Structured error envelope and standard error codes.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid


class ObservatoryError(Exception):
    """Base error with structured envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int,
        recoverable: bool = False,
        retryable: bool = False,
        fallback_mode: str = "none",
        details: Optional[List[dict]] = None,
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.recoverable = recoverable
        self.retryable = retryable
        self.fallback_mode = fallback_mode
        self.details = details or []
        super().__init__(message)

    def to_envelope(self) -> dict:
        """v4 §5 exact error envelope."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "http_status": self.http_status,
                "recoverable": self.recoverable,
                "retryable": self.retryable,
                "fallback_mode": self.fallback_mode,
                "details": self.details,
                "trace_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        }


# ============================================================================
# v4 §5.1 — Standard Error Codes
# ============================================================================

class InvalidJsonError(ObservatoryError):
    def __init__(self, details=None):
        super().__init__("INVALID_JSON", "Malformed JSON body", 400, details=details)


class SchemaValidationError(ObservatoryError):
    def __init__(self, details=None):
        super().__init__("SCHEMA_VALIDATION_FAILED", "Request body violates JSON schema", 400, details=details)


class InsufficientRoleError(ObservatoryError):
    def __init__(self, role: str = ""):
        super().__init__("INSUFFICIENT_ROLE", f"Role '{role}' lacks required access", 403)


class DecisionAccessDeniedError(ObservatoryError):
    def __init__(self):
        super().__init__("DECISION_ACCESS_DENIED", "Viewer role cannot access decision output", 403)


class ScenarioNotFoundError(ObservatoryError):
    def __init__(self, scenario_id: str = ""):
        super().__init__("SCENARIO_NOT_FOUND", f"Scenario '{scenario_id}' not found", 404)


class RunNotFoundError(ObservatoryError):
    def __init__(self, run_id: str = ""):
        super().__init__("RUN_NOT_FOUND", f"Run '{run_id}' not found", 404)


class RunNotReadyError(ObservatoryError):
    def __init__(self, run_id: str = "", status: str = ""):
        super().__init__(
            "RUN_NOT_READY",
            f"Run '{run_id}' is still {status}",
            409, recoverable=True, retryable=True,
            details=[{"field": "run_id", "issue": f"status={status}", "value": run_id}],
        )


class ScenarioDuplicateNameError(ObservatoryError):
    def __init__(self, name: str = ""):
        super().__init__("SCENARIO_DUPLICATE_NAME", f"Active scenario with name '{name}' already exists", 409)


class IdempotencyConflictError(ObservatoryError):
    def __init__(self):
        super().__init__("IDEMPOTENCY_CONFLICT", "Same Idempotency-Key with different payload", 409)


class NumericStabilityError(ObservatoryError):
    def __init__(self, stage: str = ""):
        super().__init__(
            "NUMERIC_STABILITY_ERROR",
            f"Non-finite result detected in stage '{stage}'",
            500, recoverable=True, retryable=True,
        )
