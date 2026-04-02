/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — ROLE-BASED ACCESS CONTROL (RBAC)
 * ══════════════════════════════════════════════════════════════
 * Roles: admin, analyst, viewer, api_service
 * Permissions: read_scenarios, run_scenarios, run_decisions,
 *              read_runs, read_audit, manage_users
 */

import type { Role } from './auth'

export type Permission =
  | 'read_scenarios'
  | 'run_scenarios'
  | 'run_decisions'
  | 'read_runs'
  | 'read_audit'
  | 'manage_users'
  | 'export_data'

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  admin: ['read_scenarios', 'run_scenarios', 'run_decisions', 'read_runs', 'read_audit', 'manage_users', 'export_data'],
  analyst: ['read_scenarios', 'run_scenarios', 'run_decisions', 'read_runs', 'read_audit', 'export_data'],
  viewer: ['read_scenarios', 'read_runs'],
  api_service: ['read_scenarios', 'run_scenarios', 'run_decisions', 'read_runs'],
}

export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false
}

export function getPermissions(role: Role): Permission[] {
  return ROLE_PERMISSIONS[role] || []
}

/** Enforce permission — returns error message or null */
export function enforcePermission(role: Role, permission: Permission): string | null {
  if (!hasPermission(role, permission)) {
    return `Forbidden: role '${role}' does not have '${permission}' permission`
  }
  return null
}
