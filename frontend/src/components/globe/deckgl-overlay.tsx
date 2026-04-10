"use client";

import { useMemo } from "react";
import { ScatterplotLayer, ArcLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import type { Event, Flight, Vessel } from "@/types";

/**
 * DeckGLOverlay generates deck.gl layer descriptors for overlaying on the Cesium globe.
 * In a full integration, these layers are rendered via a deck.gl canvas that is
 * synchronized with the Cesium camera. This component returns the layer configurations.
 *
 * IMPORTANT: deck.gl is an OVERLAY on Cesium, not the core map engine.
 */

interface DeckGLOverlayProps {
  events: Event[];
  flights: Flight[];
  vessels: Vessel[];
  activeLayers: Set<string>;
}

export function useDeckGLLayers({
  events,
  flights,
  vessels,
  activeLayers,
}: DeckGLOverlayProps) {
  const layers = useMemo(() => {
    const result: any[] = [];

    // Heatmap layer — risk density from events
    if (activeLayers.has("heatmap") && events.length > 0) {
      result.push(
        new HeatmapLayer({
          id: "risk-heatmap",
          data: events,
          getPosition: (d: Event) => [d.location.lng, d.location.lat],
          getWeight: (d: Event) => d.severity_score,
          radiusPixels: 60,
          intensity: 2,
          threshold: 0.1,
          colorRange: [
            [0, 25, 0, 25],
            [0, 85, 0, 100],
            [255, 255, 0, 150],
            [255, 165, 0, 180],
            [255, 69, 0, 200],
            [255, 0, 0, 230],
          ],
        })
      );
    }

    // Scatterplot layer — high-value infrastructure (vessels at rest)
    if (activeLayers.has("infrastructure") && vessels.length > 0) {
      result.push(
        new ScatterplotLayer({
          id: "infrastructure-scatter",
          data: vessels.filter((v) => v.position.speed_knots < 1),
          getPosition: (d: Vessel) => [d.position.lng, d.position.lat],
          getRadius: 5000,
          getFillColor: (d: Vessel) => {
            const r = d.risk_score;
            if (r >= 0.7) return [239, 68, 68, 200];
            if (r >= 0.4) return [245, 158, 11, 180];
            return [16, 185, 129, 160];
          },
          radiusMinPixels: 3,
          radiusMaxPixels: 15,
          pickable: true,
        })
      );
    }

    // Arc layer — trade routes (flight arcs as deck.gl arcs)
    if (activeLayers.has("arcs") && flights.length > 0) {
      result.push(
        new ArcLayer({
          id: "trade-arcs",
          data: flights.filter(
            (f) => f.origin?.location && f.destination?.location
          ),
          getSourcePosition: (d: Flight) => [
            d.origin.location.lng,
            d.origin.location.lat,
          ],
          getTargetPosition: (d: Flight) => [
            d.destination.location.lng,
            d.destination.location.lat,
          ],
          getSourceColor: (d: Flight) => {
            const r = d.risk_score;
            if (r >= 0.7) return [239, 68, 68, 180];
            if (r >= 0.4) return [245, 158, 11, 150];
            return [59, 130, 246, 120];
          },
          getTargetColor: (d: Flight) => {
            const r = d.risk_score;
            if (r >= 0.7) return [239, 68, 68, 80];
            if (r >= 0.4) return [245, 158, 11, 60];
            return [59, 130, 246, 50];
          },
          getWidth: 1.5,
          greatCircle: true,
          pickable: true,
        })
      );
    }

    return result;
  }, [events, flights, vessels, activeLayers]);

  return layers;
}

/**
 * DeckGLOverlayCanvas renders a deck.gl canvas that overlays the Cesium viewer.
 * It syncs with the Cesium camera via a shared viewState.
 *
 * NOTE: Full Cesium + deck.gl integration requires sharing camera state.
 * This is a simplified overlay that provides the layer definitions.
 * In production, use @deck.gl/cesium or manual camera sync.
 */
export function DeckGLOverlayCanvas({
  events,
  flights,
  vessels,
  activeLayers,
}: DeckGLOverlayProps) {
  const layers = useDeckGLLayers({ events, flights, vessels, activeLayers });

  if (layers.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-10">
      {/* deck.gl overlay renders here when camera sync is established */}
      <div className="absolute top-2 right-2 text-[9px] text-gray-400 bg-slate-800/80 px-2 py-1 rounded">
        deck.gl layers: {layers.length}
      </div>
    </div>
  );
}
