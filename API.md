# Impact Observatory | مرصد الأثر — API Contract v1.0

## Base URL
```
https://deevo-sim.vercel.app/api
```

## Authentication
API key via header:
```
X-DC7-API-Key: <key>
```
or
```
Authorization: Bearer <key>
```

**Pilot keys** (defaults when no env vars set):
- `dc7_pilot_key_2026` — admin (run + read + audit)
- `dc7_demo_readonly` — viewer (read-only)

**Production**: Set `DC7_API_KEY`, `DC7_ANALYST_KEY`, `DC7_PILOT_KEY` in Vercel dashboard.

## Roles (RBAC)
| Role | run_scenarios | run_decisions | read_runs | read_audit | manage_users |
|------|:---:|:---:|:---:|:---:|:---:|
| admin | Y | Y | Y | Y | Y |
| analyst | Y | Y | Y | Y | N |
| viewer | N | N | Y | N | N |
| api_service | Y | Y | Y | N | N |

---

## Endpoints

### GET /health
Public. Returns system health.
```json
{
  "status": "healthy",
  "environment": "pilot",
  "store": { "runsCount": 5, "auditEntriesCount": 8, "auditChainValid": true }
}
```

### GET /version
Public. Returns model/engine versions and capabilities.
```json
{
  "versions": { "model": "7.0.0", "engine": "2.0.0", "graph": "1.5.0", "api": "1.0.0" },
  "capabilities": { "auth": "api-key", "rbac": true, "auditTrail": true }
}
```

### GET /scenarios
Public. Lists all 17 scenarios with metadata.
```json
{
  "scenarios": [
    { "id": "hormuz_closure", "title": "Strait of Hormuz Closure", "titleAr": "...", "group": "geopolitics", "engineId": "hormuz_closure", "shockCount": 1 }
  ]
}
```

### POST /run-scenario
**Auth required.** Permission: `run_scenarios`.

Request:
```json
{ "scenarioId": "hormuz_closure", "severity": 0.7 }
```

Response:
```json
{
  "runId": "dc7_run_...",
  "traceId": "dc7_trace_...",
  "auditId": "dc7_audit_...",
  "scenarioId": "hormuz_closure",
  "metrics": { "systemEnergy": 1.49, "confidence": 0.98, "propagationDepth": 6, "totalLoss": 187.8 },
  "nodeImpacts": { "geo_hormuz": 0.623, "eco_oil": -0.402, "..." : "..." },
  "sectorImpacts": [...],
  "explanationChain": [...],
  "engineResult": { "engineId": "hormuz_closure", "steps": [...], "totalExposure": 234.7 },
  "decision": { "decisionPressureScore": 0.60, "urgencyLevel": "immediate", "recommendedActions": [...] },
  "durationMs": 3
}
```

### POST /run-decision
**Auth required.** Permission: `run_decisions`.
Same request/response as `/run-scenario` but focused on decision output.

### GET /runs/{id}
**Auth required.** Permission: `read_runs`.
Returns a persisted run by `runId`.

### GET /audit/{id}
**Auth required.** Permission: `read_audit`.
Returns an audit event by `auditId` including SHA-256 hash chain.

---

## Persistence
- **Pilot mode**: In-memory (resets on Vercel cold starts)
- **Production**: Connect `DATABASE_URL` for durable storage

## Environment Variables
See `.env.example` for full list.

## Frontend Wiring
Set `NEXT_PUBLIC_USE_API=true` to make the frontend call the backend API.
When `false` or API unavailable, falls back to client-side execution.
The top bar shows `API` or `CLIENT` mode badge.
