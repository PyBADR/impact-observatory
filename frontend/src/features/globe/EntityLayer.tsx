"use client";

import type { ImpactedEntity } from "@/types/observatory";

const CLASSIFICATION_COLORS: Record<string, string> = {
  CRITICAL: "#ef4444",
  ELEVATED: "#f97316",
  MODERATE: "#eab308",
  LOW: "#22c55e",
  NOMINAL: "#64748b",
};

interface Props {
  entities: ImpactedEntity[];
  selectedEntityId?: string | null;
  onEntityClick?: (entity: ImpactedEntity) => void;
  isAr?: boolean;
}

/**
 * 2D fallback entity layer for when CesiumJS is not available.
 * Renders impacted entities as positioned dots on a simple map projection.
 */
export function EntityLayer({ entities, selectedEntityId, onEntityClick, isAr = false }: Props) {
  if (!entities.length) return null;

  // Simple mercator projection for GCC region (lat 10-40, lng 35-65)
  const project = (lat: number, lng: number) => ({
    x: ((lng - 35) / 30) * 100,
    y: ((40 - lat) / 30) * 100,
  });

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden">
      {/* Region label */}
      <div className="absolute top-2 left-2 text-xs text-slate-500">
        {isAr ? "منطقة الخليج العربي" : "GCC Region"}
      </div>

      {/* Entity dots */}
      {entities.map((entity) => {
        const pos = project(entity.lat, entity.lng);
        const color = CLASSIFICATION_COLORS[entity.classification] || "#64748b";
        const isSelected = selectedEntityId === entity.node_id;
        const size = Math.max(6, Math.min(20, entity.stress * 30));

        return (
          <button
            key={entity.node_id}
            onClick={() => onEntityClick?.(entity)}
            className="absolute transform -translate-x-1/2 -translate-y-1/2 transition-all group"
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
            }}
            title={`${entity.label}: ${(entity.stress * 100).toFixed(1)}% stress`}
          >
            {/* Pulse ring for critical */}
            {entity.classification === "CRITICAL" && (
              <span
                className="absolute inset-0 rounded-full animate-ping opacity-30"
                style={{
                  backgroundColor: color,
                  width: size + 8,
                  height: size + 8,
                  marginLeft: -(size + 8) / 2,
                  marginTop: -(size + 8) / 2,
                  left: "50%",
                  top: "50%",
                }}
              />
            )}

            {/* Dot */}
            <span
              className={`block rounded-full border-2 ${
                isSelected ? "border-white" : "border-transparent"
              }`}
              style={{
                width: size,
                height: size,
                backgroundColor: color,
                boxShadow: `0 0 ${size}px ${color}66`,
              }}
            />

            {/* Label on hover */}
            <span className="absolute left-1/2 -translate-x-1/2 top-full mt-1 whitespace-nowrap text-[10px] text-white bg-slate-900/90 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              {isAr && entity.label_ar ? entity.label_ar : entity.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
