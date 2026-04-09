"use client";

import { useAppStore } from "@/store/app-store";
import { useEnterpriseDashboard } from "@/hooks/use-admin";
import { ADMIN_LABELS } from "@/types/admin";

function t(obj: { en: string; ar: string }, lang: "en" | "ar"): string {
  return obj[lang];
}

export default function AdminDashboard() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const S = ADMIN_LABELS.sections;

  const { data: metrics, isLoading } = useEnterpriseDashboard();

  const cards = [
    {
      title: t(S.users, language),
      value: metrics?.users?.total ?? 0,
      sub: `${metrics?.users?.active ?? 0} ${isAr ? "نشط" : "active"}`,
      color: "#1D4ED8",
      bg: "#EFF6FF",
    },
    {
      title: t(S.roles, language),
      value: metrics?.roles?.total ?? 0,
      sub: `${metrics?.roles?.system ?? 0} ${isAr ? "نظام" : "system"} · ${metrics?.roles?.custom ?? 0} ${isAr ? "مخصص" : "custom"}`,
      color: "#7C3AED",
      bg: "#F5F3FF",
    },
    {
      title: t(S.workflows, language),
      value: metrics?.workflows?.definitions ?? 0,
      sub: `${metrics?.workflows?.active_runs ?? 0} ${isAr ? "تشغيل" : "running"} · ${metrics?.workflows?.awaiting_approval ?? 0} ${isAr ? "بانتظار" : "awaiting"}`,
      color: "#B45309",
      bg: "#FFFBEB",
    },
    {
      title: t(S.audit, language),
      value: metrics?.audit?.total_events ?? 0,
      sub: metrics?.audit?.chain_valid ? (isAr ? "سلسلة صحيحة" : "Chain valid") : (isAr ? "سلسلة مكسورة!" : "Chain broken!"),
      color: metrics?.audit?.chain_valid ? "#15803D" : "#B91C1C",
      bg: metrics?.audit?.chain_valid ? "#F0FDF4" : "#FEF2F2",
    },
    {
      title: t(S.policies, language),
      value: metrics?.policies?.total ?? 0,
      sub: `${metrics?.policies?.active ?? 0} ${isAr ? "نشطة" : "active"}`,
      color: "#0891B2",
      bg: "#ECFEFF",
    },
  ];

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
          {t(S.dashboard, language)}
        </h1>
        <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
          {isAr ? "نظرة عامة على منصة المستأجر المؤسسية" : "Enterprise tenant platform overview"}
        </p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 16, marginBottom: 32 }}>
        {cards.map((card) => (
          <div key={card.title} style={{
            background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0",
            padding: "20px 16px", boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
          }}>
            <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 8 }}>
              {card.title}
            </div>
            <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", marginBottom: 4 }}>
              {isLoading ? "—" : card.value}
            </div>
            <div style={{
              display: "inline-block", padding: "2px 8px", borderRadius: 10,
              fontSize: "0.6875rem", fontWeight: 600, background: card.bg, color: card.color,
            }}>
              {isLoading ? "..." : card.sub}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
        <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0F172A", margin: "0 0 16px" }}>
          {isAr ? "إجراءات سريعة" : "Quick Actions"}
        </h2>
        <div style={{ display: "flex", gap: 12 }}>
          {[
            { href: "/enterprise/admin/users", label: isAr ? "إدارة المستخدمين" : "Manage Users", icon: "👥" },
            { href: "/enterprise/simulate", label: isAr ? "تشغيل محاكاة" : "Run Simulation", icon: "⚡" },
            { href: "/enterprise/admin/audit", label: isAr ? "عرض التدقيق" : "View Audit Log", icon: "📋" },
          ].map((action) => (
            <a
              key={action.href}
              href={action.href}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "10px 20px", borderRadius: 8, border: "1px solid #E2E8F0",
                background: "#FAFBFC", textDecoration: "none", color: "#0F172A",
                fontSize: "0.8125rem", fontWeight: 500, transition: "background 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#F1F5F9")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "#FAFBFC")}
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
