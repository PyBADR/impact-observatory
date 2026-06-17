/**
 * Impact Observatory | مرصد الأثر
 * Signal Snapshot Types — TypeScript types for signal ingestion (v2)
 *
 * These types mirror the backend signal_ingestion Python models.
 * They are type-only — no runtime code, no UI components.
 *
 * Usage: import from '@/types/signal-snapshot' when building
 * future signal display components (behind feature flag).
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Signal Source
// ═══════════════════════════════════════════════════════════════════════════════

export type SignalSourceType =
  | "rss"
  | "api"
  | "market"
  | "government"
  | "manual";

export interface SignalSource {
  readonly source_id: string;
  readonly name: string;
  readonly source_type: SignalSourceType;
  readonly url: string | null;
  readonly refresh_frequency_minutes: number;
  readonly confidence_weight: number;       // 0.0–1.0
  readonly enabled: boolean;
  readonly notes: string;
}


// ═══════════════════════════════════════════════════════════════════════════════
// Signal Snapshot
// ═══════════════════════════════════════════════════════════════════════════════

export type SnapshotFreshness =
  | "fresh"
  | "recent"
  | "stale"
  | "expired"
  | "unknown";

export interface SignalSnapshot {
  readonly snapshot_id: string;
  readonly source_id: string;
  readonly title: string;
  readonly summary: string;
  readonly url: string | null;
  readonly published_at: string;            // ISO-8601
  readonly ingested_at: string;             // ISO-8601
  readonly freshness_status: SnapshotFreshness;
  readonly confidence_score: number;        // 0.0–1.0
  readonly related_scenarios: string[];
  readonly related_countries: string[];
  readonly related_sectors: string[];
  readonly raw_metadata: Record<string, unknown>;
}


// ═══════════════════════════════════════════════════════════════════════════════
// Signal Audit
// ═══════════════════════════════════════════════════════════════════════════════

export type SignalAuditAction =
  | "source_checked"
  | "snapshot_created"
  | "source_failed"
  | "fallback_used";

export interface SignalAuditEntry {
  readonly timestamp: string;               // ISO-8601
  readonly action: SignalAuditAction;
  readonly source_id: string;
  readonly snapshot_id: string | null;
  readonly detail: string;
}

export interface SignalAuditSummary {
  readonly total_entries: number;
  readonly by_action: Record<SignalAuditAction, number>;
  readonly sources_checked: number;
  readonly snapshots_created: number;
  readonly failures: number;
  readonly fallbacks: number;
}


// ═══════════════════════════════════════════════════════════════════════════════
// Signal Advisory (v5 — advisory only, no scoring)
// ═══════════════════════════════════════════════════════════════════════════════

export interface SignalAdvisory {
  readonly advisory_id: string;
  readonly scenario_id: string;
  readonly snapshot_id: string;
  readonly source_id: string;
  readonly confidence: number;              // 0.0–1.0
  readonly freshness_status: SnapshotFreshness;
  readonly advisory_text: string;
  readonly risk_context: string;
  readonly suggested_review: string;
  readonly metric_before: number;
  readonly metric_after: number;            // Must equal metric_before
  readonly scoring_applied: boolean;        // Must always be false
  readonly fallback_used: boolean;
  readonly timestamp: string;               // ISO-8601
}
