export type MacroInput = {
  inflation: number;
  interestRate: number;
  gdpGrowth: number;
};

export type Entity = {
  id: string;
  name: string;
  sector: string;
  coverage: number;
};

export type SignalOutput = {
  inflationRisk: number;
  ratePressure: number;
  growthSignal: number;
};

export type DecisionResult = {
  entity: string;
  decision: "APPROVED" | "REJECTED" | "CONDITIONAL";
  riskScore: number;
  delta: number;
  policies: string[];
  explanation: string;
};

export type EvaluationResponse = {
  scenario: string;
  results: DecisionResult[];
  timestamp: string;
};

export type AuditEntry = {
  timestamp: string;
  scenario: string;
  macro: MacroInput;
  results: DecisionResult[];
};
