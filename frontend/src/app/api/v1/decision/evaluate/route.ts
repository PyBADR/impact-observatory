import { NextResponse } from "next/server";
import {
  evaluateMacroDecision,
  getEvaluationHistory,
  pollEvaluation,
} from "@/lib/orchestrators/decisionOrchestrator";
import { extractTenantContext } from "@/lib/tenant/context";
import { getAuditEvents } from "@/lib/persistence/store";
import { getEventRecords } from "@/lib/persistence/eventStore";
import { EventBus } from "@/lib/events/eventBus";
import type { MacroInput, Entity } from "@/types/decision";

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { macro, entities, scenario } = body as {
    macro: MacroInput;
    entities: Entity[];
    scenario?: string;
  };

  if (!macro || !entities?.length) {
    return NextResponse.json(
      { error: "macro and entities[] are required" },
      { status: 400 },
    );
  }

  const tenant = extractTenantContext(req.headers, body);
  const asyncMode = body.async === true;

  const result = await evaluateMacroDecision({
    macro,
    entities,
    scenario,
    tenant,
    async: asyncMode,
  });

  // For async mode, return 202 Accepted
  if (asyncMode) {
    return NextResponse.json(result, { status: 202 });
  }

  return NextResponse.json(result);
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const tenantId = url.searchParams.get("tenantId") || "tenant_default";
  const view = url.searchParams.get("view") || "evaluations";
  const limit = parseInt(url.searchParams.get("limit") || "20", 10);

  // Poll for async evaluation result
  if (view === "poll") {
    const evalId = url.searchParams.get("evaluationId");
    if (!evalId) {
      return NextResponse.json({ error: "evaluationId required" }, { status: 400 });
    }
    const result = pollEvaluation(evalId);
    if (!result) {
      return NextResponse.json({ status: "processing", evaluationId: evalId });
    }
    return NextResponse.json(result);
  }

  // Audit events
  if (view === "audit") {
    const eventType = url.searchParams.get("eventType") || undefined;
    const events = getAuditEvents(tenantId, { eventType, limit });
    return NextResponse.json({ events, count: events.length });
  }

  // Domain event log
  if (view === "events") {
    const type = url.searchParams.get("type") || undefined;
    const correlationId = url.searchParams.get("correlationId") || undefined;
    const events = getEventRecords(tenantId, { type, correlationId, limit });
    return NextResponse.json({ events, count: events.length });
  }

  // Event bus stats
  if (view === "stats") {
    const bus = EventBus.getInstance();
    return NextResponse.json({
      eventBus: bus.getStats(),
      recentEvents: bus.getRecentEvents(10).map((e) => ({
        id: e.id,
        type: e.type,
        correlationId: e.correlationId,
        timestamp: new Date(e.timestamp).toISOString(),
      })),
    });
  }

  // Default: evaluation history
  const evaluations = getEvaluationHistory(tenantId, limit);
  return NextResponse.json({ evaluations, count: evaluations.length });
}
