"use client";

import type { GraphLayer, StressClassification } from "@/types/observatory";

const LAYERS: { id: GraphLayer; label: string; label_ar: string; color: string }[] = [
  { id: "geography", label: "Geography", label_ar: "الجغرافيا", color: "#22d3ee" },
  { id: "infrastructure", label: "Infrastructure", label_ar: "البنية التحتية", color: "#f59e0b" },
  { id: "economy", label: "Economy", label_ar: "الاقتصاد", color: "#10b981" },
  { id: "finance", label: "Finance", label_ar: "المالية", color: "#6366f1" },
  { id: "society", label: "Society", label_ar: "المجتمع", color: "#ec4899" },
];

interface Props {
  activeLayer: GraphLayer | null;
  onLayerChange: (layer: GraphLayer | null) => void;
  totalNodes: number;
  totalEdges: number;
  visibleNodes: number;
  visibleEdges: number;
  isAr?: boolean;
}

export function GraphControls({
  activeLayer,
  onLayerChange,
  totalNodes,
  totalEdges,
  visibleNodes,
  visibleEdges,
  isAr = false,
}: Props) {
  return (
    <div className="bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg p-3 space-y-3">
      {/* Stats */}
      <div className="flex gap-4 text-xs text-slate-400">
        <span>
          {isAr ? "العقد" : "Nodes"}: <strong className="text-white">{visibleNodes}</strong>/{totalNodes}
        </span>
        <span>
          {isAr ? "الحواف" : "Edges"}: <strong className="text-white">{visibleEdges}</strong>/{totalEdges}
        </span>
      </div>

      {/* Layer filters */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => onLayerChange(null)}
          className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
            !activeLayer
              ? "bg-white/10 border-white/30 text-white"
              : "border-slate-600 text-slate-400 hover:border-slate-500"
          }`}
        >
          {isAr ? "الكل" : "All"}
        </button>
        {LAYERS.map((l) => (
          <button
            key={l.id}
            onClick={() => onLayerChange(l.id === activeLayer ? null : l.id)}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors flex items-center gap-1.5 ${
              l.id === activeLayer
                ? "bg-white/10 border-white/30 text-white"
                : "border-slate-600 text-slate-400 hover:border-slate-500"
            }`}
          >
            <span
              className="w-2 h-2 rounded-full inline-block"
              style={{ backgroundColor: l.color }}
            />
            {isAr ? l.label_ar : l.label}
          </button>
        ))}
      </div>
    </div>
  );
}
