"""
Impact Observatory | مرصد الأثر
Simulation constants — single source of truth for all formula weights.

All mathematical constants are defined here as module-level names.
Risk models, physics layer, and decision layer MUST import constants
from this module — never hardcode weights inline.

Formula reference:
  Es  = w1*I  + w2*D  + w3*U  + w4*G
  Exp = alpha_j * Es * V_j * C_j
  X_t+1 = beta*P*X_t + (1-beta)*X_t + S_t
  LSI = l1*W  + l2*F  + l3*M  + l4*C
  ISI = m1*Cf + m2*LR + m3*Re + m4*Od
  NL  = (Exp) * IF_jt * AssetBase_j * theta_j
  Conf= r1*DQ + r2*MC + r3*HS + r4*ST
  URS = g1*Es + g2*AvgExp + g3*AvgStress + g4*PS + g5*LN
"""
from __future__ import annotations

from src.core.config import settings  # noqa: F401

__all__ = ["settings"]

# ═══════════════════════════════════════════════════════════════════════════════
# Event Severity Model
# Es = w1*I + w2*D + w3*U + w4*G
#   I = infrastructure impact score    (node count proxy)
#   D = disruption scale               (base severity)
#   U = utilization stress             (cross-sector activation)
#   G = geopolitical amplification     (regional multiplier)
# ═══════════════════════════════════════════════════════════════════════════════
ES_W1: float = 0.25   # infrastructure impact weight
ES_W2: float = 0.30   # disruption scale weight
ES_W3: float = 0.20   # utilization stress weight
ES_W4: float = 0.25   # geopolitical amplification weight

# Maximum number of shock nodes used for normalization
ES_MAX_SHOCK_NODES: int = 10

# ═══════════════════════════════════════════════════════════════════════════════
# Sector Exposure Model
# Exposure_j = alpha_j * Es * V_j * C_j
#   alpha_j = sector sensitivity coefficient
#   V_j     = vulnerability (1.0 direct, 0.70 indirect, 0.35 second-hop)
#   C_j     = connectivity factor (shock_count / alpha normalizer)
# ═══════════════════════════════════════════════════════════════════════════════
SECTOR_ALPHA: dict[str, float] = {
    "energy":         0.28,
    "maritime":       0.18,
    "banking":        0.20,
    "insurance":      0.08,
    "fintech":        0.06,
    "logistics":      0.10,
    "infrastructure": 0.05,
    "government":     0.03,
    "healthcare":     0.02,
}

# Vulnerability: direct shock / first-hop / second-hop
EXPOSURE_V_DIRECT: float = 1.00
EXPOSURE_V_INDIRECT: float = 0.70
EXPOSURE_V_SECOND_HOP: float = 0.35
EXPOSURE_V_DEFAULT: float = 0.10

# ═══════════════════════════════════════════════════════════════════════════════
# Propagation Model
# X_(t+1) = beta * P * X_t + (1 - beta) * X_t + S_t
#   beta   = propagation coupling coefficient
#   P      = adjacency matrix (row-normalised)
#   X_t    = state vector at time t
#   S_t    = external shock injection at time t (decays with PROP_LAMBDA)
# ═══════════════════════════════════════════════════════════════════════════════
PROP_BETA: float = 0.65     # propagation coupling coefficient
PROP_LAMBDA: float = 0.05   # shock injection decay rate
PROP_CUTOFF: float = 0.005  # early-exit threshold (all nodes below this → stop)

# ═══════════════════════════════════════════════════════════════════════════════
# Liquidity Stress Index
# LSI = l1*W + l2*F + l3*M + l4*C
#   W = withdrawal pressure  (severity × banking_exposure × outflow_rate)
#   F = foreign exposure     (severity × GCC_foreign_dependency)
#   M = market stress        (banking + fintech sector exposure avg)
#   C = collateral stress    (severity × (1 - CAR_buffer))
# ═══════════════════════════════════════════════════════════════════════════════
LSI_L1: float = 0.30   # withdrawal pressure weight
LSI_L2: float = 0.25   # foreign exposure weight
LSI_L3: float = 0.25   # market stress weight
LSI_L4: float = 0.20   # collateral stress weight

