/**
 * V2 API Types — Frontend-Safe Mapping Layer
 *
 * Maps raw backend responses (MacroRuntimeResult, DecisionOutput,
 * PropagationResult, UnifiedRunResult) to UI-safe types with:
 *   - Zero undefined fields
 *   - Zero null fields
 *   - All defaults populated
 *   - Pure functions, never throw
 *
 * Backend models consumed (read-only — never modified):
 *   - MacroRuntimeResult  (graph_brain/macro_runtime.py)
 *   - DecisionOutput      (macro/decision/decision_models.py)
 *   - PropagationResult   (macro/propagation/propagation_schemas.py)
 *   - UnifiedRunResult    (types/observatory.ts — existing TS contract)
 *
 * Architecture:
 *   API JSON → mapApiToUI(raw) → SafeEvent + SafeDecision[] + SafeImpact[]
 */

// ═══════════════════════════════════════════════════════════════════════
// Primitive Guards (re-exported from live-mappers for consistency)
// ═══════════════════════════════════════════════════════════════════════

function str(v: unknown, fallback: string = "—"): string {
  if (v === null || v === undefined) return fallback;
  const s = String(v).trim();
  return s.length === 0 ? fallback : s;
}

function num(v: unknown, fallback: number = 0): number {
  if (v === null || v === undefined) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function bool(v: unknown, fallback: boolean = false): boolean {
  if (typeof v === "boolean") return v;
  return fallback;
}

function arr<T>(v: unknown): T[] {
  return Array.isArray(v) ? v : [];
}

function rec(v: unknown): Record<string, unknown> {
  return v !== null && typeof v === "object" && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : {};
}

// ═══════════════════════════════════════════════════════════════════════
// SafeEvent — Maps to backend PropagationResult + scenario context
// ═══════════════════════════════════════════════════════════════════════

/** Severity tier for UI badge/color classification */
export type SeverityTier =
  | "NOMINAL"
  | "LOW"
  | "GUARDED"
  | "ELEVATED"
  | "HIGH"
  | "SEVERE";

export function classifySeverity(score: number): SeverityTier {
  if (score >= 0.80) return "SEVERE";
  if (score >= 0.65) return "HIGH";
  if (score >= 0.50) return "ELEVATED";
  if (score >= 0.35) return "GUARDED";
  if (score >= 0.20) return "LOW";
  return "NOMINAL";
}

/** A single propagation hop for the causal chain display */
export interface SafePropagationHop {
  hopIndex: number;
  fromDomain: string;
  toDomain: string;
  weight: number;
  decay: number;
  severityIn: number;
  severityOut: number;
  mechanism: string;
  lagHours: number;
}

/** A single domain hit in the propagation result */
export interface SafeDomainHit {
  domain: string;
  depth: number;
  severity: number;
  severityTier: SeverityTier;
  regions: string[];
  pathDescription: string;
  reasoning: string;
}

/** Top-level event context — safe for direct UI binding */
export interface SafeEvent {
  // ── Identity ─────────────────────────────────────────────
  runId: string;
  signalId: string;
  signalTitle: string;
  scenarioTemplateId: string;
  scenarioLabel: string;

  // ── Severity ─────────────────────────────────────────────
  severity: number;
  severityTier: SeverityTier;
  horizonHours: number;

  // ── Headline metrics ─────────────────────────────────────
  totalLossUsd: number;
  nodesImpacted: number;
  propagationDepth: number;
  confidence: number;

  // ── Propagation ──────────────────────────────────────────
  entryDomains: string[];
  hops: SafePropagationHop[];
  domainHits: SafeDomainHit[];
  totalDomainsReached: number;
  maxDepth: number;

  // ── Graph enrichment (additive metadata) ─────────────────
  isGraphEnriched: boolean;
  graphCausalHints: number;
  graphExplanationFragments: number;

  // ── Audit ────────────────────────────────────────────────
  auditHash: string;
  propagatedAt: string;
  stagesCompleted: string[];
  durationMs: number;
  warnings: string[];
}

// ═══════════════════════════════════════════════════════════════════════
// SafeDecision — Maps to backend DecisionOutput + DecisionAction
// ═══════════════════════════════════════════════════════════════════════

/** Priority tier for decision urgency badge */
export type DecisionPriorityTier =
  | "ROUTINE"
  | "WATCH"
  | "ADVISORY"
  | "ALERT"
  | "CRITICAL";

/** A single recommended action — safe for card rendering */
export interface SafeAction {
  actionId: string;
  domain: string;
  actionType: string;
  description: string;
  urgency: string;
  rationale: string;
}

/** Full decision output — safe for panel rendering */
export interface SafeDecision {
  decisionId: string;
  signalId: string;
  signalTitle: string;
  priority: DecisionPriorityTier;
  requiresEscalation: boolean;
  actions: SafeAction[];
  affectedDomains: string[];
  overallSeverity: number;
  overallSeverityLevel: string;
  confidence: string;
  totalDomainsReached: number;
  impactSummary: string;
  decisionReasoning: string;
  decidedAt: string;
  auditHash: string;
}

// ═══════════════════════════════════════════════════════════════════════
// SafeImpact — Maps to per-sector stress / financial impact
// ═══════════════════════════════════════════════════════════════════════

/** Classification for impact status badge */
export type ImpactStatus = "NOMINAL" | "STRESSED" | "DEGRADED" | "CRITICAL" | "FAILED";

/** A single entity-level financial impact */
export interface SafeImpact {
  entityId: string;
  entityLabel: string;
  sector: string;
  lossUsd: number;
  exposure: number;
  stressLevel: number;
  stressTier: SeverityTier;
  impactStatus: ImpactStatus;
  // ── Banking-specific (0 if N/A) ──────────────────────────
  lcr: number;
  cet1Ratio: number;
  capitalAdequacyRatio: number;
  // ── Insurance-specific (0 if N/A) ────────────────────────
  solvencyRatio: number;
  combinedRatio: number;
  // ── Fintech-specific (0 if N/A) ──────────────────────────
  serviceAvailability: number;
  settlementDelayMinutes: number;
}

// ═══════════════════════════════════════════════════════════════════════
// Full Mapped Result
// ═══════════════════════════════════════════════════════════════════════

export interface SafeApiResult {
  event: SafeEvent;
  decisions: SafeDecision[];
  impacts: SafeImpact[];
}

// ═══════════════════════════════════════════════════════════════════════
// Mapper: mapApiToUI
// ═══════════════════════════════════════════════════════════════════════

/**
 * Transform any raw API payload into a fully-defaulted SafeApiResult.
 *
 * Accepts:
 *   - UnifiedRunResult shape (primary path)
 *   - Partial / malformed payloads (defensive path)
 *
 * Never throws. Every field gets a safe default.
 */
export function mapApiToUI(raw: unknown): SafeApiResult {
  const r = rec(raw);

  return {
    event: mapEvent(r),
    decisions: mapDecisions(r),
    impacts: mapImpacts(r),
  };
}

// ── Event mapper ─────────────────────────────────────────────────────

function mapEvent(r: Record<string, unknown>): SafeEvent {
  const scenario = rec(r.scenario);
  const headline = rec(r.headline);
  const trust = rec(r.trust);
  const graphPayload = rec(r.graph_payload);
  const graphNodes = arr<unknown>(graphPayload.nodes);

  // ── Propagation hops ────────────────────────────────────────────
  const rawSteps = arr<Record<string, unknown>>(r.propagation_steps);
  const hops: SafePropagationHop[] = rawSteps.map((s, i) => ({
    hopIndex: i,
    fromDomain: str(s.from),
    toDomain: str(s.to),
    weight: num(s.weight),
    decay: num(s.decay, 1),
    severityIn: num(s.severity_in),
    severityOut: num(s.severity_out),
    mechanism: str(s.label ?? s.transmission_label, "propagation"),
    lagHours: num(s.lag_hours),
  }));

  // ── Domain hits (from macro propagation result if present) ──────
  const rawHits = arr<Record<string, unknown>>(r.hits ?? r.domain_hits);
  const domainHits: SafeDomainHit[] = rawHits.map((h) => {
    const sev = num(h.severity_at_hit ?? h.severity);
    return {
      domain: str(h.domain),
      depth: num(h.depth),
      severity: sev,
      severityTier: classifySeverity(sev),
      regions: arr<string>(h.regions),
      pathDescription: str(h.path_description, "—"),
      reasoning: str(h.reasoning, "—"),
    };
  });

  // ── Graph enrichment metadata ──────────────────────────────────
  const graphMeta = rec(r.graph_metadata ?? r.graph_enrichment);
  const severity = num(scenario.severity);

  return {
    runId: str(r.run_id),
    signalId: str(r.signal_id ?? r.run_id),
    signalTitle: str(r.signal_title ?? scenario.label),
    scenarioTemplateId: str(scenario.template_id),
    scenarioLabel: str(scenario.label),

    severity,
    severityTier: classifySeverity(severity),
    horizonHours: num(scenario.horizon_hours),

    totalLossUsd: num(headline.total_loss_usd ?? headline.total_estimated_loss_usd),
    nodesImpacted: num(headline.total_nodes_impacted ?? graphNodes.length),
    propagationDepth: num(headline.propagation_depth ?? r.max_depth),
    confidence: num(r.confidence ?? trust.confidence_score),

    entryDomains: arr<string>(r.entry_domains),
    hops,
    domainHits,
    totalDomainsReached: num(r.total_domains_reached ?? domainHits.length),
    maxDepth: num(r.max_depth ?? headline.propagation_depth),

    isGraphEnriched: bool(graphMeta.graph_available) && (
      num(graphMeta.causal_hints) > 0 ||
      num(graphMeta.explanation_hits_enriched) > 0
    ),
    graphCausalHints: num(graphMeta.causal_hints),
    graphExplanationFragments: num(graphMeta.explanation_fragments),

    auditHash: str(r.audit_hash ?? trust.audit_hash, ""),
    propagatedAt: str(r.propagated_at ?? r.created_at, new Date().toISOString()),
    stagesCompleted: arr<string>(r.stages_completed ?? trust.stages_completed),
    durationMs: num(r.duration_ms),
    warnings: arr<string>(r.warnings ?? trust.warnings),
  };
}

// ── Decision mapper ──────────────────────────────────────────────────

const VALID_PRIORITIES: DecisionPriorityTier[] = [
  "ROUTINE", "WATCH", "ADVISORY", "ALERT", "CRITICAL",
];

function safePriority(v: unknown): DecisionPriorityTier {
  const s = String(v ?? "").toUpperCase();
  return VALID_PRIORITIES.includes(s as DecisionPriorityTier)
    ? (s as DecisionPriorityTier)
    : "ROUTINE";
}

function mapDecisions(r: Record<string, unknown>): SafeDecision[] {
  // Path 1: UnifiedRunResult.decision_inputs (V2 unified pipeline)
  const decInputs = rec(r.decision_inputs);
  const v2Actions = arr<Record<string, unknown>>(decInputs.actions);

  if (v2Actions.length > 0) {
    return [mapUnifiedDecision(r, decInputs, v2Actions)];
  }

  // Path 2: Raw DecisionOutput from macro pipeline
  const rawDecision = rec(r.decision ?? r.decision_output);
  if (rawDecision.decision_id) {
    return [mapMacroDecision(rawDecision)];
  }

  // Path 3: Array of decision outputs
  const rawDecisions = arr<Record<string, unknown>>(r.decisions ?? r.decision_outputs);
  if (rawDecisions.length > 0) {
    return rawDecisions.map((d) => mapMacroDecision(rec(d)));
  }

  // Path 4: V1 DecisionPlan
  const v1Plan = rec(r.decisions);
  const v1Actions = arr<Record<string, unknown>>(v1Plan.actions);
  if (v1Actions.length > 0) {
    return [mapV1DecisionPlan(v1Plan, v1Actions)];
  }

  // No decisions available
  return [];
}

function mapUnifiedDecision(
  r: Record<string, unknown>,
  decInputs: Record<string, unknown>,
  v2Actions: Record<string, unknown>[],
): SafeDecision {
  // Derive priority from highest urgency action
  const maxUrgency = v2Actions.reduce(
    (max, a) => Math.max(max, num(a.urgency)),
    0,
  );
  const priority: DecisionPriorityTier =
    maxUrgency >= 90 ? "CRITICAL"
      : maxUrgency >= 70 ? "ALERT"
      : maxUrgency >= 50 ? "ADVISORY"
      : maxUrgency >= 30 ? "WATCH"
      : "ROUTINE";

  return {
    decisionId: str(decInputs.run_id ?? r.run_id),
    signalId: str(r.signal_id ?? r.run_id),
    signalTitle: str(rec(r.scenario).label),
    priority,
    requiresEscalation: priority === "CRITICAL" || priority === "ALERT",
    actions: v2Actions.map((a) => ({
      actionId: str(a.id ?? a.action_id),
      domain: str(a.sector ?? a.domain),
      actionType: str(a.action_type, "review"),
      description: str(a.action ?? a.description),
      urgency: str(a.urgency),
      rationale: str(a.rationale ?? a.action_ar, "—"),
    })),
    affectedDomains: [...new Set(v2Actions.map((a) => str(a.sector ?? a.domain)))],
    overallSeverity: num(r.confidence),
    overallSeverityLevel: str(rec(r.scenario).severity),
    confidence: str(r.confidence),
    totalDomainsReached: v2Actions.length,
    impactSummary: str(rec(rec(r.sectors).explanation).summary, "—"),
    decisionReasoning: str(
      rec(rec(r.sectors).explanation).summary,
      "Decision generated from unified pipeline.",
    ),
    decidedAt: new Date().toISOString(),
    auditHash: str(rec(r.trust).audit_hash ?? r.audit_hash, ""),
  };
}

function mapMacroDecision(d: Record<string, unknown>): SafeDecision {
  const rawActions = arr<Record<string, unknown>>(d.recommended_actions);

  return {
    decisionId: str(d.decision_id),
    signalId: str(d.signal_id),
    signalTitle: str(d.signal_title),
    priority: safePriority(d.priority),
    requiresEscalation: bool(d.requires_escalation),
    actions: rawActions.map((a) => ({
      actionId: str(a.action_id),
      domain: str(a.domain),
      actionType: str(a.action_type),
      description: str(a.description),
      urgency: str(a.urgency),
      rationale: str(a.rationale),
    })),
    affectedDomains: arr<string>(d.affected_domains),
    overallSeverity: num(d.overall_severity),
    overallSeverityLevel: str(d.overall_severity_level),
    confidence: str(d.confidence),
    totalDomainsReached: num(d.total_domains_reached),
    impactSummary: str(d.impact_summary),
    decisionReasoning: str(d.decision_reasoning),
    decidedAt: str(d.decided_at, new Date().toISOString()),
    auditHash: str(d.audit_hash),
  };
}

function mapV1DecisionPlan(
  plan: Record<string, unknown>,
  actions: Record<string, unknown>[],
): SafeDecision {
  const maxUrgency = actions.reduce(
    (max, a) => Math.max(max, num(a.urgency)),
    0,
  );
  return {
    decisionId: str(plan.run_id),
    signalId: str(plan.run_id),
    signalTitle: str(plan.scenario_label),
    priority: maxUrgency >= 80 ? "CRITICAL" : maxUrgency >= 60 ? "ALERT" : "ADVISORY",
    requiresEscalation: maxUrgency >= 60,
    actions: actions.map((a) => ({
      actionId: str(a.id),
      domain: str(a.sector),
      actionType: "review",
      description: str(a.action),
      urgency: str(a.urgency),
      rationale: str(a.action_ar, "—"),
    })),
    affectedDomains: [...new Set(actions.map((a) => str(a.sector)))],
    overallSeverity: num(plan.total_loss_usd) > 0 ? 0.7 : 0.3,
    overallSeverityLevel: "ELEVATED",
    confidence: "—",
    totalDomainsReached: actions.length,
    impactSummary: `Total loss: $${num(plan.total_loss_usd).toLocaleString()}`,
    decisionReasoning: `Peak day ${num(plan.peak_day)}, time to failure ${num(plan.time_to_failure_hours)}h`,
    decidedAt: new Date().toISOString(),
    auditHash: "",
  };
}

// ── Impact mapper ────────────────────────────────────────────────────

const VALID_IMPACT_STATUS: ImpactStatus[] = [
  "NOMINAL", "STRESSED", "DEGRADED", "CRITICAL", "FAILED",
];

function safeImpactStatus(v: unknown): ImpactStatus {
  const s = String(v ?? "").toUpperCase();
  return VALID_IMPACT_STATUS.includes(s as ImpactStatus)
    ? (s as ImpactStatus)
    : "NOMINAL";
}

export function mapImpacts(r: Record<string, unknown>): SafeImpact[] {
  const impacts: SafeImpact[] = [];
  const sectors = rec(r.sectors);

  // ── Financial impacts ──────────────────────────────────────────
  const financials = arr<Record<string, unknown>>(
    sectors.financial_impacts ?? r.financial,
  );
  for (const f of financials) {
    const stress = num(f.stress_level ?? f.stress ?? f.exposure);
    impacts.push({
      entityId: str(f.entity_id),
      entityLabel: str(f.entity_label ?? f.entity_id),
      sector: str(f.sector, "financial"),
      lossUsd: num(f.loss_usd ?? f.loss),
      exposure: num(f.exposure ?? f.loss_pct_gdp),
      stressLevel: stress,
      stressTier: classifySeverity(stress),
      impactStatus: safeImpactStatus(f.impact_status ?? f.classification),
      lcr: 0,
      cet1Ratio: 0,
      capitalAdequacyRatio: 0,
      solvencyRatio: 0,
      combinedRatio: 0,
      serviceAvailability: 0,
      settlementDelayMinutes: 0,
    });
  }

  // ── Banking stresses ───────────────────────────────────────────
  const bankings = arr<Record<string, unknown>>(
    sectors.banking_stresses ?? (r.banking ? [rec(r.banking)] : []),
  );
  for (const b of bankings) {
    const stress = num(b.aggregate_stress ?? b.stress);
    impacts.push({
      entityId: str(b.entity_id ?? b.id, "banking_aggregate"),
      entityLabel: str(b.name ?? b.entity_id, "Banking"),
      sector: "banking",
      lossUsd: num(b.total_exposure_usd ?? b.loss),
      exposure: num(b.total_exposure_usd),
      stressLevel: stress,
      stressTier: classifySeverity(stress),
      impactStatus: safeImpactStatus(b.classification ?? b.impact_status),
      lcr: num(b.lcr ?? b.liquidity_stress),
      cet1Ratio: num(b.cet1_ratio),
      capitalAdequacyRatio: num(b.capital_adequacy_ratio ?? b.capital_adequacy_impact_pct),
      solvencyRatio: 0,
      combinedRatio: 0,
      serviceAvailability: 0,
      settlementDelayMinutes: 0,
    });
  }

  // ── Insurance stresses ─────────────────────────────────────────
  const insurances = arr<Record<string, unknown>>(
    sectors.insurance_stresses ?? (r.insurance ? [rec(r.insurance)] : []),
  );
  for (const ins of insurances) {
    const stress = num(ins.aggregate_stress ?? ins.stress);
    impacts.push({
      entityId: str(ins.entity_id ?? ins.id, "insurance_aggregate"),
      entityLabel: str(ins.name ?? ins.entity_id, "Insurance"),
      sector: "insurance",
      lossUsd: num(ins.portfolio_exposure_usd ?? ins.loss),
      exposure: num(ins.portfolio_exposure_usd),
      stressLevel: stress,
      stressTier: classifySeverity(stress),
      impactStatus: safeImpactStatus(ins.classification ?? ins.impact_status),
      lcr: 0,
      cet1Ratio: 0,
      capitalAdequacyRatio: 0,
      solvencyRatio: num(ins.solvency_ratio ?? ins.severity_index),
      combinedRatio: num(ins.combined_ratio),
      serviceAvailability: 0,
      settlementDelayMinutes: 0,
    });
  }

  // ── Fintech stresses ───────────────────────────────────────────
  const fintechs = arr<Record<string, unknown>>(
    sectors.fintech_stresses ?? (r.fintech ? [rec(r.fintech)] : []),
  );
  for (const ft of fintechs) {
    const stress = num(ft.aggregate_stress ?? ft.stress);
    impacts.push({
      entityId: str(ft.entity_id ?? ft.id, "fintech_aggregate"),
      entityLabel: str(ft.name ?? ft.entity_id, "Fintech"),
      sector: "fintech",
      lossUsd: num(ft.loss),
      exposure: num(ft.payment_volume_impact_pct),
      stressLevel: stress,
      stressTier: classifySeverity(stress),
      impactStatus: safeImpactStatus(ft.classification ?? ft.impact_status),
      lcr: 0,
      cet1Ratio: 0,
      capitalAdequacyRatio: 0,
      solvencyRatio: 0,
      combinedRatio: 0,
      serviceAvailability: num(ft.service_availability ?? ft.api_availability_pct),
      settlementDelayMinutes: num(ft.settlement_delay_minutes ?? (num(ft.settlement_delay_hours) * 60)),
    });
  }

  return impacts;
}
