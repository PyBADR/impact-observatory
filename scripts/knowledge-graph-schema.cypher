// ═══════════════════════════════════════════════════════════════════════════
// Impact Observatory | مرصد الأثر — Macro Intelligence Knowledge Graph
// Production Neo4j Schema — DDL, Constraints, Indexes, Seed Data
// ═══════════════════════════════════════════════════════════════════════════
//
// Layer:     Data (L1) + Governance (L7)
// Version:   1.0.0
// Domains:   Insurance · Technical/Observability · Intelligence/Event
// Alignment: graph_brain/types.py (13 entity types, 17 relation types)
//            simulation_engine.py (42 GCC nodes, 9 sectors)
//            propagation_schemas.py (NodeState, PropagationEdge)
//            decision_brain/ (action synthesis, reasoning chains)
//            signal_intel/ (feed ingestion, dedup, routing)
//
// Naming Conventions:
//   Nodes:   PascalCase labels        (Customer, Policy, Deployment)
//   Rels:    UPPER_SNAKE_CASE types   (OWNS_POLICY, TRIGGERS)
//   Props:   snake_case properties    (created_at, loss_usd)
//   IDs:     {domain}_{entity}_{uuid} (ins_cust_a1b2c3)
// ═══════════════════════════════════════════════════════════════════════════

// ─── SECTION 1: CLEANUP (idempotent re-run) ─────────────────────────────

// Drop existing constraints if re-initializing (comment out in production)
// CALL apoc.schema.assert({}, {}, true) YIELD label RETURN label;

// ─── SECTION 2: NODE CONSTRAINTS (unique identifiers) ───────────────────

// ── Insurance Domain ──
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
  FOR (n:Customer) REQUIRE n.customer_id IS UNIQUE;

CREATE CONSTRAINT policy_id_unique IF NOT EXISTS
  FOR (n:Policy) REQUIRE n.policy_id IS UNIQUE;

CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
  FOR (n:Claim) REQUIRE n.claim_id IS UNIQUE;

CREATE CONSTRAINT coverage_id_unique IF NOT EXISTS
  FOR (n:Coverage) REQUIRE n.coverage_id IS UNIQUE;

CREATE CONSTRAINT risk_profile_id_unique IF NOT EXISTS
  FOR (n:RiskProfile) REQUIRE n.risk_profile_id IS UNIQUE;

CREATE CONSTRAINT premium_id_unique IF NOT EXISTS
  FOR (n:Premium) REQUIRE n.premium_id IS UNIQUE;

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
  FOR (n:InsuranceProduct) REQUIRE n.product_id IS UNIQUE;

CREATE CONSTRAINT reinsurance_treaty_id_unique IF NOT EXISTS
  FOR (n:ReinsuranceTreaty) REQUIRE n.treaty_id IS UNIQUE;

// ── Technical / Observability Domain ──
CREATE CONSTRAINT deployment_id_unique IF NOT EXISTS
  FOR (n:Deployment) REQUIRE n.deployment_id IS UNIQUE;

CREATE CONSTRAINT service_id_unique IF NOT EXISTS
  FOR (n:Service) REQUIRE n.service_id IS UNIQUE;

CREATE CONSTRAINT repository_id_unique IF NOT EXISTS
  FOR (n:Repository) REQUIRE n.repository_id IS UNIQUE;

CREATE CONSTRAINT build_id_unique IF NOT EXISTS
  FOR (n:Build) REQUIRE n.build_id IS UNIQUE;

CREATE CONSTRAINT environment_id_unique IF NOT EXISTS
  FOR (n:Environment) REQUIRE n.environment_id IS UNIQUE;

CREATE CONSTRAINT commit_sha_unique IF NOT EXISTS
  FOR (n:Commit) REQUIRE n.sha IS UNIQUE;

// ── Intelligence / Event Domain ──
CREATE CONSTRAINT signal_id_unique IF NOT EXISTS
  FOR (n:Signal) REQUIRE n.signal_id IS UNIQUE;

CREATE CONSTRAINT event_id_unique IF NOT EXISTS
  FOR (n:Event) REQUIRE n.event_id IS UNIQUE;

CREATE CONSTRAINT anomaly_id_unique IF NOT EXISTS
  FOR (n:Anomaly) REQUIRE n.anomaly_id IS UNIQUE;

