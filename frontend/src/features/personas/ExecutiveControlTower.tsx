"use client";

/**
 * Impact Observatory — Executive Control Tower
 *
 * Unified executive narrative of value creation and risk.
 * Composes: decisions × outcomes × values → 5 panels.
 *
 * Hardening v2 fixes applied:
 *   A. Run-level values (no decision link) shown as labelled entries
 *   B. Confidence-weighted value marked "Derived (frontend)" with formula tooltip
 *   C. Multi-outcome/value per decision — latest used, counts shown
 *   D. Empty states explain WHY panel is empty
 *   E. Success rate denominator corrected (excludes PENDING_OBSERVATION)
 */

import React, { useState } from "react";
import type { Language, ValueClassification } from "@/types/observatory";
import { formatUSD } from "@/lib/format";
import type {
  ControlTowerViewModel,
  ControlTowerNarrativeEntry,
  ControlTowerRiskItem,
  ControlTowerRiskType,
} from "@/lib/persona-view-model";

// ─── Shared primitives ───────────────────────────────────────────────────────

const VALUE_CLASS_COLORS: Record<ValueClassification, string> = {
  HIGH_VALUE:     "bg-emerald-50 border-emerald-200 text-emerald-800",
  POSITIVE_VALUE: "bg-green-50 border-green-200 text-green-700",
  NEUTRAL:        "bg-gray-50 border-gray-200 text-gray-600",
  NEGATIVE_VALUE: "bg-orange-50 border-orange-200 text-orange-700",
  LOSS_INDUCING:  "bg-red-50 border-red-200 text-red-700",
};

const VALUE_CLASS_DOT: Record<ValueClassification, string> = {
  HIGH_VALUE:     "bg-emerald-500",
  POSITIVE_VALUE: "bg-green-500",
  NEUTRAL:        "bg-gray-400",
  NEGATIVE_VALUE: "bg-orange-500",
  LOSS_INDUCING:  "bg-red-600",
};

const RISK_TYPE_COLORS: Record<ControlTowerRiskType, string> = {
  LOSS_INDUCING:  "bg-red-50 border-red-200 text-red-800",
  NEGATIVE_VALUE: "bg-orange-50 border-orange-200 text-orange-700",
  LOW_CONFIDENCE: "bg-yellow-50 border-yellow-200 text-yellow-800",
};

const RISK_TYPE_LABEL: Record<ControlTowerRiskType, string> = {
  LOSS_INDUCING:  "LOSS INDUCING",
  NEGATIVE_VALUE: "NEGATIVE",
  LOW_CONFIDENCE: "LOW CONFIDENCE",
};

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="px-5 py-4 border-b border-io-border bg-io-bg/50 flex items-center justify-between">
      <h2 className="text-sm font-bold text-io-primary">{title}</h2>
      {sub && <span className="text-xs text-io-secondary">{sub}</span>}
    </div>
  );
}

/** FIX D: reason-aware empty state */
function EmptyState({ message, reason }: { message: string; reason?: string }) {
  return (
    <div className="px-5 py-6 text-center">
      <p className="text-sm text-io-secondary">{message}</p>
      {reason && <p className="text-xs text-io-secondary/70 mt-1">{reason}</p>}
    </div>
  );
}

// ─── 1. Value Overview ───────────────────────────────────────────────────────

