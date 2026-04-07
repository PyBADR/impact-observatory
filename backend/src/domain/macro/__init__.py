"""domain.macro — Thin re-export layer for the Macro Intelligence domain.

All canonical implementations live in src/macro/.
This package provides the structured domain path
(src.domain.macro.*) as an alias so consumer code can use
either import style:

    from src.macro.macro_enums import SignalType
    from src.domain.macro import SignalType          # equivalent
"""

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalStatus,
    SignalType,
)
from src.macro.macro_normalizer import (
    SOURCE_DOMAIN_MAP,
    normalize_signal,
)
from src.macro.macro_schemas import (
    MacroSignal,
    MacroSignalInput,
    NormalizedSignal,
    SignalIntakeResponse,
    SignalListResponse,
    SignalQueryResponse,
    SignalRejection,
    SignalRejectionResponse,
    SignalRegistryEntry,
)
from src.macro.macro_signal_service import (
    MacroSignalService,
    SignalRegistry,
    get_signal_service,
)
from src.macro.macro_validators import (
    severity_from_score,
    validate_direction_severity_coherence,
    validate_event_time,
    validate_regions,
    validate_scope_list,
    validate_severity_score,
    validate_signal_input,
    validate_title,
)

__all__ = [
    # Enums
    "GCCRegion",
    "ImpactDomain",
    "SignalConfidence",
    "SignalDirection",
    "SignalSeverity",
    "SignalSource",
    "SignalStatus",
    "SignalType",
    # Schemas
    "MacroSignal",
    "MacroSignalInput",
    "NormalizedSignal",
    "SignalIntakeResponse",
    "SignalListResponse",
    "SignalQueryResponse",
    "SignalRejection",
    "SignalRejectionResponse",
    "SignalRegistryEntry",
    # Service
    "MacroSignalService",
    "SignalRegistry",
    "get_signal_service",
    # Normalizer
    "SOURCE_DOMAIN_MAP",
    "normalize_signal",
    # Validators
    "severity_from_score",
    "validate_direction_severity_coherence",
    "validate_event_time",
    "validate_regions",
    "validate_scope_list",
    "validate_severity_score",
    "validate_signal_input",
    "validate_title",
]
