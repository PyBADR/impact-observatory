"use client";

import { useState } from "react";
import { useAppStore } from "@/store/app-store";
import { useAuditEvents, useAuditVerify } from "@/hooks/use-admin";
import { ADMIN_LABELS } from "@/types/admin";
import type { AuditEventResponse } from "@/types/admin";

function t(obj: { en: string; ar: string }, lang: "en" | "ar"): string {
  return obj[lang];
}

export default function AuditPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const S = ADMIN_LABELS.sections;
  const [filterAction, setFilterAction] = useState<string>("");
  const [filterResourceType, setFilterResourceType] = useState<string>("");

  const { data: auditData, isLoading } = useAuditEvents({
    action: filterAction || undefined,
    resource_type: filterResourceType || undefined,
  });

  const { data: verifyData } = useAuditVerify();

  const events = auditData?.events ?? [];
  const chainValid = verifyData?.chain_valid ?? true;

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
          {t(S.audit, language)}
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
          {isAr ? "سجل التدقيق الثابت مع سلسلة تجزئة SHA-256" : "Immutable audit log with SHA-256 hash chain verification"}
        </p>
      </div>

      {/* Chain Verification Banner */}
      {verifyData && (
        <div style={{
          padding: "12px 20px", borderRadius: 8, marginBottom: 24,
          background: chainValid ? "#F0FDF4" : "#FEF2F2",
          border: `1px solid ${chainValid ? "#BBF7D0" : "#FECACA"}`,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              {chainValid ? (
                <path d="M4 10l4 4 8-9" stroke="#15803D" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              ) : (
                <path d="M4 4l12 12M16 4L4 16" stroke="#B91C1C" strokeWidth="2" strokeLinecap="round"/>
              )}
            </svg>
            <span style={{ fontSize: "0.875rem", fontWeight: 600, color: chainValid ? "#15803D" : "#B91C1C" }}>
              {chainValid
                ? (isAr ? "سلسلة التدقيق صحيحة" : "Audit Chain Valid")
                : (isAr ? "سلسلة التدقيق مكسورة" : "Audit Chain Broken")}
            </span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "#64748B" }}>
            {verifyData.verified_events}/{verifyData.total_events} {isAr ? "تم التحقق" : "verified"}
            {verifyData.first_break_at != null && (
              <span style={{ color: "#B91C1C", marginLeft: 8 }}>
                {isAr ? "كسر في التسلسل" : "Break at seq"} #{verifyData.first_break_at}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem", color: "#475569", background: "#FFFFFF" }}
        >
          <option value="">{isAr ? "كل الإجراءات" : "All Actions"}</option>
          <option value="login">Login</option>
          <option value="workflow_started">Workflow Started</option>
          <option value="workflow_completed">Workflow Completed</option>
          <option value="decision_created">Decision Created</option>
          <option value="user_created">User Created</option>
          <option value="simulation_run">Simulation Run</option>
        </select>

        <select
          value={filterResourceType}
          onChange={(e) => setFilterResourceType(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem", color: "#475569", background: "#FFFFFF" }}
        >
          <option value="">{isAr ? "كل الموارد" : "All Resources"}</option>
          <option value="workflow">Workflow</option>
          <option value="decision">Decision</option>
          <option value="user">User</option>
          <option value="policy">Policy</option>
        </select>
      </div>

      {/* Events Table */}
      <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: "center", color: "#94A3B8", fontSize: "0.875rem" }}>
            {isAr ? "جاري التحميل..." : "Loading audit events..."}
          </div>
        ) : events.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "#94A3B8", fontSize: "0.875rem" }}>
            {isAr ? "لا توجد أحداث تدقيق" : "No audit events recorded yet"}
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #E2E8F0" }}>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {isAr ? "الوقت" : "Timestamp"}
                </th>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {isAr ? "الممثل" : "Actor"}
                </th>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {isAr ? "الإجراء" : "Action"}
                </th>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {isAr ? "المورد" : "Resource"}
                </th>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {isAr ? "التجزئة" : "Hash"}
                </th>
                <th style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  #
                </th>
              </tr>
            </thead>
            <tbody>
              {events.map((event: AuditEventResponse) => (
                <tr key={event.id} style={{ borderBottom: "1px solid #F1F5F9" }}>
                  <td style={{ padding: "10px 16px", color: "#475569", whiteSpace: "nowrap" }}>
                    {new Date(event.created_at).toLocaleString(isAr ? "ar-SA" : "en-US", { dateStyle: "short", timeStyle: "short" })}
                  </td>
                  <td style={{ padding: "10px 16px", color: "#0F172A" }}>
                    {event.actor_email ?? event.actor_id ?? "system"}
                  </td>
                  <td style={{ padding: "10px 16px" }}>
                    <span style={{
                      padding: "2px 8px", borderRadius: 10, fontSize: "0.6875rem", fontWeight: 600,
                      background: "#EFF6FF", color: "#1D4ED8",
                    }}>
                      {event.action.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ padding: "10px 16px", color: "#475569" }}>
                    {event.resource_type ? `${event.resource_type}/${event.resource_id?.slice(0, 8) ?? ""}` : "—"}
                  </td>
                  <td style={{ padding: "10px 16px", fontFamily: "monospace", fontSize: "0.6875rem", color: "#94A3B8" }}>
                    {event.event_hash.slice(0, 12)}...
                  </td>
                  <td style={{ padding: "10px 16px", color: "#64748B", fontSize: "0.75rem" }}>
                    {event.sequence}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Stats */}
      {auditData && (
        <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "#94A3B8" }}>
          <span>{auditData.total} {isAr ? "حدث" : "events"}</span>
          <span>{isAr ? "صفحة" : "Page"} {auditData.page}/{Math.max(1, Math.ceil(auditData.total / auditData.page_size))}</span>
        </div>
      )}
    </div>
  );
}
