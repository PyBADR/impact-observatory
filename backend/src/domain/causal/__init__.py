"""domain.causal — Re-export layer for the Causal Entry domain.

All canonical implementations live in src/macro/causal/.
This package provides the structured domain path
(src.domain.causal.*) as an alias so consumer code can use
either import style:

    from src.macro.causal.causal_schemas import CausalEntryPoint
    from src.domain.causal import CausalEntryPoint          # equivalent
"""

from src.macro.causal.causal_schemas import (
    CausalChannel,
    CausalEntryPoint,
    CausalMapping,
    RelationshipType,
)
from src.macro.causal.causal_graph import (
    ADJACENCY,
    GCC_CAUSAL_CHANNELS,
    get_all_domains,
    get_outgoing_channels,
)
from src.macro.causal.causal_mapper import (
    CONFIDENCE_WEIGHTS,
    compute_entry_strength,
    discover_activated_channels,
    map_signal_to_causal,
    map_signal_to_causal_entry,
)

__all__ = [
    # Schemas
    "CausalChannel",
    "CausalEntryPoint",
    "CausalMapping",
    "RelationshipType",
    # Graph
    "ADJACENCY",
    "GCC_CAUSAL_CHANNELS",
    "get_all_domains",
    "get_outgoing_channels",
    # Mapper
    "CONFIDENCE_WEIGHTS",
    "compute_entry_strength",
    "discover_activated_channels",
    "map_signal_to_causal",
    "map_signal_to_causal_entry",
]
