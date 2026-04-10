"use client";
/**
 * Impact Observatory | مرصد الأثر — Enterprise Admin Hooks
 * Layer: UI (L6) — Data fetching for Enterprise Administration
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  LoginRequest,
  TokenResponse,
  UserContext,
  TenantListResponse,
  TenantCreate,
  TenantResponse,
  UserListResponse,
  UserCreate,
  UserResponse,
  RoleListResponse,
  RoleCreate,
  RoleResponse,
  RoleAssign,
  WorkflowListResponse,
  WorkflowCreate,
  WorkflowResponse,
  WorkflowRunRequest,
  WorkflowRunListResponse,
  WorkflowRunResponse,
  WorkflowStepApproval,
  AuditListResponse,
  AuditChainVerification,
  PolicyRuleListResponse,
  PolicyRuleCreate,
  PolicyRuleResponse,
  EnterpriseDashboardMetrics,
} from "@/types/admin";

// ── Private fetch helper (mirrors api.ts pattern) ──
const BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

async function adminFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ── Query Keys ──
const ADMIN_KEYS = {
  auth: ["admin", "auth"] as const,
  currentUser: ["admin", "auth", "me"] as const,
  tenants: (params?: Record<string, string | number>) => ["admin", "tenants", params] as const,
  tenant: (id: string) => ["admin", "tenant", id] as const,
  users: (params?: Record<string, string | number>) => ["admin", "users", params] as const,
  user: (id: string) => ["admin", "user", id] as const,
  roles: ["admin", "roles"] as const,
  workflows: (params?: Record<string, string>) => ["admin", "workflows", params] as const,
  workflow: (id: string) => ["admin", "workflow", id] as const,
  workflowRuns: (params?: Record<string, string | number>) => ["admin", "workflow-runs", params] as const,
  workflowRun: (id: string) => ["admin", "workflow-run", id] as const,
  auditEvents: (params?: Record<string, string>) => ["admin", "audit", "events", params] as const,
  auditVerify: ["admin", "audit", "verify"] as const,
  auditStats: ["admin", "audit", "stats"] as const,
  policies: (params?: Record<string, string>) => ["admin", "policies", params] as const,
  dashboard: ["admin", "dashboard"] as const,
};

// ══════════════════════════════════════════════════════════════════════════════
// Authentication
// ══════════════════════════════════════════════════════════════════════════════

export function useEnterpriseLogin() {
  return useMutation({
    mutationFn: (body: LoginRequest) =>
      adminFetch<TokenResponse>("/api/v1/enterprise/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: ADMIN_KEYS.currentUser,
    queryFn: () => adminFetch<UserContext>("/api/v1/enterprise/auth/me"),
    staleTime: 10 * 60_000,
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Tenants
// ══════════════════════════════════════════════════════════════════════════════

export function useTenants(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ADMIN_KEYS.tenants(params as Record<string, string | number> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.page != null) qs.set("page", String(params.page));
      if (params?.page_size != null) qs.set("page_size", String(params.page_size));
      const q = qs.toString();
      return adminFetch<TenantListResponse>(`/api/v1/enterprise/tenants${q ? `?${q}` : ""}`);
    },
    staleTime: 5 * 60_000,
  });
}

export function useTenant(tenantId: string | null) {
  return useQuery({
    queryKey: ADMIN_KEYS.tenant(tenantId ?? ""),
    queryFn: () => adminFetch<TenantResponse>(`/api/v1/enterprise/tenants/${tenantId!}`),
    enabled: !!tenantId,
  });
}

export function useCreateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TenantCreate) =>
      adminFetch<TenantResponse>("/api/v1/enterprise/tenants", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "tenants"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Users
// ══════════════════════════════════════════════════════════════════════════════

export function useUsers(params?: { page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ADMIN_KEYS.users(params as Record<string, string | number> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.page != null) qs.set("page", String(params.page));
      if (params?.page_size != null) qs.set("page_size", String(params.page_size));
      const q = qs.toString();
      return adminFetch<UserListResponse>(`/api/v1/enterprise/users${q ? `?${q}` : ""}`);
    },
    staleTime: 5 * 60_000,
  });
}

export function useUser(userId: string | null) {
  return useQuery({
    queryKey: ADMIN_KEYS.user(userId ?? ""),
    queryFn: () => adminFetch<UserResponse>(`/api/v1/enterprise/users/${userId!}`),
    enabled: !!userId,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserCreate) =>
      adminFetch<UserResponse>("/api/v1/enterprise/users", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Roles
// ══════════════════════════════════════════════════════════════════════════════

export function useRoles() {
  return useQuery({
    queryKey: ADMIN_KEYS.roles,
    queryFn: () => adminFetch<RoleListResponse>("/api/v1/enterprise/roles"),
    staleTime: 10 * 60_000,
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RoleCreate) =>
      adminFetch<RoleResponse>("/api/v1/enterprise/roles", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "roles"] });
    },
  });
}

export function useAssignRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RoleAssign) =>
      adminFetch<{ status: string }>("/api/v1/enterprise/roles/assign", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      qc.invalidateQueries({ queryKey: ["admin", "roles"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Workflows
// ══════════════════════════════════════════════════════════════════════════════

export function useWorkflows(params?: { workflow_type?: string }) {
  return useQuery({
    queryKey: ADMIN_KEYS.workflows(params as Record<string, string> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.workflow_type) qs.set("workflow_type", params.workflow_type);
      const q = qs.toString();
      return adminFetch<WorkflowListResponse>(`/api/v1/enterprise/workflows${q ? `?${q}` : ""}`);
    },
    staleTime: 5 * 60_000,
  });
}

export function useWorkflow(workflowId: string | null) {
  return useQuery({
    queryKey: ADMIN_KEYS.workflow(workflowId ?? ""),
    queryFn: () => adminFetch<WorkflowResponse>(`/api/v1/enterprise/workflows/${workflowId!}`),
    enabled: !!workflowId,
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkflowCreate) =>
      adminFetch<WorkflowResponse>("/api/v1/enterprise/workflows", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "workflows"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Workflow Runs
// ══════════════════════════════════════════════════════════════════════════════

export function useWorkflowRuns(params?: {
  workflow_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ADMIN_KEYS.workflowRuns(params as Record<string, string | number> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.workflow_id) qs.set("workflow_id", params.workflow_id);
      if (params?.status) qs.set("status", params.status);
      if (params?.page != null) qs.set("page", String(params.page));
      if (params?.page_size != null) qs.set("page_size", String(params.page_size));
      const q = qs.toString();
      return adminFetch<WorkflowRunListResponse>(
        `/api/v1/enterprise/workflow-runs${q ? `?${q}` : ""}`
      );
    },
    refetchInterval: 10_000,
  });
}

export function useWorkflowRun(runId: string | null) {
  return useQuery({
    queryKey: ADMIN_KEYS.workflowRun(runId ?? ""),
    queryFn: () => adminFetch<WorkflowRunResponse>(`/api/v1/enterprise/workflow-runs/${runId!}`),
    enabled: !!runId,
    refetchInterval: 10_000,
  });
}

export function useStartWorkflowRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WorkflowRunRequest) =>
      adminFetch<WorkflowRunResponse>("/api/v1/enterprise/workflow-runs", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "workflow-runs"] });
    },
  });
}

export function useApproveWorkflowStep() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ runId, body }: { runId: string; body: WorkflowStepApproval }) =>
      adminFetch<WorkflowRunResponse>(
        `/api/v1/enterprise/workflow-runs/${runId}/approve`,
        { method: "POST", body: JSON.stringify(body) }
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "workflow-runs"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Audit
// ══════════════════════════════════════════════════════════════════════════════

export function useAuditEvents(params?: {
  action?: string;
  resource_type?: string;
  actor_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ADMIN_KEYS.auditEvents(params as Record<string, string> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.action) qs.set("action", params.action);
      if (params?.resource_type) qs.set("resource_type", params.resource_type);
      if (params?.actor_id) qs.set("actor_id", params.actor_id);
      if (params?.date_from) qs.set("date_from", params.date_from);
      if (params?.date_to) qs.set("date_to", params.date_to);
      if (params?.page != null) qs.set("page", String(params.page));
      if (params?.page_size != null) qs.set("page_size", String(params.page_size));
      const q = qs.toString();
      return adminFetch<AuditListResponse>(`/api/v1/enterprise/audit/events${q ? `?${q}` : ""}`);
    },
    staleTime: 30_000,
  });
}

export function useAuditVerify() {
  return useQuery({
    queryKey: ADMIN_KEYS.auditVerify,
    queryFn: () => adminFetch<AuditChainVerification>("/api/v1/enterprise/audit/verify"),
    staleTime: 60_000,
  });
}

export function useAuditStats() {
  return useQuery({
    queryKey: ADMIN_KEYS.auditStats,
    queryFn: () => adminFetch<Record<string, unknown>>("/api/v1/enterprise/audit/stats"),
    staleTime: 30_000,
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Policies
// ══════════════════════════════════════════════════════════════════════════════

export function usePolicies(params?: { category?: string }) {
  return useQuery({
    queryKey: ADMIN_KEYS.policies(params as Record<string, string> | undefined),
    queryFn: () => {
      const qs = new URLSearchParams();
      if (params?.category) qs.set("category", params.category);
      const q = qs.toString();
      return adminFetch<PolicyRuleListResponse>(`/api/v1/enterprise/policies${q ? `?${q}` : ""}`);
    },
    staleTime: 5 * 60_000,
  });
}

export function useCreatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PolicyRuleCreate) =>
      adminFetch<PolicyRuleResponse>("/api/v1/enterprise/policies", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "policies"] });
    },
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// Dashboard
// ══════════════════════════════════════════════════════════════════════════════

export function useEnterpriseDashboard() {
  return useQuery({
    queryKey: ADMIN_KEYS.dashboard,
    queryFn: () => adminFetch<EnterpriseDashboardMetrics>("/api/v1/enterprise/dashboard"),
    refetchInterval: 30_000,
  });
}

export { ADMIN_KEYS };
