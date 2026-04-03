"use client";

/**
 * Impact Observatory | مرصد الأثر — Scenario Lab (Light Theme)
 */

import { useState } from "react";
import { useAppStore } from "@/store/app-store";
import {
  useScenarioTemplates,
  useRunScenario,
  useSeverityProjection,
} from "@/hooks/use-api";
import type { ScenarioResult, ScenarioTemplate } from "@/types";
import Link from "next/link";

const TYPE_COLORS: Record<string, string> = {
  disruption: "border-io-danger text-io-danger",
  escalation: "border-io-warning text-io-warning",
  cascading: "border-purple-600 text-purple-600",
  hypothetical: "border-cyan-600 text-cyan-600",
};

const TIME_HORIZONS: { label: string; hours: 24 | 72 | 168 }[] = [
  { label: "24h", hours: 24 },
  { label: "72h", hours: 72 },
  { label: "7d", hours: 168 },
];

export default function ScenarioLabPage() {
  const { language, timeHorizon, setTimeHorizon } = useAppStore();
  const isAr = language === "ar";

  const { data: templatesData, isLoading: templatesLoading } = useScenarioTemplates();
  const templates = templatesData?.templates ?? [];

  const [selectedTemplate, setSelectedTemplate] = useState<ScenarioTemplate | null>(null);
  const [severity, setSeverity] = useState(0.6);
  const [result, setResult] = useState<ScenarioResult | null>(null);

  const runScenario = useRunScenario((data) => setResult(data));

  const { data: projectionData } = useSeverityProjection(
    result?.scenario_id ?? null,
    timeHorizon
  );

  const handleRun = () => {
    if (!selectedTemplate) return;
    runScenario.mutate({
      scenario_id: selectedTemplate.id,
      severity_override: severity,
      horizon_hours: timeHorizon,
    });
  };

  return (
    <div className="flex flex-col h-screen bg-io-bg" dir={isAr ? "rtl" : "ltr"}>
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-io-surface border-b border-io-border shrink-0">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="text-xs text-io-secondary hover:text-io-primary transition"
          >
            ← {isAr ? "لوحة المعلومات" : "Dashboard"}
          </Link>
          <span className="text-lg font-bold text-io-accent">
            {isAr ? "معمل المحاكاة" : "Scenario Lab"}
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Horizon Selector */}
          <div className="flex gap-1 bg-io-bg rounded p-0.5 border border-io-border">
            {TIME_HORIZONS.map((th) => (
              <button
                key={th.hours}
                onClick={() => setTimeHorizon(th.hours)}
                className={`px-2 py-1 text-[10px] rounded transition ${
                  timeHorizon === th.hours
                    ? "bg-io-accent text-white"
                    : "text-io-secondary hover:text-io-primary"
                }`}
              >
                {th.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — Template Browser */}
        <aside className="w-80 bg-io-surface border-r border-io-border overflow-y-auto p-4 shrink-0">
          <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-3">
            {isAr ? "قوالب المحاكاة" : "Scenario Templates"}
          </h2>

          {templatesLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-16 bg-io-bg rounded animate-pulse"
                />
              ))}
            </div>
          ) : templates.length === 0 ? (
            <p className="text-xs text-io-secondary">
              {isAr ? "لا توجد قوالب" : "No templates available"}
            </p>
          ) : (
            <div className="space-y-2">
              {templates.map((t) => {
                const isSelected = selectedTemplate?.id === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTemplate(t)}
                    className={`w-full text-left p-3 rounded-lg border text-xs transition ${
                      isSelected
                        ? "bg-io-accent/5 border-io-accent"
                        : "bg-io-bg border-io-border hover:border-io-accent/30"
                    }`}
                  >
                    <div className="font-medium text-io-primary mb-1">
                      {isAr ? t.title_ar : t.title}
                    </div>
                    {t.description && (
                      <div className="text-io-secondary mb-2 line-clamp-2">
                        {isAr ? t.description_ar || t.description : t.description}
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.5 border rounded text-[9px] ${
                          TYPE_COLORS[t.scenario_type] || "border-io-border text-io-secondary"
                        }`}
                      >
                        {t.scenario_type}
                      </span>
                      <span className="text-io-secondary">{t.horizon_hours}h</span>
                      <span className="text-io-secondary">
                        {t.shock_count} {isAr ? "صدمات" : "shocks"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </aside>

        {/* Center — Configuration & Run */}
        <div className="flex-1 flex flex-col overflow-y-auto p-6">
          {selectedTemplate ? (
            <>
              {/* Template Header */}
              <div className="mb-6">
                <h1 className="text-xl font-bold text-io-primary mb-2">
                  {isAr ? selectedTemplate.title_ar : selectedTemplate.title}
                </h1>
                {selectedTemplate.description && (
                  <p className="text-sm text-io-secondary">
                    {isAr
                      ? selectedTemplate.description_ar || selectedTemplate.description
                      : selectedTemplate.description}
                  </p>
                )}
              </div>

              {/* Severity Control */}
              <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm mb-6">
                <label className="block text-xs text-io-accent font-bold mb-2">
                  {isAr ? "مستوى الشدة" : "Severity Level"}:{" "}
                  <span className="text-io-primary">
                    {(severity * 100).toFixed(0)}%
                  </span>
                </label>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={severity}
                  onChange={(e) => setSeverity(parseFloat(e.target.value))}
                  className="w-full accent-io-accent"
                />
                <div className="flex justify-between text-[9px] text-io-secondary mt-1">
                  <span>{isAr ? "منخفض" : "Low"}</span>
                  <span>{isAr ? "متوسط" : "Moderate"}</span>
                  <span>{isAr ? "مرتفع" : "High"}</span>
                  <span>{isAr ? "كارثي" : "Catastrophic"}</span>
                </div>
              </div>

              {/* Shocks Preview */}
              {selectedTemplate.shocks && selectedTemplate.shocks.length > 0 && (
                <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm mb-6">
                  <h3 className="text-xs font-bold text-io-accent mb-3">
                    {isAr ? "الصدمات" : "Scenario Shocks"} ({selectedTemplate.shocks.length})
                  </h3>
                  <div className="space-y-2">
                    {selectedTemplate.shocks.map((shock, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 text-[11px] py-2 border-b border-io-border last:border-0"
                      >
                        <span className="w-5 h-5 rounded-full bg-io-danger/10 text-io-danger text-[9px] flex items-center justify-center font-bold">
                          {i + 1}
                        </span>
                        <div className="flex-1">
                          <div className="text-io-primary">
                            {isAr ? shock.description_ar || shock.description : shock.description}
                          </div>
                          <div className="text-io-secondary text-[9px] mt-0.5">
                            {shock.shock_type}
                            {shock.target_region && ` | ${shock.target_region}`}
                            {" | "}sev: {(shock.severity * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Run Button */}
              <button
                onClick={handleRun}
                disabled={runScenario.isPending}
                className={`w-full py-3 rounded-lg font-bold text-sm transition ${
                  runScenario.isPending
                    ? "bg-io-border text-io-secondary cursor-wait"
                    : "bg-io-accent text-white hover:bg-blue-700"
                }`}
              >
                {runScenario.isPending
                  ? isAr
                    ? "جاري المحاكاة..."
                    : "Running Simulation..."
                  : isAr
                  ? "تشغيل المحاكاة"
                  : "Run Scenario"}
              </button>

              {/* Error */}
              {runScenario.isError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-io-danger">
                  {runScenario.error.message}
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-io-secondary text-sm">
                {isAr
                  ? "اختر قالب محاكاة للبدء"
                  : "Select a scenario template to begin"}
              </p>
            </div>
          )}
        </div>

        {/* Right — Results */}
        <aside className="w-80 bg-io-surface border-l border-io-border overflow-y-auto p-4 shrink-0">
          <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-3">
            {isAr ? "النتائج" : "Results"}
          </h2>

          {!result ? (
            <p className="text-xs text-io-secondary">
              {isAr ? "اختر سيناريو وشغّل المحاكاة" : "Run a scenario to see results"}
            </p>
          ) : (
            <div className="space-y-4">
              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-2">
                <ResultCard
                  label={isAr ? "إجهاد النظام" : "System Stress"}
                  value={`${((result.system_stress_score ?? result.unified_risk_score ?? 0) * 100).toFixed(1)}%`}
                  color="danger"
                />
                <ResultCard
                  label={isAr ? "خسارة اقتصادية" : "Econ. Loss"}
                  value={`$${((result.headline?.total_loss_usd ?? result.total_economic_loss_usd ?? 0) / 1e9).toFixed(2)}B`}
                  color="warning"
                />
                <ResultCard
                  label={isAr ? "كيانات متأثرة" : "Impacted"}
                  value={String(result.impacts?.length || 0)}
                  color="accent"
                />
                <ResultCard
                  label={isAr ? "الأفق" : "Horizon"}
                  value={`${timeHorizon}h`}
                  color="accent"
                />
              </div>

              {/* Delta Risk — Top Impacted */}
              <div>
                <h3 className="text-xs font-bold text-io-accent mb-2">
                  {isAr ? "أعلى تغير في المخاطر" : "Top Risk Deltas"}
                </h3>
                <div className="space-y-1">
                  {result.impacts
                    ?.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
                    .slice(0, 10)
                    .map((imp) => (
                      <div
                        key={imp.entity_id}
                        className="flex items-center justify-between text-[10px] py-1 border-b border-io-border"
                      >
                        <div>
                          <Link
                            href={`/entity/${imp.entity_id}`}
                            className="text-io-primary hover:text-io-accent"
                          >
                            {imp.entity_id}
                          </Link>
                          <span className="text-io-secondary ml-2">
                            {imp.sector}
                          </span>
                        </div>
                        <span
                          className={
                            imp.delta > 0.3
                              ? "text-io-danger font-bold"
                              : imp.delta > 0.1
                              ? "text-io-warning"
                              : "text-io-secondary"
                          }
                        >
                          {imp.delta > 0 ? "+" : ""}
                          {(imp.delta * 100).toFixed(1)}pp
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              {/* Timeline Projection */}
              {projectionData && (
                <div>
                  <h3 className="text-xs font-bold text-io-accent mb-2">
                    {isAr ? "الإسقاط الزمني" : "Timeline Projection"}
                  </h3>
                  <div className="space-y-1">
                    {projectionData.projections.map((p) => (
                      <div
                        key={p.hour}
                        className="flex items-center gap-2 text-[10px]"
                      >
                        <span className="text-io-secondary w-8">
                          {p.hour}h
                        </span>
                        <div className="flex-1 bg-io-bg rounded-full h-2 border border-io-border">
                          <div
                            className="h-full rounded-full bg-io-danger transition-all"
                            style={{
                              width: `${Math.min(p.system_stress * 100, 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-io-primary w-12 text-right">
                          {(p.system_stress * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {result.recommendations && result.recommendations.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-io-accent mb-2">
                    {isAr ? "التوصيات" : "Recommendations"}
                  </h3>
                  <div className="space-y-1">
                    {result.recommendations.map((rec, i) => (
                      <div
                        key={i}
                        className="text-[10px] text-io-secondary p-2 bg-io-bg rounded border-l-2 border-io-accent"
                      >
                        {rec}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Narrative */}
              {result.narrative && (
                <div>
                  <h3 className="text-xs font-bold text-io-accent mb-2">
                    {isAr ? "السرد" : "Narrative"}
                  </h3>
                  <pre className="text-[10px] text-io-secondary whitespace-pre-wrap font-mono bg-io-bg p-2 rounded border border-io-border">
                    {result.narrative}
                  </pre>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

function ResultCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "danger" | "warning" | "success" | "accent";
}) {
  const colorMap = {
    danger: "text-io-danger border-io-danger/30",
    warning: "text-io-warning border-io-warning/30",
    success: "text-io-success border-io-success/30",
    accent: "text-io-accent border-io-accent/30",
  };

  return (
    <div className={`p-2 rounded-lg bg-io-bg border ${colorMap[color]}`}>
      <div className="text-[9px] text-io-secondary">{label}</div>
      <div className={`text-sm font-bold ${colorMap[color].split(" ")[0]}`}>
        {value}
      </div>
    </div>
  );
}
