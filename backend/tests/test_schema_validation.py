"""
Schema validation tests for Impact Observatory.

Tests Pydantic v2 schema validation including:
- Event model field validation
- IATA airport code validation
- Port coordinate validation
- Corridor structure validation
- Flight status validation
- Vessel MMSI validation
- Actor type validation
- Risk score range validation
- Geospatial bounds validation
- Bilingual field validation
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError, BaseModel, Field
from typing import Optional, Dict, Any, List


# ============================================================================
# Inline test models matching conftest fixture shapes
# ============================================================================

class EventModel(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    event_date: datetime
    location_name: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=3)
    admin1: Optional[str] = None
    admin2: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    fatalities: int = Field(default=0, ge=0)
    wounded: int = Field(default=0, ge=0)
    description: str
    source_id: str
    source_type: str
    confidence: float = Field(..., ge=0, le=1)
    tags: list = Field(default_factory=list)
    provenance: Optional[Dict[str, Any]] = None


class AirportModel(BaseModel):
    """Matches conftest seed_airports fixture."""
    airport_id: str
    iata: str = Field(..., min_length=3, max_length=3)
    name: str
    country: str = Field(..., min_length=2, max_length=3)
    status: str = "operational"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    passengers_annual: int = Field(ge=0)
    cargo_annual_tons: int = Field(ge=0)


class PortModel(BaseModel):
    """Matches conftest seed_ports fixture."""
    port_id: str
    name: str
    country: str = Field(..., min_length=2, max_length=3)
    status: str = "operational"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    container_capacity_teu: int = Field(ge=0)
    berths: int = Field(ge=1)


class CorridorModel(BaseModel):
    """Matches conftest seed_corridors fixture."""
    corridor_id: str
    name: str
    corridor_type: str = Field(..., pattern="^(maritime|air|ground|pipeline)$")
    origin: str
    destination: str
    distance_nm: float = Field(ge=0)
    annual_cargo_tons: int = Field(ge=0)
    status: str = "active"


class FlightModel(BaseModel):
    """Matches conftest seed_flights fixture."""
    flight_id: str
    flight_number: str
    aircraft_type: str
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    departure_time: datetime
    arrival_time: datetime
    status: str = Field(..., pattern="^(scheduled|in_flight|departed|airborne|delayed|cancelled|landed)$")
    capacity_kg: int = Field(gt=0)
    current_load_kg: int = Field(ge=0)


class VesselModel(BaseModel):
    """Matches conftest seed_vessels fixture."""
    vessel_id: str
    name: str
    mmsi: int = Field(..., ge=100000000, le=999999999)
    vessel_type: str
    flag: str
    length_m: float = Field(ge=0)
    width_m: float = Field(ge=0)
    capacity_teu: int = Field(ge=0)
    current_load_teu: int = Field(ge=0)
    current_location: Dict[str, float]
    status: str
    next_port: str
    eta: datetime


class ActorModel(BaseModel):
    """Matches conftest seed_actors fixture."""
    actor_id: str
    name: str
    actor_type: str = Field(..., pattern="^(government|corporation|ngo|non_state_actor|organization)$")
    country: str
    region: str
    influence_level: str
    focus_areas: List[str]


class RiskScoreModel(BaseModel):
    risk_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    severity: int = Field(..., ge=0, le=10)


class GeoPointModel(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str


class BilingualFieldModel(BaseModel):
    name_en: str = Field(..., min_length=1)
    name_ar: str = Field(..., min_length=1)


# ============================================================================
# Tests
# ============================================================================


class TestEventModelValidation:
    def test_event_valid_minimal(self, seed_event_base):
        event = EventModel(**seed_event_base)
        assert event.event_id == seed_event_base["event_id"]
        assert -90 <= event.latitude <= 90

    def test_event_latitude_out_of_bounds(self, seed_event_base):
        invalid = seed_event_base.copy()
        invalid["latitude"] = 95
        with pytest.raises(ValidationError):
            EventModel(**invalid)

    def test_event_longitude_out_of_bounds(self, seed_event_base):
        invalid = seed_event_base.copy()
        invalid["longitude"] = 185
        with pytest.raises(ValidationError):
            EventModel(**invalid)

    def test_event_negative_fatalities_invalid(self, seed_event_base):
        invalid = seed_event_base.copy()
        invalid["fatalities"] = -5
        with pytest.raises(ValidationError):
            EventModel(**invalid)

    def test_event_confidence_out_of_bounds(self, seed_event_base):
        invalid = seed_event_base.copy()
        invalid["confidence"] = 1.5
        with pytest.raises(ValidationError):
            EventModel(**invalid)

    def test_event_missing_required_field(self, seed_event_base):
        incomplete = seed_event_base.copy()
        del incomplete["event_type"]
        with pytest.raises(ValidationError):
            EventModel(**incomplete)

    def test_event_country_code_validation(self, seed_event_base):
        valid = seed_event_base.copy()
        valid["country"] = "US"
        event = EventModel(**valid)
        assert event.country == "US"

        invalid = seed_event_base.copy()
        invalid["country"] = "COUNTRY"
        with pytest.raises(ValidationError):
            EventModel(**invalid)


class TestIATACodeValidation:
    def test_valid_iata_codes(self, seed_airports):
        for airport in seed_airports:
            model = AirportModel(**airport)
            assert len(model.iata) == 3

    def test_iata_code_too_short(self):
        with pytest.raises(ValidationError):
            AirportModel(
                airport_id="apt_001", iata="JF", name="Test",
                country="US", latitude=40.6, longitude=-74.0,
                passengers_annual=5000, cargo_annual_tons=2000,
            )

    def test_iata_code_too_long(self):
        with pytest.raises(ValidationError):
            AirportModel(
                airport_id="apt_001", iata="JFKA", name="Test",
                country="US", latitude=40.6, longitude=-74.0,
                passengers_annual=5000, cargo_annual_tons=2000,
            )


class TestPortCoordinateValidation:
    def test_valid_port_coordinates(self, seed_ports):
        for port in seed_ports:
            model = PortModel(**port)
            assert -90 <= model.latitude <= 90
            assert -180 <= model.longitude <= 180

    def test_port_latitude_out_of_bounds(self):
        with pytest.raises(ValidationError):
            PortModel(
                port_id="port_001", name="Jebel Ali", country="AE",
                latitude=91, longitude=55.1,
                container_capacity_teu=15000000, berths=67,
            )


class TestCorridorValidation:
    def test_valid_corridor_types(self, seed_corridors):
        for corridor in seed_corridors:
            model = CorridorModel(**corridor)
            assert model.corridor_type in ["maritime", "air", "ground", "pipeline"]

    def test_invalid_corridor_type(self):
        with pytest.raises(ValidationError):
            CorridorModel(
                corridor_id="c001", name="Test", corridor_type="underwater",
                origin="A", destination="B", distance_nm=500, annual_cargo_tons=100000,
            )


class TestFlightStatusValidation:
    def test_valid_flight_statuses(self, seed_flights):
        for flight in seed_flights:
            model = FlightModel(**flight)
            assert model.status in ["scheduled", "in_flight", "departed", "airborne", "delayed", "cancelled", "landed"]

    def test_invalid_flight_status(self):
        with pytest.raises(ValidationError):
            FlightModel(
                flight_id="f001", flight_number="BA123", aircraft_type="Boeing 777",
                origin="LHR", destination="JFK",
                departure_time=datetime.utcnow(), arrival_time=datetime.utcnow(),
                capacity_kg=350, current_load_kg=200, status="flying",
            )


class TestVesselMMSIValidation:
    def test_valid_mmsi(self, seed_vessels):
        for vessel in seed_vessels:
            model = VesselModel(**vessel)
            assert 100000000 <= model.mmsi <= 999999999

    def test_mmsi_too_small(self):
        with pytest.raises(ValidationError):
            VesselModel(
                vessel_id="v001", name="Test", mmsi=99999999,
                vessel_type="container", flag="LI", length_m=400, width_m=60,
                capacity_teu=20000, current_load_teu=15000,
                current_location={"latitude": 25.0, "longitude": 55.0},
                status="at_port", next_port="SGSIN", eta=datetime.utcnow(),
            )


class TestActorTypeValidation:
    def test_valid_actor_types(self, seed_actors):
        for actor in seed_actors:
            model = ActorModel(**actor)
            assert model.actor_type in ["government", "corporation", "ngo", "non_state_actor", "organization"]

    def test_invalid_actor_type(self):
        with pytest.raises(ValidationError):
            ActorModel(
                actor_id="a001", name="Test", actor_type="individual",
                country="US", region="NA", influence_level="high",
                focus_areas=["trade"],
            )


class TestRiskScoreValidation:
    def test_valid_risk_scores(self):
        for data in [
            {"risk_score": 0, "confidence": 0.5, "severity": 0},
            {"risk_score": 0.5, "confidence": 0.75, "severity": 5},
            {"risk_score": 1.0, "confidence": 0.95, "severity": 10},
        ]:
            risk = RiskScoreModel(**data)
            assert 0 <= risk.risk_score <= 1

    def test_risk_score_exceeds_bounds(self):
        with pytest.raises(ValidationError):
            RiskScoreModel(risk_score=1.5, confidence=0.8, severity=5)


class TestGeoPointBoundsValidation:
    def test_valid_geo_points(self, seed_airports):
        for airport in seed_airports:
            geo = GeoPointModel(
                latitude=airport["latitude"],
                longitude=airport["longitude"],
                location_name=airport["name"],
            )
            assert -90 <= geo.latitude <= 90

    def test_latitude_exceeds_north_pole(self):
        with pytest.raises(ValidationError):
            GeoPointModel(latitude=90.1, longitude=0, location_name="Invalid")


class TestBilingualFieldValidation:
    def test_valid_bilingual_fields(self):
        model = BilingualFieldModel(name_en="Suez Canal", name_ar="قناة السويس")
        assert model.name_en == "Suez Canal"

    def test_missing_english_field(self):
        with pytest.raises(ValidationError):
            BilingualFieldModel(name_ar="قناة السويس")

    def test_empty_bilingual_field(self):
        with pytest.raises(ValidationError):
            BilingualFieldModel(name_en="", name_ar="قناة السويس")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
