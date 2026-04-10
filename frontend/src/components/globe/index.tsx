"use client";

import dynamic from "next/dynamic";
import type { Flight, Vessel, Event } from "@/types";

/**
 * Dynamic import wrapper for CesiumGlobe.
 * Cesium requires `window` and cannot be server-side rendered.
 */
const CesiumGlobeDynamic = dynamic(
  () => import("./cesium-globe").then((mod) => ({ default: mod.CesiumGlobe })),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-io-primary">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-io-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-io-border">Initializing Globe...</p>
        </div>
      </div>
    ),
  }
);

interface GlobeWrapperProps {
  flights: Flight[];
  vessels: Vessel[];
  events: Event[];
  selectedEntityId: string | null;
  onEntityClick: (entityId: string, entityType: string) => void;
  activeLayers: Set<string>;
  cameraTarget?: { lat: number; lng: number; altitude: number };
}

export function GlobeWrapper(props: GlobeWrapperProps) {
  const hasCesiumToken = !!process.env.NEXT_PUBLIC_CESIUM_TOKEN;

  if (!hasCesiumToken) {
    return (
      <div className="flex-1 flex items-center justify-center bg-io-primary">
        <div className="text-center text-io-border">
          <div className="text-6xl mb-4">🌐</div>
          <p className="text-sm">
            CesiumJS Globe — awaiting token configuration
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Set NEXT_PUBLIC_CESIUM_TOKEN in .env to enable 3D globe
          </p>
          <div className="mt-6 grid grid-cols-3 gap-3 text-[10px] max-w-xs mx-auto">
            <Stat label="Flights" value={props.flights.length} />
            <Stat label="Vessels" value={props.vessels.length} />
            <Stat label="Events" value={props.events.length} />
          </div>
        </div>
      </div>
    );
  }

  return <CesiumGlobeDynamic {...props} />;
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded p-2 text-center">
      <div className="text-lg font-bold text-io-accent">{value}</div>
      <div className="text-gray-400">{label}</div>
    </div>
  );
}
