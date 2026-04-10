/**
 * Macro Intelligence Demo — Multi-Scenario Data Engine
 *
 * 15 GCC macroeconomic shock scenarios aligned to backend SCENARIO_CATALOG.
 * Each scenario carries a full narrative payload consumed by the 6 demo components:
 *   MacroHero → TransmissionFlow → ExposureLayer → DecisionEngine → Outcome → TrustStrip
 *
 * Data contract:
 *   - Interfaces are STABLE — sub-components import them directly.
 *   - ScenarioMeta adds selector-level metadata (domain, icon, base loss).
 *   - scenarioCatalog is the single source of truth for the demo layer.
 *   - demoData remains as the default (backward-compat with existing imports).
 */

// ─── Core Interfaces (consumed by sub-components — DO NOT CHANGE) ───────────

export interface DemoShock {
  title: string;
  subtitle: string;
  severity: number;
  impact: number;
}

export interface TransmissionNode {
  label: string;
  delay: string;
}

export interface ExposureEntry {
  country: string;
  percent: number;
  flag: string;
}

export interface DecisionOption {
  action: string;
  value: number;
  tag: "recommended" | "alternative" | "risk";
}

export interface DemoOutcome {
  net: number;
  confidence: number;
  label: string;
}

export interface DemoTrust {
  model: string;
  hash: string;
  pipeline: string;
  latency: string;
}

export interface DemoData {
  shock: DemoShock;
  transmission: TransmissionNode[];
  exposure: ExposureEntry[];
  decisions: DecisionOption[];
  outcome: DemoOutcome;
  trust: DemoTrust;
}

// ─── Scenario Metadata (selector + catalog layer) ───────────────────────────

export type ScenarioDomain =
  | "MARITIME"
  | "ENERGY"
  | "FINANCIAL"
  | "CYBER"
  | "TRADE"
  | "INFRASTRUCTURE"
  | "GEOPOLITICAL";

export interface ScenarioMeta {
  id: string;
  name: string;
  domain: ScenarioDomain;
  baseLossLabel: string;
  peakDay: string;
  sectors: string[];
}

export interface DemoScenario {
  meta: ScenarioMeta;
  data: DemoData;
}

// ─── Shared trust baseline ──────────────────────────────────────────────────

const trust: DemoTrust = {
  model: "MacroGraph v1.4",
  hash: "0xA91F…3XZ7",
  pipeline: "17-stage deterministic",
  latency: "1.2s",
};

// ─── Scenario Catalog (15 scenarios) ────────────────────────────────────────

