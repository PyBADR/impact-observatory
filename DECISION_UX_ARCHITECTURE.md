# Decision UX Architecture — Impact Observatory
## From Intelligent System to Obvious System

**Status:** Architecture Complete | **Scope:** Frontend-only — zero backend changes
**Principle:** The system is not missing logic. It is missing clarity.

---

## 1. UX Diagnosis (Current State)

The Impact Observatory has an extraordinarily powerful 85-stage simulation engine producing provenance-traced, factor-decomposed, uncertainty-banded, decision-ranked outputs. The problem: **none of this reaches the user's eyes.**

### What the frontend currently renders:

**FinancialImpactPanel** — Shows `$4.2B` in 4xl bold. No explanation of why. No breakdown visible. No range. No confidence. No "what caused this." The propagation summary at the bottom is a single sentence that restates the headline without adding causality.

**DecisionActionCard** — Shows rank, title, urgency%, value%, time-to-act, cost, loss-avoided. Six metrics in a grid. Zero explanation of *why this action*, *why this rank*, *why now*, *what happens if you don't act*. Urgency is "85%" — 85% of what? No anchor.

**KPICard** — Label + big number + trend arrow. No definition. No drill-down. No factor breakdown. Trend arrow (↑) — is that good or bad? No context.

**MacroOverviewHeader** — System Risk Index 65%, Total Exposure $4.2B, 12 Critical Nodes. Impressive density, zero causality. "System Stress: 58%" — stress on what?

**TrustBox** — "82% Confidence" with a colored bar. "10-Stage Pipeline" as a label. Trace ID as a hash snippet. Assumptions hidden behind a click. The user sees a trust badge but gains no actual trust.

### Summary diagnosis:

The current UI is a **data display system**, not a **decision support system**. Every component answers "what" but never "why." The backend has all the "why" — it's computed, typed, tested, and exposed via 10 API endpoints. The frontend doesn't consume any of it.

---

## 2. UX Problems Mapped to User Feedback

| User Feedback | Root Cause | Backend Data Available (Unused) |
|---|---|---|
| "The data is complex and requires reading everything" | No progressive disclosure. All data at same priority level. No executive snapshot. | `provenance_layer.pipeline_meta` has pre-computed summaries |
| "Numbers are shown without explaining how they were calculated" | `FinancialImpactPanel` shows `$4.2B` with zero factor breakdown | `/metrics-provenance` returns formula + 5 contributing factors per metric |
| "I don't know why loss is 93M" | No connection between loss figure and its drivers | `/factor-breakdown` returns exact split: shipping 35%, liquidity 25%, market 20%, regulatory 20% |
| "I don't know why price increased 39%" | Sector bars show magnitude but not causation | `/metrics-provenance` contributing_factors includes weight + description |
| "I cannot make a decision without understanding the cause" | `DecisionActionCard` has no "why" fields | `/decision-reasoning` returns `why_this_decision`, `why_now`, `why_this_rank` per action |
| "Loss should be a range, not a fixed number" | `formatLoss()` renders single point | `/metric-ranges` returns `{min, expected, max, confidence_band}` per metric |
| "I need to know data recency and source" | `TrustBox` shows model version only | `/data-basis` returns historical analog, calibration period, freshness flag per metric |
| "Add profit / minimum loss context" | Only downside shown | `/metric-ranges` min_value IS the best-case; factor breakdowns show mitigation potential |

**Every single user complaint maps to a backend API that already exists and is not consumed.**

---

## 3. New UX Patterns (with Examples)

### Pattern A: "Why This Number" Popover

Every bold number in the UI becomes clickable. On click, a popover appears showing:

```
┌──────────────────────────────────────────────┐
│  Total Loss: $93M                            │
│  ────────────────────────────────────────     │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  Shipping      35%   │
│  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  Liquidity     25%   │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  Market        20%   │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  Regulatory    20%   │
│  ────────────────────────────────────────     │
│  Formula: Σ(sector × impact × θ)             │
│  Confidence: 78% · Range: $60M – $140M       │
│  📎 Based on: Tanker War analog (82% match)  │
└──────────────────────────────────────────────┘
```

**Data source:** `/factor-breakdown` + `/metric-ranges` + `/data-basis`
**Interaction:** Click on any bold metric → popover with factor bars + range + basis

