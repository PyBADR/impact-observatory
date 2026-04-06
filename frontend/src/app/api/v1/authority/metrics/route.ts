import { NextRequest, NextResponse } from "next/server";
import { serverStore } from "@/lib/server-store";

const ZERO = {
  proposed: 0, under_review: 0, approved_pending_execution: 0,
  executed: 0, rejected: 0, failed: 0, escalated: 0,
  returned: 0, revoked: 0, withdrawn: 0, total_active: 0, total: 0, overdue: 0,
};

export async function GET(req: NextRequest) {
  const backend = process.env.NEXT_PUBLIC_API_URL;

  if (backend) {
    try {
      const res = await fetch(`${backend}/api/v1/authority/metrics`, {
        headers: { "X-IO-API-Key": req.headers.get("X-IO-API-Key") ?? "" },
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        // Only use backend metrics if they have real data
        if (typeof data?.total === "number" && data.total > 0) {
          return NextResponse.json(data);
        }
      }
    } catch {
      // fall through to in-memory
    }
  }

  const m = serverStore.authority.metrics();
  return NextResponse.json({ ...ZERO, ...m });
}
