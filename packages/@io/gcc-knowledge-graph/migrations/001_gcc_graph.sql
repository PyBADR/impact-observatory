-- ═══════════════════════════════════════════════════════════
-- @deevo/gcc-knowledge-graph — PostgreSQL Migration 001
-- GCC Reality Graph: 5-Layer Causal Dependency Model v5.0
--
-- Tables: gcc_nodes, gcc_edges, gcc_scenarios, gcc_scenario_shocks
-- Indexes: layer, type, source/target, scenario group
-- ═══════════════════════════════════════════════════════════

BEGIN;

-- ── Enums ────────────────────────────────────────────────
CREATE TYPE gcc_layer AS ENUM (
  'geography', 'infrastructure', 'economy', 'finance', 'society'
);

CREATE TYPE simulation_type AS ENUM (
  'deterministic', 'probabilistic', 'hybrid'
);

CREATE TYPE scenario_group AS ENUM (
  'geopolitics', 'aviation', 'ports_supply',
  'finance_markets', 'utilities_state', 'sovereign_projects'
);

-- ── Nodes ────────────────────────────────────────────────
CREATE TABLE gcc_nodes (
  id              TEXT PRIMARY KEY,
  label           TEXT NOT NULL,
  label_ar        TEXT NOT NULL,
  layer           gcc_layer NOT NULL,
  type            TEXT NOT NULL,
  weight          DOUBLE PRECISION NOT NULL CHECK (weight >= 0 AND weight <= 1),
  sensitivity     DOUBLE PRECISION NOT NULL CHECK (sensitivity >= 0 AND sensitivity <= 1),
  damping_factor  DOUBLE PRECISION NOT NULL CHECK (damping_factor >= 0 AND damping_factor <= 1),
  lat             DOUBLE PRECISION NOT NULL CHECK (lat >= -90 AND lat <= 90),
  lng             DOUBLE PRECISION NOT NULL CHECK (lng >= -180 AND lng <= 180),
  value           DOUBLE PRECISION NOT NULL CHECK (value >= 0 AND value <= 1),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gcc_nodes_layer ON gcc_nodes(layer);
CREATE INDEX idx_gcc_nodes_type  ON gcc_nodes(type);
CREATE INDEX idx_gcc_nodes_geo   ON gcc_nodes USING gist (
  ST_SetSRID(ST_MakePoint(lng, lat), 4326)
) WHERE lat IS NOT NULL;

COMMENT ON TABLE gcc_nodes IS 'GCC Reality Graph nodes — 76 entities across 5 layers';

-- ── Edges ────────────────────────────────────────────────
CREATE TABLE gcc_edges (
  id          TEXT PRIMARY KEY,
  source      TEXT NOT NULL REFERENCES gcc_nodes(id) ON DELETE CASCADE,
  target      TEXT NOT NULL REFERENCES gcc_nodes(id) ON DELETE CASCADE,
  weight      DOUBLE PRECISION NOT NULL CHECK (weight >= 0 AND weight <= 1),
  polarity    SMALLINT NOT NULL CHECK (polarity IN (1, -1)),
  label       TEXT NOT NULL,
  label_ar    TEXT NOT NULL,
  animated    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT no_self_loop CHECK (source <> target)
);

CREATE INDEX idx_gcc_edges_source ON gcc_edges(source);
CREATE INDEX idx_gcc_edges_target ON gcc_edges(target);
CREATE INDEX idx_gcc_edges_weight ON gcc_edges(weight DESC);

COMMENT ON TABLE gcc_edges IS 'GCC Reality Graph edges — 191 weighted causal dependencies';

-- ── Scenarios ────────────────────────────────────────────
CREATE TABLE gcc_scenarios (
  id                          TEXT PRIMARY KEY,
  engine_id                   TEXT NOT NULL,
  title                       TEXT NOT NULL,
  title_ar                    TEXT NOT NULL,
  description                 TEXT NOT NULL,
  description_ar              TEXT NOT NULL,
  category                    TEXT NOT NULL,
  country                     TEXT NOT NULL,
  "group"                     scenario_group NOT NULL,
  thesis                      TEXT NOT NULL,
  thesis_ar                   TEXT NOT NULL,
  sectors                     TEXT[] NOT NULL DEFAULT '{}',
  key_entities                TEXT[] NOT NULL DEFAULT '{}',
  map_modes                   TEXT[] NOT NULL DEFAULT '{}',
  formula_tags                TEXT[] NOT NULL DEFAULT '{}',
  severity_default            DOUBLE PRECISION NOT NULL CHECK (severity_default >= 0 AND severity_default <= 1),
  time_horizon                TEXT NOT NULL,
  time_horizon_ar             TEXT NOT NULL,
  expected_propagation_domains TEXT[] NOT NULL DEFAULT '{}',
  simulation_type             simulation_type NOT NULL DEFAULT 'deterministic',
  choke_points                TEXT[] NOT NULL DEFAULT '{}',
  geospatial_anchors          TEXT[] NOT NULL DEFAULT '{}',
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gcc_scenarios_group    ON gcc_scenarios("group");
CREATE INDEX idx_gcc_scenarios_country  ON gcc_scenarios(country);
CREATE INDEX idx_gcc_scenarios_severity ON gcc_scenarios(severity_default DESC);

COMMENT ON TABLE gcc_scenarios IS 'GCC strategic command scenarios — 17 across 6 groups';

-- ── Scenario Shocks ──────────────────────────────────────
CREATE TABLE gcc_scenario_shocks (
  id           SERIAL PRIMARY KEY,
  scenario_id  TEXT NOT NULL REFERENCES gcc_scenarios(id) ON DELETE CASCADE,
  node_id      TEXT NOT NULL REFERENCES gcc_nodes(id) ON DELETE CASCADE,
  impact       DOUBLE PRECISION NOT NULL CHECK (impact >= -1 AND impact <= 1),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gcc_shocks_scenario ON gcc_scenario_shocks(scenario_id);
CREATE INDEX idx_gcc_shocks_node     ON gcc_scenario_shocks(node_id);

COMMENT ON TABLE gcc_scenario_shocks IS 'Scenario shock vectors — initial perturbation targets';

-- ── Audit Trail ──────────────────────────────────────────
CREATE TABLE gcc_graph_audit (
  id          SERIAL PRIMARY KEY,
  table_name  TEXT NOT NULL,
  record_id   TEXT NOT NULL,
  action      TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_data    JSONB,
  new_data    JSONB,
  sha256      TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by  TEXT NOT NULL DEFAULT 'system'
);

CREATE INDEX idx_gcc_audit_table  ON gcc_graph_audit(table_name);
CREATE INDEX idx_gcc_audit_record ON gcc_graph_audit(record_id);
CREATE INDEX idx_gcc_audit_time   ON gcc_graph_audit(created_at DESC);

COMMENT ON TABLE gcc_graph_audit IS 'SHA-256 audit trail for all graph mutations';

-- ── Version Tracking ─────────────────────────────────────
CREATE TABLE gcc_graph_version (
  id           SERIAL PRIMARY KEY,
  version      TEXT NOT NULL,
  description  TEXT,
  node_count   INTEGER NOT NULL,
  edge_count   INTEGER NOT NULL,
  scenario_count INTEGER NOT NULL,
  checksum     TEXT NOT NULL,
  applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO gcc_graph_version (version, description, node_count, edge_count, scenario_count, checksum)
VALUES ('5.0.0', 'Initial GCC Reality Graph — 5-Layer Causal Dependency Model', 76, 191, 17, 'pending');

COMMIT;
