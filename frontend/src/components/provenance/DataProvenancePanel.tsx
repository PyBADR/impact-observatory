"use client";

/**
 * DataProvenancePanel — Full data provenance detail (Level 3 depth).
 *
 * Shows everything about where a metric's data comes from:
 * model type, formula, historical analog, calibration source,
 * calibration period, freshness assessment, and relevance score.
 */

import type { DataBasis } from "@/types/provenance";

interface DataProvenancePanelProps {
  basis: DataBasis;
  locale: "en" | "ar";
  onClose?: () => void;
}

export function DataProvenancePanel({
  basis,
  locale,
  onClose,
}: DataProvenancePanelProps) {
  const isAr = locale === "ar";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-lg p-5 space-y-4 max-w-md">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800">
            {isAr ? basis.metric_name_ar : basis.metric_name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
          </h3>
          <p className="text-[10px] text-slate-400 mt-0.5 uppercase tracking-wider">
            {isAr ? "أساس البيانات والمصدر" : "Data Basis & Source"}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-sm"
            aria-label="Close"
          >
            ✕
          </button>
        )}
      </div>

      {/* Model */}
      <Section title={isAr ? "النموذج" : "Model"}>
        <div className="flex items-center gap-2">
          <ModelBadge type={basis.model_type} />
          <span className="text-xs text-slate-600">
            {basis.model_type === "deterministic_formula" && (isAr ? "صيغة حتمية" : "Deterministic Formula")}
            {basis.model_type === "network_simulation" && (isAr ? "محاكاة شبكية" : "Network Simulation")}
            {basis.model_type === "derived" && (isAr ? "مشتق" : "Derived from other metrics")}
            {basis.model_type === "unknown" && (isAr ? "غير معروف" : "Unknown")}
          </span>
        </div>
      </Section>

      {/* Historical Reference */}
      {basis.analog_event && (
        <Section title={isAr ? "المرجع التاريخي" : "Historical Reference"}>
          <p className="text-xs text-slate-700 font-medium">{basis.analog_event}</p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {isAr ? "الفترة" : "Period"}: {basis.analog_period}
          </p>
          {basis.analog_relevance > 0 && (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="text-[10px] text-slate-400">
                {isAr ? "الملاءمة" : "Relevance"}:
              </span>
              <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden max-w-[120px]">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${Math.round(basis.analog_relevance * 100)}%` }}
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-600 tabular-nums">
                {Math.round(basis.analog_relevance * 100)}%
              </span>
            </div>
          )}
        </Section>
      )}

      {/* Calibration */}
      <Section title={isAr ? "المعايرة" : "Calibration"}>
        <p className="text-xs text-slate-600 leading-relaxed">
          {isAr ? basis.calibration_basis_ar : basis.calibration_basis_en}
        </p>
      </Section>

      {/* Freshness */}
      <Section title={isAr ? "الحداثة" : "Freshness"}>
        <div className="flex items-center gap-2">
          <FreshnessIndicator flag={basis.freshness_flag} />
          <span className="text-xs text-slate-600 uppercase font-medium">
            {basis.freshness_flag}
          </span>
        </div>
        <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">
          {isAr ? basis.freshness_detail_ar : basis.freshness_detail_en}
        </p>
        {basis.freshness_weak && (
          <div className="mt-1.5 px-2 py-1 bg-amber-50 border border-amber-200 rounded text-[10px] text-amber-700">
            ⚠ {isAr
              ? "معايرة محدودة — تعامل مع المخرجات كمؤشرات وليس قيم نهائية"
              : "Limited calibration — treat outputs as indicative, not definitive"}
          </div>
        )}
      </Section>
    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
        {title}
      </h4>
      {children}
    </div>
  );
}

function ModelBadge({ type }: { type: string }) {
  const colors: Record<string, string> = {
    deterministic_formula: "bg-blue-100 text-blue-700",
    network_simulation: "bg-indigo-100 text-indigo-700",
    derived: "bg-slate-100 text-slate-600",
  };
  const style = colors[type] ?? "bg-slate-100 text-slate-500";
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${style}`}>
      {type === "deterministic_formula" ? "FORMULA" : type === "network_simulation" ? "SIMULATION" : "DERIVED"}
    </span>
  );
}

function FreshnessIndicator({ flag }: { flag: string }) {
  const colors: Record<string, string> = {
    CALIBRATED: "bg-emerald-500",
    SIMULATED: "bg-blue-500",
    DERIVED: "bg-slate-400",
    PARAMETRIC: "bg-amber-500",
  };
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${colors[flag] ?? "bg-slate-400"}`} />
  );
}

export default DataProvenancePanel;
