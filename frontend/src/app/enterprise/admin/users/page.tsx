"use client";

import { useState } from "react";
import { useAppStore } from "@/store/app-store";
import { useUsers, useCreateUser } from "@/hooks/use-admin";
import { ADMIN_LABELS } from "@/types/admin";
import type { UserResponse } from "@/types/admin";

function t(obj: { en: string; ar: string }, lang: "en" | "ar"): string {
  return obj[lang];
}

const STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  active: { bg: "#DCFCE7", color: "#15803D" },
  invited: { bg: "#FEF3C7", color: "#B45309" },
  suspended: { bg: "#FEE2E2", color: "#B91C1C" },
  deactivated: { bg: "#F1F5F9", color: "#64748B" },
};

export default function UsersPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const S = ADMIN_LABELS.sections;
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", name: "", password: "", role_names: "ANALYST" });

  const { data: usersData, isLoading } = useUsers();
  const createMutation = useCreateUser();

  const users = usersData?.users ?? [];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(
      {
        email: form.email,
        name: form.name,
        password: form.password,
        role_names: [form.role_names],
        mfa_enabled: false,
      },
      {
        onSuccess: () => {
          setForm({ email: "", name: "", password: "", role_names: "ANALYST" });
          setShowForm(false);
        },
      }
    );
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0F172A", margin: 0 }}>
            {t(S.users, language)}
          </h1>
          <p style={{ fontSize: "0.875rem", color: "#475569", margin: "4px 0 0" }}>
            {isAr ? "إدارة المستخدمين والأدوار لهذا المستأجر" : "Manage users and role assignments for this tenant"}
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "8px 18px", borderRadius: 8, border: "none",
            background: "#1D4ED8", color: "#FFFFFF", fontSize: "0.8125rem",
            fontWeight: 600, cursor: "pointer",
          }}
        >
          {showForm ? (isAr ? "إلغاء" : "Cancel") : (isAr ? "إضافة مستخدم" : "Add User")}
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <form onSubmit={handleCreate} style={{
          background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0",
          padding: 20, marginBottom: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
        }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 150px", gap: 12, alignItems: "end" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748B", marginBottom: 4 }}>
                {isAr ? "البريد الإلكتروني" : "Email"}
              </label>
              <input
                type="email" required value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748B", marginBottom: 4 }}>
                {isAr ? "الاسم" : "Name"}
              </label>
              <input
                type="text" required value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748B", marginBottom: 4 }}>
                {isAr ? "كلمة المرور" : "Password"}
              </label>
              <input
                type="password" required minLength={8} value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem" }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "#64748B", marginBottom: 4 }}>
                {isAr ? "الدور" : "Role"}
              </label>
              <select
                value={form.role_names}
                onChange={(e) => setForm({ ...form, role_names: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", borderRadius: 6, border: "1px solid #E2E8F0", fontSize: "0.8125rem" }}
              >
                <option value="ADMIN">Admin</option>
                <option value="UNDERWRITER">Underwriter</option>
                <option value="CLAIMS_ADJUSTER">Claims Adjuster</option>
                <option value="ANALYST">Analyst</option>
                <option value="VIEWER">Viewer</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end" }}>
            <button
              type="submit"
              disabled={createMutation.isPending}
              style={{
                padding: "8px 24px", borderRadius: 6, border: "none",
                background: createMutation.isPending ? "#94A3B8" : "#15803D",
                color: "#FFFFFF", fontSize: "0.8125rem", fontWeight: 600, cursor: "pointer",
              }}
            >
              {createMutation.isPending ? (isAr ? "جاري الإنشاء..." : "Creating...") : (isAr ? "إنشاء" : "Create")}
            </button>
          </div>
        </form>
      )}

      {/* Users Table */}
      <div style={{ background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.08)" }}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: "center", color: "#94A3B8" }}>
            {isAr ? "جاري التحميل..." : "Loading users..."}
          </div>
        ) : users.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: "#94A3B8" }}>
            {isAr ? "لا يوجد مستخدمون" : "No users found"}
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #E2E8F0" }}>
                {[isAr ? "الاسم" : "Name", isAr ? "البريد" : "Email", isAr ? "الحالة" : "Status", isAr ? "الأدوار" : "Roles", isAr ? "آخر دخول" : "Last Login"].map((h) => (
                  <th key={h} style={{ padding: "10px 16px", textAlign: isAr ? "right" : "left", fontWeight: 600, color: "#64748B", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((user: UserResponse) => {
                const sc = STATUS_COLORS[user.status] ?? STATUS_COLORS.active;
                return (
                  <tr key={user.id} style={{ borderBottom: "1px solid #F1F5F9" }}>
                    <td style={{ padding: "10px 16px", fontWeight: 600, color: "#0F172A" }}>
                      {user.name}
                    </td>
                    <td style={{ padding: "10px 16px", color: "#475569" }}>
                      {user.email}
                    </td>
                    <td style={{ padding: "10px 16px" }}>
                      <span style={{
                        padding: "2px 8px", borderRadius: 10, fontSize: "0.6875rem",
                        fontWeight: 600, background: sc.bg, color: sc.color,
                      }}>
                        {user.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px 16px", color: "#475569" }}>
                      {user.roles.map((r) => r.name).join(", ") || "—"}
                    </td>
                    <td style={{ padding: "10px 16px", color: "#94A3B8", fontSize: "0.75rem" }}>
                      {user.last_login_at
                        ? new Date(user.last_login_at).toLocaleDateString(isAr ? "ar-SA" : "en-US")
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      {usersData && (
        <div style={{ marginTop: 12, fontSize: "0.75rem", color: "#94A3B8" }}>
          {usersData.total} {isAr ? "مستخدم" : "users"} · {isAr ? "صفحة" : "Page"} {usersData.page}/{Math.max(1, Math.ceil(usersData.total / usersData.page_size))}
        </div>
      )}
    </div>
  );
}
