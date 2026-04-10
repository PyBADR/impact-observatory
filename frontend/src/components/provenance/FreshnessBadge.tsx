"use client";

/**
 * FreshnessBadge — Inline data provenance indicator.
 *
 * Small badge next to any metric:
 *   ◉ CALIBRATED  (green — strong historical basis)
 *   ◎ SIMULATED   (blue — network model output)
 *   ◉ DERIVED     (gray — computed from other metrics)
 *   ⚠ PARAMETRIC  (amber — weak basis, treat as indicative)
 *
 * Click expands to full DataProvenancePanel.
 */

import type { DataBasis, FreshnessFlag } from "@/types/provenance";

const FLAG_STYLES: Record<FreshnessFlag, {
  icon: string;
  bg: string;
  text: string;
  border: string;
}> = {
  CALIBRATED: {
    icon: "◉",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-200",
  },
  SIMULATED: {
    icon: "◎",
    bg: "bg-blue-50",
    text: "text-blue-700",
    border: "border-blue-200",
  },
  DERIVED: {
    icon: "◉",
    bg: "bg-slate-50",
    text: "text-slate-500",
    border: "border-slate-200",
  },
  PARAMETRIC: {
    icon: "⚠",
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
  },
};

interface FreshnessBadgeProps {
  basis: DataBasis;
  locale: "en" | "ar";
  onClick?: () => void;
  showLabel?: boolean;
}

export function FreshnessBadge({
  basis,
  locale,
  onClick,
  showLabel = false,
}: FreshnessBadgeProps) {
  const flag = basis.freshness_flag as FreshnessFlag;
  const style = FLAG_STYLES[flag] ?? FLAG_STYLES.PARAMETRIC;

  const label = showLabel
    ? flag
    : basis.analog_event
      ? `${flag} · ${basis.analog_event}`
      : flag;

  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border transition-colors hover:opacity-80 ${style.bg} ${style.text} ${style.border}`}
      title={locale === "ar" ? basis.freshness_detail_ar : basis.freshness_detail_en}
    >
      <span>{style.icon}</span>
      {showLabel && <span className="uppercase tracking-wider">{label}</span>}
      {basis.freshness_weak && <span className="text-amber-600">⚠</span>}
    </button>
  );
}

export default FreshnessBadge;
