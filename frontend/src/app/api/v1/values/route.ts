import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const EMPTY = { values: [], count: 0 };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  const url     = new URL(req.url);
  const qs      = url.search;

  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/values${qs}`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data?.values) && data.values.length > 0) {
          return NextResponse.json(data);
        }
      }
    } catch {
      // fall through to in-memory
    }
  }

  const sp    = url.searchParams;
  const items = serverStore.values.list({
    outcome_id:  sp.get("outcome_id")  ?? undefined,
    decision_id: sp.get("decision_id") ?? undefined,
    run_id:      sp.get("run_id")      ?? undefined,
    limit:       sp.has("limit") ? Number(sp.get("limit")) : undefined,
  });
  return NextResponse.json({ values: items, count: items.length });
}
