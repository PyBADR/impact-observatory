# Impact Observatory — Executive Demo QA Audit Report

**Date:** 2026-04-12  
**URL:** https://deevo-sim.vercel.app/demo  
**Scenario:** Energy & Trade Disruption (Hormuz)  
**Evaluator:** Automated Executive QA  

---

## 1. ACCESS VALIDATION — PASS

The `/demo` route loads without errors. The landing page renders within 2 seconds showing the IO brand mark, "Impact Observatory" heading, "Macro Financial Intelligence for GCC" tagline, and a prominent "Start Executive Demo" button. Keyboard hints (Space, Arrow Keys, Esc) display correctly below the CTA. No blank screens, no console errors, no broken assets.

## 2. FIRST IMPRESSION — PASS

The landing page conveys institutional credibility. White background, centered layout, minimal typography. The brand badge (slate-900 "IO" mark) is clean but small. The tagline "Scenario-based financial stress assessment for the GCC region" positions the product correctly without overselling. A CEO would recognize this as an intelligence platform, not a dashboard or toy demo.

## 3. 30-SECOND UNDERSTANDING — PASS

Within 30 seconds of clicking "Start Executive Demo," the viewer encounters Layer 1 (Macro State) which immediately communicates: what is happening ("GCC financial conditions tightening under energy supply disruption"), what the severity is ("ELEVATED"), and what the numbers are (31/43 exposure points, 168h time horizon, 84% confidence, $4.9B estimated exposure). Macro signals table (Brent Crude, GCC Interbank Rate, Baltic Dry Index, etc.) gives concrete economic anchors. A viewer understands the situation without technical explanation.

## 4. LANGUAGE AUDIT — PASS (with 1 exception)

Across all 9 active V4 layers, the language is consistently executive-grade and financial. No forbidden words appear in any user-visible text except one:

**Exception:** Layer 5 (Insurance) displays "Cargo Claims Pipeline" — the word "Pipeline" was on the forbidden list. Should read "Cargo Claims Backlog" or "Cargo Claims Volume."

All other language verified clean across every layer:

- "Exposure Points" (not "Nodes") ✓
- "Stress Transmission" (not "Propagation") ✓
- "Assessment flow" (not "Pipeline") ✓ (in Trust Layer footer)
- "Scenario-based" / "estimated" / "projected" / "reference" data labels ✓
- "This is Macro Financial Intelligence" (not "AI Simulation System") ✓
- "Every estimate is auditable" (not "Every simulation is auditable") ✓
- "Impact Observatory v4.0" (not "IO Simulation Engine") ✓

Legacy components (IntroStep, TrustStep, TransmissionStep, DecisionStep, ScenarioStep) still contain forbidden words but are NOT rendered in the V4 demo flow.

## 5. TRANSMISSION CLARITY — PASS

Layer 2 (Transmission) clearly communicates how stress moves through the system. The "STRESS TRANSMISSION PATH" shows 5 sequential exposure points: Energy & Commodities → Trade & Logistics → Banking & Liquidity → Insurance & Pricing → Fiscal & Policy. Edge labels between nodes (Price surge, Trade finance pressure, Liquidity tightening, Claims acceleration) explain the mechanism at each link. Animated cascade with progressive lighting makes the sequence intuitive. Running caption at bottom ("Step 5: Fiscal & Policy — Fiscal reserves under pressure — stabilization required") reinforces understanding. No technical jargon.

## 6. STRUCTURE VALIDATION — PASS

All 9 layers present and correctly ordered in the right-side navigation:

1. **Macro State** — Regime + signals table
2. **Transmission** — 5-point stress path with cascade animation
3. **Country Exposure** — 4 GCC countries (SA, UAE, Kuwait, Qatar) with flags, stress bars, estimated losses
4. **Banking** — Sector stress 67.0% ELEVATED, 4 metric cards, transmission path, risk indicators
5. **Insurance** — Sector stress 71.0% ELEVATED, 4 metric cards, risk absorption chain, downstream impact
6. **Sector Impact** — 3 critical sectors + 2 secondary exposure sectors with recommended levers
7. **Decision Room** — 5 executive interventions with expected effects and delay risks
8. **Outcome** — Base vs. Mitigated comparison with value saved
9. **Trust Layer** — Sources, assumptions, confidence, data freshness, assessment flow

Layer progression tells a coherent story: What happened → How it spreads → Where it hits → What you can do → What it costs → Why you should trust it.

