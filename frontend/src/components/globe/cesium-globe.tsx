"use client";

import { useEffect, useRef, useCallback } from "react";
import {
  Viewer,
  CameraFlyTo,
  Globe as CesiumGlobeComponent,
  Scene,
} from "resium";
import {
  Ion,
  Cartesian3,
  Color,
  createWorldTerrainAsync,
  createOsmBuildingsAsync,
  Cesium3DTileset,
  Math as CesiumMath,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  defined,
  Viewer as CesiumViewer,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

import { FlightLayer } from "./flight-layer";
import { VesselLayer } from "./vessel-layer";
import { ConflictLayer } from "./conflict-layer";
import type { Flight, Vessel, Event } from "@/types";

interface CesiumGlobeProps {
  flights: Flight[];
  vessels: Vessel[];
  events: Event[];
  selectedEntityId: string | null;
  onEntityClick: (entityId: string, entityType: string) => void;
  activeLayers: Set<string>;
  cameraTarget?: { lat: number; lng: number; altitude: number };
}

// Set Cesium ion token
const CESIUM_TOKEN = process.env.NEXT_PUBLIC_CESIUM_TOKEN || "";
if (CESIUM_TOKEN) {
  Ion.defaultAccessToken = CESIUM_TOKEN;
}

export function CesiumGlobe({
  flights,
  vessels,
  events,
  selectedEntityId,
  onEntityClick,
  activeLayers,
  cameraTarget,
}: CesiumGlobeProps) {
  const viewerRef = useRef<{ cesiumElement?: CesiumViewer }>(null);
  const buildingsRef = useRef<Cesium3DTileset | null>(null);

  // Load terrain and buildings on mount
  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;
    if (!viewer) return;

    // Configure scene
    viewer.scene.globe.enableLighting = true;
    viewer.scene.fog.enabled = true;
    if (viewer.scene.skyAtmosphere) {
      viewer.scene.skyAtmosphere.show = true;
    }

    // Remove default imagery credit
    viewer.cesiumWidget.creditContainer.setAttribute("style", "display: none;");

    // Load world terrain
    if (CESIUM_TOKEN) {
      createWorldTerrainAsync().then((terrain) => {
        if (!viewer.isDestroyed()) {
          viewer.terrainProvider = terrain;
        }
      }).catch(() => {
        // Terrain loading failed — continue without terrain
      });

      // Load OSM buildings
      createOsmBuildingsAsync().then((buildings) => {
        if (!viewer.isDestroyed()) {
          buildingsRef.current = buildings;
          viewer.scene.primitives.add(buildings);
        }
      }).catch(() => {
        // OSM buildings loading failed — continue without buildings
      });
    }

    return () => {
      if (buildingsRef.current && !viewer.isDestroyed()) {
        viewer.scene.primitives.remove(buildingsRef.current);
        buildingsRef.current = null;
      }
    };
  }, []);

  // Handle click events
  useEffect(() => {
    const viewer = viewerRef.current?.cesiumElement;
    if (!viewer) return;

    const handler = new ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction(
      (click: { position: { x: number; y: number } }) => {
        const picked = viewer.scene.pick(click.position as unknown as import("cesium").Cartesian2);
        if (defined(picked) && picked.id) {
          const entity = picked.id;
          const entityId = entity.id || entity.name;
          const entityType = entity.properties?.entityType?.getValue?.(viewer.clock.currentTime) || "unknown";
          if (entityId) {
            onEntityClick(entityId, entityType);
          }
        }
      },
      ScreenSpaceEventType.LEFT_CLICK
    );

    return () => {
      handler.destroy();
    };
  }, [onEntityClick]);

  const defaultCamera = {
    destination: Cartesian3.fromDegrees(52, 25, 3_000_000),
    orientation: {
      heading: CesiumMath.toRadians(0),
      pitch: CesiumMath.toRadians(-60),
      roll: 0,
    },
  };

  return (
    <Viewer
      ref={viewerRef as any}
      full
      timeline={false}
      animation={false}
      homeButton={false}
      sceneModePicker={false}
      baseLayerPicker={false}
      navigationHelpButton={false}
      fullscreenButton={false}
      geocoder={false}
      infoBox={false}
      selectionIndicator={false}
      className="w-full h-full"
      scene3DOnly
    >
      <Scene backgroundColor={Color.fromCssColorString("#0f172a")} />
      <CesiumGlobeComponent
        enableLighting
        showGroundAtmosphere
        baseColor={Color.fromCssColorString("#0f172a")}
      />

      {/* Camera fly-to when target changes */}
      {cameraTarget && (
        <CameraFlyTo
          destination={Cartesian3.fromDegrees(
            cameraTarget.lng,
            cameraTarget.lat,
            cameraTarget.altitude
          )}
          duration={2}
        />
      )}

      {/* Flight arcs */}
      {activeLayers.has("flights") && (
        <FlightLayer flights={flights} selectedId={selectedEntityId} />
      )}

      {/* Vessel positions */}
      {activeLayers.has("vessels") && (
        <VesselLayer vessels={vessels} selectedId={selectedEntityId} />
      )}

      {/* Conflict zones */}
      {activeLayers.has("events") && (
        <ConflictLayer events={events} />
      )}
    </Viewer>
  );
}
