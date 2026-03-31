# Deevo Sim (DVO7)

**Decision Intelligence Platform for GCC Scenarios**

Deevo Sim runs geopolitical, economic, and infrastructure scenarios through a 76-node, 190-edge GCC entity graph. It produces propagation analysis, sector impact assessment, and decision intelligence — including recommended actions, urgency levels, and mitigation effectiveness.

**Live**: https://deevo-sim.vercel.app/demo

---

## Architecture

```
frontend/                 Next.js 14 · TypeScript · Tailwind CSS
├── app/demo/page.tsx     Command Center UI (graph + globe + panels)
├── app/api/              Backend API routes (serverless)
│   ├── health/           GET  /api/health
│   ├── version/          GET  /api/version
│   ├── scenarios/        GET  /api/scenarios
│   ├── run-scenario/     POST /api/run-scenario
│   ├── run-decision/     POST /api/run-decision
│   ├── runs/             GET  /api/runs, /api/runs/{id}
│   └── audit/            GET  /api/audit/{id}
├── lib/
│   ├── gcc-graph.ts          76 nodes, 190 edges, 17 scenarios
│   ├── propagation-engine.ts Discrete dynamic propagation
│   ├── scenario-engines.ts   17 dedicated formula engines
│   ├── decision-engine.ts    DPS, APS, ME, DC, urgency, actions
│   └── server/
│       ├── auth.ts           API key authentication
│       ├── rbac.ts           Role-based access control
│       ├── audit.ts          SHA-256 chained audit log
│       ├── store.ts          Run persistence (DB-ready interface)
│       ├── execution.ts      Server-side pipeline execution
│       └── trace.ts          trace_id / run_id generation
└── middleware.ts             CORS + security headers
```

---

## Quick Start

```bash
cd frontend
cp .env.example .env.local    # Edit with your keys
npm install
npm run dev                    # → http://localhost:3000
```

### Environment Variables

See `.env.example` for full list. Key variables:

| Variable | Purpose | Required |
|---|---|---|
| `DVO7_TIER` | Environment: `dev`, `pilot`, `prod` | No (default: `pilot`) |
| `DVO7_API_KEY` | Admin API key | Yes for prod |
| `NEXT_PUBLIC_USE_API` | Frontend calls backend API | No (default: `false`) |

---

## API Usage

### Run a scenario (authenticated)

```bash
curl -X POST https://deevo-sim.vercel.app/api/run-scenario \
  -H "Content-Type: application/json" \
  -H "X-DVO7-API-Key: YOUR_KEY" \
  -d '{"scenarioId": "hormuz_closure", "severity": 0.7}'
```

Returns: `runId`, `traceId`, `auditId`, node impacts, sector impacts, engine results, decision outputs (actions, urgency, DPS, mitigation effectiveness).

### Public endpoints (no auth required)

```bash
curl https://deevo-sim.vercel.app/api/health
curl https://deevo-sim.vercel.app/api/version
curl https://deevo-sim.vercel.app/api/scenarios
```

---

## Deploy to Vercel

1. Import repository → set **Root Directory** to `frontend`
2. Set environment variables in Vercel dashboard:
   - `DVO7_API_KEY` — your admin API key
   - `DVO7_TIER` — `pilot` or `prod`
   - `NEXT_PUBLIC_USE_API` — `true` to enable API-backed frontend
3. Deploy

---

## Status

- **Phase**: Pilot
- **Persistence**: In-memory (ephemeral across cold starts). Production: swap `InMemoryRunStore` → `PostgresRunStore`.
- **Auth**: API key. Production: JWT + OAuth2.
- **Frontend**: Dual-mode — client-side (default) or API-backed (`NEXT_PUBLIC_USE_API=true`).

---

## License

Proprietary — Deevo Analytics. All rights reserved.
