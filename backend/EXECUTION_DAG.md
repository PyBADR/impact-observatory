# EXECUTION DAG — Impact Observatory | مرصد الأثر

**Runtime pipeline contract v2.1.0**
17 sequential stages, deterministic, no LLM, no external I/O during execution.

---

## Pipeline Overview

```
INPUT: ScenarioCreate(scenario_id, severity, horizon_hours)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  Stage 1: Scenario Validation & Catalog Lookup                  │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 2: Graph Bootstrap                                       │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 3: Event Severity  Es = w1*I + w2*D + w3*U + w4*G       │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 4: Sector Exposure  Exp_j = alpha_j * Es * V_j * C_j    │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 5: Propagation  X_(t+1) = β*P*X_t + (1-β)*X_t + S_t    │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 6: Liquidity Stress  LSI = l1*W + l2*F + l3*M + l4*C   │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 7: Insurance Stress  ISI = m1*Cf + m2*LR + m3*Re + m4*Od│
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 8: Unified Risk Score  URS = g1*Es+g2*Exp+g3*Str+g4*P+g5*LN │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 9: Confidence Score  Conf = r1*DQ + r2*MC + r3*HS + r4*ST │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 10: Node Utilization  U_i = load_i / capacity_i         │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 11: Flow Simulation                                      │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 12: Flow Conservation Check + Bottlenecks               │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 13: Shock Wave PDE  dP/dt = -α*P + β*Σ(A_ij*P_j)       │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 14: Recovery Trajectory                                  │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 15: Financial Losses  NL_j = Exp_j * IF_jt * AB_j * θ_j│
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 16: Decision Actions (top 3, priority-ranked)            │
  ├─────────────────────────────────────────────────────────────────┤
  │  Stage 17: Explainability (causal chain 20 steps + narrative)  │
  └─────────────────────────────────────────────────────────────────┘
         │
         ▼
OUTPUT: 16-field result dict + backward-compatible aliases
```

---

## Stage Contracts

### Stage 1 — Scenario Validation & Catalog Lookup

| Attribute | Value |
|-----------|-------|
| **Owner** | `simulation_engine.py` |
| **Inputs** | `scenario_id: str`, `severity: float`, `horizon_hours: int` |
| **Outputs** | `scenario_meta: dict`, `shock_nodes: list[str]`, `base_loss_usd: float`, `peak_day_offset: int`, `sectors_affected: list[str]`, `cross_sector: bool` |
| **Gate** | `scenario_id in SCENARIO_CATALOG` — raises `ValueError` if not found |
| **Failure** | `ValueError: Unknown scenario_id '{id}'. Available: [...]` |
| **Determinism** | Pure dict lookup — always deterministic |

---

### Stage 2 — Graph Bootstrap

| Attribute | Value |
|-----------|-------|
| **Owner** | `simulation_engine.py` |
| **Inputs** | `GCC_NODES: list[dict]`, `GCC_ADJACENCY: dict[str, list[str]]` |
| **Outputs** | `node_sectors: dict[str, str]` (node_id → sector), `adjacency: dict[str, list[str]]` |
| **Gate** | `len(GCC_NODES) == 43`, `len(adjacency) > 0` |
| **Failure** | RuntimeError if GCC_NODES is empty (startup failure) |
| **Determinism** | Static data — always identical |

---

### Stage 3 — Event Severity

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_event_severity()` |
| **Formula** | `Es = ES_W1*I + ES_W2*D + ES_W3*U + ES_W4*G` |
| **Inputs** | `base_severity: float [0,1]`, `n_shock_nodes: int`, `cross_sector: bool` |
| **Outputs** | `event_severity: float [0,1]` |
| **Gate** | Output clamped to [0, 1]; no gate failure |
| **Weight source** | `config.ES_W1=0.25, ES_W2=0.30, ES_W3=0.20, ES_W4=0.25` |
| **Variables** | I=infra_impact, D=disruption_scale, U=utilization_stress, G=geopolitical_factor |

---

### Stage 4 — Sector Exposure

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_sector_exposure()` |
| **Formula** | `Exposure_j = alpha_j * Es * V_j * C_j` |
| **Inputs** | `shock_nodes: list[str]`, `severity: float`, `node_sectors: dict[str,str]` |
| **Outputs** | `sector_exposure: dict[str, float]` (9 sectors, each 0–1) |
| **Gate** | All values clamped to [0, 1] |
| **Weight source** | `config.SECTOR_ALPHA`, `config.EXPOSURE_V_*` |
| **Variables** | alpha_j=sector_sensitivity, V_j=vulnerability, C_j=connectivity_factor |

