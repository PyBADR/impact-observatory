"""
Pytest configuration and shared fixtures for Impact Observatory tests.

This module provides reusable fixtures for:
- Sample event data (geospatial)
- Airport and port entities
- Trade corridor definitions
- Flight and vessel operational data
- Actor information
- Scenario templates
- Risk scoring weights
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4


# ============================================================================
# Event Fixtures
# ============================================================================

@pytest.fixture
def seed_event_base() -> Dict[str, Any]:
    """Base event data structure with all required fields."""
    return {
        "event_id": f"EVT-{uuid4().hex[:12].upper()}",
        "event_date": datetime.utcnow(),
        "event_type": "violence_against_civilians",
        "location_name": "Aleppo, Syria",
        "country": "SY",
        "admin1": "Aleppo Governorate",
        "admin2": "Aleppo District",
        "latitude": 36.2021,
        "longitude": 37.1670,
        "fatalities": 5,
        "wounded": 12,
        "description": "Armed conflict incident in urban area",
        "source_id": "ACLED-2024-001",
        "source_type": "ACLED",
        "confidence": 0.95,
        "tags": ["violence", "civilian_harm", "armed_conflict"],
        "provenance": {"source_url": "https://example.com/event", "collected_date": datetime.utcnow().isoformat()},
    }


@pytest.fixture
def seed_events(seed_event_base) -> List[Dict[str, Any]]:
    """Generate 5 sample events across different regions and types."""
    events = []
    event_configs = [
        {
            "event_type": "violence_against_civilians",
            "location_name": "Damascus, Syria",
            "country": "SY",
            "latitude": 33.5138,
            "longitude": 36.2765,
            "fatalities": 8,
            "wounded": 15,
        },
        {
            "event_type": "strategic_development",
            "location_name": "Istanbul, Turkey",
            "country": "TR",
            "latitude": 41.0082,
            "longitude": 28.9784,
            "fatalities": 0,
            "wounded": 0,
        },
        {
            "event_type": "explosions_remote_violence",
            "location_name": "Beirut, Lebanon",
            "country": "LB",
            "latitude": 33.3157,
            "longitude": 35.4747,
            "fatalities": 3,
            "wounded": 8,
        },
        {
            "event_type": "protests",
            "location_name": "Cairo, Egypt",
            "country": "EG",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "fatalities": 0,
            "wounded": 2,
        },
        {
            "event_type": "remote_violence",
            "location_name": "Gaza City, Palestine",
            "country": "PS",
            "latitude": 31.5167,
            "longitude": 34.4667,
            "fatalities": 12,
            "wounded": 25,
        },
    ]

    for i, config in enumerate(event_configs):
        event = seed_event_base.copy()
        event.update(config)
        event["event_id"] = f"EVT-{str(i + 1).zfill(6)}"
        event["event_date"] = datetime.utcnow() - timedelta(days=30 - i * 5)
        events.append(event)

    return events


# ============================================================================
# Airport and Port Fixtures
# ============================================================================

@pytest.fixture
def seed_airports() -> List[Dict[str, Any]]:
    """Generate 8 major international airports in Middle East/Mediterranean region."""
    return [
        {
            "airport_id": "IST",
            "iata": "IST",
            "name": "Istanbul Airport (Istanbul Havalimani)",
            "country": "TR",
            "status": "operational",
            "latitude": 41.2753,
            "longitude": 28.7520,
            "passengers_annual": 70000000,
            "cargo_annual_tons": 300000,
        },
        {
            "airport_id": "DXB",
            "iata": "DXB",
            "name": "Dubai International Airport",
            "country": "AE",
            "status": "operational",
            "latitude": 25.2528,
            "longitude": 55.3644,
            "passengers_annual": 88000000,
            "cargo_annual_tons": 2700000,
        },
        {
            "airport_id": "DOH",
            "iata": "DOH",
            "name": "Hamad International Airport",
            "country": "QA",
            "status": "operational",
            "latitude": 25.2731,
            "longitude": 51.6091,
            "passengers_annual": 37000000,
            "cargo_annual_tons": 1900000,
        },
        {
            "airport_id": "LHR",
            "iata": "LHR",
            "name": "London Heathrow Airport",
            "country": "GB",
            "status": "operational",
            "latitude": 51.4700,
            "longitude": -0.4543,
            "passengers_annual": 80000000,
            "cargo_annual_tons": 1500000,
        },
        {
            "airport_id": "CDG",
            "iata": "CDG",
            "name": "Paris Charles de Gaulle Airport",
            "country": "FR",
            "status": "operational",
            "latitude": 49.0097,
            "longitude": 2.5479,
            "passengers_annual": 75000000,
            "cargo_annual_tons": 1200000,
        },
        {
            "airport_id": "JFK",
            "iata": "JFK",
            "name": "New York John F. Kennedy International Airport",
            "country": "US",
            "status": "operational",
            "latitude": 40.6413,
            "longitude": -73.7781,
            "passengers_annual": 62000000,
            "cargo_annual_tons": 2200000,
        },
        {
            "airport_id": "SFO",
            "iata": "SFO",
            "name": "San Francisco International Airport",
            "country": "US",
            "status": "operational",
            "latitude": 37.6213,
            "longitude": -122.3790,
            "passengers_annual": 58000000,
            "cargo_annual_tons": 800000,
        },
        {
            "airport_id": "HND",
            "iata": "HND",
            "name": "Tokyo Haneda Airport",
            "country": "JP",
            "status": "operational",
            "latitude": 35.5494,
            "longitude": 139.7798,
            "passengers_annual": 90000000,
            "cargo_annual_tons": 2300000,
        },
    ]


@pytest.fixture
def seed_ports() -> List[Dict[str, Any]]:
    """Generate 8 major international seaports."""
    return [
        {
            "port_id": "AEHSX",
            "name": "Jebel Ali Port",
            "country": "AE",
            "status": "operational",
            "latitude": 24.9774,
            "longitude": 55.0173,
            "container_capacity_teu": 19500000,
            "berths": 67,
        },
        {
            "port_id": "SGSIN",
            "name": "Port of Singapore",
            "country": "SG",
            "status": "operational",
            "latitude": 1.3521,
            "longitude": 103.8198,
            "container_capacity_teu": 65600000,
            "berths": 109,
        },
        {
            "port_id": "CNSHA",
            "name": "Shanghai Port",
            "country": "CN",
            "status": "operational",
            "latitude": 30.9756,
            "longitude": 121.6898,
            "container_capacity_teu": 47000000,
            "berths": 158,
        },
        {
            "port_id": "NLAMS",
            "name": "Port of Amsterdam",
            "country": "NL",
            "status": "operational",
            "latitude": 52.3667,
            "longitude": 5.0000,
            "container_capacity_teu": 5000000,
            "berths": 81,
        },
        {
            "port_id": "GBLON",
            "name": "Port of London",
            "country": "GB",
            "status": "operational",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "container_capacity_teu": 3500000,
            "berths": 47,
        },
        {
            "port_id": "USNYC",
            "name": "Port of New York and New Jersey",
            "country": "US",
            "status": "operational",
            "latitude": 40.6892,
            "longitude": -74.0445,
            "container_capacity_teu": 7500000,
            "berths": 63,
        },
        {
            "port_id": "JPTYO",
            "name": "Port of Tokyo",
            "country": "JP",
            "status": "operational",
            "latitude": 35.6262,
            "longitude": 139.7321,
            "container_capacity_teu": 4700000,
            "berths": 49,
        },
        {
            "port_id": "LBBET",
            "name": "Port of Beirut",
            "country": "LB",
            "status": "degraded",
            "latitude": 33.8886,
            "longitude": 35.4989,
            "container_capacity_teu": 1000000,
            "berths": 22,
        },
    ]


# ============================================================================
# Corridor and Trade Route Fixtures
# ============================================================================

@pytest.fixture
def seed_corridors() -> List[Dict[str, Any]]:
    """Generate 10 major international trade corridors."""
    return [
        {
            "corridor_id": "MAR-ASIA",
            "name": "Maritime Asia-Europe Corridor",
            "corridor_type": "maritime",
            "origin": "Singapore",
            "destination": "Rotterdam",
            "distance_nm": 7400,
            "annual_cargo_tons": 450000000,
            "status": "active",
        },
        {
            "corridor_id": "AIR-TRANS",
            "name": "Transatlantic Air Corridor",
            "corridor_type": "air",
            "origin": "New York",
            "destination": "London",
            "distance_nm": 3440,
            "annual_cargo_tons": 2500000,
            "status": "active",
        },
        {
            "corridor_id": "SUE-CANAL",
            "name": "Suez Canal Route",
            "corridor_type": "maritime",
            "origin": "Mediterranean",
            "destination": "Red Sea",
            "distance_nm": 120,
            "annual_cargo_tons": 400000000,
            "status": "active",
        },
        {
            "corridor_id": "PAC-ROUTE",
            "name": "Pacific Trade Route",
            "corridor_type": "maritime",
            "origin": "Shanghai",
            "destination": "Los Angeles",
            "distance_nm": 5800,
            "annual_cargo_tons": 320000000,
            "status": "active",
        },
        {
            "corridor_id": "AIR-GULF",
            "name": "Gulf Hub Air Corridor",
            "corridor_type": "air",
            "origin": "Dubai",
            "destination": "London",
            "distance_nm": 2240,
            "annual_cargo_tons": 1800000,
            "status": "active",
        },
        {
            "corridor_id": "LAND-SILK",
            "name": "Silk Road Land Corridor",
            "corridor_type": "ground",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "distance_nm": 4600,
            "annual_cargo_tons": 80000000,
            "status": "active",
        },
        {
            "corridor_id": "MED-ROUTE",
            "name": "Mediterranean Shipping Route",
            "corridor_type": "maritime",
            "origin": "Istanbul",
            "destination": "Barcelona",
            "distance_nm": 1800,
            "annual_cargo_tons": 200000000,
            "status": "active",
        },
        {
            "corridor_id": "AIR-ASIA",
            "name": "Asia-Pacific Air Corridor",
            "corridor_type": "air",
            "origin": "Tokyo",
            "destination": "Sydney",
            "distance_nm": 4890,
            "annual_cargo_tons": 1200000,
            "status": "active",
        },
        {
            "corridor_id": "LAND-EU",
            "name": "Intra-Europe Land Corridor",
            "corridor_type": "ground",
            "origin": "Berlin",
            "destination": "Paris",
            "distance_nm": 560,
            "annual_cargo_tons": 150000000,
            "status": "active",
        },
        {
            "corridor_id": "PIPE-OIL",
            "name": "Middle East Oil Pipeline Corridor",
            "corridor_type": "pipeline",
            "origin": "Basra",
            "destination": "Fujairah",
            "distance_nm": 600,
            "annual_cargo_tons": 500000000,
            "status": "active",
        },
    ]


# ============================================================================
# Flight and Vessel Fixtures
# ============================================================================

@pytest.fixture
def seed_flights() -> List[Dict[str, Any]]:
    """Generate 10 sample flight operational records."""
    base_time = datetime.utcnow()
    return [
        {
            "flight_id": f"FL-{uuid4().hex[:12].upper()}",
            "flight_number": "BA0001",
            "aircraft_type": "Boeing 747-8F",
            "origin": "LHR",
            "destination": "DXB",
            "departure_time": base_time + timedelta(hours=2),
            "arrival_time": base_time + timedelta(hours=8),
            "status": "scheduled",
            "capacity_kg": 121000,
            "current_load_kg": 95000,
        },
        {
            "flight_id": f"FL-{uuid4().hex[:12].upper()}",
            "flight_number": "LY0502",
            "aircraft_type": "Boeing 777-300F",
            "origin": "TLV",
            "destination": "JFK",
            "departure_time": base_time - timedelta(hours=5),
            "arrival_time": base_time + timedelta(hours=10),
            "status": "in_flight",
            "capacity_kg": 102000,
            "current_load_kg": 87000,
        },
        {
            "flight_id": f"FL-{uuid4().hex[:12].upper()}",
            "flight_number": "CX0888",
            "aircraft_type": "Airbus A330-300F",
            "origin": "HKG",
            "destination": "LAX",
            "departure_time": base_time - timedelta(hours=3),
            "arrival_time": base_time + timedelta(hours=13),
            "status": "in_flight",
            "capacity_kg": 70000,
            "current_load_kg": 58000,
        },
        {
            "flight_id": f"FL-{uuid4().hex[:12].upper()}",
            "flight_number": "AF0500",
            "aircraft_type": "Boeing 787-9F",
            "origin": "CDG",
            "destination": "SFO",
            "departure_time": base_time + timedelta(hours=4),
            "arrival_time": base_time + timedelta(hours=18),
            "status": "scheduled",
            "capacity_kg": 60000,
            "current_load_kg": 42000,
        },
        {
            "flight_id": f"FL-{uuid4().hex[:12].upper()}",
            "flight_number": "QR0160",
            "aircraft_type": "Boeing 777F",
            "origin": "DOH",
            "destination": "LHR",
            "departure_time": base_time + timedelta(hours=1),
            "arrival_time": base_time + timedelta(hours=6),
            "status": "scheduled",
            "capacity_kg": 102000,
            "current_load_kg": 78000,
        },
    ]


@pytest.fixture
def seed_vessels() -> List[Dict[str, Any]]:
    """Generate 10 sample vessel operational records."""
    base_time = datetime.utcnow()
    return [
        {
            "vessel_id": f"VS-{uuid4().hex[:12].upper()}",
            "mmsi": 413769700,
            "name": "MSC Gulsun",
            "vessel_type": "Container Ship",
            "flag": "LI",
            "length_m": 400,
            "width_m": 61,
            "capacity_teu": 23756,
            "current_load_teu": 19240,
            "current_location": {"latitude": 25.2528, "longitude": 55.3644},
            "status": "at_port",
            "next_port": "SGSIN",
            "eta": base_time + timedelta(days=5),
        },
        {
            "vessel_id": f"VS-{uuid4().hex[:12].upper()}",
            "mmsi": 563105450,
            "name": "Ever Given",
            "vessel_type": "Container Ship",
            "flag": "PA",
            "length_m": 400,
            "width_m": 59,
            "capacity_teu": 20000,
            "current_load_teu": 16500,
            "current_location": {"latitude": 30.6326, "longitude": 32.3361},
            "status": "in_transit",
            "next_port": "NLAMS",
            "eta": base_time + timedelta(days=14),
        },
        {
            "vessel_id": f"VS-{uuid4().hex[:12].upper()}",
            "mmsi": 538090612,
            "name": "COSCO Shipping Universe",
            "vessel_type": "Container Ship",
            "flag": "HK",
            "length_m": 400,
            "width_m": 59,
            "capacity_teu": 21000,
            "current_load_teu": 17850,
            "current_location": {"latitude": 1.3521, "longitude": 103.8198},
            "status": "at_port",
            "next_port": "AEHSX",
            "eta": base_time + timedelta(days=3),
        },
        {
            "vessel_id": f"VS-{uuid4().hex[:12].upper()}",
            "mmsi": 244730822,
            "name": "ONE Innovation",
            "vessel_type": "Container Ship",
            "flag": "SG",
            "length_m": 400,
            "width_m": 61,
            "capacity_teu": 20000,
            "current_load_teu": 15600,
            "current_location": {"latitude": 30.9756, "longitude": 121.6898},
            "status": "in_transit",
            "next_port": "USNYC",
            "eta": base_time + timedelta(days=21),
        },
        {
            "vessel_id": f"VS-{uuid4().hex[:12].upper()}",
            "mmsi": 351759000,
            "name": "OOCL Hong Kong",
            "vessel_type": "Container Ship",
            "flag": "HK",
            "length_m": 400,
            "width_m": 59,
            "capacity_teu": 21237,
            "current_load_teu": 18321,
            "current_location": {"latitude": 52.3667, "longitude": 5.0000},
            "status": "at_port",
            "next_port": "GBLON",
            "eta": base_time + timedelta(days=1),
        },
    ]


# ============================================================================
# Actor and Stakeholder Fixtures
# ============================================================================

@pytest.fixture
def seed_actors() -> List[Dict[str, Any]]:
    """Generate 15 sample GCC actors (state and non-state)."""
    return [
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "United States Government",
            "country": "US",
            "region": "North America",
            "influence_level": "very_high",
            "focus_areas": ["logistics", "energy", "ports", "trade"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "People's Republic of China",
            "country": "CN",
            "region": "Asia-Pacific",
            "influence_level": "very_high",
            "focus_areas": ["trade", "energy", "technology", "infrastructure"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "European Union",
            "country": "EU",
            "region": "Europe",
            "influence_level": "very_high",
            "focus_areas": ["trade", "energy", "security", "infrastructure"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "Islamic Republic of Iran",
            "country": "IR",
            "region": "Middle East",
            "influence_level": "high",
            "focus_areas": ["energy", "shipping", "regional_stability"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "corporation",
            "name": "Maersk",
            "country": "DK",
            "region": "Global",
            "influence_level": "high",
            "focus_areas": ["shipping", "logistics", "ports"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "corporation",
            "name": "China State Shipping Company",
            "country": "CN",
            "region": "Asia-Pacific",
            "influence_level": "high",
            "focus_areas": ["shipping", "ports", "infrastructure"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "organization",
            "name": "International Maritime Organization",
            "country": "UN",
            "region": "Global",
            "influence_level": "medium",
            "focus_areas": ["maritime_security", "trade", "regulation"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "non_state_actor",
            "name": "Houthis",
            "country": "YE",
            "region": "Middle East",
            "influence_level": "high",
            "focus_areas": ["regional_stability", "shipping", "energy"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "Kingdom of Saudi Arabia",
            "country": "SA",
            "region": "Middle East",
            "influence_level": "very_high",
            "focus_areas": ["energy", "trade", "regional_stability"],
        },
        {
            "actor_id": f"ACT-{uuid4().hex[:8].upper()}",
            "actor_type": "government",
            "name": "United Arab Emirates",
            "country": "AE",
            "region": "Middle East",
            "influence_level": "high",
            "focus_areas": ["ports", "logistics", "trade", "infrastructure"],
        },
    ]


# ============================================================================
# Scenario Template Fixtures
# ============================================================================

@pytest.fixture
def sample_scenario_template() -> Dict[str, Any]:
    """Single representative scenario template."""
    return {
        "scenario_id": "SCEN-SUEZ-BLOCKADE-001",
        "scenario_name": "Suez Canal Blockade",
        "scenario_category": "Disruption",
        "description": "Complete blockage of Suez Canal due to geopolitical tensions, forcing rerouting around Cape of Good Hope",
        "affected_corridors": ["SUE-CANAL", "MAR-ASIA"],
        "affected_countries": ["EG", "SA", "AE", "IR"],
        "parameters": {
            "blockade_duration_days": 30,
            "reroute_distance_increase_percent": 35,
            "cost_impact_millions_usd": 2500,
            "shipping_delays_days": 14,
        },
        "severity_level": "critical",
        "probability_percent": 5,
        "impact_areas": ["maritime_trade", "energy_security", "global_commerce"],
    }


@pytest.fixture
def scenario_templates() -> List[Dict[str, Any]]:
    """All 15 GCC scenario templates."""
    return [
        {
            "scenario_id": "SCEN-SUEZ-001",
            "scenario_name": "Suez Canal Blockade",
            "category": "Disruption",
            "description": "Complete blockage of Suez Canal",
            "severity": "critical",
            "probability_percent": 5,
        },
        {
            "scenario_id": "SCEN-STRAIT-001",
            "scenario_name": "Strategic Maritime Chokepoint Disruption (Hormuz)",
            "category": "Disruption",
            "description": "Closure of Strait of Hormuz blocking oil shipments",
            "severity": "critical",
            "probability_percent": 8,
        },
        {
            "scenario_id": "SCEN-PIRACY-001",
            "scenario_name": "Escalated Piracy",
            "category": "Security Threat",
            "description": "Significant increase in piracy in Gulf of Aden and Indian Ocean",
            "severity": "high",
            "probability_percent": 12,
        },
        {
            "scenario_id": "SCEN-CYBER-001",
            "scenario_name": "Cyberattack on Port Infrastructure",
            "category": "Security Threat",
            "description": "Coordinated cyberattack disabling major port operations",
            "severity": "high",
            "probability_percent": 15,
        },
        {
            "scenario_id": "SCEN-PANDEMIC-001",
            "scenario_name": "Global Health Emergency",
            "category": "Public Health",
            "description": "New pandemic disrupting global logistics networks",
            "severity": "high",
            "probability_percent": 10,
        },
        {
            "scenario_id": "SCEN-CLIMATE-001",
            "scenario_name": "Extreme Weather Event",
            "category": "Natural Disaster",
            "description": "Hurricane or typhoon disrupting regional shipping",
            "severity": "high",
            "probability_percent": 20,
        },
        {
            "scenario_id": "SCEN-CONFLICT-001",
            "scenario_name": "Regional Armed Conflict",
            "category": "Geopolitical",
            "description": "Escalation of tensions between major powers",
            "severity": "critical",
            "probability_percent": 6,
        },
        {
            "scenario_id": "SCEN-TRADE-001",
            "scenario_name": "Trade War Escalation",
            "category": "Economic",
            "description": "Significant tariffs and trade barriers imposed",
            "severity": "medium",
            "probability_percent": 25,
        },
        {
            "scenario_id": "SCEN-FUEL-001",
            "scenario_name": "Energy Price Spike",
            "category": "Economic",
            "description": "Sudden and sustained increase in fuel prices",
            "severity": "medium",
            "probability_percent": 18,
        },
        {
            "scenario_id": "SCEN-TERROR-001",
            "scenario_name": "Terrorist Attack on Critical Infrastructure",
            "category": "Security Threat",
            "description": "Attack targeting major port or logistics hub",
            "severity": "high",
            "probability_percent": 7,
        },
        {
            "scenario_id": "SCEN-SUPPLY-001",
            "scenario_name": "Supply Chain Disruption",
            "category": "Disruption",
            "description": "Failure in key supplier affecting multiple corridors",
            "severity": "medium",
            "probability_percent": 22,
        },
        {
            "scenario_id": "SCEN-TECH-001",
            "scenario_name": "Critical Technology Failure",
            "category": "Technology",
            "description": "Failure of GPS/navigation systems or communication networks",
            "severity": "medium",
            "probability_percent": 8,
        },
        {
            "scenario_id": "SCEN-LABOR-001",
            "scenario_name": "Labor Disruption",
            "category": "Labor",
            "description": "Strikes or labor actions affecting port operations",
            "severity": "medium",
            "probability_percent": 14,
        },
        {
            "scenario_id": "SCEN-ENVIRO-001",
            "scenario_name": "Environmental Incident",
            "category": "Environmental",
            "description": "Major oil spill or environmental contamination",
            "severity": "high",
            "probability_percent": 9,
        },
        {
            "scenario_id": "SCEN-POLICY-001",
            "scenario_name": "Regulatory Policy Change",
            "category": "Regulatory",
            "description": "New environmental or security regulations affecting operations",
            "severity": "low",
            "probability_percent": 30,
        },
    ]


# ============================================================================
# Risk Scoring and Model Weights Fixtures
# ============================================================================

@pytest.fixture
def gcc_risk_weights() -> Dict[str, Any]:
    """Risk scoring weights and parameters for GCC analysis."""
    return {
        "event_severity_weights": {
            "violence_against_civilians": 0.95,
            "explosions_remote_violence": 0.85,
            "strategic_development": 0.40,
            "protests": 0.20,
            "remote_violence": 0.75,
        },
        "proximity_weights": {
            "same_country": 1.0,
            "adjacent_country": 0.8,
            "regional": 0.5,
            "global": 0.2,
        },
        "corridor_importance_weights": {
            "maritime": {
                "global_trade_share": 0.90,
                "energy_criticality": 0.85,
                "value_billions_usd": 0.75,
            },
            "air": {
                "global_trade_share": 0.08,
                "time_criticality": 0.95,
                "value_billions_usd": 0.20,
            },
            "land": {
                "global_trade_share": 0.02,
                "regional_importance": 0.60,
                "value_billions_usd": 0.05,
            },
        },
        "risk_thresholds": {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.95,
        },
        "temporal_decay": {
            "days_half_life": 90,
            "exponential_factor": 0.693,
        },
    }


# ============================================================================
# Compound Fixture: All Seed Data
# ============================================================================

@pytest.fixture
def all_seed_data(
    seed_events,
    seed_airports,
    seed_ports,
    seed_corridors,
    seed_flights,
    seed_vessels,
    seed_actors,
    scenario_templates,
    gcc_risk_weights,
) -> Dict[str, Any]:
    """
    Complete dataset combining all fixtures for integration testing.
    
    Provides a unified snapshot of the GCC data model including:
    - 5 real-world events
    - 8 major international airports
    - 8 major international seaports
    - 10 critical trade corridors
    - 5 active flights
    - 5 active vessels
    - 10 key GCC actors
    - 15 scenario templates
    - Risk scoring weights
    """
    return {
        "events": seed_events,
        "airports": seed_airports,
        "ports": seed_ports,
        "corridors": seed_corridors,
        "flights": seed_flights,
        "vessels": seed_vessels,
        "actors": seed_actors,
        "scenarios": scenario_templates,
        "risk_weights": gcc_risk_weights,
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_events": len(seed_events),
            "total_infrastructure": len(seed_airports) + len(seed_ports),
            "total_corridors": len(seed_corridors),
            "total_moving_assets": len(seed_flights) + len(seed_vessels),
            "total_actors": len(seed_actors),
            "total_scenarios": len(scenario_templates),
        },
    }
