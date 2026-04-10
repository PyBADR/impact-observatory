"use client";

import React, { useMemo, useState } from "react";
import { scaleLinear } from "d3-scale";
import type { RiskHeatmapData } from "@/types/enterprise";
import { theme } from "@/theme/tokens";

interface RiskHeatmapProps {
  data: RiskHeatmapData;
  onEntitySelect?: (entityId: string) => void;
  language: "en" | "ar";
}

const getColorForValue = (value: number): string => {
  if (value < 0.2) return theme.classification.nominal;
  if (value < 0.35) return theme.classification.low;
  if (value < 0.5) return theme.classification.moderate;
  if (value < 0.65) return theme.classification.elevated;
  if (value < 0.8) return theme.classification.critical;
  return "#6B1C1C";
};

const classificationLevels: Record<string, { label: string; value: number }> = {
  NOMINAL: { label: "Nominal", value: 0.15 },
  LOW: { label: "Low", value: 0.275 },
  MODERATE: { label: "Moderate", value: 0.425 },
  ELEVATED: { label: "Elevated", value: 0.575 },
  CRITICAL: { label: "Critical", value: 0.725 },
};

export const RiskHeatmap: React.FC<RiskHeatmapProps> = ({
  data,
  onEntitySelect,
  language,
}) => {
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);

  const cellSize = 60;
  const labelWidth = 200;
  const cellSpacing = 4;

  const getCell = (entityId: string, dimension: string) => {
    return data.cells.find(
      (c) => c.entityId === entityId && c.dimension === dimension
    );
  };

  const sortedEntities = useMemo(() => {
    return [...data.entities].sort();
  }, [data.entities]);

  const sortedDimensions = useMemo(() => {
    return [...data.dimensions].sort();
  }, [data.dimensions]);

  if (data.cells.length === 0 || sortedEntities.length === 0 || sortedDimensions.length === 0) {
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
        No risk data available
      </div>
    );
  }

  const totalWidth = labelWidth + sortedDimensions.length * (cellSize + cellSpacing);
  const totalHeight = 60 + sortedEntities.length * (cellSize + cellSpacing) + 80;

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
      {/* Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: theme.spacing.md,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: theme.spacing.md }}>
          <label
            style={{
              fontSize: "0.875rem",
              fontWeight: 600,
              color: theme.palette.secondary,
            }}
          >
            Entities: {sortedEntities.length} | Dimensions: {sortedDimensions.length}
          </label>
        </div>
        {selectedEntity && (
          <button
            onClick={() => {
              setSelectedEntity(null);
            }}
            style={{
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              backgroundColor: theme.palette.secondary,
              color: theme.palette.surface,
              border: "none",
              borderRadius: theme.borderRadius.md,
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            Clear Filter
          </button>
        )}
      </div>

      {/* Heatmap Grid */}
      <div
        style={{
          overflowX: "auto",
          overflowY: "auto",
          maxHeight: "600px",
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          padding: theme.spacing.md,
        }}
      >
        <svg
          width={totalWidth}
          height={totalHeight}
          style={{ minWidth: "100%", display: "block" }}
        >
          {/* Column Headers (Dimensions) */}
          {sortedDimensions.map((dimension, dimIndex) => (
            <text
              key={`header-${dimension}`}
              x={labelWidth + dimIndex * (cellSize + cellSpacing) + cellSize / 2}
              y={25}
              fontSize="12"
              fontWeight="600"
              fill={theme.palette.primary}
              textAnchor="middle"
              style={{ textTransform: "capitalize" }}
            >
              {dimension.substring(0, 6)}
            </text>
          ))}

          {/* Heatmap Cells */}
          {sortedEntities.map((entityId, entityIndex) => {
            const isSelected = selectedEntity === null || selectedEntity === entityId;
            const opacity = selectedEntity === null ? 1 : selectedEntity === entityId ? 1 : 0.3;

            return (
              <g key={`entity-${entityId}`} opacity={opacity}>
                {/* Entity Label */}
                <rect
                  x={0}
                  y={60 + entityIndex * (cellSize + cellSpacing)}
                  width={labelWidth}
                  height={cellSize}
                  fill={selectedEntity === entityId ? theme.palette.accent : theme.palette.border}
                  opacity={0.1}
                  style={{ cursor: "pointer" }}
                  onClick={() => {
                    setSelectedEntity(entityId);
                    onEntitySelect?.(entityId);
                  }}
                />

                <text
                  x={labelWidth - Number(theme.spacing.md.replace("rem", "")) * 16}
                  y={60 + entityIndex * (cellSize + cellSpacing) + cellSize / 2}
                  fontSize="11"
                  fontWeight={selectedEntity === entityId ? "600" : "500"}
                  fill={selectedEntity === entityId ? theme.palette.accent : theme.palette.primary}
                  textAnchor="end"
                  dy="0.3em"
                  style={{
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onClick={() => {
                    setSelectedEntity(entityId);
                    onEntitySelect?.(entityId);
                  }}
                >
                  {entityId.substring(0, 20)}
                </text>

                {/* Risk Cells */}
                {sortedDimensions.map((dimension, dimIndex) => {
                  const cell = getCell(entityId, dimension);
                  const cellId = `${entityId}-${dimension}`;
                  const isHovered = hoveredCell === cellId;
                  const value = cell?.value ?? 0;

                  return (
                    <g key={cellId}>
                      {/* Cell Background */}
                      <rect
                        x={labelWidth + dimIndex * (cellSize + cellSpacing)}
                        y={60 + entityIndex * (cellSize + cellSpacing)}
                        width={cellSize}
                        height={cellSize}
                        fill={getColorForValue(value)}
                        opacity={isHovered ? 0.9 : 0.7}
                        stroke={
                          isHovered
                            ? theme.palette.primary
                            : theme.palette.border
                        }
                        strokeWidth={isHovered ? 2 : 1}
                        style={{
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        }}
                        onMouseEnter={() => setHoveredCell(cellId)}
                        onMouseLeave={() => setHoveredCell(null)}
                      />

                      {/* Cell Value */}
                      {cell && (
                        <text
                          x={
                            labelWidth +
                            dimIndex * (cellSize + cellSpacing) +
                            cellSize / 2
                          }
                          y={
                            60 +
                            entityIndex * (cellSize + cellSpacing) +
                            cellSize / 2
                          }
                          fontSize={isHovered ? "13" : "11"}
                          fontWeight="600"
                          fill={theme.palette.surface}
                          textAnchor="middle"
                          dy="0.3em"
                          style={{
                            pointerEvents: "none",
                            transition: "all 0.2s ease",
                          }}
                        >
                          {(value * 100).toFixed(0)}
                        </text>
                      )}

                      {/* Tooltip */}
                      {isHovered && cell && (
                        <g
                          style={{
                            pointerEvents: "none",
                          }}
                        >
                          <rect
                            x={
                              labelWidth +
                              dimIndex * (cellSize + cellSpacing) +
                              cellSize / 2 -
                              60
                            }
                            y={
                              60 +
                              entityIndex * (cellSize + cellSpacing) -
                              55
                            }
                            width="120"
                            height="50"
                            fill={theme.palette.primary}
                            rx={theme.borderRadius.sm}
                            opacity={0.95}
                          />

                          <text
                            x={
                              labelWidth +
                              dimIndex * (cellSize + cellSpacing) +
                              cellSize / 2
                            }
                            y={
                              60 +
                              entityIndex * (cellSize + cellSpacing) -
                              40
                            }
                            fontSize="11"
                            fontWeight="600"
                            fill={theme.palette.surface}
                            textAnchor="middle"
                          >
                            {dimension}
                          </text>

                          <text
                            x={
                              labelWidth +
                              dimIndex * (cellSize + cellSpacing) +
                              cellSize / 2
                            }
                            y={
                              60 +
                              entityIndex * (cellSize + cellSpacing) -
                              25
                            }
                            fontSize="12"
                            fontWeight="700"
                            fill={theme.palette.surface}
                            textAnchor="middle"
                          >
                            {(value * 100).toFixed(1)}%
                          </text>

                          <text
                            x={
                              labelWidth +
                              dimIndex * (cellSize + cellSpacing) +
                              cellSize / 2
                            }
                            y={
                              60 +
                              entityIndex * (cellSize + cellSpacing) -
                              10
                            }
                            fontSize="10"
                            fill="rgba(255, 255, 255, 0.8)"
                            textAnchor="middle"
                            style={{ textTransform: "uppercase" }}
                          >
                            {cell.severity}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: theme.spacing.lg,
          padding: theme.spacing.lg,
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          flexWrap: "wrap",
        }}
      >
        {(["NOMINAL", "LOW", "MODERATE", "ELEVATED", "CRITICAL"] as const).map((level) => {
          const val = classificationLevels[level];
          return (
            <div
              key={level}
              style={{
                display: "flex",
                alignItems: "center",
                gap: theme.spacing.sm,
              }}
            >
              <div
                style={{
                  width: "20px",
                  height: "20px",
                  backgroundColor: getColorForValue(val.value),
                  borderRadius: theme.borderRadius.sm,
                  opacity: 0.7,
                }}
              />
              <div
                style={{
                  fontSize: "0.875rem",
                  color: theme.palette.secondary,
                }}
              >
                {val.label}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {selectedEntity && (
        <div
          style={{
            padding: theme.spacing.lg,
            backgroundColor: theme.palette.surface,
            borderRadius: theme.borderRadius.lg,
            border: `1px solid ${theme.palette.border}`,
          }}
        >
          <div
            style={{
              fontSize: "0.875rem",
              fontWeight: 600,
              color: theme.palette.secondary,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              marginBottom: theme.spacing.md,
            }}
          >
            Entity Risk Profile
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              gap: theme.spacing.md,
            }}
          >
            {sortedDimensions.map((dimension) => {
              const cell = getCell(selectedEntity, dimension);
              return (
                <div key={`summary-${dimension}`}>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: theme.palette.secondary,
                      marginBottom: theme.spacing.xs,
                      textTransform: "capitalize",
                    }}
                  >
                    {dimension}
                  </div>
                  <div
                    style={{
                      fontSize: "1.25rem",
                      fontWeight: 700,
                      color: getColorForValue(cell?.value ?? 0),
                    }}
                  >
                    {cell ? (cell.value * 100).toFixed(1) : "0"}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
