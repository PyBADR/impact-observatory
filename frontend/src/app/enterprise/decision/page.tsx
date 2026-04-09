"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Decision Detail Page
 * Layer: UI (L6) — Full decision lifecycle view with timeline + explainability
 *
 * Shows: Decision timeline, authority events, causal chain, policy context
 */
import { useState, useMemo } from "react";
import { useAppStore } from "@/store/app-store";
import {
  useDecisions,
  useDecisionDetail,
  useAuthorityEvents,
  useAuthorityVerify,
  useRunResult,
} from "@/hooks/use-enterprise";
import { DecisionTimeline } from "@/features/enterprise/components";
import { ExplainabilityPanel } from "@/features/enterprise/components";
import { PolicyGraph } from "@/features/enterprise/components";
import { ENTERPRISE_LABELS } from "@/types/enterprise";
import type { DecisionTimelineEvent, TimelineEventType, PolicyNode, PolicyEdge } from "@/types/enterprise";
import type { Classification } from "@/types/observatory";

const STATUS_COLORS: Record<string, string> = {
  PENDING: "#B45309",
  CREATED: "#475569",
  PROPOSED: "#1D4ED8",
  IN_REVIEW: "#7C3AED",
  APPROVED: "#15803D",
  REJECTED: "#B91C1C",
  EXECUTED: "#059669",
  EXECUTION_FAILED: "#B91C1C",
  EXECUTION_PENDING: "#CA8A04",
  ESCALATED: "#B45309",
  REVOKED: "#64748B",
  WITHDRAWN: "#94A3B8",
  CLOSED: "#475569",
};

function mapAuthorityEventToTimeline(
  event: Record<string, unknown>,
  index: number,
): DecisionTimelineEvent {
  const action = String(event.action ?? "unknown");
  const typeMap: Record<string, TimelineEventType> = {
    propose: "decision_proposed",
    submit: "decision_reviewed",
    approve: "decision_approved",
    reject: "decision_rejected",
    execute: "decision_executed",
    escalate: "decision_reviewed",
    annotate: "decision_reviewed",
    override: "override_applied",
    link: "outcome_observed",
  };
  return {
    id: String(event.event_id ?? `evt-${index}`),
    timestamp: String(event.timestamp ?? new Date().toISOString()),
    type: typeMap[action] ?? "policy_check",
    label: action.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    label_ar: action,
    description: String(event.notes ?? event.rationale ?? `Authority action: ${action}`),
    actor: String(event.actor_id ?? "system"),
    severity: (event.to_status === "REJECTED" || event.to_status === "EXECUTION_FAILED")
      ? "CRITICAL" as Classification
      : (event.to_status === "APPROVED" || event.to_status === "EXECUTED")
        ? "NOMINAL" as Classification
        : "MODERATE" as Classification,
    metadata: event as Record<string, unknown>,
  };
}

