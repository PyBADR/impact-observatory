"""Macro Intelligence Layer — Causal Entry Sublayer.

Maps normalized signals to causal entry points and defines
the GCC-domain causal channel graph.

Layer ownership:
  causal_schemas.py  — CausalEntryPoint, CausalChannel domain models
  causal_graph.py    — static GCC causal channel graph definition
  causal_mapper.py   — signal → causal entry point mapping service
"""
