"""
Banking Intelligence — Neo4j Graph Queries
============================================
Parameterized Cypher queries for the banking knowledge graph.
"""
from __future__ import annotations

from typing import Any, Optional


class BankingGraphQueries:
    """Read-only graph queries for banking intelligence."""

    def __init__(self, driver):
        self._driver = driver

    async def _run(self, cypher: str, **params) -> list[dict[str, Any]]:
        async with self._driver.session() as session:
            result = await session.run(cypher, **params)
            return [dict(record) async for record in result]

    # ── Entity Lookups ──────────────────────────────────────────────────

    async def get_entity(self, canonical_id: str) -> Optional[dict]:
        records = await self._run(
            "MATCH (n {canonical_id: $id}) RETURN properties(n) AS props",
            id=canonical_id,
        )
        return records[0]["props"] if records else None

    async def get_banks_by_country(self, country_code: str) -> list[dict]:
        return await self._run(
            "MATCH (b:Bank {country_code: $cc}) RETURN properties(b) AS props ORDER BY b.name_en",
            cc=country_code,
        )

    async def get_fintechs_by_country(self, country_code: str) -> list[dict]:
        return await self._run(
            "MATCH (f:Fintech {country_code: $cc}) RETURN properties(f) AS props ORDER BY f.name_en",
            cc=country_code,
        )

    async def get_authorities_by_country(self, country_code: str) -> list[dict]:
        return await self._run(
            "MATCH (a:Authority {country_code: $cc}) RETURN properties(a) AS props",
            cc=country_code,
        )

    # ── Regulatory Chain ────────────────────────────────────────────────

    async def get_regulated_entities(self, authority_id: str) -> list[dict]:
        """All entities regulated by a given authority."""
        return await self._run(
            """
            MATCH (a {canonical_id: $id})<-[:REGULATES]-(entity)
            RETURN properties(entity) AS props, labels(entity) AS labels
            """,
            id=authority_id,
        )

    async def get_regulators_of(self, entity_id: str) -> list[dict]:
        """All authorities that regulate a given entity."""
        return await self._run(
            """
            MATCH (entity {canonical_id: $id})-[:REGULATES]->(auth:Authority)
            RETURN properties(auth) AS props
            """,
            id=entity_id,
        )

    # ── Propagation Paths ───────────────────────────────────────────────

    async def get_propagation_paths_from(
        self, entity_id: str, max_hops: int = 5
    ) -> list[dict]:
        """All downstream propagation paths from an entity."""
        return await self._run(
            f"""
            MATCH path = (src {{canonical_id: $id}})-[:PROPAGATES_TO*1..{max_hops}]->(target)
            RETURN
                [n IN nodes(path) | n.canonical_id] AS node_ids,
                [r IN relationships(path) | properties(r)] AS edge_props,
                length(path) AS hops
            ORDER BY hops
            """,
            id=entity_id,
        )

    async def get_breakable_points_for_scenario(
        self, scenario_id: str
    ) -> list[dict]:
        """All intervention-ready breakable points for a scenario."""
        return await self._run(
            """
            MATCH (p:PropagationPath {scenario_id: $sid})
            WHERE p.breakable_point = true
            RETURN properties(p) AS props
            ORDER BY p.severity_transfer DESC
            """,
            sid=scenario_id,
        )

    # ── Decision Queries ────────────────────────────────────────────────

    async def get_decisions_by_scenario(
        self, scenario_id: str, status: Optional[str] = None
    ) -> list[dict]:
        where = "WHERE d.scenario_id = $sid"
        if status:
            where += " AND d.status = $status"
        return await self._run(
            f"""
            MATCH (d:DecisionContract)
            {where}
            OPTIONAL MATCH (d)-[:OWNED_BY]->(owner)
            OPTIONAL MATCH (d)-[:APPROVED_BY]->(approver)
            RETURN properties(d) AS decision,
                   owner.canonical_id AS owner_id,
                   approver.canonical_id AS approver_id
            ORDER BY d.created_at DESC
            """,
            sid=scenario_id,
            status=status,
        )

    async def get_decision_full_chain(self, decision_id: str) -> dict:
        """Get decision with all linked objects (counterfactual, review, audit)."""
        records = await self._run(
            """
            MATCH (d:DecisionContract {decision_id: $did})
            OPTIONAL MATCH (d)-[:HAS_COUNTERFACTUAL]->(cf)
            OPTIONAL MATCH (d)-[:HAS_OUTCOME_REVIEW]->(rev)
            OPTIONAL MATCH (d)-[:HAS_VALUE_AUDIT]->(va)
            OPTIONAL MATCH (d)-[:OWNED_BY]->(owner)
            RETURN
                properties(d) AS decision,
                properties(cf) AS counterfactual,
                properties(rev) AS outcome_review,
                properties(va) AS value_audit,
                owner.canonical_id AS owner_id
            """,
            did=decision_id,
        )
        return records[0] if records else {}

    # ── Exposure Analysis ───────────────────────────────────────────────

    async def get_exposures_for_entity(self, entity_id: str) -> list[dict]:
        return await self._run(
            """
            MATCH (e {canonical_id: $id})-[r:EXPOSED_TO]->(target)
            RETURN properties(r) AS edge, target.canonical_id AS target_id,
                   target.name_en AS target_name
            ORDER BY r.confidence DESC
            """,
            id=entity_id,
        )

    async def get_dependency_chain(
        self, entity_id: str, max_depth: int = 4
    ) -> list[dict]:
        return await self._run(
            f"""
            MATCH path = (src {{canonical_id: $id}})-[:DEPENDS_ON*1..{max_depth}]->(dep)
            RETURN
                [n IN nodes(path) | n.canonical_id] AS chain,
                [r IN relationships(path) | r.criticality] AS criticalities,
                length(path) AS depth
            ORDER BY depth
            """,
            id=entity_id,
        )

    # ── Cross-Country Analytics ─────────────────────────────────────────

    async def get_cross_border_payment_rails(self) -> list[dict]:
        return await self._run(
            """
            MATCH (r:PaymentRail)
            WHERE r.is_cross_border = true
            RETURN properties(r) AS props
            ORDER BY r.daily_volume_estimate_usd_millions DESC
            """
        )

    async def get_dsib_banks(self) -> list[dict]:
        return await self._run(
            """
            MATCH (b:Bank {bank_tier: 'DSIB'})
            RETURN properties(b) AS props
            ORDER BY b.total_assets_usd_millions DESC
            """
        )

    async def get_scenario_impact_surface(
        self, scenario_id: str
    ) -> list[dict]:
        """All entities exposed to a scenario trigger."""
        return await self._run(
            """
            MATCH (t:ScenarioTrigger {scenario_id: $sid})<-[:EXPOSED_TO]-(entity)
            RETURN entity.canonical_id AS entity_id,
                   entity.name_en AS name,
                   labels(entity) AS labels
            """,
            sid=scenario_id,
        )
