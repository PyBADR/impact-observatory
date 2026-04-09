import type { TenantContext } from "@/types/tenant";

const DEFAULT_TENANT_ID = "tenant_default";
const DEFAULT_USER_ID = "system";

/**
 * Extract tenant context from an incoming request.
 *
 * Resolution order:
 *   1. X-Tenant-Id / X-User-Id / X-User-Role headers (API gateway / proxy)
 *   2. Request body fields (tenantId, userId, role)
 *   3. Defaults (single-tenant fallback)
 *
 * In production, step 1 would be set by an API gateway (Kong, AWS ALB, etc.)
 * after JWT validation. For now, we support all three for flexibility.
 */
export function extractTenantContext(
  headers: Headers,
  body?: Record<string, unknown>,
): TenantContext {
  // Header-based (preferred in production)
  const headerTenant = headers.get("x-tenant-id");
  const headerUser = headers.get("x-user-id");
  const headerRole = headers.get("x-user-role") as TenantContext["role"] | null;

  // Body-based (client-side convenience)
  const bodyTenant = body?.tenantId as string | undefined;
  const bodyUser = body?.userId as string | undefined;
  const bodyRole = body?.role as TenantContext["role"] | undefined;

  return {
    tenantId: headerTenant || bodyTenant || DEFAULT_TENANT_ID,
    userId: headerUser || bodyUser || DEFAULT_USER_ID,
    role: headerRole || bodyRole || "operator",
    orgName: (body?.orgName as string) || undefined,
  };
}

/**
 * Validate that a tenant context has the minimum required role.
 */
const ROLE_LEVELS: Record<TenantContext["role"], number> = {
  viewer: 0,
  analyst: 1,
  operator: 2,
  admin: 3,
};

export function hasMinimumRole(
  ctx: TenantContext,
  required: TenantContext["role"],
): boolean {
  return ROLE_LEVELS[ctx.role] >= ROLE_LEVELS[required];
}