CREATE CONSTRAINT decision_id_unique IF NOT EXISTS
  FOR (n:Decision) REQUIRE n.decision_id IS UNIQUE;

CREATE CONSTRAINT outcome_id_unique IF NOT EXISTS
  FOR (n:Outcome) REQUIRE n.outcome_id IS UNIQUE;

// ── GCC Infrastructure Domain (aligned with simulation_engine 42 nodes) ──
CREATE CONSTRAINT gcc_node_id_unique IF NOT EXISTS
  FOR (n:GCCNode) REQUIRE n.node_id IS UNIQUE;

CREATE CONSTRAINT country_id_unique IF NOT EXISTS
  FOR (n:Country) REQUIRE n.country_id IS UNIQUE;

CREATE CONSTRAINT sector_id_unique IF NOT EXISTS
  FOR (n:Sector) REQUIRE n.sector_id IS UNIQUE;

CREATE CONSTRAINT regulator_id_unique IF NOT EXISTS
  FOR (n:Regulator) REQUIRE n.regulator_id IS UNIQUE;

// ── Propagation Domain ──
CREATE CONSTRAINT propagation_path_id_unique IF NOT EXISTS
  FOR (n:PropagationPath) REQUIRE n.path_id IS UNIQUE;

CREATE CONSTRAINT scenario_id_unique IF NOT EXISTS
  FOR (n:Scenario) REQUIRE n.scenario_id IS UNIQUE;

CREATE CONSTRAINT simulation_run_id_unique IF NOT EXISTS
  FOR (n:SimulationRun) REQUIRE n.run_id IS UNIQUE;


// ─── SECTION 3: INDEXES (query performance) ─────────────────────────────

// ── Temporal indexes (range queries on timestamps) ──
CREATE INDEX idx_claim_filed_at IF NOT EXISTS FOR (n:Claim) ON (n.filed_at);
CREATE INDEX idx_policy_effective_date IF NOT EXISTS FOR (n:Policy) ON (n.effective_date);
CREATE INDEX idx_deployment_created_at IF NOT EXISTS FOR (n:Deployment) ON (n.created_at);
CREATE INDEX idx_signal_received_at IF NOT EXISTS FOR (n:Signal) ON (n.received_at);
CREATE INDEX idx_event_occurred_at IF NOT EXISTS FOR (n:Event) ON (n.occurred_at);
CREATE INDEX idx_anomaly_detected_at IF NOT EXISTS FOR (n:Anomaly) ON (n.detected_at);
CREATE INDEX idx_decision_created_at IF NOT EXISTS FOR (n:Decision) ON (n.created_at);
CREATE INDEX idx_outcome_resolved_at IF NOT EXISTS FOR (n:Outcome) ON (n.resolved_at);
CREATE INDEX idx_simulation_run_at IF NOT EXISTS FOR (n:SimulationRun) ON (n.executed_at);

// ── Domain classification indexes ──
CREATE INDEX idx_policy_type IF NOT EXISTS FOR (n:Policy) ON (n.policy_type);
CREATE INDEX idx_claim_status IF NOT EXISTS FOR (n:Claim) ON (n.status);
CREATE INDEX idx_deployment_state IF NOT EXISTS FOR (n:Deployment) ON (n.state);
CREATE INDEX idx_signal_domain IF NOT EXISTS FOR (n:Signal) ON (n.impact_domain);
CREATE INDEX idx_gcc_node_sector IF NOT EXISTS FOR (n:GCCNode) ON (n.sector);
CREATE INDEX idx_anomaly_severity IF NOT EXISTS FOR (n:Anomaly) ON (n.severity);
CREATE INDEX idx_decision_urgency IF NOT EXISTS FOR (n:Decision) ON (n.urgency);

// ── Composite indexes for hot query paths ──
CREATE INDEX idx_claim_sector_status IF NOT EXISTS FOR (n:Claim) ON (n.sector, n.status);
CREATE INDEX idx_gcc_node_sector_state IF NOT EXISTS FOR (n:GCCNode) ON (n.sector, n.state);
CREATE INDEX idx_signal_domain_severity IF NOT EXISTS FOR (n:Signal) ON (n.impact_domain, n.severity);

