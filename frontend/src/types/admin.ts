/**
 * Impact Observatory | مرصد الأثر — Enterprise Multi-Tenant Admin Types
 *
 * TypeScript interfaces aligned to Pydantic schemas in backend/src/schemas/enterprise.py
 * These types drive admin dashboards, tenant management, user/role RBAC, workflows, and audit.
 */

// ══════════════════════════════════════════════════════════════════════════════
// Auth Types
// ══════════════════════════════════════════════════════════════════════════════

export interface LoginRequest {
  email: string;
  password: string;
  tenant_slug?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  tenant_id: string;
  tenant_name: string;
  roles: string[];
}

export interface JWTPayload {
  sub: string; // user_id
  email: string;
  role: string; // legacy role field (backward compat)
  org: string; // tenant_id
  tenant_id: string;
  tenant_slug: string;
  roles: string[];
  permissions: string[];
  iat: number;
  exp: number;
}

export interface UserContext {
  user_id: string;
  email: string;
  tenant_id: string;
  tenant_slug: string;
  role: string;
  roles: string[];
  permissions: string[];
}

// ══════════════════════════════════════════════════════════════════════════════
// Tenant Types
// ══════════════════════════════════════════════════════════════════════════════

export interface TenantCreate {
  name: string;
  name_ar?: string;
  slug: string;
  domain?: string;
  tier: "trial" | "standard" | "enterprise";
  max_users: number;
  max_workflows_per_month: number;
  settings_json?: Record<string, unknown>;
}

export interface TenantUpdate {
  name?: string;
  name_ar?: string;
  domain?: string;
  status?: "active" | "suspended" | "trial" | "deactivated";
  tier?: "trial" | "standard" | "enterprise";
  max_users?: number;
  max_workflows_per_month?: number;
  settings_json?: Record<string, unknown>;
}

