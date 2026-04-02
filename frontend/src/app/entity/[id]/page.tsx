"use client";

/**
 * Impact Observatory | مرصد الأثر — Entity Detail Page (Light Theme)
 */

import { useParams } from "next/navigation";
import { useAppStore } from "@/store/app-store";
import { useEntityDetail } from "@/hooks/use-api";
import type { RiskComponents } from "@/types";
import Link from "next/link";

const RISK_COMPONENT_LABELS: Record<keyof RiskComponents, { en: string; ar: string; abbr: string; color: string }> = {
  geopolitical: { en: "Geopolitical", ar: "جيوسياسي", abbr: "G", color: "#B91C1C" },
  proximity: { en: "Proximity", ar: "القرب", abbr: "P", color: "#B45309" },
  network: { en: "Network", ar: "الشبكة", abbr: "N", color: "#1D4ED8" },
  logistic: { en: "Logistic", ar: "لوجستي", abbr: "L", color: "#7C3AED" },
  temporal: { en: "Temporal", ar: "زمني", abbr: "T", color: "#0891B2" },
  uncertainty: { en: "Uncertainty", ar: "عدم اليقين", abbr: "U", color: "#475569" },
};

export default function EntityDetailPage() {
  const params = useParams();
  const entityId = params.id as string;
  const { language } = useAppStore();
  const isAr = language === "ar";

  const { data: entity, isLoading, isError, error } = useEntityDetail(entityId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-io-bg">
        <div className="w-12 h-12 border-2 border-io-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isError || !entity) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-io-bg">
        <p className="text-io-danger text-sm mb-4">
          {isError
            ? (error as Error).message
            : isAr
            ? "الكيان غير موجود"
            : "Entity not found"}
        </p>
        <Link
          href="/"
          className="text-xs text-io-accent underline"
        >
          {isAr ? "العودة للوحة المعلومات" : "Back to Dashboard"}
        </Link>
      </div>
    );
  }

  const riskComponents = entity.risk_score?.components;

  return (
    <div
      className="min-h-screen bg-io-bg"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-io-surface border-b border-io-border">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="text-xs text-io-secondary hover:text-io-primary transition"
          >
            ← {isAr ? "لوحة المعلومات" : "Dashboard"}
          </Link>
          <div>
            <h1 className="text-lg font-bold text-io-primary">
              {isAr ? entity.name_ar || entity.name : entity.name}
            </h1>
            <div className="flex items-center gap-2 text-[10px] text-io-secondary mt-0.5">
              <span className="px-1.5 py-0.5 bg-io-bg border border-io-border rounded">
                {entity.type}
              </span>
              <span className="px-1.5 py-0.5 bg-io-bg border border-io-border rounded">
                {entity.sector}
              </span>
              <span className="px-1.5 py-0.5 bg-io-bg border border-io-border rounded">
                {entity.region}
              </span>
            </div>
          </div>
        </div>
        <div className="text-[10px] text-io-secondary">{entityId}</div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Breakdown */}
        <div className="lg:col-span-2 bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-4">
            {isAr ? "تحليل المخاطر" : "Risk Breakdown"}
          </h2>

          {/* Composite Score */}
          <div className="flex items-center gap-4 mb-6">
            <div className="text-4xl font-bold" style={{
              color: entity.risk_score.composite_score >= 0.7
                ? "#B91C1C"
                : entity.risk_score.composite_score >= 0.4
                ? "#B45309"
                : "#15803D"
            }}>
              {(entity.risk_score.composite_score * 100).toFixed(1)}
            </div>
            <div>
              <div className="text-xs text-io-secondary">
                {isAr ? "المخاطر المركبة" : "Composite Risk Score"}
              </div>
              <div className="text-[10px] text-io-secondary">
                {isAr ? "الثقة" : "Confidence"}: {(entity.risk_score.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* 6-Component Bars */}
          {riskComponents && (
            <div className="space-y-3">
              {(Object.keys(RISK_COMPONENT_LABELS) as (keyof RiskComponents)[]).map(
                (key) => {
                  const meta = RISK_COMPONENT_LABELS[key];
                  const value = riskComponents[key] ?? 0;
                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between text-[10px] mb-1">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-5 h-5 rounded text-[9px] font-bold flex items-center justify-center"
                            style={{
                              backgroundColor: meta.color + "15",
                              color: meta.color,
                            }}
                          >
                            {meta.abbr}
                          </span>
                          <span className="text-io-primary">
                            {isAr ? meta.ar : meta.en}
                          </span>
                        </div>
                        <span
                          className="font-mono font-bold"
                          style={{ color: meta.color }}
                        >
                          {(value * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 bg-io-bg rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${value * 100}%`,
                            backgroundColor: meta.color,
                          }}
                        />
                      </div>
                    </div>
                  );
                }
              )}
            </div>
          )}

          {/* Explanation */}
          {entity.risk_score.explanation && (
            <div className="mt-6 p-3 bg-io-bg rounded-lg border border-io-border">
              <p className="text-xs text-io-secondary">
                {entity.risk_score.explanation.summary}
              </p>
              {entity.risk_score.explanation.top_drivers?.length > 0 && (
                <div className="mt-2 space-y-1">
                  {entity.risk_score.explanation.top_drivers.map((d, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between text-[10px]"
                    >
                      <span className="text-io-secondary">{d.factor}</span>
                      <span className="text-io-primary">
                        {(d.contribution * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Disruption Score */}
          <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
            <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-3">
              {isAr ? "درجة التعطل" : "Disruption Score"}
            </h2>
            <div
              className="text-3xl font-bold mb-3"
              style={{
                color:
                  entity.disruption_score.score >= 0.7
                    ? "#B91C1C"
                    : entity.disruption_score.score >= 0.4
                    ? "#B45309"
                    : "#15803D",
              }}
            >
              {(entity.disruption_score.score * 100).toFixed(1)}
            </div>
            {entity.disruption_score.factors.length > 0 && (
              <div className="space-y-1">
                {entity.disruption_score.factors.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between text-[10px]"
                  >
                    <span className="text-io-secondary">{f.name}</span>
                    <span className="text-io-primary font-mono">
                      {(f.contribution * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Insurance Exposure */}
          {entity.insurance_exposure && (
            <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
              <h2 className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-3">
                {isAr ? "التعرض التأميني" : "Insurance Exposure"}
              </h2>
              <div className="space-y-2 text-[10px]">
                <div className="flex justify-between">
                  <span className="text-io-secondary">
                    {isAr ? "القيمة المؤمنة" : "Total Insured Value"}
                  </span>
                  <span className="text-io-primary font-mono">
                    ${(entity.insurance_exposure.total_insured_value_usd / 1e6).toFixed(1)}M
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-io-secondary">
                    {isAr ? "أقصى خسارة محتملة" : "Probable Max Loss"}
                  </span>
                  <span className="text-io-primary font-mono">
                    ${(entity.insurance_exposure.probable_maximum_loss_usd / 1e6).toFixed(1)}M
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-io-secondary">
                    {isAr ? "فئة التعرض" : "Category"}
                  </span>
                  <span
                    className={`font-bold ${
                      entity.insurance_exposure.exposure_category === "critical"
                        ? "text-io-danger"
                        : entity.insurance_exposure.exposure_category === "high"
                        ? "text-io-warning"
                        : "text-io-secondary"
                    }`}
                  >
                    {entity.insurance_exposure.exposure_category}
                  </span>
                </div>
              </div>

              {/* Lines of Business */}
              {entity.insurance_exposure.lines_of_business.length > 0 && (
                <div className="mt-3 pt-3 border-t border-io-border">
                  <div className="text-[9px] text-io-secondary mb-2">
                    {isAr ? "فروع التأمين" : "Lines of Business"}
                  </div>
                  {entity.insurance_exposure.lines_of_business.map((lob, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between text-[10px] py-0.5"
                    >
                      <span className="text-io-secondary">{lob.line}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-io-secondary">
                          LR: {(lob.loss_ratio * 100).toFixed(0)}%
                        </span>
                        <span
                          className={
                            lob.trend === "deteriorating"
                              ? "text-io-danger"
                              : lob.trend === "improving"
                              ? "text-io-success"
                              : "text-io-secondary"
                          }
                        >
                          {lob.trend === "deteriorating"
                            ? "↑"
                            : lob.trend === "improving"
                            ? "↓"
                            : "→"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Connected Entities */}
          <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
            <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-3">
              {isAr ? "كيانات مرتبطة" : "Connected Entities"}
            </h2>
            {entity.connected_entities.length === 0 ? (
              <p className="text-[10px] text-io-secondary">
                {isAr ? "لا توجد اتصالات" : "No connections"}
              </p>
            ) : (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {entity.connected_entities.map((ce) => (
                  <Link
                    key={ce.id}
                    href={`/entity/${ce.id}`}
                    className="flex items-center justify-between text-[10px] py-1.5 border-b border-io-border hover:bg-io-bg rounded px-1 transition"
                  >
                    <div>
                      <span className="text-io-primary">{ce.name}</span>
                      <span className="text-io-secondary ml-2">
                        {ce.edge_type}
                      </span>
                    </div>
                    <span className="text-io-accent font-mono">
                      {ce.weight.toFixed(2)}
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Historical Risk Trend */}
          <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
            <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider mb-3">
              {isAr ? "اتجاه المخاطر" : "Risk Trend"}
            </h2>
            <RiskTrendPlaceholder score={entity.risk_score.composite_score} />
          </div>
        </div>
      </div>
    </div>
  );
}

/** Simple placeholder chart showing a synthetic risk trend */
function RiskTrendPlaceholder({ score }: { score: number }) {
  const points = Array.from({ length: 14 }, (_, i) => {
    const noise = (Math.sin(i * 1.3) * 0.1 + Math.cos(i * 0.7) * 0.05);
    return Math.max(0, Math.min(1, score + noise - 0.05));
  });
  points.push(score);

  const height = 60;
  const width = 240;
  const maxY = 1;
  const stepX = width / (points.length - 1);

  const pathD = points
    .map((p, i) => {
      const x = i * stepX;
      const y = height - (p / maxY) * height;
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ height: 60 }}
    >
      {/* Grid lines */}
      {[0.25, 0.5, 0.75].map((v) => (
        <line
          key={v}
          x1={0}
          y1={height - (v / maxY) * height}
          x2={width}
          y2={height - (v / maxY) * height}
          stroke="#E2E8F0"
          strokeWidth={0.5}
        />
      ))}

      {/* Trend line */}
      <path d={pathD} fill="none" stroke="#1D4ED8" strokeWidth={1.5} />

      {/* Current value dot */}
      <circle
        cx={(points.length - 1) * stepX}
        cy={height - (score / maxY) * height}
        r={3}
        fill={score >= 0.7 ? "#B91C1C" : score >= 0.4 ? "#B45309" : "#15803D"}
      />

      {/* Labels */}
      <text x={0} y={height + 10} fontSize={8} fill="#475569">
        14d ago
      </text>
      <text x={width} y={height + 10} fontSize={8} fill="#475569" textAnchor="end">
        Now
      </text>
    </svg>
  );
}
