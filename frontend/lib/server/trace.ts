/**
 * ══════════════════════════════════════════════════════════════
 * IMPACT OBSERVATORY — TRACE & ID GENERATION
 * ══════════════════════════════════════════════════════════════
 * Every run produces: trace_id, run_id, audit_id
 * Format: io_{type}_{timestamp}_{random}
 */

import crypto from 'crypto'

export function generateTraceId(): string {
  const ts = Date.now().toString(36)
  const rand = crypto.randomBytes(6).toString('hex')
  return `io_trace_${ts}_${rand}`
}

export function generateRunId(): string {
  const ts = Date.now().toString(36)
  const rand = crypto.randomBytes(6).toString('hex')
  return `io_run_${ts}_${rand}`
}

export function generateAuditId(): string {
  const ts = Date.now().toString(36)
  const rand = crypto.randomBytes(6).toString('hex')
  return `io_audit_${ts}_${rand}`
}

export function sha256(data: string): string {
  return crypto.createHash('sha256').update(data).digest('hex')
}
