# Provenance UX Wiring — Placement Instructions

## Overview

5 wiring files connect existing provenance components to existing pages.
**NO backend changes. NO new APIs. NO new ML. ONLY UI wiring.**

---

## File Inventory

| # | File | Purpose | Depends On |
|---|------|---------|------------|
| 1 | `WhyMetricInline.tsx` | Universal "Why This Number" wrapper | MetricExplainer, 4 provenance hooks |
| 2 | `PropagationFallback.tsx` | Empty-state propagation display | CausalStep type only |
| 3 | `ExecutiveBriefV2.tsx` | Wired ExecutiveSnapshot | ExecutiveSnapshot, useMetricRanges, useDecisionReasoning |
| 4 | `SectorStressV2.tsx` | Enhanced sector panels | WhyMetricInline, FreshnessBadge, RangeBar, FactorBar, 3 provenance hooks |
| 5 | `DecisionRoomV2.tsx` | Full page assembly | ExecutiveBriefV2, DecisionReasonCard, SectorStressV2, PropagationFallback, DepthToggle |

---

## Placement 1: Command Center (`app/command-center/page.tsx`)

### Drop-in: DecisionRoomV2 above Zone 1

**Location:** After line 366 (BoardView closing div), before line 368 (Phase 1.5).

**Import to add (line ~46):**
```tsx
import { DecisionRoomV2 } from "@/components/provenance";
```

**Replacement snippet — insert between BoardView and Phase 1.5:**
```tsx
      {/* ── DECISION ROOM V2: Provenance-Enhanced Decision Layer ── */}
      <div className="flex-shrink-0 px-6 py-4 bg-[#0B0F1A]">
        <DecisionRoomV2
          runId={runId ?? undefined}
          scenarioLabel={scenario.label}
          scenarioLabelAr={scenario.labelAr ?? ""}
          severity={scenario.severity}
          totalLossUsd={headline.totalLossUsd}
          averageStress={headline.averageStress}
          propagationDepth={headline.propagationDepth}
          peakDay={headline.peakDay}
          causalChain={causalChain}
          decisionActions={decisionActions}
          sectorRollups={sectorRollups}
          locale="en"
          onSubmitForReview={(actionId) => executeAction(actionId)}
        />
      </div>
```

**What this replaces:** Nothing — additive insertion. The existing zones remain below.

---

## Placement 2: WhyMetricInline in MacroOverviewHeader

### Wrap key metrics with "Why This Number" popover

**File:** `features/command-center/components/MacroOverviewHeader.tsx`

**Pattern:** Find any bold metric display like:
```tsx
<span className="text-2xl font-bold">{formatUSD(totalExposureUsd)}</span>
```

**Replace with:**
```tsx
import { WhyMetricInline } from "@/components/provenance";

<WhyMetricInline metricName="total_loss_usd" runId={runId} locale="en">
  <span className="text-2xl font-bold">{formatUSD(totalExposureUsd)}</span>
</WhyMetricInline>
```

**Note:** MacroOverviewHeader doesn't currently receive `runId`. To wire it:
1. Add `runId?: string` to its props interface
2. Pass `runId={runId ?? undefined}` from page.tsx

**Key metrics to wrap:**
- `total_loss_usd` → totalExposureUsd
- `aggregate_stress` → systemRiskIndex / averageStress
- `propagation_depth` → nodesImpacted

---

## Placement 3: DecisionPriorities Enhancement

### File: `features/command-center/components/DecisionPriorities.tsx`

The existing DecisionPriorities renders action cards. To add provenance:

**Option A (minimal):** Replace `<DecisionPriorities>` call in page.tsx with:
```tsx
{/* Original DecisionPriorities with provenance overlay */}
<DecisionPriorities
  actions={decisionActions}
  onExecute={executeAction}
  isLive={isLive}
/>
```
This is already handled by DecisionRoomV2 at Level 2 (which shows DecisionReasonCards). 
The existing Zone 4 DecisionPriorities can remain as a fallback for users who don't open Level 2.

**Option B (replace):** Remove Zone 4 DecisionPriorities entirely since DecisionRoomV2 now provides superior decision cards at Level 2.

---

## Placement 4: Sector Tabs (Banking / Insurance / Fintech)

