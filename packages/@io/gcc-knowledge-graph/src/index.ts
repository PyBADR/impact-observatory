/**
 * @io/gcc-knowledge-graph
 *
 * GCC Reality Graph — 5-Layer Causal Dependency Model v5.0
 * Server-side canonical source for all GCC knowledge graph data.
 *
 * 76 nodes · 191 edges · 17 scenarios · 5 layers · 6 scenario groups
 */

// Types
export type {
  GCCLayer,
  GCCNode,
  GCCEdge,
  GCCScenario,
  ScenarioShock,
  ScenarioGroup,
  ScenarioGroupMeta,
  SimulationType,
  LayerMeta,
} from './types';

// Node registry
export {
  gccNodes,
  getNode,
  getNodesByLayer,
  NODE_COUNTS,
  GEOGRAPHY_NODES,
  INFRASTRUCTURE_NODES,
  ECONOMY_NODES,
  FINANCE_NODES,
  SOCIETY_NODES,
} from './nodes';

// Edge registry
export {
  gccEdges,
  getEdge,
  getOutEdges,
  getInEdges,
  getAnimatedEdges,
} from './edges';

// Scenario registry
export {
  gccScenarios,
  getScenario,
  getScenariosByGroup,
  SCENARIO_GROUPS,
} from './scenarios';

// Graph class
export {
  GCCGraph,
  getDefaultGraph,
  LAYER_META,
} from './graph';

// Validation
export {
  GCCNodeSchema,
  GCCEdgeSchema,
  GCCScenarioSchema,
  ScenarioShockSchema,
  GCCLayerSchema,
  SimulationTypeSchema,
  ScenarioGroupSchema,
  validateNode,
  validateEdge,
  validateScenario,
  validateGraphIntegrity,
  validateScenarioIntegrity,
} from './validation';