export const scenarioCatalog: DemoScenario[] = [
  // ── 1. Hormuz Chokepoint Disruption ────────────────────────────────────
  {
    meta: {
      id: "hormuz_chokepoint_disruption",
      name: "Hormuz Chokepoint Disruption",
      domain: "MARITIME",
      baseLossLabel: "$3.2B",
      peakDay: "Day 3",
      sectors: ["Energy", "Banking", "Insurance", "Fintech"],
    },
    data: {
      shock: {
        title: "Hormuz Disruption",
        subtitle: "Strait of Hormuz partial blockage detected — 17.4M bbl/day at risk",
        severity: 78,
        impact: 93,
      },
      transmission: [
        { label: "Oil Supply ↑", delay: "0h" },
        { label: "Liquidity Stress", delay: "+2h" },
        { label: "Banking Impact", delay: "+6h" },
        { label: "Insurance Loss", delay: "+12h" },
        { label: "Fintech Slowdown", delay: "+24h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 42, flag: "🇸🇦" },
        { country: "UAE", percent: 28, flag: "🇦🇪" },
        { country: "Kuwait", percent: 18, flag: "🇰🇼" },
        { country: "Qatar", percent: 8, flag: "🇶🇦" },
        { country: "Bahrain", percent: 4, flag: "🇧🇭" },
      ],
      decisions: [
        { action: "Activate Strategic Petroleum Reserve", value: 120, tag: "recommended" },
        { action: "Re-route GCC Exports via Fujairah", value: 60, tag: "alternative" },
        { action: "Do Nothing — Absorb Shock", value: -93, tag: "risk" },
      ],
      outcome: { net: 87, confidence: 92, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 2. Hormuz Full Closure ─────────────────────────────────────────────
  {
    meta: {
      id: "hormuz_full_closure",
      name: "Hormuz Full Closure",
      domain: "MARITIME",
      baseLossLabel: "$8.5B",
      peakDay: "Day 1",
      sectors: ["Energy", "Maritime", "Banking", "Insurance"],
    },
    data: {
      shock: {
        title: "Hormuz Full Closure",
        subtitle: "Complete strait shutdown — zero maritime throughput, 21M bbl/day halted",
        severity: 97,
        impact: 99,
      },
      transmission: [
        { label: "Maritime Halt", delay: "0h" },
        { label: "Oil Price Spike", delay: "+1h" },
        { label: "Port Congestion", delay: "+4h" },
        { label: "Banking Freeze", delay: "+8h" },
        { label: "Insurance Crisis", delay: "+16h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 38, flag: "🇸🇦" },
        { country: "UAE", percent: 30, flag: "🇦🇪" },
        { country: "Kuwait", percent: 15, flag: "🇰🇼" },
        { country: "Qatar", percent: 12, flag: "🇶🇦" },
        { country: "Oman", percent: 5, flag: "🇴🇲" },
      ],
      decisions: [
        { action: "Emergency SPR + OPEC Coordination", value: 180, tag: "recommended" },
        { action: "Activate Fujairah Bypass Pipeline", value: 95, tag: "alternative" },
        { action: "Wait for Diplomatic Resolution", value: -210, tag: "risk" },
      ],
      outcome: { net: 72, confidence: 78, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 3. Saudi Oil Shock ─────────────────────────────────────────────────
  {
    meta: {
      id: "saudi_oil_shock",
      name: "Saudi Oil Shock",
      domain: "ENERGY",
      baseLossLabel: "$2.8B",
      peakDay: "Day 4",
      sectors: ["Energy", "Banking"],
    },
    data: {
      shock: {
        title: "Saudi Oil Shock",
        subtitle: "Aramco production disruption — 5.7M bbl/day capacity at risk",
        severity: 82,
        impact: 88,
      },
      transmission: [
        { label: "Production Drop", delay: "0h" },
        { label: "Supply Squeeze", delay: "+3h" },
        { label: "Revenue Pressure", delay: "+8h" },
        { label: "Fiscal Stress", delay: "+18h" },
        { label: "Credit Tightening", delay: "+36h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 58, flag: "🇸🇦" },
        { country: "UAE", percent: 18, flag: "🇦🇪" },
        { country: "Kuwait", percent: 10, flag: "🇰🇼" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
        { country: "Oman", percent: 6, flag: "🇴🇲" },
      ],
      decisions: [
        { action: "Deploy Spare Capacity + OPEC Swap", value: 140, tag: "recommended" },
        { action: "Accelerate Non-Oil Revenue Streams", value: 55, tag: "alternative" },
        { action: "Absorb Fiscal Impact", value: -120, tag: "risk" },
      ],
      outcome: { net: 81, confidence: 89, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 4. UAE Banking Crisis ──────────────────────────────────────────────
  {
    meta: {
      id: "uae_banking_crisis",
      name: "UAE Banking Crisis",
      domain: "FINANCIAL",
      baseLossLabel: "$1.8B",
      peakDay: "Day 5",
      sectors: ["Banking"],
    },
    data: {
      shock: {
        title: "UAE Banking Crisis",
        subtitle: "Systemic credit event at DIFC — interbank market under severe stress",
        severity: 71,
        impact: 79,
      },
      transmission: [
        { label: "Credit Freeze", delay: "0h" },
        { label: "Interbank Spread", delay: "+2h" },
        { label: "Deposit Flight", delay: "+8h" },
        { label: "Liquidity Drain", delay: "+14h" },
        { label: "Contagion Risk", delay: "+24h" },
      ],
      exposure: [
        { country: "UAE", percent: 52, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 20, flag: "🇸🇦" },
        { country: "Bahrain", percent: 14, flag: "🇧🇭" },
        { country: "Kuwait", percent: 8, flag: "🇰🇼" },
        { country: "Qatar", percent: 6, flag: "🇶🇦" },
      ],
      decisions: [
        { action: "CBUAE Emergency Liquidity Facility", value: 95, tag: "recommended" },
        { action: "Cross-Border Deposit Guarantee", value: 50, tag: "alternative" },
        { action: "Let Market Self-Correct", value: -85, tag: "risk" },
      ],
      outcome: { net: 79, confidence: 86, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 5. GCC Cyber Attack ────────────────────────────────────────────────
  {
    meta: {
      id: "gcc_cyber_attack",
      name: "GCC Cyber Attack",
      domain: "CYBER",
      baseLossLabel: "$950M",
      peakDay: "Day 1",
      sectors: ["Fintech", "Banking"],
    },
    data: {
      shock: {
        title: "GCC Cyber Attack",
        subtitle: "Coordinated attack on SWIFT GCC + payment rails — transactions halted",
        severity: 74,
        impact: 81,
      },
      transmission: [
        { label: "Payment Halt", delay: "0h" },
        { label: "SWIFT Isolation", delay: "+1h" },
        { label: "ATM Outage", delay: "+3h" },
        { label: "Settlement Failure", delay: "+6h" },
        { label: "Trust Collapse", delay: "+12h" },
      ],
      exposure: [
        { country: "UAE", percent: 35, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 32, flag: "🇸🇦" },
        { country: "Qatar", percent: 14, flag: "🇶🇦" },
        { country: "Kuwait", percent: 11, flag: "🇰🇼" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
      ],
      decisions: [
        { action: "Activate GCC Cyber Defense Protocol", value: 85, tag: "recommended" },
        { action: "Switch to Manual Settlement", value: 35, tag: "alternative" },
        { action: "Wait for System Recovery", value: -68, tag: "risk" },
      ],
      outcome: { net: 76, confidence: 83, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 6. Qatar LNG Disruption ────────────────────────────────────────────
  {
    meta: {
      id: "qatar_lng_disruption",
      name: "Qatar LNG Disruption",
      domain: "ENERGY",
      baseLossLabel: "$1.4B",
      peakDay: "Day 2",
      sectors: ["Energy"],
    },
    data: {
      shock: {
        title: "Qatar LNG Disruption",
        subtitle: "North Field export halt — 77M tonnes/year LNG capacity at risk",
        severity: 68,
        impact: 74,
      },
      transmission: [
        { label: "LNG Export Stop", delay: "0h" },
        { label: "Gas Price Spike", delay: "+2h" },
        { label: "Contract Breach", delay: "+6h" },
        { label: "Revenue Loss", delay: "+12h" },
        { label: "Regional Contagion", delay: "+24h" },
      ],
      exposure: [
        { country: "Qatar", percent: 55, flag: "🇶🇦" },
        { country: "UAE", percent: 18, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 12, flag: "🇸🇦" },
        { country: "Oman", percent: 10, flag: "🇴🇲" },
        { country: "Kuwait", percent: 5, flag: "🇰🇼" },
      ],
      decisions: [
        { action: "Invoke Force Majeure + Spot Hedging", value: 70, tag: "recommended" },
        { action: "Redirect Pipeline Gas to Domestic", value: 30, tag: "alternative" },
        { action: "Honor Contracts at Loss", value: -62, tag: "risk" },
      ],
      outcome: { net: 74, confidence: 88, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 7. Bahrain Sovereign Stress ────────────────────────────────────────
  {
    meta: {
      id: "bahrain_sovereign_stress",
      name: "Bahrain Sovereign Stress",
      domain: "FINANCIAL",
      baseLossLabel: "$600M",
      peakDay: "Day 7",
      sectors: ["Banking", "Insurance"],
    },
    data: {
      shock: {
        title: "Bahrain Sovereign Stress",
        subtitle: "Fiscal deficit deepens — sovereign credit downgrade triggers capital flight",
        severity: 55,
        impact: 62,
      },
      transmission: [
        { label: "Rating Cut", delay: "0h" },
        { label: "Bond Sell-Off", delay: "+4h" },
        { label: "Capital Outflow", delay: "+12h" },
        { label: "Banking Pressure", delay: "+24h" },
        { label: "Insurance Drain", delay: "+48h" },
      ],
      exposure: [
        { country: "Bahrain", percent: 60, flag: "🇧🇭" },
        { country: "Saudi Arabia", percent: 18, flag: "🇸🇦" },
        { country: "UAE", percent: 12, flag: "🇦🇪" },
        { country: "Kuwait", percent: 6, flag: "🇰🇼" },
        { country: "Qatar", percent: 4, flag: "🇶🇦" },
      ],
      decisions: [
        { action: "GCC Stability Fund Injection", value: 55, tag: "recommended" },
        { action: "Fiscal Austerity Package", value: 25, tag: "alternative" },
        { action: "Delay Restructuring", value: -45, tag: "risk" },
      ],
      outcome: { net: 68, confidence: 84, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 8. Kuwait Fiscal Shock ─────────────────────────────────────────────
  {
    meta: {
      id: "kuwait_fiscal_shock",
      name: "Kuwait Fiscal Shock",
      domain: "ENERGY",
      baseLossLabel: "$750M",
      peakDay: "Day 6",
      sectors: ["Energy", "Banking"],
    },
    data: {
      shock: {
        title: "Kuwait Fiscal Shock",
        subtitle: "Oil revenue collapse strains sovereign budget — reserve drawdown accelerates",
        severity: 58,
        impact: 65,
      },
      transmission: [
        { label: "Revenue Drop", delay: "0h" },
        { label: "Budget Shortfall", delay: "+6h" },
        { label: "Project Delays", delay: "+18h" },
        { label: "Banking Caution", delay: "+30h" },
        { label: "Credit Squeeze", delay: "+48h" },
      ],
      exposure: [
        { country: "Kuwait", percent: 55, flag: "🇰🇼" },
        { country: "Saudi Arabia", percent: 18, flag: "🇸🇦" },
        { country: "UAE", percent: 14, flag: "🇦🇪" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
        { country: "Qatar", percent: 5, flag: "🇶🇦" },
      ],
      decisions: [
        { action: "Accelerate Future Generations Fund Drawdown", value: 60, tag: "recommended" },
        { action: "Emergency Debt Issuance", value: 30, tag: "alternative" },
        { action: "Cut Subsidies Abruptly", value: -55, tag: "risk" },
      ],
      outcome: { net: 71, confidence: 85, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 9. Oman Port Closure ───────────────────────────────────────────────
  {
    meta: {
      id: "oman_port_closure",
      name: "Oman Port Closure",
      domain: "TRADE",
      baseLossLabel: "$420M",
      peakDay: "Day 2",
      sectors: ["Logistics", "Maritime"],
    },
    data: {
      shock: {
        title: "Oman Port Closure",
        subtitle: "Salalah + Sohar ports shut down — Indian Ocean trade corridor severed",
        severity: 48,
        impact: 56,
      },
      transmission: [
        { label: "Port Shutdown", delay: "0h" },
        { label: "Container Backlog", delay: "+3h" },
        { label: "Route Diversion", delay: "+8h" },
        { label: "Trade Delays", delay: "+18h" },
        { label: "Cost Pass-Through", delay: "+36h" },
      ],
      exposure: [
        { country: "Oman", percent: 52, flag: "🇴🇲" },
        { country: "UAE", percent: 22, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 12, flag: "🇸🇦" },
        { country: "Qatar", percent: 8, flag: "🇶🇦" },
        { country: "Kuwait", percent: 6, flag: "🇰🇼" },
      ],
      decisions: [
        { action: "Reroute to Jebel Ali + Dammam", value: 40, tag: "recommended" },
        { action: "Activate Emergency Overland Corridors", value: 18, tag: "alternative" },
        { action: "Accept Delivery Delays", value: -32, tag: "risk" },
      ],
      outcome: { net: 65, confidence: 90, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 10. Red Sea Trade Corridor Instability ─────────────────────────────
  {
    meta: {
      id: "red_sea_trade_corridor_instability",
      name: "Red Sea Corridor Instability",
      domain: "TRADE",
      baseLossLabel: "$1.9B",
      peakDay: "Day 3",
      sectors: ["Maritime", "Insurance", "Energy"],
    },
    data: {
      shock: {
        title: "Red Sea Instability",
        subtitle: "Bab el-Mandeb attacks escalate — Suez-bound shipping reroutes via Cape",
        severity: 72,
        impact: 80,
      },
      transmission: [
        { label: "Shipping Reroute", delay: "0h" },
        { label: "Insurance Surge", delay: "+2h" },
        { label: "Freight Cost ↑", delay: "+6h" },
        { label: "Supply Chain Lag", delay: "+18h" },
        { label: "Import Inflation", delay: "+48h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 36, flag: "🇸🇦" },
        { country: "UAE", percent: 28, flag: "🇦🇪" },
        { country: "Oman", percent: 16, flag: "🇴🇲" },
        { country: "Qatar", percent: 12, flag: "🇶🇦" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
      ],
      decisions: [
        { action: "Joint Naval Escort + Insurance Pool", value: 90, tag: "recommended" },
        { action: "Shift to Overland Rail Freight", value: 40, tag: "alternative" },
        { action: "Accept Higher Shipping Costs", value: -75, tag: "risk" },
      ],
      outcome: { net: 77, confidence: 81, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 11. Energy Market Volatility Shock ─────────────────────────────────
  {
    meta: {
      id: "energy_market_volatility_shock",
      name: "Energy Market Volatility",
      domain: "ENERGY",
      baseLossLabel: "$2.1B",
      peakDay: "Day 4",
      sectors: ["Energy", "Banking", "Insurance"],
    },
    data: {
      shock: {
        title: "Energy Volatility Shock",
        subtitle: "Brent crude swings ±30% in 48h — GCC hedging positions underwater",
        severity: 70,
        impact: 76,
      },
      transmission: [
        { label: "Price Whipsaw", delay: "0h" },
        { label: "Hedge Losses", delay: "+2h" },
        { label: "Margin Calls", delay: "+6h" },
        { label: "Fiscal Revision", delay: "+18h" },
        { label: "Credit Review", delay: "+36h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 38, flag: "🇸🇦" },
        { country: "UAE", percent: 24, flag: "🇦🇪" },
        { country: "Kuwait", percent: 16, flag: "🇰🇼" },
        { country: "Qatar", percent: 14, flag: "🇶🇦" },
        { country: "Oman", percent: 8, flag: "🇴🇲" },
      ],
      decisions: [
        { action: "OPEC+ Emergency Cut Coordination", value: 110, tag: "recommended" },
        { action: "Sovereign Hedging Program Activation", value: 55, tag: "alternative" },
        { action: "Ride Out Volatility", value: -88, tag: "risk" },
      ],
      outcome: { net: 80, confidence: 85, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 12. Regional Liquidity Stress Event ────────────────────────────────
  {
    meta: {
      id: "regional_liquidity_stress_event",
      name: "Regional Liquidity Stress",
      domain: "FINANCIAL",
      baseLossLabel: "$1.5B",
      peakDay: "Day 3",
      sectors: ["Banking", "Fintech"],
    },
    data: {
      shock: {
        title: "Liquidity Stress Event",
        subtitle: "Cross-border USD shortage cascades through GCC interbank market",
        severity: 66,
        impact: 73,
      },
      transmission: [
        { label: "USD Shortage", delay: "0h" },
        { label: "Repo Rate Spike", delay: "+2h" },
        { label: "Interbank Freeze", delay: "+6h" },
        { label: "FX Peg Pressure", delay: "+12h" },
        { label: "Payment Delays", delay: "+24h" },
      ],
      exposure: [
        { country: "UAE", percent: 34, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 28, flag: "🇸🇦" },
        { country: "Bahrain", percent: 16, flag: "🇧🇭" },
        { country: "Qatar", percent: 12, flag: "🇶🇦" },
        { country: "Kuwait", percent: 10, flag: "🇰🇼" },
      ],
      decisions: [
        { action: "Central Bank USD Swap Lines", value: 80, tag: "recommended" },
        { action: "Temporary Capital Controls", value: 35, tag: "alternative" },
        { action: "Let Market Clear Naturally", value: -70, tag: "risk" },
      ],
      outcome: { net: 73, confidence: 87, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 13. Critical Port Throughput Disruption ────────────────────────────
  {
    meta: {
      id: "critical_port_throughput_disruption",
      name: "Multi-Port Throughput Failure",
      domain: "MARITIME",
      baseLossLabel: "$1.7B",
      peakDay: "Day 2",
      sectors: ["Maritime", "Logistics", "Insurance"],
    },
    data: {
      shock: {
        title: "Port Throughput Failure",
        subtitle: "Jebel Ali + Dammam + Kuwait Port simultaneous capacity collapse",
        severity: 73,
        impact: 82,
      },
      transmission: [
        { label: "Throughput ↓ 60%", delay: "0h" },
        { label: "Vessel Queue", delay: "+3h" },
        { label: "Demurrage Surge", delay: "+8h" },
        { label: "Supply Shortage", delay: "+18h" },
        { label: "Insurance Claims", delay: "+30h" },
      ],
      exposure: [
        { country: "UAE", percent: 40, flag: "🇦🇪" },
        { country: "Saudi Arabia", percent: 28, flag: "🇸🇦" },
        { country: "Kuwait", percent: 16, flag: "🇰🇼" },
        { country: "Oman", percent: 10, flag: "🇴🇲" },
        { country: "Qatar", percent: 6, flag: "🇶🇦" },
      ],
      decisions: [
        { action: "Emergency Port Triage + Priority Lanes", value: 85, tag: "recommended" },
        { action: "Activate Secondary Port Network", value: 45, tag: "alternative" },
        { action: "Wait for Capacity Restoration", value: -78, tag: "risk" },
      ],
      outcome: { net: 75, confidence: 82, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 14. Financial Infrastructure Cyber Disruption ──────────────────────
  {
    meta: {
      id: "financial_infrastructure_cyber_disruption",
      name: "Financial Cyber Disruption",
      domain: "CYBER",
      baseLossLabel: "$1.3B",
      peakDay: "Day 1",
      sectors: ["Banking", "Fintech", "Insurance"],
    },
    data: {
      shock: {
        title: "Financial Cyber Disruption",
        subtitle: "SAMA + CBUAE payment rails compromised — cross-border settlements frozen",
        severity: 76,
        impact: 84,
      },
      transmission: [
        { label: "Settlement Halt", delay: "0h" },
        { label: "ATM Network Down", delay: "+1h" },
        { label: "E-Commerce Stop", delay: "+3h" },
        { label: "Cross-Border Freeze", delay: "+6h" },
        { label: "Consumer Panic", delay: "+12h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 36, flag: "🇸🇦" },
        { country: "UAE", percent: 34, flag: "🇦🇪" },
        { country: "Qatar", percent: 12, flag: "🇶🇦" },
        { country: "Kuwait", percent: 10, flag: "🇰🇼" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
      ],
      decisions: [
        { action: "Activate National Cyber Command + Isolate", value: 90, tag: "recommended" },
        { action: "Manual Paper-Based Settlement", value: 30, tag: "alternative" },
        { action: "Attempt Online Patch Under Attack", value: -72, tag: "risk" },
      ],
      outcome: { net: 70, confidence: 79, label: "Projected Loss Mitigation" },
      trust,
    },
  },

  // ── 15. Iran Regional Escalation ───────────────────────────────────────
  {
    meta: {
      id: "iran_regional_escalation",
      name: "Iran Regional Escalation",
      domain: "GEOPOLITICAL",
      baseLossLabel: "$5.2B",
      peakDay: "Day 2",
      sectors: ["Energy", "Maritime", "Banking", "Insurance"],
    },
    data: {
      shock: {
        title: "Iran Regional Escalation",
        subtitle: "Military escalation triggers multi-vector GCC exposure — war risk pricing active",
        severity: 91,
        impact: 96,
      },
      transmission: [
        { label: "Military Alert", delay: "0h" },
        { label: "Oil Embargo Risk", delay: "+1h" },
        { label: "Hormuz Threat", delay: "+3h" },
        { label: "Capital Flight", delay: "+8h" },
        { label: "Insurance Freeze", delay: "+16h" },
      ],
      exposure: [
        { country: "Saudi Arabia", percent: 34, flag: "🇸🇦" },
        { country: "UAE", percent: 28, flag: "🇦🇪" },
        { country: "Kuwait", percent: 16, flag: "🇰🇼" },
        { country: "Qatar", percent: 14, flag: "🇶🇦" },
        { country: "Bahrain", percent: 8, flag: "🇧🇭" },
      ],
      decisions: [
        { action: "GCC Unified Defense + Diplomatic Channel", value: 160, tag: "recommended" },
        { action: "Sovereign Wealth Stabilization Deploy", value: 75, tag: "alternative" },
        { action: "Unilateral Response", value: -140, tag: "risk" },
      ],
      outcome: { net: 68, confidence: 74, label: "Projected Loss Mitigation" },
      trust,
    },
  },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Get a scenario by its backend-aligned ID. Falls back to Hormuz. */
export function getScenarioById(id: string): DemoScenario {
  return scenarioCatalog.find((s) => s.meta.id === id) ?? scenarioCatalog[0];
}

/** Default scenario data — backward-compatible with existing single-scenario imports. */
export const demoData: DemoData = scenarioCatalog[0].data;
