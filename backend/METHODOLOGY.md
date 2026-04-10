# Impact Observatory — Methodology Reference
## Model v2.1.0 | April 2026

---

## 1. Event Severity Model

**File:** `src/risk_models.py` → `compute_event_severity`

### Equation

```
S = base_severity × cascade_multiplier × (1 + regional_amplification)

cascade_multiplier     = 1 + 0.3 × n_shock_nodes + 0.2 × cross_sector_factor
regional_amplification = base_severity × 0.4
```

### Variables

| Symbol | Description | Range |
|--------|-------------|-------|
| `base_severity` | User-supplied shock intensity | [0.01, 1.0] |
| `n_shock_nodes` | Number of directly-shocked nodes | Integer ≥ 1 |
| `cross_sector_factor` | 1 if event crosses sector boundaries, else 0 | {0, 1} |
| `regional_amplification` | GCC systemic interconnect factor | [0, 0.4] |

### Rationale
The 0.4 GCC regional amplification coefficient reflects the high systemic
interconnectedness of GCC economies (hydrocarbon dependency, shared currency pegs,
cross-border banking exposures). The 0.3 per-node multiplier is calibrated to
historical GCC disruption events.

---

## 2. Sector Exposure Model

**File:** `src/risk_models.py` → `compute_sector_exposure`

### Equation

```
E_i = w_k × dependency_ik × proximity_i

Where:
  w_k           = sector GDP weight
  dependency_ik = cross-sector dependency factor (1.0 direct, 0.70 1st-hop, 0.35 2nd-hop, 0.10 none)
  proximity_i   = derived from hop distance to shock node
```

### Sector Weights (GCC GDP calibrated)

| Sector | Weight |
|--------|--------|
| Energy | 0.28 |
| Banking | 0.20 |
| Maritime | 0.18 |
| Logistics | 0.10 |
| Insurance | 0.08 |
| Fintech | 0.06 |
| Infrastructure | 0.05 |
| Government | 0.03 |
| Healthcare | 0.02 |

---

## 3. Propagation Model

**File:** `src/risk_models.py` → `compute_propagation`

### Equation (discrete-time epidemic model)

```
P_i(t) = P_i(0) × e^(-λt) + Σ_j [A_ij × P_j(t-1)]

λ = 0.05   (decay rate — shock attenuates over time)
A_ij = row-normalised adjacency matrix weight
```

### Physics Shock Propagation (continuous analog)

**File:** `src/physics_intelligence_layer.py` → `propagate_shock_wave`

```
dP/dt = -α × P + β × Σ_j [A_ij × P_j]

α = 0.08   (attenuation coefficient)
β = 0.65   (amplification coefficient)
```

Discretised as: `P(t+1) = P(t) + (-α × P(t) + β × A_norm @ P(t))`

---

## 4. Liquidity Stress Index (Basel III)

**File:** `src/risk_models.py` → `compute_liquidity_stress`

### Equations

```
L = (outflow_rate × severity) / (buffer × CAR_ratio)

outflow_rate = 0.25 + 0.50 × banking_exposure + 0.15 × fintech_exposure
buffer       = 0.85   (GCC sovereign buffer factor)
CAR_ratio    = 0.105 + max(0, 0.05 - severity × 0.04)   ∈ [0.085, 0.20]
LCR_ratio    = 1.0 - severity × 0.65

time_to_breach_hours = (buffer × CAR_ratio / daily_drain) × 24
daily_drain = outflow_rate × severity
```

### Basel III Thresholds

| Ratio | Minimum | Description |
|-------|---------|-------------|
| CAR | 10.5% | Capital Adequacy Ratio (Tier 1 + Tier 2 + Buffer) |
| LCR | 100% | Liquidity Coverage Ratio |
| NSFR | 100% | Net Stable Funding Ratio |

**Trigger:** If `LCR < 1.0` → emergency liquidity escalation.

---

## 5. Insurance Stress Index (IFRS-17)

**File:** `src/risk_models.py` → `compute_insurance_stress`

