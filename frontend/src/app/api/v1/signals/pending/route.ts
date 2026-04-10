import { NextRequest, NextResponse } from "next/server";

const EMPTY: { seeds: never[] } = { seeds: [] };

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;
  if (!backend) return NextResponse.json(EMPTY);

  try {
    const res = await fetch(`${backend}/api/v1/signals/pending`, {
      headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
      cache: "no-store",
    });
    if (!res.ok) return NextResponse.json(EMPTY);
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json(EMPTY);
  }
}