function ValueOverviewPanel({ vm, lang }: { vm: ControlTowerViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const { valueOverview: vo } = vm;

  // FIX D: explain why panel is empty
  if (vo.totalValues === 0) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "نظرة عامة على القيمة" : "Value Overview"} />
        <EmptyState
          message={isAr ? "لا توجد قيم محسوبة بعد" : "No values computed yet"}
          reason={
            isAr
              ? "سجّل نتيجة مؤكدة ثم احسب قيمتها"
              : "Record a confirmed outcome and compute its value to populate this panel"
          }
        />
      </section>
    );
  }

  const classRows = [
    { key: "HIGH_VALUE" as ValueClassification,     label: isAr ? "قيمة عالية"   : "High Value"     },
    { key: "POSITIVE_VALUE" as ValueClassification, label: isAr ? "قيمة موجبة"  : "Positive"       },
    { key: "NEUTRAL" as ValueClassification,        label: isAr ? "محايد"         : "Neutral"        },
    { key: "NEGATIVE_VALUE" as ValueClassification, label: isAr ? "قيمة سالبة"  : "Negative"       },
    { key: "LOSS_INDUCING" as ValueClassification,  label: isAr ? "خسارة"         : "Loss Inducing"  },
  ] as const;

  const coverageOk = vo.valueCoveragePct === 100;

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <SectionHeader
        title={isAr ? "نظرة عامة على القيمة" : "Value Overview"}
        sub={`${vo.totalValues} ${isAr ? "قيمة" : "values"} · ${isAr ? "تغطية: " : "coverage: "}${vo.valueCoveragePct}%`}
      />
      <div className="px-5 py-4 space-y-4">
        {/* Coverage warning — value coverage metric (optional, low cost) */}
        {!coverageOk && (
          <div className="flex items-center gap-2 text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
            <span>⚠</span>
            <span>
              {vo.valueCoverage} {isAr ? "من" : "of"} {vo.totalValues}{" "}
              {isAr
                ? "قيم ظاهرة في السردية — الباقي بلا قرار مرتبط"
                : "values appear in narratives — remaining have no linked decision"}
            </span>
          </div>
        )}

        {/* Headline metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-io-bg border border-io-border rounded-lg px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "صافي القيمة" : "Total Net Value"}
            </p>
            <p className={`text-xl font-bold tabular-nums ${vo.totalNetValue >= 0 ? "text-emerald-700" : "text-red-700"}`}>
              {vo.totalNetValueFormatted}
            </p>
          </div>
          <div className="bg-io-bg border border-io-border rounded-lg px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "الخسارة المُتجنَّبة" : "Avoided Loss"}
            </p>
            <p className="text-xl font-bold tabular-nums text-io-primary">{vo.totalAvoidedLossFormatted}</p>
          </div>
          <div className="bg-io-bg border border-io-border rounded-lg px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1">
              {isAr ? "إجمالي التكاليف" : "Total Cost"}
            </p>
            <p className="text-xl font-bold tabular-nums text-io-primary">{vo.totalCostFormatted}</p>
          </div>

          {/* FIX B: confidence-weighted clearly labelled as derived + formula tooltip */}
          <div className="bg-io-bg border border-io-border rounded-lg px-4 py-3 relative group">
            <p className="text-xs font-medium uppercase tracking-wider text-io-secondary mb-1 flex items-center gap-1">
              {isAr ? "مُعدَّل بالثقة" : "Conf-Weighted"}
              <span
                className="cursor-help text-io-secondary/50 text-[10px] border border-io-border rounded px-0.5"
                title="Derived (frontend) — not persisted. Formula: Σ(net_value × confidence) / n"
              >
                ?
              </span>
            </p>
            <p className={`text-xl font-bold tabular-nums ${vo.confidenceWeightedValue >= 0 ? "text-emerald-700" : "text-red-700"}`}>
              {vo.confidenceWeightedValueFormatted}
            </p>
            <p className="text-[10px] text-io-secondary/60 mt-0.5">
              {isAr ? "مشتق · غير محفوظ" : "Derived · not persisted"}
            </p>
          </div>
        </div>

        {/* Classification distribution */}
        <div className="grid grid-cols-5 gap-2">
          {classRows.map(({ key, label }) => (
            <div key={key} className={`border rounded-lg px-2 py-2 text-center ${VALUE_CLASS_COLORS[key]}`}>
              <p className="text-lg font-bold tabular-nums">{vo.byClassification[key] ?? 0}</p>
              <p className="text-xs font-medium mt-0.5 leading-tight">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── 2. Decision Narrative ───────────────────────────────────────────────────

function NarrativeRow({ entry, lang }: { entry: ControlTowerNarrativeEntry; lang: Language }) {
  const [open, setOpen] = useState(false);
  const isAr = lang === "ar";
  const vcls = entry.valueClassification;
  // FIX A: run-level rows get a distinct visual treatment
  const isRunLevel = entry.entryType === "run";

  return (
    <div className="border-b border-io-border/50 last:border-0">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`w-full flex items-start gap-3 px-4 py-3 hover:bg-io-bg/50 transition-colors text-left ${isRunLevel ? "bg-blue-50/30" : ""}`}
      >
        <span
          className={`mt-1 shrink-0 w-2.5 h-2.5 rounded-full ${vcls ? VALUE_CLASS_DOT[vcls] : "bg-gray-300"}`}
        />
        <span className="flex-1 text-sm text-io-primary font-medium leading-snug">
          {entry.story}
        </span>
        <span className="shrink-0 flex items-center gap-2">
          {isRunLevel && (
            <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-700 border border-blue-200 rounded font-semibold uppercase tracking-wider">
              {isAr ? "مستوى التشغيل" : "RUN LEVEL"}
            </span>
          )}
          {entry.shouldRepeat && (
            <span className="text-xs px-1.5 py-0.5 bg-emerald-100 text-emerald-700 border border-emerald-200 rounded font-semibold">
              {isAr ? "يُنصح بتكراره" : "REPEAT"}
            </span>
          )}
          <span className="text-xs text-io-secondary">{open ? "▲" : "▼"}</span>
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 bg-io-bg/30">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            {entry.decisionType && (
              <div>
                <p className="text-io-secondary font-semibold mb-0.5">
                  {isAr ? "نوع القرار" : "Decision Type"}
                </p>
                <p className="font-mono text-io-primary">{entry.decisionType.replace(/_/g, " ")}</p>
              </div>
            )}
            <div>
              <p className="text-io-secondary font-semibold mb-0.5">
                {isAr ? "بواسطة" : entry.entryType === "run" ? "Computed By" : "Created By"}
              </p>
              <p className="text-io-primary">{entry.createdBy}</p>
            </div>
            <div>
              <p className="text-io-secondary font-semibold mb-0.5">
                {isAr ? "حالة النتيجة" : "Outcome Status"}
              </p>
              <p className="text-io-primary">{entry.outcomeStatus ?? "—"}</p>
            </div>
            <div>
              <p className="text-io-secondary font-semibold mb-0.5">
                {isAr ? "صافي القيمة" : "Net Value"}
              </p>
              <p className={`font-bold ${(entry.netValue ?? 0) >= 0 ? "text-emerald-700" : "text-red-700"}`}>
                {entry.netValueFormatted ?? "—"}
              </p>
            </div>
            {entry.confidenceScore != null && (
              <div>
                <p className="text-io-secondary font-semibold mb-0.5">
                  {isAr ? "درجة الثقة" : "Confidence"}
                </p>
                <p className="text-io-primary">{Math.round(entry.confidenceScore * 100)}%</p>
              </div>
            )}
            {entry.outcomeClassification && (
              <div>
                <p className="text-io-secondary font-semibold mb-0.5">
                  {isAr ? "تصنيف النتيجة" : "Outcome Class"}
                </p>
                <p className="text-io-primary">{entry.outcomeClassification.replace(/_/g, " ")}</p>
              </div>
            )}
            {entry.sourceRunId && (
              <div>
                <p className="text-io-secondary font-semibold mb-0.5">
                  {isAr ? "معرّف التشغيل" : "Run ID"}
                </p>
                <p className="font-mono text-io-secondary text-[11px] break-all">{entry.sourceRunId}</p>
              </div>
            )}
            {entry.decisionId && (
              <div className="col-span-2">
                <p className="text-io-secondary font-semibold mb-0.5">
                  {isAr ? "معرّف القرار" : "Decision ID"}
                </p>
                <p className="font-mono text-io-secondary text-[11px] break-all">{entry.decisionId}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DecisionNarrativePanel({ vm, lang }: { vm: ControlTowerViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const { narratives } = vm;

  const decisionCount = narratives.filter((n) => n.entryType === "decision").length;
  const runCount      = narratives.filter((n) => n.entryType === "run").length;
  const repeatCount   = narratives.filter((n) => n.shouldRepeat).length;

  // FIX D: explain why panel is empty
  if (narratives.length === 0) {
    const hasValues = vm.valueOverview.totalValues > 0;
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "سردية القرارات" : "Decision Narrative"} />
        <EmptyState
          message={isAr ? "لا توجد قرارات مسجّلة" : "No decisions recorded"}
          reason={
            hasValues
              ? isAr
                ? "القيم موجودة لكنها غير مرتبطة بقرارات — تظهر في مستوى التشغيل أعلاه"
                : "Values exist but are not linked to decisions — they appear as run-level entries"
              : isAr
              ? "ابدأ بإنشاء قرار مشغّل"
              : "Start by creating an operator decision"
          }
        />
      </section>
    );
  }

  const subParts: string[] = [
    `${decisionCount} ${isAr ? "قرار" : "decision"}`,
  ];
  if (runCount > 0) subParts.push(`${runCount} ${isAr ? "مستوى تشغيل" : "run-level"}`);
  if (repeatCount > 0) subParts.push(`${repeatCount} ${isAr ? "يُنصح بتكراره" : "repeat"}`);

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <SectionHeader
        title={isAr ? "سردية القرارات" : "Decision Narrative"}
        sub={subParts.join(" · ")}
      />
      <div>
        {narratives.map((entry, idx) => (
          <NarrativeRow
            key={entry.valueId ?? entry.decisionId ?? idx}
            entry={entry}
            lang={lang}
          />
        ))}
      </div>
    </section>
  );
}

// ─── 3. Value Drivers ────────────────────────────────────────────────────────

function ValueDriversPanel({ vm, lang }: { vm: ControlTowerViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const { valueDrivers } = vm;

  // FIX D: reason-aware empty state
  if (valueDrivers.length === 0) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "محرّكات القيمة" : "Value Drivers"} />
        <EmptyState
          message={isAr ? "لا توجد قيم لعرض المحرّكات" : "No values to show drivers"}
          reason={isAr ? "احسب قيمة واحدة على الأقل لتفعيل هذا القسم" : "Compute at least one value to activate this panel"}
        />
      </section>
    );
  }

  const maxAbsValue = Math.max(...valueDrivers.map((d) => Math.abs(d.totalNetValue)), 1);

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <SectionHeader
        title={isAr ? "محرّكات القيمة" : "Value Drivers"}
        sub={isAr ? "مجمَّع حسب نوع القرار" : "grouped by decision type"}
      />
      <div className="px-5 py-4 space-y-3">
        {valueDrivers.map((driver) => {
          const barPct   = Math.round((Math.abs(driver.totalNetValue) / maxAbsValue) * 100);
          const positive = driver.totalNetValue >= 0;
          // FIX A: label run-level group distinctly
          const isRunLevel = driver.groupKey === "RUN LEVEL";
          return (
            <div key={driver.groupKey}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className={`font-medium capitalize flex items-center gap-1.5 ${isRunLevel ? "text-blue-700" : "text-io-primary"}`}>
                  {driver.label}
                  {isRunLevel && (
                    <span className="text-[10px] px-1 py-0.5 bg-blue-100 text-blue-600 border border-blue-200 rounded uppercase tracking-wider font-semibold">
                      {isAr ? "بلا قرار" : "no decision"}
                    </span>
                  )}
                </span>
                <span className="flex items-center gap-3 text-xs text-io-secondary">
                  <span>{driver.valueCount} {isAr ? "قيمة" : "values"}</span>
                  <span>{isAr ? "ثقة: " : "conf: "}{Math.round(driver.avgConfidence * 100)}%</span>
                  <span className={`font-bold ${positive ? "text-emerald-700" : "text-red-700"}`}>
                    {driver.totalNetValueFormatted}
                  </span>
                </span>
              </div>
              <div className="h-2 bg-io-border rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${positive ? "bg-emerald-500" : "bg-red-500"}`}
                  style={{ width: `${barPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ─── 4. Outcome Performance ──────────────────────────────────────────────────

function OutcomePerformancePanel({ vm, lang }: { vm: ControlTowerViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const { outcomeStats: os } = vm;

  // FIX D: reason-aware empty state
  if (os.total === 0) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "أداء النتائج" : "Outcome Performance"} />
        <EmptyState
          message={isAr ? "لا توجد نتائج مسجّلة" : "No outcomes recorded yet"}
          reason={isAr ? "سجّل نتيجة قرار لتفعيل هذا القسم" : "Record a decision outcome to activate this panel"}
        />
      </section>
    );
  }

  // FIX E: use confirmedRate (excludes PENDING_OBSERVATION) and show pending separately
  const confirmedPct = Math.round(os.confirmedRate * 100);
  const avgResHours  = os.avgResolutionSeconds != null
    ? (os.avgResolutionSeconds / 3600).toFixed(1)
    : null;

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <SectionHeader
        title={isAr ? "أداء النتائج" : "Outcome Performance"}
        sub={`${os.total} ${isAr ? "إجمالي" : "total"}`}
      />
      <div className="px-5 py-4 space-y-4">
        {/* Confirmed Rate — FIX E: correct denominator, pending shown separately */}
        <div>
          <div className="flex items-center justify-between text-xs text-io-secondary mb-1.5">
            <span className="flex items-center gap-1">
              {isAr ? "معدل التأكيد" : "Confirmed Rate"}
              <span
                className="cursor-help text-io-secondary/50 text-[10px] border border-io-border rounded px-0.5"
                title={`confirmed / (total − pending) = ${os.confirmed} / ${os.validOutcomes}`}
              >
                ?
              </span>
            </span>
            <span className={`font-bold text-sm ${confirmedPct >= 50 ? "text-emerald-700" : "text-orange-700"}`}>
              {confirmedPct}%
            </span>
          </div>
          {/* Bar uses validOutcomes as base — pending shown as separate band */}
          <div className="h-2.5 bg-io-border rounded-full overflow-hidden flex">
            {os.confirmed > 0 && os.validOutcomes > 0 && (
              <div
                className="h-full bg-emerald-500"
                style={{ width: `${(os.confirmed / os.validOutcomes) * 100}%` }}
              />
            )}
            {os.disputed > 0 && os.validOutcomes > 0 && (
              <div
                className="h-full bg-orange-400"
                style={{ width: `${(os.disputed / os.validOutcomes) * 100}%` }}
              />
            )}
            {os.failed > 0 && os.validOutcomes > 0 && (
              <div
                className="h-full bg-red-500"
                style={{ width: `${(os.failed / os.validOutcomes) * 100}%` }}
              />
            )}
          </div>
          <div className="flex flex-wrap gap-4 text-xs text-io-secondary mt-1.5">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              {isAr ? "مؤكد" : "Confirmed"} {os.confirmed}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />
              {isAr ? "متنازع" : "Disputed"} {os.disputed}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
              {isAr ? "فاشل" : "Failed"} {os.failed}
            </span>
            {/* FIX E: pending shown outside bar, clearly separated */}
            <span className="flex items-center gap-1 opacity-60" title="Excluded from confirmed rate denominator">
              <span className="w-2 h-2 rounded-full bg-blue-300 inline-block" />
              {isAr ? "معلّق (مستثنى)" : "Pending (excl.)"} {os.pending}
            </span>
          </div>
        </div>

        {/* Supplementary metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
          {avgResHours && (
            <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2">
              <p className="text-io-secondary mb-0.5">{isAr ? "متوسط وقت الحل" : "Avg Resolution"}</p>
              <p className="font-bold text-io-primary">{avgResHours}h</p>
            </div>
          )}
          {os.totalExpectedValue > 0 && (
            <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2">
              <p className="text-io-secondary mb-0.5">{isAr ? "القيمة المتوقعة" : "Expected Value"}</p>
              <p className="font-bold text-io-primary">{formatUSD(os.totalExpectedValue)}</p>
            </div>
          )}
          {os.totalRealizedValue > 0 && (
            <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2">
              <p className="text-io-secondary mb-0.5">{isAr ? "القيمة المحققة" : "Realized Value"}</p>
              <p className="font-bold text-io-primary">{formatUSD(os.totalRealizedValue)}</p>
            </div>
          )}
          {os.realizedVsExpectedPct != null && (
            <div className="bg-io-bg border border-io-border rounded-lg px-3 py-2">
              <p className="text-io-secondary mb-0.5">{isAr ? "محقق %" : "Realized %"}</p>
              <p className={`font-bold ${os.realizedVsExpectedPct >= 100 ? "text-emerald-700" : "text-orange-700"}`}>
                {os.realizedVsExpectedPct.toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

// ─── 5. Risk & Loss Panel ────────────────────────────────────────────────────

function RiskRow({ item }: { item: ControlTowerRiskItem }) {
  return (
    <div className="px-4 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <span
          className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${RISK_TYPE_COLORS[item.riskType]}`}
        >
          {RISK_TYPE_LABEL[item.riskType]}
        </span>
        <span className="text-sm text-io-secondary truncate">{item.label}</span>
      </div>
      <span className="shrink-0 font-bold tabular-nums text-sm text-red-700">
        {item.netValueFormatted}
      </span>
    </div>
  );
}

function RiskLossPanel({ vm, lang }: { vm: ControlTowerViewModel; lang: Language }) {
  const isAr = lang === "ar";
  const { riskPanel } = vm;

  if (riskPanel.length === 0) {
    // FIX D: meaningful empty state — this one is intentionally positive
    const hasValues = vm.valueOverview.totalValues > 0;
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "المخاطر والخسائر" : "Risk & Loss"} />
        <div className="px-5 py-4">
          {hasValues ? (
            <div className="flex items-center gap-2 text-sm text-emerald-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
              {isAr
                ? "لا توجد قيم ضارة أو منخفضة الثقة — جميع القيم المحسوبة ضمن النطاق المقبول"
                : "No loss-inducing or low-confidence values — all computed values are within acceptable range"}
            </div>
          ) : (
            <p className="text-sm text-io-secondary">
              {isAr
                ? "لا توجد قيم محسوبة بعد — لا يمكن تقييم المخاطر"
                : "No values computed yet — risk assessment unavailable"}
            </p>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      <SectionHeader
        title={isAr ? "المخاطر والخسائر" : "Risk & Loss"}
        sub={`${riskPanel.length} ${isAr ? "عنصر" : "items"}`}
      />
      <div className="divide-y divide-io-border/50">
        {riskPanel.map((item, idx) => (
          <RiskRow key={item.valueId ?? idx} item={item} />
        ))}
      </div>
    </section>
  );
}

// ─── Main export ─────────────────────────────────────────────────────────────

interface ExecutiveControlTowerProps {
  vm: ControlTowerViewModel;
  lang: Language;
}

export function ExecutiveControlTower({ vm, lang }: ExecutiveControlTowerProps) {
  const isAr = lang === "ar";

  if (!vm.hasData) {
    return (
      <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
        <SectionHeader title={isAr ? "برج التحكم التنفيذي" : "Executive Control Tower"} />
        <EmptyState
          message={isAr ? "لا توجد بيانات" : "No data yet"}
          reason={
            isAr
              ? "ابدأ بتسجيل القرارات والنتائج لتفعيل برج التحكم"
              : "Start by recording decisions and outcomes to activate the control tower"
          }
        />
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <ValueOverviewPanel vm={vm} lang={lang} />
      <DecisionNarrativePanel vm={vm} lang={lang} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ValueDriversPanel vm={vm} lang={lang} />
        <OutcomePerformancePanel vm={vm} lang={lang} />
      </div>
      <RiskLossPanel vm={vm} lang={lang} />
    </div>
  );
}
