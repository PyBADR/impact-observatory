"use client";

import Link from "next/link";
import { useAppStore } from "@/store/app-store";
const NAV_ITEMS = [
  { key: "dashboard", href: "/enterprise/admin", label: "Dashboard", label_ar: "لوحة التحكم" },
  { key: "users", href: "/enterprise/admin/users", label: "Users", label_ar: "المستخدمون" },
  { key: "roles", href: "/enterprise/admin/roles", label: "Roles", label_ar: "الأدوار" },
  { key: "workflows", href: "/enterprise/admin/workflows", label: "Workflows", label_ar: "سير العمل" },
  { key: "audit", href: "/enterprise/admin/audit", label: "Audit Log", label_ar: "سجل التدقيق" },
  { key: "policies", href: "/enterprise/admin/policies", label: "Policies", label_ar: "السياسات" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "#F8FAFC",
        direction: isAr ? "rtl" : "ltr",
      }}
    >
      {/* Sidebar Navigation */}
      <aside
        style={{
          width: 280,
          background: "#FFFFFF",
          borderRight: isAr ? "none" : "1px solid #E2E8F0",
          borderLeft: isAr ? "1px solid #E2E8F0" : "none",
          padding: "32px 0",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
          position: "fixed",
          height: "100vh",
          overflowY: "auto",
          [isAr ? "right" : "left"]: 0,
        }}
      >
        <div style={{ paddingLeft: isAr ? 0 : 20, paddingRight: isAr ? 20 : 0, marginBottom: 32 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0F172A", margin: 0 }}>
            Admin Panel
          </h2>
        </div>

        <nav>
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.key}
              href={item.href}
              style={{
                display: "block",
                padding: "12px 20px",
                color: "#475569",
                textDecoration: "none",
                fontSize: 14,
                fontWeight: 500,
                borderLeft: isAr ? "none" : "4px solid transparent",
                borderRight: isAr ? "4px solid transparent" : "none",
                marginLeft: isAr ? 0 : 0,
                marginRight: isAr ? 0 : 0,
                paddingLeft: isAr ? 0 : 20,
                paddingRight: isAr ? 20 : 0,
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLAnchorElement;
                el.style.background = "#F1F5F9";
                el.style.color = "#0F172A";
                el.style[isAr ? "borderRightColor" : "borderLeftColor"] = "#1D4ED8";
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLAnchorElement;
                el.style.background = "transparent";
                el.style.color = "#475569";
                el.style[isAr ? "borderRightColor" : "borderLeftColor"] = "transparent";
              }}
            >
              {language === "ar" ? item.label_ar : item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main
        style={{
          flex: 1,
          padding: "24px 40px 48px",
          marginLeft: isAr ? 0 : 280,
          marginRight: isAr ? 280 : 0,
          overflowY: "auto",
        }}
      >
        {children}
      </main>
    </div>
  );
}
