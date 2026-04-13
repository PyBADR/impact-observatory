# Observatory V2 — Vercel Deployment Guide

## Pre-Deployment Fixes Applied

### 1. Static Generation Enabled

All three `[slug]` pages now export `generateStaticParams()`, meaning Vercel pre-renders all 45 pages (15 scenarios + 15 decisions + 15 evaluations) as static HTML at build time. Zero serverless function invocations for page views.

| Route | Static Params Source | Pages Generated |
|---|---|---|
| `/scenario/[slug]` | `getAllScenarios()` → 15 IDs | 15 |
| `/decision/[slug]` | `getAllDecisions()` → 15 IDs | 15 |
| `/evaluation/[slug]` | `getAllEvaluations()` → 15 IDs | 15 |
| `/` | No params (static page) | 1 |
| `/evaluation` | No params (static page) | 1 |

Total: 47 static pages. No dynamic rendering. No edge functions required.

### 2. Duplicate Rewrite Configuration

**Issue:** Root `vercel.json` duplicates the rewrites already defined in `next.config.mjs`. Worse, `vercel.json` uses `${NEXT_PUBLIC_API_URL}` placeholder syntax which Vercel does not process — it becomes a literal string destination.

**Fix required before deploy:** Delete the root `vercel.json` file, or replace its contents with:

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next"
}
```

The `next.config.mjs` async rewrites function correctly reads `process.env.NEXT_PUBLIC_API_URL` at build time — that is the canonical rewrite source.

---

## Deployment Checklist

### Environment Variables (set in Vercel Dashboard → Settings → Environment Variables)

| Variable | Required | Value | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | `https://deevo-cortex-production.up.railway.app` | Backend URL. Must NOT have trailing slash. |
| `NEXT_PUBLIC_PRODUCT_NAME` | No | `Impact Observatory` | Used in metadata only |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | No | Your Mapbox token | Only if map features are active |
| `NEXT_PUBLIC_CESIUM_TOKEN` | No | Your Cesium ion token | Only if globe visualization is active |
| `NEXT_PUBLIC_USE_API` | No | `true` | Enables backend API calls. Defaults to false. |

**Do not set:** `IO_API_KEY`, `IO_ANALYST_KEY`, `IO_PILOT_KEY` — these are backend-only variables. Never expose in frontend env.

### Vercel Project Settings

| Setting | Value |
|---|---|
| Framework Preset | Next.js |
| Root Directory | `frontend` |
| Build Command | `npm run build` (default) |
| Output Directory | `.next` (default) |
| Install Command | `npm install` (default) |
| Node.js Version | 18.x or 20.x |

### Pre-Push Verification (run locally)

```bash
cd frontend

# 1. Type check — must show ONLY the 3 pre-existing vitest errors
npx tsc --noEmit

# 2. Production build — must complete without errors
npm run build

# 3. Verify static generation output
# Look for these lines in the build output:
#   ● /scenario/[slug]           (15 entries)
#   ● /decision/[slug]           (15 entries)
#   ● /evaluation/[slug]         (15 entries)
#   ○ /                          (static)
#   ○ /evaluation                (static)
# ● = SSG (static site generation), ○ = static

# 4. Local smoke test
npm start
# Visit localhost:3000 — should serve pre-rendered HTML instantly
```

---

## Route Verification Checklist

After deploy, verify every route returns 200 and renders correctly.

### Static Pages (no params)

| Route | Expected Title | Check |
|---|---|---|
| `/` | "Macro Signal Intelligence" heading, 15 scenario rows | [ ] |
| `/evaluation` | "Decision Evaluation" heading, 15 evaluation rows | [ ] |

### Scenario Pages (15 routes)

| Route | Check |
|---|---|
| `/scenario/hormuz_chokepoint_disruption` | [ ] |
| `/scenario/hormuz_full_closure` | [ ] |
| `/scenario/iran_regional_escalation` | [ ] |
| `/scenario/critical_port_throughput_disruption` | [ ] |
| `/scenario/saudi_oil_shock` | [ ] |
| `/scenario/uae_banking_crisis` | [ ] |
| `/scenario/qatar_lng_disruption` | [ ] |
| `/scenario/regional_liquidity_stress_event` | [ ] |
| `/scenario/financial_infrastructure_cyber_disruption` | [ ] |
| `/scenario/red_sea_trade_corridor_instability` | [ ] |
| `/scenario/gcc_cyber_attack` | [ ] |
| `/scenario/energy_market_volatility_shock` | [ ] |
| `/scenario/oman_port_closure` | [ ] |
| `/scenario/bahrain_sovereign_stress` | [ ] |
| `/scenario/kuwait_fiscal_shock` | [ ] |

### Decision Pages (15 routes)

| Route | Check |
|---|---|
| `/decision/hormuz_chokepoint_disruption` | [ ] |
| `/decision/hormuz_full_closure` | [ ] |
| `/decision/iran_regional_escalation` | [ ] |
| `/decision/critical_port_throughput_disruption` | [ ] |
| `/decision/saudi_oil_shock` | [ ] |
| `/decision/uae_banking_crisis` | [ ] |
| `/decision/qatar_lng_disruption` | [ ] |
| `/decision/regional_liquidity_stress_event` | [ ] |
| `/decision/financial_infrastructure_cyber_disruption` | [ ] |
| `/decision/red_sea_trade_corridor_instability` | [ ] |
| `/decision/gcc_cyber_attack` | [ ] |
| `/decision/energy_market_volatility_shock` | [ ] |
| `/decision/oman_port_closure` | [ ] |
| `/decision/bahrain_sovereign_stress` | [ ] |
| `/decision/kuwait_fiscal_shock` | [ ] |

### Evaluation Pages (15 routes)

