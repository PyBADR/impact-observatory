"use client";

/**
 * Impact Observatory | مرصد الأثر — Authority Detail Panel
 *
 * Expanded detail view for a single DecisionAuthority envelope.
 * Shows: proposal info, review state, approval/rejection, execution,
 * linked outcome/value, and full audit timeline.
 *
 * Rendered when a user clicks an item in AuthorityQueuePanel.
 * Persona-aware: actions rendered based on PERSONA_AUTHORITY_CAPABILITIES.
 */

import React, { useEffect, useMemo } from "react";
import { useAuthorityStore } from "@/store/authority-store";
import { useAppStore } from "@/store/app-store";
import { AuthorityAuditTimeline } from "./AuthorityAuditTimeline";
import {
  PERSONA_AUTHORITY_CAPABILITIES,
  type AuthorityStatus,
  type AuthorityActor,
  type DecisionAuthority,
} from "@/types/authority";
import type { Language } from "@/types/observatory";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AS_ADP  = ReturnType<typeof useAuthorityStore.getState>;
type AppS_ADP = ReturnType<typeof useAppStore.getState>;
const selectAuthorities_ADP   = (s: AS_ADP)   => s.authorities;
const selectLoadByAuthority_ADP = (s: AS_ADP) => s.loadByAuthority;
const selectPersona_ADP       = (s: AppS_ADP) => s.persona;

// ─── Field Row ────────────────────────────────────────────────────────────

function Field({ label, value, mono }: { label: string; value: string | null; mono?: boolean }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 py-1">
      <span className="text-[10px] font-semibold text-io-secondary uppercase tracking-wider w-28 shrink-0">
        {label}
      </span>
      <span className={`text-xs text-io-primary ${mono ? "font-mono text-[11px]" : ""}`}>
        {value}
      </span>
    </div>
  );
}

// ─── Status Lifecycle Visualization ───────────────────────────────────────

const LIFECYCLE_STAGES: AuthorityStatus[] = [
  "PROPOSED", "UNDER_REVIEW", "APPROVED", "EXECUTION_PENDING", "EXECUTED",
];

