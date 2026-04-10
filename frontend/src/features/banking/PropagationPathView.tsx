"use client";

import type { PropagationContract, InterventionSpec } from "@/types/banking-intelligence";

const MECHANISM_COLORS: Record<string, string> = {
  liquidity_channel: "bg-blue-900 text-blue-300",
  credit_channel: "bg-purple-900 text-purple-300",
  payment_channel: "bg-emerald-900 text-emerald-300",
  confidence_channel: "bg-amber-900 text-amber-300",
  operational_channel: "bg-orange-900 text-orange-300",
  regulatory_channel: "bg-rose-900 text-rose-300",
  market_channel: "bg-cyan-900 text-cyan-300",
  contagion: "bg-red-900 text-red-300",
};

function InterventionDetail({ spec }: { spec: InterventionSpec }) {
  const readinessColor =
    spec.readiness === "ready" ? "text-emerald-400" :
    spec.readiness === "requires_approval" ? "text-amber-400" :
    "text-red-400";

  return (
    <div className="mt-2 pl-3 border-l-2 border-emerald-700 space-y-1 text-xs">
      <div className="flex items-center gap-2">
        <span className="text-zinc-500">Intervention:</span>
        <span className="text-zinc-200 capitalize">{spec.intervention_type.replace(/_/g, " ")}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-zinc-500">Readiness:</span>
        <span className={`capitalize font-medium ${readinessColor}`}>{spec.readiness.replace(/_/g, " ")}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-zinc-500">Effectiveness:</span>
        <span className="text-emerald-400 font-mono">{(spec.effectiveness_estimate * 100).toFixed(0)}%</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-zinc-500">Activation:</span>
        <span className="text-zinc-300 font-mono">{spec.estimated_activation_hours}h</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-zinc-500">Owner:</span>
        <span className="text-zinc-300 font-mono text-[10px]">{spec.owner_entity_id}</span>
      </div>
    </div>
  );
}

function PropagationCard({ prop }: { prop: PropagationContract }) {
  const mechClass = MECHANISM_COLORS[prop.transfer_mechanism] || "bg-zinc-800 text-zinc-300";
  const bestIntervention = prop.interventions?.find(
    (i) => i.readiness === "ready" || i.readiness === "requires_approval"
  );

  return (
    <div className={`rounded-lg border ${prop.breakable_point ? "border-emerald-700" : "border-zinc-700"} bg-zinc-900 p-4`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="font-mono text-xs text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">{prop.from_entity_id}</span>
        <svg width="20" height="12" viewBox="0 0 20 12" className="text-zinc-500 flex-shrink-0">
          <path d="M0 6h16M12 1l5 5-5 5" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
        <span className="font-mono text-xs text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">{prop.to_entity_id}</span>
      </div>

      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${mechClass}`}>
          {prop.transfer_mechanism.replace(/_/g, " ")}
        </span>
        {prop.breakable_point ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900 text-emerald-300">BREAKABLE</span>
        ) : (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900 text-red-300">UNBREAKABLE</span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs mb-2">
        <div>
          <span className="text-zinc-500">Delay</span>
          <p className="text-zinc-200 font-mono">{prop.delay_hours}h</p>
        </div>
        <div>
          <span className="text-zinc-500">Severity</span>
          <p className={`font-mono font-medium ${prop.severity_transfer >= 0.5 ? "text-red-400" : prop.severity_transfer >= 0.25 ? "text-amber-400" : "text-emerald-400"}`}>
            {(prop.severity_transfer * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <span className="text-zinc-500">Confidence</span>
          <p className="text-zinc-300 font-mono">{(prop.confidence * 100).toFixed(0)}%</p>
        </div>
      </div>

      {bestIntervention && <InterventionDetail spec={bestIntervention} />}
    </div>
  );
}

export default function PropagationPathView({ propagations, lang }: { propagations: PropagationContract[]; lang: "en" | "ar" }) {
  const sorted = [...propagations].sort((a, b) => b.severity_transfer - a.severity_transfer);
  const breakableCount = sorted.filter((p) => p.breakable_point).length;
  const totalSeverity = sorted.reduce((sum, p) => sum + p.severity_transfer, 0);

  return (
    <div dir={lang === "ar" ? "rtl" : "ltr"} className="space-y-4">
      <h3 className="text-lg font-semibold text-zinc-100">
        {lang === "ar" ? "مسارات الانتشار" : "Propagation Paths"}
      </h3>

      <div className="grid grid-cols-3 gap-3 rounded-lg bg-zinc-900 border border-zinc-700 p-3">
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "المسارات" : "Paths"}</span>
          <p className="text-lg font-bold text-zinc-100">{sorted.length}</p>
        </div>
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "قابلة للقطع" : "Breakable"}</span>
          <p className="text-lg font-bold text-emerald-400">{breakableCount}</p>
        </div>
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "إجمالي الشدة" : "Total Severity"}</span>
          <p className="text-lg font-bold text-amber-400">{totalSeverity.toFixed(2)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {sorted.map((p) => (
          <PropagationCard key={p.propagation_id} prop={p} />
        ))}
      </div>
    </div>
  );
}
