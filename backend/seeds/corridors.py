"""Seed data for GCC and regional transportation corridors.

This module provides realistic corridor data for maritime, air, and land routes (2023-2026).
All corridors use real geographic waypoints and realistic traffic volumes.
"""

from datetime import datetime, timedelta

from app.schema import GeoPoint, GeoZone, Corridor


def get_seed_corridors() -> list[Corridor]:
    """Return a list of strategic GCC and regional transportation corridors.
    
    Includes major sea routes, air lanes, and land corridors across:
    - Strait of Hormuz (critical maritime chokepoint)
    - Red Sea maritime routes (Egypt-Gulf shipping)
    - Persian Gulf shipping lanes
    - Air corridors linking GCC cities and beyond
    - Land routes for regional trade (GCC states and neighbors)
    
    Returns:
        list[Corridor]: 15 strategic corridors with realistic traffic data
    """
    corridors = []
    
    # Critical Sea Routes
    corridors.append(Corridor(
        id="cor-001",
        name="Strait of Hormuz - Export Route",
        description="Critical oil and gas export route from Persian Gulf",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=26.5, longitude=55.5),  # Gulf side
        destination_location=GeoPoint(latitude=26.0, longitude=56.5),  # Export side
        waypoints=[
            GeoPoint(latitude=26.2, longitude=55.8),
            GeoPoint(latitude=26.1, longitude=56.2),
        ],
        distance_nm=45,
        distance_km=83,
        expected_transit_hours=2.5,
        annual_traffic_volume=21_000,  # Tanker transits annually
        critical_corridor=True,
        bottleneck_zones=[
            GeoZone(
                id="zone-001",
                name="Hormuz Strait Narrows",
                center_point=GeoPoint(latitude=26.15, longitude=56.0),
                radius_km=5.0,
                zone_type="bottleneck",
            )
        ],
        source_type="government_api",
        confidence=0.99,
        last_status_update=datetime.utcnow() - timedelta(hours=1),
    ))
    
    corridors.append(Corridor(
        id="cor-002",
        name="Red Sea Trading Route - Bab el-Mandeb",
        description="Major shipping route connecting Red Sea and Indian Ocean via Yemen",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=13.0, longitude=43.0),  # Red Sea entry
        destination_location=GeoPoint(latitude=12.5, longitude=44.5),  # Indian Ocean
        waypoints=[
            GeoPoint(latitude=12.8, longitude=43.5),
            GeoPoint(latitude=12.6, longitude=44.0),
        ],
        distance_nm=52,
        distance_km=96,
        expected_transit_hours=3.0,
        annual_traffic_volume=8_000,  # Vessel transits annually
        critical_corridor=True,
        bottleneck_zones=[
            GeoZone(
                id="zone-002",
                name="Bab el-Mandeb Strait",
                center_point=GeoPoint(latitude=12.58, longitude=43.35),
                radius_km=8.0,
                zone_type="bottleneck",
            )
        ],
        source_type="government_api",
        confidence=0.98,
        last_status_update=datetime.utcnow() - timedelta(hours=2),
    ))
    
    corridors.append(Corridor(
        id="cor-003",
        name="Persian Gulf Main Shipping Lane",
        description="Primary shipping corridor through Persian Gulf linking GCC ports",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=29.5, longitude=47.8),  # Kuwait
        destination_location=GeoPoint(latitude=25.3, longitude=55.1),  # UAE
        waypoints=[
            GeoPoint(latitude=29.2, longitude=48.5),
            GeoPoint(latitude=27.5, longitude=49.5),
            GeoPoint(latitude=26.5, longitude=51.0),
        ],
        distance_nm=310,
        distance_km=574,
        expected_transit_hours=16.0,
        annual_traffic_volume=15_000,  # Commercial transits annually
        critical_corridor=True,
        bottleneck_zones=[
            GeoZone(
                id="zone-003",
                name="Dammam-Qatar Traffic Separation",
                center_point=GeoPoint(latitude=27.0, longitude=50.0),
                radius_km=12.0,
                zone_type="congestion_area",
            )
        ],
        source_type="government_api",
        confidence=0.96,
        last_status_update=datetime.utcnow() - timedelta(hours=3),
    ))
    
    corridors.append(Corridor(
        id="cor-004",
        name="Suez Canal Northbound Route",
        description="Egypt-Mediterranean shipping corridor via Suez",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=29.9, longitude=32.6),  # Suez south
        destination_location=GeoPoint(latitude=31.4, longitude=32.3),  # Suez north
        waypoints=[
            GeoPoint(latitude=30.5, longitude=32.4),
            GeoPoint(latitude=31.0, longitude=32.35),
        ],
        distance_nm=101,
        distance_km=187,
        expected_transit_hours=12.0,
        annual_traffic_volume=20_000,  # Total transits annually
        critical_corridor=True,
        bottleneck_zones=[
            GeoZone(
                id="zone-004",
                name="Great Bitter Lake",
                center_point=GeoPoint(latitude=30.6, longitude=32.4),
                radius_km=3.0,
                zone_type="transit_zone",
            )
        ],
        source_type="government_api",
        confidence=0.97,
        last_status_update=datetime.utcnow() - timedelta(hours=4),
    ))
    
    # Air Lanes
    corridors.append(Corridor(
        id="cor-005",
        name="Dubai-Saudi Arabia Air Corridor",
        description="Primary air corridor linking UAE and Saudi Arabia",
        corridor_type="air_lane",
        origin_location=GeoPoint(latitude=25.2528, longitude=55.3644),  # Dubai
        destination_location=GeoPoint(latitude=24.9266, longitude=46.6989),  # Riyadh
        waypoints=[
            GeoPoint(latitude=25.5, longitude=50.5),
            GeoPoint(latitude=25.2, longitude=48.5),
        ],
        distance_nm=360,
        distance_km=667,
        expected_transit_hours=1.5,
        annual_traffic_volume=15_000,  # Flights annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.94,
        last_status_update=datetime.utcnow() - timedelta(hours=5),
    ))
    
    corridors.append(Corridor(
        id="cor-006",
        name="GCC-Europe Air Corridor",
        description="Major international air route linking GCC and European airports",
        corridor_type="air_lane",
        origin_location=GeoPoint(latitude=25.2528, longitude=55.3644),  # Dubai hub
        destination_location=GeoPoint(latitude=51.5, longitude=0.0),  # London reference
        waypoints=[
            GeoPoint(latitude=29.0, longitude=40.0),  # Over Egypt
            GeoPoint(latitude=35.0, longitude=20.0),  # Over Mediterranean
            GeoPoint(latitude=45.0, longitude=10.0),  # Over southern Europe
        ],
        distance_nm=3_200,
        distance_km=5_926,
        expected_transit_hours=7.0,
        annual_traffic_volume=8_000,  # Transatlantic flights annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.93,
        last_status_update=datetime.utcnow() - timedelta(hours=6),
    ))
    
    corridors.append(Corridor(
        id="cor-007",
        name="GCC Regional Air Loop",
        description="Inter-GCC air corridor linking major hubs",
        corridor_type="air_lane",
        origin_location=GeoPoint(latitude=29.2262, longitude=47.9688),  # Kuwait
        destination_location=GeoPoint(latitude=23.5933, longitude=58.2842),  # Muscat
        waypoints=[
            GeoPoint(latitude=26.5, longitude=50.0),  # Central Gulf
            GeoPoint(latitude=25.5, longitude=54.0),  # Doha-Abu Dhabi area
        ],
        distance_nm=650,
        distance_km=1_204,
        expected_transit_hours=2.5,
        annual_traffic_volume=22_000,  # Inter-GCC flights annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.92,
        last_status_update=datetime.utcnow() - timedelta(hours=7),
    ))
    
    corridors.append(Corridor(
        id="cor-008",
        name="GCC-Asia Air Corridor",
        description="Major air route linking GCC and Indian subcontinent/Asia",
        corridor_type="air_lane",
        origin_location=GeoPoint(latitude=25.2528, longitude=55.3644),  # Dubai
        destination_location=GeoPoint(latitude=28.7041, longitude=77.1025),  # Delhi reference
        waypoints=[
            GeoPoint(latitude=27.0, longitude=60.0),
            GeoPoint(latitude=26.0, longitude=65.0),
        ],
        distance_nm=1_400,
        distance_km=2_593,
        expected_transit_hours=3.5,
        annual_traffic_volume=12_000,  # Asia flights annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.91,
        last_status_update=datetime.utcnow() - timedelta(hours=8),
    ))
    
    # Land Routes
    corridors.append(Corridor(
        id="cor-009",
        name="Saudi Arabia-UAE Land Corridor",
        description="Major highway corridor linking Riyadh and Abu Dhabi",
        corridor_type="land_route",
        origin_location=GeoPoint(latitude=24.7136, longitude=46.6753),  # Riyadh center
        destination_location=GeoPoint(latitude=24.4539, longitude=54.3773),  # Abu Dhabi airport
        waypoints=[
            GeoPoint(latitude=24.5, longitude=50.0),
            GeoPoint(latitude=24.3, longitude=52.0),
        ],
        distance_nm=650,
        distance_km=1_204,
        expected_transit_hours=13.0,
        annual_traffic_volume=450_000,  # Vehicles annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.90,
        last_status_update=datetime.utcnow() - timedelta(hours=9),
    ))
    
    corridors.append(Corridor(
        id="cor-010",
        name="Saudi Arabia-Qatar Land Corridor",
        description="Causeway connecting Saudi Arabia and Qatar",
        corridor_type="land_route",
        origin_location=GeoPoint(latitude=26.1355, longitude=50.3628),  # Bahrain reference
        destination_location=GeoPoint(latitude=25.2731, longitude=51.6139),  # Doha
        waypoints=[
            GeoPoint(latitude=25.9, longitude=50.5),
            GeoPoint(latitude=25.5, longitude=51.0),
        ],
        distance_nm=120,
        distance_km=222,
        expected_transit_hours=2.5,
        annual_traffic_volume=200_000,  # Vehicles annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.89,
        last_status_update=datetime.utcnow() - timedelta(hours=10),
    ))
    
    corridors.append(Corridor(
        id="cor-011",
        name="GCC-Iraq Land Corridor",
        description="Cross-border trade route connecting Kuwait and Iraq",
        corridor_type="land_route",
        origin_location=GeoPoint(latitude=29.3862, longitude=47.9774),  # Kuwait City
        destination_location=GeoPoint(latitude=33.3128, longitude=44.3615),  # Baghdad
        waypoints=[
            GeoPoint(latitude=30.0, longitude=47.8),
            GeoPoint(latitude=31.0, longitude=45.0),
        ],
        distance_nm=280,
        distance_km=519,
        expected_transit_hours=8.0,
        annual_traffic_volume=150_000,  # Vehicles annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.78,
        last_status_update=datetime.utcnow() - timedelta(hours=12),
    ))
    
    corridors.append(Corridor(
        id="cor-012",
        name="Oman-UAE Land Route",
        description="Highway connecting Muscat and Abu Dhabi",
        corridor_type="land_route",
        origin_location=GeoPoint(latitude=23.6100, longitude=58.5400),  # Muscat
        destination_location=GeoPoint(latitude=24.4539, longitude=54.3773),  # Abu Dhabi
        waypoints=[
            GeoPoint(latitude=24.0, longitude=56.5),
            GeoPoint(latitude=24.2, longitude=55.5),
        ],
        distance_nm=260,
        distance_km=482,
        expected_transit_hours=5.5,
        annual_traffic_volume=180_000,  # Vehicles annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.88,
        last_status_update=datetime.utcnow() - timedelta(hours=11),
    ))
    
    corridors.append(Corridor(
        id="cor-013",
        name="Egypt-Sudan-Red Sea Trade Route",
        description="Overland trade corridor connecting northeastern Africa",
        corridor_type="land_route",
        origin_location=GeoPoint(latitude=30.0626, longitude=31.2497),  # Cairo area
        destination_location=GeoPoint(latitude=15.5527, longitude=32.5373),  # Port Sudan
        waypoints=[
            GeoPoint(latitude=26.0, longitude=31.5),
            GeoPoint(latitude=22.0, longitude=32.0),
        ],
        distance_nm=1_050,
        distance_km=1_944,
        expected_transit_hours=24.0,
        annual_traffic_volume=120_000,  # Vehicles annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.82,
        last_status_update=datetime.utcnow() - timedelta(hours=13),
    ))
    
    corridors.append(Corridor(
        id="cor-014",
        name="Iran-UAE Maritime Corridor",
        description="Shipping route across Persian Gulf between Iran and UAE",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=26.2, longitude=54.3),  # Qeshm Island area
        destination_location=GeoPoint(latitude=25.2, longitude=55.3),  # Dubai/Jebel Ali
        waypoints=[
            GeoPoint(latitude=25.8, longitude=54.8),
        ],
        distance_nm=90,
        distance_km=167,
        expected_transit_hours=4.5,
        annual_traffic_volume=3_000,  # Transits annually
        critical_corridor=False,
        bottleneck_zones=[],
        source_type="government_api",
        confidence=0.80,
        last_status_update=datetime.utcnow() - timedelta(hours=14),
    ))
    
    corridors.append(Corridor(
        id="cor-015",
        name="Pakistan-GCC Shipping Lane",
        description="Major maritime trade route from Pakistan to Gulf ports",
        corridor_type="sea_route",
        origin_location=GeoPoint(latitude=24.8179, longitude=66.9953),  # Karachi
        destination_location=GeoPoint(latitude=26.0, longitude=50.1),  # Dammam
        waypoints=[
            GeoPoint(latitude=25.5, longitude=58.0),
            GeoPoint(latitude=26.0, longitude=54.0),
        ],
        distance_nm=850,
        distance_km=1_574,
        expected_transit_hours=4.0,
        annual_traffic_volume=5_500,  # Transits annually
        critical_corridor=False,
        source_type="government_api",
        confidence=0.85,
        last_status_update=datetime.utcnow() - timedelta(hours=15),
    ))
    
    return corridors