// ── Full-text search (requires APOC or Neo4j 5.x) ──
// CREATE FULLTEXT INDEX ft_signal_description IF NOT EXISTS
//   FOR (n:Signal) ON EACH [n.description, n.source_title];


// ─── SECTION 4: SAMPLE GRAPH INSTANCES ──────────────────────────────────

// ── 4a. GCC Infrastructure Nodes (subset of 42 — aligned with simulation_engine.py) ──

CREATE (uae:Country {country_id: 'uae', name: 'United Arab Emirates', name_ar: 'الإمارات العربية المتحدة', iso_code: 'AE', gdp_usd: 507000000000})
CREATE (ksa:Country {country_id: 'ksa', name: 'Saudi Arabia', name_ar: 'المملكة العربية السعودية', iso_code: 'SA', gdp_usd: 1069000000000})
CREATE (qat:Country {country_id: 'qatar', name: 'Qatar', name_ar: 'قطر', iso_code: 'QA', gdp_usd: 236000000000})

CREATE (s_banking:Sector {sector_id: 'banking', name: 'Banking', name_ar: 'القطاع المصرفي', alpha_coefficient: 0.20})
CREATE (s_insurance:Sector {sector_id: 'insurance', name: 'Insurance', name_ar: 'التأمين', alpha_coefficient: 0.08})
CREATE (s_energy:Sector {sector_id: 'energy', name: 'Energy', name_ar: 'الطاقة', alpha_coefficient: 0.28})
CREATE (s_maritime:Sector {sector_id: 'maritime', name: 'Maritime', name_ar: 'النقل البحري', alpha_coefficient: 0.18})

CREATE (hormuz:GCCNode {node_id: 'hormuz', label: 'Strait of Hormuz', label_ar: 'مضيق هرمز', sector: 'maritime', capacity: 1.0, current_load: 0.85, criticality: 0.95, redundancy: 0.1, lat: 26.5667, lng: 56.25, state: 'NOMINAL'})
CREATE (dubai_port:GCCNode {node_id: 'dubai_port', label: 'Dubai Port (Jebel Ali)', label_ar: 'ميناء جبل علي', sector: 'maritime', capacity: 1.0, current_load: 0.78, criticality: 0.88, redundancy: 0.3, lat: 25.0, lng: 55.06, state: 'NOMINAL'})
CREATE (saudi_aramco:GCCNode {node_id: 'saudi_aramco', label: 'Saudi Aramco', label_ar: 'أرامكو السعودية', sector: 'energy', capacity: 1.0, current_load: 0.9, criticality: 0.95, redundancy: 0.15, lat: 26.32, lng: 50.21, state: 'NOMINAL'})
CREATE (uae_banking:GCCNode {node_id: 'uae_banking', label: 'UAE Banking Sector', label_ar: 'القطاع المصرفي الإماراتي', sector: 'banking', capacity: 1.0, current_load: 0.72, criticality: 0.85, redundancy: 0.4, lat: 25.2048, lng: 55.2708, state: 'NOMINAL'})
CREATE (gcc_insurance:GCCNode {node_id: 'gcc_insurance', label: 'GCC Insurance Sector', label_ar: 'قطاع التأمين الخليجي', sector: 'insurance', capacity: 1.0, current_load: 0.60, criticality: 0.70, redundancy: 0.45, lat: 25.276987, lng: 55.296249, state: 'NOMINAL'})

CREATE (cbuae:Regulator {regulator_id: 'cbuae', name: 'Central Bank of UAE', name_ar: 'مصرف الإمارات المركزي', country: 'uae', jurisdiction: 'banking,insurance'})
CREATE (sama:Regulator {regulator_id: 'sama', name: 'Saudi Central Bank', name_ar: 'البنك المركزي السعودي', country: 'ksa', jurisdiction: 'banking,insurance'})

// ── 4b. Insurance Domain ──

CREATE (cust1:Customer {
  customer_id: 'ins_cust_001',
  name: 'Gulf Maritime Holdings',
  name_ar: 'القابضة البحرية الخليجية',
  customer_type: 'CORPORATE',
  country: 'uae',
  sector: 'maritime',
  kyc_verified: true,
  risk_tier: 'HIGH',
  created_at: datetime('2024-01-15T00:00:00Z'),
  audit_hash: 'sha256:a1b2c3d4e5f6'
})

