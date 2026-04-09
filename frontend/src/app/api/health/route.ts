import { NextResponse } from "next/server";
import { EventBus } from "@/lib/events/eventBus";

export async function GET() {
  const bus = EventBus.getInstance();
  const stats = bus.getStats();

  return NextResponse.json({
    status: "healthy",
    service: "impact-observatory-frontend",
    version: "4.0.0",
    runtime: "vercel",
    eventBus: stats,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
}