function LifecycleBar({ current, lang }: { current: AuthorityStatus; lang: Language }) {
  const isAr = lang === "ar";
  const currentIdx = LIFECYCLE_STAGES.indexOf(current);
  const isTerminalOff = currentIdx === -1; // status not in happy path

  return (
    <div className="flex items-center gap-1 py-2">
      {LIFECYCLE_STAGES.map((stage, idx) => {
        let color = "bg-gray-200 text-gray-400";
        if (stage === current) {
          color = "bg-io-accent text-white";
        } else if (!isTerminalOff && idx < currentIdx) {
          color = "bg-emerald-200 text-emerald-700";
        }

        return (
          <React.Fragment key={stage}>
            {idx > 0 && (
              <div className={`h-px w-4 ${idx <= currentIdx && !isTerminalOff ? "bg-emerald-300" : "bg-gray-200"}`} />
            )}
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-bold ${color}`}>
              {stage.replace(/_/g, " ")}
            </span>
          </React.Fragment>
        );
      })}

      {/* If off the happy path, show the actual status */}
      {isTerminalOff && (
        <>
          <div className="h-px w-4 bg-red-200" />
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-700 border border-red-200">
            {current.replace(/_/g, " ")}
          </span>
        </>
      )}
    </div>
  );
}

// ─── Main: Authority Detail Panel ─────────────────────────────────────────

interface AuthorityDetailPanelProps {
  authorityId: string;
  lang: Language;
  onClose?: () => void;
}

export function AuthorityDetailPanel({ authorityId, lang, onClose }: AuthorityDetailPanelProps) {
  const isAr = lang === "ar";
  const persona         = useAppStore(selectPersona_ADP);
  const authoritiesMap  = useAuthorityStore(selectAuthorities_ADP);
  const loadByAuthority = useAuthorityStore(selectLoadByAuthority_ADP);
  const authority       = useMemo(
    () => authoritiesMap.get(authorityId) ?? null,
    [authoritiesMap, authorityId],
  );
  const capabilities = PERSONA_AUTHORITY_CAPABILITIES[persona];

  // Refresh this authority from backend on mount
  useEffect(() => {
    loadByAuthority(authorityId);
  }, [authorityId, loadByAuthority]);

  if (!authority) {
    return (
      <div className="p-6 text-center text-sm text-io-secondary">
        {isAr ? "لم يتم العثور على سجل الصلاحية" : "Authority record not found"}
      </div>
    );
  }

  const showHashChain = capabilities?.can_view_audit_trail ?? false;

  return (
    <div className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-io-border bg-gradient-to-r from-io-accent/5 to-transparent flex items-start justify-between">
        <div>
          <h2 className="text-sm font-bold text-io-primary flex items-center gap-2">
            <span className="text-base">⚖️</span>
            {isAr ? "تفاصيل الصلاحية" : "Authority Detail"}
          </h2>
          <p className="text-[10px] text-io-secondary font-mono mt-0.5">
            {authority.authority_id}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-io-secondary hover:text-io-primary text-lg leading-none"
          >
            ×
          </button>
        )}
      </div>

      {/* Lifecycle Bar */}
      <div className="px-5 py-3 border-b border-io-border overflow-x-auto">
        <LifecycleBar current={authority.authority_status} lang={lang} />
      </div>

      {/* Fields */}
      <div className="px-5 py-4 space-y-0 border-b border-io-border">
        {/* Proposal Section */}
        <p className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
          {isAr ? "الاقتراح" : "Proposal"}
        </p>
        <Field label={isAr ? "القرار" : "Decision"} value={authority.decision_id} mono />
        <Field label={isAr ? "المقترح" : "Proposed By"} value={`${authority.proposed_by} (${authority.proposed_by_role})`} />
        <Field label={isAr ? "التبرير" : "Rationale"} value={authority.proposal_rationale} />
        <Field label={isAr ? "الأولوية" : "Priority"} value={`P${authority.priority}`} />
        <Field label={isAr ? "المراجعة" : "Revision"} value={`#${authority.revision_number}`} />
        {authority.escalation_level > 0 && (
          <Field label={isAr ? "التصعيد" : "Escalation"} value={`Level ${authority.escalation_level}`} />
        )}

        {/* Review Section */}
        {authority.reviewer_id && (
          <>
            <div className="h-3" />
            <p className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
              {isAr ? "المراجعة" : "Review"}
            </p>
            <Field label={isAr ? "المراجع" : "Reviewer"} value={`${authority.reviewer_id} (${authority.reviewer_role ?? ""})`} />
            <Field label={isAr ? "بدأ" : "Started"} value={authority.review_started_at} mono />
          </>
        )}

        {/* Authority Decision Section */}
        {authority.authority_actor_id && (
          <>
            <div className="h-3" />
            <p className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
              {isAr ? "قرار الصلاحية" : "Authority Decision"}
            </p>
            <Field label={isAr ? "بواسطة" : "Decided By"} value={`${authority.authority_actor_id} (${authority.authority_actor_role ?? ""})`} />
            <Field label={isAr ? "التاريخ" : "Decided At"} value={authority.authority_decided_at} mono />
            <Field label={isAr ? "المبرر" : "Rationale"} value={authority.authority_rationale} />
          </>
        )}

        {/* Execution Section */}
        {authority.executed_by && (
          <>
            <div className="h-3" />
            <p className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
              {isAr ? "التنفيذ" : "Execution"}
            </p>
            <Field label={isAr ? "المنفذ" : "Executed By"} value={`${authority.executed_by} (${authority.executed_by_role ?? ""})`} />
            <Field label={isAr ? "التاريخ" : "At"} value={authority.executed_at} mono />
            <Field label={isAr ? "النتيجة" : "Result"} value={authority.execution_result} />
          </>
        )}

        {/* Linkage */}
        {(authority.linked_outcome_id || authority.linked_value_id) && (
          <>
            <div className="h-3" />
            <p className="text-[10px] font-bold text-io-secondary uppercase tracking-wider mb-2">
              {isAr ? "الروابط" : "Linkage"}
            </p>
            <Field label={isAr ? "النتيجة" : "Outcome"} value={authority.linked_outcome_id} mono />
            <Field label={isAr ? "القيمة" : "Value"} value={authority.linked_value_id} mono />
          </>
        )}
      </div>

      {/* Audit Timeline */}
      <div className="px-5 py-4">
        <AuthorityAuditTimeline
          authorityId={authorityId}
          lang={lang}
          showHashChain={showHashChain}
          maxEvents={showHashChain ? undefined : 5}
        />
      </div>
    </div>
  );
}