CREATE (pol1:Policy {
  policy_id: 'ins_pol_001',
  policy_type: 'MARINE_HULL',
  product_line: 'marine',
  effective_date: date('2025-01-01'),
  expiry_date: date('2026-01-01'),
  sum_insured_usd: 250000000,
  premium_usd: 1875000,
  currency: 'AED',
  status: 'ACTIVE',
  ifrs17_group: 'PAA',
  country: 'uae',
  created_at: datetime('2024-12-20T00:00:00Z')
})

CREATE (cov1:Coverage {
  coverage_id: 'ins_cov_001',
  coverage_type: 'HULL_AND_MACHINERY',
  limit_usd: 250000000,
  deductible_usd: 500000,
  sublimits: '{"war_risk": 50000000, "piracy": 25000000}',
  territory: 'GCC_WATERS'
})

CREATE (clm1:Claim {
  claim_id: 'ins_clm_001',
  claim_type: 'CARGO_DAMAGE',
  filed_at: datetime('2025-06-15T08:30:00Z'),
  amount_claimed_usd: 12500000,
  amount_reserved_usd: 10000000,
  amount_paid_usd: 0,
  status: 'OPEN',
  sector: 'maritime',
  cause: 'chokepoint_disruption',
  country: 'uae',
  fraud_score: 0.12,
  severity: 'HIGH'
})

CREATE (risk1:RiskProfile {
  risk_profile_id: 'ins_risk_001',
  entity_type: 'CORPORATE',
  overall_score: 0.72,
  financial_score: 0.65,
  operational_score: 0.78,
  geopolitical_score: 0.80,
  exposure_usd: 250000000,
  concentration_index: 0.45,
  last_assessed_at: datetime('2025-05-01T00:00:00Z')
})

CREATE (prem1:Premium {
  premium_id: 'ins_prem_001',
  base_premium_usd: 1500000,
  risk_loading_usd: 250000,
  catastrophe_loading_usd: 125000,
  total_premium_usd: 1875000,
  combined_ratio: 0.92,
  loss_ratio: 0.68,
  expense_ratio: 0.24,
  pricing_model_version: 'v3.2'
})

CREATE (treaty1:ReinsuranceTreaty {
  treaty_id: 'ins_treaty_001',
  treaty_type: 'EXCESS_OF_LOSS',
  reinsurer: 'Swiss Re',
  attachment_point_usd: 10000000,
  limit_usd: 100000000,
  rate_on_line: 0.085,
  effective_date: date('2025-01-01'),
  territory: 'GCC'
})

// ── 4c. Technical / Observability Domain ──

CREATE (repo1:Repository {
  repository_id: 'repo_impact_observatory',
  name: 'impact-observatory',
  full_name: 'PyBADR/impact-observatory',
  provider: 'github',
  default_branch: 'main',
  url: 'https://github.com/PyBADR/impact-observatory',
  language: 'TypeScript,Python',
  created_at: datetime('2024-06-01T00:00:00Z')
})

CREATE (svc_fe:Service {
  service_id: 'svc_frontend',
  name: 'Impact Observatory Frontend',
  service_type: 'FRONTEND',
  runtime: 'Next.js 15',
  provider: 'vercel',
  health_endpoint: 'https://deevo-sim.vercel.app',
  status: 'HEALTHY',
  sla_target: 0.999
})

CREATE (svc_be:Service {
  service_id: 'svc_backend',
  name: 'Impact Observatory Backend',
  service_type: 'API',
  runtime: 'FastAPI + Python 3.12',
  provider: 'railway',
  health_endpoint: 'https://api.impact-observatory.io/health',
  status: 'HEALTHY',
  sla_target: 0.999
})

CREATE (env_prod:Environment {
  environment_id: 'env_production',
  name: 'production',
  tier: 'PRODUCTION',
  url: 'https://deevo-sim.vercel.app',
  region: 'us-east-1',
  auto_deploy: true
})

CREATE (env_staging:Environment {
  environment_id: 'env_staging',
  name: 'staging',
  tier: 'STAGING',
  url: 'https://deevo-sim-staging.vercel.app',
  region: 'us-east-1',
  auto_deploy: true
})

