"""
Neo4j graph database client module.

Provides async Neo4j connectivity for Impact Observatory platform.
Graceful degradation — runs in offline mode if neo4j driver unavailable.
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "decision_core_2024")


class Neo4jClient:
    """
    Async Neo4j client with connection pooling.

    Falls back to offline mode if neo4j driver is not installed or connection fails.
    """

    def __init__(
        self,
        uri: str = NEO4J_URI,
        user: str = NEO4J_USER,
        password: str = NEO4J_PASSWORD,
        database: str = "neo4j",
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver = None

    async def connect(self):
        """Connect to Neo4j. Graceful fallback on failure."""
        try:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
        except ImportError:
            logger.warning("neo4j driver not installed — running in offline mode")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e} — running in offline mode")

    async def close(self):
        """Close driver connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute a Cypher query and return results as list of dicts."""
        if not self._driver:
            logger.debug("Neo4j offline — returning empty results")
            return []
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]

    async def execute_write(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """Execute a write Cypher query."""
        if not self._driver:
            logger.debug("Neo4j offline — write skipped")
            return []
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]

    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j connectivity."""
        if not self._driver:
            return {"status": "offline", "message": "Neo4j driver not connected"}
        try:
            records = await self.execute_query("RETURN 1 AS ok")
            return {"status": "healthy", "result": records}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @property
    def connected(self) -> bool:
        return self._driver is not None


# Module-level singleton
neo4j_client = Neo4jClient()


async def get_neo4j_client() -> Neo4jClient:
    """FastAPI dependency to get Neo4j client."""
    return neo4j_client