### Pattern B: "Decision Reason Card"

Replaces the current `DecisionActionCard` metrics grid with a narrative-first card:

```
┌──────────────────────────────────────────────┐
│  ① Execute Liquidity Support                 │
│  ─────────────────────────────────────────── │
│  WHY: Liquidity breach projected in 12h.     │
│  Trade disruption propagates to banking      │
│  sector via Hormuz → ADCB → interbank.       │
│                                              │
│  WHY NOW: Time-to-act window closes in 8h.   │
│  Delay increases systemic loss by 40%.        │
│                                              │
│  COST: $250M → AVOIDS: $800M (net +$550M)   │
│  ████████████████████░░░░░  78% confidence   │
│                                              │
│  [Submit for Review]                         │
└──────────────────────────────────────────────┘
```

**Data source:** `/decision-reasoning` → `why_this_decision_en`, `why_now_en`, `propagation_link_en`

### Pattern C: "Range Bar" (replaces point values)

```
  Loss:   ├─── $60M ────── $93M ────── $140M ───┤
                            ▲
                        expected
          Confidence: 78%  ·  Band: ±42%
```

**Data source:** `/metric-ranges` → `min_value`, `expected_value`, `max_value`, `confidence_band`

### Pattern D: "Freshness Badge"

Small badge next to any metric:

```
  $93M  [CALIBRATED · Tanker War 2019 · 82% match]
  $93M  [SIMULATED · No historical analog]
  $93M  [PARAMETRIC ⚠ · Treat as indicative]
```

**Data source:** `/data-basis` → `freshness_flag`, `analog_event`, `analog_relevance`, `freshness_weak`

### Pattern E: "Executive Snapshot" (5-second comprehension)

```
┌──────────────────────────────────────────────────────────┐
│  HORMUZ CHOKEPOINT DISRUPTION                    SEVERE  │
│  ─────────────────────────────────────────────────────── │
│                                                          │
│  WHAT: Shipping disruption cascades to banking + fintech │
│  LOSS: $60M — $93M — $140M (78% confidence)             │
│  BREACH: Liquidity breach in 12h if unmitigated          │
│                                                          │
│  TOP 3 DECISIONS:                                        │
│  ① Liquidity support ($250M cost → $800M avoided)        │
│  ② Port rerouting ($45M cost → $320M avoided)            │
│  ③ Insurance reserve activation ($0 → $180M preserved)   │
│                                                          │
│  Shock path: Shipping → Banking → Fintech                │
│  Peak impact: Day 7 of 30                                │
└──────────────────────────────────────────────────────────┘
```

**Data source:** `headline` + `/metric-ranges` for loss + `/decision-reasoning` for top 3 + propagation chain for shock path

### Pattern F: "Progressive Disclosure" (3-Level Depth)

```
Level 1 (DEFAULT):  $93M loss · SEVERE · 3 decisions ready
Level 2 (CLICK):    Factor breakdown + range + decision cards
Level 3 (EXPAND):   Full provenance + formula + data basis + audit trail
```

**Mechanism:** Level 1 = executive snapshot. Level 2 = "Why This Number" popovers + decision reason cards. Level 3 = full provenance panel (already wired to API).

---

## 4. Executive Snapshot Design

### Component: `<ExecutiveSnapshot />`

**Position:** Top of every view. Fixed. No scrolling. Visible within 5 seconds.

**Layout:**
```
┌───────────────────────────────────────────────────────────────────┐
│ Row 1: Scenario Identity                                         │
│   [SEVERE] Hormuz Chokepoint Disruption · 30-day horizon         │
│                                                                   │
│ Row 2: One-Line Propagation Statement                            │
│   "Shock propagates: Shipping → Banking → Fintech.               │
│    Liquidity breach expected in 12h."                            │
│                                                                   │
│ Row 3: Three Impact Cards (horizontal)                           │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│   │ LOSS         │ │ RISK        │ │ BREACH      │               │
│   │ $60M—$93M—   │ │ 0.52—0.68— │ │ 12h until   │               │
│   │ $140M        │ │ 0.81        │ │ LCR breach  │               │
│   │ 78% conf     │ │ HIGH        │ │ CRITICAL    │               │
│   └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                   │
│ Row 4: Three Decision Cards (horizontal, condensed)              │
│   ① Liquidity support → saves $550M net                          │
│   ② Port rerouting → saves $275M net                             │
│   ③ Insurance reserves → preserves $180M                         │
└───────────────────────────────────────────────────────────────────┘
```

