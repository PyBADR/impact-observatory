/**
 * Impact Observatory | Demo Scenario Data — V4.0 (Macro Financial Intelligence)
 *
 * Two scenarios:
 *   A. Energy & Trade Disruption (Hormuz)
 *   B. Financial Flow Disruption (Settlement / Payment friction)
 *
 * Top-down: signal → transmission → exposure → banking → insurance → sector → decision → outcome → trust
 *
 * LANGUAGE RULES:
 *   - No technical/IT terms (cyber, infrastructure, API, network, platform, backend, frontend)
 *   - Financial, economic, executive language only
 */

export const DEMO_MODE = true;

/* ═══════ ROLE AWARENESS ═══════ */

export type DemoRole = "ceo" | "risk" | "regulator" | "energy";

export interface RoleDef {
  id: DemoRole;
  label: string;
  focus: string;
}

export const DEMO_ROLES: RoleDef[] = [
  { id: "ceo", label: "CEO", focus: "Strategic exposure & decision ROI" },
  { id: "risk", label: "Risk", focus: "Probability distributions & tail risk" },
  { id: "regulator", label: "Regulator", focus: "Systemic stability & compliance" },
  { id: "energy", label: "Energy", focus: "Supply chain & price volatility" },
];

/* ═══════ SHARED INTERFACES ═══════ */

export interface MacroSignal {
  indicator: string;
  value: string;
  change: string;
  direction: "up" | "down";
}

export interface BankingMetric {
  label: string;
  value: string;
  severity: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW";
  detail: string;
}

export interface InsuranceMetric {
  label: string;
  value: string;
  severity: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW";
  detail: string;
}

export interface TransmissionPoint {
  id: string;
  label: string;
  description: string;
  delay: number;
}

export interface TransmissionLink {
  from: string;
  to: string;
  label: string;
}

export interface GCCCountryImpact {
  country: string;
  flag: string;
  sectorStress: number;
  estimatedLoss: string;
  impactLevel: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL";
  topSector: string;
  driver: string;
  channel: string;
}

export interface SectorImpact {
  name: string;
  icon: string;
  signal: string;
  impact: string;
  riskLevel: "CRITICAL" | "ELEVATED" | "MODERATE" | "LOW" | "NOMINAL";
  explanation: string;
  currentStress: number;
  topDriver: string;
  secondOrderRisk: string;
  confidenceBand: string;
  recommendedLever: string;
}

export interface DecisionAction {
  title: string;
  owner: string;
  urgency: "IMMEDIATE" | "24H" | "72H";
  expectedEffect: string;
  consequence: string;
}

export interface StructuredAssumption {
  assumption: string;
  source: string;
  sensitivity: "HIGH" | "MEDIUM" | "LOW";
}

/* ═══════ SCENARIO TYPE ═══════ */

export type ScenarioId = "hormuz" | "financial_flow";

export interface Scenario {
  id: ScenarioId;
  name: string;
  nameAr: string;
  severity: number;
  severityLabel: string;
  lossWithoutAction: number;
  lossWithAction: number;
  lossSaved: number;
  confidence: number;
  exposurePoints: number;
  timeHorizon: string;

  macroRegime: {
    regimeLabel: string;
    severityTier: string;
    systemState: string;
    scenarioType: string;
    signals: MacroSignal[];
    regimeMetrics: {
      exposurePoints: number;
      totalPoints: number;
      scenariosActive: number;
      timeHorizon: string;
      confidence: number;
      estimatedExposure: string;
    };
  };

  shock: {
    headline: string;
    transmissionHeadline: string;
    details: { label: string; value: string; description: string }[];
  };

  transmission: {
    points: TransmissionPoint[];
    links: TransmissionLink[];
    cascadeLabels: string[];
  };

  countries: GCCCountryImpact[];
  /** Which country flags to show in exposure view */
  exposureFilter: string[];

  bankingLayer: {
    stressIndex: number;
    sectorIndex: number;
    headline: string;
    metrics: BankingMetric[];
    transmissionPath: string[];
  };

  insuranceLayer: {
    stressIndex: number;
    sectorIndex: number;
    headline: string;
    metrics: InsuranceMetric[];
    riskAbsorption: string[];
  };

  sectors: SectorImpact[];
  /** Which sector indices to show in sector stress view */
  primarySectors: number[];
  secondarySectors: number[];

  decisionPressure: {
    clockLabel: string;
    clockValue: string;
    hoursRemaining: number;
    escalationBanner: string;
    consequenceStatement: string;
  };

  decisions: DecisionAction[];

