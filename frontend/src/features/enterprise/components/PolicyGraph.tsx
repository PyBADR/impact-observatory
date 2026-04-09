"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import { forceSimulation, forceLink, forceManyBody, forceCenter } from "d3-force";
import { scaleLinear } from "d3-scale";
import type { PolicyNode, PolicyEdge } from "@/types/enterprise";
import { theme } from "@/theme/tokens";

interface PolicyGraphProps {
  nodes: PolicyNode[];
  edges: PolicyEdge[];
  onNodeSelect?: (node: PolicyNode) => void;
  language: "en" | "ar";
}

interface SimulationNode extends PolicyNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface SimulationEdge {
  source: SimulationNode | string;
  target: SimulationNode | string;
  label: string;
  type: "requires" | "blocks" | "enables" | "triggers";
  weight: number;
}

const getNodeColor = (type: string): string => {
  switch (type) {
    case "rule":
      return theme.palette.accent;
    case "constraint":
      return theme.palette.warning;
    case "threshold":
      return theme.classification.critical;
    case "action":
      return theme.classification.low;
    case "decision_path":
      return theme.palette.secondary;
    default:
      return theme.palette.secondary;
  }
};

const getEdgeDashArray = (
  type: "requires" | "blocks" | "enables" | "triggers"
): string => {
  switch (type) {
    case "requires":
      return "0";
    case "blocks":
      return "5,5";
    case "enables":
      return "10,5";
    case "triggers":
      return "3,3";
    default:
      return "0";
  }
};

