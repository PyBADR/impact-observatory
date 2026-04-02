"use client";

import { Entity, EllipseGraphics } from "resium";
import {
  Cartesian3,
  Color,
  PropertyBag,
} from "cesium";
import type { Event, EventType } from "@/types";

interface ConflictLayerProps {
  events: Event[];
}

const EVENT_COLORS: Record<string, string> = {
  kinetic: "#ef4444",
  terrorism: "#dc2626",
  sanctions: "#f97316",
  protest: "#eab308",
  cyber: "#a855f7",
  natural_disaster: "#06b6d4",
  political: "#f59e0b",
  economic: "#3b82f6",
};

function eventColor(eventType: EventType): Color {
  const hex = EVENT_COLORS[eventType] || "#6b7280";
  return Color.fromCssColorString(hex);
}

function severityToRadius(severity: number): number {
  // Map 0..1 severity to 5km..80km radius
  return 5_000 + severity * 75_000;
}

export function ConflictLayer({ events }: ConflictLayerProps) {
  if (!events || events.length === 0) return null;

  return (
    <>
      {events.map((event) => {
        if (!event.location) return null;

        const color = eventColor(event.event_type);
        const radius = severityToRadius(event.severity_score);

        return (
          <Entity
            key={event.id}
            id={event.id}
            name={event.title}
            description={`${event.event_type} | Severity: ${(event.severity_score * 100).toFixed(0)}% | ${event.region}`}
            position={Cartesian3.fromDegrees(
              event.location.lng,
              event.location.lat,
              0
            )}
            properties={
              new PropertyBag({
                entityType: "event",
                eventType: event.event_type,
                severity: event.severity_score,
              })
            }
          >
            {/* Outer pulsing ring */}
            <EllipseGraphics
              semiMajorAxis={radius}
              semiMinorAxis={radius}
              material={color.withAlpha(0.15)}
              outline
              outlineColor={color.withAlpha(0.4)}
              outlineWidth={2}
              height={0}
            />

            {/* Inner solid core */}
            <EllipseGraphics
              semiMajorAxis={radius * 0.3}
              semiMinorAxis={radius * 0.3}
              material={color.withAlpha(0.5)}
              outline={false}
              height={0}
            />
          </Entity>
        );
      })}

      {/* Point markers on top for visibility at all zoom levels */}
      {events.map((event) => {
        if (!event.location) return null;

        const color = eventColor(event.event_type);

        return (
          <Entity
            key={`pt-${event.id}`}
            position={Cartesian3.fromDegrees(
              event.location.lng,
              event.location.lat,
              100
            )}
            point={{
              pixelSize: Math.max(4, event.severity_score * 12),
              color: color,
              outlineColor: Color.WHITE,
              outlineWidth: 1,
            }}
          />
        );
      })}
    </>
  );
}
