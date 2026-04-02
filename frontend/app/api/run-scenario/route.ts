import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest, getEnvironment } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { createAuditEntry } from '@/lib/server/audit'
import { generateTraceId } from '@/lib/server/trace'
import { executeScenario } from '@/lib/server/execution'

export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  const startTime = Date.now()
  const auth = authenticateRequest(req)
  const env = getEnvironment()

  // Auth check — required for run endpoints
  if (!auth.authenticated) {
    return NextResponse.json(
      {
        error: 'Authentication required',
        code: 'AUTH_REQUIRED',
        hint: 'Provide X-IO-API-Key header or Authorization: Bearer <key>',
      },
      { status: 401 }
    )
  }

  // RBAC check
  const denied = enforcePermission(auth.role, 'run_scenarios')
  if (denied) {
    createAuditEntry({
      traceId: generateTraceId(),
      runId: '',
      tenantId: auth.tenantId,
      userId: auth.userId,
      action: 'run_scenario_denied',
      endpoint: '/api/run-scenario',
      method: 'POST',
      inputs: {},
      status: 'forbidden',
      statusCode: 403,
      durationMs: Date.now() - startTime,
    })
    return NextResponse.json({ error: denied, code: 'FORBIDDEN' }, { status: 403 })
  }

  // Parse body
  let body: { scenarioId?: string; severity?: number; analysisMode?: string }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body', code: 'INVALID_INPUT' },
      { status: 400 }
    )
  }

  // Validate inputs
  if (!body.scenarioId || typeof body.scenarioId !== 'string') {
    return NextResponse.json(
      { error: 'scenarioId is required (string)', code: 'INVALID_INPUT' },
      { status: 400 }
    )
  }

  const severity = typeof body.severity === 'number' ? body.severity : 0.5
  if (severity < 0 || severity > 1) {
    return NextResponse.json(
      { error: 'severity must be between 0 and 1', code: 'INVALID_INPUT' },
      { status: 400 }
    )
  }

  // Execute
  try {
    const result = executeScenario(
      {
        scenarioId: body.scenarioId,
        severity,
        analysisMode: body.analysisMode === 'probabilistic' ? 'probabilistic' : 'deterministic',
      },
      auth,
      env,
    )

    return NextResponse.json(result)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown execution error'

    createAuditEntry({
      traceId: generateTraceId(),
      runId: '',
      tenantId: auth.tenantId,
      userId: auth.userId,
      action: 'run_scenario_error',
      endpoint: '/api/run-scenario',
      method: 'POST',
      inputs: { scenarioId: body.scenarioId, severity },
      status: 'error',
      statusCode: 500,
      durationMs: Date.now() - startTime,
      metadata: { error: message },
    })

    return NextResponse.json(
      { error: message, code: 'EXECUTION_ERROR' },
      { status: 500 }
    )
  }
}
