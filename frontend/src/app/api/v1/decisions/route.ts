import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const EMPTY = { decisions: [], count: 0 };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  const url     = new URL(req.url);
  const qs      = url.search;

  // Backend is primary source of truth — trust its response (including empty arrays).
  // Only fall through to in-memory store if backend is unreachable or returns an error.
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/decisions${qs}`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) return NextResponse.json(await res.json());
    } catch {
      // backend unreachable — fall through to in-memory
    }
  }

  // In-memory fallback
  const sp    = url.searchParams;
  const items = serverStore.decisions.list({
    status:        sp.get("status")        ?? undefined,
    decision_type: sp.get("decision_type") ?? undefined,
    run_id:        sp.get("run_id")        ?? undefined,
    limit:         sp.has("limit") ? Number(sp.get("limit")) : undefined,
  });
  return NextResponse.json({ decisions: items, count: items.length });
}

export async function POST(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* ignore */ }

  // Try backend first
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/decisions`, {
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

  // In-memory create — also auto-creates authority envelope + outcome + value
  const dec = serverStore.decisions.create(
    body as Parameters<typeof serverStore.decisions.create>[0],
  );
  return NextResponse.json(dec, { status: 201 });
}
