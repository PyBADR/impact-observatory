"use client";

import { RouteErrorFallback } from "@/components/ErrorBoundary";

export default function ScenarioLabError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} />;
}
