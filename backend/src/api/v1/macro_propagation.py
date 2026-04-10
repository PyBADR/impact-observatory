"""Macro Propagation API — Pack 2 entry point.

Re-exports the router defined in src/api/v1/propagation.py.

The canonical route implementation lives in propagation.py
(registered in main.py as v1_propagation_router). This module
provides the Pack 2 conventional path (macro_propagation.py)
as a stable import alias.

Routes provided:
  POST   /api/v1/macro/propagate              — propagate by registry_id
  POST   /api/v1/macro/propagate/inline       — submit + propagate in one call
  POST   /api/v1/macro/propagate/{signal_id}  — propagate by signal_id
  GET    /api/v1/macro/propagation            — list propagation results
  GET    /api/v1/macro/propagation/stats      — propagation statistics
  GET    /api/v1/macro/propagation/by-signal/{signal_id}
  GET    /api/v1/macro/propagation/{result_id}
  POST   /api/v1/macro/causal/{registry_id}   — causal mapping only
"""

from src.api.v1.propagation import router  # noqa: F401 — re-export

__all__ = ["router"]
