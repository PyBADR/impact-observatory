import { NextRequest, NextResponse } from "next/server";

const EMPTY: { decisions: never[]; count: number } = { decisions: [], count: 0 };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  if (!backend) return NextResponse.json(EMPTY);

  const qs = new URL(req.url).search;
  try {
    const res = await fetch(`${backend}/api/v1/decisions${qs}`, {
      headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
      cache: "no-store",
    });
    if (!res.ok) return NextResponse.json(EMPTY);
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json(EMPTY);
  }
}

export async function POST(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  if (!backend) return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });

  try {
    const body = await req.text();
    const res = await fetch(`${backend}/api/v1/decisions`, {
      method: "POST",
      headers: {
        "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "",
        "Content-Type": "application/json",
      },
      body,
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}
