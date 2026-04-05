"use client";

/**
 * Impact Observatory | مرصد الأثر — Propagation Graph Explorer
 *
 * GCC Causal Knowledge Graph.
 * 5 layers · 76 nodes · 190 edges
 *
 * Institutional light shell + dark visualization canvas.
 * Enterprise empty state with context and guidance.
 */

import { useState, useCallback } from "react";
import AppShell from "@/components/shell/AppShell";
import { useAppStore } from "@/store/app-store";
import { useGraphData } from "@/features/graph/useGraphData";
import { GraphCanvas } from "@/features/graph/GraphCanvas";
import { GraphControls } from "@/features/graph/GraphControls";
import { GraphNodeCard } from "@/features/graph/GraphNodeCard";
import {
  Panel,
  EmptyState,
  FilterChip,
  SectionHeader,
  ClassificationBadge,
  InlineLoader,
} from "@/components/ui";
import type { GraphLayer, KnowledgeGraphNode } from "@/types/observatory";

const LAYER_META: Record<string, { label: string; labelAr: string; desc: string }> = {
  geography: { label: "Geography", labelAr: "الجغرافيا", desc: "Physical locations, corridors, chokepoints" },
  infrastructure: { label: "Infrastructure", labelAr: "البنية التحتية", desc: "Ports, airports, pipelines" },
  economy: { label: "Economy", labelAr: "الاقتصاد", desc: "Trade flows, commodity markets" },
  finance: { label: "Finance", labelAr: "المالية", desc: "Banks, insurers, payment networks" },
  society: { label: "Society", labelAr: "المجتمع", desc: "Regulatory bodies, public services" },
};

const GRAPH_CONTEXT = {
  en: {
    title: "GCC Causal Knowledge Graph",
    subtitle:
      "Structural model of systemic interdependencies across GCC financial markets and physical infrastructure.",
    nodeCount: "76 nodes across 5 system layers",
    edgeCount: "190 directed causal edges",
    purpose:
      "Select a node to inspect its causal relationships, sector classification, and estimated systemic weight. Filter by layer to isolate propagation pathways.",
    selectHint: "Click any node to inspect",
    layerHint: "Filter by system layer",
  },
  ar: {
    title: "رسم المعرفة السببي لدول مجلس التعاون",
    subtitle:
      "نموذج هيكلي للترابطات المنظومية عبر الأسواق المالية الخليجية والبنية التحتية المادية.",
    nodeCount: "٧٦ عقدة عبر ٥ طبقات",
    edgeCount: "١٩٠ حافة سببية موجّهة",
    purpose:
      "اختر عقدة لفحص علاقاتها السببية وتصنيف القطاع والوزن المنظومي المقدّر.",
    selectHint: "انقر فوق أي عقدة للفحص",
    layerHint: "تصفية حسب طبقة النظام",
  },
};

// ── Enterprise error state ─────────────────────────────────────────────

function GraphErrorState({
  error,
  isAr,
}: {
  error: string;
  isAr: boolean;
}) {
  return (
    <Panel className="mx-6 my-6">
      <EmptyState
        icon={
          <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        }
        title={isAr ? "تعذّر تحميل الرسم البياني" : "Graph Unavailable"}
        titleAr="تعذّر تحميل الرسم البياني"
        description={
          isAr
            ? "تعذّر الاتصال بخدمة الرسم البياني. تحقق من تشغيل الخادم الخلفي."
            : "Unable to connect to the knowledge graph service. Verify the backend API is reachable."
        }
        lang={isAr ? "ar" : "en"}
        action={
          <a
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
          >
            {isAr ? "العودة إلى لوحة المعلومات" : "Return to Dashboard"}
          </a>
        }
      />
    </Panel>
  );
}

// ── Context panel (right side, always visible) ─────────────────────────

