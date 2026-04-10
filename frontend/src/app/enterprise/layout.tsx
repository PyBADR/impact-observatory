"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Intelligence Layout
 * Layer: UI (L6) — Shell for all /enterprise/* pages
 */
import { useState } from "react";
import { useAppStore } from "@/store/app-store";

const NAV_ITEMS = [
  { key: "dashboard", href: "/enterprise", label: "Dashboard", label_ar: "لوحة القيادة" },
  { key: "decisions", href: "/enterprise/decision", label: "Decisions", label_ar: "القرارات" },
  { key: "simulate", href: "/enterprise/simulate", label: "Simulation", label_ar: "المحاكاة" },
  { key: "admin", href: "/enterprise/admin", label: "Admin", label_ar: "الإدارة" },
] as const;

export default function EnterpriseLayout({ children }: { children: React.ReactNode }) {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC", fontFamily: isAr ? "'Noto Sans Arabic', system-ui, sans-serif" : "Inter, system-ui, sans-serif", direction: isAr ? "rtl" : "ltr" }}>
      {/* Top Bar */}
      <header style={{ background: "#FFFFFF", borderBottom: "1px solid #E2E8F0", padding: "0 24px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button onClick={() => setNavOpen(!navOpen)} style={{ background: "none", border: "none", cursor: "pointer", padding: 4, display: "flex", alignItems: "center" }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 5h14M3 10h14M3 15h14" stroke="#475569" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
          <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
            <span style={{ fontSize: "1.125rem", fontWeight: 700, color: "#0F172A" }}>Impact Observatory</span>
            <span style={{ fontSize: "0.75rem", fontWeight: 500, color: "#1D4ED8", letterSpacing: "0.04em", textTransform: "uppercase" as const }}>Enterprise</span>
          </div>
        </div>
        <nav style={{ display: "flex", gap: 4 }}>
          {NAV_ITEMS.map((item) => (
            <a
              key={item.key}
              href={item.href}
              style={{ padding: "6px 14px", borderRadius: 6, fontSize: "0.875rem", fontWeight: 500, color: "#475569", textDecoration: "none", transition: "background 0.15s" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#F1F5F9")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {isAr ? item.label_ar : item.label}
            </a>
          ))}
        </nav>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 1440, margin: "0 auto", padding: "24px 24px 48px" }}>
        {children}
      </main>
    </div>
  );
}
