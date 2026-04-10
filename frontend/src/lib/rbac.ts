/**
 * Impact Observatory | مرصد الأثر — Frontend RBAC (v4 §10)
 * Mirrors backend/app/core/rbac.py exactly.
 * 5 roles × 25 permissions.
 */

export type Role = "viewer" | "analyst" | "operator" | "admin" | "regulator";

export type Permission =
  | "create_scenario"
  | "launch_run"
  | "launch_run_with_overrides"
  | "read_financial"
  | "read_banking"
  | "read_insurance"
  | "read_fintech"
  | "read_decision"
  | "read_explanation"
  | "read_business_impact"
  | "read_timeline"
  | "read_regulatory_timeline"
  | "read_executive_explanation"
  | "override_thresholds"
  | "force_rerun"
  | "manage_manifests"
  | "archive_scenario"
  | "read_audit_logs"
  | "generate_compliance_report"
  // Operator Layer — decision management
  | "create_decision"    // ANALYST+
  | "execute_decision"   // OPERATOR+
  // Outcome Intelligence Layer
  | "read_outcome"       // ANALYST+
  | "record_outcome"     // OPERATOR+
  // ROI / Decision Value Layer
  | "read_value"         // ANALYST+
  | "compute_value";     // OPERATOR+

/** v4 §10.2 — Permission matrix (exact mirror of backend). */
const ROLE_PERMISSIONS: Record<Role, Set<Permission>> = {
  viewer: new Set([
    "read_financial",
    "read_banking",
    "read_insurance",
    "read_fintech",
    "read_explanation",
    "read_business_impact",
    "read_timeline",
    "read_regulatory_timeline",
    "read_executive_explanation",
  ]),
  analyst: new Set([
    "create_scenario",
    "launch_run",
    "read_financial",
    "read_banking",
    "read_insurance",
    "read_fintech",
    "read_decision",
    "read_explanation",
    "read_business_impact",
    "read_timeline",
    "read_regulatory_timeline",
    "read_executive_explanation",
    "create_decision",
    "read_outcome",
    "read_value",
  ]),
  operator: new Set([
    "create_scenario",
    "launch_run",
    "launch_run_with_overrides",
    "read_financial",
    "read_banking",
    "read_insurance",
    "read_fintech",
    "read_decision",
    "read_explanation",
    "read_business_impact",
    "read_timeline",
    "read_regulatory_timeline",
    "read_executive_explanation",
    "override_thresholds",
    "force_rerun",
    "create_decision",
    "execute_decision",
    "read_outcome",
    "record_outcome",
    "read_value",
    "compute_value",
  ]),
  admin: new Set([
    "create_scenario",
    "launch_run",
    "launch_run_with_overrides",
    "read_financial",
    "read_banking",
    "read_insurance",
    "read_fintech",
    "read_decision",
    "read_explanation",
    "read_business_impact",
    "read_timeline",
    "read_regulatory_timeline",
    "read_executive_explanation",
    "override_thresholds",
    "force_rerun",
    "manage_manifests",
    "archive_scenario",
    "read_audit_logs",
    "generate_compliance_report",
    "create_decision",
    "execute_decision",
    "read_outcome",
    "record_outcome",
    "read_value",
    "compute_value",
  ]),
  regulator: new Set([
    "create_scenario",
    "launch_run",
    "launch_run_with_overrides",
    "read_financial",
    "read_banking",
    "read_insurance",
    "read_fintech",
    "read_decision",
    "read_explanation",
    "read_business_impact",
    "read_timeline",
    "read_regulatory_timeline",
    "read_executive_explanation",
    "override_thresholds",
    "read_audit_logs",
    "generate_compliance_report",
    "create_decision",
    "execute_decision",
    "read_outcome",
    "record_outcome",
    "read_value",
    "compute_value",
  ]),
};

/** Check if a role has a specific permission. */
export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.has(permission) ?? false;
}

/** Get all permissions for a role. */
export function getPermissions(role: Role): Permission[] {
  return Array.from(ROLE_PERMISSIONS[role] ?? []);
}

/** Check if a role can access any of the given permissions. */
export function hasAnyPermission(
  role: Role,
  permissions: Permission[],
): boolean {
  return permissions.some((p) => hasPermission(role, p));
}