CREATE (commit1:Commit {
  sha: 'f2996bf11fe46e888c0823c2ad069d69f4de11a9',
  short_sha: 'f2996bf',
  message: 'fix(hardening): close 4 production blockers from architecture review',
  author: 'PyBADR',
  branch: 'main',
  committed_at: datetime('2026-04-06T11:03:45Z')
})

CREATE (build1:Build {
  build_id: 'bld_mAjyXlYWevyKDnYddu2rL',
  provider: 'vercel',
  status: 'SUCCESS',
  duration_seconds: 87,
  started_at: datetime('2026-04-06T11:04:00Z'),
  finished_at: datetime('2026-04-06T11:05:27Z')
})

CREATE (deploy1:Deployment {
  deployment_id: 'dpl_prod_20260406',
  provider: 'vercel',
  state: 'READY',
  target: 'production',
  url: 'https://deevo-sim.vercel.app',
  commit_sha: 'f2996bf',
  created_at: datetime('2026-04-06T11:05:30Z'),
  verified: true,
  verification_fingerprint: 'sha256:e7f8a9b0c1d2',
  ready_at: datetime('2026-04-06T11:05:45Z')
})

// ── 4d. Intelligence / Event Domain ──

CREATE (sig1:Signal {
  signal_id: 'sig_hormuz_alert_001',
  signal_type: 'GEOPOLITICAL',
  source: 'RSS_FEED',
  source_title: 'Strait of Hormuz maritime traffic disruption detected',
  description: 'Naval exercises reported near Strait of Hormuz causing shipping delays',
  impact_domain: 'MARITIME',
  severity: 0.78,
  severity_level: 'HIGH',
  confidence: 0.85,
  regions: ['uae', 'oman', 'qatar'],
  received_at: datetime('2025-06-14T06:00:00Z'),
  content_hash: 'sha256:f1e2d3c4b5a6',
  dedup_status: 'UNIQUE'
})

CREATE (evt1:Event {
  event_id: 'evt_hormuz_disruption_001',
  event_type: 'CHOKEPOINT_DISRUPTION',
  severity: 0.82,
  started_at: datetime('2025-06-14T08:00:00Z'),
  duration_hours: 72,
  affected_sectors: ['maritime', 'energy', 'logistics'],
  affected_countries: ['uae', 'oman', 'qatar', 'ksa'],
  occurred_at: datetime('2025-06-14T08:00:00Z'),
  source_signal_id: 'sig_hormuz_alert_001'
})

CREATE (anom1:Anomaly {
  anomaly_id: 'anom_claims_spike_001',
  anomaly_type: 'CLAIMS_VOLUME_SPIKE',
  severity: 0.75,
  severity_level: 'ELEVATED',
  baseline_value: 12.0,
  observed_value: 47.0,
  deviation_factor: 3.92,
  sector: 'insurance',
  detected_at: datetime('2025-06-15T10:00:00Z'),
  detection_method: 'Z_SCORE_THRESHOLD',
  confirmed: true
})

CREATE (dec1:Decision {
  decision_id: 'dec_activate_catastrophe_001',
  action: 'Activate catastrophe reinsurance treaty for marine hull portfolio',
  action_ar: 'تفعيل اتفاقية إعادة التأمين الكارثي لمحفظة السفن البحرية',
  sector: 'insurance',
  owner: 'Chief Risk Officer',
  urgency: 'CRITICAL',
  priority: 1,
  time_to_act_hours: 4,
  loss_avoided_usd: 85000000,
  cost_usd: 2500000,
  regulatory_risk: 'MEDIUM',
  status: 'EXECUTED',
  created_at: datetime('2025-06-15T11:00:00Z'),
  executed_at: datetime('2025-06-15T12:30:00Z'),
  reasoning_chain: 'Signal→Event→ClaimsSpike→ReinsuranceActivation',
  graph_contribution_pct: 0.45,
  propagation_contribution_pct: 0.35,
  rule_contribution_pct: 0.20
})

