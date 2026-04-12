"""P2 Data Foundation — initial 12 tables.

Revision ID: 001_p2_foundation
Revises: None
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_p2_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _foundation_cols():
    """Columns shared by every df_ table (mirrors FoundationModel)."""
    return [
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("tenant_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("provenance_hash", sa.String(128), nullable=True),
    ]


def upgrade() -> None:
    # ── df_entity_registry ───────────────────────────────────────────────
    op.create_table(
        "df_entity_registry",
        sa.Column("entity_id", sa.String(64), primary_key=True),
        sa.Column("entity_name", sa.String(256), nullable=False),
        sa.Column("entity_name_ar", sa.String(256), nullable=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("sector", sa.String(64), nullable=False),
        sa.Column("parent_entity_id", sa.String(64), nullable=True),
        sa.Column("geo_lat", sa.Float, nullable=True),
        sa.Column("geo_lng", sa.Float, nullable=True),
        sa.Column("gdp_weight", sa.Float, nullable=False, server_default="0"),
        sa.Column("criticality_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("systemic_importance", sa.String(64), nullable=True),
        sa.Column("regulatory_id", sa.String(128), nullable=True),
        sa.Column("swift_code", sa.String(16), nullable=True),
        sa.Column("lei_code", sa.String(32), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("related_entity_ids", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_entity_type", "df_entity_registry", ["entity_type"])
    op.create_index("ix_df_entity_country", "df_entity_registry", ["country"])
    op.create_index("ix_df_entity_sector", "df_entity_registry", ["sector"])
    op.create_index("ix_df_entity_criticality", "df_entity_registry", ["criticality_score"])
    op.create_index("ix_df_entity_type_country", "df_entity_registry", ["entity_type", "country"])

    # ── df_event_signals ─────────────────────────────────────────────────
    op.create_table(
        "df_event_signals",
        sa.Column("event_id", sa.String(128), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("title_ar", sa.String(512), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("subcategory", sa.String(64), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("severity_score", sa.Float, nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("countries_affected", postgresql.JSONB, nullable=True),
        sa.Column("sectors_affected", postgresql.JSONB, nullable=True),
        sa.Column("entity_ids_affected", postgresql.JSONB, nullable=True),
        sa.Column("scenario_ids", postgresql.JSONB, nullable=True),
        sa.Column("geo_lat", sa.Float, nullable=True),
        sa.Column("geo_lng", sa.Float, nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'DEFAULT'"),
        sa.Column("corroborating_source_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_ongoing", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("parent_event_id", sa.String(128), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("raw_payload", postgresql.JSONB, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_event_category", "df_event_signals", ["category"])
    op.create_index("ix_df_event_severity", "df_event_signals", ["severity"])
    op.create_index("ix_df_event_time", "df_event_signals", ["event_time"])
    op.create_index("ix_df_event_source", "df_event_signals", ["source_id"])
    op.create_index("ix_df_event_severity_score", "df_event_signals", ["severity_score"])
    op.create_index("ix_df_event_category_severity", "df_event_signals", ["category", "severity"])

    # ── df_macro_indicators ──────────────────────────────────────────────
    op.create_table(
        "df_macro_indicators",
        sa.Column("indicator_id", sa.String(128), primary_key=True),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("indicator_code", sa.String(64), nullable=False),
        sa.Column("indicator_name", sa.String(256), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(4), nullable=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("frequency", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("source_reliability", sa.String(32), nullable=False, server_default="'HIGH'"),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.8"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("is_provisional", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("revision_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("previous_value", sa.Float, nullable=True),
        sa.Column("yoy_change_pct", sa.Float, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_macro_country", "df_macro_indicators", ["country"])
    op.create_index("ix_df_macro_code", "df_macro_indicators", ["indicator_code"])
    op.create_index("ix_df_macro_period", "df_macro_indicators", ["period_start", "period_end"])
    op.create_index("ix_df_macro_country_code", "df_macro_indicators", ["country", "indicator_code"])

    # ── df_interest_rate_signals ─────────────────────────────────────────
    op.create_table(
        "df_interest_rate_signals",
        sa.Column("signal_id", sa.String(128), primary_key=True),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("issuer_entity_id", sa.String(64), nullable=False),
        sa.Column("rate_type", sa.String(64), nullable=False),
        sa.Column("rate_value_bps", sa.Integer, nullable=False),
        sa.Column("rate_value_pct", sa.Float, nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("previous_rate_bps", sa.Integer, nullable=True),
        sa.Column("change_bps", sa.Integer, nullable=True),
        sa.Column("reference_rate", sa.String(64), nullable=True),
        sa.Column("spread_to_reference_bps", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(4), nullable=False, server_default="'USD'"),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.95"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("is_scheduled_decision", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("next_decision_date", sa.Date, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_ir_country", "df_interest_rate_signals", ["country"])
    op.create_index("ix_df_ir_rate_type", "df_interest_rate_signals", ["rate_type"])
    op.create_index("ix_df_ir_effective", "df_interest_rate_signals", ["effective_date"])

    # ── df_oil_energy_signals ────────────────────────────────────────────
    op.create_table(
        "df_oil_energy_signals",
        sa.Column("signal_id", sa.String(128), primary_key=True),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("benchmark", sa.String(64), nullable=True),
        sa.Column("country", sa.String(4), nullable=True),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(4), nullable=False, server_default="'USD'"),
        sa.Column("observation_date", sa.Date, nullable=False),
        sa.Column("previous_value", sa.Float, nullable=True),
        sa.Column("change_pct", sa.Float, nullable=True),
        sa.Column("fiscal_breakeven_price", sa.Float, nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.85"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        *_foundation_cols(),
    )
    op.create_index("ix_df_oil_type", "df_oil_energy_signals", ["signal_type"])
    op.create_index("ix_df_oil_country", "df_oil_energy_signals", ["country"])
    op.create_index("ix_df_oil_date", "df_oil_energy_signals", ["observation_date"])

    # ── df_fx_signals ────────────────────────────────────────────────────
    op.create_table(
        "df_fx_signals",
        sa.Column("signal_id", sa.String(128), primary_key=True),
        sa.Column("base_currency", sa.String(4), nullable=False),
        sa.Column("quote_currency", sa.String(4), nullable=False),
        sa.Column("country", sa.String(4), nullable=True),
        sa.Column("rate", sa.Float, nullable=False),
        sa.Column("rate_type", sa.String(32), nullable=False, server_default="'SPOT'"),
        sa.Column("observation_date", sa.Date, nullable=False),
        sa.Column("peg_rate", sa.Float, nullable=True),
        sa.Column("deviation_from_peg_bps", sa.Integer, nullable=True),
        sa.Column("bid", sa.Float, nullable=True),
        sa.Column("ask", sa.Float, nullable=True),
        sa.Column("spread_bps", sa.Integer, nullable=True),
        sa.Column("daily_high", sa.Float, nullable=True),
        sa.Column("daily_low", sa.Float, nullable=True),
        sa.Column("previous_close", sa.Float, nullable=True),
        sa.Column("change_pct", sa.Float, nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.9"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        *_foundation_cols(),
    )
    op.create_index("ix_df_fx_base", "df_fx_signals", ["base_currency"])
    op.create_index("ix_df_fx_date", "df_fx_signals", ["observation_date"])

    # ── df_cbk_indicators ────────────────────────────────────────────────
    op.create_table(
        "df_cbk_indicators",
        sa.Column("indicator_id", sa.String(128), primary_key=True),
        sa.Column("indicator_code", sa.String(64), nullable=False),
        sa.Column("indicator_name", sa.String(256), nullable=False),
        sa.Column("indicator_name_ar", sa.String(256), nullable=True),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(4), nullable=False, server_default="'KWD'"),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("frequency", sa.String(32), nullable=False, server_default="'monthly'"),
        sa.Column("source_id", sa.String(128), nullable=False, server_default="'cbk-statistical-bulletin'"),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.95"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("is_provisional", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("previous_value", sa.Float, nullable=True),
        sa.Column("yoy_change_pct", sa.Float, nullable=True),
        sa.Column("mom_change_pct", sa.Float, nullable=True),
        sa.Column("regulatory_threshold", sa.Float, nullable=True),
        sa.Column("breach_status", sa.String(32), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_cbk_code", "df_cbk_indicators", ["indicator_code"])
    op.create_index("ix_df_cbk_period", "df_cbk_indicators", ["period_start"])

    # ── df_banking_profiles ──────────────────────────────────────────────
    op.create_table(
        "df_banking_profiles",
        sa.Column("profile_id", sa.String(128), primary_key=True),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("entity_name", sa.String(256), nullable=False),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("reporting_date", sa.Date, nullable=False),
        sa.Column("reporting_period", sa.String(16), nullable=False),
        sa.Column("currency", sa.String(4), nullable=False, server_default="'KWD'"),
        sa.Column("total_assets", sa.Float, nullable=True),
        sa.Column("total_deposits", sa.Float, nullable=True),
        sa.Column("total_loans", sa.Float, nullable=True),
        sa.Column("total_equity", sa.Float, nullable=True),
        sa.Column("net_income", sa.Float, nullable=True),
        sa.Column("roe_pct", sa.Float, nullable=True),
        sa.Column("roa_pct", sa.Float, nullable=True),
        sa.Column("cost_to_income_pct", sa.Float, nullable=True),
        sa.Column("nim_pct", sa.Float, nullable=True),
        sa.Column("npl_ratio_pct", sa.Float, nullable=True),
        sa.Column("npl_coverage_pct", sa.Float, nullable=True),
        sa.Column("loan_loss_provision", sa.Float, nullable=True),
        sa.Column("car_pct", sa.Float, nullable=True),
        sa.Column("cet1_pct", sa.Float, nullable=True),
        sa.Column("tier1_pct", sa.Float, nullable=True),
        sa.Column("leverage_ratio_pct", sa.Float, nullable=True),
        sa.Column("lcr_pct", sa.Float, nullable=True),
        sa.Column("nsfr_pct", sa.Float, nullable=True),
        sa.Column("loan_to_deposit_pct", sa.Float, nullable=True),
        sa.Column("is_dsib", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("dsib_buffer_pct", sa.Float, nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.85"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("is_audited", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("auditor", sa.String(64), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_bank_entity", "df_banking_profiles", ["entity_id"])
    op.create_index("ix_df_bank_country", "df_banking_profiles", ["country"])
    op.create_index("ix_df_bank_date", "df_banking_profiles", ["reporting_date"])

    # ── df_insurance_profiles ────────────────────────────────────────────
    op.create_table(
        "df_insurance_profiles",
        sa.Column("profile_id", sa.String(128), primary_key=True),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("entity_name", sa.String(256), nullable=False),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("insurance_type", sa.String(32), nullable=False),
        sa.Column("reporting_date", sa.Date, nullable=False),
        sa.Column("reporting_period", sa.String(16), nullable=False),
        sa.Column("currency", sa.String(4), nullable=False, server_default="'KWD'"),
        sa.Column("gwp", sa.Float, nullable=True),
        sa.Column("nwp", sa.Float, nullable=True),
        sa.Column("nep", sa.Float, nullable=True),
        sa.Column("retention_ratio_pct", sa.Float, nullable=True),
        sa.Column("net_claims_incurred", sa.Float, nullable=True),
        sa.Column("loss_ratio_pct", sa.Float, nullable=True),
        sa.Column("combined_ratio_pct", sa.Float, nullable=True),
        sa.Column("expense_ratio_pct", sa.Float, nullable=True),
        sa.Column("underwriting_result", sa.Float, nullable=True),
        sa.Column("investment_income", sa.Float, nullable=True),
        sa.Column("investment_yield_pct", sa.Float, nullable=True),
        sa.Column("total_investments", sa.Float, nullable=True),
        sa.Column("total_assets", sa.Float, nullable=True),
        sa.Column("total_equity", sa.Float, nullable=True),
        sa.Column("solvency_ratio_pct", sa.Float, nullable=True),
        sa.Column("minimum_capital_required", sa.Float, nullable=True),
        sa.Column("solvency_capital_required", sa.Float, nullable=True),
        sa.Column("ifrs17_adopted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("csm_balance", sa.Float, nullable=True),
        sa.Column("risk_adjustment", sa.Float, nullable=True),
        sa.Column("insurance_revenue", sa.Float, nullable=True),
        sa.Column("am_best_rating", sa.String(8), nullable=True),
        sa.Column("sp_rating", sa.String(8), nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.8"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("is_audited", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_ins_entity", "df_insurance_profiles", ["entity_id"])
    op.create_index("ix_df_ins_country", "df_insurance_profiles", ["country"])
    op.create_index("ix_df_ins_date", "df_insurance_profiles", ["reporting_date"])

    # ── df_logistics_nodes ───────────────────────────────────────────────
    op.create_table(
        "df_logistics_nodes",
        sa.Column("node_id", sa.String(64), primary_key=True),
        sa.Column("node_name", sa.String(256), nullable=False),
        sa.Column("node_name_ar", sa.String(256), nullable=True),
        sa.Column("country", sa.String(4), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("transport_mode", sa.String(32), nullable=False),
        sa.Column("port_type", sa.String(32), nullable=True),
        sa.Column("geo_lat", sa.Float, nullable=False),
        sa.Column("geo_lng", sa.Float, nullable=False),
        sa.Column("annual_capacity_teu", sa.Integer, nullable=True),
        sa.Column("annual_throughput_teu", sa.Integer, nullable=True),
        sa.Column("utilization_pct", sa.Float, nullable=True),
        sa.Column("annual_cargo_tonnage", sa.Float, nullable=True),
        sa.Column("vessel_calls_annual", sa.Integer, nullable=True),
        sa.Column("pax_annual", sa.Integer, nullable=True),
        sa.Column("connected_node_ids", postgresql.JSONB, nullable=True),
        sa.Column("chokepoint_dependency", sa.String(64), nullable=True),
        sa.Column("hinterland_coverage", postgresql.JSONB, nullable=True),
        sa.Column("operational_status", sa.String(32), nullable=False, server_default="'OPERATIONAL'"),
        sa.Column("criticality_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("last_disruption_date", sa.Date, nullable=True),
        sa.Column("operator", sa.String(256), nullable=True),
        sa.Column("free_zone_id", sa.String(64), nullable=True),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="0.8"),
        sa.Column("confidence_method", sa.String(64), nullable=False, server_default="'SOURCE_DECLARED'"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_log_country", "df_logistics_nodes", ["country"])
    op.create_index("ix_df_log_mode", "df_logistics_nodes", ["transport_mode"])

    # ── df_decision_rules ────────────────────────────────────────────────
    op.create_table(
        "df_decision_rules",
        sa.Column("rule_id", sa.String(128), primary_key=True),
        sa.Column("rule_name", sa.String(256), nullable=False),
        sa.Column("rule_name_ar", sa.String(256), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("conditions", postgresql.JSONB, nullable=False),
        sa.Column("condition_logic", sa.String(8), nullable=False, server_default="'AND'"),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("action_params", postgresql.JSONB, nullable=True),
        sa.Column("escalation_level", sa.String(32), nullable=False, server_default="'ELEVATED'"),
        sa.Column("applicable_countries", postgresql.JSONB, nullable=True),
        sa.Column("applicable_sectors", postgresql.JSONB, nullable=True),
        sa.Column("applicable_scenarios", postgresql.JSONB, nullable=True),
        sa.Column("requires_human_approval", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("cooldown_minutes", sa.Integer, nullable=False, server_default="60"),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_dataset_ids", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        # AuditMixin
        sa.Column("created_by", sa.String(128), nullable=True),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.Column("audit_notes", sa.Text, nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_rule_active", "df_decision_rules", ["is_active"])
    op.create_index("ix_df_rule_action", "df_decision_rules", ["action"])
    op.create_index("ix_df_rule_active_action", "df_decision_rules", ["is_active", "action"])

    # ── df_decision_logs ─────────────────────────────────────────────────
    op.create_table(
        "df_decision_logs",
        sa.Column("log_id", sa.String(128), primary_key=True),
        sa.Column("rule_id", sa.String(128), nullable=False),
        sa.Column("rule_version", sa.Integer, nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="'PROPOSED'"),
        sa.Column("trigger_context", postgresql.JSONB, nullable=False),
        sa.Column("country", sa.String(4), nullable=True),
        sa.Column("entity_ids", postgresql.JSONB, nullable=True),
        sa.Column("requires_approval", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_result", postgresql.JSONB, nullable=True),
        sa.Column("superseded_by", sa.String(128), nullable=True),
        sa.Column("audit_hash", sa.String(128), nullable=True),
        sa.Column("previous_log_hash", sa.String(128), nullable=True),
        *_foundation_cols(),
    )
    op.create_index("ix_df_dlog_rule", "df_decision_logs", ["rule_id"])
    op.create_index("ix_df_dlog_triggered", "df_decision_logs", ["triggered_at"])
    op.create_index("ix_df_dlog_action", "df_decision_logs", ["action"])
    op.create_index("ix_df_dlog_status", "df_decision_logs", ["status"])
    op.create_index("ix_df_dlog_rule_triggered", "df_decision_logs", ["rule_id", "triggered_at"])
    op.create_index("ix_df_dlog_status_action", "df_decision_logs", ["status", "action"])


def downgrade() -> None:
    tables = [
        "df_decision_logs",
        "df_decision_rules",
        "df_logistics_nodes",
        "df_insurance_profiles",
        "df_banking_profiles",
        "df_cbk_indicators",
        "df_fx_signals",
        "df_oil_energy_signals",
        "df_interest_rate_signals",
        "df_macro_indicators",
        "df_event_signals",
        "df_entity_registry",
    ]
    for t in tables:
        op.drop_table(t)
