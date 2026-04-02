"use client";

import { Entity } from "resium";
import {
  Cartesian3,
  Color,
  ArcType,
  PropertyBag,
} from "cesium";
import type { Flight } from "@/types";

interface FlightLayerProps {
  flights: Flight[];
  selectedId: string | null;
}

function riskToColor(risk: number): Color {
  if (risk >= 0.7) return Color.fromCssColorString("#ef4444");
  if (risk >= 0.4) return Color.fromCssColorString("#f59e0b");
  return Color.fromCssColorString("#10b981");
}

export function FlightLayer({ flights, selectedId }: FlightLayerProps) {
  if (!flights || flights.length === 0) return null;

  return (
    <>
      {/* Flight arc from origin to destination */}
      {flights.map((flight) => {
        if (!flight.origin?.location || !flight.destination?.location) return null;

        const isSelected = selectedId === flight.id;
        const color = riskToColor(flight.risk_score);
        const width = isSelected ? 4 : 2;
        const alpha = isSelected ? 1.0 : 0.6;

        const positions = Cartesian3.fromDegreesArrayHeights([
          flight.origin.location.lng,
          flight.origin.location.lat,
          0,
          flight.destination.location.lng,
          flight.destination.location.lat,
          0,
        ]);

        return (
          <Entity
            key={flight.id}
            id={flight.id}
            name={flight.callsign}
            description={`${flight.origin.iata} → ${flight.destination.iata} | Risk: ${(flight.risk_score * 100).toFixed(0)}%`}
            polyline={{
              positions,
              width,
              material: color.withAlpha(alpha),
              arcType: ArcType.GEODESIC,
              clampToGround: false,
            }}
            properties={
              new PropertyBag({
                entityType: "flight",
                riskScore: flight.risk_score,
              })
            }
          />
        );
      })}

      {/* Origin airport dots */}
      {flights.map((flight) => {
        if (!flight.origin?.location) return null;
        return (
          <Entity
            key={`origin-${flight.id}`}
            position={Cartesian3.fromDegrees(
              flight.origin.location.lng,
              flight.origin.location.lat,
              100
            )}
            point={{
              pixelSize: 4,
              color: Color.fromCssColorString("#3b82f6").withAlpha(0.7),
              outlineColor: Color.WHITE,
              outlineWidth: 1,
            }}
            name={flight.origin.iata}
          />
        );
      })}

      {/* Current aircraft position if available */}
      {flights.map((flight) => {
        if (!flight.position) return null;
        const isSelected = selectedId === flight.id;
        return (
          <Entity
            key={`pos-${flight.id}`}
            id={`pos-${flight.id}`}
            position={Cartesian3.fromDegrees(
              flight.position.lng,
              flight.position.lat,
              (flight.position.altitude_ft || 35000) * 0.3048
            )}
            point={{
              pixelSize: isSelected ? 8 : 5,
              color: riskToColor(flight.risk_score),
              outlineColor: Color.WHITE,
              outlineWidth: 1,
            }}
            name={flight.callsign}
            properties={
              new PropertyBag({
                entityType: "flight",
                riskScore: flight.risk_score,
              })
            }
          />
        );
      })}
    </>
  );
}