**Data sources:**
- Row 1: `run_result.scenario`, `run_result.risk_level`
- Row 2: Built from `propagation_chain` top 3 sectors + `decision_plan.time_to_first_failure_hours`
- Row 3: `/metric-ranges` for loss, URS, banking_stress
- Row 4: `/decision-reasoning` top 3 by rank + `cost_usd`, `loss_avoided_usd`

**Rules:**
- Max 4 rows. No fifth row. No scrolling.
- Row 2 is ONE sentence. Generated from propagation chain: take top 3 sectors by impact, chain them with "→", append breach timing.
- Impact cards show ranges, not points. Min — Expected — Max format.
- Decision cards show net value (benefit − cost) and one-word action summary.

---

## 5. Metric Explanation Design

### Component: `<MetricExplainer />`

**Trigger:** Click on any bold metric value in any component.

**Content (popover):**

```
┌ MetricExplainer ──────────────────────────────────────┐
│                                                        │
│  Total Loss: $93M                                      │
│  ──────────────────────────────────────────────────    │
│                                                        │
│  WHY THIS NUMBER:                                      │
│  ▓▓▓▓▓▓▓▓▓▓▓░░  Shipping disruption    $33M  (35%)   │
│  ▓▓▓▓▓▓▓▓░░░░░  Liquidity stress       $23M  (25%)   │
│  ▓▓▓▓▓▓░░░░░░░  Market reaction        $19M  (20%)   │
│  ▓▓▓▓▓▓░░░░░░░  Regulatory delay       $19M  (20%)   │
│  ──────────────────────────────────────────────────    │
│  100% of value explained                               │
│                                                        │
│  RANGE:                                                │
│  ├── $60M ──────── $93M ──────── $140M ──┤            │
│  78% confidence · Band ±42%                            │
│                                                        │
│  DATA BASIS:                                           │
│  [CALIBRATED] Tanker War analog (82% match)            │
│  Model: deterministic formula · Period: 2019–2024      │
│                                                        │
│  ▸ Show full formula                                   │
└────────────────────────────────────────────────────────┘
```

**Data mapping:**
- Factor bars → `/factor-breakdown` `.factors[]` → `contribution_value`, `contribution_pct`
- Range → `/metric-ranges` → `min_value`, `expected_value`, `max_value`, `confidence_band`
- Data basis → `/data-basis` → `freshness_flag`, `analog_event`, `analog_relevance`
- Formula (hidden by default) → `/metrics-provenance` → `formula`

**Interaction:**
- Click on metric value → popover opens
- Popover has 3 sections: factors (always visible), range (always visible), data basis (always visible)
- "Show full formula" link at bottom → expands to show exact formula string + contributing_factors with weights
- Click outside → popover closes

---

## 6. Decision Card Design

### Component: `<DecisionReasonCard />`

**Replaces:** Current `DecisionActionCard` which shows 6 unexplained metrics.

**Layout:**

```
┌ DecisionReasonCard ────────────────────────────────────┐
│                                                         │
│  ① EXECUTE LIQUIDITY SUPPORT            [IMMEDIATE]    │
│     التنفيذ: دعم السيولة                                │
│  ───────────────────────────────────────────────────    │
│                                                         │
│  WHY THIS DECISION:                                     │
│  Liquidity breach projected in 12h. Trade disruption    │
│  propagates via Hormuz → ADCB → interbank channel.      │
│                                                         │
│  WHY NOW:                                               │
│  Action window closes in 8h. Severity regime:           │
│  CRISIS — auto-escalation active. Delay increases       │
│  systemic exposure by 40%.                              │
│                                                         │
│  ECONOMICS:                                             │
│  Cost          $250M  ████░░░░░░                        │
│  Loss Avoided  $800M  ██████████████████████            │
│  Net Benefit   +$550M                                   │
│  Confidence    78%    ████████████████░░░░               │
│                                                         │
│  IF NOT EXECUTED:                                       │
│  Banking aggregate stress rises from 0.45 → 0.72       │
│  (ELEVATED → HIGH). 3 additional entities breached.     │
│                                                         │
│  [Submit for Review]                                    │
└─────────────────────────────────────────────────────────┘
```