# Basel III thresholds
LSI_BASE_OUTFLOW_RATE: float = 0.25
LSI_BANKING_OUTFLOW_COEFF: float = 0.50
LSI_FINTECH_OUTFLOW_COEFF: float = 0.15
LSI_SOVEREIGN_BUFFER: float = 0.85       # GCC sovereign buffer factor
LSI_CAR_BASE: float = 0.105              # minimum CAR ratio
LSI_LCR_SEVERITY_COEFF: float = 0.65    # LCR degrades by this × severity
LSI_GCC_FOREIGN_DEPENDENCY: float = 0.35  # fraction of banking assets foreign

# ═══════════════════════════════════════════════════════════════════════════════
# Insurance Stress Index
# ISI = m1*Cf + m2*LR + m3*Re + m4*Od
#   Cf = claims frequency index      (normalised surge factor)
#   LR = loss ratio                  (0.55 + severity*0.35)
#   Re = reserve erosion             (severity × (1 - reserve_adequacy))
#   Od = operational disruption      (severity × insurance_exposure)
# ═══════════════════════════════════════════════════════════════════════════════
ISI_M1: float = 0.30   # claims frequency weight
ISI_M2: float = 0.30   # loss ratio weight
ISI_M3: float = 0.25   # reserve erosion weight
ISI_M4: float = 0.15   # operational disruption weight

# IFRS-17 thresholds
ISI_CLAIMS_SURGE_COEFF: float = 2.5     # multiplier at max severity
ISI_BASE_LOSS_RATIO: float = 0.55
ISI_SEVERITY_LR_COEFF: float = 0.35
ISI_EXPENSE_RATIO: float = 0.28
ISI_RESERVE_RATIO: float = 0.18         # minimum reserve requirement
ISI_REINSURANCE_COVERAGE: float = 0.60  # GCC average cession rate
ISI_MAX_CLAIMS_SURGE: float = 3.5       # normalisation denominator for Cf

# ═══════════════════════════════════════════════════════════════════════════════
# Financial Loss Model
# NormalizedLoss_j = Exposure_j * ImpactFactor_(j,t) * AssetBase_j * theta_j
#   Exposure_j     = sector exposure score (0–1)
#   ImpactFactor   = severity^2 × prop_factor
#   AssetBase_j    = fraction of scenario base loss allocated to sector j
#   theta_j        = sector loss amplification factor
# ═══════════════════════════════════════════════════════════════════════════════
SECTOR_THETA: dict[str, float] = {
    "energy":         1.40,
    "maritime":       1.20,
    "banking":        1.15,
    "insurance":      1.10,
    "logistics":      1.05,
    "fintech":        1.08,
    "infrastructure": 1.03,
    "government":     1.00,
    "healthcare":     1.00,
}

# Sector base loss allocation fractions (must sum to ≤ 1.0)
SECTOR_LOSS_ALLOCATION: dict[str, float] = {
    "energy":         0.30,
    "maritime":       0.20,
    "banking":        0.18,
    "insurance":      0.10,
    "logistics":      0.08,
    "fintech":        0.06,
    "infrastructure": 0.05,
    "government":     0.02,
    "healthcare":     0.01,
}

# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Score
# Conf = r1*DQ + r2*MC + r3*HS + r4*ST
#   DQ = data quality          (degrades at extreme severities)
#   MC = model coverage        (higher for well-calibrated scenarios)
#   HS = historical similarity (known scenarios have precedent)
#   ST = scenario tractability (degrades with shock node count)
# ═══════════════════════════════════════════════════════════════════════════════
CONF_R1: float = 0.30   # data quality weight
CONF_R2: float = 0.25   # model coverage weight
CONF_R3: float = 0.25   # historical similarity weight
CONF_R4: float = 0.20   # scenario tractability weight

