import { NextResponse } from "next/server";
import { EventBus } from "@/lib/events/eventBus";

export async function GET() {
  const bus = EventBus.getInstance();
  const stats = bus.getStats();
  const recent = bus.getRecentEvents(20).map((e) => ({
    id: e.id,
    type: e.type,
    tenantId: e.tenantId,
    correlationId: e.correlationId,
    timestamp: new Date(e.timestamp).toISOString(),
  }));

  return NextResponse.json({
    eventBus: stats,
    recentEvents: recent,
    timestamp: new Date().toISOString(),
  });
}
