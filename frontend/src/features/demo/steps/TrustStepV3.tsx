"use client";

import React from "react";
import type { DemoStepProps } from "../DemoStepRenderer";
import { demoScenario } from "../data/demo-scenario";
import {
  ShieldCheck,
  Clock,
  CheckCircle2,
} from "lucide-react";

function TrustKPI({
  icon,
  iconBg,
  label,
  value,
  valueColor,
  detail,
  smallValue = false,
}: {
  icon: React.ReactNode;
  iconBg: string;
  label: string;
  value: string;
  valueColor: string;
  detail: string;
  smallValue?: boolean;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm text-center">
      <div className="flex justify-center mb-2.5">
        <div
          className={`w-8 h-8 rounded-lg ${iconBg} border border-slate-100/50 flex items-center justify-center`}
        >
          {icon}
        </div>
      </div>
      <p className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-300 mb-1">
        {label}
      </p>
      <p className={`${smallValue ? "text-[15px]" : "text-2xl"} font-bold tabular-nums ${valueColor}`}>
        {value}
      </p>
      <p className="text-[9px] text-slate-400 mt-0.5">{detail}</p>
    </div>
  );
}

function SensitivityDot({ level }: { level: "HIGH" | "MEDIUM" | "LOW" }) {
  const colorMap = {
    HIGH: "bg-red-500",
    MEDIUM: "bg-amber-500",
    LOW: "bg-emerald-500",
  };
  return <div className={`w-2 h-2 rounded-full ${colorMap[level]}`} />;
}

export function TrustStepV3(_props: DemoStepProps) {
  const trust = demoScenario.trust;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-100 border border-slate-200">
            <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-slate-600">
              TRUST LAYER
            </span>
          </span>
        </div>
        <h2 className="text-3xl font-bold text-slate-900 mb-1">
          Sources & Assumptions
        </h2>
        <p className="text-sm text-slate-500">
          Every estimate is auditable. Every number is traceable.
        </p>
      </div>

      {/* Trust KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <TrustKPI
          icon={<ShieldCheck className="w-4 h-4 text-slate-700" />}
          iconBg="bg-slate-100"
          label="Confidence"
          value="84%"
          valueColor="text-slate-900"
          detail="Cross-signal consensus"
        />
        <TrustKPI
          icon={<Clock className="w-4 h-4 text-emerald-600" />}
          iconBg="bg-emerald-100"
          label="Data Freshness"
          value="<10m"
          valueColor="text-emerald-700"
          detail="Real-time validated"
        />
        <TrustKPI
          icon={<CheckCircle2 className="w-4 h-4 text-amber-600" />}
          iconBg="bg-amber-100"
          label="Validation"
          value="Multi"
          valueColor="text-amber-700"
          detail="Signal cross-check"
          smallValue
        />
      </div>

      {/* Data Sources & Assumptions */}
      <div className="grid grid-cols-2 gap-4">
        {/* Data Sources */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="mb-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500 mb-3">
              Data Sources
            </p>
          </div>
          <div className="space-y-2">
            {trust.dataSources.map((source, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-800">
                    {source}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Assumptions */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div className="mb-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500 mb-3">
              Key Assumptions
            </p>
          </div>
          <div className="space-y-2.5">
            {demoScenario.structuredAssumptions.map((assumption, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <div className="flex items-center gap-1 flex-shrink-0 pt-0.5">
                  <SensitivityDot level={assumption.sensitivity} />
                  <span
                    className={`text-[9px] font-bold uppercase tracking-[0.05em] ${
                      assumption.sensitivity === "HIGH"
                        ? "text-red-600"
                        : assumption.sensitivity === "MEDIUM"
                          ? "text-amber-600"
                          : "text-emerald-600"
                    }`}
                  >
                    {assumption.sensitivity}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-800">
                    {assumption.assumption}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-[9px] text-slate-500">
                      {assumption.source}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-xl p-4 text-white">
        <p className="text-sm font-semibold mb-3">
          This is not a dashboard. This is institutional macroeconomic intelligence.
        </p>
        <div className="flex items-center gap-2 mb-3 text-[9px] text-slate-300">
          <span>Assessment flow:</span>
          <span className="flex items-center gap-1">
            {trust.footerPipeline.split(" → ").map((stage, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span className="text-slate-500">→</span>}
                <span className="whitespace-nowrap">{stage}</span>
              </React.Fragment>
            ))}
          </span>
        </div>
        <div className="flex items-center justify-between text-[9px] text-slate-400">
          <span>Calibrated: {trust.lastCalibration}</span>
          <span>{trust.assessmentVersion}</span>
        </div>
      </div>
    </div>
  );
}