### Equations

```
IS = (claims_surge × TIV_exposure) / (reserve_ratio × reinsurance_coverage)

claims_surge_multiplier = 1.0 + severity × 2.5
TIV_exposure            = insurance_exposure + energy_exposure × 0.3
reserve_ratio           = 0.18   (GCC industry minimum)
reinsurance_coverage    = 0.60   (GCC average treaty retention)

loss_ratio     = 0.55 + severity × 0.35
expense_ratio  = 0.28
combined_ratio = loss_ratio + expense_ratio

reserve_adequacy = reserve_ratio / (TIV_exposure × severity + ε)
```

### IFRS-17 Compliance

The combined ratio tracks the IFRS-17 insurance contract liability measurement.
A combined ratio > 1.0 indicates underwriting losses; > 1.10 triggers escalation.

---

## 6. Financial Loss Model

**File:** `src/risk_models.py` → `compute_financial_losses`

### Equation

```
Loss_i = base_loss × severity² × sector_weight_i × propagation_factor_i × (1 + exposure_i)

Direct loss:   Loss × 0.60
Indirect loss: Loss × 0.28
Systemic loss: Loss × 0.12
Total:         Direct + Indirect + Systemic = Loss
```

The quadratic severity term reflects empirical evidence that financial losses
scale super-linearly with disruption intensity.

---

## 7. Confidence Score

**File:** `src/risk_models.py` → `compute_confidence_score`

### Equation

```
C = 0.30 × data_quality + 0.25 × model_coverage
  + 0.25 × scenario_precedent + 0.20 × node_completeness

data_quality        = 1.0 - |severity - 0.5| × 0.4    (degrades at extremes)
model_coverage      = 0.92 (known scenario) | 0.72 (novel)
scenario_precedent  = 0.88 (historical) | 0.65 (hypothetical)
node_completeness   = 1.0 - (n_shock_nodes - 1) × 0.04
```

### Weights

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Data quality | 30% | Primary driver of model accuracy |
| Model coverage | 25% | GCC-calibrated scenarios are better covered |
| Scenario precedent | 25% | Historical precedents reduce uncertainty |
| Node completeness | 20% | More nodes = marginal per-node degradation |

---

## 8. Unified Risk Score

**File:** `src/risk_models.py` → `compute_unified_risk_score`

### Equation

```
R = 0.20 × G + 0.25 × P + 0.15 × N + 0.20 × L + 0.10 × T + 0.10 × U

G = Geopolitical   (event_severity)
P = Propagation    (propagation_score)
N = Network        (mean sector exposure)
L = Liquidity      (aggregate_stress)
T = Threat Field   (insurance_stress × severity)
U = Utilization    (max sector exposure)
```

### Weight Rationale

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Propagation | 25% | Key GCC cascade driver |
| Liquidity | 20% | Basel III systemic risk proxy |
| Geopolitical | 20% | GCC geopolitical risk premium |
| Network | 15% | Graph topology stress |
| Utilization | 10% | Infrastructure headroom |
| Threat Field | 10% | Insurance system strain |

---

## 9. Risk Threshold Table

| Classification | Score Range | Recommended Action |
|----------------|-------------|-------------------|
| NOMINAL | 0.00 – 0.20 | Standard monitoring |
| LOW | 0.20 – 0.35 | Enhanced surveillance |
| GUARDED | 0.35 – 0.50 | Precautionary measures |
| ELEVATED | 0.50 – 0.65 | Activate contingency plans |
| HIGH | 0.65 – 0.80 | Emergency protocols |
| SEVERE | 0.80 – 1.00 | Crisis management — full mobilisation |

---

## 10. Node Utilization Model

**File:** `src/physics_intelligence_layer.py` → `compute_node_utilization`

### Equations

```
U_base_i = current_load_i / capacity_i
ΔLoad_i  = severity × (1 - U_base_i) × criticality_i × capacity_i
U_i      = (base_load + ΔLoad_i) / capacity_i   [can exceed 1.0 — overflow state]

Saturation threshold: 0.85
```

