/**
 * ══════════════════════════════════════════════════════════════
 * DEEVO SIM — AUTHENTICATION
 * ══════════════════════════════════════════════════════════════
 * API key authentication with tenant/workspace model.
 * Production: replace with JWT / OAuth2 / SAML.
 * Current: API key header validation + tenant extraction.
 */

import { NextRequest } from 'next/server'

export interface AuthContext {
  tenantId: string
  userId: string
  role: Role
  workspace: string
  authenticated: boolean
}

export type Role = 'admin' | 'analyst' | 'viewer' | 'api_service'

/** Environment-based API keys (set in Vercel dashboard or .env.local) */
function getValidApiKeys(): Map<string, { tenantId: string; userId: string; role: Role; workspace: string }> {
  const keys = new Map<string, { tenantId: string; userId: string; role: Role; workspace: string }>()

  // Master key from env — set DVO7_API_KEY in Vercel dashboard for production
  // Pilot fallback only active when DVO7_TIER !== 'prod'
  const tier = process.env.DVO7_TIER || 'pilot'
  const masterKey = process.env.DVO7_API_KEY || (tier !== 'prod' ? 'dvo7_pilot_key_2026' : '')
  keys.set(masterKey, {
    tenantId: 'dvo7_default',
    userId: 'admin@deevo.ai',
    role: 'admin',
    workspace: 'default',
  })

  // Pilot demo key (read-only)
  const pilotKey = process.env.DVO7_PILOT_KEY || 'dvo7_demo_readonly'
  keys.set(pilotKey, {
    tenantId: 'dvo7_pilot',
    userId: 'pilot@demo.deevo.ai',
    role: 'viewer',
    workspace: 'pilot',
  })

  // Analyst key
  const analystKey = process.env.DVO7_ANALYST_KEY || ''
  if (analystKey) {
    keys.set(analystKey, {
      tenantId: 'dvo7_default',
      userId: 'analyst@deevo.ai',
      role: 'analyst',
      workspace: 'default',
    })
  }

  return keys
}

/**
 * Authenticate a request via API key header.
 * Header: X-DVO7-API-Key or Authorization: Bearer <key>
 */
export function authenticateRequest(req: NextRequest): AuthContext {
  // Check X-DVO7-API-Key header first
  let apiKey = req.headers.get('x-dvo7-api-key')

  // Fall back to Authorization: Bearer
  if (!apiKey) {
    const authHeader = req.headers.get('authorization')
    if (authHeader?.startsWith('Bearer ')) {
      apiKey = authHeader.slice(7)
    }
  }

  if (!apiKey) {
    return { tenantId: '', userId: '', role: 'viewer', workspace: '', authenticated: false }
  }

  const validKeys = getValidApiKeys()
  const keyData = validKeys.get(apiKey)

  if (!keyData) {
    return { tenantId: '', userId: '', role: 'viewer', workspace: '', authenticated: false }
  }

  return { ...keyData, authenticated: true }
}

/** Check if a public endpoint (no auth required) */
export function isPublicEndpoint(pathname: string): boolean {
  const publicPaths = ['/api/health', '/api/version']
  return publicPaths.some(p => pathname.startsWith(p))
}

/** Get environment tier */
export function getEnvironment(): 'dev' | 'pilot' | 'prod' {
  const env = process.env.DVO7_ENV || process.env.NODE_ENV
  if (env === 'production') return process.env.DVO7_TIER as 'pilot' | 'prod' || 'pilot'
  return 'dev'
}