CREATE (out1:Outcome {
  outcome_id: 'out_reinsurance_activation_001',
  classification: 'TRUE_POSITIVE',
  actual_loss_usd: 78000000,
  predicted_loss_usd: 85000000,
  prediction_accuracy: 0.918,
  net_value_usd: 75500000,
  resolved_at: datetime('2025-09-01T00:00:00Z'),
  lessons_learned: 'Treaty activation within 4h window prevented reserve shortfall'
})

CREATE (scenario1:Scenario {
  scenario_id: 'hormuz_chokepoint_disruption',
  name: 'Strait of Hormuz Partial Blockage',
  name_ar: 'انسداد جزئي لمضيق هرمز',
  severity_multiplier: 1.0,
  affected_nodes: ['hormuz', 'dubai_port', 'saudi_aramco'],
  category: 'GEOPOLITICAL'
})

CREATE (simrun1:SimulationRun {
  run_id: 'run_hormuz_20250614',
  scenario_id: 'hormuz_chokepoint_disruption',
  executed_at: datetime('2025-06-14T09:00:00Z'),
  total_loss_usd: 4200000000,
  peak_day: 3,
  recovery_days: 45,
  urs_score: 0.78,
  risk_level: 'HIGH',
  pipeline_stages_completed: 17,
  audit_hash: 'sha256:b2c3d4e5f6a7'
})

CREATE (proppath1:PropagationPath {
  path_id: 'prop_hormuz_to_insurance_001',
  entry_domain: 'maritime',
  terminal_domain: 'insurance',
  total_hops: 3,
  cumulative_decay: 0.42,
  path_description: 'hormuz → dubai_port → uae_banking → gcc_insurance',
  audit_hash: 'sha256:c3d4e5f6a7b8'
})


// ─── SECTION 5: RELATIONSHIPS ───────────────────────────────────────────

// ── Insurance Domain Relationships ──
CREATE (cust1)-[:OWNS_POLICY {since: date('2025-01-01'), relationship_type: 'POLICYHOLDER'}]->(pol1)
CREATE (pol1)-[:HAS_COVERAGE {effective_date: date('2025-01-01')}]->(cov1)
CREATE (pol1)-[:GENERATED_CLAIM {filed_at: datetime('2025-06-15T08:30:00Z')}]->(clm1)
CREATE (cust1)-[:HAS_RISK_PROFILE {assessed_at: datetime('2025-05-01T00:00:00Z')}]->(risk1)
CREATE (pol1)-[:PRICED_BY {pricing_date: date('2024-12-15')}]->(prem1)
CREATE (pol1)-[:PROTECTED_BY {attachment_point_usd: 10000000}]->(treaty1)
CREATE (cust1)-[:OPERATES_IN_SECTOR]->(s_maritime)
CREATE (cust1)-[:LOCATED_IN]->(uae)

// ── GCC Infrastructure Relationships (aligned with simulation_engine adjacency) ──
CREATE (hormuz)-[:PROPAGATES_TO {weight: 0.85, channel: 'SUPPLY_CHAIN', decay: 0.05}]->(dubai_port)
CREATE (hormuz)-[:PROPAGATES_TO {weight: 0.70, channel: 'DIRECT_EXPOSURE', decay: 0.05}]->(saudi_aramco)
CREATE (dubai_port)-[:PROPAGATES_TO {weight: 0.55, channel: 'MARKET_CONTAGION', decay: 0.05}]->(uae_banking)
CREATE (uae_banking)-[:PROPAGATES_TO {weight: 0.40, channel: 'RISK_TRANSFER', decay: 0.05}]->(gcc_insurance)
CREATE (hormuz)-[:BELONGS_TO_SECTOR]->(s_maritime)
CREATE (dubai_port)-[:BELONGS_TO_SECTOR]->(s_maritime)
CREATE (saudi_aramco)-[:BELONGS_TO_SECTOR]->(s_energy)
CREATE (uae_banking)-[:BELONGS_TO_SECTOR]->(s_banking)
CREATE (gcc_insurance)-[:BELONGS_TO_SECTOR]->(s_insurance)
CREATE (uae_banking)-[:LOCATED_IN]->(uae)
CREATE (gcc_insurance)-[:LOCATED_IN]->(uae)
CREATE (saudi_aramco)-[:LOCATED_IN]->(ksa)
CREATE (cbuae)-[:REGULATES]->(uae_banking)
CREATE (cbuae)-[:REGULATES]->(gcc_insurance)
CREATE (sama)-[:REGULATES]->(saudi_aramco)