  financialRanges: {
    withoutAction: { base: string; low: string; high: string; sensitivity: string };
    withAction: { base: string; low: string; high: string; sensitivity: string };
    saved: { base: string; low: string; high: string; sensitivity: string };
  };

  outcome: {
    withoutAction: {
      totalLoss: string;
      lossRaw: number;
      recoveryTimeline: string;
      riskEscalation: string;
      description: string;
      why: string;
    };
    withAction: {
      totalLoss: string;
      lossRaw: number;
      recoveryTimeline: string;
      riskReduction: string;
      description: string;
      why: string;
    };
    saved: {
      amount: string;
      amountRaw: number;
      explanation: string;
    };
  };

  structuredAssumptions: StructuredAssumption[];

  trust: {
    confidence: number;
    dataFreshness: string;
    validationMethod: string;
    dataSources: string[];
    assumptions: string[];
    assessmentVersion: string;
    lastCalibration: string;
    footerPipeline: string;
  };
}

/* ═══════════════════════════════════════════════════════════════════
 * SCENARIO A — ENERGY & TRADE DISRUPTION (HORMUZ)
 * ═══════════════════════════════════════════════════════════════════ */

const hormuzScenario: Scenario = {
  id: "hormuz",
  name: "Energy & Trade Disruption",
  nameAr: "اضطراب الطاقة والتجارة",
  severity: 0.72,
  severityLabel: "Elevated",
  lossWithoutAction: 4.9e9,
  lossWithAction: 4.3e9,
  lossSaved: 0.6e9,
  confidence: 0.84,
  exposurePoints: 31,
  timeHorizon: "168 hours",

  macroRegime: {
    regimeLabel: "ENERGY-DRIVEN STRESS",
    severityTier: "ELEVATED",
    systemState: "GCC financial conditions tightening under energy supply disruption",
    scenarioType: "Energy & trade disruption — Strait of Hormuz",
    signals: [
      { indicator: "Brent Crude", value: "$127.40/bbl", change: "+38%", direction: "up" },
      { indicator: "GCC Interbank Rate", value: "4.82%", change: "+190bps", direction: "up" },
      { indicator: "Baltic Dry Index", value: "892", change: "-44%", direction: "down" },
      { indicator: "Marine War-Risk Premium", value: "2.8%", change: "+680bps", direction: "up" },
      { indicator: "GCC CDS Spread", value: "142bps", change: "+58bps", direction: "up" },
      { indicator: "FX Reserves Drawdown", value: "$12.4B", change: "est. 14-day", direction: "down" },
    ],
    regimeMetrics: {
      exposurePoints: 31,
      totalPoints: 43,
      scenariosActive: 1,
      timeHorizon: "168h",
      confidence: 0.84,
      estimatedExposure: "$4.9B",
    },
  },

  shock: {
    headline: "Maritime disruption reduces oil transit by 60%",
    transmissionHeadline: "Stress transmitting from energy pricing into banking liquidity and insurance exposure",
    details: [
      { label: "Transit Reduction", value: "60%", description: "Volume reduction through the strait" },
      { label: "Reroute Delay", value: "12–18 days", description: "Average delay via Cape of Good Hope" },
      { label: "Critical Window", value: "72 hours", description: "First-order economic effects horizon" },
    ],
  },

  transmission: {
    points: [
      { id: "oil", label: "Energy & Commodities", description: "Crude transit disrupted", delay: 0 },
      { id: "shipping", label: "Trade & Logistics", description: "Route costs tripling", delay: 0.8 },
      { id: "banking", label: "Banking & Liquidity", description: "Trade finance tightening", delay: 1.6 },
      { id: "insurance", label: "Insurance & Pricing", description: "Claims accelerating", delay: 2.4 },
      { id: "government", label: "Fiscal & Policy", description: "Stabilization required", delay: 3.2 },
    ],
    links: [
      { from: "oil", to: "shipping", label: "Price surge" },
      { from: "shipping", to: "banking", label: "Trade finance pressure" },
      { from: "banking", to: "insurance", label: "Liquidity tightening" },
      { from: "insurance", to: "government", label: "Claims acceleration" },
    ],
    cascadeLabels: [
      "Crude prices surge 40% within hours",
      "Shipping routes rerouted — costs tripling",
      "Trade finance tightening across GCC banks",
      "Marine and energy claims accelerating 280%",
      "Fiscal reserves under pressure — stabilization required",
    ],
  },

  countries: [
    { country: "Saudi Arabia", flag: "SA", sectorStress: 0.68, estimatedLoss: "$1.8B", impactLevel: "ELEVATED", topSector: "Oil & Gas", driver: "Largest crude exporter via Hormuz — direct export volume loss", channel: "Energy export → fiscal revenue" },
    { country: "UAE", flag: "AE", sectorStress: 0.61, estimatedLoss: "$1.1B", impactLevel: "ELEVATED", topSector: "Banking", driver: "Trade finance hub — letter of credit exposure to in-transit cargo", channel: "Trade finance → interbank liquidity" },
    { country: "Kuwait", flag: "KW", sectorStress: 0.55, estimatedLoss: "$480M", impactLevel: "MODERATE", topSector: "Oil & Gas", driver: "Oil revenue dependence (90%+ fiscal) amplifies price volatility", channel: "Oil revenue → fiscal balance" },
    { country: "Qatar", flag: "QA", sectorStress: 0.49, estimatedLoss: "$420M", impactLevel: "MODERATE", topSector: "LNG Export", driver: "LNG tanker rerouting adds 12-day delay per cargo", channel: "LNG transit → export revenue" },
    { country: "Bahrain", flag: "BH", sectorStress: 0.42, estimatedLoss: "$210M", impactLevel: "MODERATE", topSector: "Insurance", driver: "Regional reinsurance center — war-risk premium cascade", channel: "Reinsurance → coverage capacity" },
    { country: "Oman", flag: "OM", sectorStress: 0.58, estimatedLoss: "$310M", impactLevel: "MODERATE", topSector: "Port & Shipping", driver: "Salalah/Sohar ports on disrupted route corridor", channel: "Port throughput → trade flow" },
  ],
  exposureFilter: ["SA", "AE", "KW", "QA", "BH", "OM"],

  bankingLayer: {
    stressIndex: 0.67,
    sectorIndex: 1,
    headline: "Liquidity tightening across interbank channels",
    metrics: [
      { label: "Interbank Liquidity", value: "Tightening", severity: "ELEVATED", detail: "Overnight rate +190bps above corridor ceiling" },
      { label: "Trade Finance Exposure", value: "$2.1B frozen", severity: "CRITICAL", detail: "340+ letters of credit on in-transit cargo suspended" },
      { label: "Credit Facility Drawdown", value: "87%", severity: "ELEVATED", detail: "Energy sector drawdowns accelerating beyond normal corridor" },
      { label: "LCR Impact", value: "-14 pts", severity: "MODERATE", detail: "Liquidity Coverage Ratio declining toward regulatory floor" },
    ],
    transmissionPath: [
      "Trade finance freeze on maritime cargo",
      "Interbank rate pressure → overnight lending stress",
      "Energy sector credit facility drawdowns",
      "SME receivables chain disruption",
    ],
  },

  insuranceLayer: {
    stressIndex: 0.71,
    sectorIndex: 2,
    headline: "Insurance exposure rising as disruption translates into claims and pricing pressure",
    metrics: [
      { label: "Marine Hull Claims", value: "+280%", severity: "CRITICAL", detail: "War-risk triggers activated across GCC maritime fleet" },
      { label: "Cargo Claims Backlog", value: "$890M", severity: "ELEVATED", detail: "In-transit cargo claims from rerouting and delays" },
      { label: "Reinsurance Utilization", value: "78%", severity: "ELEVATED", detail: "Treaty capacity approaching exhaustion threshold" },
      { label: "Coverage Gap", value: "12% uninsured", severity: "MODERATE", detail: "Force majeure exclusions creating protection gaps" },
    ],
    riskAbsorption: [
      "War-risk premium activation across GCC maritime policies",
      "Reinsurers invoking force majeure — coverage gaps widening",
      "Business interruption claims backlog forming",
      "Retrocession market tightening globally",
    ],
  },

  sectors: [
    {
      name: "Oil & Gas",
      icon: "fuel",
      signal: "Crude transit volume at 40% of baseline",
      impact: "Spot price surge, forward contracts repricing",
      riskLevel: "CRITICAL",
      explanation: "60% transit disruption triggers repricing across all GCC crude benchmarks.",
      currentStress: 0.82,
      topDriver: "Transit volume reduction",
      secondOrderRisk: "Petrochemical supply chain halt",
      confidenceBand: "80–88%",
      recommendedLever: "Activate strategic petroleum reserves",
    },
    {
      name: "Banking & Finance",
      icon: "landmark",
      signal: "Interbank liquidity tightening",
      impact: "Credit lines frozen on trade finance",
      riskLevel: "ELEVATED",
      explanation: "Trade finance exposure creates cascading liquidity pressure.",
      currentStress: 0.67,
      topDriver: "Trade finance exposure",
      secondOrderRisk: "SME credit crunch from frozen receivables",
      confidenceBand: "76–85%",
      recommendedLever: "Central bank emergency liquidity window",
    },
    {
      name: "Insurance",
      icon: "shield",
      signal: "Marine hull and cargo claims surging",
      impact: "Reinsurance capacity under pressure",
      riskLevel: "ELEVATED",
      explanation: "War-risk premiums activate across GCC maritime policies.",
      currentStress: 0.71,
      topDriver: "War-risk premium activation",
      secondOrderRisk: "Coverage gaps delay cargo release",
      confidenceBand: "74–83%",
      recommendedLever: "Government-backed reinsurance backstop",
    },
    {
      name: "Financial Flows",
      icon: "smartphone",
      signal: "Cross-border settlement latency increasing",
      impact: "Settlement delays on trade corridors",
      riskLevel: "MODERATE",
      explanation: "Transaction settlement slowing as underlying trade enters dispute.",
      currentStress: 0.44,
      topDriver: "Settlement dispute backlog",
      secondOrderRisk: "Remittance corridor disruption",
      confidenceBand: "68–78%",
      recommendedLever: "Settlement prioritization via regulator directive",
    },
    {
      name: "Real Estate",
      icon: "building",
      signal: "Project financing activity slowing",
      impact: "Repricing pressure on project tranches",
      riskLevel: "LOW",
      explanation: "Tightening liquidity reduces project finance availability, triggering repricing.",
      currentStress: 0.28,
      topDriver: "Project financing slowdown",
      secondOrderRisk: "Construction cost inflation from import delays",
      confidenceBand: "60–72%",
      recommendedLever: "Developer incentive extension & permitting fast-track",
    },
    {
      name: "Government & Fiscal",
      icon: "university",
      signal: "Fiscal stabilization under review",
      impact: "Policy response capacity being assessed",
      riskLevel: "ELEVATED",
      explanation: "Revenue shortfall compresses fiscal headroom, requiring stabilization fund drawdowns.",
      currentStress: 0.63,
      topDriver: "Fiscal revenue compression",
      secondOrderRisk: "Sovereign credit rating watch",
      confidenceBand: "75–84%",
      recommendedLever: "SWF stabilization fund drawdown",
    },
  ],
  primarySectors: [0, 1, 2],
  secondarySectors: [3, 5],

  decisionPressure: {
    clockLabel: "Decision Window",
    clockValue: "71h 42m remaining",
    hoursRemaining: 71.7,
    escalationBanner: "Delayed response increases estimated loss from $4.9B to $6.1B within 24 hours",
    consequenceStatement: "Inaction cost compounds at $85M per hour after the critical window closes.",
  },

  decisions: [
    {
      title: "Release strategic petroleum reserves",
      owner: "Ministry of Energy",
      urgency: "IMMEDIATE",
      expectedEffect: "Stabilize crude supply for 14 days, prevent price escalation above $130/bbl",
      consequence: "Without release, crude price escalates past $145/bbl within 48h — $2.1B additional exposure",
    },
    {
      title: "Inject emergency liquidity into interbank market",
      owner: "Central Bank",
      urgency: "IMMEDIATE",
      expectedEffect: "Unfreeze trade finance lines, restore letter of credit processing",
      consequence: "24h delay triggers SME liquidity crisis — 340+ trade finance facilities frozen",
    },
    {
      title: "Reroute trade flows via alternative corridors",
      owner: "Port Authority",
      urgency: "24H",
      expectedEffect: "Reduce delivery delays from 18 days to 8 days",
      consequence: "Each day of delay adds $120M in cargo costs and perishable goods loss",
    },
    {
      title: "Adjust credit exposure limits on energy sector",
      owner: "Banking Regulator (SAMA / CBUAE)",
      urgency: "24H",
      expectedEffect: "Prevent cascading defaults in energy-linked loan portfolios",
      consequence: "Uncontrolled exposure risks $380M in non-performing loan reclassification",
    },
    {
      title: "Activate government-backed reinsurance backstop",
      owner: "Insurance Regulator",
      urgency: "72H",
      expectedEffect: "Stabilize coverage capacity and prevent further premium escalation",
      consequence: "Coverage gaps widen — cargo release delays compound across GCC ports",
    },
  ],

  financialRanges: {
    withoutAction: { base: "$4.9B", low: "$3.8B", high: "$6.1B", sensitivity: "Oil price ±15% shifts range by ~$800M" },
    withAction:    { base: "$4.3B", low: "$3.5B", high: "$5.0B", sensitivity: "Intervention speed ±12h shifts range by ~$400M" },
    saved:         { base: "$600M", low: "$300M", high: "$1.2B", sensitivity: "Coordinated vs. unilateral response determines range" },
  },

  outcome: {
    withoutAction: {
      totalLoss: "$4.9B",
      lossRaw: 4.9e9,
      recoveryTimeline: "21–30 days",
      riskEscalation: "+45%",
      description: "Without intervention, supply disruption compounds through banking and insurance channels.",
      why: "Stress transmission across multiple sectors amplifies the initial energy shock into a region-wide financial event.",
    },
    withAction: {
      totalLoss: "$4.3B",
      lossRaw: 4.3e9,
      recoveryTimeline: "5–7 days",
      riskReduction: "62%",
      description: "Coordinated response across energy, banking, and fiscal authorities contains the disruption within 72 hours.",
      why: "Early intervention breaks the stress linkage between banking and insurance, preventing secondary escalation.",
    },
    saved: {
      amount: "$600M",
      amountRaw: 0.6e9,
      explanation: "Net savings from coordinated liquidity injection, strategic reserve release, and trade corridor rerouting within the decision window.",
    },
  },

  structuredAssumptions: [
    { assumption: "60% transit volume reduction sustained for 168 hours", source: "Maritime Traffic Data", sensitivity: "HIGH" },
    { assumption: "No military escalation beyond maritime disruption", source: "Geopolitical Analysis", sensitivity: "HIGH" },
    { assumption: "Central bank reserves sufficient for 14-day intervention", source: "Central Bank Reports", sensitivity: "MEDIUM" },
    { assumption: "Reinsurance contracts honor force majeure within 48h", source: "Lloyd's Market Data", sensitivity: "MEDIUM" },
    { assumption: "Oil spot price returns to baseline within 21 days", source: "Energy Futures Market Data", sensitivity: "LOW" },
  ],

  trust: {
    confidence: 0.84,
    dataFreshness: "<10 minutes",
    validationMethod: "Cross-referenced across multiple independent signals",
    dataSources: [
      "Maritime Traffic Data (scenario-based)",
      "Central Bank Interbank Rates (scenario-based)",
      "Geopolitical Event Data (reference)",
      "GCC Exchange Market Data (estimated)",
      "Insurance Claims Data (projected)",
    ],
    assumptions: [
      "60% transit volume reduction sustained for 168 hours",
      "No military escalation beyond maritime disruption",
      "Central bank reserves sufficient for 14-day intervention",
      "Reinsurance contracts honor force majeure within 48 hours",
    ],
    assessmentVersion: "Impact Observatory v4.0",
    lastCalibration: "2026-04-10",
    footerPipeline: "Signal → Transmission → Exposure → Sector → Decision → Outcome → Audit",
  },
};

