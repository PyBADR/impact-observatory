import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const ZERO = {
  proposed: 0, under_review: 0, approved_pending_execution: 0,
  executed: 0, rejected: 0, failed: 0, escalated: 0,
  returned: 0, revoked: 0, withdrawn: 0, total_active: 0, total: 0, overdue: 0,
};

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;

  // Backend is primary source of truth — trust its response (including zero counts).
  // Only fall through to in-memory store if backend is unreachable or returns an error.
  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/authority/metrics`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) return NextResponse.json(await res.json());
    } catch {
      // backend unreachable — fall through to in-memory
    }
  }

  const m = serverStore.authority.metrics();
  return NextResponse.json({ ...ZERO, ...m });
}
