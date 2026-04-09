import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import type { EvaluationRecord, AuditEvent, TenantScenario } from "@/types/tenant";

/**
 * File-based persistence layer — tenant-scoped, JSON-backed.
 *
 * Data layout:
 *   .data/{tenantId}/evaluations.json
 *   .data/{tenantId}/audit.json
 *   .data/{tenantId}/scenarios.json
 *
 * This is the foundation layer. Swap for PostgreSQL/DynamoDB later
 * by implementing the same interface against a real DB client.
 */

const DATA_ROOT = join(process.cwd(), ".data");
const MAX_EVALUATIONS = 500;
const MAX_AUDIT_EVENTS = 2000;

function tenantDir(tenantId: string): string {
  const dir = join(DATA_ROOT, tenantId);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  return dir;
}

function readJSON<T>(path: string, fallback: T): T {
  if (!existsSync(path)) return fallback;
  try {
    return JSON.parse(readFileSync(path, "utf-8")) as T;
  } catch {
    return fallback;
  }
}

function writeJSON(path: string, data: unknown): void {
  writeFileSync(path, JSON.stringify(data, null, 2), "utf-8");
}

// ── Evaluations ──────────────────────────────────────────────────────────────

export function saveEvaluation(record: EvaluationRecord): void {
  const file = join(tenantDir(record.tenantId), "evaluations.json");
  const records = readJSON<EvaluationRecord[]>(file, []);
  records.push(record);
  // Keep only recent evaluations per tenant
  if (records.length > MAX_EVALUATIONS) {
    records.splice(0, records.length - MAX_EVALUATIONS);
  }
  writeJSON(file, records);
}

export function getEvaluations(
  tenantId: string,
  limit = 20,
): EvaluationRecord[] {
  const file = join(tenantDir(tenantId), "evaluations.json");
  const records = readJSON<EvaluationRecord[]>(file, []);
  return records.slice(-limit);
}

export function getEvaluationById(
  tenantId: string,
  id: string,
): EvaluationRecord | null {
  const file = join(tenantDir(tenantId), "evaluations.json");
  const records = readJSON<EvaluationRecord[]>(file, []);
  return records.find((r) => r.id === id) ?? null;
}

// ── Audit Events ─────────────────────────────────────────────────────────────

export function appendAuditEvent(event: AuditEvent): void {
  const file = join(tenantDir(event.tenantId), "audit.json");
  const events = readJSON<AuditEvent[]>(file, []);
  events.push(event);
  if (events.length > MAX_AUDIT_EVENTS) {
    events.splice(0, events.length - MAX_AUDIT_EVENTS);
  }
  writeJSON(file, events);
}

export function getAuditEvents(
  tenantId: string,
  opts?: { eventType?: string; entityId?: string; limit?: number },
): AuditEvent[] {
  const file = join(tenantDir(tenantId), "audit.json");
  let events = readJSON<AuditEvent[]>(file, []);
  if (opts?.eventType) {
    events = events.filter((e) => e.eventType === opts.eventType);
  }
  if (opts?.entityId) {
    events = events.filter((e) => e.entityId === opts.entityId);
  }
  return events.slice(-(opts?.limit ?? 50));
}

// ── Tenant Scenarios ─────────────────────────────────────────────────────────

export function saveTenantScenario(scenario: TenantScenario): void {
  const file = join(tenantDir(scenario.tenantId), "scenarios.json");
  const scenarios = readJSON<TenantScenario[]>(file, []);
  const idx = scenarios.findIndex((s) => s.id === scenario.id);
  if (idx >= 0) {
    scenarios[idx] = scenario;
  } else {
    scenarios.push(scenario);
  }
  writeJSON(file, scenarios);
}

export function getTenantScenarios(tenantId: string): TenantScenario[] {
  const file = join(tenantDir(tenantId), "scenarios.json");
  return readJSON<TenantScenario[]>(file, []);
}

// ── Metrics (cross-tenant summary) ───────────────────────────────────────────

export function getEvaluationCount(tenantId: string): number {
  const file = join(tenantDir(tenantId), "evaluations.json");
  return readJSON<EvaluationRecord[]>(file, []).length;
}