export default function DecisionDetailPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const L = ENTERPRISE_LABELS[language];

  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);

  // ── Data ──
  const { data: decisionsData } = useDecisions({ limit: 50 });
  const { data: decisionDetail } = useDecisionDetail(selectedDecisionId);
  const { data: authorityEventsData } = useAuthorityEvents(selectedDecisionId);
  const { data: verifyData } = useAuthorityVerify(selectedDecisionId);

  const decisions = useMemo(() => {
    return ((decisionsData as any)?.decisions ?? []) as Array<Record<string, unknown>>;
  }, [decisionsData]);

  // ── Map authority events to timeline ──
  const timelineEvents = useMemo<DecisionTimelineEvent[]>(() => {
    const events = (authorityEventsData as { events?: Array<Record<string, unknown>> })?.events ?? [];
    return events.map(mapAuthorityEventToTimeline);
  }, [authorityEventsData]);

  // ── Build policy graph from decision context ──
  const policyNodes = useMemo<PolicyNode[]>(() => {
    const detail = decisionDetail as any | undefined;
    if (!detail) return [];
    const nodes: PolicyNode[] = [
      { id: "trigger", label: "Scenario Trigger", label_ar: "محفز السيناريو", type: "rule", sector: "system", weight: 1, active: true, triggered: true },
      { id: "risk_threshold", label: "Risk Threshold", label_ar: "حد المخاطر", type: "threshold", sector: "risk", weight: 0.8, active: true, triggered: true },
      { id: "policy_eval", label: "Policy Evaluation", label_ar: "تقييم السياسة", type: "constraint", sector: "compliance", weight: 0.7, active: true, triggered: true },
      { id: "decision_gate", label: "Decision Gate", label_ar: "بوابة القرار", type: "decision_path", sector: "governance", weight: 0.9, active: true, triggered: true },
    ];
    const dt = String(detail.decision_type ?? "");
    if (dt.includes("APPROVE") || dt.includes("EXECUTE")) {
      nodes.push({ id: "action_approve", label: "Approve Action", label_ar: "اعتماد الإجراء", type: "action", sector: "execution", weight: 0.6, active: true, triggered: true });
    }
    if (dt.includes("ESCALATE")) {
      nodes.push({ id: "action_escalate", label: "Escalate", label_ar: "تصعيد", type: "action", sector: "governance", weight: 0.5, active: true, triggered: true });
    }
    return nodes;
  }, [decisionDetail]);

  const policyEdges = useMemo<PolicyEdge[]>(() => {
    if (!policyNodes.length) return [];
    return [
      { source: "trigger", target: "risk_threshold", label: "activates", type: "triggers", weight: 1 },
      { source: "risk_threshold", target: "policy_eval", label: "requires", type: "requires", weight: 0.8 },
      { source: "policy_eval", target: "decision_gate", label: "enables", type: "enables", weight: 0.7 },
      ...policyNodes.filter((n) => n.type === "action").map((n) => ({
        source: "decision_gate", target: n.id, label: "triggers", type: "triggers" as const, weight: 0.6,
      })),
    ];
  }, [policyNodes]);

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
          {L.decisions}
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
          {isAr ? "دورة حياة القرار الكاملة مع الجدول الزمني والتفسير" : "Full decision lifecycle with timeline, governance audit, and explainability"}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 24 }}>
        {/* Left: Decision List */}
        <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", maxHeight: "80vh", overflowY: "auto" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748B", letterSpacing: "0.04em", textTransform: "uppercase" as const, marginBottom: 12 }}>
            {isAr ? "قائمة القرارات" : "Decision Queue"} ({decisions.length})
          </div>
          {decisions.length === 0 ? (
            <p style={{ fontSize: "0.8125rem", color: "#94A3B8" }}>{L.noData}</p>
          ) : (
            decisions.map((d) => {
              const id = String(d.id);
              const status = String(d.status ?? "PENDING");
              const isSelected = id === selectedDecisionId;
              return (
                <button
                  key={id}
                  onClick={() => setSelectedDecisionId(id)}
                  style={{
                    display: "block", width: "100%", padding: "10px 12px", marginBottom: 6,
                    borderRadius: 8, border: isSelected ? "2px solid #1D4ED8" : "1px solid #E2E8F0",
                    background: isSelected ? "#EFF6FF" : "#FFFFFF", cursor: "pointer",
                    textAlign: isAr ? "right" : "left", transition: "all 0.15s",
                  }}
                >
                  <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#0F172A" }}>
                    {String(d.decision_type ?? "Decision").replace(/_/g, " ")}
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
                    <span style={{ fontSize: "0.6875rem", color: "#64748B" }}>{id.slice(0, 12)}</span>
                    <span style={{
                      fontSize: "0.625rem", fontWeight: 600, padding: "1px 6px", borderRadius: 10,
                      color: STATUS_COLORS[status] ?? "#475569",
                      background: `${STATUS_COLORS[status] ?? "#475569"}18`,
                    }}>
                      {status}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Right: Detail View */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {!selectedDecisionId ? (
            <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 40, textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none" style={{ margin: "0 auto 16px" }}>
                <circle cx="24" cy="24" r="22" stroke="#E2E8F0" strokeWidth="2"/>
                <path d="M16 24h16M24 16v16" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              <p style={{ fontSize: "0.875rem", color: "#94A3B8" }}>
                {isAr ? "اختر قراراً لعرض التفاصيل" : "Select a decision to view its full lifecycle"}
              </p>
            </div>
          ) : (
            <>
              {/* Decision Summary Card */}
              <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                  <div>
                    <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0F172A", margin: 0 }}>
                      {String((decisionDetail as any)?.decision_type ?? "Decision").replace(/_/g, " ")}
                    </h2>
                    <p style={{ fontSize: "0.8125rem", color: "#64748B", margin: "4px 0 0" }}>
                      ID: {selectedDecisionId.slice(0, 20)}
                    </p>
                  </div>
                  {/* Verify badge */}
                  {verifyData && (
                    <div style={{
                      display: "flex", alignItems: "center", gap: 6, padding: "4px 12px", borderRadius: 20,
                      background: verifyData.valid ? "#DCFCE7" : "#FEE2E2",
                      color: verifyData.valid ? "#15803D" : "#B91C1C",
                      fontSize: "0.75rem", fontWeight: 600,
                    }}>
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        {verifyData.valid ? (
                          <path d="M3 7l3 3 5-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        ) : (
                          <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                        )}
                      </svg>
                      {verifyData.valid ? (isAr ? "سلسلة التدقيق صحيحة" : "Audit Chain Valid") : (isAr ? "سلسلة التدقيق مكسورة" : "Audit Chain Broken")}
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 24, fontSize: "0.8125rem", color: "#475569" }}>
                  <span>{isAr ? "الحالة" : "Status"}: <strong style={{ color: STATUS_COLORS[String((decisionDetail as any)?.status ?? "")] ?? "#475569" }}>{String((decisionDetail as any)?.status ?? "N/A")}</strong></span>
                  <span>{isAr ? "النوع" : "Type"}: <strong>{String((decisionDetail as any)?.decision_type ?? "N/A")}</strong></span>
                </div>
              </div>

              {/* Decision Timeline */}
              <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                  {L.timeline}
                </h3>
                <DecisionTimeline
                  events={timelineEvents}
                  language={language}
                  onEventSelect={() => {}}
                />
              </div>

              {/* Policy Graph */}
              {policyNodes.length > 0 && (
                <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
                  <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
                    {L.policyGraph}
                  </h3>
                  <PolicyGraph
                    nodes={policyNodes}
                    edges={policyEdges}
                    language={language}
                    onNodeSelect={() => {}}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
