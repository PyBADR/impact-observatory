"""
Banking Intelligence — Neo4j Schema Definition
================================================
Defines node labels, relationship types, constraints, and indexes
for the banking + fintech knowledge graph.

Integrates with the existing graph/schema.py (20 node labels, 22 rel types)
by adding banking-specific labels and relationships.

All writes are idempotent (MERGE-based) using deterministic merge keys.
"""
from __future__ import annotations

from typing import Optional


# ─── Node Labels ────────────────────────────────────────────────────────────

BANKING_NODE_LABELS = [
    "BankingCountry",
    "Authority",
    "Bank",
    "Fintech",
    "PaymentRail",
    "ScenarioTrigger",
    "DecisionPlaybook",
    "DecisionContract",
    "CounterfactualAnalysis",
    "PropagationPath",
    "OutcomeReview",
    "ValueAudit",
]

# ─── Relationship Types ────────────────────────────────────────────────────

BANKING_RELATIONSHIP_TYPES = [
    "REGULATES",
    "OPERATES_IN",
    "DEPENDS_ON",
    "EXPOSED_TO",
    "PROPAGATES_TO",
    "HAS_PLAYBOOK",
    "TRIGGERS",
    "HAS_COUNTERFACTUAL",
    "HAS_OUTCOME_REVIEW",
    "HAS_VALUE_AUDIT",
    "OWNED_BY",
    "APPROVED_BY",
]

# ─── Constraint & Index Definitions ────────────────────────────────────────

BANKING_CONSTRAINTS: list[str] = [
    # Unique ID constraints for every node type
    "CREATE CONSTRAINT banking_country_id IF NOT EXISTS FOR (n:BankingCountry) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT authority_id IF NOT EXISTS FOR (n:Authority) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT bank_id IF NOT EXISTS FOR (n:Bank) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT fintech_id IF NOT EXISTS FOR (n:Fintech) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT payment_rail_id IF NOT EXISTS FOR (n:PaymentRail) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT scenario_trigger_id IF NOT EXISTS FOR (n:ScenarioTrigger) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT decision_playbook_id IF NOT EXISTS FOR (n:DecisionPlaybook) REQUIRE n.canonical_id IS UNIQUE",
    "CREATE CONSTRAINT decision_contract_id IF NOT EXISTS FOR (n:DecisionContract) REQUIRE n.decision_id IS UNIQUE",
    "CREATE CONSTRAINT counterfactual_id IF NOT EXISTS FOR (n:CounterfactualAnalysis) REQUIRE n.counterfactual_id IS UNIQUE",
    "CREATE CONSTRAINT propagation_id IF NOT EXISTS FOR (n:PropagationPath) REQUIRE n.propagation_id IS UNIQUE",
    "CREATE CONSTRAINT outcome_review_id IF NOT EXISTS FOR (n:OutcomeReview) REQUIRE n.review_id IS UNIQUE",
    "CREATE CONSTRAINT value_audit_id IF NOT EXISTS FOR (n:ValueAudit) REQUIRE n.audit_id IS UNIQUE",
    # Dedup key constraints
    "CREATE CONSTRAINT bank_dedup IF NOT EXISTS FOR (n:Bank) REQUIRE n.dedup_key IS UNIQUE",
    "CREATE CONSTRAINT fintech_dedup IF NOT EXISTS FOR (n:Fintech) REQUIRE n.dedup_key IS UNIQUE",
    "CREATE CONSTRAINT authority_dedup IF NOT EXISTS FOR (n:Authority) REQUIRE n.dedup_key IS UNIQUE",
]

BANKING_INDEXES: list[str] = [
    # Performance indexes for common query patterns
    "CREATE INDEX bank_country IF NOT EXISTS FOR (n:Bank) ON (n.country_code)",
    "CREATE INDEX bank_tier IF NOT EXISTS FOR (n:Bank) ON (n.bank_tier)",
    "CREATE INDEX bank_swift IF NOT EXISTS FOR (n:Bank) ON (n.swift_code)",
    "CREATE INDEX fintech_country IF NOT EXISTS FOR (n:Fintech) ON (n.country_code)",
    "CREATE INDEX fintech_category IF NOT EXISTS FOR (n:Fintech) ON (n.category)",
    "CREATE INDEX authority_country IF NOT EXISTS FOR (n:Authority) ON (n.country_code)",
    "CREATE INDEX authority_type IF NOT EXISTS FOR (n:Authority) ON (n.authority_type)",
    "CREATE INDEX payment_rail_type IF NOT EXISTS FOR (n:PaymentRail) ON (n.rail_type)",
    "CREATE INDEX decision_status IF NOT EXISTS FOR (n:DecisionContract) ON (n.status)",
    "CREATE INDEX decision_scenario IF NOT EXISTS FOR (n:DecisionContract) ON (n.scenario_id)",
    "CREATE INDEX trigger_scenario IF NOT EXISTS FOR (n:ScenarioTrigger) ON (n.scenario_id)",
]


# ─── Schema Initialization ─────────────────────────────────────────────────

async def init_banking_schema(driver) -> dict[str, int]:
    """
    Apply all constraints and indexes for the banking intelligence graph.
    Idempotent — safe to call on every startup.

    Returns: {"constraints_applied": N, "indexes_applied": M}
    """
    constraints_applied = 0
    indexes_applied = 0

    async with driver.session() as session:
        for cypher in BANKING_CONSTRAINTS:
            try:
                await session.run(cypher)
                constraints_applied += 1
            except Exception:
                pass  # Constraint already exists

        for cypher in BANKING_INDEXES:
            try:
                await session.run(cypher)
                indexes_applied += 1
            except Exception:
                pass  # Index already exists

    return {
        "constraints_applied": constraints_applied,
        "indexes_applied": indexes_applied,
    }
