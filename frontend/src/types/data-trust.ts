/**
 * Impact Observatory | مرصد الأثر
 * Data Trust Audit Layer — TypeScript Types (v1)
 *
 * These types mirror the backend data_trust Python models.
 * They are additive — no existing types are modified.
 *
 * Usage: import from '@/types/data-trust' when building
 * trust/provenance UI components (behind feature flag).
 */

// ═══════════════════════════════════════════════════════════════════════════════
// Data Source Registry
// ═══════════════════════════════════════════════════════════════════════════════

export type DataSourceType =
  | "static"
  | "manual"
  | "rss"
  | "api"
  | "market"
  | "government"
  | "internal";

export type RefreshFrequency =
  | "static"
  | "daily"
  | "weekly"
  | "manual";

export type FreshnessStatus =
  | "fresh"
  | "stale"
  | "unknown";

export interface DataSource {
  readonly source_id: string;
  readonly name: string;
  readonly source_type: DataSourceType;
  readonly url: string | null;
  readonly refresh_frequency: RefreshFrequency;
  readonly last_updated: string;           // ISO-8601
  readonly freshness_status: FreshnessStatus;
  readonly confidence_weight: number;      // 0.0–1.0
  readonly notes: string;
}

export interface DataSourceRegistrySummary {
  readonly total_sources: number;
  readonly by_type: Record<DataSourceType, number>;
  readonly live_connected_count: number;
  readonly stale_count: number;
  readonly all_static_fallback: boolean;
  readonly static_sources: string[];
  readonly stale_sources: string[];
}


// ═══════════════════════════════════════════════════════════════════════════════
// Scenario Data Provenance
// ═══════════════════════════════════════════════════════════════════════════════

export interface ScenarioProvenance {
  readonly scenario_id: string;
  readonly value_name: string;
  readonly current_value: unknown;
  readonly source_id: string;
  readonly calculation_method: string;
  readonly is_static_fallback: boolean;
  readonly last_updated: string;           // ISO-8601
  readonly confidence_score: number;       // 0.0–1.0
}


// ═══════════════════════════════════════════════════════════════════════════════
// Trust Score (Scoring Logic Layer)
// ═══════════════════════════════════════════════════════════════════════════════

export interface TrustScore {
  readonly scenario_id: string;
  readonly raw_base_loss_usd: number;
  readonly adjusted_loss_usd: number;
  readonly source_confidence: number;              // 0.0–1.0
  readonly freshness_penalty: number;              // 0.0–1.0
  readonly sector_multiplier: number;
  readonly country_exposure_multiplier: number;
  readonly is_static_fallback: boolean;
  readonly signal_inputs_used: string[];
  readonly computation_trace: string[];
}


// ═══════════════════════════════════════════════════════════════════════════════
// Audit Reviewer
// ═══════════════════════════════════════════════════════════════════════════════

export type AuditSeverity = "info" | "warning" | "critical";

export interface AuditFinding {
  readonly category: string;
  readonly severity: AuditSeverity;
  readonly file_path: string;
  readonly line_number: number | null;
  readonly description: string;
  readonly recommendation: string;
}

export interface AuditReport {
  readonly findings: AuditFinding[];
  readonly total: number;
  readonly by_severity: Record<AuditSeverity, number>;
}
