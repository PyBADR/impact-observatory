import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const EMPTY = { items: [], count: 0 };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  const url     = new URL(req.url);
  const qs      = url.search;

  // Try backend first
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/authority${qs}`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data?.items) && data.items.length > 0) {
          return NextResponse.json(data);
        }
      }
    } catch {
      // fall through to in-memory
    }
  }

  // In-memory fallback
  const sp    = url.searchParams;
  const items = serverStore.authority.list({
    status: sp.get("status")  ?? undefined,
    limit:  sp.has("limit")   ? Number(sp.get("limit"))  : undefined,
    offset: sp.has("offset")  ? Number(sp.get("offset")) : undefined,
  });
  return NextResponse.json({ items, count: items.length });
}

export async function POST(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* ignore */ }

  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/authority/propose`, {
        method:  "POST",
        headers: {
          "X-IO-API-Key":  req.headers.get("X-IO-API-Key") ?? "",
          "Content-Type":  "application/json",
        },
        body:  JSON.stringify(body),
        cache: "no-store",
      });
      if (res.ok) return NextResponse.json(await res.json(), { status: res.status });
    } catch { /* fall through */ }
  }

  return NextResponse.json(EMPTY, { status: 200 });
}
