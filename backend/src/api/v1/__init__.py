"""Impact Observatory — مرصد الأثر — API v1.

Versioned API endpoints:
    POST /api/v1/scenarios        — list templates
    POST /api/v1/runs             — execute scenario run
    GET  /api/v1/runs/{run_id}    — full run result
    GET  /api/v1/runs/{run_id}/financial   — financial impacts
    GET  /api/v1/runs/{run_id}/banking     — banking stress
    GET  /api/v1/runs/{run_id}/insurance   — insurance stress
    GET  /api/v1/runs/{run_id}/fintech     — fintech stress
    GET  /api/v1/runs/{run_id}/decision    — decision actions
    GET  /api/v1/runs/{run_id}/explanation — causal explanation
"""
