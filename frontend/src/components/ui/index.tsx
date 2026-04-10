"use client";

/**
 * Impact Observatory | مرصد الأثر
 * Enterprise Design System Primitives
 *
 * Canonical components for all pages. Institutional, boardroom-grade.
 * No emoji. No decorative gradients. Strict spacing.
 */

import React from "react";

// ── Types ─────────────────────────────────────────────────────────────

export type Language = "en" | "ar";

export type Classification =
  | "CRITICAL"
  | "ELEVATED"
  | "MODERATE"
  | "LOW"
  | "NOMINAL";

export type AuthorityStatus =
  | "PROPOSED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "ESCALATED"
  | "EXECUTED"
  | "EXECUTION_PENDING"
  | "RETURNED"
  | "WITHDRAWN"
  | "REVOKED";

export type OperationalStatus = "operational" | "degraded" | "unavailable";

// ── Classification Badge ───────────────────────────────────────────────

const CLASSIFICATION_STYLES: Record<Classification, string> = {
  CRITICAL:  "bg-io-critical text-white",
  ELEVATED:  "bg-io-elevated text-white",
  MODERATE:  "bg-io-moderate text-white",
  LOW:       "bg-io-guarded text-white",
  NOMINAL:   "bg-io-stable  text-white",
};

// Enterprise status labels — 5-level ladder (Stable → Critical)
const CLASSIFICATION_LABELS_EN: Record<Classification, string> = {
  CRITICAL: "Critical",
  ELEVATED: "Severe",
  MODERATE: "Elevated",
  LOW: "Guarded",
  NOMINAL: "Stable",
};

const CLASSIFICATION_LABELS_AR: Record<Classification, string> = {
  CRITICAL: "حرج",
  ELEVATED: "شديد",
  MODERATE: "مرتفع",
  LOW: "محدود",
  NOMINAL: "مستقر",
};

export function ClassificationBadge({
  level,
  lang = "en",
  size = "sm",
}: {
  level: Classification;
  lang?: Language;
  size?: "xs" | "sm" | "md";
}) {
  const label =
    lang === "ar" ? CLASSIFICATION_LABELS_AR[level] : CLASSIFICATION_LABELS_EN[level];
  const sizeClass =
    size === "xs"
      ? "px-1.5 py-0.5 text-[10px]"
      : size === "md"
      ? "px-3 py-1 text-xs"
      : "px-2 py-0.5 text-[11px]";

  return (
    <span
      className={`inline-flex items-center font-semibold tracking-wide rounded ${sizeClass} ${CLASSIFICATION_STYLES[level]}`}
    >
      {label}
    </span>
  );
}

// ── Authority Status Badge ─────────────────────────────────────────────

const AUTHORITY_STATUS_STYLES: Record<AuthorityStatus, string> = {
  PROPOSED: "bg-slate-100 text-slate-700 border border-slate-300",
  UNDER_REVIEW: "bg-blue-50 text-blue-700 border border-blue-200",
  APPROVED: "bg-emerald-50 text-emerald-700 border border-emerald-200",
  REJECTED: "bg-red-50 text-red-700 border border-red-200",
  ESCALATED: "bg-purple-50 text-purple-700 border border-purple-200",
  EXECUTED: "bg-emerald-100 text-emerald-800 border border-emerald-300",
  EXECUTION_PENDING: "bg-amber-50 text-amber-700 border border-amber-200",
  RETURNED: "bg-orange-50 text-orange-700 border border-orange-200",
  WITHDRAWN: "bg-slate-100 text-slate-500 border border-slate-200",
  REVOKED: "bg-red-100 text-red-800 border border-red-300",
};