export interface TenantResponse {
  id: string;
  name: string;
  name_ar?: string;
  slug: string;
  domain?: string;
  status: string;
  tier: string;
  max_users: number;
  max_workflows_per_month: number;
  settings_json?: Record<string, unknown>;
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface TenantListResponse {
  tenants: TenantResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// User Types
// ══════════════════════════════════════════════════════════════════════════════

export interface UserCreate {
  email: string;
  name: string;
  name_ar?: string;
  password: string;
  role_names: string[];
  mfa_enabled: boolean;
  metadata_json?: Record<string, unknown>;
}

export interface UserInvite {
  email: string;
  name: string;
  name_ar?: string;
  role_names?: string[];
}

export interface UserUpdate {
  name?: string;
  name_ar?: string;
  status?: "active" | "invited" | "suspended" | "deactivated";
  mfa_enabled?: boolean;
  metadata_json?: Record<string, unknown>;
}

export interface UserResponse {
  id: string;
  tenant_id: string;
  email: string;
  name: string;
  name_ar?: string;
  status: string;
  mfa_enabled: boolean;
  last_login_at?: string;
  roles: RoleResponse[];
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  users: UserResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// Role & Permission Types
// ══════════════════════════════════════════════════════════════════════════════

export interface PermissionSpec {
  resource: string;
  action: string;
}

export interface RoleCreate {
  name: string;
  name_ar?: string;
  description?: string;
  permissions: PermissionSpec[];
}

export interface RoleUpdate {
  name?: string;
  name_ar?: string;
  description?: string;
  permissions?: PermissionSpec[];
}

export interface PermissionResponse {
  id: string;
  resource: string;
  action: string;
}

export interface RoleResponse {
  id: string;
  tenant_id: string;
  name: string;
  name_ar?: string;
  description?: string;
  is_system: boolean;
  permissions: PermissionResponse[];
  created_at: string;
}

export interface RoleAssign {
  user_id: string;
  role_id: string;
}

export interface RoleListResponse {
  roles: RoleResponse[];
  total: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// Workflow Types
// ══════════════════════════════════════════════════════════════════════════════

export interface WorkflowStepDef {
  step_name: string;
  step_type: "auto" | "hitl" | "conditional" | "api_call";
  config?: Record<string, unknown>;
  timeout_seconds?: number;
  required_permission?: string;
}

export interface WorkflowCreate {
  name: string;
  name_ar?: string;
  workflow_type: "underwriting" | "claims" | "risk_assessment" | "policy_renewal" | "fraud_review" | "custom";
  description?: string;
  steps: WorkflowStepDef[];
  config_json?: Record<string, unknown>;
}

export interface WorkflowUpdate {
  name?: string;
  name_ar?: string;
  description?: string;
  is_active?: boolean;
  steps?: WorkflowStepDef[];
  config_json?: Record<string, unknown>;
}

export interface WorkflowResponse {
  id: string;
  tenant_id: string;
  name: string;
  name_ar?: string;
  workflow_type: string;
  description?: string;
  version: number;
  is_active: boolean;
  steps_json?: Record<string, unknown>[];
  config_json?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListResponse {
  workflows: WorkflowResponse[];
  total: number;
}

export interface WorkflowRunRequest {
  workflow_id: string;
  input_json: Record<string, unknown>;
  run_id?: string;
}

export interface WorkflowStepApproval {
  decision: "approve" | "reject" | "return";
  reason?: string;
  metadata?: Record<string, unknown>;
}

export interface WorkflowStepResponse {
  id: string;
  step_index: number;
  step_name: string;
  step_type: string;
  status: string;
  input_json?: Record<string, unknown>;
  output_json?: Record<string, unknown>;
  decision_by?: string;
  decision_reason?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface WorkflowRunResponse {
  id: string;
  tenant_id: string;
  workflow_id: string;
  initiated_by: string;
  status: string;
  current_step: number;
  input_json?: Record<string, unknown>;
  output_json?: Record<string, unknown>;
  context_json?: Record<string, unknown>;
  error_message?: string;
  run_id?: string;
  steps: WorkflowStepResponse[];
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface WorkflowRunListResponse {
  runs: WorkflowRunResponse[];
  total: number;
  page: number;
  page_size: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// Audit Types
// ══════════════════════════════════════════════════════════════════════════════

export interface AuditEventResponse {
  id: string;
  tenant_id: string;
  actor_id?: string;
  actor_email?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  description?: string;
  before_json?: Record<string, unknown>;
  after_json?: Record<string, unknown>;
  metadata_json?: Record<string, unknown>;
  ip_address?: string;
  event_hash: string;
  prev_hash?: string;
  sequence: number;
  created_at: string;
}

export interface AuditQueryParams {
  action?: string;
  resource_type?: string;
  resource_id?: string;
  actor_id?: string;
  date_from?: string;
  date_to?: string;
  page: number;
  page_size: number;
}

export interface AuditListResponse {
  events: AuditEventResponse[];
  total: number;
  page: number;
  page_size: number;
  chain_valid: boolean;
}

export interface AuditChainVerification {
  tenant_id: string;
  total_events: number;
  verified_events: number;
  chain_valid: boolean;
  first_break_at?: number;
  verified_at: string;
}

// ══════════════════════════════════════════════════════════════════════════════
// Policy Rule Types
// ══════════════════════════════════════════════════════════════════════════════

export interface PolicyRuleCreate {
  name: string;
  name_ar?: string;
  category: "underwriting" | "claims" | "risk" | "compliance" | "fraud";
  condition_json?: Record<string, unknown>;
  action_json?: Record<string, unknown>;
  priority: number;
  is_active: boolean;
}

export interface PolicyRuleUpdate {
  name?: string;
  name_ar?: string;
  category?: "underwriting" | "claims" | "risk" | "compliance" | "fraud";
  condition_json?: Record<string, unknown>;
  action_json?: Record<string, unknown>;
  priority?: number;
  is_active?: boolean;
}

export interface PolicyRuleResponse {
  id: string;
  tenant_id: string;
  name: string;
  name_ar?: string;
  category: string;
  condition_json?: Record<string, unknown>;
  action_json?: Record<string, unknown>;
  priority: number;
  is_active: boolean;
  version: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyRuleListResponse {
  rules: PolicyRuleResponse[];
  total: number;
}

// ══════════════════════════════════════════════════════════════════════════════
// Dashboard Types
// ══════════════════════════════════════════════════════════════════════════════

export interface EnterpriseDashboardMetrics {
  tenant_id: string;
  users: {
    total: number;
    active: number;
    invited: number;
  };
  roles: {
    total: number;
    system: number;
    custom: number;
  };
  workflows: {
    definitions: number;
    active_runs: number;
    completed_this_month: number;
    awaiting_approval: number;
  };
  audit: {
    total_events: number;
    chain_valid: boolean;
    last_event?: AuditEventResponse;
  };
  policies: {
    total: number;
    active: number;
  };
}

// ══════════════════════════════════════════════════════════════════════════════
// UI Labels & Constants
// ══════════════════════════════════════════════════════════════════════════════

export const ADMIN_LABELS = {
  // Section headings
  sections: {
    tenants: { en: "Tenants", ar: "المستأجرون" },
    users: { en: "Users", ar: "المستخدمون" },
    roles: { en: "Roles", ar: "الأدوار" },
    workflows: { en: "Workflows", ar: "سير العمل" },
    audit: { en: "Audit", ar: "التدقيق" },
    policies: { en: "Policies", ar: "السياسات" },
    dashboard: { en: "Dashboard", ar: "لوحة التحكم" },
  },

  // Tenant status
  tenantStatus: {
    active: { en: "Active", ar: "نشط" },
    suspended: { en: "Suspended", ar: "معلق" },
    trial: { en: "Trial", ar: "تجريبي" },
    deactivated: { en: "Deactivated", ar: "معطل" },
  },

  // Tenant tier
  tenantTier: {
    trial: { en: "Trial", ar: "تجريبي" },
    standard: { en: "Standard", ar: "معياري" },
    enterprise: { en: "Enterprise", ar: "مؤسسي" },
  },

  // User status
  userStatus: {
    active: { en: "Active", ar: "نشط" },
    invited: { en: "Invited", ar: "مدعو" },
    suspended: { en: "Suspended", ar: "معلق" },
    deactivated: { en: "Deactivated", ar: "معطل" },
  },

  // Workflow types
  workflowType: {
    underwriting: { en: "Underwriting", ar: "الاكتتاب" },
    claims: { en: "Claims", ar: "المطالبات" },
    risk_assessment: { en: "Risk Assessment", ar: "تقييم المخاطر" },
    policy_renewal: { en: "Policy Renewal", ar: "تجديد الوثيقة" },
    fraud_review: { en: "Fraud Review", ar: "مراجعة الاحتيال" },
    custom: { en: "Custom", ar: "مخصص" },
  },

  // Workflow step types
  stepType: {
    auto: { en: "Automatic", ar: "تلقائي" },
    hitl: { en: "Human-in-the-Loop", ar: "إدخال بشري" },
    conditional: { en: "Conditional", ar: "شرطي" },
    api_call: { en: "API Call", ar: "استدعاء API" },
  },

  // Workflow run status
  workflowStatus: {
    pending: { en: "Pending", ar: "قيد الانتظار" },
    running: { en: "Running", ar: "قيد التنفيذ" },
    approved: { en: "Approved", ar: "موافق عليه" },
    rejected: { en: "Rejected", ar: "مرفوض" },
    completed: { en: "Completed", ar: "اكتمل" },
    failed: { en: "Failed", ar: "فشل" },
  },

  // Step approval decisions
  stepDecision: {
    approve: { en: "Approve", ar: "موافقة" },
    reject: { en: "Reject", ar: "رفض" },
    return: { en: "Return for Review", ar: "الإرجاع للمراجعة" },
  },

  // Policy rule categories
  policyCategory: {
    underwriting: { en: "Underwriting", ar: "الاكتتاب" },
    claims: { en: "Claims", ar: "المطالبات" },
    risk: { en: "Risk", ar: "المخاطرة" },
    compliance: { en: "Compliance", ar: "الامتثال" },
    fraud: { en: "Fraud", ar: "الاحتيال" },
  },

  // Common actions
  actions: {
    create: { en: "Create", ar: "إنشاء" },
    edit: { en: "Edit", ar: "تحرير" },
    delete: { en: "Delete", ar: "حذف" },
    save: { en: "Save", ar: "حفظ" },
    cancel: { en: "Cancel", ar: "إلغاء" },
    view: { en: "View", ar: "عرض" },
    manage: { en: "Manage", ar: "إدارة" },
    assign: { en: "Assign", ar: "تعيين" },
    revoke: { en: "Revoke", ar: "إلغاء" },
  },

  // Audit-related labels
  audit: {
    chainValid: { en: "Chain Valid", ar: "السلسلة صحيحة" },
    chainBroken: { en: "Chain Broken", ar: "السلسلة معطوبة" },
    verified: { en: "Verified", ar: "التحقق" },
    action: { en: "Action", ar: "الإجراء" },
    resource: { en: "Resource", ar: "المورد" },
    actor: { en: "Actor", ar: "المنفذ" },
    timestamp: { en: "Timestamp", ar: "الطابع الزمني" },
  },

  // Form field labels
  fields: {
    email: { en: "Email", ar: "البريد الإلكتروني" },
    name: { en: "Name", ar: "الاسم" },
    nameAr: { en: "Arabic Name", ar: "الاسم بالعربية" },
    password: { en: "Password", ar: "كلمة المرور" },
    slug: { en: "Slug", ar: "الرابط النصي" },
    domain: { en: "Domain", ar: "المجال" },
    tier: { en: "Tier", ar: "المستوى" },
    maxUsers: { en: "Max Users", ar: "أقصى مستخدمين" },
    maxWorkflows: { en: "Max Workflows/Month", ar: "أقصى سير عمل/الشهر" },
    status: { en: "Status", ar: "الحالة" },
    mfaEnabled: { en: "MFA Enabled", ar: "MFA مفعل" },
    description: { en: "Description", ar: "الوصف" },
    permissions: { en: "Permissions", ar: "الأذونات" },
    priority: { en: "Priority", ar: "الأولوية" },
    isActive: { en: "Active", ar: "نشط" },
  },

  // Dashboard metrics
  metrics: {
    totalUsers: { en: "Total Users", ar: "إجمالي المستخدمين" },
    activeUsers: { en: "Active Users", ar: "المستخدمون النشطون" },
    totalRoles: { en: "Total Roles", ar: "إجمالي الأدوار" },
    totalWorkflows: { en: "Total Workflows", ar: "إجمالي سير العمل" },
    activeRuns: { en: "Active Runs", ar: "التشغيلات النشطة" },
    totalEvents: { en: "Total Events", ar: "إجمالي الأحداث" },
    totalPolicies: { en: "Total Policies", ar: "إجمالي السياسات" },
  },
} as const;
