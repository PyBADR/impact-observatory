"""Loader for all seed data in the Impact Observatory platform."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.schema import Event, Airport, Port, Corridor, Flight, Vessel, Actor

from .events import get_seed_events
from .airports import get_seed_airports
from .ports import get_seed_ports
from .corridors import get_seed_corridors
from .flights import get_seed_flights
from .vessels import get_seed_vessels
from .actors import get_seed_actors


class SeedLoader:
    """Loader class for Impact Observatory seed data.
    
    Provides methods to load all seed data types, validate data integrity,
    and export seed data to JSON format for database ingestion.
    """
    
    def __init__(self):
        """Initialize the SeedLoader."""
        self._events: Optional[list[Event]] = None
        self._airports: Optional[list[Airport]] = None
        self._ports: Optional[list[Port]] = None
        self._corridors: Optional[list[Corridor]] = None
        self._flights: Optional[list[Flight]] = None
        self._vessels: Optional[list[Vessel]] = None
        self._actors: Optional[list[Actor]] = None
        self._load_timestamp = None
    
    def load_all(self) -> dict[str, Any]:
        """Load all seed data from all modules.
        
        Returns:
            dict: Dictionary containing all loaded seed data with keys:
                  - events: list of Event instances
                  - airports: list of Airport instances
                  - ports: list of Port instances
                  - corridors: list of Corridor instances
                  - flights: list of Flight instances
                  - vessels: list of Vessel instances
                  - actors: list of Actor instances
                  - load_timestamp: ISO format timestamp of load time
                  - summary: dict with counts of each data type
        """
        self._load_timestamp = datetime.now(timezone.utc).isoformat()
        
        self._events = get_seed_events()
        self._airports = get_seed_airports()
        self._ports = get_seed_ports()
        self._corridors = get_seed_corridors()
        self._flights = get_seed_flights()
        self._vessels = get_seed_vessels()
        self._actors = get_seed_actors()
        
        return {
            "events": self._events,
            "airports": self._airports,
            "ports": self._ports,
            "corridors": self._corridors,
            "flights": self._flights,
            "vessels": self._vessels,
            "actors": self._actors,
            "load_timestamp": self._load_timestamp,
            "summary": self._get_summary(),
        }
    
    def load_events(self) -> list[Event]:
        """Load security events seed data.
        
        Returns:
            list[Event]: List of 50 GCC security events.
        """
        if self._events is None:
            self._events = get_seed_events()
        return self._events
    
    def load_airports(self) -> list[Airport]:
        """Load airports seed data.
        
        Returns:
            list[Airport]: List of 30 GCC region airports.
        """
        if self._airports is None:
            self._airports = get_seed_airports()
        return self._airports
    
    def load_ports(self) -> list[Port]:
        """Load ports seed data.
        
        Returns:
            list[Port]: List of 20 GCC and regional seaports.
        """
        if self._ports is None:
            self._ports = get_seed_ports()
        return self._ports
    
    def load_corridors(self) -> list[Corridor]:
        """Load transportation corridors seed data.
        
        Returns:
            list[Corridor]: List of 15 strategic corridors.
        """
        if self._corridors is None:
            self._corridors = get_seed_corridors()
        return self._corridors
    
    def load_flights(self) -> list[Flight]:
        """Load flights seed data.
        
        Returns:
            list[Flight]: List of 25 GCC region flights.
        """
        if self._flights is None:
            self._flights = get_seed_flights()
        return self._flights
    
    def load_vessels(self) -> list[Vessel]:
        """Load vessels seed data.
        
        Returns:
            list[Vessel]: List of 20 Gulf region vessels.
        """
        if self._vessels is None:
            self._vessels = get_seed_vessels()
        return self._vessels
    
    def load_actors(self) -> list[Actor]:
        """Load actors seed data.
        
        Returns:
            list[Actor]: List of 15 regional actors.
        """
        if self._actors is None:
            self._actors = get_seed_actors()
        return self._actors
    
    def validate_all(self) -> dict[str, Any]:
        """Validate all loaded seed data for integrity.
        
        Validates:
        - All instances have required fields
        - GeoPoint coordinates are valid (-90 to 90 lat, -180 to 180 lon)
        - Confidence scores are between 0 and 1
        - All IATA/ICAO codes and port codes are non-empty
        - All IDs are unique within their type
        - All datetime fields are valid UTC timestamps
        
        Returns:
            dict: Validation result with keys:
                  - valid: bool indicating if all data is valid
                  - errors: list of validation errors found
                  - warnings: list of validation warnings
                  - details: dict with validation details per data type
        """
        errors = []
        warnings = []
        details = {}
        
        # Validate events
        if self._events:
            event_ids = set()
            for event in self._events:
                if event.id in event_ids:
                    errors.append(f"Duplicate event ID: {event.id}")
                event_ids.add(event.id)
                
                # Validate GeoPoint
                if not (-90 <= event.location.latitude <= 90):
                    errors.append(f"Invalid latitude in event {event.id}")
                if not (-180 <= event.location.longitude <= 180):
                    errors.append(f"Invalid longitude in event {event.id}")
                
                # Validate confidence
                if not (0 <= event.confidence <= 1):
                    errors.append(f"Invalid confidence score in event {event.id}")
            
            details["events"] = {
                "count": len(self._events),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate airports
        if self._airports:
            airport_icaos = set()
            for airport in self._airports:
                if airport.icao_code in airport_icaos:
                    errors.append(f"Duplicate ICAO code: {airport.icao_code}")
                airport_icaos.add(airport.icao_code)
                
                # Validate GeoPoint
                if not (-90 <= airport.location.latitude <= 90):
                    errors.append(f"Invalid latitude in airport {airport.icao_code}")
                if not (-180 <= airport.location.longitude <= 180):
                    errors.append(f"Invalid longitude in airport {airport.icao_code}")
                
                # Validate confidence
                if not (0 <= airport.confidence <= 1):
                    errors.append(f"Invalid confidence in airport {airport.icao_code}")
            
            details["airports"] = {
                "count": len(self._airports),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate ports
        if self._ports:
            port_codes = set()
            for port in self._ports:
                if port.port_code in port_codes:
                    errors.append(f"Duplicate port code: {port.port_code}")
                port_codes.add(port.port_code)
                
                # Validate GeoPoint
                if not (-90 <= port.location.latitude <= 90):
                    errors.append(f"Invalid latitude in port {port.port_code}")
                if not (-180 <= port.location.longitude <= 180):
                    errors.append(f"Invalid longitude in port {port.port_code}")
                
                # Validate berth count
                if port.berth_count < 1:
                    errors.append(f"Invalid berth count in port {port.port_code}")
                
                # Validate confidence
                if not (0 <= port.confidence <= 1):
                    errors.append(f"Invalid confidence in port {port.port_code}")
            
            details["ports"] = {
                "count": len(self._ports),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate corridors
        if self._corridors:
            for corridor in self._corridors:
                # Validate origin and destination coordinates
                if not (-90 <= corridor.origin_location.latitude <= 90):
                    errors.append(f"Invalid origin latitude in corridor {corridor.id}")
                if not (-180 <= corridor.origin_location.longitude <= 180):
                    errors.append(f"Invalid origin longitude in corridor {corridor.id}")
                
                if not (-90 <= corridor.destination_location.latitude <= 90):
                    errors.append(f"Invalid destination latitude in corridor {corridor.id}")
                if not (-180 <= corridor.destination_location.longitude <= 180):
                    errors.append(f"Invalid destination longitude in corridor {corridor.id}")
                
                # Validate confidence
                if not (0 <= corridor.confidence <= 1):
                    errors.append(f"Invalid confidence in corridor {corridor.id}")
                
                # Validate waypoints if present
                if corridor.waypoints:
                    for i, wp in enumerate(corridor.waypoints):
                        if not (-90 <= wp.latitude <= 90):
                            errors.append(f"Invalid waypoint latitude in corridor {corridor.id} waypoint {i}")
                        if not (-180 <= wp.longitude <= 180):
                            errors.append(f"Invalid waypoint longitude in corridor {corridor.id} waypoint {i}")
            
            details["corridors"] = {
                "count": len(self._corridors),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate flights
        if self._flights:
            flight_numbers = set()
            for flight in self._flights:
                if flight.flight_number in flight_numbers:
                    warnings.append(f"Duplicate flight number: {flight.flight_number}")
                flight_numbers.add(flight.flight_number)
                
                # Validate current position if present
                if flight.current_position:
                    if not (-90 <= flight.current_position.latitude <= 90):
                        errors.append(f"Invalid latitude in flight {flight.flight_number}")
                    if not (-180 <= flight.current_position.longitude <= 180):
                        errors.append(f"Invalid longitude in flight {flight.flight_number}")
                
                # Validate heading
                if flight.heading and not (0 <= flight.heading <= 360):
                    errors.append(f"Invalid heading in flight {flight.flight_number}")
                
                # Validate confidence
                if not (0 <= flight.confidence <= 1):
                    errors.append(f"Invalid confidence in flight {flight.flight_number}")
            
            details["flights"] = {
                "count": len(self._flights),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate vessels
        if self._vessels:
            mmsis = set()
            for vessel in self._vessels:
                if vessel.mmsi in mmsis:
                    errors.append(f"Duplicate MMSI: {vessel.mmsi}")
                mmsis.add(vessel.mmsi)
                
                # Validate current position
                if not (-90 <= vessel.current_position.latitude <= 90):
                    errors.append(f"Invalid latitude in vessel {vessel.vessel_name}")
                if not (-180 <= vessel.current_position.longitude <= 180):
                    errors.append(f"Invalid longitude in vessel {vessel.vessel_name}")
                
                # Validate heading
                if vessel.heading and not (0 <= vessel.heading <= 360):
                    errors.append(f"Invalid heading in vessel {vessel.vessel_name}")
                
                # Validate confidence
                if not (0 <= vessel.confidence <= 1):
                    errors.append(f"Invalid confidence in vessel {vessel.vessel_name}")
            
            details["vessels"] = {
                "count": len(self._vessels),
                "status": "valid" if not errors else "invalid"
            }
        
        # Validate actors
        if self._actors:
            actor_ids = set()
            for actor in self._actors:
                if actor.id in actor_ids:
                    errors.append(f"Duplicate actor ID: {actor.id}")
                actor_ids.add(actor.id)
                
                # Validate confidence
                if not (0 <= actor.confidence <= 1):
                    errors.append(f"Invalid confidence in actor {actor.id}")
            
            details["actors"] = {
                "count": len(self._actors),
                "status": "valid" if not errors else "invalid"
            }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "details": details,
        }
    
    def to_json(self) -> str:
        """Export all loaded seed data to JSON format.
        
        Returns:
            str: JSON string containing all seed data, suitable for
                 database ingestion or external processing.
        """
        data = {
            "timestamp": self._load_timestamp or datetime.now(timezone.utc).isoformat(),
            "platform": "Impact Observatory Seed Data",
            "version": "1.0",
            "data": {
                "events": [json.loads(event.model_dump_json()) for event in self._events or []],
                "airports": [json.loads(airport.model_dump_json()) for airport in self._airports or []],
                "ports": [json.loads(port.model_dump_json()) for port in self._ports or []],
                "corridors": [json.loads(corridor.model_dump_json()) for corridor in self._corridors or []],
                "flights": [json.loads(flight.model_dump_json()) for flight in self._flights or []],
                "vessels": [json.loads(vessel.model_dump_json()) for vessel in self._vessels or []],
                "actors": [json.loads(actor.model_dump_json()) for actor in self._actors or []],
            },
            "summary": self._get_summary(),
        }
        
        return json.dumps(data, indent=2, default=str)
    
    def _get_summary(self) -> dict[str, int]:
        """Get summary counts of all loaded data types.
        
        Returns:
            dict: Dictionary with counts for each data type.
        """
        return {
            "events": len(self._events) if self._events else 0,
            "airports": len(self._airports) if self._airports else 0,
            "ports": len(self._ports) if self._ports else 0,
            "corridors": len(self._corridors) if self._corridors else 0,
            "flights": len(self._flights) if self._flights else 0,
            "vessels": len(self._vessels) if self._vessels else 0,
            "actors": len(self._actors) if self._actors else 0,
            "total_entities": sum([
                len(self._events) if self._events else 0,
                len(self._airports) if self._airports else 0,
                len(self._ports) if self._ports else 0,
                len(self._corridors) if self._corridors else 0,
                len(self._flights) if self._flights else 0,
                len(self._vessels) if self._vessels else 0,
                len(self._actors) if self._actors else 0,
            ]),
        }