export const PolicyGraph: React.FC<PolicyGraphProps> = ({
  nodes,
  edges,
  onNodeSelect,
  language,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<PolicyNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const simulationNodesRef = useRef<SimulationNode[]>([]);
  const simulationEdgesRef = useRef<SimulationEdge[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const simulationRef = useRef<any>(null);

  const nodeRadiusScale = useMemo(() => {
    const maxWeight = Math.max(...nodes.map((n) => n.weight), 1);
    return scaleLinear().domain([0, maxWeight]).range([8, 24]);
  }, [nodes]);

  useEffect(() => {
    const container = svgRef.current?.parentElement;
    if (!container) return;

    const handleResize = () => {
      const { width, height } = container.getBoundingClientRect();
      setDimensions({ width: Math.max(600, width), height: Math.max(400, height) });
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    simulationNodesRef.current = nodes.map((node, i) => ({
      ...node,
      x: Math.random() * dimensions.width,
      y: Math.random() * dimensions.height,
    }));

    simulationEdgesRef.current = edges.map((edge) => ({
      ...edge,
      source: simulationNodesRef.current.find((n) => n.id === edge.source)!,
      target: simulationNodesRef.current.find((n) => n.id === edge.target)!,
    }));

    const simulation = forceSimulation<SimulationNode>(
      simulationNodesRef.current
    )
      .force(
        "link",
        forceLink<SimulationNode, SimulationEdge>(simulationEdgesRef.current)
          .id((d) => (d as SimulationNode).id)
          .distance(120)
          .strength(0.5)
      )
      .force("charge", forceManyBody().strength(-400))
      .force("center", forceCenter(dimensions.width / 2, dimensions.height / 2))
      .on("tick", () => {
        if (svgRef.current) {
          svgRef.current.style.background = "transparent";
        }
      });

    simulationRef.current = simulation;

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, dimensions]);

  const handleNodeClick = (node: PolicyNode) => {
    setSelectedNode(node);
    onNodeSelect?.(node);
  };

  const connectedNodeIds = useMemo(() => {
    if (!selectedNode) return new Set();
    const connected = new Set<string>([selectedNode.id]);
    edges.forEach((edge) => {
      if (edge.source === selectedNode.id) connected.add(edge.target);
      if (edge.target === selectedNode.id) connected.add(edge.source);
    });
    return connected;
  }, [selectedNode, edges]);

  const isNodeHighlighted = (nodeId: string) => {
    return (
      selectedNode?.id === nodeId ||
      hoveredNode === nodeId ||
      connectedNodeIds.has(nodeId)
    );
  };

  const isEdgeHighlighted = (edge: PolicyEdge) => {
    if (!selectedNode) return false;
    return (
      (edge.source === selectedNode.id || edge.target === selectedNode.id) &&
      (connectedNodeIds.has(edge.source as string) &&
        connectedNodeIds.has(edge.target as string))
    );
  };

  if (nodes.length === 0) {
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
        No policy nodes available
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
        borderRadius: theme.borderRadius.lg,
        padding: theme.spacing.lg,
      }}
    >
      {/* Legend */}
      <div
        style={{
          display: "flex",
          gap: theme.spacing.lg,
          flexWrap: "wrap",
          fontSize: "0.875rem",
          color: theme.palette.secondary,
        }}
      >
        {(["rule", "constraint", "threshold", "action"] as const).map((type) => (
          <div key={type} style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
            <div
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: getNodeColor(type),
              }}
            />
            <span style={{ textTransform: "capitalize" }}>{type}</span>
          </div>
        ))}
      </div>

      {/* Graph Container */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: dimensions.height,
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          overflow: "hidden",
        }}
      >
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          style={{
            display: "block",
            fontFamily: theme.typography.fontFamily,
          }}
        >
          {/* Edges */}
          {simulationEdgesRef.current.map((edge, i) => {
            const isHighlighted = isEdgeHighlighted(edge as PolicyEdge);
            const sourceNode = edge.source as SimulationNode;
            const targetNode = edge.target as SimulationNode;

            return (
              <g key={`edge-${i}`}>
                <line
                  x1={sourceNode.x || 0}
                  y1={sourceNode.y || 0}
                  x2={targetNode.x || 0}
                  y2={targetNode.y || 0}
                  stroke={isHighlighted ? theme.palette.accent : theme.palette.border}
                  strokeWidth={isHighlighted ? 2 : 1}
                  strokeDasharray={getEdgeDashArray(edge.type)}
                  opacity={isHighlighted ? 1 : 0.5}
                  style={{ transition: "all 0.2s ease" }}
                />

                {/* Edge Label */}
                {(sourceNode.x && targetNode.x && sourceNode.y && targetNode.y) && (
                  <text
                    x={(sourceNode.x + targetNode.x) / 2}
                    y={(sourceNode.y + targetNode.y) / 2}
                    fontSize="10"
                    fill={theme.palette.secondary}
                    textAnchor="middle"
                    opacity={0.6}
                    style={{ pointerEvents: "none" }}
                  >
                    {edge.type}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {simulationNodesRef.current.map((node) => {
            const radius = nodeRadiusScale(node.weight);
            const isHighlighted = isNodeHighlighted(node.id);
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={`node-${node.id}`}
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => handleNodeClick(node)}
              >
                {/* Node Circle */}
                <circle
                  cx={node.x || 0}
                  cy={node.y || 0}
                  r={radius}
                  fill={getNodeColor(node.type)}
                  opacity={isHighlighted ? 1 : 0.6}
                  style={{
                    transition: "all 0.2s ease",
                    filter: isSelected ? `drop-shadow(0 0 8px ${getNodeColor(node.type)})` : "none",
                  }}
                  stroke={isSelected ? getNodeColor(node.type) : "none"}
                  strokeWidth={isSelected ? 2 : 0}
                />

                {/* Status Indicator */}
                {(node.active || node.triggered) && (
                  <circle
                    cx={(node.x || 0) + radius - 3}
                    cy={(node.y || 0) - radius + 3}
                    r={4}
                    fill={node.triggered ? theme.classification.critical : theme.classification.low}
                    opacity={0.8}
                  />
                )}

                {/* Node Label */}
                <text
                  x={node.x || 0}
                  y={node.y || 0}
                  fontSize="11"
                  fontWeight={isSelected ? "bold" : "normal"}
                  fill={theme.palette.surface}
                  textAnchor="middle"
                  dy="0.3em"
                  opacity={isHighlighted ? 1 : 0.7}
                  style={{
                    pointerEvents: "none",
                    transition: "opacity 0.2s ease",
                    maxWidth: radius * 2,
                  }}
                >
                  {language === "ar" ? node.label_ar : node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Details Panel */}
      {selectedNode && (
        <div
          style={{
            padding: theme.spacing.lg,
            backgroundColor: theme.palette.surface,
            borderRadius: theme.borderRadius.lg,
            border: `1px solid ${theme.palette.border}`,
            boxShadow: theme.shadow.md,
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: theme.spacing.lg,
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
                Name
              </div>
              <div
                style={{
                  fontSize: "1rem",
                  fontWeight: 600,
                  color: theme.palette.primary,
                }}
              >
                {language === "ar" ? selectedNode.label_ar : selectedNode.label}
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
                Type
              </div>
              <div
                style={{
                  fontSize: "0.875rem",
                  color: getNodeColor(selectedNode.type),
                  fontWeight: 600,
                  textTransform: "capitalize",
                }}
              >
                {selectedNode.type}
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
                Sector
              </div>
              <div style={{ fontSize: "0.875rem", color: theme.palette.primary }}>
                {selectedNode.sector}
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
                Weight
              </div>
              <div style={{ fontSize: "0.875rem", color: theme.palette.primary }}>
                {selectedNode.weight.toFixed(2)}
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
                Status
              </div>
              <div style={{ display: "flex", gap: theme.spacing.sm }}>
                <div
                  style={{
                    display: "inline-block",
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    backgroundColor: selectedNode.active
                      ? theme.classification.low
                      : theme.palette.border,
                    color: selectedNode.active
                      ? theme.palette.surface
                      : theme.palette.secondary,
                    borderRadius: theme.borderRadius.sm,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                  }}
                >
                  {selectedNode.active ? "Active" : "Inactive"}
                </div>
                {selectedNode.triggered && (
                  <div
                    style={{
                      display: "inline-block",
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      backgroundColor: theme.classification.critical,
                      color: theme.palette.surface,
                      borderRadius: theme.borderRadius.sm,
                      fontSize: "0.75rem",
                      fontWeight: 600,
                    }}
                  >
                    Triggered
                  </div>
                )}
              </div>
            </div>
          </div>

          {selectedNode.description && (
            <div
              style={{
                marginTop: theme.spacing.lg,
                paddingTop: theme.spacing.lg,
                borderTop: `1px solid ${theme.palette.border}`,
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
                Description
              </div>
              <div
                style={{
                  fontSize: "0.875rem",
                  lineHeight: 1.6,
                  color: theme.palette.primary,
                }}
              >
                {selectedNode.description}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
