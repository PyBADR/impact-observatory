/**
 * @io/gcc-knowledge-graph — Type Definitions
 *
 * GCC Reality Graph: 5-Layer Causal Dependency Model v5.0
 * Extracted from frontend/lib/gcc-graph.ts — server-side canonical source.
 *
 * Layer 1: Geography     (6 countries + chokepoints)
 * Layer 2: Infrastructure (airports, ports, utilities, telecom, ministries)
 * Layer 3: Economy       (oil, logistics, aviation, food, tourism, telecom)
 * Layer 4: Finance       (central banks, commercial banks, insurance, markets)
 * Layer 5: Society       (citizens, expats, travelers, Hajj, media)
 */

// ─── Layer Taxonomy ──────────────────────────────────────────
export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society';

export type ScenarioGroup =
  | 'geopolitics'
  | 'aviation'
  | 'ports_supply'
  | 'finance_markets'
  | 'utilities_state'
  | 'sovereign_projects';

export type SimulationType = 'deterministic' | 'probabilistic' | 'hybrid';

// ─── Node ────────────────────────────────────────────────────
export interface GCCNode {
  /** Unique node identifier (e.g. 'geo_hormuz', 'inf_dxb') */
  id: string;
  /** English display label */
  label: string;
  /** Arabic display label */
  labelAr: string;
  /** Layer membership */
  layer: GCCLayer;
  /** Entity type: Region, Organization, Topic, Event, Person, Ministry, Platform */
  type: string;
  /** Baseline importance 0–1 */
  weight: number;
  /** Reactivity to incoming shocks 0–1 */
  sensitivity: number;
  /** Rate of self-decay per propagation iteration 0–1 */
  damping_factor: number;
  /** Latitude (WGS84) */
  lat: number;
  /** Longitude (WGS84) */
  lng: number;
  /** Base economic/strategic value (normalized 0–1) */
  value: number;
}

// ─── Edge ────────────────────────────────────────────────────
export interface GCCEdge {
  /** Unique edge identifier (e.g. 'e01') */
  id: string;
  /** Source node ID */
  source: string;
  /** Target node ID */
  target: string;
  /** Causal strength 0–1 */
  weight: number;
  /** +1 = amplifying, -1 = dampening */
  polarity: 1 | -1;
  /** English label */
  label: string;
  /** Arabic label */
  labelAr: string;
  /** UI animation hint for critical cascade paths */
  animated?: boolean;
}

// ─── Shock ───────────────────────────────────────────────────
export interface ScenarioShock {
  /** Target node ID */
  nodeId: string;
  /** Impact magnitude (positive = stress increase, negative = capacity decrease) */
  impact: number;
}

// ─── Scenario ────────────────────────────────────────────────
export interface GCCScenario {
  /** Unique scenario identifier */
  id: string;
  /** Engine implementation reference */
  engineId: string;
  /** English title */
  title: string;
  /** Arabic title */
  titleAr: string;
  /** English description */
  description: string;
  /** Arabic description */
  descriptionAr: string;
  /** Scenario category tag */
  category: string;
  /** Country scope */
  country: string;
  /** Scenario group */
  group: ScenarioGroup;
  /** Strategic thesis (English) */
  thesis: string;
  /** Strategic thesis (Arabic) */
  thesisAr: string;
  /** Affected sector labels */
  sectors: string[];
  /** Key entity node IDs */
  keyEntities: string[];
  /** Map visualization modes */
  mapModes: string[];
  /** Associated formula tags */
  formulaTags: string[];
  /** Default severity 0–1 */
  severityDefault: number;
  /** Time horizon label (English) */
  timeHorizon: string;
  /** Time horizon label (Arabic) */
  timeHorizonAr: string;
  /** Expected propagation domain layers */
  expectedPropagationDomains: string[];
  /** Simulation methodology */
  simulationType: SimulationType;
  /** Chokepoint node IDs */
  chokePoints: string[];
  /** Geospatial anchor node IDs */
  geospatialAnchors: string[];
  /** Initial shock vector */
  shocks: ScenarioShock[];
}

// ─── Scenario Group Metadata ─────────────────────────────────
export interface ScenarioGroupMeta {
  label: string;
  labelAr: string;
  icon: string;
}

// ─── Layer Metadata ──────────────────────────────────────────
export interface LayerMeta {
  label: string;
  labelAr: string;
  color: string;
  yBase: number;
}