---

### Stage 5 — Propagation Model

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_propagation()` |
| **Formula** | `X_(t+1) = β*P*X_t + (1-β)*X_t + S_t` |
| **Inputs** | `shock_nodes: list[str]`, `severity: float`, `adjacency: dict`, `horizon_days: int` |
| **Outputs** | `propagation_raw: list[dict]` (max 20 rows, sorted by impact desc) |
| **Gate** | Returns empty list if no nodes; early-exit if all X < PROP_CUTOFF=0.005 |
| **Weight source** | `config.PROP_BETA=0.65`, `config.PROP_LAMBDA=0.05` |
| **Variables** | β=coupling_coefficient, P=adjacency_matrix, S_t=decaying_shock_injection |

---

### Stage 6 — Liquidity Stress Index

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_liquidity_stress()` |
| **Formula** | `LSI = l1*W + l2*F + l3*M + l4*C` |
| **Inputs** | `severity: float`, `sector_exposure: dict[str, float]` |
| **Outputs** | `{lsi, aggregate_stress, liquidity_stress, lcr_ratio, car_ratio, outflow_rate, time_to_breach_hours, classification}` |
| **Gate** | All components clamped to [0, 1] |
| **Weight source** | `config.LSI_L1=0.30, L2=0.25, L3=0.25, L4=0.20` |
| **Variables** | W=withdrawal_pressure, F=foreign_exposure, M=market_stress, C=collateral_stress |
| **Regulatory** | LCR breach when `lcr_ratio < 1.0`; CAR breach when `car_ratio < 0.105` |

---

### Stage 7 — Insurance Stress Index

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_insurance_stress()` |
| **Formula** | `ISI = m1*Cf + m2*LR + m3*Re + m4*Od` |
| **Inputs** | `severity: float`, `sector_exposure: dict[str, float]` |
| **Outputs** | `{isi, severity_index, claims_surge_multiplier, combined_ratio, reserve_adequacy, tiv_exposure, loss_ratio, classification}` |
| **Gate** | All components clamped to [0, 1]; combined_ratio may exceed 1.0 (stress indicator) |
| **Weight source** | `config.ISI_M1=0.30, M2=0.30, M3=0.25, M4=0.15` |
| **Variables** | Cf=claims_frequency, LR=loss_ratio, Re=reserve_erosion, Od=operational_disruption |
| **Regulatory** | Combined ratio breach when `combined_ratio > 1.10` |

---

### Stage 8 — Unified Risk Score

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_unified_risk_score()` |
| **Formula** | `URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropScore + g5*LossNorm` |
| **Inputs** | `severity`, `propagation_score`, `liquidity_stress`, `insurance_stress`, `sector_exposure`, `event_severity` |
| **Outputs** | `{score: float, components: dict, risk_level: str, classification: str}` |
| **Gate** | Score clamped to [0, 1] |
| **Weight source** | `config.URS_G1=0.25, G2=0.20, G3=0.20, G4=0.20, G5=0.15` |
| **Risk levels** | NOMINAL(<0.20), LOW(<0.35), GUARDED(<0.50), ELEVATED(<0.65), HIGH(<0.80), SEVERE(≥0.80) |

---

