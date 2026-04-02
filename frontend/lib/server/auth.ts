/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — AUTHENTICATION
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

  // Master key from env — set IO_API_KEY in deployment config for production
  // Pilot fallback only active when IO_TIER !== 'prod'
  const tier = process.env.IO_TIER || 'pilot'
  const masterKey = process.env.IO_API_KEY || (tier !== 'prod' ? 'io_pilot_key_2026' : '')
  keys.set(masterKey, {
    tenantId: 'io_default',
    userId: 'admin@impact-observatory.ai',
    role: 'admin',
    workspace: 'default',
  })

  // Pilot demo key (read-only)
  const pilotKey = process.env.IO_PILOT_KEY || 'io_demo_readonly'
  keys.set(pilotKey, {
    tenantId: 'io_pilot',
    userId: 'pilot@impact-observatory.ai',
    role: 'viewer',
    workspace: 'pilot',
  })

  // Analyst key
  const analystKey = process.env.IO_ANALYST_KEY || ''
  if (analystKey) {
    keys.set(analystKey, {
      tenantId: 'io_default',
      userId: 'analyst@impact-observatory.ai',
      role: 'analyst',
      workspace: 'default',
    })
  }

  return keys
}

/**
 * Authenticate a request via API key header.
 * Header: X-IO-API-Key or Authorization: Bearer <key>
 */
export function authenticateRequest(req: NextRequest): AuthContext {
  // Check X-IO-API-Key header first
  let apiKey = req.headers.get('x-io-api-key')

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
  const env = process.env.IO_ENV || process.env.NODE_ENV
  if (env === 'production') return process.env.IO_TIER as 'pilot' | 'prod' || 'pilot'
  return 'dev'
}
