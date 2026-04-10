"use client";

import React, { useState, useCallback } from "react";
import { Play, RotateCcw } from "lucide-react";
import type { SimulationParams, SimulationComparison } from "@/types/enterprise";
import type { ScenarioCatalogEntry } from "@/types/observatory";
import { theme } from "@/theme/tokens";

interface ScenarioSimulatorProps {
  scenarios: ScenarioCatalogEntry[];
  onRunSimulation?: (params: SimulationParams) => Promise<unknown>;
  onSimulate?: (params: SimulationParams) => Promise<unknown>;
  language: "en" | "ar";
  isLoading?: boolean;
  previousResult?: { totalLoss: number; peakDay: number; affectedEntities: number; avgStress: number };
}

const getChangeColor = (change: number): string => {
  if (change > 0) return "#B91C1C";
  if (change < 0) return "#15803D";
  return theme.palette.secondary;
};

const getPercentageColor = (pct: number): string => {
  if (pct > 20) return "#B91C1C";
  if (pct > 10) return "#B45309";
  if (pct > 0) return "#CA8A04";
  return "#15803D";
};

export const ScenarioSimulator: React.FC<ScenarioSimulatorProps> = ({
  scenarios,
  onRunSimulation,
  language,
  isLoading = false,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<string>(
    scenarios[0]?.scenario_id || ""
  );
  const [severity, setSeverity] = useState(0.5);
  const [horizonHours, setHorizonHours] = useState(72);
  const [label, setLabel] = useState("");
  const [result, setResult] = useState<SimulationComparison | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunSimulation = useCallback(async () => {
    if (!onRunSimulation || !selectedScenario) return;

    setIsRunning(true);
    try {
      const params: SimulationParams = {
        templateId: selectedScenario,
        severity,
        horizonHours,
        label: label || undefined,
      };
      const comparison = await onRunSimulation(params);
      setResult(comparison as SimulationComparison | null);
    } finally {
      setIsRunning(false);
    }
  }, [selectedScenario, severity, horizonHours, label, onRunSimulation]);

  const handleReset = useCallback(() => {
    setSelectedScenario(scenarios[0]?.scenario_id || "");
    setSeverity(0.5);
    setHorizonHours(72);
    setLabel("");
    setResult(null);
  }, [scenarios]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing.xl,
        backgroundColor: theme.palette.background,
        padding: theme.spacing.xl,
        borderRadius: theme.borderRadius.lg,
        fontFamily:
          language === "ar"
            ? theme.typography.fontFamilyAr
            : theme.typography.fontFamily,
      }}
    >
      {/* Input Section */}
      <div
        style={{
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          padding: theme.spacing.lg,
        }}
      >
        <div
          style={{
            fontSize: "1rem",
            fontWeight: 600,
            color: theme.palette.primary,
            marginBottom: theme.spacing.lg,
          }}
        >
          Simulation Parameters
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: theme.spacing.lg,
          }}
        >
          {/* Scenario Selection */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: theme.palette.secondary,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                marginBottom: theme.spacing.sm,
              }}
            >
              Scenario Template
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={isRunning || isLoading}
              style={{
                width: "100%",
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.palette.border}`,
                backgroundColor: theme.palette.background,
                fontFamily: "inherit",
                fontSize: "0.875rem",
                color: theme.palette.primary,
                cursor: isRunning || isLoading ? "not-allowed" : "pointer",
                opacity: isRunning || isLoading ? 0.6 : 1,
              }}
            >
              {scenarios.map((scenario) => (
                <option key={scenario.scenario_id} value={scenario.scenario_id}>
                  {language === "ar" ? scenario.scenario_name_ar : scenario.scenario_name_en}
                </option>
              ))}
            </select>
          </div>

          {/* Label Input */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: theme.palette.secondary,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                marginBottom: theme.spacing.sm,
              }}
            >
              Simulation Label (Optional)
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={isRunning || isLoading}
              placeholder="e.g., Stress Test A"
              style={{
                width: "100%",
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.palette.border}`,
                backgroundColor: theme.palette.background,
                fontFamily: "inherit",
                fontSize: "0.875rem",
                color: theme.palette.primary,
                cursor: isRunning || isLoading ? "not-allowed" : "text",
                opacity: isRunning || isLoading ? 0.6 : 1,
              }}
            />
          </div>

          {/* Severity Slider */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: theme.palette.secondary,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                marginBottom: theme.spacing.sm,
              }}
            >
              Severity: {(severity * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={severity}
              onChange={(e) => setSeverity(parseFloat(e.target.value))}
              disabled={isRunning || isLoading}
              style={{
                width: "100%",
                cursor: isRunning || isLoading ? "not-allowed" : "pointer",
                opacity: isRunning || isLoading ? 0.6 : 1,
              }}
            />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.75rem",
                color: theme.palette.secondary,
                marginTop: theme.spacing.xs,
              }}
            >
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Horizon Hours */}
          <div>
            <label
              style={{
                display: "block",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: theme.palette.secondary,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                marginBottom: theme.spacing.sm,
              }}
            >
              Forecast Horizon (Hours)
            </label>
            <input
              type="number"
              value={horizonHours}
              onChange={(e) => setHorizonHours(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={isRunning || isLoading}
              min="1"
              max="8760"
              style={{
                width: "100%",
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.palette.border}`,
                backgroundColor: theme.palette.background,
                fontFamily: "inherit",
                fontSize: "0.875rem",
                color: theme.palette.primary,
                cursor: isRunning || isLoading ? "not-allowed" : "text",
                opacity: isRunning || isLoading ? 0.6 : 1,
              }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div
          style={{
            display: "flex",
            gap: theme.spacing.md,
            marginTop: theme.spacing.lg,
          }}
        >
          <button
            onClick={handleRunSimulation}
            disabled={!selectedScenario || isRunning || isLoading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: theme.spacing.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              backgroundColor:
                !selectedScenario || isRunning || isLoading
                  ? theme.palette.border
                  : theme.palette.accent,
              color: theme.palette.surface,
              border: "none",
              borderRadius: theme.borderRadius.md,
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor:
                !selectedScenario || isRunning || isLoading
                  ? "not-allowed"
                  : "pointer",
              opacity:
                !selectedScenario || isRunning || isLoading ? 0.5 : 1,
              fontFamily: "inherit",
            }}
          >
            <Play size={16} />
            {isRunning || isLoading ? "Running..." : "Run Simulation"}
          </button>

          <button
            onClick={handleReset}
            disabled={isRunning || isLoading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: theme.spacing.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              backgroundColor: theme.palette.border,
              color: theme.palette.secondary,
              border: "none",
              borderRadius: theme.borderRadius.md,
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: isRunning || isLoading ? "not-allowed" : "pointer",
              opacity: isRunning || isLoading ? 0.5 : 1,
              fontFamily: "inherit",
            }}
          >
            <RotateCcw size={16} />
            Reset
          </button>
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div
          style={{
            backgroundColor: theme.palette.surface,
            borderRadius: theme.borderRadius.lg,
            border: `1px solid ${theme.palette.border}`,
            padding: theme.spacing.lg,
          }}
        >
          <div
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: theme.palette.primary,
              marginBottom: theme.spacing.lg,
            }}
          >
            Simulation Results
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: theme.spacing.lg,
            }}
          >
            {/* Before State */}
            {result.before && (
              <div
                style={{
                  backgroundColor: theme.palette.background,
                  padding: theme.spacing.md,
                  borderRadius: theme.borderRadius.md,
                  border: `1px solid ${theme.palette.border}`,
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: theme.palette.secondary,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                    marginBottom: theme.spacing.md,
                  }}
                >
                  Before Intervention
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.sm }}>
                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Total Loss
                    </div>
                    <div
                      style={{
                        fontSize: "1.25rem",
                        fontWeight: 700,
                        color: theme.palette.primary,
                      }}
                    >
                      ${(result.before.totalLoss / 1e9).toFixed(2)}B
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Peak Impact Day
                    </div>
                    <div
                      style={{
                        fontSize: "1rem",
                        fontWeight: 600,
                        color: theme.palette.primary,
                      }}
                    >
                      Day {result.before.peakDay}
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Affected Entities
                    </div>
                    <div
                      style={{
                        fontSize: "1rem",
                        fontWeight: 600,
                        color: theme.palette.primary,
                      }}
                    >
                      {result.before.affectedEntities}
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Avg Stress
                    </div>
                    <div
                      style={{
                        fontSize: "1rem",
                        fontWeight: 600,
                        color: theme.palette.primary,
                      }}
                    >
                      {(result.before.avgStress * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* After State */}
            <div
              style={{
                backgroundColor: theme.palette.background,
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.palette.border}`,
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: theme.palette.secondary,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  marginBottom: theme.spacing.md,
                }}
              >
                After Intervention
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.sm }}>
                <div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: theme.palette.secondary,
                      marginBottom: theme.spacing.xs,
                    }}
                  >
                    Total Loss
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: theme.palette.primary,
                    }}
                  >
                    ${(result.after.totalLoss / 1e9).toFixed(2)}B
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: theme.palette.secondary,
                      marginBottom: theme.spacing.xs,
                    }}
                  >
                    Peak Impact Day
                  </div>
                  <div
                    style={{
                      fontSize: "1rem",
                      fontWeight: 600,
                      color: theme.palette.primary,
                    }}
                  >
                    Day {result.after.peakDay}
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: theme.palette.secondary,
                      marginBottom: theme.spacing.xs,
                    }}
                  >
                    Affected Entities
                  </div>
                  <div
                    style={{
                      fontSize: "1rem",
                      fontWeight: 600,
                      color: theme.palette.primary,
                    }}
                  >
                    {result.after.affectedEntities}
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: theme.palette.secondary,
                      marginBottom: theme.spacing.xs,
                    }}
                  >
                    Avg Stress
                  </div>
                  <div
                    style={{
                      fontSize: "1rem",
                      fontWeight: 600,
                      color: theme.palette.primary,
                    }}
                  >
                    {(result.after.avgStress * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Delta (Change) */}
            {result.delta && (
              <div
                style={{
                  backgroundColor: theme.palette.background,
                  padding: theme.spacing.md,
                  borderRadius: theme.borderRadius.md,
                  border: `2px solid ${getPercentageColor(
                    Math.abs(result.delta.lossChangePct)
                  )}`,
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: theme.palette.secondary,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                    marginBottom: theme.spacing.md,
                  }}
                >
                  Change Impact
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.sm }}>
                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Loss Change
                    </div>
                    <div
                      style={{
                        fontSize: "1.25rem",
                        fontWeight: 700,
                        color: getChangeColor(result.delta.lossChange),
                      }}
                    >
                      {result.delta.lossChange < 0 ? "-" : "+"}$
                      {Math.abs(result.delta.lossChange / 1e9).toFixed(2)}B
                    </div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: getPercentageColor(
                          Math.abs(result.delta.lossChangePct)
                        ),
                        marginTop: theme.spacing.xs,
                      }}
                    >
                      {result.delta.lossChangePct < 0 ? "-" : "+"}
                      {Math.abs(result.delta.lossChangePct).toFixed(1)}%
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Stress Change
                    </div>
                    <div
                      style={{
                        fontSize: "1rem",
                        fontWeight: 600,
                        color: getChangeColor(result.delta.stressChange),
                      }}
                    >
                      {result.delta.stressChange < 0 ? "-" : "+"}
                      {Math.abs(result.delta.stressChange * 100).toFixed(1)}pp
                    </div>
                  </div>

                  <div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Entity Change
                    </div>
                    <div
                      style={{
                        fontSize: "1rem",
                        fontWeight: 600,
                        color: getChangeColor(result.delta.entityChange),
                      }}
                    >
                      {result.delta.entityChange < 0 ? "-" : "+"}
                      {Math.abs(result.delta.entityChange)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && (
        <div
          style={{
            backgroundColor: theme.palette.surface,
            borderRadius: theme.borderRadius.lg,
            border: `1px dashed ${theme.palette.border}`,
            padding: theme.spacing.xl,
            textAlign: "center",
            color: theme.palette.secondary,
          }}
        >
          Run a simulation to see results
        </div>
      )}
    </div>
  );
};
