"use client";

import { RouteErrorFallback } from "@/components/ErrorBoundary";

export default function ControlRoomError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} />;
}