# Well-calibrated GCC scenarios (get higher MC and HS scores)
CONF_WELL_KNOWN_SCENARIOS: frozenset[str] = frozenset({
    "hormuz_chokepoint_disruption",
    "uae_banking_crisis",
    "gcc_cyber_attack",
    "saudi_oil_shock",
    "qatar_lng_disruption",
    "bahrain_sovereign_stress",
    "kuwait_fiscal_shock",
    "oman_port_closure",
})
CONF_DQ_EXTREME_PENALTY: float = 0.40   # penalty factor at extreme severities
CONF_MC_WELL_KNOWN: float = 0.92
CONF_MC_UNKNOWN: float = 0.72
CONF_HS_WELL_KNOWN: float = 0.88
CONF_HS_UNKNOWN: float = 0.65
CONF_ST_NODE_PENALTY: float = 0.04     # per additional shock node beyond first
CONF_ST_MIN: float = 0.55
CONF_ST_MAX: float = 0.97

# ═══════════════════════════════════════════════════════════════════════════════
# Unified Risk Score
# URS = g1*Es + g2*AvgExposure + g3*AvgStress + g4*PropagationScore + g5*LossNorm
#   Es              = event severity score
#   AvgExposure     = mean sector exposure
#   AvgStress       = mean(LSI, ISI)
#   PropagationScore = normalised propagation intensity
#   LossNorm        = severity² (proxy for normalized financial loss)
# ═══════════════════════════════════════════════════════════════════════════════
URS_G1: float = 0.35   # event severity weight           (calibrated: Es range 0.18-0.85)
URS_G2: float = 0.10   # peak sector exposure weight    (calibrated: peak_exp range 0.01-0.28)
URS_G3: float = 0.15   # peak stress weight             (calibrated: max(LSI,ISI) range 0.07-0.50)
URS_G4: float = 0.30   # propagation score weight       (calibrated: PS range 0.6-1.0)
URS_G5: float = 0.10   # normalized loss weight         (severity² proxy range 0.04-1.0)

# ═══════════════════════════════════════════════════════════════════════════════
# Risk Classification Thresholds (0–1 scale)
# Equivalent 0–100 scale: 0–20 Low, 20–35 Guarded, 35–50 Elevated,
#                          50–65 High, 65–80 Severe, 80–100 Critical
# ═══════════════════════════════════════════════════════════════════════════════
RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "NOMINAL":  (0.00, 0.20),
    "LOW":      (0.20, 0.35),
    "GUARDED":  (0.35, 0.50),
    "ELEVATED": (0.50, 0.65),
    "HIGH":     (0.65, 0.80),
    "SEVERE":   (0.80, 1.01),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Scenario Taxonomy & Action Mapping (owned by decision_layer.py)
# ═══════════════════════════════════════════════════════════════════════════════
SCENARIO_TYPES = frozenset(["MARITIME", "ENERGY", "LIQUIDITY", "CYBER", "REGULATORY"])

# Map all 21 GCC scenarios to canonical scenario type
SCENARIO_TAXONOMY: dict[str, str] = {
    # Maritime (port/shipping disruptions)
    "hormuz_chokepoint_disruption":       "MARITIME",
    "hormuz_full_closure":                "MARITIME",
    "oman_port_closure":                  "MARITIME",
    "red_sea_trade_corridor_instability": "MARITIME",
    "critical_port_throughput_disruption": "MARITIME",
    # Energy (oil/gas production/supply)
    "saudi_oil_shock":                    "ENERGY",
    "qatar_lng_disruption":               "ENERGY",
    "kuwait_fiscal_shock":                "ENERGY",
    "energy_market_volatility_shock":     "ENERGY",
    # Liquidity (banking/credit systems)
    "uae_banking_crisis":                 "LIQUIDITY",
    "bahrain_sovereign_stress":           "LIQUIDITY",
    "regional_liquidity_stress_event":    "LIQUIDITY",
    # Cyber (infrastructure attacks)
    "gcc_cyber_attack":                   "CYBER",
    "financial_infrastructure_cyber_disruption": "CYBER",
    # Regulatory/Geopolitical
    "iran_regional_escalation":           "REGULATORY",
}

