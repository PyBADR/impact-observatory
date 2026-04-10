"use client";

import type { KnowledgeGraphNode } from "@/types/observatory";

const STRESS_COLORS: Record<string, string> = {
  CRITICAL: "text-red-400",
  ELEVATED: "text-orange-400",
  MODERATE: "text-yellow-400",
  LOW: "text-green-400",
  NOMINAL: "text-slate-400",
};

const STRESS_BG: Record<string, string> = {
  CRITICAL: "bg-red-500/10 border-red-500/30",
  ELEVATED: "bg-orange-500/10 border-orange-500/30",
  MODERATE: "bg-yellow-500/10 border-yellow-500/30",
  LOW: "bg-green-500/10 border-green-500/30",
  NOMINAL: "bg-slate-500/10 border-slate-500/30",
};

interface Props {
  node: KnowledgeGraphNode;
  onClose?: () => void;
  isAr?: boolean;
}

export function GraphNodeCard({ node, onClose, isAr = false }: Props) {
  const classification = node.classification || "NOMINAL";

  return (
    <div className="bg-slate-900/95 backdrop-blur border border-slate-700 rounded-lg p-4 w-72 shadow-xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-white">
            {isAr && node.label_ar ? node.label_ar : node.label}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">{node.id}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-white text-lg leading-none"
          >
            x
          </button>
        )}
      </div>

      {/* Classification badge */}
      <div
        className={`inline-block px-2 py-0.5 text-xs font-medium rounded border mb-3 ${
          STRESS_BG[classification]
        } ${STRESS_COLORS[classification]}`}
      >
        {classification}
      </div>

      {/* Details */}
      <div className="space-y-1.5 text-xs">
        <Row label={isAr ? "الطبقة" : "Layer"} value={node.layer} />
        <Row label={isAr ? "النوع" : "Type"} value={node.type} />
        <Row label={isAr ? "الوزن" : "Weight"} value={node.weight.toFixed(3)} />
        <Row label={isAr ? "الحساسية" : "Sensitivity"} value={node.sensitivity.toFixed(3)} />
        <Row label={isAr ? "خط العرض" : "Lat"} value={node.lat.toFixed(4)} />
        <Row label={isAr ? "خط الطول" : "Lng"} value={node.lng.toFixed(4)} />
        {node.stress != null && node.stress > 0 && (
          <Row
            label={isAr ? "الضغط" : "Stress"}
            value={`${(node.stress * 100).toFixed(1)}%`}
            valueClass={STRESS_COLORS[classification]}
          />
        )}
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  valueClass = "text-white",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={valueClass}>{value}</span>
    </div>
  );
}