| Route | Check |
|---|---|
| `/evaluation/hormuz_chokepoint_disruption` | [ ] |
| `/evaluation/hormuz_full_closure` | [ ] |
| `/evaluation/iran_regional_escalation` | [ ] |
| `/evaluation/critical_port_throughput_disruption` | [ ] |
| `/evaluation/saudi_oil_shock` | [ ] |
| `/evaluation/uae_banking_crisis` | [ ] |
| `/evaluation/qatar_lng_disruption` | [ ] |
| `/evaluation/regional_liquidity_stress_event` | [ ] |
| `/evaluation/financial_infrastructure_cyber_disruption` | [ ] |
| `/evaluation/red_sea_trade_corridor_instability` | [ ] |
| `/evaluation/gcc_cyber_attack` | [ ] |
| `/evaluation/energy_market_volatility_shock` | [ ] |
| `/evaluation/oman_port_closure` | [ ] |
| `/evaluation/bahrain_sovereign_stress` | [ ] |
| `/evaluation/kuwait_fiscal_shock` | [ ] |

### 404 Behavior

| Route | Expected |
|---|---|
| `/scenario/nonexistent` | Next.js 404 page | [ ] |
| `/decision/nonexistent` | Next.js 404 page | [ ] |
| `/evaluation/nonexistent` | Next.js 404 page | [ ] |

---

## Preview QA Checklist

Run against the Vercel preview URL (generated on every PR push).

### Visual Checks

- [ ] Background color is #F5F5F2 (warm off-white), not pure white
- [ ] DM Sans font loads (check heading letterforms — DM Sans has distinctive 'a' and 'g')
- [ ] IBM Plex Sans Arabic loads for Arabic text ("مرصد الأثر" in TopNav)
- [ ] TopNav shows three links: "Overview · Decisions · Evaluation"
- [ ] TopNav frosted glass effect visible on scroll (backdrop-blur)
- [ ] Severity colors render correctly: red for Severe/High, amber for Elevated, grey for Guarded
- [ ] Verdict colors render correctly: olive for Confirmed, amber for Partially Confirmed, grey for Inconclusive

### Layout Checks

- [ ] No horizontal scroll at any viewport width
- [ ] Content max-width constrains at `max-w-6xl` (Container)
- [ ] Prose blocks constrain at `max-w-3xl`
- [ ] Section borders render as thin `border-[var(--io-border-muted)]` lines
- [ ] Padding scales correctly: mobile → tablet → desktop

### Navigation Checks

- [ ] Landing → click scenario → Scenario page loads
- [ ] Scenario page → "View decision brief →" → Decision page loads
- [ ] Decision page → "View scenario analysis →" → Scenario page loads
- [ ] Decision page → "View evaluation →" → Evaluation page loads
- [ ] Evaluation page → "View scenario →" → Scenario page loads
- [ ] Evaluation page → "View decision brief →" → Decision page loads
- [ ] Evaluation register → click row → Individual evaluation loads
- [ ] "← All scenarios" back link → Landing page
- [ ] "← All evaluations" back link → Evaluation register
- [ ] TopNav "Overview" → Landing
- [ ] TopNav "Decisions" → currently highlights when on /decision/* routes
- [ ] TopNav "Evaluation" → Evaluation register

### Mobile Checks (390px viewport)

- [ ] Landing: metadata stacks above title, no horizontal overflow
- [ ] Scenario: sections stack cleanly, prose readable at mobile width
- [ ] Decision: primary directive renders at readable size, no overflow
- [ ] Evaluation: verdict + correctness stack on mobile
- [ ] TopNav: brand and links fit without wrapping or overflow
- [ ] Briefing footers: 2-column grid at mobile, 4-column at desktop

### Performance Checks

- [ ] Lighthouse Performance score > 90
- [ ] First Contentful Paint < 1.5s
- [ ] No layout shift (CLS = 0)
- [ ] No unnecessary JavaScript hydration on static pages
- [ ] Page source shows pre-rendered HTML (view-source:, not empty div)

---

## Production Smoke Test

Run after promoting preview to production at deevo-sim.vercel.app.

### Critical Path (must pass before announcing)

1. [ ] `https://deevo-sim.vercel.app/` — loads in < 2s, shows 15 scenarios
2. [ ] `https://deevo-sim.vercel.app/scenario/hormuz_chokepoint_disruption` — all 5 sections render
3. [ ] `https://deevo-sim.vercel.app/decision/hormuz_chokepoint_disruption` — primary directive visible at dominant scale
4. [ ] `https://deevo-sim.vercel.app/evaluation` — register shows 15 evaluations with verdicts
5. [ ] `https://deevo-sim.vercel.app/evaluation/hormuz_chokepoint_disruption` — expected vs actual renders
6. [ ] Full navigation chain: Landing → Scenario → Decision → Evaluation without 404 or error

### API Health (if backend integration is active)

7. [ ] `https://deevo-sim.vercel.app/health` — proxies to backend health endpoint
8. [ ] `https://deevo-sim.vercel.app/api/health` — proxies to backend health endpoint

### Edge Cases

9. [ ] Invalid slug returns 404: `/scenario/does_not_exist`
10. [ ] Direct URL access works (no client-side routing dependency)
11. [ ] Browser back button works through the full navigation chain
12. [ ] Page refresh on any route returns the correct page (not 404)
13. [ ] Open Graph meta tags present in page source for social sharing

### Infrastructure

14. [ ] Vercel deployment logs show no build warnings beyond the lockfile notice
15. [ ] Function execution count in Vercel dashboard is zero for page routes (confirms SSG)
16. [ ] Build time is reasonable (< 3 minutes)
17. [ ] Bundle size in Vercel dashboard — note the value for baseline monitoring
