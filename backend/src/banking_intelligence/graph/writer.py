"""
Banking Intelligence — Neo4j Graph Writer
==========================================
Deterministic, idempotent graph writes using MERGE with dedup keys.

Design rules:
  - Every write uses MERGE, never CREATE (idempotent)
  - Merge keys are deterministic (computed from entity/edge properties)
  - Timestamps auto-update on every write
  - All writes are parameterized (no string interpolation in Cypher)
  - Batch writes use UNWIND for performance
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from src.banking_intelligence.schemas.entities import (
    BaseEntity,
    Country,
    Authority,
    Bank,
    Fintech,
    PaymentRail,
    ScenarioTrigger,
    DecisionPlaybook,
)
from src.banking_intelligence.schemas.edges import (
    BaseEdge,
    EdgeType,
)
from src.banking_intelligence.schemas.decision_contract import DecisionContract
from src.banking_intelligence.schemas.counterfactual import CounterfactualContract
from src.banking_intelligence.schemas.propagation import PropagationContract
from src.banking_intelligence.schemas.outcome_review import (
    OutcomeReviewContract,
    DecisionValueAudit,
)


# ─── Entity Label Mapping ──────────────────────────────────────────────────

ENTITY_LABEL_MAP: dict[str, str] = {
    "country": "BankingCountry",
    "authority": "Authority",
    "bank": "Bank",
    "fintech": "Fintech",
    "payment_rail": "PaymentRail",
    "scenario_trigger": "ScenarioTrigger",
    "decision_playbook": "DecisionPlaybook",
}


def _entity_type_from_id(canonical_id: str) -> str:
    """Extract entity type prefix from canonical_id."""
    prefix = canonical_id.split(":")[0]
    type_map = {
        "country": "country",
        "authority": "authority",
        "bank": "bank",
        "fintech": "fintech",
        "rail": "payment_rail",
        "trigger": "scenario_trigger",
        "playbook": "decision_playbook",
    }
    return type_map.get(prefix, prefix)


def _serialize_for_neo4j(entity: BaseEntity) -> dict[str, Any]:
    """
    Serialize a Pydantic model to a flat dict suitable for Neo4j properties.
    Nested objects become JSON strings. Lists of primitives stay as lists.
    """
    data = entity.model_dump(mode="json")
    flat: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            import json
            flat[key] = json.dumps(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            import json
            flat[key] = json.dumps(value)
        else:
            flat[key] = value
    flat["_updated_at"] = datetime.now(timezone.utc).isoformat()
    return flat


# ─── Node Writer ────────────────────────────────────────────────────────────

class BankingGraphWriter:
    """
    Writes banking intelligence entities and edges to Neo4j.
    All operations are idempotent via MERGE on deterministic keys.
    """

    def __init__(self, driver):
        self._driver = driver

    # ── Single Entity Write ─────────────────────────────────────────────

    async def write_entity(self, entity: BaseEntity) -> str:
        """
        MERGE a single entity node into Neo4j.
        Returns the canonical_id of the merged node.
        """
        entity_type = _entity_type_from_id(entity.canonical_id)
        label = ENTITY_LABEL_MAP.get(entity_type)
        if not label:
            raise ValueError(f"Unknown entity type for canonical_id: {entity.canonical_id}")

        props = _serialize_for_neo4j(entity)
        cypher = f"""
        MERGE (n:{label} {{canonical_id: $canonical_id}})
        SET n += $props
        RETURN n.canonical_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                canonical_id=entity.canonical_id,
                props=props,
            )
            record = await result.single()
            return record["id"] if record else entity.canonical_id

    # ── Batch Entity Write ──────────────────────────────────────────────

    async def write_entities_batch(
        self, entities: list[BaseEntity], label: str
    ) -> int:
        """
        Batch MERGE multiple entities of the same label.
        Returns count of merged nodes.
        """
        if not entities:
            return 0

        rows = [_serialize_for_neo4j(e) for e in entities]
        cypher = f"""
        UNWIND $rows AS row
        MERGE (n:{label} {{canonical_id: row.canonical_id}})
        SET n += row
        RETURN count(n) AS cnt
        """

        async with self._driver.session() as session:
            result = await session.run(cypher, rows=rows)
            record = await result.single()
            return record["cnt"] if record else 0

    # ── Edge Write ──────────────────────────────────────────────────────

    async def write_edge(self, edge: BaseEdge) -> str:
        """
        MERGE an edge between two existing nodes.
        Uses merge_key for idempotency.
        Returns the merge_key.
        """
        from_type = _entity_type_from_id(edge.from_entity_id)
        to_type = _entity_type_from_id(edge.to_entity_id)
        from_label = ENTITY_LABEL_MAP.get(from_type, from_type)
        to_label = ENTITY_LABEL_MAP.get(to_type, to_type)

        # Serialize edge properties (exclude from/to IDs and type)
        edge_data = edge.model_dump(mode="json")
        edge_props = {
            k: v for k, v in edge_data.items()
            if k not in ("from_entity_id", "to_entity_id", "edge_type")
        }
        # Flatten nested structures
        for key, value in list(edge_props.items()):
            if isinstance(value, (dict, list)):
                import json
                edge_props[key] = json.dumps(value)
        edge_props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        rel_type = edge.edge_type.value
        cypher = f"""
        MATCH (a {{canonical_id: $from_id}})
        MATCH (b {{canonical_id: $to_id}})
        MERGE (a)-[r:{rel_type} {{merge_key: $merge_key}}]->(b)
        SET r += $props
        RETURN r.merge_key AS key
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                from_id=edge.from_entity_id,
                to_id=edge.to_entity_id,
                merge_key=edge.merge_key,
                props=edge_props,
            )
            record = await result.single()
            return record["key"] if record else edge.merge_key

    # ── Batch Edge Write ────────────────────────────────────────────────

    async def write_edges_batch(
        self, edges: list[BaseEdge], rel_type: str
    ) -> int:
        """
        Batch MERGE edges of the same relationship type.
        Returns count of merged relationships.
        """
        if not edges:
            return 0

        rows = []
        for edge in edges:
            edge_data = edge.model_dump(mode="json")
            props = {
                k: v for k, v in edge_data.items()
                if k not in ("from_entity_id", "to_entity_id", "edge_type")
            }
            for key, value in list(props.items()):
                if isinstance(value, (dict, list)):
                    import json
                    props[key] = json.dumps(value)
            props["_updated_at"] = datetime.now(timezone.utc).isoformat()
            rows.append({
                "from_id": edge.from_entity_id,
                "to_id": edge.to_entity_id,
                "merge_key": edge.merge_key,
                "props": props,
            })

        cypher = f"""
        UNWIND $rows AS row
        MATCH (a {{canonical_id: row.from_id}})
        MATCH (b {{canonical_id: row.to_id}})
        MERGE (a)-[r:{rel_type} {{merge_key: row.merge_key}}]->(b)
        SET r += row.props
        RETURN count(r) AS cnt
        """

        async with self._driver.session() as session:
            result = await session.run(cypher, rows=rows)
            record = await result.single()
            return record["cnt"] if record else 0

    # ── Decision Contract Write ─────────────────────────────────────────

    async def write_decision_contract(self, contract: DecisionContract) -> str:
        """MERGE a DecisionContract node and link to owner/approver."""
        props = contract.model_dump(mode="json")
        # Flatten complex fields
        for key in ("dependencies", "rollback_plan", "observation_plan", "status_history"):
            if key in props and isinstance(props[key], (dict, list)):
                import json
                props[key] = json.dumps(props[key])
        props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (d:DecisionContract {decision_id: $decision_id})
        SET d += $props
        WITH d
        OPTIONAL MATCH (owner {canonical_id: $owner_id})
        FOREACH (_ IN CASE WHEN owner IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:OWNED_BY]->(owner)
        )
        WITH d
        OPTIONAL MATCH (approver {canonical_id: $approver_id})
        FOREACH (_ IN CASE WHEN approver IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:APPROVED_BY]->(approver)
        )
        RETURN d.decision_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                decision_id=contract.decision_id,
                props=props,
                owner_id=contract.primary_owner_id,
                approver_id=contract.approver_id,
            )
            record = await result.single()
            return record["id"] if record else contract.decision_id

    # ── Counterfactual Write ────────────────────────────────────────────

    async def write_counterfactual(self, cf: CounterfactualContract) -> str:
        """MERGE a CounterfactualAnalysis node and link to decision."""
        props = cf.model_dump(mode="json")
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                import json
                props[key] = json.dumps(value)
        props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (cf:CounterfactualAnalysis {counterfactual_id: $cf_id})
        SET cf += $props
        WITH cf
        OPTIONAL MATCH (d:DecisionContract {decision_id: $decision_id})
        FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:HAS_COUNTERFACTUAL]->(cf)
        )
        RETURN cf.counterfactual_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                cf_id=cf.counterfactual_id,
                props=props,
                decision_id=cf.decision_id,
            )
            record = await result.single()
            return record["id"] if record else cf.counterfactual_id

    # ── Propagation Write ───────────────────────────────────────────────

    async def write_propagation(self, prop: PropagationContract) -> str:
        """MERGE a PropagationPath node and link from/to entities."""
        props = prop.model_dump(mode="json")
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                import json
                props[key] = json.dumps(value)
        props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (p:PropagationPath {propagation_id: $prop_id})
        SET p += $props
        WITH p
        OPTIONAL MATCH (src {canonical_id: $from_id})
        OPTIONAL MATCH (tgt {canonical_id: $to_id})
        FOREACH (_ IN CASE WHEN src IS NOT NULL THEN [1] ELSE [] END |
            MERGE (src)-[:PROPAGATES_TO {propagation_id: $prop_id}]->(tgt)
        )
        RETURN p.propagation_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                prop_id=prop.propagation_id,
                props=props,
                from_id=prop.from_entity_id,
                to_id=prop.to_entity_id,
            )
            record = await result.single()
            return record["id"] if record else prop.propagation_id

    # ── Outcome Review Write ────────────────────────────────────────────

    async def write_outcome_review(self, review: OutcomeReviewContract) -> str:
        """MERGE an OutcomeReview node and link to decision."""
        props = review.model_dump(mode="json")
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                import json
                props[key] = json.dumps(value)
        props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (r:OutcomeReview {review_id: $review_id})
        SET r += $props
        WITH r
        OPTIONAL MATCH (d:DecisionContract {decision_id: $decision_id})
        FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:HAS_OUTCOME_REVIEW]->(r)
        )
        RETURN r.review_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                review_id=review.review_id,
                props=props,
                decision_id=review.decision_id,
            )
            record = await result.single()
            return record["id"] if record else review.review_id

    # ── Value Audit Write ───────────────────────────────────────────────

    async def write_value_audit(self, audit: DecisionValueAudit) -> str:
        """MERGE a ValueAudit node and link to decision + outcome review."""
        props = audit.model_dump(mode="json")
        for key, value in list(props.items()):
            if isinstance(value, (dict, list)):
                import json
                props[key] = json.dumps(value)
        props["_updated_at"] = datetime.now(timezone.utc).isoformat()

        cypher = """
        MERGE (a:ValueAudit {audit_id: $audit_id})
        SET a += $props
        WITH a
        OPTIONAL MATCH (d:DecisionContract {decision_id: $decision_id})
        FOREACH (_ IN CASE WHEN d IS NOT NULL THEN [1] ELSE [] END |
            MERGE (d)-[:HAS_VALUE_AUDIT]->(a)
        )
        WITH a
        OPTIONAL MATCH (r:OutcomeReview {review_id: $review_id})
        FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
            MERGE (r)-[:HAS_VALUE_AUDIT]->(a)
        )
        RETURN a.audit_id AS id
        """

        async with self._driver.session() as session:
            result = await session.run(
                cypher,
                audit_id=audit.audit_id,
                props=props,
                decision_id=audit.decision_id,
                review_id=audit.outcome_review_id,
            )
            record = await result.single()
            return record["id"] if record else audit.audit_id