function GraphContextPanel({
  node,
  onClose,
  isAr,
  totalNodes,
  totalEdges,
  visibleNodes,
  visibleEdges,
  activeLayer,
}: {
  node: KnowledgeGraphNode | null;
  onClose: () => void;
  isAr: boolean;
  totalNodes: number;
  totalEdges: number;
  visibleNodes: number;
  visibleEdges: number;
  activeLayer: GraphLayer | null;
}) {
  const ctx = GRAPH_CONTEXT[isAr ? "ar" : "en"];

  return (
    <div className="w-72 flex-shrink-0 border-l border-io-border bg-io-surface flex flex-col overflow-y-auto">
      {/* Graph info header */}
      <div className="p-4 border-b border-io-border">
        <p className="text-xs font-semibold text-io-secondary uppercase tracking-widest mb-2">
          {isAr ? "الرسم البياني" : "Knowledge Graph"}
        </p>
        <h2 className="text-sm font-semibold text-io-primary mb-3 leading-snug">
          {ctx.title}
        </h2>
        <p className="text-xs text-io-secondary leading-relaxed mb-3">
          {ctx.subtitle}
        </p>
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-io-secondary">{isAr ? "العقد" : "Nodes"}</span>
            <span className="font-medium text-io-primary tabular-nums">
              {visibleNodes === totalNodes
                ? totalNodes
                : `${visibleNodes} / ${totalNodes}`}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-io-secondary">{isAr ? "الحواف" : "Edges"}</span>
            <span className="font-medium text-io-primary tabular-nums">
              {visibleEdges === totalEdges
                ? totalEdges
                : `${visibleEdges} / ${totalEdges}`}
            </span>
          </div>
          {activeLayer && (
            <div className="flex justify-between text-xs">
              <span className="text-io-secondary">{isAr ? "الطبقة النشطة" : "Active Layer"}</span>
              <span className="font-medium text-io-accent capitalize">{activeLayer}</span>
            </div>
          )}
        </div>
      </div>

      {/* Selected node detail */}
      {node ? (
        <div className="flex-1 p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-io-secondary uppercase tracking-widest">
              {isAr ? "العقدة المحددة" : "Selected Node"}
            </p>
            <button
              onClick={onClose}
              className="w-6 h-6 flex items-center justify-center rounded text-io-secondary hover:text-io-primary hover:bg-io-bg transition-colors"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-3">
            {/* Name */}
            <div>
              <p className="text-sm font-semibold text-io-primary leading-snug">
                {isAr && node.label_ar ? node.label_ar : node.label ?? node.id}
              </p>
              <p className="text-xs text-io-secondary mt-0.5 font-mono">{node.id}</p>
            </div>

            {/* Layer */}
            {node.layer && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-io-secondary">
                  {isAr ? "الطبقة" : "Layer"}
                </span>
                <span className="text-xs font-medium text-io-primary capitalize bg-io-bg border border-io-border px-2 py-0.5 rounded">
                  {node.layer}
                </span>
              </div>
            )}

            {/* Node type */}
            {node.type && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-io-secondary">
                  {isAr ? "النوع" : "Type"}
                </span>
                <span className="text-xs font-medium text-io-primary capitalize">
                  {node.type}
                </span>
              </div>
            )}

            {/* Systemic weight */}
            {node.weight !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-io-secondary">
                  {isAr ? "الوزن المنظومي" : "Systemic Weight"}
                </span>
                <span className="text-xs font-semibold tabular-nums text-io-primary">
                  {(node.weight * 100).toFixed(1)}%
                </span>
              </div>
            )}

            {/* Stress */}
            {node.stress !== undefined && (
              <div className="pt-2 border-t border-io-border">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-io-secondary">
                    {isAr ? "مستوى الضغط" : "Stress Level"}
                  </span>
                  {node.classification && (
                    <ClassificationBadge level={node.classification} lang={isAr ? "ar" : "en"} size="xs" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex-1 p-4">
          <div className="py-6 text-center">
            <div className="w-10 h-10 rounded-xl bg-io-bg border border-io-border flex items-center justify-center mx-auto mb-3">
              <svg className="w-5 h-5 text-io-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 3.75H6A2.25 2.25 0 003.75 6v1.5M16.5 3.75H18A2.25 2.25 0 0120.25 6v1.5m0 9V18A2.25 2.25 0 0118 20.25h-1.5m-9 0H6A2.25 2.25 0 013.75 18v-1.5M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <p className="text-xs font-medium text-io-primary mb-1">
              {isAr ? "لم يُحدد أي عقدة" : "No Node Selected"}
            </p>
            <p className="text-xs text-io-secondary leading-relaxed">
              {ctx.selectHint}
            </p>
          </div>

          {/* Layer guide */}
          <div className="border-t border-io-border pt-4">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-3">
              {isAr ? "طبقات النظام" : "System Layers"}
            </p>
            <div className="space-y-2">
              {Object.entries(LAYER_META).map(([key, meta]) => (
                <div key={key} className="flex gap-2">
                  <span className="text-xs font-medium text-io-primary w-24 flex-shrink-0 capitalize">
                    {isAr ? meta.labelAr : meta.label}
                  </span>
                  <span className="text-xs text-io-secondary leading-relaxed">
                    {meta.desc}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────

export default function GraphExplorerPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const {
    nodes,
    edges,
    loading,
    error,
    totalNodes,
    totalEdges,
    activeLayer,
    filterByLayer,
  } = useGraphData();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(true);

  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId) || null
    : null;

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId));
  }, []);

  const handleLayerChange = useCallback(
    (layer: GraphLayer | null) => {
      filterByLayer(layer);
    },
    [filterByLayer]
  );

  if (error) {
    return (
      <AppShell activeRoute="graph">
        <GraphErrorState error={error} isAr={isAr} />
      </AppShell>
    );
  }

  const ctx = GRAPH_CONTEXT[isAr ? "ar" : "en"];

  return (
    <AppShell activeRoute="graph">
      <div className="flex h-[calc(100vh-56px)]" dir={isAr ? "rtl" : "ltr"}>

        {/* ── Left / Top: Controls panel ──────────────────────────── */}
        <div className="w-56 flex-shrink-0 border-r border-io-border bg-io-surface flex flex-col">
          {/* Panel header */}
          <div className="px-4 py-3.5 border-b border-io-border">
            <p className="text-[10px] font-semibold text-io-secondary uppercase tracking-widest mb-0.5">
              {isAr ? "التصفية" : "Filters"}
            </p>
            <p className="text-xs text-io-secondary">
              {isAr ? ctx.layerHint : ctx.layerHint}
            </p>
          </div>

          {/* Layer filters */}
          <div className="p-3 flex flex-col gap-1.5 flex-1">
            <button
              onClick={() => handleLayerChange(null)}
              className={`w-full text-left px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                activeLayer === null
                  ? "bg-io-accent text-white"
                  : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
              }`}
            >
              {isAr ? "كل الطبقات" : "All Layers"}
            </button>

            {Object.entries(LAYER_META).map(([key, meta]) => (
              <button
                key={key}
                onClick={() => handleLayerChange(key as GraphLayer)}
                className={`w-full text-left px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                  activeLayer === key
                    ? "bg-io-accent text-white"
                    : "text-io-secondary hover:text-io-primary hover:bg-io-bg"
                }`}
              >
                <span className="block">{isAr ? meta.labelAr : meta.label}</span>
                <span
                  className={`text-[10px] mt-0.5 block ${
                    activeLayer === key ? "text-blue-100" : "text-io-secondary/70"
                  }`}
                >
                  {meta.desc}
                </span>
              </button>
            ))}

            {/* Label toggle */}
            <div className="mt-auto pt-3 border-t border-io-border">
              <label className="flex items-center gap-2 cursor-pointer px-1 py-1 rounded hover:bg-io-bg transition-colors">
                <input
                  type="checkbox"
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                  className="rounded border-io-border text-io-accent"
                />
                <span className="text-xs text-io-secondary">
                  {isAr ? "إظهار التسميات" : "Show Labels"}
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* ── Center: Canvas ───────────────────────────────────────── */}
        <div className="flex-1 relative bg-slate-950 overflow-hidden">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                {/* Loading state — enterprise */}
                <div className="w-10 h-10 border border-slate-700 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-5 h-5 animate-spin text-blue-400"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="3"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                </div>
                <p className="text-xs text-slate-400 font-medium">
                  {isAr ? "جاري تحميل رسم المعرفة..." : "Loading knowledge graph…"}
                </p>
                <p className="text-[10px] text-slate-600 mt-1">
                  {isAr ? "٧٦ عقدة · ١٩٠ حافة" : "76 nodes · 190 edges"}
                </p>
              </div>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center max-w-xs px-6">
                <div className="w-10 h-10 rounded-xl border border-slate-700 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-5 h-5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0016.803 15.803z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-slate-300 mb-1.5">
                  {isAr ? "لا توجد كيانات مطابقة" : "No Entities Matched"}
                </p>
                <p className="text-xs text-slate-500 leading-relaxed">
                  {isAr
                    ? "لا توجد كيانات تطابق المرشحات الحالية. عدّل المرشحات أو ابحث عن قطاع أو مؤسسة أو حدث."
                    : "No entities matched the current filters. Adjust filters or search for a sector, institution, or event."}
                </p>
              </div>
            </div>
          ) : (
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedNodeId}
              showLabels={showLabels}
              isAr={isAr}
            />
          )}

          {/* Canvas overlay: graph stats bar */}
          {!loading && (
            <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur border border-slate-700/60 rounded-lg px-3.5 py-2.5">
              <p className="text-[11px] font-semibold text-white leading-none mb-1">
                {isAr ? "رسم المعرفة السببي" : "GCC Causal Knowledge Graph"}
              </p>
              <p className="text-[10px] text-slate-400 tabular-nums">
                {nodes.length}{" "}
                {isAr ? "عقدة" : "nodes"}{" · "}
                {edges.length}{" "}
                {isAr ? "حافة" : "edges"}{" · "}
                5{" "}
                {isAr ? "طبقات" : "layers"}
              </p>
            </div>
          )}
        </div>

        {/* ── Right: Context panel ─────────────────────────────────── */}
        <GraphContextPanel
          node={selectedNode}
          onClose={() => setSelectedNodeId(null)}
          isAr={isAr}
          totalNodes={totalNodes}
          totalEdges={totalEdges}
          visibleNodes={nodes.length}
          visibleEdges={edges.length}
          activeLayer={activeLayer}
        />
      </div>
    </AppShell>
  );
}
