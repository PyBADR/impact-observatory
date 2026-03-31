"""Neo4j async driver wrapper for GCC DIP graph operations."""

import logging
from typing import Any, Optional
from dataclasses import asdict

from neo4j import AsyncDriver, AsyncSession, basic_auth, NotFound
from neo4j.exceptions import (
    Neo4jError,
    ClientError,
    ServiceUnavailable,
    SessionExpired,
)

logger = logging.getLogger(__name__)


class GraphClient:
    """Async Neo4j driver wrapper with connection pooling and error handling."""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j async driver.

        Args:
            uri: Neo4j connection URI (e.g., 'neo4j+s://hostname:7687')
            user: Neo4j username
            password: Neo4j password

        Raises:
            ServiceUnavailable: If Neo4j is unreachable
        """
        logger.debug(f"Initializing GraphClient with URI: {uri}")
        self.uri = uri
        self.user = user
        self._driver: Optional[AsyncDriver] = None

        try:
            self._driver = AsyncDriver(
                uri=uri,
                auth=basic_auth(user, password),
                max_connection_pool_size=50,
                connection_timeout=30.0,
                trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
            )
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j at {uri}: {e}")
            raise

    async def initialize_schema(self) -> None:
        """
        Initialize database schema with constraints and indexes.

        Executes all constraint and index creation statements.
        Safe to call multiple times (uses IF NOT EXISTS).

        Raises:
            Neo4jError: If schema initialization fails
        """
        from .schema import GraphSchema

        schema = GraphSchema()
        statements = schema.get_constraints() + schema.get_indexes()

        async with self._driver.session() as session:
            for statement in statements:
                try:
                    logger.debug(f"Executing schema statement: {statement[:100]}...")
                    await session.run(statement)
                except ClientError as e:
                    logger.warning(f"Schema statement failed (may already exist): {e}")
                except Neo4jError as e:
                    logger.error(f"Failed to initialize schema: {e}")
                    raise

        logger.info(f"Schema initialization complete: {len(statements)} statements executed")

    async def create_node(self, node: Any) -> str:
        """
        Create or merge a node in the graph.

        Args:
            node: Dataclass instance with label() and to_cypher_properties() methods

        Returns:
            ID of created/merged node

        Raises:
            Neo4jError: If node creation fails
        """
        label = node.label()
        props = node.to_cypher_properties()
        node_id = props.get("id")

        cypher = f"""
MERGE (n:{label} {{id: $id}})
SET n += $props
RETURN n.id AS id
"""
        params = {"id": node_id, "props": props}

        logger.debug(f"Creating node: {label}[id={node_id}]")

        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, params)
                record = await result.single()
                return record["id"] if record else node_id
        except (Neo4jError, SessionExpired) as e:
            logger.error(f"Failed to create node {label}[{node_id}]: {e}")
            raise

    async def create_edge(self, edge: Any) -> None:
        """
        Create or merge a relationship in the graph.

        Args:
            edge: Dataclass instance with to_merge_cypher() and to_cypher_properties() methods

        Raises:
            Neo4jError: If relationship creation fails
        """
        rel_type = edge.rel_type()
        props = edge.to_cypher_properties()

        # Extract IDs from edge dataclass fields
        edge_dict = asdict(edge)
        # Filter out non-ID fields to get source and destination IDs
        id_fields = [k for k in edge_dict.keys() if k.endswith("_id")]

        if len(id_fields) < 2:
            logger.warning(f"Edge {rel_type} missing source/destination IDs")
            return

        src_id_field = id_fields[0]
        dst_id_field = id_fields[1]
        src_id = edge_dict[src_id_field]
        dst_id = edge_dict[dst_id_field]

        # Build dynamic cypher based on edge type
        props_clause = ""
        if props:
            props_str = ", ".join(f"{k}: ${k}" for k in props.keys())
            props_clause = f" {{{props_str}}}"

        # Simple MERGE for any node type
        cypher = f"""
MATCH (src {{id: ${src_id_field}}})
MATCH (dst {{id: ${dst_id_field}}})
MERGE (src)-[r:{rel_type}{props_clause}]->(dst)
RETURN r
"""

        params = {src_id_field: src_id, dst_id_field: dst_id}
        params.update(props)

        logger.debug(f"Creating edge: {rel_type}[{src_id}->{dst_id}]")

        try:
            async with self._driver.session() as session:
                await session.run(cypher, params)
        except (Neo4jError, SessionExpired) as e:
            logger.error(f"Failed to create edge {rel_type}: {e}")
            raise

    async def run_query(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        """
        Execute a Cypher query and return results as list of dicts.

        Args:
            cypher: Cypher query string (with $param placeholders)
            params: Parameter dictionary for parameterized queries

        Returns:
            List of result records as dictionaries

        Raises:
            Neo4jError: If query execution fails
        """
        if params is None:
            params = {}

        logger.debug(f"Executing query: {cypher[:200]}... with params: {params}")

        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, params)
                records = await result.data()
                logger.debug(f"Query returned {len(records)} records")
                return records
        except (Neo4jError, SessionExpired) as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def close(self) -> None:
        """
        Close the Neo4j driver and release connections.

        Must be called when the client is no longer needed.
        """
        if self._driver:
            logger.debug("Closing Neo4j driver")
            await self._driver.close()
            self._driver = None
            logger.info("GraphClient closed successfully")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
