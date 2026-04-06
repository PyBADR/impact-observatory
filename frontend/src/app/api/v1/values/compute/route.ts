import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

export async function POST(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* ignore */ }

  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/values/compute`, {
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

  if (!body.source_outcome_id) {
    return NextResponse.json({ error: "source_outcome_id is required" }, { status: 400 });
  }

  const val = serverStore.values.compute(
    body as Parameters<typeof serverStore.values.compute>[0],
  );
  return NextResponse.json(val, { status: 201 });
}
