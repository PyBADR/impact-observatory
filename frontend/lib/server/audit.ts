/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — AUDIT LOGGING
 * ══════════════════════════════════════════════════════════════
 * Every API action produces an audit entry with SHA-256 hash.
 * Entries are immutable, append-only.
 * Production: replace in-memory store with append-only DB table.
 */

import { generateAuditId, sha256 } from './trace'

export interface AuditEntry {
  auditId: string
  traceId: string
  runId: string
  tenantId: string
  userId: string
  action: string
  endpoint: string
  method: string
  inputs: Record<string, unknown>
  status: 'success' | 'error' | 'forbidden'
  statusCode: number
  timestamp: string
  durationMs: number
  hash: string           // SHA-256 of (auditId + traceId + action + timestamp + inputs)
  previousHash: string   // Chain link to previous entry
  metadata: Record<string, unknown>
}

/** In-memory audit log — production: Vercel Postgres / append-only table */
const auditLog: AuditEntry[] = []
let lastHash = 'genesis_0000000000000000000000000000000000000000000000000000000000000000'

export function createAuditEntry(params: {
  traceId: string
  runId: string
  tenantId: string
  userId: string
  action: string
  endpoint: string
  method: string
  inputs: Record<string, unknown>
  status: 'success' | 'error' | 'forbidden'
  statusCode: number
  durationMs: number
  metadata?: Record<string, unknown>
}): AuditEntry {
  const auditId = generateAuditId()
  const timestamp = new Date().toISOString()

  const hashInput = `${auditId}|${params.traceId}|${params.action}|${timestamp}|${JSON.stringify(params.inputs)}`
  const hash = sha256(hashInput)

  const entry: AuditEntry = {
    auditId,
    traceId: params.traceId,
    runId: params.runId,
    tenantId: params.tenantId,
    userId: params.userId,
    action: params.action,
    endpoint: params.endpoint,
    method: params.method,
    inputs: params.inputs,
    status: params.status,
    statusCode: params.statusCode,
    timestamp,
    durationMs: params.durationMs,
    hash,
    previousHash: lastHash,
    metadata: params.metadata || {},
  }

  auditLog.push(entry)
  lastHash = hash

  return entry
}

export function getAuditEntry(auditId: string): AuditEntry | undefined {
  return auditLog.find(e => e.auditId === auditId)
}

export function getAuditEntriesByTrace(traceId: string): AuditEntry[] {
  return auditLog.filter(e => e.traceId === traceId)
}

export function getAuditEntriesByRun(runId: string): AuditEntry[] {
  return auditLog.filter(e => e.runId === runId)
}

export function getAuditEntriesByTenant(tenantId: string, limit = 100): AuditEntry[] {
  return auditLog.filter(e => e.tenantId === tenantId).slice(-limit)
}

export function getAuditLogSize(): number {
  return auditLog.length
}

/** Verify chain integrity */
export function verifyAuditChain(): { valid: boolean; brokenAt?: number } {
  for (let i = 1; i < auditLog.length; i++) {
    if (auditLog[i].previousHash !== auditLog[i - 1].hash) {
      return { valid: false, brokenAt: i }
    }
  }
  return { valid: true }
}
