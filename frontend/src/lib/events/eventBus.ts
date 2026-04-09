import type {
  DomainEvent,
  EventType,
  EventHandler,
} from "./types";

/**
 * Queue Adapter interface — pluggable backend for event processing.
 *
 * Implementations:
 *   - InMemoryAdapter (default, single-process)
 *   - RedisAdapter    (production, cross-service via Redis/BullMQ)
 *   - HttpAdapter     (hybrid, Vercel → Railway via HTTP)
 */
export interface QueueAdapter {
  publish(event: DomainEvent): Promise<void>;
  subscribe<T extends EventType>(eventType: T, handler: EventHandler<T>): void;
  getProcessedCount(): number;
  getFailedCount(): number;
  drain(): Promise<void>;
}

// ── In-Memory Queue Adapter ──────────────────────────────────────────────────

class InMemoryAdapter implements QueueAdapter {
  private handlers = new Map<string, Array<(event: DomainEvent) => Promise<void>>>();
  private processedCount = 0;
  private failedCount = 0;
  private pending: Promise<void>[] = [];

  async publish(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.type) ?? [];
    for (const handler of handlers) {
      const p = Promise.resolve()
        .then(() => handler(event))
        .then(() => { this.processedCount++; })
        .catch((err) => {
          this.failedCount++;
          console.error(
            `[EventBus] Handler failed for ${event.type}:`,
            err instanceof Error ? err.message : err,
          );
        });
      this.pending.push(p);
    }
  }

  subscribe<T extends EventType>(eventType: T, handler: EventHandler<T>): void {
    const existing = this.handlers.get(eventType) ?? [];
    existing.push(handler as (event: DomainEvent) => Promise<void>);
    this.handlers.set(eventType, existing);
  }

  getProcessedCount(): number { return this.processedCount; }
  getFailedCount(): number { return this.failedCount; }

  async drain(): Promise<void> {
    await Promise.allSettled(this.pending);
    this.pending = [];
  }
}

// ── HTTP Adapter (Vercel → Railway) ──────────────────────────────────────────

class HttpAdapter implements QueueAdapter {
  private workerUrl: string;
  private localAdapter = new InMemoryAdapter();
  private publishCount = 0;
  private publishFailCount = 0;

  constructor(workerUrl: string) {
    this.workerUrl = workerUrl;
  }

  async publish(event: DomainEvent): Promise<void> {
    // Try to forward to Railway worker
    try {
      const res = await fetch(`${this.workerUrl}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(event),
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        this.publishCount++;
        return;
      }
    } catch {
      // Worker unreachable — fall back to local processing
    }

    // Fallback: process locally
    this.publishFailCount++;
    await this.localAdapter.publish(event);
  }

  subscribe<T extends EventType>(eventType: T, handler: EventHandler<T>): void {
    // Local fallback handlers
    this.localAdapter.subscribe(eventType, handler);
  }

  getProcessedCount(): number {
    return this.publishCount + this.localAdapter.getProcessedCount();
  }
  getFailedCount(): number {
    return this.publishFailCount + this.localAdapter.getFailedCount();
  }

  async drain(): Promise<void> {
    await this.localAdapter.drain();
  }
}

// ── Redis Adapter (Stub — implement when Redis is available) ─────────────────

class RedisAdapter implements QueueAdapter {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  constructor(_redisUrl: string) {
    console.log("[EventBus] RedisAdapter initialized (stub — not connected)");
  }

  async publish(_event: DomainEvent): Promise<void> {
    throw new Error("RedisAdapter not implemented — set EVENT_MODE=memory or EVENT_MODE=http");
  }

  subscribe<T extends EventType>(_eventType: T, _handler: EventHandler<T>): void {
    // No-op stub
  }

  getProcessedCount(): number { return 0; }
  getFailedCount(): number { return 0; }
  async drain(): Promise<void> { /* no-op */ }
}

// ── Adapter Factory ──────────────────────────────────────────────────────────

function createAdapter(): QueueAdapter {
  const mode = process.env.EVENT_MODE || "memory";

  if (mode === "http" && process.env.WORKER_URL) {
    return new HttpAdapter(process.env.WORKER_URL);
  }

  if (mode === "redis" && process.env.REDIS_URL) {
    return new RedisAdapter(process.env.REDIS_URL);
  }

  return new InMemoryAdapter();
}

// ── Singleton Event Bus ──────────────────────────────────────────────────────

let busInstance: EventBus | null = null;

export class EventBus {
  private queue: QueueAdapter;
  private eventLog: DomainEvent[] = [];
  private readonly maxLogSize = 1000;

  constructor(queue?: QueueAdapter) {
    this.queue = queue ?? createAdapter();
  }

  static getInstance(): EventBus {
    if (!busInstance) {
      busInstance = new EventBus();
    }
    return busInstance;
  }

  emit(event: DomainEvent): void {
    this.eventLog.push(event);
    if (this.eventLog.length > this.maxLogSize) {
      this.eventLog.splice(0, this.eventLog.length - this.maxLogSize);
    }
    // Fire-and-forget — don't block the caller
    this.queue.publish(event).catch(() => {});
  }

  on<T extends EventType>(eventType: T, handler: EventHandler<T>): void {
    this.queue.subscribe(eventType, handler);
  }

  async drain(): Promise<void> {
    await this.queue.drain();
  }

  getRecentEvents(limit = 50): DomainEvent[] {
    return this.eventLog.slice(-limit);
  }

  getStats(): {
    processed: number;
    failed: number;
    logSize: number;
    mode: string;
  } {
    return {
      processed: this.queue.getProcessedCount(),
      failed: this.queue.getFailedCount(),
      logSize: this.eventLog.length,
      mode: process.env.EVENT_MODE || "memory",
    };
  }
}

// ── Helper ───────────────────────────────────────────────────────────────────

export function eventId(): string {
  return `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
