"use client";

import { Entity } from "resium";
import {
  Cartesian3,
  Color,
  Math as CesiumMath,
  PropertyBag,
} from "cesium";
import type { Vessel } from "@/types";

interface VesselLayerProps {
  vessels: Vessel[];
  selectedId: string | null;
}

function vesselRiskColor(risk: number): Color {
  if (risk >= 0.7) return Color.fromCssColorString("#ef4444");
  if (risk >= 0.4) return Color.fromCssColorString("#f59e0b");
  return Color.fromCssColorString("#10b981");
}

export function VesselLayer({ vessels, selectedId }: VesselLayerProps) {
  if (!vessels || vessels.length === 0) return null;

  return (
    <>
      {vessels.map((vessel) => {
        if (!vessel.position) return null;

        const isSelected = selectedId === vessel.id;
        const color = vesselRiskColor(vessel.risk_score);
        const size = isSelected ? 10 : 6;

        return (
          <Entity
            key={vessel.id}
            id={vessel.id}
            name={vessel.name}
            description={`${vessel.vessel_type} | ${vessel.flag_country} | Risk: ${(vessel.risk_score * 100).toFixed(0)}%`}
            position={Cartesian3.fromDegrees(
              vessel.position.lng,
              vessel.position.lat,
              0
            )}
            point={{
              pixelSize: size,
              color: color,
              outlineColor: isSelected ? Color.WHITE : Color.BLACK,
              outlineWidth: isSelected ? 2 : 1,
            }}
            properties={
              new PropertyBag({
                entityType: "vessel",
                riskScore: vessel.risk_score,
                vesselType: vessel.vessel_type,
              })
            }
          />
        );
      })}

      {/* Heading indicators — short lines showing direction */}
      {vessels.map((vessel) => {
        if (!vessel.position || vessel.position.heading === undefined) return null;

        const headingRad = CesiumMath.toRadians(vessel.position.heading);
        const len = 0.05; // degrees offset for heading line
        const endLat = vessel.position.lat + Math.cos(headingRad) * len;
        const endLng = vessel.position.lng + Math.sin(headingRad) * len;

        return (
          <Entity
            key={`heading-${vessel.id}`}
            polyline={{
              positions: Cartesian3.fromDegreesArray([
                vessel.position.lng,
                vessel.position.lat,
                endLng,
                endLat,
              ]),
              width: 2,
              material: vesselRiskColor(vessel.risk_score).withAlpha(0.5),
              clampToGround: true,
            }}
          />
        );
      })}
    </>
  );
}
