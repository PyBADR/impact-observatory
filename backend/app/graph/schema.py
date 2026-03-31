"""Neo4j graph schema definitions with constraints and indexes."""


class GraphSchema:
    """Manages Neo4j schema constraints and indexes for the GCC DIP."""

    @staticmethod
    def get_constraints() -> list[str]:
        """
        Get Cypher CREATE CONSTRAINT statements for node uniqueness.

        Returns:
            List of Cypher constraint creation statements.
        """
        return [
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT airport_icao_unique IF NOT EXISTS FOR (a:Airport) REQUIRE a.icao IS UNIQUE",
            "CREATE CONSTRAINT port_unlocode_unique IF NOT EXISTS FOR (p:Port) REQUIRE p.unlocode IS UNIQUE",
            "CREATE CONSTRAINT flight_id_unique IF NOT EXISTS FOR (f:Flight) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT vessel_mmsi_unique IF NOT EXISTS FOR (v:Vessel) REQUIRE v.mmsi IS UNIQUE",
            "CREATE CONSTRAINT actor_id_unique IF NOT EXISTS FOR (a:Actor) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT region_id_unique IF NOT EXISTS FOR (r:Region) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT corridor_id_unique IF NOT EXISTS FOR (c:Corridor) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT route_id_unique IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT scenario_id_unique IF NOT EXISTS FOR (s:Scenario) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
        ]

    @staticmethod
    def get_indexes() -> list[str]:
        """
        Get Cypher CREATE INDEX statements for performance optimization.

        Returns:
            List of Cypher index creation statements.
        """
        return [
            "CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.event_type)",
            "CREATE INDEX event_severity_idx IF NOT EXISTS FOR (e:Event) ON (e.severity)",
            "CREATE INDEX event_timestamp_idx IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
            "CREATE INDEX airport_location_idx IF NOT EXISTS FOR (a:Airport) ON (a.lat, a.lon)",
            "CREATE INDEX port_location_idx IF NOT EXISTS FOR (p:Port) ON (p.lat, p.lon)",
            "CREATE INDEX flight_status_idx IF NOT EXISTS FOR (f:Flight) ON (f.status)",
            "CREATE INDEX flight_departure_time_idx IF NOT EXISTS FOR (f:Flight) ON (f.departure_time)",
            "CREATE INDEX vessel_type_idx IF NOT EXISTS FOR (v:Vessel) ON (v.vessel_type)",
            "CREATE INDEX actor_type_idx IF NOT EXISTS FOR (a:Actor) ON (a.actor_type)",
            "CREATE INDEX region_name_idx IF NOT EXISTS FOR (r:Region) ON (r.name)",
        ]

    @staticmethod
    def get_full_schema_cypher() -> str:
        """
        Get complete schema DDL as single Cypher string.

        Returns:
            Concatenated Cypher string with all constraints and indexes.
        """
        constraints = GraphSchema.get_constraints()
        indexes = GraphSchema.get_indexes()
        all_statements = constraints + indexes
        return ";\n".join(all_statements) + ";"
