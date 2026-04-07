"""domain.propagation — Re-export layer for the Propagation domain.

All canonical implementations live in src/macro/propagation/.
This package provides the structured domain path
(src.domain.propagation.*) as an alias so consumer code can use
either import style:

    from src.macro.propagation.propagation_schemas import PropagationResult
    from src.domain.propagation import PropagationResult          # equivalent
"""

from src.macro.propagation.propagation_schemas import (
    NodeState,
    PropagationEdge,
    PropagationHit,
    PropagationNode,
    PropagationPath,
    PropagationResponse,
    PropagationResult,
    PropagationSummary,
)
from src.macro.propagation.propagation_engine import (
    MAX_PROPAGATION_DEPTH,
    MIN_SEVERITY_THRESHOLD,
    propagate,
)
from src.macro.propagation.propagation_service import (
    PropagationResultStore,
    PropagationService,
    get_propagation_service,
)

__all__ = [
    # Schemas
    "NodeState",
    "PropagationEdge",
    "PropagationHit",
    "PropagationNode",
    "PropagationPath",
    "PropagationResponse",
    "PropagationResult",
    "PropagationSummary",
    # Engine
    "MAX_PROPAGATION_DEPTH",
    "MIN_SEVERITY_THRESHOLD",
    "propagate",
    # Service
    "PropagationResultStore",
    "PropagationService",
    "get_propagation_service",
]