---

## 11. Bottleneck Score

**File:** `src/physics_intelligence_layer.py` → `compute_bottleneck_scores`

### Equation

```
B_i = U_i × criticality_i × (1 / (redundancy_i + 0.1))
      × (0.7 + 0.3 × connectivity_bonus)

connectivity_bonus = log(1 + degree_i) / log(1 + max_degree)

Critical bottleneck: B_i > 0.75
```

---

## 12. Recovery Trajectory

**File:** `src/physics_intelligence_layer.py` → `compute_recovery_trajectory`

### Equations

```
R(t+1) = R(t) + r × (1 - Damage(t)) - max(0, ResidualStress(t) × 0.1)
Damage(t) = severity × (1 - R(t))
ResidualStress(t) = severity × e^(-0.12 × max(0, t - peak_day))
```

### Sector Recovery Rates

| Sector | Rate (r) |
|--------|----------|
| Fintech | 0.14 |
| Government | 0.15 |
| Banking | 0.12 |
| Insurance | 0.10 |
| Logistics | 0.08 |
| Energy | 0.07 |
| Maritime | 0.06 |
| Healthcare | 0.09 |
| Infrastructure | 0.05 |

---

## 13. Congestion Score

**File:** `src/physics_intelligence_layer.py` → `compute_congestion`

### Equation

```
CG_i = max(0, U_i - τ) / (1 - τ)    τ = 0.75 (congestion threshold)

System_congestion = Σ(CG_i × capacity_i) / Σ(capacity_i)
```

---

## 14. Decision Priority Formula

**File:** `src/decision_layer.py` → `_compute_priority`

### Equation

```
Priority = 0.25 × urgency
         + 0.30 × loss_avoided_normalised
         + 0.20 × regulatory_risk
         + 0.15 × feasibility
         + 0.10 × time_effect

time_effect: ≤6h → 1.0 | ≤24h → 0.75 | ≤48h → 0.50 | >48h → 0.25
```

---

## 15. Flow Disruption Model

**File:** `src/flow_models.py`

### Equations

```
disruption_factor = severity × sensitivity × (1 + sector_stress × 0.25)
disrupted_volume  = base_volume × (1 - disruption_factor)
backlog_usd       = disrupted_volume × disruption_factor × max(1, delay_days / 7)
rerouting_cost    = disrupted_volume × rerouting_premium × (1 + disruption_factor)
saturation_pct    = (disrupted_volume / channel_capacity) × 100 × (1 + disruption_factor × 0.40)
```

### GCC Baseline Daily Volumes

| Flow Type | Daily Volume (USD) | Sensitivity |
|-----------|--------------------|-------------|
| Money | $42B | 0.70 |
| Logistics | $18B | 0.75 |
| Energy | $580M | 0.85 |
| Payments | $8B | 0.60 |
| Claims | $120M | 0.50 |

---

## 16. Sensitivity Analysis

**File:** `src/explainability.py` → `compute_sensitivity`

Severity is perturbed at ±10%, ±20%. Loss changes quadratically (severity²),
risk score changes linearly. Linearity score measures consistency of proportional
changes across perturbation levels.

---

## 17. Uncertainty Bands

**File:** `src/explainability.py` → `compute_uncertainty_bands`

```
band_width    = (1 - confidence) × 0.40
lower_bound   = max(0, base_score - band_width / 2)
upper_bound   = min(1, base_score + band_width / 2)
```

At 85% confidence, band width = 0.06 (±3 percentage points).
At 65% confidence, band width = 0.14 (±7 percentage points).

---

## References

- Basel Committee on Banking Supervision (BCBS), "Basel III: A global regulatory framework", 2010/2017
- IFRS Foundation, "IFRS 17 Insurance Contracts", 2017
- IMF, "GCC Financial Stability Report", 2023
- BIS, "Global Systemically Important Banks", 2024
- Arab Monetary Fund, "GCC Banking Sector Report", 2024
