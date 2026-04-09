"use client";

/**
 * OperatingLayerView — Unified view for the Decision Operating Layer
 *
 * Composes: DecisionAnchorCard + CounterfactualBlock + DecisionGatePanel
 * Integrated into the Decision Authority Panel as an additive section.
 */

import React from "react";
import { Layers } from "lucide-react";
import { DecisionAnchorCard } from "./DecisionAnchorCard";
import { CounterfactualBlock } from "./CounterfactualBlock";
import { DecisionGatePanel } from "./DecisionGatePanel";
import type { OperatingLayer } from "../types";

interface OperatingLayerViewProps {
  operatingLayer: OperatingLayer;
  language?: "en" | "ar";
}

export function OperatingLayerView({
  operatingLayer,
  language = "en",
}: OperatingLayerViewProps) {
  const isAr = language === "ar";

  return (
    <div className="space-y-4" dir={isAr ? "rtl" : "ltr"}>
      {/* Section header */}
      <div className="flex items-center gap-2 px-1">
        <Layers size={14} className="text-violet-400" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-violet-400">
          {isAr ? "طبقة التشغيل" : "Decision Operating Layer"}
        </span>
        <span className="text-[8px] text-slate-600 font-mono ml-auto">
          v{operatingLayer.version}
        </span>
      </div>

      {/* 1. Decision Anchor */}
      <DecisionAnchorCard
        anchor={operatingLayer.decision_anchor}
        language={language}
      />

      {/* 2. Counterfactual Comparison */}
      <div className="bg-white/[0.02] rounded-xl border border-white/[0.06] p-4">
        <CounterfactualBlock
          comparison={operatingLayer.counterfactual_comparison}
          language={language}
        />
      </div>

      {/* 3. Decision Gate */}
      <DecisionGatePanel
        gate={operatingLayer.decision_gate}
        language={language}
      />
    </div>
  );
}
