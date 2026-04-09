import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";

/**
 * Event persistence — append-only log of domain events per tenant.
 * Stored at .data/{tenantId}/events.json
 */

const DATA_ROOT = join(process.cwd(), ".data");
const MAX_EVENTS = 2000;

interface PersistedEvent {
  id: string;
  type: string;
  correlationId: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

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

export function appendEventRecord(tenantId: string, event: PersistedEvent): void {
  const file = join(tenantDir(tenantId), "events.json");
  const events = readJSON<PersistedEvent[]>(file, []);
  events.push(event);
  if (events.length > MAX_EVENTS) {
    events.splice(0, events.length - MAX_EVENTS);
  }
  writeJSON(file, events);
}

export function getEventRecords(
  tenantId: string,
  opts?: { type?: string; correlationId?: string; limit?: number },
): PersistedEvent[] {
  const file = join(tenantDir(tenantId), "events.json");
  let events = readJSON<PersistedEvent[]>(file, []);
  if (opts?.type) events = events.filter((e) => e.type === opts.type);
  if (opts?.correlationId) events = events.filter((e) => e.correlationId === opts.correlationId);
  return events.slice(-(opts?.limit ?? 50));
}
