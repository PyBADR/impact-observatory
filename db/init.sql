-- Impact Observatory | مرصد الأثر
-- PostgreSQL initialization script
-- Runs automatically on first docker-compose up

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Runs table — persists pipeline execution results
-- ============================================================================
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(64) UNIQUE NOT NULL,
    template_id VARCHAR(128) NOT NULL,
    severity FLOAT NOT NULL DEFAULT 0.5,
    horizon_hours INTEGER NOT NULL DEFAULT 336,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    headline_loss_usd DOUBLE PRECISION,
    peak_day INTEGER,
    severity_code VARCHAR(32),
    result_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms FLOAT
);

CREATE INDEX IF NOT EXISTS idx_runs_template ON runs(template_id);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

-- ============================================================================
-- Decision actions table — tracks human approvals
-- ============================================================================
CREATE TABLE IF NOT EXISTS decision_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(64) NOT NULL REFERENCES runs(run_id),
    action_id VARCHAR(64) NOT NULL,
    action_text TEXT NOT NULL,
    action_text_ar TEXT,
    sector VARCHAR(64),
    owner VARCHAR(128),
    priority FLOAT,
    urgency FLOAT,
    value FLOAT,
    feasibility FLOAT,
    time_effect FLOAT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    approved_by VARCHAR(128),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(run_id, action_id)
);

CREATE INDEX IF NOT EXISTS idx_actions_run ON decision_actions(run_id);
CREATE INDEX IF NOT EXISTS idx_actions_status ON decision_actions(status);

-- ============================================================================
-- Audit log — immutable record of all pipeline executions
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    run_id VARCHAR(64),
    stage VARCHAR(64) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    payload JSONB,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_run ON audit_log(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);

-- ============================================================================
-- GCC Entities — reference data for the knowledge graph
-- ============================================================================
CREATE TABLE IF NOT EXISTS entities (
    id VARCHAR(64) PRIMARY KEY,
    label VARCHAR(256) NOT NULL,
    label_ar VARCHAR(256),
    layer VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64),
    country VARCHAR(64),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    gdp_usd DOUBLE PRECISION,
    criticality FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_layer ON entities(layer);
CREATE INDEX IF NOT EXISTS idx_entities_country ON entities(country);
CREATE INDEX IF NOT EXISTS idx_entities_geom ON entities USING GIST(geom);

-- ============================================================================
-- Entity edges — relationships in the knowledge graph
-- ============================================================================
CREATE TABLE IF NOT EXISTS entity_edges (
    id BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES entities(id),
    target_id VARCHAR(64) NOT NULL REFERENCES entities(id),
    edge_type VARCHAR(64) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    UNIQUE(source_id, target_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON entity_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON entity_edges(target_id);

-- ============================================================================
-- Scenario templates — predefined scenario configurations
-- ============================================================================
CREATE TABLE IF NOT EXISTS scenario_templates (
    template_id VARCHAR(128) PRIMARY KEY,
    title_en VARCHAR(256) NOT NULL,
    title_ar VARCHAR(256),
    description_en TEXT,
    description_ar TEXT,
    scenario_type VARCHAR(64) NOT NULL,
    default_severity FLOAT DEFAULT 0.6,
    default_horizon_hours INTEGER DEFAULT 336,
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Seed scenario templates
-- ============================================================================
INSERT INTO scenario_templates (template_id, title_en, title_ar, scenario_type, default_severity, default_horizon_hours)
VALUES
    ('hormuz_disruption', 'Strait of Hormuz Closure', 'إغلاق مضيق هرمز', 'disruption', 0.8, 336),
    ('yemen_escalation', 'Yemen Escalation', 'تصعيد يمني', 'escalation', 0.7, 336),
    ('cyber_attack', 'Cyber Attack on Financial Infrastructure', 'هجوم سيبراني على البنية المالية', 'cascading', 0.6, 168),
    ('oil_price_shock', 'Oil Price Shock', 'صدمة أسعار النفط', 'disruption', 0.8, 504),
    ('banking_stress', 'Regional Banking Stress', 'ضغط بنكي إقليمي', 'cascading', 0.7, 336),
    ('port_disruption', 'Major Port Disruption', 'تعطل ميناء رئيسي', 'disruption', 0.6, 240),
    ('iran_sanctions', 'Iran Sanctions Escalation', 'تصعيد عقوبات إيران', 'escalation', 0.7, 504),
    ('gulf_airspace', 'Gulf Airspace Restriction', 'تقييد المجال الجوي الخليجي', 'disruption', 0.5, 168)
ON CONFLICT (template_id) DO NOTHING;

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO observatory_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO observatory_admin;
