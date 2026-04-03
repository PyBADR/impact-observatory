/**
 * @io/gcc-knowledge-graph — Zod Validation Schemas
 *
 * Runtime validation for nodes, edges, scenarios, and shock vectors.
 * Used for API input validation and data contract enforcement.
 */

import { z } from 'zod';

// ─── Layer ───────────────────────────────────────
export const GCCLayerSchema = z.enum([
  'geography',
  'infrastructure',
  'economy',
  'finance',
  'society',
]);

export const SimulationTypeSchema = z.enum([
  'deterministic',
  'probabilistic',
  'hybrid',
]);

export const ScenarioGroupSchema = z.enum([
  'geopolitics',
  'aviation',
  'ports_supply',
  'finance_markets',
  'utilities_state',
  'sovereign_projects',
]);

// ─── Node ────────────────────────────────────────
export const GCCNodeSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  labelAr: z.string().min(1),
  layer: GCCLayerSchema,
  type: z.string().min(1),
  weight: z.number().min(0).max(1),
  sensitivity: z.number().min(0).max(1),
  damping_factor: z.number().min(0).max(1),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  value: z.number().min(0).max(1),
});

// ─── Edge ────────────────────────────────────────
export const GCCEdgeSchema = z.object({
  id: z.string().min(1),
  source: z.string().min(1),
  target: z.string().min(1),
  weight: z.number().min(0).max(1),
  polarity: z.union([z.literal(1), z.literal(-1)]),
  label: z.string().min(1),
  labelAr: z.string().min(1),
  animated: z.boolean().optional(),
});

// ─── Shock ───────────────────────────────────────
export const ScenarioShockSchema = z.object({
  nodeId: z.string().min(1),
  impact: z.number().min(-1).max(1),
});

// ─── Scenario ────────────────────────────────────
export const GCCScenarioSchema = z.object({
  id: z.string().min(1),
  engineId: z.string().min(1),
  title: z.string().min(1),
  titleAr: z.string().min(1),
  description: z.string().min(1),
  descriptionAr: z.string().min(1),
  category: z.string().min(1),
  country: z.string().min(1),
  group: ScenarioGroupSchema,
  thesis: z.string().min(1),
  thesisAr: z.string().min(1),
  sectors: z.array(z.string()),
  keyEntities: z.array(z.string()),
  mapModes: z.array(z.string()),
  formulaTags: z.array(z.string()),
  severityDefault: z.number().min(0).max(1),
  timeHorizon: z.string().min(1),
  timeHorizonAr: z.string().min(1),
  expectedPropagationDomains: z.array(z.string()),
  simulationType: SimulationTypeSchema,
  chokePoints: z.array(z.string()),
  geospatialAnchors: z.array(z.string()),
  shocks: z.array(ScenarioShockSchema).min(1),
});

// ─── Validation Helpers ──────────────────────────
import { GCCNode, GCCEdge, GCCScenario } from './types';

export function validateNode(node: unknown): z.SafeParseReturnType<unknown, GCCNode> {
  return GCCNodeSchema.safeParse(node) as z.SafeParseReturnType<unknown, GCCNode>;
}

export function validateEdge(edge: unknown): z.SafeParseReturnType<unknown, GCCEdge> {
  return GCCEdgeSchema.safeParse(edge) as z.SafeParseReturnType<unknown, GCCEdge>;
}

export function validateScenario(scenario: unknown): z.SafeParseReturnType<unknown, GCCScenario> {
  return GCCScenarioSchema.safeParse(scenario) as z.SafeParseReturnType<unknown, GCCScenario>;
}

/**
 * Validate referential integrity: all edge sources and targets
 * must reference existing node IDs.
 */
export function validateGraphIntegrity(
  nodes: GCCNode[],
  edges: GCCEdge[],
): { valid: boolean; orphanedEdges: string[] } {
  const nodeIds = new Set(nodes.map(n => n.id));
  const orphanedEdges = edges
    .filter(e => !nodeIds.has(e.source) || !nodeIds.has(e.target))
    .map(e => `${e.id}: ${e.source} → ${e.target}`);

  return { valid: orphanedEdges.length === 0, orphanedEdges };
}

/**
 * Validate that all scenario shock targets and key entities
 * reference existing node IDs.
 */
export function validateScenarioIntegrity(
  scenario: GCCScenario,
  nodeIds: Set<string>,
): { valid: boolean; missingNodes: string[] } {
  const referenced = [
    ...scenario.shocks.map(s => s.nodeId),
    ...scenario.keyEntities,
    ...scenario.chokePoints,
    ...scenario.geospatialAnchors,
  ];

  const missingNodes = [...new Set(referenced.filter(id => !nodeIds.has(id)))];
  return { valid: missingNodes.length === 0, missingNodes };
}
