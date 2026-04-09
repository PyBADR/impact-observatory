"""Macro Intelligence Layer — Signal Validators.

All validation rules live here. No validation logic in routes or services.
Validators operate on MacroSignalInput and return structured errors.

Design:
  - Field-level validators catch type/range issues
  - Cross-field validators enforce business invariants
  - All validators return (is_valid, errors) tuples
  - Fail closed: any validation error = signal rejected
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.macro.macro_enums import (
    GCCRegion,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
)
from src.macro.macro_schemas import MacroSignalInput


# ── Severity Score → Level Mapping ───────────────────────────────────────────

def severity_from_score(score: float) -> SignalSeverity:
    """Map a [0.0, 1.0] severity score to the discrete severity level.

    Thresholds aligned with URS risk levels from config:
      NOMINAL  : < 0.20
      LOW      : 0.20 – 0.35
      GUARDED  : 0.35 – 0.50
      ELEVATED : 0.50 – 0.65
      HIGH     : 0.65 – 0.80
      SEVERE   : >= 0.80
    """
    if score < 0.20:
        return SignalSeverity.NOMINAL
    elif score < 0.35:
        return SignalSeverity.LOW
    elif score < 0.50:
        return SignalSeverity.GUARDED
    elif score < 0.65:
        return SignalSeverity.ELEVATED
    elif score < 0.80:
        return SignalSeverity.HIGH
    else:
        return SignalSeverity.SEVERE


# ── Field-Level Validators ───────────────────────────────────────────────────

def validate_title(title: str) -> list[str]:
    """Title must be non-empty, 5–300 chars, not all whitespace."""
    errors: list[str] = []
    stripped = title.strip()
    if not stripped:
        errors.append("title: must not be empty or whitespace-only")
    if len(stripped) < 5:
        errors.append(f"title: too short ({len(stripped)} chars, minimum 5)")
    if len(stripped) > 300:
        errors.append(f"title: too long ({len(stripped)} chars, maximum 300)")
    return errors


def validate_severity_score(score: float) -> list[str]:
    """Severity must be in [0.0, 1.0]."""
    errors: list[str] = []
    if score < 0.0 or score > 1.0:
        errors.append(f"severity_score: out of range ({score}), must be [0.0, 1.0]")
    return errors


def validate_regions(regions: list[GCCRegion]) -> list[str]:
    """At least one region required. No duplicates."""
    errors: list[str] = []
    if not regions:
        errors.append("regions: at least one GCC region is required")
    if len(regions) != len(set(regions)):
        errors.append("regions: duplicate regions detected")
    return errors


def validate_event_time(event_time: datetime | None) -> list[str]:
    """If provided, event_time must not be in the future (>5min tolerance)."""
    errors: list[str] = []
    if event_time is not None:
        now = datetime.now(timezone.utc)
        # Ensure event_time is timezone-aware
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        if event_time > now + timedelta(minutes=5):
            errors.append(
                f"event_time: cannot be in the future "
                f"(received {event_time.isoformat()}, now {now.isoformat()})"
            )
    return errors


def validate_ttl(ttl_hours: int | None) -> list[str]:
    """TTL must be 1–8760 hours (1h to 365 days)."""
    errors: list[str] = []
    if ttl_hours is not None:
        if ttl_hours < 1 or ttl_hours > 8760:
            errors.append(f"ttl_hours: out of range ({ttl_hours}), must be [1, 8760]")
    return errors


# ── Cross-Field Validators ───────────────────────────────────────────────────

def validate_severity_confidence_coherence(
    severity_score: float,
    confidence: SignalConfidence,
) -> list[str]:
    """SEVERE signals with UNVERIFIED confidence are suspicious — warn but accept."""
    warnings: list[str] = []
    if severity_score >= 0.80 and confidence == SignalConfidence.UNVERIFIED:
        warnings.append(
            "cross_field_warning: SEVERE signal with UNVERIFIED confidence — "
            "recommend verification before downstream propagation"
        )
    return warnings


def validate_scope_list(field: str, values: list[str]) -> list[str]:
    """Validate a scope array (country_scope, sector_scope).

    Must be a list of non-empty strings. The schema validators already strip
    and deduplicate; this provides an explicit guard for direct construction.
    """
    errors: list[str] = []
    for i, v in enumerate(values):
        if not isinstance(v, str) or not v.strip():
            errors.append(
                f"{field}[{i}]: empty or non-string value — "
                "all scope entries must be non-empty strings"
            )
    return errors


def validate_direction_severity_coherence(
    direction: SignalDirection,
    severity_score: float,
) -> list[str]:
    """NEUTRAL or UNCERTAIN direction with HIGH/SEVERE severity is contradictory.

    Both NEUTRAL and UNCERTAIN imply the signal lacks a directional impact.
    A severity score >= 0.65 (HIGH or SEVERE) implies a material impact exists.
    The combination is logically contradictory and is rejected.
    """
    errors: list[str] = []
    undirected = {SignalDirection.NEUTRAL, SignalDirection.UNCERTAIN}
    if direction in undirected and severity_score >= 0.65:
        errors.append(
            f"cross_field: {direction.value.upper()} direction with severity >= 0.65 is contradictory — "
            "a high-severity signal must have a directional impact"
        )
    return errors


# ── Master Validator ─────────────────────────────────────────────────────────

def validate_signal_input(input_data: MacroSignalInput) -> tuple[bool, list[str], list[str]]:
    """Run all validators against a MacroSignalInput.

    Returns:
        (is_valid, errors, warnings)
        - is_valid: True if no hard errors
        - errors: list of blocking error strings
        - warnings: list of non-blocking warning strings
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Field-level
    errors.extend(validate_title(input_data.title))
    errors.extend(validate_severity_score(input_data.severity_score))
    errors.extend(validate_regions(input_data.regions))
    errors.extend(validate_event_time(input_data.event_time))
    errors.extend(validate_ttl(input_data.ttl_hours))
    errors.extend(validate_scope_list("country_scope", input_data.country_scope))
    errors.extend(validate_scope_list("sector_scope", input_data.sector_scope))

    # Cross-field
    errors.extend(validate_direction_severity_coherence(
        input_data.direction, input_data.severity_score
    ))
    warnings.extend(validate_severity_confidence_coherence(
        input_data.severity_score, input_data.confidence
    ))

    is_valid = len(errors) == 0
    return is_valid, errors, warnings
