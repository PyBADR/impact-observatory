"use client";

import type { CounterfactualContract, CounterfactualBranch, ConfidenceDimensions } from "@/types/banking-intelligence";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(v);

function ConfidenceBars({ c }: { c: ConfidenceDimensions }) {
  const dims = [
    { label: "Direction", v: c.directional_confidence },
    { label: "Impact", v: c.impact_estimate_confidence },
    { label: "Execution", v: c.execution_confidence },
    { label: "Data", v: c.data_sufficiency_confidence },
  ];
  return (
    <div className="mt-2 space-y-1">
      {dims.map((d) => (
        <div key={d.label} className="flex items-center gap-2 text-xs">
          <span className="w-16 text-zinc-500">{d.label}</span>
          <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${d.v >= 0.7 ? "bg-emerald-500" : d.v >= 0.5 ? "bg-amber-500" : "bg-red-500"}`}
              style={{ width: `${d.v * 100}%` }}
            />
          </div>
          <span className="w-8 text-right text-zinc-400">{(d.v * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}

function BranchCard({ branch, isBest, isBaseline }: { branch: CounterfactualBranch; isBest: boolean; isBaseline: boolean }) {
  const borderColor = isBest ? "border-emerald-500" : isBaseline ? "border-zinc-600" : "border-zinc-700";
  return (
    <div className={`rounded-lg border-2 ${borderColor} bg-zinc-900 p-4 flex flex-col gap-3`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-zinc-200 capitalize">
          {branch.branch_label.replace(/_/g, " ")}
        </span>
        {isBest && <span className="text-[10px] px-1.5 py-0.5 bg-emerald-900 text-emerald-300 rounded">BEST</span>}
        {isBaseline && <span className="text-[10px] px-1.5 py-0.5 bg-zinc-700 text-zinc-300 rounded">BASELINE</span>}
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed">{branch.description}</p>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-zinc-500">Expected Loss</span>
          <p className="text-red-400 font-mono font-medium">{fmt(branch.expected_loss_usd)}</p>
        </div>
        <div>
          <span className="text-zinc-500">Cost</span>
          <p className="text-amber-400 font-mono font-medium">{fmt(branch.expected_cost_usd)}</p>
        </div>
        <div>
          <span className="text-zinc-500">Stabilize</span>
          <p className="text-zinc-200 font-mono">{branch.expected_time_to_stabilize_hours}h</p>
        </div>
        <div>
          <span className="text-zinc-500">vs Baseline</span>
          <p className={`font-mono font-medium ${branch.delta_vs_baseline_usd < 0 ? "text-emerald-400" : branch.delta_vs_baseline_usd === 0 ? "text-zinc-400" : "text-red-400"}`}>
            {branch.delta_vs_baseline_usd <= 0 ? "" : "+"}{fmt(branch.delta_vs_baseline_usd)}
          </p>
        </div>
      </div>
      <div className="border-t border-zinc-800 pt-2">
        <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Downside Risk</span>
        <p className="text-xs text-red-300 mt-0.5">
          {fmt(branch.downside_risk.worst_case_loss_usd)} worst case ({(branch.downside_risk.probability_of_worst_case * 100).toFixed(0)}% prob)
        </p>
      </div>
      <ConfidenceBars c={branch.confidence} />
    </div>
  );
}

export default function CounterfactualPanel({ contract, lang }: { contract: CounterfactualContract; lang: "en" | "ar" }) {
  const branches: CounterfactualBranch[] = [
    contract.do_nothing,
    contract.recommended_action,
    contract.delayed_action,
    contract.alternative_action,
  ];

  const bestLabel = branches.reduce((best, b) =>
    (b.expected_loss_usd + b.expected_cost_usd) < (best.expected_loss_usd + best.expected_cost_usd) ? b : best
  ).branch_label;

  const isJustified = contract.confidence_adjusted_benefit_usd > 0;

  return (
    <div dir={lang === "ar" ? "rtl" : "ltr"} className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-zinc-100">
          {lang === "ar" ? "تحليل السيناريو المقارن" : "Counterfactual Analysis"}
        </h3>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${isJustified ? "bg-emerald-900 text-emerald-300" : "bg-red-900 text-red-300"}`}>
          {isJustified ? "Action Justified" : "Action Not Justified"}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {branches.map((b) => (
          <BranchCard
            key={b.branch_label}
            branch={b}
            isBest={b.branch_label === bestLabel}
            isBaseline={b.branch_label === "do_nothing"}
          />
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3 rounded-lg bg-zinc-900 border border-zinc-700 p-4">
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "صافي المنفعة" : "Net Benefit"}</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">{fmt(contract.recommended_net_benefit_usd)}</p>
        </div>
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "معدل حسب الثقة" : "Confidence-Adjusted"}</span>
          <p className="text-xl font-bold text-blue-400 font-mono">{fmt(contract.confidence_adjusted_benefit_usd)}</p>
        </div>
        <div className="text-center">
          <span className="text-xs text-zinc-500 block">{lang === "ar" ? "تكلفة التأخير" : "Delay Penalty"}</span>
          <p className="text-xl font-bold text-red-400 font-mono">{fmt(contract.delay_penalty_usd)}</p>
        </div>
      </div>
    </div>
  );
}