**Data mapping:**
- Title + rank → existing `DecisionActionV2`
- "WHY THIS DECISION" → `/decision-reasoning` → `why_this_decision_en`
- "WHY NOW" → `/decision-reasoning` → `why_now_en` + `regime_link_en`
- Economics → existing `cost_usd`, `loss_avoided_usd`
- Confidence → existing `priority_score` or from `/metric-ranges`
- "IF NOT EXECUTED" → `/decision-reasoning` → `tradeoff_summary_en`

**Key change:** The card leads with narrative ("WHY") not metrics. Cost/benefit becomes a secondary visual bar. The user reads the reason FIRST, then confirms the economics.

---

## 7. Data Provenance Display Design

### Component: `<DataProvenanceBadge />` (inline) + `<DataProvenancePanel />` (expanded)

**Inline badge (always visible next to any metric):**

```
  $93M  ◉ CALIBRATED
  $93M  ◎ SIMULATED
  $93M  ⚠ PARAMETRIC
```

**Color coding:**
- CALIBRATED → emerald-500 (strong basis)
- SIMULATED → blue-500 (network model)
- DERIVED → slate-400 (computed from other metrics)
- PARAMETRIC → amber-500 (weak basis, flagged)

**Expanded panel (on click of badge):**

```
┌ DataProvenancePanel ───────────────────────────────────┐
│                                                         │
│  Total Loss · إجمالي الخسائر                           │
│  ───────────────────────────────────────────────────    │
│                                                         │
│  MODEL:                                                 │
│  Deterministic formula                                  │
│  Σ(sector_exposure × impact_factor × base_loss × θ)    │
│                                                         │
│  HISTORICAL REFERENCE:                                  │
│  Tanker War / 2019 Strait incidents                     │
│  Period: 1984–1988 / Jun–Sep 2019                       │
│  Relevance: ████████████████████░░  82%                 │
│                                                         │
│  CALIBRATION:                                           │
│  Source: GCC GDP sectoral data (IMF WEO 2024)          │
│  Period: 2019–2024 annual data                          │
│                                                         │
│  FRESHNESS: CALIBRATED                                  │
│  Model parameters last updated: 2024-Q4                 │
│  ✓ This metric has strong historical basis              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Data mapping:**
- Badge → `/data-basis` → `freshness_flag`
- Model → `/data-basis` → `model_type`, `calibration_basis_en`
- Historical → `/data-basis` → `analog_event`, `analog_period`, `analog_relevance`
- Freshness → `/data-basis` → `freshness_detail_en`, `freshness_weak`

**Rule:** If `freshness_weak === true`, badge uses amber with ⚠ icon and adds text: "Treat outputs as indicative."

---

## 8. Interaction Model (Click / Hover / Expand)

### Three-Tier Interaction:

| Tier | Trigger | Content | Duration |
|------|---------|---------|----------|
| **Glance** | Page load | Executive Snapshot (Row 1-4), risk level badge, severity color | 5 seconds |
| **Inspect** | Click on any bold metric | MetricExplainer popover: factors + range + basis | 10 seconds |
| **Investigate** | Click "Show full formula" or "View full provenance" | Full DataProvenancePanel or API-level detail | 30+ seconds |

### Specific Interactions:

| Element | Current Behavior | New Behavior |
|---------|-----------------|--------------|
| Loss headline ($93M) | Static text | **Click** → MetricExplainer popover with factor bars, range, basis |
| Sector exposure bar | Static bar | **Click** → MetricExplainer for that sector's exposure value |
| System Risk Index | Gauge + percentage | **Click** → URS 5-factor breakdown popover |
| Decision card title | Static text | Already linked; no change needed |
| Decision metrics (urgency, value, etc.) | Static percentage | **Replaced** by narrative "WHY" blocks from `/decision-reasoning` |
| Confidence percentage | Colored number | **Click** → Confidence 4-factor breakdown popover |
| KPI card | Big number + trend | **Click** → MetricExplainer for that KPI |
| Freshness badge | Does not exist | **New:** Inline badge (◉/◎/⚠) next to every metric. **Click** → DataProvenancePanel |
| "Show more" / depth toggle | Does not exist | **New:** Level 1/2/3 toggle at top of each section |

### State Management:

```typescript
// New Zustand slice for provenance UI state
interface ProvenanceUIState {
  activePopover: string | null;       // metric_name of open explainer
  depthLevel: 1 | 2 | 3;            // progressive disclosure level
  setPopover: (metric: string | null) => void;
  setDepth: (level: 1 | 2 | 3) => void;
}
```

### Data Fetching Strategy:

Provenance data is fetched ONCE per run, then cached:

```typescript
// In use-api.ts — add alongside existing hooks
export function useMetricsProvenance(runId: string) {
  return useQuery({
    queryKey: ['provenance', 'metrics', runId],
    queryFn: () => fetchMetricsProvenance(runId),
    staleTime: Infinity,  // provenance doesn't change for a completed run
    enabled: !!runId,
  });
}

