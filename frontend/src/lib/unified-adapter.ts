/**
 * Impact Observatory | مرصد الأثر — Unified Adapter
 *
 * Converts UnifiedRunResult (from POST /graph/unified-run)
 * → RunResult (consumed by ExecutiveDashboard and legacy pages).
 *
 * This adapter exists because:
 * 1. The unified pipeline produces a different shape than pipeline_v4
 * 2. The Dashboard is typed to RunResult
 * 3. We need both pipelines to feed the same UI until full migration
 *
 * Zero logic duplication — only structural mapping.
 */

import { emitAudit } from "@/lib/audit";
import type {
  RunResult,
  UnifiedRunResult,
  FinancialImpact,
  BankingStress,
  InsuranceStress,
  FintechStress,
  DecisionPlan,
  ExplanationPack,
  RunHeadline,
  Classification,
  BusinessSeverity,
  ExecutiveStatus,
  TimelineStep,
  RegulatoryEvent,
} from "@/types/observatory";

/**
 * Convert UnifiedRunResult → RunResult for Dashboard consumption.
 *
 * Maps unified pipeline output (graph-centric) to the legacy RunResult
 * shape (sector-centric) that ExecutiveDashboard expects.
 */
export function unifiedToRunResult(
  unified: UnifiedRunResult,
  /** Optional context for same-run integrity checking. Does not change output shape. */
  opts?: { expected_run_id?: string; scenario_id?: string },
): RunResult {
  // Cast to any for cross-version field access (v4 unified + v2 legacy schemas)
  const u = unified as unknown as Record<string, unknown>;

  // ── API contract violation checks ──────────────────────────────────────────
  // run_id is the linchpin of the entire execution lineage. If it is absent
  // the result is structurally invalid — every downstream consumer loses
  // traceability. Emit immediately before any further mapping.
  const inboundRunId = unified.run_id ?? (u.run_id as string) ?? "";
  if (!inboundRunId) {
    emitAudit({
      event_type: "api_contract_violation",
      entity_id:  "unifiedToRunResult",
      actor:      "adapter",
      details: {
        violation: "run_id absent or empty in UnifiedRunResult",
        field:     "run_id",
        received:  inboundRunId || null,
        hint:      "Backend must always return a stable run_id for execution lineage",
      },
      lineage_ref: null,
    });
  }

  // headline is required for all financial KPI rendering downstream.
  const headlinePresent = !!(unified.headline ?? u.headline);
  if (!headlinePresent) {
    emitAudit({
      event_type: "api_contract_violation",
      entity_id:  "unifiedToRunResult",
      run_id:     inboundRunId || null,
      actor:      "adapter",
      details: {
        violation: "headline object absent in UnifiedRunResult",
        field:     "headline",
        received:  null,
        hint:      "Financial KPI rendering will use zero-value fallbacks",
      },
      lineage_ref: null,
    });
  }

  // ── Same-run integrity check ───────────────────────────────────────────────
  // If the caller specifies an expected run_id (from the active run context in
  // the store) and the backend response carries a different run_id, a response
  // from a stale or concurrent run may have been mixed into the active session.
  if (
    opts?.expected_run_id &&
    inboundRunId &&
    opts.expected_run_id !== inboundRunId
  ) {
    emitAudit({
      event_type: "same_run_integrity_violation",
      entity_id:  "unifiedToRunResult",
      run_id:     inboundRunId,
      scenario_id: opts.scenario_id ?? null,
      actor:      "adapter",
      details: {
        expected_run_id: opts.expected_run_id,
        received_run_id: inboundRunId,
        hint: "Response run_id does not match the active session run_id — possible stale or concurrent response",
      },
      lineage_ref: null,
    });
  }

  // Normalise scenario: v4 uses template_id, v2 uses scenario_id
  const rawScenario = (u.scenario as Record<string, unknown>) ?? {};
  const normalizedTemplateId = (rawScenario.template_id as string)
    ?? (rawScenario.scenario_id as string)
    ?? (u.scenario_id as string)
    ?? "";

  // Defensive: ensure top-level objects exist even if payload is partial
  const uHeadline = (unified.headline ?? u.headline ?? { total_loss_usd: 0, total_nodes_impacted: 0, propagation_depth: 0 }) as Record<string, unknown>;
  // Extracted typed scalars for use in sub-object constructors below
  const totalLossUsd = (uHeadline.total_loss_usd as number) ?? 0;
  const uScenario = {
    template_id: normalizedTemplateId,
    label: (rawScenario.label as string) ?? normalizedTemplateId,
    severity: (rawScenario.severity as number) ?? (u.severity as number) ?? 0.7,
    horizon_hours: (rawScenario.horizon_hours as number) ?? (u.horizon_hours as number) ?? 168,
  };
  const mapPayload = unified.map_payload ?? { impacted_entities: [], total_estimated_loss_usd: 0 };
  const sectorRollups = unified.sector_rollups ?? { banking: {} as any, insurance: {} as any, fintech: {} as any };
  const decisionInputs = unified.decision_inputs ?? { run_id: "", total_loss_usd: 0, actions: [], all_actions: [] };
  const graphPayload = unified.graph_payload ?? { nodes: [], edges: [], categories: [] };
  const warnings = unified.warnings ?? [];
  const confidence = (unified.confidence ?? (u.confidence_score as number) ?? 0.1) as number;
  const sectors = unified.sectors;
  const math = unified.math;
  const physics = unified.physics;

  void decisionInputs; void graphPayload; void warnings; void math; void physics;

  // ── v2 backend sector dicts (top-level keys: banking, insurance, fintech) ──
  // Backend returns these as aliases for banking_stress / insurance_stress / fintech_stress.
  // Adapter MUST prefer these over the v4 `sectors.*` paths which do not exist in v2.
  const uBanking = ((u.banking ?? u.banking_stress ?? {}) as Record<string, unknown>);
  const uInsurance = ((u.insurance ?? u.insurance_stress ?? {}) as Record<string, unknown>);
  const uFintech = ((u.fintech ?? u.fintech_stress ?? {}) as Record<string, unknown>);

  // ── Financial Impacts ───────────────────────────────────
  // v4: sectors.financial_impacts  |  v2: u.financial (= financial_impact.top_entities list)
  // top_entities fields: entity_id, entity_label, loss_usd, stress_score, classification, peak_day, sector
  const rawFinancialEntities: Record<string, unknown>[] =
    (sectors?.financial_impacts as Record<string, unknown>[])
    ?? (u.financial as Record<string, unknown>[])
    ?? (u.financial_impacts as Record<string, unknown>[])
    ?? [];
  const financial: FinancialImpact[] = rawFinancialEntities.map(
    (fi) => {
      const lossUsd = (fi.loss_usd as number) ?? (fi.loss as number) ?? 0;
      const stressLevel = (fi.stress_score as number) ?? (fi.loss && fi.exposure ? (fi.loss as number) / (fi.exposure as number) : 0);
      return {
        entity_id: (fi.entity_id as string) ?? "",
        entity_label: (fi.entity_label as string) ?? (fi.entity_id as string ?? "").replace(/_/g, " "),
        sector: (fi.sector as string) ?? (fi.entity_id as string ?? "").split("_")[0] ?? "finance",
        loss_usd: lossUsd,
        loss_pct_gdp: lossUsd ? lossUsd / 2.1e12 : 0,
        peak_day: (fi.peak_day as number) ?? 1,
        recovery_days: 7,
        confidence: confidence,
        stress_level: stressLevel,
        classification: (fi.classification as Classification) ?? _classifyStress(stressLevel),
      };
    }
  );

  // ── Banking Stress ──────────────────────────────────────
  // v4: sectors.banking_aggregate + sector_rollups.banking  |  v2: u.banking (top-level)
  const bankingAggStress = (uBanking.aggregate_stress as number)
    ?? (sectorRollups?.banking?.aggregate_stress as number)
    ?? 0;
  const banking: BankingStress = {
    run_id: unified.run_id,
    total_exposure_usd: (uBanking.total_exposure_usd as number) ?? totalLossUsd,
    liquidity_stress: (uBanking.liquidity_stress as number) ?? 0,
    credit_stress: (uBanking.credit_stress as number) ?? 0,
    fx_stress: (uBanking.fx_stress as number) ?? 0,
    interbank_contagion: (uBanking.interbank_contagion as number) ?? 0,
    time_to_liquidity_breach_hours: (uBanking.time_to_liquidity_breach_hours as number) ?? 9999,
    capital_adequacy_impact_pct: (uBanking.capital_adequacy_impact_pct as number) ?? 0,
    aggregate_stress: bankingAggStress,
    classification: (uBanking.classification as Classification) ?? _classifyStress(bankingAggStress),
    // affected_institutions: backend v2 engine hardcodes [] — not produced at source
    affected_institutions: (uBanking.affected_institutions as any[]) ?? [],
  };

  // ── Insurance Stress ────────────────────────────────────
  // v4: sectors.insurance_aggregate + sector_rollups.insurance  |  v2: u.insurance (top-level)
  const insAggStress = (uInsurance.aggregate_stress as number)
    ?? (sectorRollups?.insurance?.aggregate_stress as number)
    ?? 0;
  const insurance: InsuranceStress = {
    run_id: unified.run_id,
    portfolio_exposure_usd: (uInsurance.portfolio_exposure_usd as number) ?? totalLossUsd * 0.15,
    claims_surge_multiplier: (uInsurance.claims_surge_multiplier as number) ?? 1.0,
    severity_index: (uInsurance.severity_index as number) ?? uScenario.severity,
    loss_ratio: (uInsurance.loss_ratio as number) ?? 0,
    combined_ratio: (uInsurance.combined_ratio as number) ?? 1.0,
    underwriting_status: (uInsurance.underwriting_status as string) ?? "stable",
    time_to_insolvency_hours: (uInsurance.time_to_insolvency_hours as number) ?? 9999,
    reinsurance_trigger: (uInsurance.reinsurance_trigger as boolean) ?? false,
    ifrs17_risk_adjustment_pct: (uInsurance.ifrs17_risk_adjustment_pct as number) ?? 0,
    aggregate_stress: insAggStress,
    classification: (uInsurance.classification as Classification) ?? _classifyStress(insAggStress),
    // affected_lines: backend v2 engine hardcodes [] — not produced at source
    affected_lines: (uInsurance.affected_lines as any[]) ?? [],
  };

  // ── Fintech Stress ──────────────────────────────────────
  // v4: sectors.fintech_aggregate + sector_rollups.fintech  |  v2: u.fintech (top-level)
  const ftAggStress = (uFintech.aggregate_stress as number)
    ?? (sectorRollups?.fintech?.aggregate_stress as number)
    ?? 0;
  const fintech: FintechStress = {
    run_id: unified.run_id,
    payment_volume_impact_pct: (uFintech.payment_volume_impact_pct as number) ?? 0,
    settlement_delay_hours: (uFintech.settlement_delay_hours as number) ?? 0,
    api_availability_pct: (uFintech.api_availability_pct as number) ?? 100,
    cross_border_disruption: (uFintech.cross_border_disruption as number) ?? 0,
    digital_banking_stress: (uFintech.digital_banking_stress as number) ?? ftAggStress,
    time_to_payment_failure_hours: (uFintech.time_to_payment_failure_hours as number) ?? 9999,
    aggregate_stress: ftAggStress,
    classification: (uFintech.classification as Classification) ?? _classifyStress(ftAggStress),
    // affected_platforms: backend v2 engine hardcodes [] — not produced at source
    affected_platforms: (uFintech.affected_platforms as any[]) ?? [],
  };

  // ── Decision Plan ───────────────────────────────────────
  // v4: sectors.decision_plan.actions  |  v2: top-level decision_plan.actions or decision_actions
  const rawDp = (u.decision_plan as Record<string, unknown>);
  const dpActions: Record<string, unknown>[] =
    sectors?.decision_plan?.actions ??
    (rawDp?.actions as Record<string, unknown>[]) ??
    (u.decision_actions as Record<string, unknown>[]) ??
    [];
  /** Normalise a single action from either v4 or v2 schemas. */
  function _mapAction(a: Record<string, unknown>) {
    // v4 fields: action_id, action_type, target_ref, urgency, value, priority_score, execution_window_hours, expected_loss_reduction, feasibility
    // v2 fields: id, action, sector, owner, urgency, value, regulatory_risk, priority, time_to_act, loss_avoided_usd, cost_usd, confidence
    const id = (a.id as string) ?? (a.action_id as string) ?? "";
    const actionText = (a.action as string)
      ?? ((a.action_type && a.target_ref) ? `${a.action_type}: ${a.target_ref}` : undefined)
      ?? (a.description as string)
      ?? "";
    const sector = (a.sector as string)
      ?? ((a.target_ref as string)?.split("_")[0])
      ?? "finance";
    return {
      id,
      action: actionText,
      action_ar: (a.action_ar as string) ?? null,
      sector,
      owner: (a.owner as string) ?? "Risk Committee",
      urgency: (a.urgency as number) ?? 0.5,
      value: (a.value as number) ?? (a.loss_avoided_usd as number) ?? 0,
      regulatory_risk: (a.regulatory_risk as number) ?? 0.5,
      priority: (a.priority as number) ?? (a.priority_score as number) ?? 0.5,
      time_to_act_hours: (a.time_to_act_hours as number) ?? (a.time_to_act as number) ?? (a.execution_window_hours as number) ?? 24,
      time_to_failure_hours: 72,
      loss_avoided_usd: (a.loss_avoided_usd as number) ?? (a.expected_loss_reduction as number) ?? 0,
      cost_usd: (a.cost_usd as number) ?? 0,
      confidence: (a.confidence as number) ?? (a.feasibility as number) ?? 0.7,
    };
  }

  const decisions: DecisionPlan = {
    run_id: unified.run_id,
    scenario_label: uScenario.label,
    total_loss_usd: totalLossUsd,
    peak_day: 1,
    time_to_failure_hours: 72,
    actions: dpActions.map(_mapAction),
    all_actions: dpActions.map(_mapAction),
  };

  // ── Explanation ─────────────────────────────────────────
  // v4: sectors.explanation  |  v2: top-level explanation or explainability
  const expData = sectors?.explanation
    ?? (u.explanation as Record<string, unknown>)
    ?? (u.explainability as Record<string, unknown>);
  const explanation: ExplanationPack = {
    run_id: unified.run_id,
    scenario_label: uScenario.label,
    narrative_en: (expData?.summary as string) ?? (expData?.narrative_en as string) ?? "",
    narrative_ar: (expData?.narrative_ar as string) ?? "",
    causal_chain: ((expData?.drivers as Record<string, unknown>[]) ?? []).map((d, i) => ({
      step: i + 1,
      entity_id: "",
      entity_label: (d.driver as string) ?? "",
      entity_label_ar: null,
      event: (d.driver as string) ?? "",
      event_ar: null,
      impact_usd: (d.magnitude as number) ?? 0,
      stress_delta: 0,
      mechanism: (d.unit as string) ?? "",
    })),
    total_steps: ((expData?.drivers as unknown[]) ?? []).length,
    headline_loss_usd: totalLossUsd,
    peak_day: (uHeadline.peak_day as number) ?? 1,
    confidence: confidence,
    methodology: "Unified pipeline: quality→graph→physics→math→sector→decision",
  };

  // ── Headline ────────────────────────────────────────────
  const impactedEntities = mapPayload.impacted_entities ?? [];
  const headline: RunHeadline = {
    total_loss_usd: totalLossUsd,
    peak_day: (uHeadline.peak_day as number) ?? 1,
    max_recovery_days: (uHeadline.max_recovery_days as number) ?? (uScenario.horizon_hours / 24),
    average_stress:
      impactedEntities.length > 0
        ? impactedEntities.reduce((s: number, e: any) => s + (e.stress ?? 0), 0) / impactedEntities.length
        : (uHeadline.average_stress as number) ?? 0,
    affected_entities: (uHeadline.affected_entities as number) ?? (uHeadline.total_nodes_impacted as number) ?? 0,
    critical_count: (uHeadline.critical_count as number)
      ?? impactedEntities.filter((e: any) => e.classification === "CRITICAL").length,
    elevated_count: (uHeadline.elevated_count as number)
      ?? impactedEntities.filter((e: any) => e.classification === "ELEVATED").length,
  };

  // ── Severity / Status ───────────────────────────────────
  const avgStress = headline.average_stress;
  const businessSeverity: BusinessSeverity =
    avgStress >= 0.7
      ? "severe"
      : avgStress >= 0.5
        ? "high"
        : avgStress >= 0.3
          ? "medium"
          : "low";
  const executiveStatus: ExecutiveStatus =
    avgStress >= 0.7
      ? "CRITICAL"
      : avgStress >= 0.5
        ? "SEVERE"
        : avgStress >= 0.3
          ? "ELEVATED"
          : "STABLE";

  // ── Regulatory Events ───────────────────────────────────
  const regState = sectors?.regulatory_state;
  const regulatoryEvents: RegulatoryEvent[] = regState
    ? [
        {
          timestep: 0,
          breach_level: (regState.breach_level as RegulatoryEvent["breach_level"]) ?? "none",
          mandatory_actions: regState.mandatory_actions ?? [],
          sector: "cross_sector",
        },
      ]
    : [];

  // v2 propagation stored in different fields
  const propagationSteps = unified.propagation_steps
    ?? (u.propagation as unknown[])
    ?? [];

  return {
    schema_version: "4.0.0",
    run_id: unified.run_id ?? (u.run_id as string) ?? "",
    status: (unified.status ?? (u.status as string) ?? "completed") as RunResult["status"],
    // CV-01/02 FIX: resolve the string[] vs number type split.
    // Prefer the backend's explicit count; fall back to array length.
    pipeline_stages_completed:
      ((u.pipeline_stages_completed as number) || 0)
      || (unified.stages_completed ?? []).length,
    scenario: {
      ...uScenario,
      label_ar: (rawScenario.label_ar as string) ?? null,
    },
    headline,
    financial,
    banking,
    insurance,
    fintech,
    decisions,
    explanation,
    business_severity: businessSeverity,
    executive_status: executiveStatus,
    model_version: "4.0.0",
    global_confidence: confidence,
    assumptions: unified.assumptions ?? [],
    audit_hash: unified.trust?.audit_hash ?? (u.trace_id as string) ?? "",
    // CV-01/02 FIX: if the backend does not send stages_completed as a string array
    // (it only sends pipeline_stages_completed: number), synthesise a stages array
    // so all consumers (ImpactOverlay, ExecutiveDashboard, persona-view-model) see
    // a non-empty array and do not display "0 stages".
    stages_completed: (() => {
      const fromBackend = unified.stages_completed ?? [];
      if (fromBackend.length > 0) return fromBackend;
      const count = (u.pipeline_stages_completed as number) ?? 0;
      if (count > 0) return Array.from({ length: count }, (_, i) => `stage_${i + 1}`);
      // Last resort: derive from stage_log key count
      const logKeys = Object.keys((unified.stage_log ?? {}) as Record<string, unknown>);
      return logKeys.length > 0 ? logKeys : [];
    })(),
    stage_log: (unified.stage_log ?? {}) as RunResult["stage_log"],
    timeline: [],
    regulatory_events: regulatoryEvents,
    executive_report: {},
    flow_states: [],
    propagation: propagationSteps as RunResult["propagation"],
    duration_ms: unified.duration_ms ?? (u.duration_ms as number) ?? 0,
  };
}

function _classifyStress(stress: number): Classification {
  if (stress >= 0.8) return "CRITICAL";
  if (stress >= 0.6) return "ELEVATED";
  if (stress >= 0.4) return "MODERATE";
  if (stress >= 0.2) return "LOW";
  return "NOMINAL";
}