## 7. DECISION QUALITY — FAIL

The Decision Room (Layer 7) contains a **critical display bug**: the countdown timer renders as "2d 21.200000000000145h remaining to activate mitigations" — a JavaScript floating-point precision error caused by `hours % 24` without rounding in `DecisionEngineStep.tsx` line 37.

**Impact:** This is a demo-breaking bug in front of any executive audience. A number like `21.200000000000145` signals engineering immaturity.

**Fix:** Change line 37-38 from:
```typescript
const remainingHours = hours % 24;
return `${days}d ${remainingHours}h`;
```
To:
```typescript
const remainingHours = Math.round((hours % 24) * 10) / 10;
return `${days}d ${remainingHours}h`;
```

Content quality of the decisions themselves is excellent: clear titles, named owners (Ministry of Energy, Central Bank, Port Authority, Banking Regulator, Insurance Regulator), concrete expected effects, and specific risk-if-delayed consequences with dollar amounts.

## 8. OUTCOME VALIDATION — PASS

Layer 8 shows a clean three-panel comparison: "Without Action" ($4.9B loss, 18–24 months recovery, Critical escalation), "With Coordinated Response" ($4.3B loss, 9–12 months recovery, 12% risk reduction), "Value Saved" ($0.6B). Each panel includes range bands (Low/High) and a "Why" explanation in plain language. The green panel for value saved provides clear visual emphasis. Numbers are internally consistent with earlier layers.

## 9. VISUAL QUALITY — PASS

The design system is consistent across all 9 layers. Slate-900 primary with functional color coding: red/orange for stress indicators, green for positive outcomes, amber for moderate severity. Typography hierarchy is clear (section labels → headlines → body). Card-based layout with consistent borders and spacing. The bottom credibility strip (SOURCES, FRESHNESS, CONFIDENCE, VERSION) persists across all layers. Role tabs (CEO, Risk, Regulator, Energy) at top provide context framing.

**Minor note:** The landing page and IO badge use blue (`bg-blue-600`) which creates a slight brand inconsistency with the slate-900 palette used throughout the demo itself.

## 10. AUTOPLAY BEHAVIOR — PASS

Autoplay starts immediately after clicking "Start Executive Demo." Transitions between layers are smooth (slide animation, ~0.45s). Space bar pauses/resumes. Arrow keys navigate forward/back. Escape returns to landing. Right panel shows progress (LAYER X/9 with percentage). The "Auto-playing" / paused status indicator works correctly. Layer durations feel appropriate — enough time to read each layer before advancing.

## 11. TRUST LAYER — PASS

Layer 9 (Trust) provides institutional credibility: 84% confidence from "Cross-signal consensus," data freshness <10 minutes, multi-signal validation. Data sources are listed with appropriate caveats: "(scenario-based)", "(reference)", "(estimated)", "(projected)". Key assumptions are prioritized by impact level (HIGH, MEDIUM, LOW) with source attribution. The closing statement "This is not a dashboard. This is Macro Financial Intelligence." and the full assessment flow (Signal → Transmission → Exposure → Sector → Decision → Outcome → Audit) reinforce the product category.

## 12. FINAL JUDGMENT — ALMOST READY

---

## Critical Issues

1. **BLOCKER — Decision Room timer floating-point bug**: "2d 21.200000000000145h" is unacceptable in any presentation context. One-line fix in `DecisionEngineStep.tsx`.

## Top 3 Improvements Needed

1. **Fix the floating-point timer** in Decision Room — `Math.round()` the hours remainder. This is the only blocker.

2. **Rename "Cargo Claims Pipeline"** to "Cargo Claims Backlog" or "Cargo Claims Volume" in `demo-scenario.ts` line 340. Last remaining forbidden word in user-visible text.

3. **Clean up legacy step components** (IntroStep.tsx, TrustStep.tsx, TransmissionStep.tsx, DecisionStep.tsx, ScenarioStep.tsx) that still contain forbidden words. While not rendered in V4, they create audit risk if anyone greps the codebase.

---

## Final Verdict

### ALMOST READY

The demo is 95% CEO-presentable. The 9-layer narrative is coherent, the language is executive-grade, the visual design is calm and institutional, and the trust layer closes with credibility. One blocking bug (floating-point timer display) must be fixed before any live presentation. Estimated fix time: 5 minutes. After that fix and the "Pipeline" label rename, this is **READY TO SHOW**.