export function useFactorBreakdown(runId: string) { /* same pattern */ }
export function useMetricRanges(runId: string) { /* same pattern */ }
export function useDecisionReasoning(runId: string) { /* same pattern */ }
export function useDataBasis(runId: string) { /* same pattern */ }
```

---

## 9. What to REMOVE or Simplify

### REMOVE (zero decision value):

| Element | Location | Reason |
|---------|----------|--------|
| Pipeline stage count ("5/9 stages") | MacroOverviewHeader | Implementation detail. User doesn't care which stage is running. Replace with loading spinner + "Analyzing…" |
| Trace ID hash snippet | TrustBox | Meaningless to humans. Move to Level 3 (full provenance panel only) |
| "Deterministic Simulation Engine" badge | TrustBox | Technical jargon. Replace with "Model: v2.1 · 85-stage analysis" |
| Model equation string | explainability.model_equation | LaTeX in a business dashboard. Move to Level 3 |
| Pipeline progress bar | MacroOverviewHeader secondary row | Status: completed is all that matters post-run |
| Architecture tab | ArchitectureTab.tsx | Zero decision value. Developer tool only. Hide behind admin flag |
| DataFlowPanel | DataFlowPanel.tsx | Pipeline visualization for engineers. Move to analyst-only Level 3 |
| PipelineViewer | PipelineViewer.tsx | 10-stage execution detail. Developer diagnostics. Remove from default view |

### SIMPLIFY:

| Element | Current | Simplified |
|---------|---------|-----------|
| Sector exposure bars | 8 bars with USD amounts only | Top 3 bars with factor breakdown on click |
| Decision card metrics grid | 6 numbers (urgency, value, time, cost, loss-avoided, priority) | Remove urgency/value/priority. Keep: cost, benefit, net value. Add: WHY narrative |
| MacroOverviewHeader KPIs | 8 KPIs in a row (risk, exposure, nodes, critical, elevated, confidence, stress, pipeline) | 3 KPIs only: Loss Range, Risk Level, Time to Breach |
| TrustBox | Model version + confidence + methodology + trace + assumptions | Confidence percentage + freshness badge. Full detail on Level 3 |
| Region chips | 5+ chips with no values | Top 3 regions with USD exposure |

### REORDER (Decision-First):

**Current priority order in Command Center:**
1. Macro overview (data)
2. Transmission channels (charts)
3. Country/sector exposure (data)
4. Decisions (buried at position 4)
5. Trust (position 5)
6. Operational detail (position 6)

**New priority order:**
1. **Executive Snapshot** (scenario + propagation statement + 3 impacts + 3 decisions)
2. **Decision cards** (with WHY narrative — promoted from position 4)
3. **Impact detail** (factor breakdowns on click — replaces data-first approach)
4. **Trust + Provenance** (badges inline, panel on demand)

---

## 10. Frontend Implementation Plan (Step-by-Step)

### Phase 1: Data Hooks (Day 1) — Foundation

**Files to create:**

```
frontend/src/hooks/use-provenance.ts
```

**Content:** 5 React Query hooks wrapping the provenance API client:
- `useMetricsProvenance(runId)` → fetches `/metrics-provenance`
- `useFactorBreakdown(runId)` → fetches `/factor-breakdown`
- `useMetricRanges(runId)` → fetches `/metric-ranges`
- `useDecisionReasoning(runId)` → fetches `/decision-reasoning`
- `useDataBasis(runId)` → fetches `/data-basis`

All with `staleTime: Infinity` (provenance is immutable per run).

### Phase 2: Atomic Components (Day 2-3) — Building Blocks

**Files to create:**

```
frontend/src/components/provenance/MetricExplainer.tsx    — Factor popover
frontend/src/components/provenance/RangeBar.tsx          — Min-expected-max visual
frontend/src/components/provenance/FreshnessBadge.tsx    — Inline ◉/◎/⚠ badge
frontend/src/components/provenance/DataProvenancePanel.tsx — Full provenance detail
frontend/src/components/provenance/FactorBar.tsx          — Single factor bar
```

Each component is self-contained. Receives typed props from the hooks. No internal fetching.

### Phase 3: Composite Components (Day 4-5) — Decision UX

**Files to create:**

```
frontend/src/components/provenance/ExecutiveSnapshot.tsx     — Top-level 4-row summary
frontend/src/components/provenance/DecisionReasonCard.tsx    — Narrative-first decision card
frontend/src/components/provenance/DepthToggle.tsx           — Level 1/2/3 selector
```

`ExecutiveSnapshot` composes: RangeBar × 3, propagation statement builder, DecisionReasonCard × 3.
`DecisionReasonCard` composes: reason narrative, economics bars, tradeoff summary.

### Phase 4: Integration (Day 6-7) — Wire Into Existing Views

**Files to modify:**

```
frontend/src/components/FinancialImpactPanel.tsx
  → Make loss headline clickable → opens MetricExplainer
  → Add RangeBar below headline
  → Add FreshnessBadge next to loss value
  → Reduce sector bars from 8 to top 3, make clickable

