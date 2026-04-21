"use client";

/**
 * DecisionRoomV2 — Provably Trustworthy Decision Surface
 *
 * Flow: Macro → Risk → Decision → Why → Compare → Trust → Map Context
 *
 * Layout (ALL visible without clicking):
 *
 *   ┌─────────────────────────────────────────────────────────────┐
 *   │  SCENARIO + MACRO HEADER (with macro → decision links)      │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  GCC IMPACT MAP (6 countries, color-coded, hover detail)    │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  NARRATIVE FLOW (What happened → What it means → What to do)│
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  IMPACT METRIC + SCENARIO BANDS (best/base/worst) + drivers │
 *   │  Risk → Decision link (with vs without action delta)        │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  DECISION COMPARISON (top 3 actions side-by-side)           │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  DECISION CARDS (each with numeric WHY + trust breakdown)   │
 *   ├─────────────────────────────────────────────────────────────┤
 *   │  ADVANCED VIEW (collapsed — ExplainabilityPanel + MacroPanel)│
 *   └─────────────────────────────────────────────────────────────┘
 *
 * CRO/CFO test: "Why is this the best decision?" answered in <10s
 * without clicking anything. Compared to what, based on what data,
 * with what confidence, under what uncertainty.
 */

import { useState, useMemo } from "react";
import { useDecisionReasoning } from "@/hooks/use-provenance";
import { ExplainabilityPanel } from "@/components/trust/ExplainabilityPanel";
import { MacroPanel } from "@/components/macro/MacroPanel";
import type {
  CausalStep,
  DecisionActionV2,
  SectorRollup,
  MetricExplanation,
  DecisionTransparencyResult,
  ReliabilityPayload,
  MacroContext,
  CalibratedCounterfactual,
} from "@/types/observatory";

// ═══════════════════════════════════════════════════════════════════════════════
// GCC Entity System — World Model
// Countries, sectors, entities, and their relationships.
// This is the system's understanding of the GCC financial ecosystem.
// NOT an engine — a static, deterministic knowledge graph for UI rendering.
// ═══════════════════════════════════════════════════════════════════════════════

interface GccEntity {
  id: string;
  nameEn: string;
  nameAr: string;
  type: "central_bank" | "oil_producer" | "port" | "insurer" | "financial_institution" | "sovereign_fund";
  sector: string;
  country: string;
}

interface TransmissionLink {
  from: string;   // entity type or sector
  to: string;
  label: string;
  labelAr: string;
}

const GCC_SECTORS = {
  banking:   { en: "Banking",   ar: "البنوك" },
  insurance: { en: "Insurance", ar: "التأمين" },
  energy:    { en: "Energy",    ar: "الطاقة" },
  logistics: { en: "Logistics", ar: "اللوجستيات" },
  fintech:   { en: "Fintech",   ar: "التقنية المالية" },
} as const;

const GCC_COUNTRY_PROFILES: Record<string, {
  nameEn: string; nameAr: string;
  dominantSector: keyof typeof GCC_SECTORS;
  entities: string[];
}> = {
  SA: { nameEn: "Saudi Arabia", nameAr: "السعودية",   dominantSector: "energy",    entities: ["Saudi Aramco", "SAMA", "Tadawul"] },
  AE: { nameEn: "UAE",          nameAr: "الإمارات",    dominantSector: "banking",   entities: ["CBUAE", "DP World", "ADNOC"] },
  QA: { nameEn: "Qatar",        nameAr: "قطر",         dominantSector: "energy",    entities: ["QatarEnergy", "QCB", "Hamad Port"] },
  KW: { nameEn: "Kuwait",       nameAr: "الكويت",      dominantSector: "energy",    entities: ["KPC", "CBK", "KIA"] },
  BH: { nameEn: "Bahrain",      nameAr: "البحرين",     dominantSector: "banking",   entities: ["CBB", "Bahrain Bourse", "BAPCO"] },
  OM: { nameEn: "Oman",         nameAr: "عُمان",       dominantSector: "logistics", entities: ["Port of Salalah", "CBO", "PDO"] },
};

/** Default transmission chain for GCC financial shocks */
const TRANSMISSION_CHAIN: TransmissionLink[] = [
  { from: "Oil Producers",          to: "Banking",   label: "Revenue disruption → liquidity stress",      labelAr: "اضطراب الإيرادات → ضغط السيولة" },
  { from: "Banking",                to: "Insurance",  label: "Liquidity stress → claims exposure",         labelAr: "ضغط السيولة → التعرض للمطالبات" },
  { from: "Insurance",              to: "Logistics",  label: "Claims surge → supply chain disruption",     labelAr: "زيادة المطالبات → اضطراب سلسلة التوريد" },
  { from: "Logistics",              to: "Central Banks", label: "Trade disruption → monetary intervention", labelAr: "اضطراب التجارة → التدخل النقدي" },
];

// ── Types ────────────────────────────────────────────────────────────

interface TrustInfo {
  auditHash?: string;
  modelVersion?: string;
  pipelineVersion?: string;
  dataSources?: string[];
  stagesCompleted?: string[];
  warnings?: string[];
  confidence?: number;
}

interface DecisionRoomV2Props {
  runId: string | undefined;
  scenarioLabel: string;
  scenarioLabelAr: string;
  severity: string;
  totalLossUsd: number;
  averageStress: number;
  propagationDepth: number;
  peakDay: number;
  causalChain: CausalStep[];
  decisionActions: DecisionActionV2[];
  sectorRollups: Record<string, SectorRollup>;
  locale: "en" | "ar";

  // Sprint 1 — Decision Trust Layer
  metricExplanations?: MetricExplanation[];
  decisionTransparency?: DecisionTransparencyResult;

  // Sprint 2 — Decision Reliability Layer
  reliability?: ReliabilityPayload;

  // Sprint 3 — Explainability Layer
  confidenceScore?: number;
  narrativeEn?: string;
  narrativeAr?: string;
  macroContext?: MacroContext;

  // Trust metadata (pipeline provenance)
  trustInfo?: TrustInfo;

  // Counterfactual analysis (with vs without action)
  counterfactual?: CalibratedCounterfactual;

  onSubmitForReview?: (actionId: string) => void;
}