# Map action template index (0-15) to allowed scenario types
SCENARIO_ACTION_MATRIX: dict[int, set[str]] = {
    0:  {"LIQUIDITY"},                                      # Central bank liquidity injection
    1:  {"MARITIME", "ENERGY"},                             # Trade corridor reopening
    2:  {"ENERGY"},                                         # Energy rationing protocols
    3:  {"LIQUIDITY"},                                      # Interbank lending facility
    4:  {"CYBER", "LIQUIDITY"},                             # Payment system contingency
    5:  {"MARITIME", "ENERGY", "LIQUIDITY"},               # Emergency financing facility
    6:  {"REGULATORY"},                                     # Regulatory forbearance
    7:  {"MARITIME"},                                       # Port rerouting protocols
    8:  {"ENERGY"},                                         # Oil reserves release
    9:  {"LIQUIDITY"},                                      # Reserve requirement reduction
    10: {"CYBER", "LIQUIDITY"},                             # Backup systems activation
    11: {"MARITIME", "ENERGY", "LIQUIDITY", "CYBER"},      # Regional coordination
    12: {"REGULATORY"},                                     # Cross-border exemptions
    13: {"LIQUIDITY"},                                      # Capital controls easing
    14: {"MARITIME", "ENERGY"},                             # Strategic reserve drawdown
    15: {"CYBER"},                                          # Cyber defense mobilization
}

# ═══════════════════════════════════════════════════════════════════════════════
# Physics Constants (owned by physics_intelligence_layer.py)
# ═══════════════════════════════════════════════════════════════════════════════
PHYS_ALPHA: float = 0.08   # shock wave decay coefficient (dP/dt = -α*P + β*Σ)
PHYS_BETA: float = 0.65    # shock wave coupling (same as PROP_BETA for consistency)
PHYS_FLOW_IMBALANCE_THRESHOLD: float = 0.01   # 1% — trigger PhysicsViolationError
PHYS_CONGESTION_ONSET: float = 0.75           # utilisation above this → congestion
PHYS_RECOVERY_BASE_RATE: float = 0.08         # base daily recovery rate

# ═══════════════════════════════════════════════════════════════════════════════
# Decision Layer Priority Formula
# Priority = P_W1*urgency + P_W2*loss_avoided_norm + P_W3*reg_risk
#          + P_W4*feasibility + P_W5*time_effect
# ═══════════════════════════════════════════════════════════════════════════════
DL_P_W1: float = 0.25   # urgency weight
DL_P_W2: float = 0.30   # loss avoided (normalised) weight
DL_P_W3: float = 0.20   # regulatory risk weight
DL_P_W4: float = 0.15   # feasibility weight
DL_P_W5: float = 0.10   # time effect weight

# ═══════════════════════════════════════════════════════════════════════════════
# Transmission Path Engine
# Severity transfer between nodes; breakable-point detection
# ═══════════════════════════════════════════════════════════════════════════════
TX_BASE_DELAY_HOURS: float = 6.0         # base propagation delay per hop
TX_SEVERITY_TRANSFER_RATIO: float = 0.72 # default severity attenuation per hop
TX_BREAKABLE_SEVERITY_THRESHOLD: float = 0.45  # severity above this → breakable
TX_CRITICAL_WINDOW_HOURS: float = 24.0   # delay below this + severity above threshold → breakable

# Sector-specific delay multipliers (higher = slower transmission)
TX_SECTOR_DELAY: dict[str, float] = {
    "energy":         0.8,   # fast — physical commodity flow
    "maritime":       1.0,   # baseline
    "banking":        0.5,   # very fast — electronic settlement
    "insurance":      1.5,   # slower — contractual lag
    "fintech":        0.4,   # fastest — API-based
    "logistics":      1.2,   # physical movement
    "infrastructure": 1.8,   # slow — capex dependent
    "government":     2.0,   # slowest — bureaucratic
    "healthcare":     1.6,   # moderate
}

# Sector-specific severity transfer ratios (higher = more contagious)
TX_SECTOR_TRANSFER: dict[str, float] = {
    "energy":         0.82,
    "maritime":       0.75,
    "banking":        0.88,
    "insurance":      0.65,
    "fintech":        0.80,
    "logistics":      0.70,
    "infrastructure": 0.55,
    "government":     0.50,
    "healthcare":     0.45,
}