frontend/src/components/DecisionActionCard.tsx
  → Replace with DecisionReasonCard
  → Or: add WHY section above metrics grid, collapse grid to essentials

frontend/src/components/KPICard.tsx
  → Make value clickable → opens MetricExplainer
  → Add FreshnessBadge

frontend/src/features/command-center/components/MacroOverviewHeader.tsx
  → Replace 8-KPI row with 3-KPI row (Loss, Risk, Breach)
  → Remove pipeline progress
  → Add one-line propagation statement

frontend/src/features/command-center/components/DecisionPriorities.tsx
  → Swap DecisionActionV2 cards for DecisionReasonCard
  → Add decision reasoning data via useDecisionReasoning hook

frontend/src/app/command-center/page.tsx
  → Insert ExecutiveSnapshot as Zone 0 (above MacroOverviewHeader)
  → Move DecisionPriorities to Zone 1 (promoted)
  → Demote MacroOverview to Zone 2
```

### Phase 5: Cleanup (Day 8) — Remove Noise

**Files to modify:**
- Remove or hide: ArchitectureTab, DataFlowPanel, PipelineViewer from default views
- Simplify TrustBox: confidence + badge only. Full detail behind "View Details"
- Remove trace ID from visible surface (keep in Level 3)

### Dependency Graph:

```
Phase 1 (hooks)
  ↓
Phase 2 (atomic components) — no dependencies between atoms
  ↓
Phase 3 (composites) — depend on Phase 2
  ↓
Phase 4 (integration) — depend on Phase 3
  ↓
Phase 5 (cleanup) — independent, can run in parallel with Phase 4
```

### Testing Strategy:

- Phase 1: Mock API responses, verify hook return types
- Phase 2: Storybook/unit test each atom with typed fixture data
- Phase 3: Integration test: pass run_result fixture through composites, verify render
- Phase 4: E2E: run scenario → verify ExecutiveSnapshot renders with correct values
- Phase 5: Visual regression: screenshot before/after cleanup

---

## Success Criteria Checklist

- [ ] Non-technical user understands system state in under 10 seconds (ExecutiveSnapshot)
- [ ] Every bold metric is clickable and shows "why" (MetricExplainer)
- [ ] Loss shown as range, not point (RangeBar)
- [ ] Every decision card explains "why this", "why now", "what if not" (DecisionReasonCard)
- [ ] Data freshness visible inline (FreshnessBadge)
- [ ] Default view is decision-first, not data-first (reordering)
- [ ] Progressive disclosure: Level 1 simple, Level 2 factors, Level 3 full provenance
- [ ] Cognitive load reduced: 8 KPIs → 3, 6 decision metrics → narrative + economics
- [ ] Zero backend changes. Zero new APIs. Zero new computation.