// ── Technical Domain Relationships ──
CREATE (repo1)-[:CONTAINS_SERVICE]->(svc_fe)
CREATE (repo1)-[:CONTAINS_SERVICE]->(svc_be)
CREATE (commit1)-[:COMMITTED_TO]->(repo1)
CREATE (build1)-[:BUILT_FROM]->(commit1)
CREATE (deploy1)-[:DEPLOYS]->(svc_fe)
CREATE (deploy1)-[:BUILT_BY]->(build1)
CREATE (deploy1)-[:TARGETS]->(env_prod)
CREATE (svc_fe)-[:RUNS_IN]->(env_prod)
CREATE (svc_be)-[:RUNS_IN]->(env_prod)

// ── Intelligence Lifecycle Relationships ──
//    Signal → Event → Anomaly → Decision → Outcome
CREATE (sig1)-[:TRIGGERS {confidence: 0.85}]->(evt1)
CREATE (evt1)-[:AFFECTS {severity: 0.82, channel: 'CHOKEPOINT_DISRUPTION'}]->(hormuz)
CREATE (evt1)-[:CAUSED_ANOMALY {detection_lag_hours: 26}]->(anom1)
CREATE (anom1)-[:PROMPTED_DECISION {urgency: 'CRITICAL'}]->(dec1)
CREATE (dec1)-[:PRODUCED_OUTCOME {accuracy: 0.918}]->(out1)

// ── Cross-Domain Bridging Relationships (insurance ↔ events) ──
CREATE (evt1)-[:TRIGGERED_CLAIMS_IN {volume_increase_pct: 292}]->(gcc_insurance)
CREATE (clm1)-[:CAUSED_BY_EVENT]->(evt1)
CREATE (dec1)-[:APPLIED_TO]->(treaty1)
CREATE (risk1)-[:INFLUENCED_BY]->(evt1)

// ── Simulation Relationships ──
CREATE (scenario1)-[:EXECUTED_AS]->(simrun1)
CREATE (simrun1)-[:PROPAGATED_VIA]->(proppath1)
CREATE (simrun1)-[:IMPACTED_NODE {loss_usd: 2100000000}]->(hormuz)
CREATE (simrun1)-[:IMPACTED_NODE {loss_usd: 890000000}]->(dubai_port)
CREATE (simrun1)-[:IMPACTED_NODE {loss_usd: 650000000}]->(uae_banking)
CREATE (simrun1)-[:IMPACTED_NODE {loss_usd: 320000000}]->(gcc_insurance)
CREATE (sig1)-[:SEEDED_SCENARIO]->(scenario1)

// ── Deployment ↔ Business Impact (cross-domain) ──
CREATE (deploy1)-[:SERVES]->(svc_fe)
CREATE (svc_fe)-[:POWERS_ANALYTICS_FOR]->(gcc_insurance)
CREATE (svc_be)-[:RUNS_SIMULATION_FOR]->(simrun1);


// ─── SECTION 6: EXAMPLE QUERIES ─────────────────────────────────────────

// ── Q1: Traverse from deployment failures to affected services ──
// MATCH (d:Deployment {state: 'ERROR'})-[:DEPLOYS]->(s:Service)
// OPTIONAL MATCH (s)-[:POWERS_ANALYTICS_FOR]->(g:GCCNode)
// RETURN d.deployment_id, d.commit_sha, s.name, s.status,
//        collect(g.label) AS affected_gcc_nodes
// ORDER BY d.created_at DESC;

// ── Q2: Link claims to customer risk profiles ──
// MATCH (c:Customer)-[:OWNS_POLICY]->(p:Policy)-[:GENERATED_CLAIM]->(cl:Claim)
// MATCH (c)-[:HAS_RISK_PROFILE]->(r:RiskProfile)
// WHERE cl.status = 'OPEN' AND cl.amount_claimed_usd > 1000000
// RETURN c.name, c.risk_tier, r.overall_score, r.geopolitical_score,
//        cl.claim_id, cl.amount_claimed_usd, cl.fraud_score
// ORDER BY cl.amount_claimed_usd DESC;