# ═══════════════════════════════════════════════════════════════════════════════
# Counterfactual Calibration Engine
# Ensures recommended outcome never contradicts its narrative
# ═══════════════════════════════════════════════════════════════════════════════
CF_MITIGATION_FACTOR: float = 0.35       # default loss reduction from recommended action
CF_ALTERNATIVE_PENALTY: float = 0.15     # cost increase from choosing alternative
CF_COST_TOLERANCE: float = 0.10          # short-term cost increase allowed in recommendation

# ═══════════════════════════════════════════════════════════════════════════════
# Action Pathways Engine
# Classifies actions into IMMEDIATE / CONDITIONAL / STRATEGIC
# ═══════════════════════════════════════════════════════════════════════════════
AP_IMMEDIATE_THRESHOLD_HOURS: int = 6    # time_to_act ≤ this → IMMEDIATE
AP_CONDITIONAL_THRESHOLD_HOURS: int = 48 # 6 < time_to_act ≤ this → CONDITIONAL
AP_REVERSIBILITY_COST_RATIO: float = 0.3 # cost/loss_avoided > this → LOW reversibility

# ═══════════════════════════════════════════════════════════════════════════════
# Executive Classification System
# Maps multi-factor metrics to operational escalation levels (STABLE/ELEVATED/SEVERE/CRITICAL)
# ═══════════════════════════════════════════════════════════════════════════════
EXEC_CLASS_WEIGHTS: dict[str, float] = {
    "severity": 0.35,           # event magnitude (0-1 scale)
    "breach_timing": 0.30,      # time to first regulatory breach (hours)
    "loss_ratio": 0.20,         # peak loss / baseline loss
    "propagation_speed": 0.15,  # velocity of contagion (0-1 scale)
}
EXEC_BREACH_TIMING_MAX_HOURS: float = 72.0  # maximum breach horizon considered
EXEC_LOSS_RATIO_CAP: float = 2.5             # loss ratio ceiling for normalization

# ═══════════════════════════════════════════════════════════════════════════════
# Decision Trust System (Phase 2)
# Action-Level Confidence, Model Dependency, Validation, Risk Envelope
# ═══════════════════════════════════════════════════════════════════════════════

# Action-Level Confidence weights
# confidence = W_SIG*signal + W_DATA*data + W_PROP*propagation + W_CF*counterfactual
TRUST_W_SIGNAL: float = 0.30           # signal strength weight
TRUST_W_DATA: float = 0.30            # data completeness weight
TRUST_W_PROPAGATION: float = 0.20     # propagation clarity weight
TRUST_W_COUNTERFACTUAL: float = 0.20  # counterfactual stability weight

# Confidence label thresholds
TRUST_HIGH_THRESHOLD: float = 0.75    # ≥ this → HIGH
TRUST_LOW_THRESHOLD: float = 0.45     # < this → LOW (between → MEDIUM)

# Model Dependency — base data completeness by sector (known data availability)
TRUST_SECTOR_DATA_COMPLETENESS: dict[str, float] = {
    "energy":         0.88,   # OPEC data, futures pricing — well-observed
    "maritime":       0.72,   # AIS data gaps, port reporting lags
    "banking":        0.82,   # CBUAE/SAMA regulatory reporting
    "insurance":      0.65,   # IFRS 17 transition incomplete across GCC
    "fintech":        0.58,   # limited regulatory visibility
    "logistics":      0.70,   # partial customs data
    "infrastructure": 0.60,   # capex data fragmented
    "government":     0.75,   # sovereign budgets published
    "healthcare":     0.55,   # weakest data coverage in GCC
}

# Validation trigger thresholds
TRUST_VALIDATION_CONFIDENCE_FLOOR: float = 0.50   # confidence below this → require validation
TRUST_VALIDATION_LOSS_THRESHOLD_USD: float = 500_000_000  # loss above this → require validation
TRUST_VALIDATION_DATA_FLOOR: float = 0.55         # data_completeness below this → require validation

# Risk Envelope — downside thresholds
TRUST_DOWNSIDE_HIGH_LOSS_USD: float = 1_000_000_000  # loss above → HIGH downside
TRUST_DOWNSIDE_MEDIUM_LOSS_USD: float = 200_000_000  # loss above → MEDIUM downside
TRUST_TIME_CRITICAL_HOURS: float = 12.0              # propagation < this → CRITICAL time sensitivity