export function AuthorityStatusBadge({
  status,
}: {
  status: AuthorityStatus;
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide rounded ${AUTHORITY_STATUS_STYLES[status]}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

// ── Operational Status Indicator ───────────────────────────────────────

const OPERATIONAL_STYLES: Record<
  OperationalStatus,
  { dot: string; label: string; labelAr: string }
> = {
  operational: {
    dot: "bg-emerald-500",
    label: "Operational",
    labelAr: "يعمل",
  },
  degraded: {
    dot: "bg-amber-500",
    label: "Degraded",
    labelAr: "أداء متأثر",
  },
  unavailable: {
    dot: "bg-red-500",
    label: "Unavailable",
    labelAr: "غير متاح",
  },
};

export function OperationalIndicator({
  status,
  lang = "en",
}: {
  status: OperationalStatus;
  lang?: Language;
}) {
  const s = OPERATIONAL_STYLES[status];
  return (
    <div className="flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
      <span className="text-xs text-io-secondary">
        {lang === "ar" ? s.labelAr : s.label}
      </span>
    </div>
  );
}

// ── Domain Badge ───────────────────────────────────────────────────────

const DOMAIN_STYLES: Record<string, string> = {
  MARITIME: "bg-blue-50 text-blue-700 border border-blue-200",
  ENERGY: "bg-amber-50 text-amber-700 border border-amber-200",
  FINANCIAL: "bg-indigo-50 text-indigo-700 border border-indigo-200",
  CYBER: "bg-red-50 text-red-700 border border-red-200",
  AVIATION: "bg-sky-50 text-sky-700 border border-sky-200",
  TRADE: "bg-teal-50 text-teal-700 border border-teal-200",
};

export function DomainBadge({ domain }: { domain: string }) {
  const style = DOMAIN_STYLES[domain] ?? "bg-slate-50 text-slate-700 border border-slate-200";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded ${style}`}
    >
      {domain}
    </span>
  );
}

// ── Panel ──────────────────────────────────────────────────────────────

interface PanelProps {
  title?: string;
  titleAr?: string;
  lang?: Language;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  /** Remove padding from body (for tables / full-bleed content) */
  noPadding?: boolean;
  /** Subtle bg instead of white */
  muted?: boolean;
}

export function Panel({
  title,
  titleAr,
  lang = "en",
  action,
  children,
  className = "",
  noPadding = false,
  muted = false,
}: PanelProps) {
  const displayTitle = lang === "ar" && titleAr ? titleAr : title;
  const bg = muted ? "bg-io-bg" : "bg-io-surface";

  return (
    <div
      className={`${bg} border border-io-border rounded-xl shadow-sm overflow-hidden ${className}`}
    >
      {displayTitle && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-io-border">
          <h3 className="text-xs font-semibold text-io-secondary uppercase tracking-wider">
            {displayTitle}
          </h3>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={noPadding ? "" : "p-5"}>{children}</div>
    </div>
  );
}

// ── Section Header ─────────────────────────────────────────────────────

interface SectionHeaderProps {
  label: string;
  labelAr?: string;
  subtitle?: string;
  subtitleAr?: string;
  lang?: Language;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  label,
  labelAr,
  subtitle,
  subtitleAr,
  lang = "en",
  action,
  className = "",
}: SectionHeaderProps) {
  const displayLabel = lang === "ar" && labelAr ? labelAr : label;
  const displaySubtitle = lang === "ar" && subtitleAr ? subtitleAr : subtitle;

  return (
    <div className={`flex items-end justify-between mb-4 ${className}`}>
      <div>
        <p className="text-[11px] font-semibold text-io-secondary uppercase tracking-widest mb-0.5">
          {displayLabel}
        </p>
        {displaySubtitle && (
          <p className="text-sm text-io-secondary">{displaySubtitle}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

// ── KPI Card ───────────────────────────────────────────────────────────

interface KPICardProps {
  label: string;
  labelAr?: string;
  value: string;
  unit?: string;
  context?: string;
  contextAr?: string;
  classification?: Classification;
  lang?: Language;
  /** Left accent color override (CSS color string) */
  accentColor?: string;
}

export function KPICard({
  label,
  labelAr,
  value,
  unit,
  context,
  contextAr,
  classification,
  lang = "en",
  accentColor,
}: KPICardProps) {
  const displayLabel = lang === "ar" && labelAr ? labelAr : label;
  const displayContext = lang === "ar" && contextAr ? contextAr : context;

  const defaultAccent = classification
    ? {
        CRITICAL: "#991b1b",
        ELEVATED: "#b45309",
        MODERATE: "#ca8a04",
        LOW: "#15803d",
        NOMINAL: "#64748b",
      }[classification]
    : "#1D4ED8";

  const borderColor = accentColor ?? defaultAccent;

  return (
    <div
      className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm relative overflow-hidden"
      style={{ borderInlineStartWidth: "3px", borderInlineStartColor: borderColor }}
    >
      <p className="text-[11px] font-medium uppercase tracking-wider text-io-secondary mb-2">
        {displayLabel}
      </p>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tabular-nums text-io-primary leading-none">
          {value}
        </span>
        {unit && (
          <span className="text-xs text-io-secondary font-medium">{unit}</span>
        )}
      </div>
      {(displayContext || classification) && (
        <div className="flex items-center gap-2 mt-2">
          {classification && (
            <ClassificationBadge level={classification} lang={lang} size="xs" />
          )}
          {displayContext && (
            <span className="text-xs text-io-secondary">{displayContext}</span>
          )}
        </div>
      )}
    </div>
  );
}

// ── Data Row ───────────────────────────────────────────────────────────

export function DataRow({
  label,
  value,
  muted = false,
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  muted?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-io-border/50 last:border-0">
      <span className={`text-sm ${muted ? "text-io-secondary" : "text-io-secondary"}`}>
        {label}
      </span>
      <span
        className={`text-sm font-medium text-io-primary ${
          mono ? "font-mono tabular-nums" : ""
        }`}
      >
        {value}
      </span>
    </div>
  );
}

// ── Divider ────────────────────────────────────────────────────────────

export function Divider({ className = "" }: { className?: string }) {
  return <div className={`border-t border-io-border ${className}`} />;
}

// ── Empty State ────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  titleAr?: string;
  description: string;
  descriptionAr?: string;
  detail?: string;
  detailAr?: string;
  action?: React.ReactNode;
  lang?: Language;
  compact?: boolean;
}

export function EmptyState({
  icon,
  title,
  titleAr,
  description,
  descriptionAr,
  detail,
  detailAr,
  action,
  lang = "en",
  compact = false,
}: EmptyStateProps) {
  const displayTitle = lang === "ar" && titleAr ? titleAr : title;
  const displayDescription =
    lang === "ar" && descriptionAr ? descriptionAr : description;
  const displayDetail = lang === "ar" && detailAr ? detailAr : detail;

  return (
    <div
      className={`flex flex-col items-center text-center ${
        compact ? "py-10 px-6" : "py-20 px-8"
      } max-w-md mx-auto`}
    >
      {icon && (
        <div className="mb-5 w-14 h-14 rounded-xl bg-io-bg border border-io-border flex items-center justify-center text-io-secondary">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-io-primary mb-2">
        {displayTitle}
      </h3>
      <p className="text-sm text-io-secondary leading-relaxed mb-1">
        {displayDescription}
      </p>
      {displayDetail && (
        <p className="text-xs text-io-secondary/70 mb-5">{displayDetail}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ── Institutional Action Card ──────────────────────────────────────────
//
// Exact structure per spec:
//   Action Title (executive)
//   Impact (%) · Feasibility (%) · Execution Time · Estimated Mitigation Value (USD)
//   [Submit for Review]

interface ActionCardProps {
  rank: number;
  title: string;
  titleAr?: string;
  /** urgency 0–100 → displayed as Impact (%) */
  urgency?: number;
  /** confidence 0–1 → displayed as Feasibility (%) */
  confidence?: number;
  timeToEffectHours?: number;
  mitigationValueUSD?: number;
  costUSD?: number;
  lang?: Language;
  onReview?: () => void;
  isReviewing?: boolean;
}

function formatCompactUSD(value: number | undefined): string {
  if (value === undefined || value === null || !isFinite(value)) return "—";
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${Math.round(value).toLocaleString()}`;
}

function formatExecutionTime(hours: number | undefined): string {
  if (hours === undefined || hours === null || !isFinite(hours)) return "—";
  if (hours >= 168) return `${Math.round(hours / 168)}w`;
  if (hours >= 24) return `${Math.round(hours / 24)}d`;
  return `${Math.round(hours)}h`;
}

function urgencyClassification(urgency: number | undefined): Classification {
  if (!urgency) return "NOMINAL";
  if (urgency >= 80) return "CRITICAL";
  if (urgency >= 50) return "ELEVATED";
  if (urgency >= 20) return "MODERATE";
  return "LOW";
}

export function InstitutionalActionCard({
  rank,
  title,
  titleAr,
  urgency,
  confidence,
  timeToEffectHours,
  mitigationValueUSD,
  costUSD,
  lang = "en",
  onReview,
  isReviewing = false,
}: ActionCardProps) {
  const displayTitle = lang === "ar" && titleAr ? titleAr : title;
  const classification = urgencyClassification(urgency);

  // Exact fields per spec
  const impactPct =
    urgency !== undefined && isFinite(urgency)
      ? `${Math.round(urgency)}%`
      : "—";
  const feasibilityPct =
    confidence !== undefined && isFinite(confidence)
      ? `${Math.round(confidence <= 1 ? confidence * 100 : confidence)}%`
      : "—";
  const executionTime = formatExecutionTime(timeToEffectHours);
  const mitigationValue = formatCompactUSD(mitigationValueUSD);

  const metrics = lang === "ar"
    ? [
        { label: "الأثر", value: impactPct },
        { label: "قابلية التنفيذ", value: feasibilityPct },
        { label: "وقت التنفيذ", value: executionTime },
        { label: "قيمة التخفيف المقدّرة", value: mitigationValue },
      ]
    : [
        { label: "Impact", value: impactPct },
        { label: "Feasibility", value: feasibilityPct },
        { label: "Execution Time", value: executionTime },
        { label: "Estimated Mitigation Value", value: mitigationValue },
      ];

  return (
    <div className="bg-io-surface border border-io-border rounded-xl overflow-hidden shadow-sm">
      {/* Header: rank + title + status badge */}
      <div className="flex items-start gap-4 px-5 py-4 border-b border-io-border/60">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-io-bg border border-io-border flex items-center justify-center mt-0.5">
          <span className="text-xs font-bold text-io-primary tabular-nums">{rank}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm font-semibold text-io-primary leading-snug">{displayTitle}</p>
            <ClassificationBadge level={classification} lang={lang} size="xs" />
          </div>
        </div>
      </div>

      {/* Metrics: Impact / Feasibility / Execution Time / Mitigation Value */}
      <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-io-border bg-io-bg/40">
        {metrics.map((m) => (
          <div key={m.label} className="px-4 py-3">
            <p className="text-[10px] font-medium uppercase tracking-wider text-io-secondary mb-1 leading-tight">
              {m.label}
            </p>
            <p className="text-sm font-bold text-io-primary tabular-nums">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Footer: cost + CTA */}
      {(costUSD !== undefined || onReview) && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-io-border">
          {costUSD !== undefined ? (
            <p className="text-xs text-io-secondary">
              {lang === "ar" ? "التكلفة التقديرية" : "Estimated Cost"}{" "}
              <span className="font-semibold text-io-primary">{formatCompactUSD(costUSD)}</span>
            </p>
          ) : (
            <span />
          )}
          {onReview && (
            <button
              onClick={onReview}
              disabled={isReviewing}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isReviewing
                ? lang === "ar"
                  ? "جاري الإرسال..."
                  : "Submitting..."
                : lang === "ar"
                ? "إرسال للمراجعة"
                : "Submit for Review"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Page Container ─────────────────────────────────────────────────────

export function PageContainer({
  children,
  className = "",
  width = "xl",
}: {
  children: React.ReactNode;
  className?: string;
  width?: "md" | "lg" | "xl" | "full";
}) {
  const maxW =
    width === "md"
      ? "max-w-4xl"
      : width === "lg"
      ? "max-w-6xl"
      : width === "xl"
      ? "max-w-7xl"
      : "w-full";

  return (
    <div className={`${maxW} mx-auto px-6 lg:px-10 ${className}`}>
      {children}
    </div>
  );
}

// ── Sector Stress Panel ────────────────────────────────────────────────

interface SectorStressPanelProps {
  title: string;
  titleAr?: string;
  classification: Classification;
  stressPercent: number;
  metrics: { label: string; labelAr?: string; value: string }[];
  lang?: Language;
  onClick?: () => void;
}

export function SectorStressPanel({
  title,
  titleAr,
  classification,
  stressPercent,
  metrics,
  lang = "en",
  onClick,
}: SectorStressPanelProps) {
  const displayTitle = lang === "ar" && titleAr ? titleAr : title;

  return (
    <div
      onClick={onClick}
      className={`bg-io-surface border border-io-border rounded-xl p-5 shadow-sm ${
        onClick ? "cursor-pointer hover:border-io-accent/40 transition-colors" : ""
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-io-secondary uppercase tracking-wider">{displayTitle}</h4>
        <ClassificationBadge level={classification} lang={lang} size="xs" />
      </div>
      {/* Index format: X / 100 per spec */}
      <div className="flex items-baseline gap-1 mb-4">
        <span className="text-2xl font-bold tabular-nums text-io-primary leading-none">
          {Math.round(stressPercent * 100)}
        </span>
        <span className="text-sm font-medium text-io-secondary">/ 100</span>
      </div>
      <div className="space-y-2">
        {metrics.map((m, i) => {
          const displayLabel =
            lang === "ar" && m.labelAr ? m.labelAr : m.label;
          return (
            <div key={i} className="flex justify-between items-center">
              <span className="text-xs text-io-secondary">{displayLabel}</span>
              <span className="text-xs font-medium text-io-primary tabular-nums">
                {m.value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Graph Layer Filter Chip ────────────────────────────────────────────

export function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
        active
          ? "bg-io-accent text-white border-io-accent"
          : "bg-io-surface text-io-secondary border-io-border hover:border-io-accent/40 hover:text-io-primary"
      }`}
    >
      {label}
    </button>
  );
}

// ── Inline Loader ──────────────────────────────────────────────────────

export function InlineLoader({
  label = "Loading…",
  labelAr,
  lang = "en",
}: {
  label?: string;
  labelAr?: string;
  lang?: Language;
}) {
  const display = lang === "ar" && labelAr ? labelAr : label;
  return (
    <div className="flex items-center gap-2 text-io-secondary text-sm py-2">
      <svg
        className="w-4 h-4 animate-spin text-io-accent"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <span>{display}</span>
    </div>
  );
}