// ── Q3: Identify anomalies across systems ──
// MATCH (a:Anomaly)
// WHERE a.severity > 0.6 AND a.detected_at > datetime() - duration('P7D')
// OPTIONAL MATCH (a)<-[:CAUSED_ANOMALY]-(e:Event)-[:AFFECTS]->(g:GCCNode)
// RETURN a.anomaly_type, a.severity, a.deviation_factor,
//        e.event_type, collect(DISTINCT g.label) AS affected_nodes
// ORDER BY a.severity DESC;

// ── Q4: Correlate technical events with business impact ──
// MATCH (d:Deployment)-[:DEPLOYS]->(s:Service)-[:POWERS_ANALYTICS_FOR]->(g:GCCNode)
// MATCH (g)<-[:AFFECTS]-(e:Event)<-[:TRIGGERS]-(sig:Signal)
// WHERE d.created_at > datetime() - duration('P30D')
// RETURN d.deployment_id, d.state, s.name,
//        g.label, e.event_type, sig.severity,
//        e.affected_sectors
// ORDER BY sig.severity DESC;

// ── Q5: Full signal-to-outcome lifecycle trace ──
// MATCH path = (sig:Signal)-[:TRIGGERS]->(evt:Event)
//              -[:CAUSED_ANOMALY]->(anom:Anomaly)
//              -[:PROMPTED_DECISION]->(dec:Decision)
//              -[:PRODUCED_OUTCOME]->(out:Outcome)
// RETURN sig.signal_id, sig.severity AS signal_severity,
//        evt.event_type, anom.anomaly_type,
//        dec.action, dec.loss_avoided_usd,
//        out.classification, out.net_value_usd,
//        length(path) AS lifecycle_hops;

// ── Q6: Propagation path analysis ──
// MATCH path = (entry:GCCNode)-[:PROPAGATES_TO*1..5]->(terminal:GCCNode)
// WHERE entry.node_id = 'hormuz'
// RETURN [n IN nodes(path) | n.label] AS propagation_chain,
//        [r IN relationships(path) | r.weight] AS weights,
//        reduce(w = 1.0, r IN relationships(path) | w * r.weight) AS cumulative_weight
// ORDER BY cumulative_weight DESC;

// ── Q7: Insurance exposure by GCC event ──
// MATCH (evt:Event)-[:TRIGGERED_CLAIMS_IN]->(g:GCCNode {sector: 'insurance'})
// MATCH (cl:Claim)-[:CAUSED_BY_EVENT]->(evt)
// MATCH (cl)<-[:GENERATED_CLAIM]-(p:Policy)<-[:OWNS_POLICY]-(c:Customer)
// RETURN evt.event_type,
//        count(DISTINCT cl) AS claim_count,
//        sum(cl.amount_claimed_usd) AS total_exposure_usd,
//        collect(DISTINCT c.name) AS affected_customers;

// ── Q8: Fraud detection — high-risk claims with event correlation ──
// MATCH (cl:Claim)
// WHERE cl.fraud_score > 0.5
// OPTIONAL MATCH (cl)-[:CAUSED_BY_EVENT]->(evt:Event)
// OPTIONAL MATCH (cl)<-[:GENERATED_CLAIM]-(p:Policy)<-[:OWNS_POLICY]-(c:Customer)
//                -[:HAS_RISK_PROFILE]->(r:RiskProfile)
// RETURN cl.claim_id, cl.fraud_score, cl.amount_claimed_usd,
//        c.name, c.risk_tier, r.overall_score,
//        evt.event_type,
//        CASE WHEN evt IS NULL THEN 'NO_CORRELATED_EVENT'
//             ELSE 'EVENT_CORRELATED' END AS correlation_status;

// ── Q9: Deployment verification audit trail ──
// MATCH (d:Deployment)-[:BUILT_BY]->(b:Build)-[:BUILT_FROM]->(c:Commit)
//       -[:COMMITTED_TO]->(r:Repository)
// WHERE d.target = 'production'
// RETURN d.deployment_id, d.state, d.verified,
//        d.verification_fingerprint,
//        c.sha, c.message, c.committed_at,
//        b.duration_seconds, r.full_name
// ORDER BY d.created_at DESC LIMIT 10;
