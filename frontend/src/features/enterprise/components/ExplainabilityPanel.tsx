"use client";

import React, { useMemo } from "react";
import { theme } from "@/theme/tokens";
import type { ExplainabilityFactor } from "@/types/enterprise";
import type { ExplanationPack, DecisionAction } from "@/types/observatory";

interface ExplainabilityPanelProps {
  explanation: ExplanationPack;
  language: "en" | "ar";
  actions?: DecisionAction[];
}

const getContributionColor = (contribution: number): string => {
  if (contribution > 0.5) return theme.classification.critical;
  if (contribution > 0.25) return theme.classification.elevated;
  if (contribution > 0) return theme.classification.moderate;
  if (contribution > -0.25) return theme.classification.low;
  return theme.classification.nominal;
};

const getFactorTypeColor = (type: string): string => {
  switch (type) {
    case "risk":
      return theme.classification.critical;
    case "policy":
      return theme.palette.accent;
    case "market":
      return theme.classification.elevated;
    case "geopolitical":
      return theme.classification.moderate;
    case "model":
      return theme.palette.secondary;
    default:
      return theme.palette.secondary;
  }
};

export const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({
  explanation,
  language,
  actions,
}) => {
  const maxAbsContribution = useMemo(() => {
    return 1;
  }, []);

  if (!explanation) {
    return (
      <div
        style={{
          padding: theme.spacing.xl,
          textAlign: "center",
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          color: theme.palette.secondary,
          fontFamily: theme.typography.fontFamily,
        }}
      >
        No explanation available
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing.lg,
        backgroundColor: theme.palette.background,
        padding: theme.spacing.lg,
        borderRadius: theme.borderRadius.lg,
        fontFamily: language === "ar" ? theme.typography.fontFamilyAr : theme.typography.fontFamily,
      }}
    >
      {/* Header */}
      <div>
        <div
          style={{
            fontSize: "0.75rem",
            fontWeight: 600,
            color: theme.palette.secondary,
            textTransform: "uppercase",
            letterSpacing: "0.04em",
            marginBottom: theme.spacing.sm,
          }}
        >
          Decision Explanation
        </div>
        <div
          style={{
            fontSize: "1.125rem",
            fontWeight: 600,
            color: theme.palette.primary,
            marginBottom: theme.spacing.md,
          }}
        >
          {explanation.scenario_label}
        </div>
        <div
          style={{
            fontSize: "0.875rem",
            color: theme.palette.secondary,
          }}
        >
          Run ID: {explanation.run_id}
        </div>
      </div>

      {/* Confidence & Methodology */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: theme.spacing.lg,
          backgroundColor: theme.palette.surface,
          padding: theme.spacing.lg,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
        }}
      >
        <div>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: theme.palette.secondary,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              marginBottom: theme.spacing.sm,
            }}
          >
            Confidence Score
          </div>
          <div
            style={{
              fontSize: "2rem",
              fontWeight: 700,
              color: explanation.confidence >= 0.8 
                ? theme.classification.low 
                : explanation.confidence >= 0.6 
                  ? theme.classification.moderate 
                  : theme.classification.elevated,
              marginBottom: theme.spacing.md,
            }}
          >
            {(explanation.confidence * 100).toFixed(0)}%
          </div>
          <div
            style={{
              width: "100%",
              height: "8px",
              backgroundColor: theme.palette.border,
              borderRadius: theme.borderRadius.sm,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${explanation.confidence * 100}%`,
                backgroundColor: explanation.confidence >= 0.8 
                  ? theme.classification.low 
                  : explanation.confidence >= 0.6 
                    ? theme.classification.moderate 
                    : theme.classification.elevated,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>

        <div>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: theme.palette.secondary,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              marginBottom: theme.spacing.sm,
            }}
          >
            Methodology
          </div>
          <div
            style={{
              fontSize: "0.875rem",
              color: theme.palette.primary,
              lineHeight: 1.6,
            }}
          >
            {explanation.methodology}
          </div>
        </div>
      </div>

      {/* Reasoning Narrative */}
      <div
        style={{
          backgroundColor: theme.palette.surface,
          padding: theme.spacing.lg,
          borderRadius: theme.borderRadius.lg,
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
          Reasoning
        </div>
        <div
          style={{
            fontSize: "0.875rem",
            lineHeight: 1.8,
            color: theme.palette.primary,
          }}
        >
          {language === "ar" ? explanation.narrative_ar : explanation.narrative_en}
        </div>
      </div>


      {/* Causal Chain */}
      {explanation.causal_chain && explanation.causal_chain.length > 0 && (
        <div
          style={{
            backgroundColor: theme.palette.surface,
            padding: theme.spacing.lg,
            borderRadius: theme.borderRadius.lg,
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
            Causal Chain ({explanation.causal_chain.length} steps)
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: theme.spacing.md,
            }}
          >
            {explanation.causal_chain.map((step, index) => (
              <div key={index}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: theme.spacing.md,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      minWidth: "32px",
                      minHeight: "32px",
                      backgroundColor: theme.palette.accent,
                      color: theme.palette.surface,
                      borderRadius: "50%",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                    }}
                  >
                    {index + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontSize: "0.875rem",
                        fontWeight: 600,
                        color: theme.palette.primary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      {step.event}
                    </div>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                      }}
                    >
                      Impact: {step.impact_usd?.toFixed(2) || "N/A"}
                    </div>
                  </div>
                </div>
                {index < explanation.causal_chain.length - 1 && (
                  <div
                    style={{
                      marginLeft: "16px",
                      marginTop: theme.spacing.md,
                      marginBottom: theme.spacing.md,
                      paddingLeft: theme.spacing.md,
                      borderLeft: `2px solid ${theme.palette.accent}`,
                      opacity: 0.5,
                    }}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
