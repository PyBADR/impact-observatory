"use client";

import React, { useMemo } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { EnterpriseKPI } from "@/types/enterprise";
import { theme } from "@/theme/tokens";

interface MetricsStripProps {
  metrics: EnterpriseKPI[];
  language: "en" | "ar";
}

const getSeverityColor = (severity?: string): string => {
  switch (severity) {
    case "CRITICAL":
      return theme.classification.critical;
    case "ELEVATED":
      return theme.classification.elevated;
    case "MODERATE":
      return theme.classification.moderate;
    case "LOW":
      return theme.classification.low;
    case "NOMINAL":
      return theme.classification.nominal;
    default:
      return theme.palette.secondary;
  }
};

const getTrendIcon = (trend?: "up" | "down" | "stable") => {
  switch (trend) {
    case "up":
      return <TrendingUp size={14} />;
    case "down":
      return <TrendingDown size={14} />;
    case "stable":
      return <Minus size={14} />;
    default:
      return null;
  }
};

const getTrendColor = (trend?: "up" | "down" | "stable"): string => {
  switch (trend) {
    case "up":
      return theme.classification.critical;
    case "down":
      return theme.classification.low;
    case "stable":
      return theme.palette.secondary;
    default:
      return theme.palette.secondary;
  }
};

export const MetricsStrip: React.FC<MetricsStripProps> = ({
  metrics,
  language,
}) => {
  const displayMetrics = useMemo(() => {
    return metrics.slice(0, 6);
  }, [metrics]);

  if (displayMetrics.length === 0) {
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
        No metrics available
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        gap: theme.spacing.md,
        flexWrap: "wrap",
        backgroundColor: theme.palette.background,
        padding: theme.spacing.lg,
        borderRadius: theme.borderRadius.lg,
        fontFamily:
          language === "ar"
            ? theme.typography.fontFamilyAr
            : theme.typography.fontFamily,
      }}
    >
      {displayMetrics.map((metric) => {
        const hasSparkline = metric.sparkline && metric.sparkline.length > 0;
        const minSparkline = hasSparkline
          ? Math.min(...metric.sparkline!)
          : 0;
        const maxSparkline = hasSparkline
          ? Math.max(...metric.sparkline!)
          : 1;
        const range = maxSparkline - minSparkline || 1;

        return (
          <div
            key={metric.id}
            style={{
              flex: "1 1 auto",
              minWidth: "140px",
              backgroundColor: theme.palette.surface,
              borderRadius: theme.borderRadius.lg,
              border: `1px solid ${theme.palette.border}`,
              padding: theme.spacing.lg,
              boxShadow: theme.shadow.sm,
              transition: "all 0.2s ease",
              display: "flex",
              flexDirection: "column",
              gap: theme.spacing.md,
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.boxShadow = theme.shadow.md;
              (e.currentTarget as HTMLDivElement).style.borderColor = theme.palette.accent;
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.boxShadow = theme.shadow.sm;
              (e.currentTarget as HTMLDivElement).style.borderColor = theme.palette.border;
            }}
          >
            {/* Header with Label and Trend */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: theme.spacing.sm,
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: theme.palette.secondary,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  flex: 1,
                  lineHeight: 1.2,
                }}
              >
                {language === "ar" ? metric.label_ar : metric.label}
              </div>
              {metric.trend && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "2px",
                    color: getTrendColor(metric.trend),
                    flexShrink: 0,
                  }}
                >
                  {getTrendIcon(metric.trend)}
                </div>
              )}
            </div>

            {/* Value Display */}
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: theme.spacing.xs,
              }}
            >
              <div
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color:
                    metric.severity
                      ? getSeverityColor(metric.severity)
                      : theme.palette.primary,
                }}
              >
                {typeof metric.value === "number"
                  ? metric.value.toFixed(1)
                  : metric.value}
              </div>
              <div
                style={{
                  fontSize: "0.75rem",
                  color: theme.palette.secondary,
                  fontWeight: 500,
                }}
              >
                {metric.unit}
              </div>
            </div>

            {/* Severity Indicator Badge */}
            {metric.severity && (
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: theme.spacing.xs,
                  paddingTop: theme.spacing.sm,
                  borderTop: `1px solid ${theme.palette.border}`,
                }}
              >
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: getSeverityColor(metric.severity),
                  }}
                />
                <div
                  style={{
                    fontSize: "0.7rem",
                    color: getSeverityColor(metric.severity),
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.02em",
                  }}
                >
                  {metric.severity}
                </div>
              </div>
            )}

            {/* Sparkline Chart */}
            {hasSparkline && (
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  gap: "2px",
                  height: "32px",
                  paddingTop: theme.spacing.sm,
                  borderTop: `1px solid ${theme.palette.border}`,
                  opacity: 0.7,
                }}
              >
                {metric.sparkline!.map((value, index) => {
                  const normalizedValue = (value - minSparkline) / range;
                  const barHeight = Math.max(2, normalizedValue * 28);

                  return (
                    <div
                      key={index}
                      style={{
                        flex: 1,
                        height: `${barHeight}px`,
                        backgroundColor: theme.palette.accent,
                        borderRadius: "1px",
                        opacity: 0.6 + (normalizedValue * 0.4),
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLDivElement).style.opacity = "1";
                        (e.currentTarget as HTMLDivElement).style.backgroundColor =
                          theme.palette.primary;
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLDivElement).style.opacity =
                          String(0.6 + normalizedValue * 0.4);
                        (e.currentTarget as HTMLDivElement).style.backgroundColor =
                          theme.palette.accent;
                      }}
                    />
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
