import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

type Params = { params: Promise<{ decision_id: string }> };

export async function POST(req: NextRequest, { params }: Params) {
  const { decision_id } = await params;

  if (!decision_id) {
    return NextResponse.json({ error: "decision_id is required" }, { status: 400 });
  }

  const backend = process.env.NEXT_PUBLIC_API_URL;
  const apiKey  = req.headers.get("X-IO-API-Key") ?? "";
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* body is optional */ }

  // Backend is primary — forward if available
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/decisions/${decision_id}/execute`, {
        method: "POST",
        headers: { "X-IO-API-Key": apiKey, "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
      });
      if (res.ok)             return NextResponse.json(await res.json());
      if (res.status !== 404) return NextResponse.json(await res.json(), { status: res.status });
      // 404 from backend → fall through to server-store
    } catch {
      // backend unreachable — fall through to server-store
    }
  }

  const dec = serverStore.decisions.execute(decision_id);
  if (!dec) {
    // Could be not-found or invalid transition — mirror backend status codes
    const existing = serverStore.decisions.get(decision_id);
    if (!existing) {
      return NextResponse.json({ error: `Decision ${decision_id} not found` }, { status: 404 });
    }
    return NextResponse.json(
      { error: `Cannot execute decision in ${existing.decision_status} status` },
      { status: 409 },
    );
  }
  return NextResponse.json(dec);
}
