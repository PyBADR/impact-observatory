import { NextRequest, NextResponse } from 'next/server'
import { authenticateRequest } from '@/lib/server/auth'
import { enforcePermission } from '@/lib/server/rbac'
import { gccScenarios, SCENARIO_GROUPS, type ScenarioGroup } from '@/lib/gcc-graph'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const auth = authenticateRequest(req)

  // Allow unauthenticated read for pilot (configurable)
  if (!auth.authenticated) {
    const env = process.env.IO_TIER || 'pilot'
    if (env === 'prod') {
      return NextResponse.json(
        { error: 'Authentication required', code: 'AUTH_REQUIRED' },
        { status: 401 }
      )
    }
  }

  if (auth.authenticated) {
    const denied = enforcePermission(auth.role, 'read_scenarios')
    if (denied) {
      return NextResponse.json({ error: denied, code: 'FORBIDDEN' }, { status: 403 })
    }
  }

  const scenarios = gccScenarios.map(s => ({
    id: s.id,
    title: s.title,
    titleAr: s.titleAr,
    group: s.group,
    description: s.description,
    descriptionAr: s.descriptionAr,
    timeHorizon: s.timeHorizon,
    timeHorizonAr: s.timeHorizonAr,
    engineId: s.engineId || s.id,
    shockCount: s.shocks.length,
    keyEntityCount: s.keyEntities?.length || 0,
  }))

  const groups = (Object.entries(SCENARIO_GROUPS) as [ScenarioGroup, { label: string; labelAr: string; icon: string }][]).map(([id, g]) => ({
    id,
    label: g.label,
    labelAr: g.labelAr,
    icon: g.icon,
  }))

  return NextResponse.json({
    scenarios,
    groups,
    total: scenarios.length,
    timestamp: new Date().toISOString(),
  })
}
