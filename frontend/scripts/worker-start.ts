/**
 * Worker Entry Point — Railway deployment target.
 *
 * Runs the event-driven decision workers as a standalone Node process,
 * independent of the Next.js runtime. Includes a minimal HTTP health
 * check server for Railway's healthcheck probe.
 *
 * Usage:
 *   npx tsx scripts/worker-start.ts
 *   or after build: node dist/scripts/worker-start.js
 *
 * Environment:
 *   PORT              — health check port (default: 3001)
 *   EVENT_MODE        — "memory" | "redis" (default: "memory")
 *   NODE_ENV          — production | development
 *   WORKER_LOG_LEVEL  — "info" | "debug" | "error" (default: "info")
 */

import http from "node:http";

// ── Bootstrap ────────────────────────────────────────────────────────────────

const PORT = parseInt(process.env.PORT || "3001", 10);
const LOG_LEVEL = process.env.WORKER_LOG_LEVEL || "info";

function log(level: string, msg: string, data?: Record<string, unknown>) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    service: "decision-worker",
    msg,
    ...data,
  };
  console.log(JSON.stringify(entry));
}

async function main() {
  log("info", "Starting decision worker...", {
    nodeEnv: process.env.NODE_ENV,
    eventMode: process.env.EVENT_MODE || "memory",
    port: PORT,
  });

  // Import and initialize event bus + workers
  // Dynamic imports so path aliases resolve at runtime
  const { EventBus } = await import("../src/lib/events/eventBus");
  const { initializeWorkers } = await import("../src/lib/workers/decisionWorker");

  const bus = EventBus.getInstance();
  initializeWorkers();

  log("info", "Workers registered", { stats: bus.getStats() });

  // ── Health Check Server ─────────────────────────────────────────────────
  const server = http.createServer((req, res) => {
    const stats = bus.getStats();

    if (req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: "healthy",
        service: "decision-worker",
        uptime: process.uptime(),
        eventBus: stats,
        timestamp: new Date().toISOString(),
      }));
      return;
    }

    if (req.url === "/stats") {
      const recent = bus.getRecentEvents(20).map((e) => ({
        id: e.id,
        type: e.type,
        correlationId: e.correlationId,
        timestamp: new Date(e.timestamp).toISOString(),
      }));
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ stats, recentEvents: recent }));
      return;
    }

    res.writeHead(404);
    res.end("Not found");
  });

  server.listen(PORT, () => {
    log("info", `Health check server listening on :${PORT}`);
    log("info", "Decision worker ready — awaiting events");
  });

  // ── Graceful Shutdown ───────────────────────────────────────────────────
  const shutdown = async (signal: string) => {
    log("info", `Received ${signal}, draining events...`);
    await bus.drain();
    server.close();
    log("info", "Worker shutdown complete", { finalStats: bus.getStats() });
    process.exit(0);
  };

  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));
}

main().catch((err) => {
  log("error", "Worker failed to start", {
    error: err instanceof Error ? err.message : String(err),
  });
  process.exit(1);
});
