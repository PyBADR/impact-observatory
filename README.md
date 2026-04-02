# Impact Observatory | مرصد الأثر

Production-grade GCC executive decision intelligence platform.

Simulate systemic stress across banking, insurance, fintech, and critical infrastructure — then act before failure.

حاكي الضغط النظامي عبر البنوك والتأمين والفنتك والبنية الحيوية — واتخذ القرار قبل الانهيار.

## Pipeline

```
Scenario → Physics → Graph → Propagation → Financial → Banking → Insurance → Fintech →
Decision → Explainability → Reporting → Audit → Business Impact → Timeline → Regulatory
```

15-stage deterministic pipeline. All 8 GCC scenarios. <2ms execution.

## V1 Flagship

**Hormuz Closure — 14D — Severe**

Produces:
- FinancialImpact — entity-level loss, stress classification, GDP impact
- BankingStress — LCR, CAR, liquidity/credit/FX stress, institution breakdown
- InsuranceStress — solvency, combined ratio, IFRS-17, claims surge, reinsurance triggers
- FintechStress — payment volume, settlement delay, API availability, cross-border disruption
- DecisionPlan — top 3 ranked actions (5-component weighted priority formula)
- RegulatoryState — GCC jurisdiction compliance (SAMA/CBUAE/QCB/CBK/CBB/CBO)
- ExplanationPack — bilingual causal chain, confidence scoring, methodology trace
- BusinessImpactSummary — peak loss, first failure, severity, executive status
- TimelineOutputs — timestep simulation with shock decay, loss trajectory, breach events

## Decision Priority Formula

```
Priority = 0.25×Urgency + 0.30×Value + 0.20×RegRisk + 0.15×Feasibility + 0.10×TimeEffect
```

Returns TOP 3 actions only. Deterministic ranking with tie-breaking.

## Dashboard Structure

| Panel | Content |
|-------|---------|
| Top Summary | Headline Loss, Peak Day, Time to First Failure, Business Severity, Executive Status |
| Financial Impact | Entity-level losses, stress classification, GDP impact |
| Banking Stress | Aggregate + institution breakdown, LCR/CAR gauges |
| Insurance Stress | Claims surge, combined ratio, solvency, IFRS-17 |
| Fintech Stress | Payment volume, settlement delay, API availability |
| Decision Actions | Top 3 ranked actions with priority decomposition |
| Business Impact Timeline | Loss trajectory, time-to-failure, severity mapping |
| Regulatory Timeline | Breach events, LCR/NSFR/CAR/Solvency gauges, mandatory actions |
| Timeline Simulation | Timestep playback with shock/loss/flow/breach |

Modes: Executive | Analyst | Regulator

## RBAC

| Role | Permissions |
|------|-------------|
| viewer | Read scenarios, runs, financial, sector stress, explanations |
| analyst | + Create scenarios/runs, timeline, regulatory, decision read |
| operator | + Approve/reject actions, audit stats |
| admin | + All permissions, config, audit read |
| regulator | + Regulatory reports, audit read, compliance export |

## API Surface

```
POST /api/v1/scenarios
POST /api/v1/runs
GET  /api/v1/runs/{run_id}
GET  /api/v1/runs/{run_id}/financial
GET  /api/v1/runs/{run_id}/banking
GET  /api/v1/runs/{run_id}/insurance
GET  /api/v1/runs/{run_id}/fintech
GET  /api/v1/runs/{run_id}/decision
GET  /api/v1/runs/{run_id}/explanation
GET  /api/v1/runs/{run_id}/business-impact
GET  /api/v1/runs/{run_id}/timeline
GET  /api/v1/runs/{run_id}/regulatory-timeline
GET  /api/v1/runs/{run_id}/executive-explanation
GET  /api/v1/runs/{run_id}/report/{mode}
POST /api/v1/runs/{run_id}/actions/{action_id}/approve
POST /api/v1/runs/{run_id}/actions/{action_id}/reject
```

## Scenarios (8)

| ID | Label | Base Loss |
|----|-------|-----------|
| hormuz_disruption | Hormuz Closure | $3.2B |
| yemen_escalation | Yemen Escalation | $1.8B |
| iran_sanctions | Iran Sanctions | $2.4B |
| cyber_attack | Cyber Attack | $0.9B |
| gulf_airspace | Gulf Airspace Closure | $1.1B |
| port_disruption | Port Disruption | $1.5B |
| oil_price_shock | Oil Price Shock | $4.5B |
| banking_stress | Banking Stress | $2.1B |

## Stack

- **Backend**: FastAPI (Python 3.12) — 15 services, Pydantic v2 schemas
- **Frontend**: Next.js 15 (React 18) — Tailwind CSS, DM Sans + IBM Plex Sans Arabic
- **Schemas**: 27 canonical v4 models in `backend/src/schemas/v4.py`
- **Deployment**: Vercel (frontend) + Railway (backend)
- **Design**: White/light boardroom aesthetic, bilingual AR/EN, RTL/LTR

## Live

- Frontend: https://deevo-sim.vercel.app
- Backend: https://deevo-cortex-production.up.railway.app
- Repository: https://github.com/PyBADR/impact-observatory
