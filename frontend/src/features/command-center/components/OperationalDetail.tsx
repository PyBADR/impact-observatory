"use client";

/**
 * OperationalDetail — Tabbed container for deep-dive operational data
 *
 * This component wraps Graph, Propagation, Impact Assessment, Sector Rollup,
 * and Explanation into a single tabbed panel at the BOTTOM of the dashboard.
 *
 * Design rationale: Operational data is important but subordinate to
 * decision priorities. Executives see decisions first; analysts drill
 * down here for causal chains, graph topology, and sector-level detail.
 *
 * Tabs:
 *   1. Network Graph — force-directed causal graph
 *   2. Propagation — causal chain + sector impacts
 *   3. Sector Detail — impact assessment + rollup
 *   4. Explanation — narrative + methodology + audit trail
 */

import React, { useState } from "react";
import {
  Network,
  GitBranch,
  BarChart3,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  Shield,
} from "lucide-react";
import { GraphPanel } from "./GraphPanel";
import { PropagationView } from "./PropagationView";
import { ImpactPanel } from "./ImpactPanel";
import { SectorRollupBar } from "./SectorRollupBar";
import { ExplanationPanel } from "./ExplanationPanel";
import { NarrativeFetcher } from "./NarrativeFetcher";
import { DecisionAuthorityPanel } from "./DecisionAuthorityPanel";
import type { NarrativeData } from "./NarrativePanel";
import type { KnowledgeGraphNode, KnowledgeGraphEdge, CausalStep, SectorImpact, SectorRollup } from "@/types/observatory";
import type { SafeImpact } from "@/lib/v2/api-types";

// ── Types ─────────────────────────────────────────────────────────────

type TabId = "graph" | "propagation" | "sectors" | "narrative" | "authority" | "explanation";

interface OperationalDetailProps {
  // Graph tab
  graphNodes: KnowledgeGraphNode[];
  graphEdges: KnowledgeGraphEdge[];
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string | null) => void;

  // Propagation tab
  causalChain: CausalStep[];
  sectorImpacts: SectorImpact[];
  totalLossUsd: number;
  propagationDepth: number;

  // Sector tab
  impacts: SafeImpact[];
  sectorRollups: Record<string, SectorRollup>;

  // Narrative tab (executive intelligence brief — self-fetching)
  scenarioId?: string;
  scenarioSeverity?: number;
  scenarioHorizonHours?: number;
  narrativeLanguage?: "en" | "ar";

  // Explanation tab
  narrativeEn: string;
  narrativeAr: string;
  methodology: string;
  confidence: number;
  totalSteps: number;
  auditHash: string;
  modelVersion: string;
  dataSources: string[];
  stagesCompleted: string[];
  warnings: string[];
}

// ── Tab definitions ──────────────────────────────────────────────────

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "graph", label: "Network Graph", icon: <Network size={13} /> },
  { id: "propagation", label: "Propagation", icon: <GitBranch size={13} /> },
  { id: "sectors", label: "Sector Detail", icon: <BarChart3 size={13} /> },
  { id: "narrative", label: "Intelligence Brief", icon: <FileText size={13} /> },
  { id: "authority", label: "Decision Authority", icon: <Shield size={13} /> },
  { id: "explanation", label: "Explanation", icon: <BookOpen size={13} /> },
];

// ── Main Component ────────────────────────────────────────────────────

export function OperationalDetail(props: OperationalDetailProps) {
  const [activeTab, setActiveTab] = useState<TabId>("propagation");
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="bg-[#0A0E18] border-t border-white/[0.06] flex flex-col">
      {/* Tab bar with collapse toggle */}
      <div className="flex items-center justify-between px-4 border-b border-white/[0.04]">
        <div className="flex items-center gap-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                if (collapsed) setCollapsed(false);
              }}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wider transition-colors border-b-2 ${
                activeTab === tab.id && !collapsed
                  ? "text-blue-400 border-blue-400"
                  : "text-slate-500 border-transparent hover:text-slate-400"
              }`}
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-1 px-2 py-1.5 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
        >
          {collapsed ? (
            <>
              Expand <ChevronDown size={11} />
            </>
          ) : (
            <>
              Collapse <ChevronUp size={11} />
            </>
          )}
        </button>
      </div>

      {/* Tab content */}
      {!collapsed && (
        <div className="flex-1 min-h-[300px] max-h-[450px] overflow-hidden">
          {activeTab === "graph" && (
            <GraphPanel
              nodes={props.graphNodes}
              edges={props.graphEdges}
              selectedNodeId={props.selectedNodeId}
              onNodeSelect={props.onNodeSelect}
            />
          )}
          {activeTab === "propagation" && (
            <PropagationView
              causalChain={props.causalChain}
              sectorImpacts={props.sectorImpacts}
              totalLossUsd={props.totalLossUsd}
              propagationDepth={props.propagationDepth}
              confidence={props.confidence}
            />
          )}
          {activeTab === "sectors" && (
            <div className="flex flex-col h-full overflow-hidden">
              <SectorRollupBar rollups={props.sectorRollups} />
              <div className="flex-1 overflow-y-auto">
                <ImpactPanel impacts={props.impacts} />
              </div>
            </div>
          )}
          {activeTab === "narrative" && props.scenarioId && (
            <NarrativeFetcher
              scenarioId={props.scenarioId}
              severity={props.scenarioSeverity ?? 0.7}
              horizonHours={props.scenarioHorizonHours ?? 336}
              language={props.narrativeLanguage ?? "en"}
            />
          )}
          {activeTab === "authority" && props.scenarioId && (
            <DecisionAuthorityPanel
              scenarioId={props.scenarioId}
              severity={props.scenarioSeverity ?? 0.7}
              horizonHours={props.scenarioHorizonHours ?? 336}
              language={props.narrativeLanguage ?? "en"}
            />
          )}
          {activeTab === "explanation" && (
            <ExplanationPanel
              narrativeEn={props.narrativeEn}
              narrativeAr={props.narrativeAr}
              methodology={props.methodology}
              confidence={props.confidence}
              totalSteps={props.totalSteps}
              auditHash={props.auditHash}
              modelVersion={props.modelVersion}
              dataSources={props.dataSources}
              stagesCompleted={props.stagesCompleted}
              warnings={props.warnings}
            />
          )}
        </div>
      )}
    </div>
  );
}
