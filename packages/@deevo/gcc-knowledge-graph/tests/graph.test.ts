/**
 * @deevo/gcc-knowledge-graph — Test Suite
 *
 * Validates graph integrity, node/edge counts, scenario completeness,
 * Zod schema validation, GCCGraph class operations, and data contracts.
 */

import {
  gccNodes,
  gccEdges,
  gccScenarios,
  GCCGraph,
  getDefaultGraph,
  getNode,
  getEdge,
  getAnimatedEdges,
  getScenario,
  getScenariosByGroup,
  NODE_COUNTS,
  LAYER_META,
  SCENARIO_GROUPS,
  validateNode,
  validateEdge,
  validateScenario,
  validateGraphIntegrity,
  validateScenarioIntegrity,
} from '../src';

// ═══════════════════════════════════════════════
// DATA INTEGRITY
// ═══════════════════════════════════════════════
describe('Data Integrity', () => {
  test('has exactly 76 nodes', () => {
    expect(gccNodes.length).toBe(76);
    expect(NODE_COUNTS.total).toBe(76);
  });

  test('node layer counts match expected distribution', () => {
    expect(NODE_COUNTS.geography).toBe(7);
    expect(NODE_COUNTS.infrastructure).toBe(22);
    expect(NODE_COUNTS.economy).toBe(21);
    expect(NODE_COUNTS.finance).toBe(12);
    expect(NODE_COUNTS.society).toBe(14);
  });

  test('has 191 edges', () => {
    // Edge IDs range from e01 to e191 (with gaps)
    expect(gccEdges.length).toBeGreaterThanOrEqual(150);
    // Exact count from source
    const uniqueIds = new Set(gccEdges.map(e => e.id));
    expect(uniqueIds.size).toBe(gccEdges.length); // no duplicate IDs
  });

  test('has exactly 17 scenarios', () => {
    expect(gccScenarios.length).toBe(17);
  });

  test('all node IDs are unique', () => {
    const ids = gccNodes.map(n => n.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('all edge IDs are unique', () => {
    const ids = gccEdges.map(e => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('all scenario IDs are unique', () => {
    const ids = gccScenarios.map(s => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test('all edge sources reference existing nodes', () => {
    const nodeIds = new Set(gccNodes.map(n => n.id));
    for (const edge of gccEdges) {
      expect(nodeIds.has(edge.source)).toBe(true);
    }
  });

  test('all edge targets reference existing nodes', () => {
    const nodeIds = new Set(gccNodes.map(n => n.id));
    for (const edge of gccEdges) {
      expect(nodeIds.has(edge.target)).toBe(true);
    }
  });

  test('no self-loops in edges', () => {
    for (const edge of gccEdges) {
      expect(edge.source).not.toBe(edge.target);
    }
  });

  test('validateGraphIntegrity passes', () => {
    const result = validateGraphIntegrity([...gccNodes], [...gccEdges]);
    expect(result.valid).toBe(true);
    expect(result.orphanedEdges).toHaveLength(0);
  });
});

// ═══════════════════════════════════════════════
// NODE PROPERTIES
// ═══════════════════════════════════════════════
describe('Node Properties', () => {
  test('all nodes have valid weight range [0, 1]', () => {
    for (const n of gccNodes) {
      expect(n.weight).toBeGreaterThanOrEqual(0);
      expect(n.weight).toBeLessThanOrEqual(1);
    }
  });

  test('all nodes have valid sensitivity range [0, 1]', () => {
    for (const n of gccNodes) {
      expect(n.sensitivity).toBeGreaterThanOrEqual(0);
      expect(n.sensitivity).toBeLessThanOrEqual(1);
    }
  });

  test('all nodes have valid damping_factor range [0, 1]', () => {
    for (const n of gccNodes) {
      expect(n.damping_factor).toBeGreaterThanOrEqual(0);
      expect(n.damping_factor).toBeLessThanOrEqual(1);
    }
  });

  test('all nodes have valid coordinates', () => {
    for (const n of gccNodes) {
      expect(n.lat).toBeGreaterThanOrEqual(-90);
      expect(n.lat).toBeLessThanOrEqual(90);
      expect(n.lng).toBeGreaterThanOrEqual(-180);
      expect(n.lng).toBeLessThanOrEqual(180);
    }
  });

  test('all nodes have bilingual labels', () => {
    for (const n of gccNodes) {
      expect(n.label.length).toBeGreaterThan(0);
      expect(n.labelAr.length).toBeGreaterThan(0);
    }
  });

  test('Strait of Hormuz has highest weight', () => {
    const hormuz = getNode('geo_hormuz');
    expect(hormuz).toBeDefined();
    expect(hormuz!.weight).toBe(0.98);
  });

  test('Oil Export has high sensitivity', () => {
    const oil = getNode('eco_oil');
    expect(oil).toBeDefined();
    expect(oil!.sensitivity).toBe(0.7);
  });
});

// ═══════════════════════════════════════════════
// EDGE PROPERTIES
// ═══════════════════════════════════════════════
describe('Edge Properties', () => {
  test('all edges have valid weight range [0, 1]', () => {
    for (const e of gccEdges) {
      expect(e.weight).toBeGreaterThanOrEqual(0);
      expect(e.weight).toBeLessThanOrEqual(1);
    }
  });

  test('all edges have valid polarity (1 or -1)', () => {
    for (const e of gccEdges) {
      expect([1, -1]).toContain(e.polarity);
    }
  });

  test('all edges have bilingual labels', () => {
    for (const e of gccEdges) {
      expect(e.label.length).toBeGreaterThan(0);
      expect(e.labelAr.length).toBeGreaterThan(0);
    }
  });

  test('Hormuz → Oil edge has weight 0.95', () => {
    const e = getEdge('e01');
    expect(e).toBeDefined();
    expect(e!.source).toBe('geo_hormuz');
    expect(e!.target).toBe('eco_oil');
    expect(e!.weight).toBe(0.95);
    expect(e!.polarity).toBe(-1);
  });

  test('animated edges exist (critical cascade paths)', () => {
    const animated = getAnimatedEdges();
    expect(animated.length).toBeGreaterThan(10);
    // e01 (Hormuz→Oil) should be animated
    expect(animated.find(e => e.id === 'e01')).toBeDefined();
  });
});

// ═══════════════════════════════════════════════
// SCENARIO PROPERTIES
// ═══════════════════════════════════════════════
describe('Scenario Properties', () => {
  test('all scenarios have bilingual content', () => {
    for (const s of gccScenarios) {
      expect(s.title.length).toBeGreaterThan(0);
      expect(s.titleAr.length).toBeGreaterThan(0);
      expect(s.description.length).toBeGreaterThan(0);
      expect(s.descriptionAr.length).toBeGreaterThan(0);
      expect(s.thesis.length).toBeGreaterThan(0);
      expect(s.thesisAr.length).toBeGreaterThan(0);
    }
  });

  test('all scenarios have at least one shock', () => {
    for (const s of gccScenarios) {
      expect(s.shocks.length).toBeGreaterThan(0);
    }
  });

  test('all scenario shock targets reference existing nodes', () => {
    const nodeIds = new Set(gccNodes.map(n => n.id));
    for (const s of gccScenarios) {
      const result = validateScenarioIntegrity(s, nodeIds);
      expect(result.valid).toBe(true);
    }
  });

  test('scenario groups cover all 6 categories', () => {
    const groups = new Set(gccScenarios.map(s => s.group));
    expect(groups.size).toBe(6);
    expect(groups.has('geopolitics')).toBe(true);
    expect(groups.has('aviation')).toBe(true);
    expect(groups.has('ports_supply')).toBe(true);
    expect(groups.has('finance_markets')).toBe(true);
    expect(groups.has('utilities_state')).toBe(true);
    expect(groups.has('sovereign_projects')).toBe(true);
  });

  test('hormuz_closure scenario has correct shock', () => {
    const s = getScenario('hormuz_closure');
    expect(s).toBeDefined();
    expect(s!.shocks).toEqual([{ nodeId: 'geo_hormuz', impact: 0.90 }]);
    expect(s!.severityDefault).toBe(0.90);
    expect(s!.simulationType).toBe('deterministic');
  });

  test('getScenariosByGroup returns correct counts', () => {
    expect(getScenariosByGroup('geopolitics').length).toBe(3);
    expect(getScenariosByGroup('aviation').length).toBe(3);
    expect(getScenariosByGroup('ports_supply').length).toBe(3);
    expect(getScenariosByGroup('finance_markets').length).toBe(3);
    expect(getScenariosByGroup('utilities_state').length).toBe(3);
    expect(getScenariosByGroup('sovereign_projects').length).toBe(2);
  });

  test('all severity defaults are in [0, 1]', () => {
    for (const s of gccScenarios) {
      expect(s.severityDefault).toBeGreaterThanOrEqual(0);
      expect(s.severityDefault).toBeLessThanOrEqual(1);
    }
  });
});

// ═══════════════════════════════════════════════
// ZOD VALIDATION
// ═══════════════════════════════════════════════
describe('Zod Schema Validation', () => {
  test('all nodes pass Zod validation', () => {
    for (const n of gccNodes) {
      const result = validateNode(n);
      expect(result.success).toBe(true);
    }
  });

  test('all edges pass Zod validation', () => {
    for (const e of gccEdges) {
      const result = validateEdge(e);
      expect(result.success).toBe(true);
    }
  });

  test('all scenarios pass Zod validation', () => {
    for (const s of gccScenarios) {
      const result = validateScenario(s);
      expect(result.success).toBe(true);
    }
  });

  test('invalid node fails Zod validation', () => {
    const bad = { id: '', label: 'test', weight: 2.0 };
    const result = validateNode(bad);
    expect(result.success).toBe(false);
  });

  test('invalid edge fails Zod validation', () => {
    const bad = { id: 'x', source: 'a', target: 'b', weight: -0.5, polarity: 0 };
    const result = validateEdge(bad);
    expect(result.success).toBe(false);
  });
});

// ═══════════════════════════════════════════════
// GCCGraph CLASS
// ═══════════════════════════════════════════════
describe('GCCGraph Class', () => {
  let graph: GCCGraph;

  beforeAll(() => {
    graph = getDefaultGraph();
  });

  test('nodeCount matches data', () => {
    expect(graph.nodeCount).toBe(76);
  });

  test('edgeCount matches data', () => {
    expect(graph.edgeCount).toBe(gccEdges.length);
  });

  test('getNode returns correct node', () => {
    const n = graph.getNode('inf_dxb');
    expect(n).toBeDefined();
    expect(n!.label).toBe('DXB Airport');
    expect(n!.layer).toBe('infrastructure');
  });

  test('getNodeOrThrow throws for missing ID', () => {
    expect(() => graph.getNodeOrThrow('nonexistent')).toThrow('Node not found');
  });

  test('hasNode works correctly', () => {
    expect(graph.hasNode('geo_hormuz')).toBe(true);
    expect(graph.hasNode('fake_node')).toBe(false);
  });

  test('getNodesByLayer returns correct layer', () => {
    const geoNodes = graph.getNodesByLayer('geography');
    expect(geoNodes.length).toBe(7);
    for (const n of geoNodes) {
      expect(n.layer).toBe('geography');
    }
  });

  test('getOutEdges returns outgoing edges', () => {
    const outEdges = graph.getOutEdges('geo_hormuz');
    expect(outEdges.length).toBeGreaterThan(0);
    for (const e of outEdges) {
      expect(e.source).toBe('geo_hormuz');
    }
  });

  test('getInEdges returns incoming edges', () => {
    const inEdges = graph.getInEdges('eco_oil');
    expect(inEdges.length).toBeGreaterThan(0);
    for (const e of inEdges) {
      expect(e.target).toBe('eco_oil');
    }
  });

  test('getNeighbors returns connected nodes', () => {
    const neighbors = graph.getNeighbors('eco_oil');
    expect(neighbors.length).toBeGreaterThan(3);
    // Hormuz should be a neighbor (incoming)
    expect(neighbors.find(n => n.id === 'geo_hormuz')).toBeDefined();
    // Aramco should be a neighbor (outgoing)
    expect(neighbors.find(n => n.id === 'eco_aramco')).toBeDefined();
  });

  test('shortestPath from Hormuz to GDP', () => {
    const dist = graph.shortestPath('geo_hormuz', 'eco_gdp');
    expect(dist).toBeGreaterThan(0);
    expect(dist).toBeLessThanOrEqual(4); // should be reachable in ≤4 hops
  });

  test('shortestPath returns 0 for same node', () => {
    expect(graph.shortestPath('eco_oil', 'eco_oil')).toBe(0);
  });

  test('reachableNodes from Hormuz within 2 hops', () => {
    const reachable = graph.reachableNodes('geo_hormuz', 2);
    expect(reachable.size).toBeGreaterThan(3);
    expect(reachable.get('geo_hormuz')).toBe(0);
    expect(reachable.has('eco_oil')).toBe(true); // 1 hop
  });

  test('inDegreeMap is populated', () => {
    const degrees = graph.inDegreeMap();
    expect(degrees.size).toBe(76);
    // eco_gdp should have high in-degree (many things feed GDP)
    expect(degrees.get('eco_gdp')!).toBeGreaterThan(5);
  });

  test('outDegreeMap is populated', () => {
    const degrees = graph.outDegreeMap();
    expect(degrees.size).toBe(76);
    // eco_oil should have high out-degree
    expect(degrees.get('eco_oil')!).toBeGreaterThan(3);
  });

  test('validateShocks identifies missing nodes', () => {
    const result = graph.validateShocks([
      { nodeId: 'geo_hormuz', impact: 0.9 },
      { nodeId: 'fake_node', impact: 0.5 },
    ]);
    expect(result.valid).toBe(false);
    expect(result.missing).toContain('fake_node');
  });

  test('validateShocks passes for valid scenario', () => {
    const hormuz = getScenario('hormuz_closure')!;
    const result = graph.validateShocks(hormuz.shocks);
    expect(result.valid).toBe(true);
  });

  test('scenarioSubgraph returns affected nodes and edges', () => {
    const hormuz = getScenario('hormuz_closure')!;
    const sub = graph.scenarioSubgraph(hormuz, 2);
    expect(sub.nodes.length).toBeGreaterThan(5);
    expect(sub.edges.length).toBeGreaterThan(3);
    expect(sub.shockNodeIds.has('geo_hormuz')).toBe(true);
  });

  test('toJSON returns serializable output', () => {
    const json = graph.toJSON();
    expect(json.nodes.length).toBe(76);
    expect(json.edges.length).toBe(gccEdges.length);
    expect(json.meta.nodeCount).toBe(76);
  });
});

// ═══════════════════════════════════════════════
// LAYER METADATA
// ═══════════════════════════════════════════════
describe('Layer & Group Metadata', () => {
  test('LAYER_META has all 5 layers', () => {
    expect(Object.keys(LAYER_META)).toHaveLength(5);
    expect(LAYER_META.geography.color).toBe('#2DD4A0');
    expect(LAYER_META.finance.color).toBe('#A78BFA');
  });

  test('SCENARIO_GROUPS has all 6 groups', () => {
    expect(Object.keys(SCENARIO_GROUPS)).toHaveLength(6);
  });

  test('layer metadata has bilingual labels', () => {
    for (const meta of Object.values(LAYER_META)) {
      expect(meta.label.length).toBeGreaterThan(0);
      expect(meta.labelAr.length).toBeGreaterThan(0);
    }
  });
});

// ═══════════════════════════════════════════════
// CRITICAL CASCADE PATHS
// ═══════════════════════════════════════════════
describe('Critical Cascade Paths', () => {
  let graph: GCCGraph;

  beforeAll(() => {
    graph = getDefaultGraph();
  });

  test('Hormuz → Oil → Shipping → Insurance cascade exists', () => {
    // e01: Hormuz → Oil
    const e01 = graph.getEdge('e01');
    expect(e01?.source).toBe('geo_hormuz');
    expect(e01?.target).toBe('eco_oil');

    // e05: Oil → Shipping
    const e05 = graph.getEdge('e05');
    expect(e05?.source).toBe('eco_oil');
    expect(e05?.target).toBe('eco_shipping');

    // e10: Shipping → Insurance Risk
    const e10 = graph.getEdge('e10');
    expect(e10?.source).toBe('eco_shipping');
    expect(e10?.target).toBe('fin_ins_risk');
  });

  test('Fuel → Aviation → Ticket → Travel Demand cascade exists', () => {
    const e14 = graph.getEdge('e14');
    expect(e14?.source).toBe('eco_fuel');
    expect(e14?.target).toBe('eco_aviation');

    const e15 = graph.getEdge('e15');
    expect(e15?.source).toBe('eco_aviation');
    expect(e15?.target).toBe('soc_ticket');

    const e150 = graph.getEdge('e150');
    expect(e150?.source).toBe('soc_ticket');
    expect(e150?.target).toBe('soc_travel_d');
    expect(e150?.polarity).toBe(-1); // negative feedback
  });

  test('Power → Desalination → Citizens cascade exists', () => {
    const e61 = graph.getEdge('e61');
    expect(e61?.source).toBe('inf_power');
    expect(e61?.target).toBe('inf_desal');

    const e62 = graph.getEdge('e62');
    expect(e62?.source).toBe('inf_desal');
    expect(e62?.target).toBe('soc_citizens');
  });

  test('Food Security chain: Shipping → Food → Citizens', () => {
    const e122 = graph.getEdge('e122');
    expect(e122?.source).toBe('eco_shipping');
    expect(e122?.target).toBe('eco_food');

    const e126 = graph.getEdge('e126');
    expect(e126?.source).toBe('eco_food');
    expect(e126?.target).toBe('soc_citizens');
  });
});

// ═══════════════════════════════════════════════
// GCC-SPECIFIC VALIDATIONS
// ═══════════════════════════════════════════════
describe('GCC-Specific Validations', () => {
  test('all 6 GCC countries present', () => {
    const countries = ['geo_sa', 'geo_uae', 'geo_kw', 'geo_qa', 'geo_om', 'geo_bh'];
    for (const id of countries) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('all 9 airports present', () => {
    const airports = ['inf_ruh', 'inf_jed', 'inf_dmm', 'inf_dxb', 'inf_auh', 'inf_doh', 'inf_kwi', 'inf_bah', 'inf_mct'];
    for (const id of airports) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('all 7 ports present', () => {
    const ports = ['inf_jebel', 'inf_dammam', 'inf_doha_p', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'inf_sohar'];
    for (const id of ports) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('all 6 central banks present', () => {
    const cbs = ['fin_sama', 'fin_uae_cb', 'fin_kw_cb', 'fin_qa_cb', 'fin_om_cb', 'fin_bh_cb'];
    for (const id of cbs) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('all 6 airlines present', () => {
    const airlines = ['eco_saudia', 'eco_emirates', 'eco_qatar_aw', 'eco_kw_airways', 'eco_gulf_air', 'eco_oman_air'];
    for (const id of airlines) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('all 5 ministries present', () => {
    const ministries = ['gov_energy', 'gov_tourism', 'gov_transport', 'gov_water', 'gov_finance'];
    for (const id of ministries) {
      expect(getNode(id)).toBeDefined();
    }
  });

  test('Jebel Ali has highest port weight', () => {
    const ports = ['inf_jebel', 'inf_dammam', 'inf_doha_p', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'inf_sohar'];
    const weights = ports.map(id => getNode(id)!.weight);
    const maxWeight = Math.max(...weights);
    expect(getNode('inf_jebel')!.weight).toBe(maxWeight);
  });

  test('DXB has highest airport weight', () => {
    const airports = ['inf_ruh', 'inf_jed', 'inf_dmm', 'inf_dxb', 'inf_auh', 'inf_doh', 'inf_kwi', 'inf_bah', 'inf_mct'];
    const weights = airports.map(id => getNode(id)!.weight);
    const maxWeight = Math.max(...weights);
    expect(getNode('inf_dxb')!.weight).toBe(maxWeight);
  });
});
