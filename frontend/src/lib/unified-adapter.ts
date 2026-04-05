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
export function unifiedToRunResult(unified: UnifiedRunResult): RunResult {
  // Cast to any for cross-version field access (v4 unified + v2 legacy schemas)
  const u = unified as unknown as Record<string, unknown>;

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

  void decisionInputs; void graphPayload; void math; void physics;

  // ── Financial Impacts ───────────────────────────────────
  const financial: FinancialImpact[] = (sectors?.financial_impacts ?? []).map(
    (fi) => ({
      entity_id: fi.entity_id,
      entity_label: fi.entity_id.replace(/_/g, " "),
      sector: fi.entity_id.split("_")[0] ?? "finance",
      loss_usd: fi.loss ?? 0,
      loss_pct_gdp: fi.loss ? fi.loss / 2.1e12 : 0,
      peak_day: 1,
      recovery_days: 7,
      confidence: confidence,
      stress_level: fi.loss && fi.exposure ? fi.loss / fi.exposure : 0,
      classification: _classifyStress(
        fi.loss && fi.exposure ? fi.loss / fi.exposure : 0
      ),
    })
  );

  // ── Banking Stress ──────────────────────────────────────
  const bankingAgg = sectors?.banking_aggregate ?? ({} as Record<string, unknown>);
  const banking: BankingStress = {
    run_id: unified.run_id,
    total_exposure_usd: totalLossUsd,
    liquidity_stress:
      1.0 - ((bankingAgg.aggregate_lcr as number) ?? 1.0),
    credit_stress:
      1.0 - ((bankingAgg.aggregate_cet1 as number) ?? 0.045),
    fx_stress: 0.3,
    interbank_contagion: confidence < 0.5 ? 0.7 : 0.3,
    time_to_liquidity_breach_hours: 72,
    capital_adequacy_impact_pct:
      ((bankingAgg.aggregate_car as number) ?? 0.08) * 100,
    aggregate_stress:
      sectorRollups?.banking?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.banking?.aggregate_stress ?? 0
    ),
    affected_institutions: (sectors?.banking_stresses ?? []).map((bs) => ({
      id: bs.entity_id,
      name: bs.entity_id.replace(/_/g, " "),
      name_ar: "",
      country: "GCC",
      exposure_usd: 0,
      stress: 1.0 - bs.lcr,
      projected_car_pct: bs.capital_adequacy_ratio * 100,
    })),
  };

  // ── Insurance Stress ────────────────────────────────────
  const insAgg = sectors?.insurance_aggregate ?? ({} as Record<string, unknown>);
  const insurance: InsuranceStress = {
    run_id: unified.run_id,
    portfolio_exposure_usd: totalLossUsd * 0.15,
    claims_surge_multiplier:
      (insAgg.claims_spike as number) ?? 1.0,
    severity_index: uScenario.severity,
    loss_ratio: 0.75,
    combined_ratio:
      (insAgg.aggregate_combined_ratio as number) ?? 1.0,
    underwriting_status: "stressed",
    time_to_insolvency_hours: 168,
    reinsurance_trigger: true,
    ifrs17_risk_adjustment_pct: 15,
    aggregate_stress:
      sectorRollups?.insurance?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.insurance?.aggregate_stress ?? 0
    ),
    affected_lines: (sectors?.insurance_stresses ?? []).map((is_) => ({
      id: is_.entity_id,
      name: is_.entity_id.replace(/_/g, " "),
      name_ar: "",
      exposure_usd: 0,
      claims_surge: 1.0 - is_.solvency_ratio,
      stress: is_.combined_ratio,
    })),
  };

  // ── Fintech Stress ──────────────────────────────────────
  const ftAgg = sectors?.fintech_aggregate ?? ({} as Record<string, unknown>);
  const fintech: FintechStress = {
    run_id: unified.run_id,
    payment_volume_impact_pct:
      (1.0 - ((ftAgg.aggregate_service_availability as number) ?? 1.0)) * 100,
    settlement_delay_hours:
      ((ftAgg.aggregate_settlement_delay_min as number) ?? 0) / 60,
    api_availability_pct:
      ((ftAgg.aggregate_service_availability as number) ?? 1.0) * 100,
    cross_border_disruption: 0.5,
    digital_banking_stress:
      sectorRollups?.fintech?.aggregate_stress ?? 0,
    time_to_payment_failure_hours: 48,
    aggregate_stress:
      sectorRollups?.fintech?.aggregate_stress ?? 0,
    classification: _classifyStress(
      sectorRollups?.fintech?.aggregate_stress ?? 0
    ),
    affected_platforms: (sectors?.fintech_stresses ?? []).map((ft) => ({
      id: ft.entity_id,
      name: ft.entity_id.replace(/_/g, " "),
      name_ar: "",
      country: "GCC",
      volume_impact_pct: (1.0 - ft.service_availability) * 100,
      cross_border_stress: 0.5,
      stress: 1.0 - ft.service_availability,
    })),
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
      ? "crisis"
      : avgStress >= 0.5
        ? "escalate"
        : avgStress >= 0.3
          ? "intervene"
          : "monitor";

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
    pipeline_stages_completed:
      (unified.stages_completed ?? []).length
      || ((u.pipeline_stages_completed as number) ?? 0),
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
    stages_completed: unified.stages_completed ?? [],
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