/* ═══════════════════════════════════════════════════════════════════
 * SCENARIO B — FINANCIAL FLOW DISRUPTION
 * ═══════════════════════════════════════════════════════════════════ */

const financialFlowScenario: Scenario = {
  id: "financial_flow",
  name: "Financial Flow Disruption",
  nameAr: "اضطراب التدفقات المالية",
  severity: 0.58,
  severityLabel: "Elevated",
  lossWithoutAction: 2.8e9,
  lossWithAction: 2.1e9,
  lossSaved: 0.7e9,
  confidence: 0.79,
  exposurePoints: 24,
  timeHorizon: "96 hours",

  macroRegime: {
    regimeLabel: "LIQUIDITY STRESS",
    severityTier: "ELEVATED",
    systemState: "Liquidity conditions tightening across regional banking and settlement channels",
    scenarioType: "Financial flow disruption — cross-border settlement friction",
    signals: [
      { indicator: "GCC Interbank Rate", value: "5.14%", change: "+240bps", direction: "up" },
      { indicator: "Cross-Border Settlement", value: "18.4h avg", change: "+340%", direction: "up" },
      { indicator: "Correspondent Banking", value: "42% delayed", change: "+38pp", direction: "up" },
      { indicator: "FX Forward Premium", value: "2.6%", change: "+180bps", direction: "up" },
      { indicator: "Remittance Volume", value: "-34%", change: "vs. 30d avg", direction: "down" },
      { indicator: "Trade Finance Availability", value: "Constrained", change: "-28%", direction: "down" },
    ],
    regimeMetrics: {
      exposurePoints: 24,
      totalPoints: 43,
      scenariosActive: 1,
      timeHorizon: "96h",
      confidence: 0.79,
      estimatedExposure: "$2.8B",
    },
  },

  shock: {
    headline: "Cross-border settlement delays disrupt regional financial flows",
    transmissionHeadline: "Disruption in financial flows transmitting into banking liquidity and settlement risk",
    details: [
      { label: "Settlement Delay", value: "18.4h", description: "Average cross-border settlement time (normal: 4.2h)" },
      { label: "Affected Corridors", value: "12 of 18", description: "Major GCC bilateral settlement corridors impacted" },
      { label: "Liquidity Gap", value: "$1.4B", description: "Estimated daily funding shortfall across affected banks" },
    ],
  },

  transmission: {
    points: [
      { id: "settlement", label: "Settlement Channels", description: "Clearing delays", delay: 0 },
      { id: "banking", label: "Banking & Liquidity", description: "Funding pressure", delay: 0.8 },
      { id: "trade", label: "Trade Finance", description: "LC processing halted", delay: 1.6 },
      { id: "insurance", label: "Credit Insurance", description: "Exposure repricing", delay: 2.4 },
      { id: "government", label: "Fiscal & Policy", description: "Intervention required", delay: 3.2 },
    ],
    links: [
      { from: "settlement", to: "banking", label: "Funding gaps" },
      { from: "banking", to: "trade", label: "Credit tightening" },
      { from: "trade", to: "insurance", label: "Exposure repricing" },
      { from: "insurance", to: "government", label: "Regulatory response" },
    ],
    cascadeLabels: [
      "Cross-border settlements delayed to 18+ hours",
      "Interbank funding gaps emerging across GCC",
      "Trade finance letters of credit processing halted",
      "Credit insurance repricing on delayed settlements",
      "Regulatory intervention required to restore flow",
    ],
  },

  countries: [
    { country: "UAE", flag: "AE", sectorStress: 0.65, estimatedLoss: "$980M", impactLevel: "ELEVATED", topSector: "Banking", driver: "Primary regional clearing hub — highest exposure to settlement delays", channel: "Settlement clearing → interbank liquidity" },
    { country: "Saudi Arabia", flag: "SA", sectorStress: 0.54, estimatedLoss: "$720M", impactLevel: "MODERATE", topSector: "Banking", driver: "Largest bilateral corridor with UAE — cross-border flow disruption", channel: "Bilateral flow → trade finance" },
    { country: "Bahrain", flag: "BH", sectorStress: 0.52, estimatedLoss: "$380M", impactLevel: "MODERATE", topSector: "Financial Services", driver: "Regional financial services hub — concentrated settlement exposure", channel: "Financial services → correspondent banking" },
    { country: "Qatar", flag: "QA", sectorStress: 0.41, estimatedLoss: "$340M", impactLevel: "MODERATE", topSector: "Banking", driver: "LNG revenue settlement delays affecting fiscal inflows", channel: "Revenue settlement → fiscal balance" },
    { country: "Kuwait", flag: "KW", sectorStress: 0.35, estimatedLoss: "$220M", impactLevel: "LOW", topSector: "Government", driver: "Sovereign fund repatriation flows delayed", channel: "Fund flows → fiscal operations" },
    { country: "Oman", flag: "OM", sectorStress: 0.30, estimatedLoss: "$160M", impactLevel: "LOW", topSector: "Trade", driver: "Port settlement clearing backlogs", channel: "Trade settlement → port operations" },
  ],
  exposureFilter: ["AE", "SA", "BH", "QA"],

  bankingLayer: {
    stressIndex: 0.62,
    sectorIndex: 1,
    headline: "Funding pressure increasing due to settlement delays",
    metrics: [
      { label: "Interbank Liquidity", value: "Stressed", severity: "ELEVATED", detail: "Overnight rate +240bps above corridor ceiling" },
      { label: "Settlement Backlog", value: "$4.2B pending", severity: "CRITICAL", detail: "Cross-border transactions queued beyond normal clearing window" },
      { label: "Correspondent Banking", value: "42% delayed", severity: "ELEVATED", detail: "Major correspondent banks applying enhanced review procedures" },
      { label: "Funding Gap", value: "$1.4B/day", severity: "ELEVATED", detail: "Daily shortfall across affected institutions" },
    ],
    transmissionPath: [
      "Settlement clearing delays cascade to funding gaps",
      "Interbank lending rates spike above policy corridor",
      "Trade finance availability constrained",
      "SME working capital lines restricted",
    ],
  },

  insuranceLayer: {
    stressIndex: 0.48,
    sectorIndex: 2,
    headline: "Credit insurance exposure rising on settlement uncertainty",
    metrics: [
      { label: "Trade Credit Claims", value: "+120%", severity: "ELEVATED", detail: "Settlement-linked trade credit claims accelerating" },
      { label: "Receivables Insurance", value: "Repricing", severity: "ELEVATED", detail: "Policies on cross-border receivables under review" },
      { label: "Surety Utilization", value: "64%", severity: "MODERATE", detail: "Performance bond capacity tightening on delayed contracts" },
      { label: "Coverage Adjustment", value: "-8% capacity", severity: "MODERATE", detail: "Underwriters reducing exposure to affected corridors" },
    ],
    riskAbsorption: [
      "Trade credit claims accelerating on delayed settlements",
      "Receivables insurance repricing across affected corridors",
      "Performance bond capacity tightening",
      "Underwriters reducing cross-border exposure",
    ],
  },

  sectors: [
    {
      name: "Oil & Gas",
      icon: "fuel",
      signal: "Revenue settlement delays affecting cash flow",
      impact: "Working capital pressure on energy companies",
      riskLevel: "MODERATE",
      explanation: "Energy revenue settlements delayed, creating temporary cash flow gaps.",
      currentStress: 0.38,
      topDriver: "Revenue settlement delays",
      secondOrderRisk: "Supplier payment chain disruption",
      confidenceBand: "65–75%",
      recommendedLever: "Treasury facility activation",
    },
    {
      name: "Banking & Finance",
      icon: "landmark",
      signal: "Interbank funding pressure rising",
      impact: "Settlement backlogs creating liquidity gaps",
      riskLevel: "ELEVATED",
      explanation: "Settlement delays transmit directly into interbank funding pressure.",
      currentStress: 0.62,
      topDriver: "Settlement clearing backlog",
      secondOrderRisk: "Correspondent banking relationship stress",
      confidenceBand: "74–82%",
      recommendedLever: "Central bank liquidity backstop",
    },
    {
      name: "Insurance",
      icon: "shield",
      signal: "Credit insurance repricing underway",
      impact: "Trade credit exposure rising",
      riskLevel: "MODERATE",
      explanation: "Settlement delays trigger repricing of trade credit insurance.",
      currentStress: 0.48,
      topDriver: "Trade credit claims surge",
      secondOrderRisk: "Coverage reduction on cross-border exposure",
      confidenceBand: "68–78%",
      recommendedLever: "Regulatory guidance on coverage continuity",
    },
    {
      name: "Financial Flows",
      icon: "smartphone",
      signal: "Cross-border transaction volumes declining",
      impact: "Remittance and trade settlement disruption",
      riskLevel: "CRITICAL",
      explanation: "Core settlement channels experiencing multi-hour delays, disrupting cross-border flows.",
      currentStress: 0.74,
      topDriver: "Settlement channel congestion",
      secondOrderRisk: "Remittance corridor disruption",
      confidenceBand: "72–82%",
      recommendedLever: "Settlement prioritization and rerouting",
    },
    {
      name: "Real Estate",
      icon: "building",
      signal: "Cross-border investment flows pausing",
      impact: "Foreign investment settlement delays",
      riskLevel: "LOW",
      explanation: "International real estate investment flows affected by settlement delays.",
      currentStress: 0.22,
      topDriver: "Investment flow delays",
      secondOrderRisk: "Project financing uncertainty",
      confidenceBand: "55–68%",
      recommendedLever: "Bilateral clearing agreements",
    },
    {
      name: "Government & Fiscal",
      icon: "university",
      signal: "Revenue collection settlement delays",
      impact: "Fiscal cash flow management under pressure",
      riskLevel: "ELEVATED",
      explanation: "Government revenue collection and sovereign fund flows affected by settlement friction.",
      currentStress: 0.51,
      topDriver: "Revenue collection delays",
      secondOrderRisk: "Short-term fiscal funding gap",
      confidenceBand: "70–80%",
      recommendedLever: "Emergency fiscal facility activation",
    },
  ],
  primarySectors: [1, 3, 5],
  secondarySectors: [0, 2],

  decisionPressure: {
    clockLabel: "Decision Window",
    clockValue: "48h 15m remaining",
    hoursRemaining: 48.25,
    escalationBanner: "Delayed response increases estimated loss from $2.8B to $3.6B within 24 hours",
    consequenceStatement: "Each 6-hour delay in response adds approximately $140M in cascading settlement losses.",
  },

  decisions: [
    {
      title: "Activate emergency settlement rerouting",
      owner: "Central Bank",
      urgency: "IMMEDIATE",
      expectedEffect: "Redirect cross-border flows through alternative clearing channels within 4 hours",
      consequence: "Continued delays cascade into $180M/day in additional settlement losses",
    },
    {
      title: "Deploy central bank liquidity backstop",
      owner: "Central Bank / Ministry of Finance",
      urgency: "IMMEDIATE",
      expectedEffect: "Bridge $1.4B daily funding gap, stabilize interbank lending conditions",
      consequence: "Funding gaps trigger correspondent banking withdrawals — credit tightening accelerates",
    },
    {
      title: "Prioritize critical settlement corridors",
      owner: "Financial Market Authority",
      urgency: "24H",
      expectedEffect: "Restore 8 of 12 affected corridors to normal processing within 24 hours",
      consequence: "Unprioritized processing extends disruption to 72+ hours across all corridors",
    },
    {
      title: "Coordinate bilateral regulatory response",
      owner: "GCC Central Banks (Joint)",
      urgency: "24H",
      expectedEffect: "Harmonize settlement protocols across GCC, prevent unilateral restrictions",
      consequence: "Uncoordinated response risks capital flow restrictions between member states",
    },
    {
      title: "Extend trade finance facility terms",
      owner: "Banking Regulator",
      urgency: "72H",
      expectedEffect: "Prevent LC expiration and trade credit defaults on delayed settlements",
      consequence: "Mass LC expiration triggers $420M in trade credit defaults across GCC",
    },
  ],

  financialRanges: {
    withoutAction: { base: "$2.8B", low: "$2.1B", high: "$3.6B", sensitivity: "Settlement duration ±12h shifts range by ~$400M" },
    withAction:    { base: "$2.1B", low: "$1.6B", high: "$2.5B", sensitivity: "Response coordination speed ±6h shifts range by ~$250M" },
    saved:         { base: "$700M", low: "$400M", high: "$1.1B", sensitivity: "Bilateral vs. unilateral response determines range" },
  },

  outcome: {
    withoutAction: {
      totalLoss: "$2.8B",
      lossRaw: 2.8e9,
      recoveryTimeline: "14–21 days",
      riskEscalation: "+28%",
      description: "Without intervention, settlement delays cascade into banking liquidity crisis and trade finance disruption.",
      why: "Unresolved settlement friction compounds through interbank channels, disrupting trade finance and government fiscal flows.",
    },
    withAction: {
      totalLoss: "$2.1B",
      lossRaw: 2.1e9,
      recoveryTimeline: "3–5 days",
      riskReduction: "54%",
      description: "Coordinated central bank and regulatory response restores settlement flow within 48 hours.",
      why: "Emergency rerouting and liquidity backstop contain the disruption before it reaches trade finance and fiscal channels.",
    },
    saved: {
      amount: "$700M",
      amountRaw: 0.7e9,
      explanation: "Net savings from settlement rerouting, liquidity backstop deployment, and coordinated regulatory response within the decision window.",
    },
  },

  structuredAssumptions: [
    { assumption: "Settlement delays sustained at 18+ hours for 96-hour period", source: "Clearing House Data", sensitivity: "HIGH" },
    { assumption: "No unilateral capital controls imposed by member states", source: "Regulatory Guidance", sensitivity: "HIGH" },
    { assumption: "Central bank liquidity facilities available within 4 hours", source: "Central Bank Reports", sensitivity: "MEDIUM" },
    { assumption: "Alternative clearing channels have sufficient capacity", source: "Settlement Data", sensitivity: "MEDIUM" },
    { assumption: "Correspondent banking relationships maintained through disruption", source: "Banking Sector Analysis", sensitivity: "LOW" },
  ],

  trust: {
    confidence: 0.79,
    dataFreshness: "<10 minutes",
    validationMethod: "Cross-referenced across multiple independent signals",
    dataSources: [
      "Clearing House Settlement Data (scenario-based)",
      "Central Bank Interbank Rates (scenario-based)",
      "Correspondent Banking Reports (reference)",
      "GCC Exchange Market Data (estimated)",
      "Trade Finance Registry (projected)",
    ],
    assumptions: [
      "Settlement delays sustained at 18+ hours for 96-hour period",
      "No unilateral capital controls imposed",
      "Central bank liquidity available within 4 hours",
      "Alternative clearing channels have capacity",
    ],
    assessmentVersion: "Impact Observatory v4.0",
    lastCalibration: "2026-04-10",
    footerPipeline: "Signal → Transmission → Exposure → Sector → Decision → Outcome → Audit",
  },
};

/* ═══════════════════════════════════════════════════════════════════
 * SCENARIO REGISTRY
 * ═══════════════════════════════════════════════════════════════════ */

export const SCENARIOS: Record<ScenarioId, Scenario> = {
  hormuz: hormuzScenario,
  financial_flow: financialFlowScenario,
};

export const DEFAULT_SCENARIO_ID: ScenarioId = "hormuz";

/** Helper to get scenario by ID */
export function getScenario(id: ScenarioId): Scenario {
  return SCENARIOS[id];
}

/**
 * Legacy compat — demoScenario is the default (Hormuz) scenario.
 * New components should use getScenario(scenarioId) instead.
 */
export const demoScenario = hormuzScenario;
