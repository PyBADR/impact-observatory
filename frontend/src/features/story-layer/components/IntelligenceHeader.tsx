"use client";

/**
 * IntelligenceHeader — Repositioned product framing above the story flow
 *
 * Purpose: Frame the product as "Macro → Decision Intelligence"
 * NOT just "Financial Impact Intelligence"
 *
 * Shows: Platform name, macro-to-decision positioning, scenario context,
 *        one-line executive summary
 *
 * Design: Clean, compact, institutional header strip
 */

import React from "react";
import { Activity, ChevronRight } from "lucide-react";
import type { RunResult, Language } from "@/types/observatory";

// ── Executive summary generation ────────────────────────────────────

function deriveExecutiveSummary(result: RunResult, isAr: boolean): string {
  const scenario = result.scenario;
  const headline = result.headline;
  const totalLoss = headline?.total_loss_usd ?? 0;
  const critical = headline?.critical_count ?? 0;
  const elevated = headline?.elevated_count ?? 0;
  const avgStress = headline?.average_stress ?? 0;
  const severity = scenario?.severity ?? 0;

  // Format loss
  let lossStr: string;
  if (totalLoss >= 1e9) lossStr = `$${(totalLoss / 1e9).toFixed(1)}B`;
  else if (totalLoss >= 1e6) lossStr = `$${(totalLoss / 1e6).toFixed(0)}M`;
  else lossStr = `$${Math.round(totalLoss).toLocaleString()}`;

  if (isAr) {
    return `صدمة بشدة ${Math.round(severity * 100)}% تُعرّض ${lossStr} عبر ${critical + elevated} كيان متأثر. مستوى الإجهاد: ${Math.round(avgStress * 100)}%.`;
  }

  return `${Math.round(severity * 100)}% severity shock exposes ${lossStr} across ${critical + elevated} stressed entities. System stress at ${Math.round(avgStress * 100)}%.`;
}

// ── Story flow indicator ────────────────────────────────────────────

const STORY_STEPS = [
  { en: "Macro Shock", ar: "الصدمة" },
  { en: "Transmission", ar: "الانتقال" },
  { en: "Sector Impact", ar: "القطاعات" },
  { en: "Exposure", ar: "التعرض" },
  { en: "Decision", ar: "القرار" },
  { en: "Execution", ar: "التنفيذ" },
];

function StoryFlowIndicator({ isAr }: { isAr: boolean }) {
  return (
    <div className="flex items-center gap-0.5">
      {STORY_STEPS.map((step, i) => (
        <React.Fragment key={step.en}>
          <span className="text-[9px] text-slate-500 font-medium whitespace-nowrap">
            {isAr ? step.ar : step.en}
          </span>
          {i < STORY_STEPS.length - 1 && (
            <ChevronRight size={10} className="text-slate-700 flex-shrink-0" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

interface IntelligenceHeaderProps {
  result: RunResult;
  lang?: Language;
}

export function IntelligenceHeader({ result, lang = "en" }: IntelligenceHeaderProps) {
  const isAr = lang === "ar";
  const summary = deriveExecutiveSummary(result, isAr);

  return (
    <div className="w-full bg-[#0B0F1A] border-b border-white/[0.08]">
      <div className="flex items-center justify-between px-6 py-2.5">
        {/* Left: Product positioning */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-blue-400" />
            <span className="text-[11px] font-bold text-slate-300 tracking-tight">
              {isAr
                ? "الذكاء الاقتصادي الكلي → القرار"
                : "Macro → Decision Intelligence"}
            </span>
          </div>
          <div className="hidden md:block h-3.5 w-px bg-white/[0.08]" />
          <div className="hidden md:block">
            <StoryFlowIndicator isAr={isAr} />
          </div>
        </div>

        {/* Right: Executive summary */}
        <p className="text-[10px] text-slate-500 font-medium max-w-[400px] truncate hidden lg:block">
          {summary}
        </p>
      </div>
    </div>
  );
}
