import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { getAuditEntry, getAuditEntriesByRun, getAuditEntriesByTrace } from '@/lib/server/audit'

export const dynamic = 'force-dynamic'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const auth = authenticateRequest(req)

  if (!auth.authenticated) {
    return NextResponse.json(
      { error: 'Authentication required', code: 'AUTH_REQUIRED' },
      { status: 401 }
    )
  }

  const denied = enforcePermission(auth.role, 'read_audit')
  if (denied) {
    return NextResponse.json({ error: denied, code: 'FORBIDDEN' }, { status: 403 })
  }

  const id = params.id

  // Try direct audit ID lookup first
  const entry = getAuditEntry(id)
  if (entry) {
    // Tenant isolation
    if (auth.role !== 'admin' && entry.tenantId !== auth.tenantId) {
      return NextResponse.json({ error: 'Not found', code: 'NOT_FOUND' }, { status: 404 })
    }
    return NextResponse.json({ audit: entry, type: 'single' })
  }

  // Try as run_id
  if (id.startsWith('io_run_')) {
    const entries = getAuditEntriesByRun(id)
    if (entries.length > 0) {
      const filtered = auth.role === 'admin' ? entries : entries.filter(e => e.tenantId === auth.tenantId)
      return NextResponse.json({ audit: filtered, type: 'by_run', runId: id })
    }
  }

  // Try as trace_id
  if (id.startsWith('io_trace_')) {
    const entries = getAuditEntriesByTrace(id)
    if (entries.length > 0) {
      const filtered = auth.role === 'admin' ? entries : entries.filter(e => e.tenantId === auth.tenantId)
      return NextResponse.json({ audit: filtered, type: 'by_trace', traceId: id })
    }
  }

  return NextResponse.json(
    { error: `Audit entry not found: ${id}`, code: 'NOT_FOUND' },
    { status: 404 }
  )
}