### In OperationalDetail's "Sectors" tab

**File:** `features/command-center/components/OperationalDetail.tsx`

The Sectors tab currently renders BankingDetailPanel / InsuranceDetailPanel / FintechDetailPanel.

**Enhancement:** Add SectorStressV2 as a header above the existing detail panels:
```tsx
import { SectorStressV2 } from "@/components/provenance";

{/* Inside the Sectors tab content */}
<SectorStressV2
  runId={runId}
  sectorRollups={sectorRollups}
  locale="en"
  activeSector={activeSector}
  onSectorChange={setActiveSector}
/>
{/* Existing detail panel below */}
{activeSector === "banking" && <BankingDetailPanel data={bankingData} />}
{activeSector === "insurance" && <InsuranceDetailPanel data={insuranceData} />}
{activeSector === "fintech" && <FintechDetailPanel data={fintechData} />}
```

**Note:** OperationalDetail needs `runId` and `sectorRollups` passed as new props.

---

## Placement 5: PropagationFallback in OperationalDetail

### In the "Propagation" tab when graph/map is empty

**File:** `features/command-center/components/OperationalDetail.tsx`

**Pattern:** In the Propagation tab, add a fallback when the graph view is empty:
```tsx
import { PropagationFallback } from "@/components/provenance";

{/* Inside Propagation tab */}
{graphNodes.length === 0 ? (
  <PropagationFallback
    scenarioLabel={scenarioLabel}
    causalChain={causalChain}
    propagationDepth={propagationDepth}
    peakDay={peakDay}
    totalLossUsd={totalLossUsd}
    locale="en"
  />
) : (
  {/* Existing graph visualization */}
)}
```

---

## Placement 6: Enterprise Intelligence Page

### File: `app/enterprise/page.tsx` (if exists)

The same `DecisionRoomV2` can be embedded in any page that has a runId:

```tsx
import { DecisionRoomV2 } from "@/components/provenance";

// Inside the page component, after fetching run data:
<DecisionRoomV2
  runId={runId}
  scenarioLabel={scenario.label}
  scenarioLabelAr={scenario.labelAr}
  severity={scenario.severity}
  totalLossUsd={headline.totalLossUsd}
  averageStress={headline.averageStress}
  propagationDepth={headline.propagationDepth}
  peakDay={headline.peakDay}
  causalChain={causalChain}
  decisionActions={decisionActions}
  sectorRollups={sectorRollups}
  locale="en"
/>
```

---

## Props Mapping Summary

### DecisionRoomV2 — from useCommandCenter():
```
runId                  ← searchParams.get("run")
scenarioLabel          ← scenario.label
scenarioLabelAr        ← scenario.labelAr ?? ""
severity               ← scenario.severity
totalLossUsd           ← headline.totalLossUsd
averageStress          ← headline.averageStress
propagationDepth       ← headline.propagationDepth
peakDay                ← headline.peakDay
causalChain            ← causalChain
decisionActions        ← decisionActions
sectorRollups          ← sectorRollups
locale                 ← "en" | "ar" (from i18n context or hardcoded)
onSubmitForReview      ← executeAction (from useCommandCenter)
```

### WhyMetricInline — universal wrapper:
```
metricName             ← snake_case key matching backend provenance
runId                  ← from URL or parent
locale                 ← "en" | "ar"
children               ← the rendered metric value
```

### SectorStressV2 — from useCommandCenter():
```
runId                  ← searchParams.get("run")
sectorRollups          ← sectorRollups
locale                 ← "en" | "ar"
activeSector           ← local state (default: "banking")
onSectorChange         ← local state setter
```

---

## Implementation Sequence

1. **Add imports** to `command-center/page.tsx` (1 line)
2. **Insert DecisionRoomV2** between BoardView and Phase 1.5 (15 lines)
3. **Test** — DecisionRoomV2 should render with mock data immediately
4. **Optionally** wire WhyMetricInline into MacroOverviewHeader metrics
5. **Optionally** wire SectorStressV2 into OperationalDetail Sectors tab
6. **Optionally** wire PropagationFallback into OperationalDetail Propagation tab

Steps 1-3 are the critical path. Steps 4-6 are progressive enhancements.