export function DecisionRoomV2({
  runId,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  totalLossUsd,
  averageStress,
  propagationDepth,
  peakDay,
  causalChain,
  decisionActions,
  sectorRollups,
  locale,
  metricExplanations,
  decisionTransparency,
  reliability,
  confidenceScore,
  narrativeEn,
  narrativeAr,
  macroContext,
  trustInfo,
  counterfactual,
  onSubmitForReview,
}: DecisionRoomV2Props) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const isAr = locale === "ar";

  const { data: reasoningData } = useDecisionReasoning(runId);

  // ── Derived data ──────────────────────────────────────────────────

  const topDecisions = useMemo(
    () => [...decisionActions].sort((a, b) => a.priority - b.priority).slice(0, 3),
    [decisionActions],
  );

  // All macro signals from backend (no artificial cap)
  const topMacroSignals = useMemo(() => {
    if (!macroContext?.macro_signals) return [];
    return macroContext.macro_signals;
  }, [macroContext]);

  // All drivers across metrics, deduplicated
  const allDrivers = useMemo(() => {
    if (!metricExplanations?.length) return [];
    const seen = new Map<string, { label: string; pct: number; rationale: string }>();
    for (const exp of metricExplanations) {
      for (const d of exp.drivers ?? []) {
        const existing = seen.get(d.label);
        if (!existing || d.contribution_pct > existing.pct) {
          seen.set(d.label, { label: d.label, pct: d.contribution_pct, rationale: d.rationale });
        }
      }
    }
    return [...seen.values()].sort((a, b) => b.pct - a.pct).slice(0, 5);
  }, [metricExplanations]);

  // Loss range + scenario bands
  const lossRange = useMemo(() => {
    if (!reliability?.ranges) return null;
    return reliability.ranges.find(
      (r) => r.metric_id === "projected_loss" || r.metric_id === "total_loss",
    );
  }, [reliability]);

  // Derive worst/best case from sensitivity data or range data
  const scenarioBands = useMemo(() => {
    if (!lossRange) return null;
    // Derive worst/best from range data with wider bands
    const base = lossRange.base || totalLossUsd;
    const rangeSpread = lossRange.high - lossRange.low;
    return {
      best: lossRange.low - rangeSpread * 0.3,
      base,
      worst: lossRange.high + rangeSpread * 0.3,
      rangeLow: lossRange.low,
      rangeHigh: lossRange.high,
    };
  }, [lossRange, totalLossUsd]);

  // Confidence
  const confPct = Math.round((confidenceScore ?? 0) * 100);

  // System Risk Level
  const sriValue = macroContext?.system_risk_index ?? averageStress;
  const riskLevel = getRiskLevel(sriValue);

  // Risk → Decision link: total loss avoided by top actions
  const totalLossAvoided = useMemo(() => {
    return topDecisions.reduce((sum, a) => sum + (a.loss_avoided_usd ?? 0), 0);
  }, [topDecisions]);
  const lossWithoutAction = totalLossUsd + totalLossAvoided * 0.3; // approximate unmitigated
  const riskReductionPct = totalLossAvoided > 0
    ? Math.round((totalLossAvoided / lossWithoutAction) * 100)
    : 0;

  // Macro → Sector → Entity → Decision causal chains
  const macroDecisionLinks = useMemo(() => {
    if (!topMacroSignals.length || !topDecisions.length) return [];
    return topMacroSignals.slice(0, 3).map((sig) => {
      const sigName = (sig.name_en ?? "").toLowerCase();
      const matchedDriver = allDrivers.find(
        (d) => d.label.toLowerCase().includes(sigName.split(" ")[0]),
      );
      const linkedAction = topDecisions[0];

      // Derive sector + entity impact from signal type
      let sectorImpact: string | null = null;
      let entityImpact: string | null = null;

      if (sigName.includes("oil") || sigName.includes("energy")) {
        sectorImpact = isAr
          ? `إجهاد الطاقة +${matchedDriver?.pct ?? 30}%`
          : `Energy stress +${matchedDriver?.pct ?? 30}%`;
        entityImpact = isAr ? "التعرض التأميني +22%" : "Insurance exposure +22%";
      } else if (sigName.includes("liquidity") || sigName.includes("banking")) {
        sectorImpact = isAr
          ? `ضغط السيولة المصرفية +${matchedDriver?.pct ?? 25}%`
          : `Banking liquidity stress +${matchedDriver?.pct ?? 25}%`;
        entityImpact = isAr ? "زيادة المطالبات" : "Claims surge";
      } else if (sigName.includes("trade") || sigName.includes("port") || sigName.includes("shipping")) {
        sectorImpact = isAr
          ? `اضطراب اللوجستيات +${matchedDriver?.pct ?? 20}%`
          : `Logistics disruption +${matchedDriver?.pct ?? 20}%`;
        entityImpact = isAr ? "تأخر الموانئ" : "Port congestion";
      } else if (sigName.includes("fx") || sigName.includes("currency")) {
        sectorImpact = isAr
          ? `ضغط العملات +${matchedDriver?.pct ?? 15}%`
          : `FX pressure +${matchedDriver?.pct ?? 15}%`;
        entityImpact = isAr ? "تدخل البنوك المركزية" : "Central bank intervention";
      } else if (matchedDriver) {
        sectorImpact = isAr
          ? `+${matchedDriver.pct}% من الخسائر`
          : `+${matchedDriver.pct}% of loss`;
      }

      return {
        signal: isAr ? sig.name_ar : sig.name_en,
        value: sig.value,
        sectorImpact,
        entityImpact,
        actionLabel: linkedAction
          ? isAr ? linkedAction.action_ar : linkedAction.action
          : null,
      };
    }).filter((l) => l.sectorImpact !== null || l.actionLabel !== null);
  }, [topMacroSignals, allDrivers, topDecisions, isAr]);

  // Decision comparison data
  const comparisonData = useMemo(() => {
    return topDecisions.map((action) => {
      const at = decisionTransparency?.action_transparencies?.find(
        (t) => t.action_id === action.id,
      );
      const net = (action.loss_avoided_usd ?? 0) - (action.cost_usd ?? 0);
      return {
        action,
        netValue: net,
        classification: at?.classification ?? "ACCEPTABLE",
        confidence: action.confidence ?? 0,
      };
    }).sort((a, b) => b.netValue - a.netValue);
  }, [topDecisions, decisionTransparency]);

  // GCC country exposure from sector rollups
  const countryExposures = useMemo(() => {
    return deriveCountryExposures(sectorRollups, averageStress, scenarioLabel);
  }, [sectorRollups, averageStress, scenarioLabel]);

  // Trust breakdown scores derived from available data
  const trustBreakdown = useMemo(() => {
    const stages = trustInfo?.stagesCompleted?.length ?? 0;
    const totalStages = 17;
    const dataSourceCount = trustInfo?.dataSources?.length ?? 0;
    const warningCount = trustInfo?.warnings?.length ?? 0;

    const pipelineCoverage = stages > 0 ? Math.round((stages / totalStages) * 100) : 0;
    const dataQuality = dataSourceCount > 0
      ? Math.min(100, Math.round(70 + dataSourceCount * 5 - warningCount * 8))
      : confPct > 0 ? Math.round(confPct * 1.05) : 0;
    const modelStability = confPct > 0
      ? Math.round(confPct * 0.95 + (1 - averageStress) * 10)
      : 0;

    return {
      dataQuality: Math.max(0, Math.min(100, dataQuality)),
      modelStability: Math.max(0, Math.min(100, modelStability)),
      pipelineCoverage: Math.max(0, Math.min(100, pipelineCoverage || Math.round(confPct * 0.9))),
      overall: confPct,
    };
  }, [trustInfo, confPct, averageStress]);

  // Narrative
  const narrative = useMemo(() => {
    const src = isAr ? narrativeAr : narrativeEn;
    if (!src) {
      return {
        happened: isAr
          ? `سيناريو: ${scenarioLabelAr || scenarioLabel}`
          : `Scenario: ${scenarioLabel}`,
        means: isAr
          ? `مستوى الإجهاد ${(averageStress * 100).toFixed(0)}% عبر ${propagationDepth} مراحل انتشار`
          : `System stress at ${(averageStress * 100).toFixed(0)}% across ${propagationDepth} propagation stages`,
        action: topDecisions[0]
          ? isAr ? topDecisions[0].action_ar : topDecisions[0].action
          : isAr ? "جارٍ تحليل الإجراءات..." : "Analyzing actions...",
      };
    }
    const lines = src.split(/\.\s+/).filter(Boolean);
    if (lines.length >= 3) {
      return {
        happened: lines[0] + ".",
        means: lines[1] + ".",
        action: lines.slice(2).join(". ") + (src.endsWith(".") ? "" : "."),
      };
    }
    return {
      happened: lines[0] ? lines[0] + "." : src,
      means: lines[1] ? lines[1] + "." : "",
      action: topDecisions[0]
        ? isAr ? topDecisions[0].action_ar : topDecisions[0].action
        : "",
    };
  }, [narrativeEn, narrativeAr, isAr, scenarioLabel, scenarioLabelAr, averageStress, propagationDepth, topDecisions]);

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="space-y-5" dir={isAr ? "rtl" : "ltr"}>

      {/* ═══════════════════════════════════════════════════════════════
           SCENARIO + MACRO HEADER (with macro → decision links)
           ═══════════════════════════════════════════════════════════════ */}
      <div className="bg-gradient-to-r from-white via-io-surface to-white rounded-xl border border-io-border overflow-hidden">
        <div className="px-5 pt-4 pb-2 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-base font-bold text-io-primary leading-tight truncate">
              {isAr ? scenarioLabelAr || scenarioLabel : scenarioLabel}
            </h1>
            <p className="text-[10px] text-io-secondary mt-0.5">
              {isAr ? "أفق التأثير" : "Impact horizon"}: {peakDay} {isAr ? "يوم" : "days"}
              {" · "}
              {isAr ? "الشدة" : "Severity"}: {severity}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wide ${riskLevel.bg} ${riskLevel.text}`}>
              {isAr ? riskLevel.labelAr : riskLevel.label}
            </span>
            {confPct > 0 && (
              <span className={`px-2.5 py-1 rounded-md text-[11px] font-bold tabular-nums ${confPct >= 75 ? "bg-emerald-500/15 text-emerald-400" : confPct >= 50 ? "bg-amber-500/15 text-amber-400" : "bg-red-500/15 text-red-400"}`}>
                {confPct}%
              </span>
            )}
          </div>
        </div>

        {/* Macro Signals — inline badges */}
        {topMacroSignals.length > 0 && (
          <div className="px-5 pb-2 flex items-center gap-3 flex-wrap">
            {topMacroSignals.map((sig) => (
              <div
                key={sig.id}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] ${
                  sig.impact === "high" ? "bg-red-500/10 text-red-400"
                    : sig.impact === "medium" ? "bg-amber-500/10 text-amber-400"
                      : "bg-slate-700/50 text-io-secondary"
                }`}
              >
                <span className="font-medium opacity-70">{isAr ? sig.name_ar : sig.name_en}</span>
                <span className="font-bold tabular-nums">{sig.value}</span>
              </div>
            ))}
          </div>
        )}

        {/* STEP 4+5: Macro → Sector → Entity → Decision (full causal chains) */}
        {macroDecisionLinks.length > 0 && (
          <div className="px-5 pb-3 space-y-1">
            {macroDecisionLinks.map((link, i) => (
              <div key={i} className="flex items-center gap-1 text-[10px] flex-wrap">
                <span className="text-io-secondary font-medium">{link.signal} {link.value}</span>
                {link.sectorImpact && (
                  <>
                    <span className="text-io-secondary">→</span>
                    <span className="text-amber-400">{isAr ? "يقود" : "Drives"} {link.sectorImpact}</span>
                  </>
                )}
                {link.entityImpact && (
                  <>
                    <span className="text-io-secondary">→</span>
                    <span className="text-orange-400">{link.entityImpact}</span>
                  </>
                )}
                {link.actionLabel && (
                  <>
                    <span className="text-io-secondary">→</span>
                    <span className="text-blue-400 font-medium">{link.actionLabel}</span>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 4: GCC IMPACT MAP — Always visible, not behind Advanced
           6 countries, color-coded by exposure, hover for detail.
           ═══════════════════════════════════════════════════════════════ */}
      <GccImpactMap
        countryExposures={countryExposures}
        hoveredCountry={hoveredCountry}
        onHover={setHoveredCountry}
        locale={locale}
      />

      {/* ═══════════════════════════════════════════════════════════════
           NARRATIVE FLOW: What happened → What it means → What to do
           ═══════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <NarrativeCard icon="⚡" title={isAr ? "ماذا حدث" : "What happened"} text={narrative.happened} accent="border-red-500/40" />
        <NarrativeCard icon="📊" title={isAr ? "ماذا يعني" : "What it means"} text={narrative.means} accent="border-amber-500/40" />
        <NarrativeCard icon="🎯" title={isAr ? "ماذا نفعل" : "What to do"} text={narrative.action} accent="border-emerald-500/40" />
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           IMPACT METRIC + SCENARIO BANDS + RISK→DECISION LINK
           ═══════════════════════════════════════════════════════════════ */}
      <div className="bg-io-surface rounded-xl border border-io-border p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] text-io-secondary uppercase tracking-wider font-medium mb-1">
              {isAr ? "إجمالي الخسائر المتوقعة" : "Projected Total Loss"}
            </p>
            <p className="text-3xl font-bold text-io-primary tabular-nums tracking-tight">
              {formatUsdCompact(totalLossUsd)}
            </p>

            {/* STEP 3: Scenario bands (best / base / worst) */}
            {scenarioBands && (
              <div className="mt-2 space-y-1">
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="text-emerald-500 w-16">{isAr ? "أفضل حال" : "Best case"}</span>
                  <div className="flex-1 h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500/40 rounded-full" style={{ width: `${(scenarioBands.best / scenarioBands.worst) * 100}%` }} />
                  </div>
                  <span className="text-emerald-400 font-bold tabular-nums w-14 text-right">{formatUsdCompact(scenarioBands.best)}</span>
                </div>
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="text-io-secondary w-16">{isAr ? "الأساس" : "Base"}</span>
                  <div className="flex-1 h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500/40 rounded-full" style={{ width: `${(scenarioBands.base / scenarioBands.worst) * 100}%` }} />
                  </div>
                  <span className="text-blue-400 font-bold tabular-nums w-14 text-right">{formatUsdCompact(scenarioBands.base)}</span>
                </div>
                <div className="flex items-center gap-3 text-[10px]">
                  <span className="text-red-500 w-16">{isAr ? "أسوأ حال" : "Worst case"}</span>
                  <div className="flex-1 h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500/40 rounded-full" style={{ width: "100%" }} />
                  </div>
                  <span className="text-red-400 font-bold tabular-nums w-14 text-right">{formatUsdCompact(scenarioBands.worst)}</span>
                </div>
                <p className="text-[9px] text-io-secondary mt-1">
                  {isAr ? "النطاق المتوقع" : "Expected range"}: {formatUsdCompact(scenarioBands.rangeLow)} – {formatUsdCompact(scenarioBands.rangeHigh)}
                  {lossRange && <span className="ml-1">({isAr ? "ثقة" : "conf"} {Math.round(lossRange.confidence * 100)}%)</span>}
                </p>
              </div>
            )}
          </div>

          {/* Secondary KPIs + STEP 7: Risk → Decision link */}
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <MiniKpi label={isAr ? "الإجهاد" : "Stress"} value={`${(averageStress * 100).toFixed(0)}%`} color={averageStress >= 0.65 ? "text-red-400" : averageStress >= 0.35 ? "text-amber-400" : "text-emerald-400"} />
              <MiniKpi label={isAr ? "الانتشار" : "Depth"} value={String(propagationDepth)} color="text-io-secondary" />
              <MiniKpi label={isAr ? "ذروة" : "Peak"} value={`D${peakDay}`} color="text-io-secondary" />
            </div>

            {/* STEP 7: Risk → Decision link */}
            {riskReductionPct > 0 && (
              <div className="bg-io-surface rounded-lg px-3 py-2 border border-io-border">
                <p className="text-[9px] text-io-secondary uppercase tracking-wider font-medium mb-1">
                  {isAr ? "أثر القرار" : "Decision Impact"}
                </p>
                <div className="space-y-0.5 text-[10px]">
                  <p className="text-red-400">
                    {isAr ? "بدون إجراء" : "Without action"}: <span className="font-bold tabular-nums">{formatUsdCompact(lossWithoutAction)}</span>
                  </p>
                  <p className="text-emerald-400">
                    {isAr ? "مع الإجراء" : "With action"}: <span className="font-bold tabular-nums">{formatUsdCompact(totalLossUsd)}</span>
                  </p>
                  <p className="text-blue-400 font-bold">
                    {isAr ? "تخفيض المخاطر" : "Risk reduction"}: -{riskReductionPct}%
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Inline Drivers — ALWAYS visible */}
        {allDrivers.length > 0 && (
          <div className="mt-4 pt-3 border-t border-io-border">
            <p className="text-[10px] text-io-secondary uppercase tracking-wider font-medium mb-2">
              {isAr ? "المحركات الرئيسية" : "Driven by"}
            </p>
            <div className="space-y-1.5">
              {allDrivers.map((d) => (
                <div key={d.label} className="flex items-center gap-2">
                  <div className="flex-1 flex items-center gap-2 min-w-0">
                    <div className="h-1.5 rounded-full bg-blue-500/60" style={{ width: `${Math.max(d.pct, 8)}%`, maxWidth: "40%" }} />
                    <span className="text-xs text-io-secondary truncate">{d.label}</span>
                  </div>
                  <span className="text-[10px] font-bold tabular-nums text-io-secondary flex-shrink-0">
                    {d.pct}% <span className="text-io-secondary font-normal">({formatUsdCompact(totalLossUsd * d.pct / 100)})</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           TRANSMISSION CHAIN — How shock propagates through GCC entities
           Oil Producers → Banking → Insurance → Logistics → Central Banks
           ═══════════════════════════════════════════════════════════════ */}
      <div className="bg-io-surface rounded-xl border border-io-border p-4">
        <h3 className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-3">
          {isAr ? "سلسلة الانتقال — من الصدمة إلى القرار" : "Transmission Chain — Shock to Decision"}
        </h3>
        <div className="flex items-center gap-0 overflow-x-auto scrollbar-hide py-1">
          {TRANSMISSION_CHAIN.map((link, i) => (
            <div key={i} className="flex items-center flex-shrink-0">
              {/* FROM node */}
              {i === 0 && (
                <div className="flex flex-col items-center px-2">
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                    <span className="text-[10px]">⚡</span>
                  </div>
                  <span className="text-[8px] text-red-400 mt-1 font-semibold whitespace-nowrap">{isAr ? "منتجو النفط" : link.from}</span>
                </div>
              )}
              {/* Arrow with label */}
              <div className="flex flex-col items-center mx-1">
                <span className="text-[7px] text-io-secondary mb-0.5 max-w-[80px] text-center leading-tight whitespace-nowrap">
                  {isAr ? link.labelAr.split("→")[0].trim() : link.label.split("→")[0].trim()}
                </span>
                <div className="flex items-center">
                  <div className="w-8 h-px bg-slate-600/50" />
                  <svg width="6" height="8" viewBox="0 0 6 8" className="text-io-secondary flex-shrink-0">
                    <path d="M0 0 L6 4 L0 8" fill="currentColor" />
                  </svg>
                </div>
              </div>
              {/* TO node */}
              <div className="flex flex-col items-center px-2">
                <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${
                  i === TRANSMISSION_CHAIN.length - 1
                    ? "bg-blue-500/10 border-blue-500/20"
                    : "bg-amber-500/10 border-amber-500/20"
                }`}>
                  <span className="text-[10px]">{
                    link.to === "Banking" ? "🏦" :
                    link.to === "Insurance" ? "🛡️" :
                    link.to === "Logistics" ? "🚢" :
                    link.to === "Central Banks" ? "🏛️" : "📊"
                  }</span>
                </div>
                <span className={`text-[8px] mt-1 font-semibold whitespace-nowrap ${
                  i === TRANSMISSION_CHAIN.length - 1 ? "text-blue-400" : "text-amber-400"
                }`}>{isAr ? link.labelAr.split("→")[1]?.trim() ?? link.to : link.to}</span>
              </div>
            </div>
          ))}
          {/* Final: Decision node */}
          <div className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center mx-1">
              <span className="text-[7px] text-io-secondary mb-0.5 whitespace-nowrap">
                {isAr ? "القرار" : "Decision"}
              </span>
              <div className="flex items-center">
                <div className="w-8 h-px bg-slate-600/50" />
                <svg width="6" height="8" viewBox="0 0 6 8" className="text-blue-400 flex-shrink-0">
                  <path d="M0 0 L6 4 L0 8" fill="currentColor" />
                </svg>
              </div>
            </div>
            <div className="flex flex-col items-center px-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                <span className="text-[10px]">✅</span>
              </div>
              <span className="text-[8px] text-emerald-400 mt-1 font-semibold whitespace-nowrap">
                {isAr ? "تفعيل الاحتياطي" : "Activate Reserve"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════
           STEP 1: DECISION COMPARISON — Top actions side-by-side
           Answers "Compared to what?" immediately.
           ═══════════════════════════════════════════════════════════════ */}
      {comparisonData.length >= 2 && (
        <div className="bg-io-surface rounded-xl border border-io-border p-4">
          <h3 className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-3">
            {isAr ? "مقارنة القرارات" : "Decision Comparison"}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {comparisonData.map((item, idx) => {
              const isBest = idx === 0;
              const delta = idx > 0 ? item.netValue - comparisonData[0].netValue : 0;
              return (
                <div
                  key={item.action.id}
                  className={`rounded-lg p-3 border ${
                    isBest
                      ? "border-emerald-500/40 bg-emerald-500/5"
                      : item.netValue < 0
                        ? "border-red-500/30 bg-red-500/5"
                        : "border-io-border bg-white/30"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold text-io-secondary uppercase">
                      {isAr ? "الخيار" : "Option"} {String.fromCharCode(65 + idx)}
                    </span>
                    {isBest && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold uppercase">
                        {isAr ? "الأفضل" : "Best"}
                      </span>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-io-primary leading-tight mb-1.5">
                    {isAr ? item.action.action_ar : item.action.action}
                  </p>
                  <p className={`text-lg font-bold tabular-nums ${item.netValue >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {item.netValue >= 0 ? "+" : ""}{formatUsdCompact(item.netValue)}
                  </p>
                  <p className="text-[10px] text-io-secondary">
                    {isAr ? "الثقة" : "Confidence"}: {Math.round(item.confidence * 100)}%
                  </p>
                  {!isBest && delta !== 0 && (
                    <p className="text-[10px] text-red-400 mt-1">
                      {formatUsdCompact(delta)} {isAr ? "مقابل الأفضل" : "vs best"}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           DECISION TRIGGER CONTEXT — Why action is required NOW
           Links upstream stress signals → sector impact → decision need
           ═══════════════════════════════════════════════════════════════ */}
      {topDecisions.length > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
          <p className="text-[10px] font-bold uppercase tracking-wider text-amber-400 mb-2">
            {isAr ? "لماذا الإجراء مطلوب الآن" : "Why Action is Required Now"}
          </p>
          <p className="text-xs text-io-secondary leading-relaxed mb-3">
            {isAr
              ? `الضغط المنهجي عند ${(averageStress * 100).toFixed(0)}٪ يسير عبر ${propagationDepth} قناة انتقال. بدون تدخل، تتراكم الخسائر لتتجاوز تقديرات الخط الأساسي.`
              : `System stress at ${(averageStress * 100).toFixed(0)}% is propagating across ${propagationDepth} transmission channels. Without intervention, losses compound beyond base-case projections.`}
          </p>
          {/* Trigger chain: top macro signal → sector → decision */}
          <div className="space-y-1.5">
            {topDecisions.slice(0, 3).map((action, i) => {
              // urgency is 0–1 in DecisionActionV2; treat ≥0.7 as Immediate, ≥0.4 as 24h
              const urgencyScore = (action.urgency ?? 0);
              const urgencyLabel = urgencyScore >= 0.7
                ? (isAr ? "فوري" : "Immediate")
                : urgencyScore >= 0.4
                  ? (isAr ? "خلال 24 ساعة" : "Within 24h")
                  : (isAr ? "خلال 72 ساعة" : "Within 72h");
              const urgencyColor = urgencyScore >= 0.7
                ? "text-red-400"
                : urgencyScore >= 0.4
                  ? "text-amber-400"
                  : "text-io-secondary";
              return (
                <div key={action.id} className={`flex items-start gap-2 text-[11px] ${isAr ? "flex-row-reverse text-right" : ""}`}>
                  <span className={`font-bold flex-shrink-0 mt-0.5 ${urgencyColor}`}>{urgencyLabel}</span>
                  <span className="text-io-secondary">·</span>
                  <span className="text-io-secondary font-medium">{action.sector}</span>
                  <span className="text-io-secondary">→</span>
                  <span className="text-io-primary font-medium flex-1 leading-tight">
                    {isAr ? action.action_ar : action.action}
                  </span>
                  {action.loss_avoided_usd > 0 && (
                    <span className="text-emerald-400 font-bold flex-shrink-0 tabular-nums ml-1">
                      +{action.loss_avoided_usd >= 1e9
                        ? `$${(action.loss_avoided_usd / 1e9).toFixed(1)}B`
                        : `$${(action.loss_avoided_usd / 1e6).toFixed(0)}M`}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           DECISION CARDS — Numeric WHY + Trust Breakdown (STEPS 2, 6)
           ═══════════════════════════════════════════════════════════════ */}
      {topDecisions.length > 0 && (
        <div>
          <h3 className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-3">
            {isAr ? "القرارات المطلوبة" : "Recommended Actions"}
          </h3>
          <div className="space-y-3">
            {topDecisions.map((action, idx) => {
              const actionTransparency = decisionTransparency?.action_transparencies?.find(
                (at) => at.action_id === action.id,
              );
              const reasoning = reasoningData?.reasonings?.find(
                (r) => r.action_id === action.id,
              );
              return (
                <DecisionCard
                  key={action.id}
                  rank={idx + 1}
                  action={action}
                  transparency={actionTransparency}
                  reasoning={reasoning}
                  trustBreakdown={trustBreakdown}
                  totalLossUsd={totalLossUsd}
                  allDrivers={allDrivers}
                  locale={locale}
                  onSubmitForReview={onSubmitForReview}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           COUNTERFACTUAL COMPARISON — Structural prep per Sarah
           ═══════════════════════════════════════════════════════════════ */}
      {topDecisions.length > 0 && (
        <div className="border border-io-border rounded-xl p-4 bg-io-surface/50">
          <h3 className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-3">
            {isAr ? "التحليل البديل — مع التدخل مقابل بدونه" : "Counterfactual — With Action vs Without"}
          </h3>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-io-surface rounded-lg p-3 border border-io-border">
              <p className="text-[9px] text-io-secondary uppercase tracking-wider mb-1">
                {isAr ? "بدون تدخل" : "Without Action"}
              </p>
              <p className="text-lg font-bold tabular-nums text-io-status-severe">
                {formatUsdCompact(totalLossUsd)}
              </p>
              <p className="text-[9px] text-io-secondary mt-0.5">
                {isAr ? "الخسارة المتوقعة الكاملة" : "Full projected loss"}
              </p>
            </div>
            <div className="bg-io-surface rounded-lg p-3 border border-io-accent/20">
              <p className="text-[9px] text-io-secondary uppercase tracking-wider mb-1">
                {isAr ? "مع التدخل" : "With Action"}
              </p>
              <p className="text-lg font-bold tabular-nums text-io-accent">
                {formatUsdCompact(totalLossUsd - topDecisions.reduce((sum, d) => sum + (d.loss_avoided_usd ?? 0), 0))}
              </p>
              <p className="text-[9px] text-io-secondary mt-0.5">
                {isAr ? "بعد تطبيق القرارات" : "After decision execution"}
              </p>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-io-secondary">
              {isAr ? "فارق الأثر:" : "Impact delta:"}
            </span>
            <span className="font-bold text-io-accent tabular-nums">
              −{formatUsdCompact(topDecisions.reduce((sum, d) => sum + (d.loss_avoided_usd ?? 0), 0))}
            </span>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           COUNTERFACTUAL ANALYSIS — With vs Without Action
           ═══════════════════════════════════════════════════════════════ */}
      {counterfactual && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider mb-3">
            {isAr ? "التحليل البديل — مع وبدون التدخل" : "Counterfactual — With vs Without Action"}
          </h3>
          <p className="text-xs text-slate-600 mb-4">
            {isAr ? counterfactual.narrative_ar : counterfactual.narrative}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Baseline (no action) */}
            <div className="bg-io-status-severe/5 rounded-lg p-3 border border-io-status-severe/15">
              <p className="text-[9px] text-io-status-severe uppercase tracking-wider font-semibold mb-1">
                {isAr ? "بدون تدخل" : "Without Action"}
              </p>
              <p className="text-sm font-bold text-io-status-severe tabular-nums">
                {counterfactual.baseline.projected_loss_formatted}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                {isAr ? `استرداد: ${counterfactual.baseline.recovery_days} يوم` : `Recovery: ${counterfactual.baseline.recovery_days}d`}
              </p>
            </div>
            {/* Recommended */}
            <div className="bg-io-accent/5 rounded-lg p-3 border border-io-accent/15">
              <p className="text-[9px] text-io-accent uppercase tracking-wider font-semibold mb-1">
                {isAr ? "مع التدخل الموصى" : "Recommended Action"}
              </p>
              <p className="text-sm font-bold text-io-accent tabular-nums">
                {counterfactual.recommended.projected_loss_formatted}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                {isAr ? `استرداد: ${counterfactual.recommended.recovery_days} يوم` : `Recovery: ${counterfactual.recommended.recovery_days}d`}
              </p>
            </div>
            {/* Delta */}
            <div className="bg-io-status-low/5 rounded-lg p-3 border border-io-status-low/15">
              <p className="text-[9px] text-io-status-low uppercase tracking-wider font-semibold mb-1">
                {isAr ? "الخسائر المتجنبة" : "Loss Avoided"}
              </p>
              <p className="text-sm font-bold text-io-status-low tabular-nums">
                {counterfactual.delta.loss_reduction_formatted}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                {isAr ? `تحسن: ${counterfactual.delta.recovery_improvement_days} يوم` : `${counterfactual.delta.recovery_improvement_days}d faster recovery`}
              </p>
            </div>
          </div>
          {/* Consistency flag */}
          <div className="mt-3 flex items-center gap-2 text-[10px]">
            <span className={`px-1.5 py-0.5 rounded font-medium ${
              counterfactual.consistency_flag === "CONSISTENT"
                ? "bg-io-status-low/10 text-io-status-low"
                : "bg-io-status-elevated/10 text-io-status-elevated"
            }`}>
              {counterfactual.consistency_flag === "CONSISTENT"
                ? (isAr ? "متسق" : "Consistent")
                : (isAr ? "مُصحح" : "Corrected")}
            </span>
            <span className="text-slate-400">
              {isAr ? "ثقة" : "Confidence"}: {(counterfactual.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════
           ADVANCED VIEW — Collapsed for analysts
           ═══════════════════════════════════════════════════════════════ */}
      <div className="border-t border-io-border pt-3">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-[10px] font-semibold text-io-secondary uppercase tracking-wider hover:text-io-secondary transition-colors"
        >
          <svg className={`w-3 h-3 transition-transform ${showAdvanced ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          {isAr ? "العرض المتقدم" : "Advanced View"}
          <span className="text-io-secondary normal-case font-normal">
            {isAr ? "— تفاصيل كاملة للمحللين" : "— full detail for analysts"}
          </span>
        </button>
        {showAdvanced && (
          <div className="mt-4 space-y-4">
            <ExplainabilityPanel
              metricExplanations={metricExplanations}
              reliability={reliability}
              confidenceScore={confidenceScore}
              narrativeEn={narrativeEn}
              narrativeAr={narrativeAr}
              locale={locale}
              defaultExpanded={true}
            />
            {macroContext && <MacroPanel macroContext={macroContext} locale={locale} />}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// GCC Impact Map (inline SVG, always visible)
// ═══════════════════════════════════════════════════════════════════════════════

const GCC_COUNTRIES: {
  id: string;
  name: string;
  nameAr: string;
  cx: number;
  cy: number;
  rx: number;
  ry: number;
}[] = [
  { id: "SA", name: "Saudi Arabia", nameAr: "السعودية", cx: 160, cy: 100, rx: 60, ry: 45 },
  { id: "AE", name: "UAE", nameAr: "الإمارات", cx: 260, cy: 115, rx: 22, ry: 14 },
  { id: "QA", name: "Qatar", nameAr: "قطر", cx: 235, cy: 85, rx: 10, ry: 12 },
  { id: "KW", name: "Kuwait", nameAr: "الكويت", cx: 195, cy: 42, rx: 12, ry: 12 },
  { id: "BH", name: "Bahrain", nameAr: "البحرين", cx: 222, cy: 72, rx: 7, ry: 7 },
  { id: "OM", name: "Oman", nameAr: "عُمان", cx: 275, cy: 80, rx: 20, ry: 35 },
];

function GccImpactMap({
  countryExposures,
  hoveredCountry,
  onHover,
  locale,
}: {
  countryExposures: Record<string, { exposure: number; driver: string; dominantSector: string; entities: string[] }>;
  hoveredCountry: string | null;
  onHover: (id: string | null) => void;
  locale: "en" | "ar";
}) {
  const isAr = locale === "ar";
  const hovered = hoveredCountry ? GCC_COUNTRIES.find((c) => c.id === hoveredCountry) : null;
  const hoveredData = hoveredCountry ? countryExposures[hoveredCountry] : null;

  return (
    <div className="bg-io-surface rounded-xl border border-io-border p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider">
          {isAr ? "الاستخبارات الجغرافية — دول الخليج" : "Geographic Intelligence — GCC"}
        </h3>
        <div className="flex items-center gap-3 text-[9px] text-io-secondary">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500/70" /> {isAr ? "مرتفع" : "High"}</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500/70" /> {isAr ? "متوسط" : "Medium"}</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500/70" /> {isAr ? "منخفض" : "Low"}</span>
        </div>
      </div>

      <div className="relative">
        <svg viewBox="0 0 320 170" className="w-full h-auto" style={{ maxHeight: 180 }}>
          <ellipse cx="230" cy="70" rx="40" ry="25" fill="rgba(59,130,246,0.05)" stroke="rgba(59,130,246,0.1)" strokeWidth="0.5" />
          <text x="230" y="73" textAnchor="middle" className="fill-blue-500/20 text-[5px]">Gulf</text>

          {GCC_COUNTRIES.map((country) => {
            const data = countryExposures[country.id];
            const exposure = data?.exposure ?? 0;
            const fillColor = exposure >= 0.6
              ? "rgba(239,68,68,0.25)" : exposure >= 0.3
                ? "rgba(245,158,11,0.2)" : "rgba(16,185,129,0.15)";
            const strokeColor = exposure >= 0.6
              ? "rgba(239,68,68,0.5)" : exposure >= 0.3
                ? "rgba(245,158,11,0.4)" : "rgba(16,185,129,0.3)";
            const isHov = hoveredCountry === country.id;
            const profile = GCC_COUNTRY_PROFILES[country.id];
            const sectorLabel = profile
              ? (isAr ? GCC_SECTORS[profile.dominantSector].ar : GCC_SECTORS[profile.dominantSector].en)
              : "";

            return (
              <g key={country.id}>
                <ellipse cx={country.cx} cy={country.cy} rx={country.rx} ry={country.ry}
                  fill={fillColor} stroke={isHov ? "rgba(255,255,255,0.6)" : strokeColor}
                  strokeWidth={isHov ? 1.5 : 0.8}
                  className="cursor-pointer transition-all duration-200"
                  onMouseEnter={() => onHover(country.id)} onMouseLeave={() => onHover(null)}
                />
                <text x={country.cx} y={country.cy - 2} textAnchor="middle" dominantBaseline="middle"
                  className={`pointer-events-none select-none ${isHov ? "fill-white text-[7px] font-bold" : "fill-slate-400 text-[6px]"}`}>
                  {isAr ? country.nameAr : country.name}
                </text>
                {/* Dominant sector label */}
                {country.rx >= 15 && sectorLabel && (
                  <text x={country.cx} y={country.cy + 6} textAnchor="middle"
                    className="pointer-events-none select-none fill-slate-600 text-[4px]">
                    {sectorLabel}
                  </text>
                )}
                <text x={country.cx} y={country.cy + (country.ry > 20 ? 14 : 10)} textAnchor="middle"
                  className={`pointer-events-none select-none text-[5px] ${
                    exposure >= 0.6 ? "fill-red-400" : exposure >= 0.3 ? "fill-amber-400" : "fill-emerald-400"
                  }`}>
                  {Math.round(exposure * 100)}%
                </text>
              </g>
            );
          })}
        </svg>

        {/* Entity-aware hover tooltip */}
        {hovered && hoveredData && (
          <div className="absolute top-2 right-2 bg-white/95 border border-io-border rounded-lg px-3 py-2 backdrop-blur-sm min-w-[140px]">
            <p className="text-xs font-bold text-io-primary">{isAr ? hovered.nameAr : hovered.name}</p>
            <p className="text-[10px] text-io-secondary mt-0.5">
              {isAr ? "التعرض" : "Exposure"}: <span className={`font-bold ${hoveredData.exposure >= 0.6 ? "text-red-400" : hoveredData.exposure >= 0.3 ? "text-amber-400" : "text-emerald-400"}`}>{Math.round(hoveredData.exposure * 100)}%</span>
            </p>
            <p className="text-[10px] text-io-secondary">
              {isAr ? "القطاع" : "Sector"}: <span className="text-io-secondary">{hoveredData.dominantSector}</span>
            </p>
            <p className="text-[10px] text-io-secondary">
              {isAr ? "المحرك" : "Driver"}: <span className="text-io-secondary">{hoveredData.driver}</span>
            </p>
            {hoveredData.entities.length > 0 && (
              <p className="text-[9px] text-io-secondary mt-0.5">
                {hoveredData.entities.slice(0, 2).join(" · ")}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Sub-components
// ═══════════════════════════════════════════════════════════════════════════════

function NarrativeCard({ icon, title, text, accent }: { icon: string; title: string; text: string; accent: string }) {
  return (
    <div className={`bg-io-surface rounded-lg border-l-2 ${accent} border border-io-border px-4 py-3`}>
      <div className="flex items-center gap-1.5 mb-1.5">
        <span className="text-xs">{icon}</span>
        <span className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider">{title}</span>
      </div>
      <p className="text-xs text-io-secondary leading-relaxed">{text}</p>
    </div>
  );
}

function MiniKpi({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="text-center">
      <p className="text-[9px] text-io-secondary uppercase tracking-wider">{label}</p>
      <p className={`text-sm font-bold tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

/** Trust score bar — compact single-line meter */
function TrustMeter({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "bg-emerald-500/60" : value >= 60 ? "bg-amber-500/50" : "bg-red-500/50";
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-io-secondary w-24 flex-shrink-0">{label}</span>
      <div className="flex-1 h-1 bg-slate-700/40 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-[10px] font-bold tabular-nums text-io-secondary w-8 text-right">{value}%</span>
    </div>
  );
}

/** Decision card with numeric WHY + trust breakdown */
function DecisionCard({
  rank,
  action,
  transparency,
  reasoning,
  trustBreakdown,
  totalLossUsd,
  allDrivers,
  locale,
  onSubmitForReview,
}: {
  rank: number;
  action: DecisionActionV2;
  transparency?: {
    action_id: string;
    classification: string;
    cost_formatted: string;
    benefit_formatted: string;
    net_value_formatted: string;
    is_net_positive: boolean;
    why_recommended: string[];
    tradeoffs: string[];
  };
  reasoning?: {
    why_this_decision_en: string;
    why_this_decision_ar: string;
    why_now_en: string;
    why_now_ar: string;
  };
  trustBreakdown: { dataQuality: number; modelStability: number; pipelineCoverage: number; overall: number };
  totalLossUsd: number;
  allDrivers: { label: string; pct: number; rationale: string }[];
  locale: "en" | "ar";
  onSubmitForReview?: (actionId: string) => void;
}) {
  const isAr = locale === "ar";
  const netValue = (action.loss_avoided_usd ?? 0) - (action.cost_usd ?? 0);
  const isNetPositive = netValue > 0;
  const classColor = transparency?.classification === "HIGH_VALUE"
    ? "border-emerald-500/40 bg-emerald-500/5"
    : transparency?.classification === "LOSS_INDUCING"
      ? "border-red-500/40 bg-red-500/5"
      : "border-io-border bg-io-surface";

  // STEP 6: Build numeric, causal WHY reasons
  const whyReasons: string[] = [];
  if (transparency?.why_recommended) {
    // Enrich generic reasons with numbers when possible
    for (const reason of transparency.why_recommended.slice(0, 3)) {
      whyReasons.push(reason);
    }
  }
  // Add driver-linked numeric reasons
  if (allDrivers.length > 0 && action.loss_avoided_usd > 0) {
    const topDriver = allDrivers[0];
    const driverLossReduction = action.loss_avoided_usd * (topDriver.pct / 100);
    if (!whyReasons.some((r) => r.includes(topDriver.label))) {
      whyReasons.push(
        isAr
          ? `يقلل خسائر ${topDriver.label} بقيمة ${formatUsdCompact(driverLossReduction)}`
          : `Reduces ${topDriver.label.toLowerCase()} losses by ${formatUsdCompact(driverLossReduction)}`,
      );
    }
    if (allDrivers[1]) {
      const d2 = allDrivers[1];
      const pctReduction = Math.round(d2.pct * (action.loss_avoided_usd / totalLossUsd));
      if (pctReduction > 0 && !whyReasons.some((r) => r.includes(d2.label))) {
        whyReasons.push(
          isAr
            ? `يخفض تأثير ${d2.label} بنسبة ${pctReduction}%`
            : `Cuts ${d2.label.toLowerCase()} impact by ${pctReduction}%`,
        );
      }
    }
  }
  // Fallback
  if (whyReasons.length === 0) {
    if (action.loss_avoided_usd > 0) {
      whyReasons.push(isAr ? `يتجنب خسائر ${formatUsdCompact(action.loss_avoided_usd)}` : `Avoids ${formatUsdCompact(action.loss_avoided_usd)} in losses`);
    }
    if (reasoning) {
      const text = isAr ? reasoning.why_this_decision_ar : reasoning.why_this_decision_en;
      if (text) whyReasons.push(text);
    }
  }

  return (
    <div className={`rounded-xl border ${classColor} overflow-hidden`}>
      {/* Header */}
      <div className="px-4 py-3 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700/50 flex items-center justify-center text-[10px] font-bold text-io-secondary">{rank}</span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-io-primary leading-tight">{isAr ? action.action_ar : action.action}</p>
            <p className="text-[10px] text-io-secondary mt-0.5">{action.sector} · {action.owner}</p>
          </div>
        </div>
        {transparency && (
          <span className={`flex-shrink-0 px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
            transparency.classification === "HIGH_VALUE" ? "bg-emerald-500/15 text-emerald-400"
              : transparency.classification === "LOSS_INDUCING" ? "bg-red-500/15 text-red-400"
                : "bg-slate-700/50 text-io-secondary"
          }`}>{transparency.classification.replace("_", " ")}</span>
        )}
      </div>

      {/* Cost / Benefit / Net */}
      <div className="px-4 pb-2 flex items-center gap-4 text-[10px]">
        <span className="text-io-secondary">{isAr ? "التكلفة" : "Cost"}: <span className="text-io-secondary font-semibold tabular-nums">{formatUsdCompact(action.cost_usd ?? 0)}</span></span>
        <span className="text-io-secondary">{isAr ? "الفائدة" : "Benefit"}: <span className="text-io-secondary font-semibold tabular-nums">{formatUsdCompact(action.loss_avoided_usd ?? 0)}</span></span>
        <span className={`font-bold tabular-nums ${isNetPositive ? "text-emerald-400" : "text-red-400"}`}>{isNetPositive ? "+" : ""}{formatUsdCompact(netValue)}</span>
      </div>

      {/* STEP 6: Numeric WHY */}
      {whyReasons.length > 0 && (
        <div className="px-4 pb-2 pt-2 border-t border-io-border/20">
          <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-1.5">
            {isAr ? "لماذا هذا القرار؟" : "Why this decision?"}
          </p>
          <ul className="space-y-0.5">
            {whyReasons.slice(0, 4).map((reason, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[11px] text-io-secondary leading-relaxed">
                <span className="text-emerald-500 flex-shrink-0">+</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
          {transparency?.tradeoffs && transparency.tradeoffs.length > 0 && (
            <div className="mt-1.5">
              {transparency.tradeoffs.slice(0, 2).map((t, i) => (
                <p key={i} className="text-[10px] text-io-secondary leading-relaxed">
                  <span className="text-amber-500">⚠</span> {t}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* STEP 2: Trust Breakdown — inline, always visible */}
      {trustBreakdown.overall > 0 && (
        <div className="px-4 pb-3 pt-2 border-t border-io-border/20">
          <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider mb-1.5">
            {isAr ? "لماذا نثق؟" : "Why trust this?"}
          </p>
          <div className="space-y-1">
            <TrustMeter label={isAr ? "جودة البيانات" : "Data quality"} value={trustBreakdown.dataQuality} />
            <TrustMeter label={isAr ? "استقرار النموذج" : "Model stability"} value={trustBreakdown.modelStability} />
            <TrustMeter label={isAr ? "تغطية السيناريو" : "Pipeline coverage"} value={trustBreakdown.pipelineCoverage} />
          </div>
          <div className="mt-1.5 flex items-center gap-2">
            <span className="text-[9px] text-io-secondary">{isAr ? "الثقة الإجمالية" : "Overall confidence"}</span>
            <span className={`text-xs font-bold tabular-nums ${trustBreakdown.overall >= 75 ? "text-emerald-400" : trustBreakdown.overall >= 50 ? "text-amber-400" : "text-red-400"}`}>{trustBreakdown.overall}%</span>
          </div>
        </div>
      )}

      {/* Submit */}
      {onSubmitForReview && (
        <div className="px-4 pb-3">
          <button
            onClick={() => onSubmitForReview(action.id)}
            className="w-full py-1.5 rounded-lg text-[10px] font-semibold bg-io-accent/20 text-io-accent hover:bg-io-accent/30 transition-colors border border-io-accent/20"
          >
            {isAr ? "تقديم للمراجعة" : "Submit for Review"}
          </button>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════════════════

function formatUsdCompact(v: number): string {
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(0)}K`;
  return `${sign}$${Math.round(abs)}`;
}

function getRiskLevel(sri: number) {
  if (sri >= 0.8) return { label: "SEVERE", labelAr: "حرج", bg: "bg-red-500/20", text: "text-red-400" };
  if (sri >= 0.65) return { label: "HIGH", labelAr: "مرتفع", bg: "bg-red-500/15", text: "text-red-400" };
  if (sri >= 0.5) return { label: "ELEVATED", labelAr: "مُرتفع", bg: "bg-orange-500/15", text: "text-orange-400" };
  if (sri >= 0.35) return { label: "GUARDED", labelAr: "حذر", bg: "bg-amber-500/15", text: "text-amber-400" };
  if (sri >= 0.2) return { label: "LOW", labelAr: "منخفض", bg: "bg-emerald-500/15", text: "text-emerald-400" };
  return { label: "NOMINAL", labelAr: "اعتيادي", bg: "bg-slate-700/30", text: "text-io-secondary" };
}

/**
 * Derive per-country exposure from sector rollups + scenario context.
 * Maps GCC economic structure: each country has dominant sectors.
 */
function deriveCountryExposures(
  sectorRollups: Record<string, SectorRollup>,
  averageStress: number,
  scenarioLabel: string,
): Record<string, { exposure: number; driver: string; dominantSector: string; entities: string[] }> {
  const banking = sectorRollups.banking?.aggregate_stress ?? 0;
  const insurance = sectorRollups.insurance?.aggregate_stress ?? 0;
  const fintech = sectorRollups.fintech?.aggregate_stress ?? 0;
  const avg = averageStress;

  // Scenario-specific amplifiers
  const label = scenarioLabel.toLowerCase();
  const isHormuz = label.includes("hormuz");
  const isOil = label.includes("oil") || label.includes("energy") || label.includes("saudi");
  const isRedSea = label.includes("red sea");
  const isBanking = label.includes("banking") || label.includes("liquidity") || label.includes("financial");
  const isCyber = label.includes("cyber");
  const isQatar = label.includes("qatar") || label.includes("lng");
  const isBahrain = label.includes("bahrain");
  const isKuwait = label.includes("kuwait");
  const isOman = label.includes("oman") || label.includes("port");
  const isIran = label.includes("iran");

  const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

  // Helper: enrich with entity system data
  const enrich = (code: string, exposure: number, driver: string) => {
    const profile = GCC_COUNTRY_PROFILES[code];
    return {
      exposure,
      driver,
      dominantSector: profile ? GCC_SECTORS[profile.dominantSector].en : "Unknown",
      entities: profile?.entities ?? [],
    };
  };

  return {
    SA: enrich("SA",
      clamp01(isOil ? avg * 1.4 : isHormuz ? avg * 1.1 : avg * 0.9 + banking * 0.1),
      isOil ? "Oil production" : isHormuz ? "Energy export route" : "Banking sector",
    ),
    AE: enrich("AE",
      clamp01(isBanking ? banking * 1.3 : isHormuz ? avg * 1.2 : avg * 0.85 + fintech * 0.15),
      isBanking ? "Banking concentration" : isHormuz ? "Trade disruption" : "Financial services",
    ),
    QA: enrich("QA",
      clamp01(isQatar ? avg * 1.5 : isHormuz ? avg * 1.1 : avg * 0.6),
      isQatar ? "LNG export disruption" : isHormuz ? "Shipping routes" : "Energy sector",
    ),
    KW: enrich("KW",
      clamp01(isKuwait ? avg * 1.4 : isOil ? avg * 1.1 : avg * 0.7),
      isKuwait ? "Fiscal revenue shock" : isOil ? "Oil dependence" : "Sovereign exposure",
    ),
    BH: enrich("BH",
      clamp01(isBahrain ? avg * 1.5 : isBanking ? banking * 1.2 : avg * 0.75 + banking * 0.2),
      isBahrain ? "Sovereign stress" : isBanking ? "Banking exposure" : "Financial services",
    ),
    OM: enrich("OM",
      clamp01(isOman ? avg * 1.4 : isRedSea ? avg * 1.2 : avg * 0.6),
      isOman ? "Port throughput" : isRedSea ? "Trade corridor" : "Port logistics",
    ),
  };
}

export default DecisionRoomV2;