### Stage 9 — Confidence Score

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_confidence_score()` |
| **Formula** | `Conf = r1*DQ + r2*MC + r3*HS + r4*ST` |
| **Inputs** | `n_shock_nodes: int`, `severity: float`, `scenario_id: str` |
| **Outputs** | `confidence_score: float [0.50, 0.98]` |
| **Gate** | Output bounded to [0.50, 0.98] by component constraints |
| **Weight source** | `config.CONF_R1=0.30, R2=0.25, R3=0.25, R4=0.20` |
| **Variables** | DQ=data_quality, MC=model_coverage, HS=historical_similarity, ST=scenario_tractability |

---

### Stage 10 — Node Utilization

| Attribute | Value |
|-----------|-------|
| **Owner** | `physics_intelligence_layer.compute_node_utilization()` |
| **Formula** | `U_i = (base_load + Δload) / capacity; Δload = severity*(1-U_base)*criticality*capacity` |
| **Inputs** | `nodes: list[dict]` (43 GCC nodes), `severity: float` |
| **Outputs** | `node_utilization: list[dict]` with {node_id, utilization, saturation_status, capacity, load} |
| **Gate** | Utilization may exceed 1.0 (overflow) — capped at 1.20 (20% overflow indicator) |
| **Failure** | None (graceful — never raises) |

---

### Stage 11 — Flow Simulation

| Attribute | Value |
|-----------|-------|
| **Owner** | `flow_models.simulate_all_flows()` |
| **Inputs** | `severity: float`, `congestion_score: float`, `sector_exposure: dict` |
| **Outputs** | `flow_analysis: dict` with 5 flow types (money, logistics, energy, payments, claims) + aggregate |
| **Gate** | None (graceful — never raises) |
| **GCC flows** | Money $42B/day, Logistics $18B/day, Energy $580M/day, Payments $8B/day, Claims $120M/day |

---

### Stage 12 — Flow Conservation + Bottlenecks

| Attribute | Value |
|-----------|-------|
| **Owner** | `physics_intelligence_layer.check_flow_conservation()` + `compute_bottleneck_scores()` |
| **Formula** | `B_i = U_i * criticality_i * (1/(redundancy_i + 0.1)) * connectivity_bonus` |
| **Inputs** | `nodes: list[dict]`, `flow_records: list[dict]`, `node_utilization: list[dict]`, `adjacency: dict` |
| **Outputs** | `physical_system_status: dict`, `bottlenecks: list[dict]`, `flow_balance_status: str` |
| **Gate** | `PhysicsViolationError` raised if node imbalance > 1% (PHYS_FLOW_IMBALANCE_THRESHOLD) |
| **Failure mode** | Caught in simulation_engine Stage 12b → `flow_balance_status = "VIOLATION_DETECTED"` — execution continues |

---

### Stage 13 — Shock Wave PDE

| Attribute | Value |
|-----------|-------|
| **Owner** | `physics_intelligence_layer.propagate_shock_wave()` |
| **Formula** | `dP/dt = -α*P + β*Σ_j(A_ij*P_j)` discretised as `P_new = P + dP` |
| **Inputs** | `shock_nodes: list[str]`, `severity: float`, `adjacency: dict`, `n_steps: int` |
| **Outputs** | `shock_wave: list[dict]` with {step, node_id, shock_intensity, cumulative_damage, affected_nodes} |
| **Gate** | Early exit when all P < 0.003 |
| **Constants** | `config.PHYS_ALPHA=0.08`, `config.PHYS_BETA=0.65` |

---

### Stage 14 — Recovery Trajectory

| Attribute | Value |
|-----------|-------|
| **Owner** | `physics_intelligence_layer.compute_recovery_trajectory()` |
| **Formula** | `R(t+1) = R(t) + r*(1 - Damage(t)) - ResidualStress(t)` |
| **Inputs** | `severity: float`, `peak_day: int`, `horizon_days: int`, `sector: str` |
| **Outputs** | `recovery_trajectory: list[dict]` with {day, recovery_fraction, damage_remaining, residual_stress} |
| **Gate** | Early exit when recovery ≥ 99% |
| **Recovery rates** | energy: 7%/day, banking: 12%/day, fintech: 14%/day (see config) |

---

### Stage 15 — Financial Losses

| Attribute | Value |
|-----------|-------|
| **Owner** | `risk_models.compute_financial_losses()` |
| **Formula** | `NL_j = Exposure_j * ImpactFactor_(j,t) * AssetBase_j * theta_j` |
| **Inputs** | `severity: float`, `scenario_base_loss: float`, `propagation: list[dict]`, `sector_exposure: dict` |
| **Outputs** | `financial_losses: list[dict]` (top 20 entities, each with loss_usd, classification, peak_day) |
| **Gate** | Returns empty list if propagation is empty |
| **Theta factors** | energy: 1.40, maritime: 1.20, banking: 1.15 (see `config.SECTOR_THETA`) |

---

### Stage 16 — Decision Actions

| Attribute | Value |
|-----------|-------|
| **Owner** | `decision_layer.build_decision_actions()` + `build_five_questions()` + `compute_escalation_triggers()` |
| **Formula** | `Priority_k = 0.25*U + 0.30*V + 0.20*R + 0.15*F + 0.10*T` |
| **Inputs** | `scenario_id`, `severity`, `risk_level`, `liquidity_stress`, `insurance_stress`, `bottlenecks`, `sector_exposure`, `headline` |
| **Outputs** | `decision_plan: dict` with {actions: top-3, escalation_triggers, monitoring_priorities, business_severity, time_to_first_failure_hours} |
| **Gate** | Always returns at least 1 action |
| **Five questions** | what_happened, what_is_the_impact, what_is_affected, how_big_is_the_risk, recommended_actions |

---

### Stage 17 — Explainability

| Attribute | Value |
|-----------|-------|
| **Owner** | `explainability.build_causal_chain()` + `build_narrative()` + `compute_sensitivity()` + `compute_uncertainty_bands()` |
| **Inputs** | `scenario_id`, `event_severity`, `propagation_raw`, `sector_exposure`, `unified_risk_score`, `confidence_score`, `financial_losses`, `decision_actions` |
| **Outputs** | `explainability: dict` with {narrative_en, narrative_ar, causal_chain (20 steps), methodology, model_equation, confidence_score, sensitivity, uncertainty_bands} |
| **Gate** | Causal chain always expands to exactly 20 steps via sub-step synthesis if propagation < 20 rows |
| **Model equation** | `R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U` (display form) |

---

## Failure Mode Summary

| Stage | Failure Type | Handling |
|-------|-------------|----------|
| 1 — Validation | `ValueError` | Propagates to HTTP 400 (via global handler in main.py) |
| 2 — Graph | `RuntimeError` | Fatal — startup failure |
| 12b — Flow Conservation | `PhysicsViolationError` | Caught, sets `flow_balance_status = "VIOLATION_DETECTED"`, continues |
| Any other stage | `Exception` | Caught in simulation_engine, logged, stage output replaced with safe default |

---

## Output Contract — 16 Mandatory Fields

Every call to `SimulationEngine.run()` MUST return all 16 fields:

```python
{
    "scenario_id":           str,
    "model_version":         str,       # "2.1.0"
    "time_horizon_days":     int,
    "event_severity":        float,     # Es, [0,1]
    "peak_day":              int,
    "confidence_score":      float,     # Conf, [0,1]
    "financial_impact":      dict,      # {total_loss_usd, top_entities}
    "sector_analysis":       list,      # per-sector stress objects
    "propagation_score":     float,     # [0,1]
    "unified_risk_score":    float,     # URS, [0,1]
    "risk_level":            str,       # NOMINAL|LOW|GUARDED|ELEVATED|HIGH|SEVERE
    "physical_system_status":dict,      # node counts, flow balance
    "bottlenecks":           list,      # top bottleneck nodes
    "congestion_score":      float,     # [0,1]
    "recovery_score":        float,     # [0,1]
    "explainability":        dict,      # narrative, causal chain, sensitivity
    "decision_plan":         dict,      # top-3 actions, 5 questions
}
```

---

## Execution Time Budget

| Stage | Target (ms) | Alert Threshold (ms) |
|-------|------------|---------------------|
| 1–3 (Validation + Severity) | < 5 | 20 |
| 4–5 (Exposure + Propagation) | < 50 | 200 |
| 6–9 (Stress + URS + Conf) | < 30 | 100 |
| 10–14 (Physics + Recovery) | < 80 | 300 |
| 15–17 (Loss + Decision + Explain) | < 100 | 400 |
| **Total pipeline** | **< 300** | **1000** |

---

*Generated: 2026-04-03 | Model version: 2.1.0 | Stages: 17 | Scenarios: 15*
