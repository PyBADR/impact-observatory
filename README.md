# Impact Observatory | مرصد الأثر

GCC macro financial intelligence — from signals to decisions to accountability.

A sovereign-grade briefing system for executive decision-makers. Impact Observatory traces how macro shocks move through GCC economies, surfaces the institutional response required, and evaluates whether those decisions worked.

من الإشارات الكلية إلى القرارات الاقتصادية — مرصد الأثر يتتبع انتقال الصدمات عبر اقتصادات الخليج، ويحدد الاستجابة المؤسسية المطلوبة، ويقيّم فعالية القرارات.

## Architecture

The system follows a vertical institutional narrative — not a dashboard.

Every scenario reads as a structured briefing through five layers:

```
Context → Transmission → Impact → Decision → Outcome
```

The frontend renders each layer as calm, readable prose. No KPI grids, no dashboard cards, no analytics console patterns. The interface reads like a macro intelligence memo for a GCC board room.

## Pages

**Scenario Register** — institutional index of 15 active GCC macro scenarios, sorted by severity. Each entry shows classification, domain, horizon, and a significance summary.

**Scenario Briefing** — vertical five-section analysis for each scenario: what happened, how pressure transmits through the system, which institutions are exposed, what decisions are required, and what the expected outcome is if those decisions execute.

**Decision Directive** — sovereign-grade decision document. One dominant primary directive with rationale and consequence of inaction. Supporting actions beneath. Owner and deadline embedded in prose, not metadata rows.

**Evaluation Review** — post-decision accountability layer. Expected versus actual outcomes in institutional language. Correctness assessment, analyst commentary, institutional learning, and rule performance audit.

## Scenarios (15)

| ID | Severity | Domain |
|----|----------|--------|
| hormuz_chokepoint_disruption | Severe | Maritime & Energy |
| hormuz_full_closure | Severe | Maritime & Energy |
| iran_regional_escalation | Severe | Geopolitical |
| critical_port_throughput_disruption | Severe | Logistics |
| saudi_oil_shock | High | Energy |
| uae_banking_crisis | High | Financial |
| qatar_lng_disruption | High | Energy |
| regional_liquidity_stress_event | High | Financial |
| financial_infrastructure_cyber_disruption | High | Cyber & Financial |
| red_sea_trade_corridor_instability | Elevated | Maritime & Trade |
| gcc_cyber_attack | Elevated | Cyber |
| energy_market_volatility_shock | Elevated | Energy & Fiscal |
| oman_port_closure | Elevated | Logistics |
| bahrain_sovereign_stress | Guarded | Sovereign & Fiscal |
| kuwait_fiscal_shock | Guarded | Sovereign & Fiscal |

## Pipeline

```
Scenario → Physics → Graph → Propagation → Financial → Banking → Insurance → Fintech →
Decision → Explainability → Reporting → Audit → Business Impact → Timeline → Regulatory
```

17-stage deterministic simulation engine. 43 nodes. <2ms execution per scenario.

## Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS 3.4
- **Backend**: FastAPI, Python 3.12, Pydantic v2
- **Design**: DM Sans + IBM Plex Sans Arabic, institutional palette (#F5F5F2 background, charcoal/graphite text, amber/red/olive status accents)
- **Deployment**: Vercel (frontend) + Railway (backend)

## Development

```bash
# Backend
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm install
npm run dev
```

Frontend at localhost:3000. Backend at localhost:8000. API docs at localhost:8000/docs.

## Tests

```bash
cd backend
.venv/bin/python -m pytest tests/ -v --tb=short    # 140 tests
```

```bash
cd frontend
npx tsc --noEmit                                    # Type check
```

## Live

- Frontend: https://deevo-sim.vercel.app
- Backend: https://deevo-cortex-production.up.railway.app
- Repository: https://github.com/PyBADR/impact-observatory
