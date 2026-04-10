import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const EMPTY = { outcomes: [], count: 0 };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  const url     = new URL(req.url);
  const qs      = url.search;

  // Backend is primary source of truth — trust its response (including empty arrays).
  // Only fall through to in-memory store if backend is unreachable or returns an error.
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/outcomes${qs}`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) return NextResponse.json(await res.json());
    } catch {
      // backend unreachable — fall through to in-memory
    }
  }

  const sp   = url.searchParams;
  const items = serverStore.outcomes.list({
    decision_id: sp.get("decision_id") ?? undefined,
    run_id:      sp.get("run_id")      ?? undefined,
    status:      sp.get("status")      ?? undefined,
    limit:       sp.has("limit") ? Number(sp.get("limit")) : undefined,
  });
  return NextResponse.json({ outcomes: items, count: items.length });
}

export async function POST(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* ignore */ }

  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/outcomes`, {
        method:  "POST",
        headers: {
          "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "",
          "Content-Type": "application/json",
        },
        body:  JSON.stringify(body),
        cache: "no-store",
      });
      if (res.ok) return NextResponse.json(await res.json(), { status: res.status });
    } catch { /* fall through */ }
  }

  const out = serverStore.outcomes.create(body as Parameters<typeof serverStore.outcomes.create>[0]);
  return NextResponse.json(out, { status: 201 });
}
