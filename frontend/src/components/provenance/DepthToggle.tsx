"use client";

/**
 * DepthToggle — Progressive disclosure level selector.
 *
 * Three levels:
 *   Level 1: Summary (default) — executive snapshot only
 *   Level 2: Factors — breakdown + range + decision cards
 *   Level 3: Full — provenance + formula + data basis + audit
 */

interface DepthToggleProps {
  level: 1 | 2 | 3;
  onChange: (level: 1 | 2 | 3) => void;
  locale: "en" | "ar";
}

const LEVELS: Array<{ value: 1 | 2 | 3; labelEn: string; labelAr: string }> = [
  { value: 1, labelEn: "Summary", labelAr: "ملخص" },
  { value: 2, labelEn: "Factors", labelAr: "العوامل" },
  { value: 3, labelEn: "Full Detail", labelAr: "التفاصيل الكاملة" },
];

export function DepthToggle({ level, onChange, locale }: DepthToggleProps) {
  const isAr = locale === "ar";

  return (
    <div className="inline-flex items-center bg-slate-100 rounded-lg p-0.5 gap-0.5">
      {LEVELS.map((l) => (
        <button
          key={l.value}
          onClick={() => onChange(l.value)}
          className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
            level === l.value
              ? "bg-white text-slate-800 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          {isAr ? l.labelAr : l.labelEn}
        </button>
      ))}
    </div>
  );
}

export default DepthToggle;
