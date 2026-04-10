"""
Seeded GCC Scenario Data for Phase 11.

This module defines all 15 mandatory disruption scenarios with pre-configured
seed data, injection events, and expected outputs for regression testing and
scenario validation.

Each scenario is grounded in real node IDs from the GCC infrastructure seeds,
realistic injection events, and expected output ranges derived from the
intelligence math modules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from enum import Enum


class EventType(Enum):
    """Types of shock events that can be injected."""
    NAVAL_BLOCKADE = "naval_blockade"
    MISSILE_THREAT = "missile_threat"
    AIRSPACE_CLOSURE = "airspace_closure"
    PORT_DAMAGE = "port_damage"
    AIRPORT_SHUTDOWN = "airport_shutdown"
    FLIGHT_DIVERSION = "flight_diversion"
    VESSEL_DIVERSION = "vessel_diversion"
    CORRIDOR_RESTRICTION = "corridor_restriction"
    CONFLICT_SPILLOVER = "conflict_spillover"
    INSURANCE_RATE_SPIKE = "insurance_rate_spike"
    LOGISTICS_DELAY = "logistics_delay"
    CYBER_ATTACK = "cyber_attack"
    FUEL_SHORTAGE = "fuel_shortage"
    ECONOMIC_PRESSURE = "economic_pressure"
    MARITIME_RISK_SURGE = "maritime_risk_surge"
    PORT_CONGESTION = "port_congestion"
    COMBINED_DISRUPTION = "combined_disruption"


@dataclass
class ScenarioSeed:
    """
    Pre-configured seed data for a disruption scenario.
    
    Attributes:
        scenario_id: Kebab-case unique identifier (e.g., 'hormuz_closure')
        title: Human-readable scenario title
        title_ar: Arabic title for internationalization
        description: Detailed narrative of the scenario
        inject_events: List of shock events to inject into simulation
        affected_node_ids: Airport, port, and corridor IDs impacted
        severity: Baseline severity (0.0-1.0)
        time_horizon_hours: Simulation duration in hours
        propagation_coefficient: Risk propagation alpha (0.0-1.0)
        expected_output: Ranges for regression testing
    """
    scenario_id: str
    title: str
    title_ar: str
    description: str
    inject_events: List[Dict[str, Any]]
    affected_node_ids: List[str]
    severity: float
    time_horizon_hours: int
    propagation_coefficient: float = 0.75
    expected_output: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SCENARIO SEEDS - All 15 Mandatory Scenarios
# =============================================================================

SCENARIO_SEEDS = [
    ScenarioSeed(
        scenario_id="hormuz_closure",
        title="Strait of Hormuz Closure",
        title_ar="إغلاق مضيق هرمز",
        description=(
            "Full naval blockade of the Strait of Hormuz with coordinated missile "
            "threats. Affects 40% of global oil transport and forces 8+ ports and "
            "10+ maritime corridors into critical diversion mode. Cascades to aviation "
            "through fuel price spikes and insurance cost escalation."
        ),
        inject_events=[
            {
                "event_type": EventType.NAVAL_BLOCKADE.value,
                "latitude": 26.5667,
                "longitude": 56.2500,
                "severity": 0.95,
                "affected_corridors": ["cor-001", "cor-002"],
                "duration_hours": 168,
            },
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 26.2000,
                "longitude": 56.4000,
                "severity": 0.85,
                "radius_nm": 50,
                "duration_hours": 168,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.45,
                "region": "Strait of Hormuz",
                "duration_hours": 336,
            },
        ],
        affected_node_ids=[
            "prt-002",
            "prt-004",
            "prt-008",
            "prt-010",
            "prt-011",
            "prt-012",
            "cor-001",
            "cor-002",
            "apt-006",
            "apt-010",
        ],
        severity=0.90,
        time_horizon_hours=168,
        propagation_coefficient=0.80,
        expected_output={
            "risk_increase_min": 0.30,
            "risk_increase_max": 0.55,
            "affected_ports_min": 8,
            "affected_ports_max": 12,
            "affected_corridors_min": 3,
            "affected_corridors_max": 5,
            "affected_flights_min": 150,
            "insurance_surge_min": 0.25,
            "insurance_surge_max": 0.50,
            "system_stress_level": "critical",
            "cascade_depth_min": 3,
            "confidence_adjustment_min": -0.15,
        },
    ),
    ScenarioSeed(
        scenario_id="gcc_airspace_closure",
        title="GCC Airspace Closure",
        title_ar="إغلاق الأجواء الخليجية",
        description=(
            "Coordinated closure of key GCC airspace corridors forcing all traffic "
            "to international routes. Affects Riyadh, Dubai, Doha, Kuwait, and Manama "
            "airspaces. Increases flight times by 3-5 hours, fuel costs by 15-20%, "
            "and cascades to port scheduling through crew rotation delays."
        ),
        inject_events=[
            {
                "event_type": EventType.AIRSPACE_CLOSURE.value,
                "affected_airports": ["apt-001", "apt-006", "apt-008", "apt-011"],
                "severity": 0.80,
                "duration_hours": 96,
            },
            {
                "event_type": EventType.FLIGHT_DIVERSION.value,
                "severity": 0.70,
                "reroute_distance_increase_nm": 300,
                "affected_airports": ["apt-001", "apt-006", "apt-008", "apt-009"],
                "duration_hours": 96,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.50,
                "delay_hours_min": 4,
                "delay_hours_max": 8,
                "affected_ports": ["prt-005", "prt-006", "prt-011"],
                "duration_hours": 120,
            },
        ],
        affected_node_ids=[
            "apt-001",
            "apt-006",
            "apt-008",
            "apt-009",
            "apt-011",
            "prt-005",
            "prt-006",
            "prt-011",
            "cor-003",
            "cor-004",
        ],
        severity=0.75,
        time_horizon_hours=96,
        propagation_coefficient=0.70,
        expected_output={
            "risk_increase_min": 0.15,
            "risk_increase_max": 0.35,
            "affected_airports_min": 5,
            "affected_flights_min": 200,
            "affected_ports_min": 3,
            "fuel_cost_increase_min": 0.12,
            "fuel_cost_increase_max": 0.22,
            "system_stress_level": "high",
            "cascade_depth_min": 2,
        },
    ),
    ScenarioSeed(
        scenario_id="missile_escalation",
        title="Missile Escalation Event",
        title_ar="تصعيد صاروخي",
        description=(
            "Sustained missile threat campaign targeting maritime zones and key "
            "infrastructure. Affects Jebel Ali, Dammam, and Ras Laffan ports with "
            "high-confidence threat intelligence. Triggers emergency vessel rerouting "
            "and insurance underwriting pause."
        ),
        inject_events=[
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 25.1972,
                "longitude": 55.2744,
                "severity": 0.88,
                "radius_nm": 100,
                "affected_ports": ["prt-005", "prt-006"],
                "duration_hours": 72,
            },
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 26.1667,
                "longitude": 50.2167,
                "severity": 0.75,
                "radius_nm": 80,
                "affected_ports": ["prt-002"],
                "duration_hours": 72,
            },
            {
                "event_type": EventType.VESSEL_DIVERSION.value,
                "severity": 0.72,
                "reroute_distance_increase_nm": 150,
                "affected_ports": ["prt-005", "prt-006", "prt-002"],
                "duration_hours": 120,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.60,
                "region": "Arabian Gulf",
                "duration_hours": 168,
            },
        ],
        affected_node_ids=[
            "prt-002",
            "prt-005",
            "prt-006",
            "prt-008",
            "prt-010",
            "cor-001",
            "cor-005",
        ],
        severity=0.80,
        time_horizon_hours=72,
        propagation_coefficient=0.75,
        expected_output={
            "risk_increase_min": 0.25,
            "risk_increase_max": 0.45,
            "affected_ports_min": 5,
            "affected_corridors_min": 2,
            "insurance_surge_min": 0.35,
            "insurance_surge_max": 0.60,
            "vessel_diversions_min": 20,
            "system_stress_level": "critical",
            "cascade_depth_min": 2,
            "confidence_increase_min": 0.10,
        },
    ),
    ScenarioSeed(
        scenario_id="airport_shutdown",
        title="Airport Shutdown Cascades",
        title_ar="توقف المطارات المتسلسل",
        description=(
            "Emergency closure of Dubai, Riyadh, or Doha airports due to runway "
            "damage or air traffic control systems failure. Cascades to 200+ daily "
            "flight cancellations, port scheduling pressures through crew delays, "
            "and vessel diversions due to air-sea crew synchronization loss."
        ),
        inject_events=[
            {
                "event_type": EventType.AIRPORT_SHUTDOWN.value,
                "affected_airport": "apt-006",
                "severity": 0.92,
                "duration_hours": 48,
            },
            {
                "event_type": EventType.FLIGHT_DIVERSION.value,
                "severity": 0.85,
                "affected_airports": ["apt-001", "apt-008", "apt-011"],
                "reroute_distance_increase_nm": 250,
                "duration_hours": 48,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.60,
                "delay_hours_min": 6,
                "delay_hours_max": 12,
                "affected_ports": ["prt-005", "prt-006", "prt-009"],
                "duration_hours": 96,
            },
        ],
        affected_node_ids=[
            "apt-006",
            "apt-001",
            "apt-008",
            "apt-011",
            "prt-005",
            "prt-006",
            "prt-009",
            "cor-003",
        ],
        severity=0.85,
        time_horizon_hours=48,
        propagation_coefficient=0.78,
        expected_output={
            "risk_increase_min": 0.20,
            "risk_increase_max": 0.40,
            "affected_airports_min": 4,
            "affected_flights_cancelled_min": 150,
            "affected_flights_diverted_min": 200,
            "cascade_to_ports_min": 3,
            "system_stress_level": "high",
            "cascade_depth_min": 2,
        },
    ),
    ScenarioSeed(
        scenario_id="port_congestion",
        title="Port Congestion Crisis",
        title_ar="أزمة الاختناق في الموانئ",
        description=(
            "Container ship pileup at Jebel Ali, Port Rashid, and Dammam due to "
            "loading equipment failure or labor strikes. Creates 2-3 week delays, "
            "forces cargo diversions to Red Sea/Oman Sea routes, spikes logistics "
            "costs, and stresses air freight alternatives."
        ),
        inject_events=[
            {
                "event_type": EventType.PORT_DAMAGE.value,
                "affected_port": "prt-005",
                "severity": 0.78,
                "capacity_reduction": 0.70,
                "duration_hours": 336,
            },
            {
                "event_type": EventType.PORT_DAMAGE.value,
                "affected_port": "prt-006",
                "severity": 0.65,
                "capacity_reduction": 0.50,
                "duration_hours": 240,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.75,
                "delay_hours_min": 120,
                "delay_hours_max": 240,
                "affected_ports": ["prt-005", "prt-006", "prt-002"],
                "duration_hours": 504,
            },
            {
                "event_type": EventType.VESSEL_DIVERSION.value,
                "severity": 0.68,
                "reroute_distance_increase_nm": 200,
                "affected_ports": ["prt-005", "prt-006"],
                "duration_hours": 336,
            },
        ],
        affected_node_ids=[
            "prt-005",
            "prt-006",
            "prt-002",
            "prt-001",
            "prt-003",
            "cor-001",
            "cor-005",
            "apt-006",
            "apt-001",
        ],
        severity=0.72,
        time_horizon_hours=336,
        propagation_coefficient=0.72,
        expected_output={
            "risk_increase_min": 0.18,
            "risk_increase_max": 0.38,
            "affected_ports_min": 5,
            "avg_delay_hours_min": 96,
            "avg_delay_hours_max": 240,
            "cargo_diversion_min": 0.30,
            "logistics_cost_increase_min": 0.20,
            "logistics_cost_increase_max": 0.40,
            "system_stress_level": "high",
            "cascade_depth_min": 2,
        },
    ),
    ScenarioSeed(
        scenario_id="conflict_spillover",
        title="Conflict Spillover Multi-Region",
        title_ar="تجاوز النزاع لمناطق متعددة",
        description=(
            "Regional conflict escalation affecting Iraq, Kuwait, and Saudi borders. "
            "Multi-domain impact: airspace restrictions over Iraq/Kuwait, port "
            "congestion in Basra, asset seizures, and insurance downgrades. Affects "
            "5+ major nodes and 3+ corridors. Confidence in forecasts drops 20%."
        ),
        inject_events=[
            {
                "event_type": EventType.AIRSPACE_CLOSURE.value,
                "affected_airports": ["apt-010", "apt-011"],
                "severity": 0.82,
                "duration_hours": 240,
            },
            {
                "event_type": EventType.CONFLICT_SPILLOVER.value,
                "latitude": 29.9464,
                "longitude": 47.6094,
                "severity": 0.85,
                "radius_nm": 150,
                "affected_airports": ["apt-010"],
                "affected_ports": ["prt-019", "prt-020"],
                "duration_hours": 240,
            },
            {
                "event_type": EventType.VESSEL_DIVERSION.value,
                "severity": 0.70,
                "reroute_distance_increase_nm": 180,
                "affected_ports": ["prt-019", "prt-020"],
                "duration_hours": 240,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.55,
                "region": "Northern Gulf",
                "duration_hours": 360,
            },
        ],
        affected_node_ids=[
            "apt-010",
            "apt-011",
            "prt-002",
            "prt-011",
            "prt-019",
            "prt-020",
            "cor-006",
            "cor-007",
            "cor-008",
        ],
        severity=0.80,
        time_horizon_hours=240,
        propagation_coefficient=0.76,
        expected_output={
            "risk_increase_min": 0.28,
            "risk_increase_max": 0.48,
            "affected_airports_min": 2,
            "affected_ports_min": 4,
            "affected_corridors_min": 3,
            "insurance_surge_min": 0.30,
            "system_stress_level": "critical",
            "cascade_depth_min": 3,
            "confidence_adjustment_min": -0.20,
        },
    ),
    ScenarioSeed(
        scenario_id="maritime_risk_surge",
        title="Maritime Risk Surge Corridor",
        title_ar="ارتفاع المخاطر البحرية",
        description=(
            "Sustained piracy, hostile boarding, or smuggling activity in Arabian Sea "
            "and Gulf of Aden corridors. Affects Red Sea diversion routes, increases "
            "insurance costs 35-50%, forces vessel speed reductions, and creates "
            "2-week cargo delays through expanded security protocols."
        ),
        inject_events=[
            {
                "event_type": EventType.MARITIME_RISK_SURGE.value,
                "latitude": 12.5, 
                "longitude": 53.5,
                "severity": 0.75,
                "affected_corridors": ["cor-009", "cor-010"],
                "duration_hours": 504,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.42,
                "region": "Red Sea-Gulf of Aden",
                "duration_hours": 504,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.65,
                "delay_hours_min": 120,
                "delay_hours_max": 168,
                "affected_corridors": ["cor-009", "cor-010"],
                "duration_hours": 504,
            },
        ],
        affected_node_ids=[
            "prt-001",
            "prt-003",
            "prt-004",
            "cor-009",
            "cor-010",
            "apt-002",
            "apt-003",
        ],
        severity=0.68,
        time_horizon_hours=504,
        propagation_coefficient=0.65,
        expected_output={
            "risk_increase_min": 0.22,
            "risk_increase_max": 0.42,
            "affected_corridors_min": 2,
            "affected_ports_min": 4,
            "insurance_surge_min": 0.35,
            "insurance_surge_max": 0.50,
            "avg_delay_hours_min": 96,
            "system_stress_level": "elevated",
            "cascade_depth_min": 2,
        },
    ),
    ScenarioSeed(
        scenario_id="combined_disruption",
        title="Combined Disruption (Hormuz + Airspace)",
        title_ar="تعطل مدمج",
        description=(
            "Simultaneous Hormuz blockade AND GCC airspace closure. Dual-vector "
            "attack on maritime and aviation corridors. Forces all traffic to "
            "international routes, creates system-wide bottlenecks, and escalates "
            "insurance costs 50-70%. System stress reaches 'critical' across "
            "all infrastructure domains."
        ),
        inject_events=[
            {
                "event_type": EventType.NAVAL_BLOCKADE.value,
                "latitude": 26.5667,
                "longitude": 56.2500,
                "severity": 0.92,
                "affected_corridors": ["cor-001", "cor-002"],
                "duration_hours": 168,
            },
            {
                "event_type": EventType.AIRSPACE_CLOSURE.value,
                "affected_airports": ["apt-001", "apt-006", "apt-008", "apt-011"],
                "severity": 0.78,
                "duration_hours": 168,
            },
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 26.2,
                "longitude": 56.4,
                "severity": 0.80,
                "radius_nm": 50,
                "duration_hours": 168,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.55,
                "region": "GCC",
                "duration_hours": 336,
            },
        ],
        affected_node_ids=[
            "apt-001",
            "apt-006",
            "apt-008",
            "apt-011",
            "prt-001",
            "prt-002",
            "prt-005",
            "prt-006",
            "prt-010",
            "cor-001",
            "cor-002",
            "cor-003",
        ],
        severity=0.88,
        time_horizon_hours=168,
        propagation_coefficient=0.82,
        expected_output={
            "risk_increase_min": 0.40,
            "risk_increase_max": 0.65,
            "affected_airports_min": 4,
            "affected_ports_min": 8,
            "affected_corridors_min": 4,
            "affected_flights_min": 300,
            "insurance_surge_min": 0.50,
            "insurance_surge_max": 0.70,
            "system_stress_level": "critical",
            "cascade_depth_min": 4,
        },
    ),
    ScenarioSeed(
        scenario_id="insurance_surge",
        title="Insurance Surge Event",
        title_ar="ارتفاع تكاليف التأمين",
        description=(
            "Major maritime incident (ship grounding, tanker collision, container loss) "
            "in high-traffic corridor triggers insurance industry downgrades. Major "
            "underwriters exit GCC risk pools temporarily. Premium rates spike 40-60% "
            "across all vessel classes. Affects cargo affordability and route economics."
        ),
        inject_events=[
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.70,
                "region": "Arabian Gulf",
                "duration_hours": 240,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.50,
                "delay_hours_min": 24,
                "delay_hours_max": 48,
                "affected_ports": ["prt-005", "prt-006", "prt-008"],
                "duration_hours": 240,
            },
        ],
        affected_node_ids=[
            "prt-001",
            "prt-005",
            "prt-006",
            "prt-008",
            "prt-010",
            "cor-001",
            "cor-005",
        ],
        severity=0.62,
        time_horizon_hours=240,
        propagation_coefficient=0.68,
        expected_output={
            "risk_increase_min": 0.15,
            "risk_increase_max": 0.32,
            "affected_ports_min": 5,
            "insurance_surge_min": 0.40,
            "insurance_surge_max": 0.60,
            "cargo_cost_increase_min": 0.35,
            "cargo_cost_increase_max": 0.55,
            "system_stress_level": "elevated",
            "cascade_depth_min": 1,
        },
    ),
    ScenarioSeed(
        scenario_id="executive_board",
        title="Executive Board Multi-Timeframe",
        title_ar="السيناريو التنفيذي متعدد الفترات",
        description=(
            "Strategic-level scenario for C-suite decision-making. Models 1-month "
            "impact of sustained regional instability on executive KPIs: revenue impact, "
            "supply chain resilience, insurance costs, and stakeholder confidence. "
            "Combines moderate shocks across 3-5 corridors with high confidence."
        ),
        inject_events=[
            {
                "event_type": EventType.AIRSPACE_CLOSURE.value,
                "affected_airports": ["apt-001", "apt-006"],
                "severity": 0.60,
                "duration_hours": 720,
            },
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 26.5667,
                "longitude": 56.2500,
                "severity": 0.55,
                "radius_nm": 100,
                "duration_hours": 720,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.35,
                "region": "GCC",
                "duration_hours": 720,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.40,
                "delay_hours_min": 12,
                "delay_hours_max": 36,
                "affected_ports": ["prt-005", "prt-006", "prt-010"],
                "duration_hours": 720,
            },
        ],
        affected_node_ids=[
            "apt-001",
            "apt-006",
            "apt-008",
            "prt-005",
            "prt-006",
            "prt-010",
            "cor-001",
            "cor-003",
        ],
        severity=0.58,
        time_horizon_hours=720,
        propagation_coefficient=0.70,
        expected_output={
            "risk_increase_min": 0.12,
            "risk_increase_max": 0.28,
            "affected_airports_min": 3,
            "affected_ports_min": 3,
            "affected_corridors_min": 2,
            "revenue_impact_min": -0.08,
            "revenue_impact_max": -0.18,
            "insurance_cost_increase_min": 0.20,
            "system_stress_level": "elevated",
            "cascade_depth_min": 2,
            "confidence_min": 0.75,
        },
    ),
    ScenarioSeed(
        scenario_id="red_sea_diversion",
        title="Red Sea Diversion Route Stress",
        title_ar="ضغط طرق التحويل في البحر الأحمر",
        description=(
            "Hormuz closure forces 70% of traffic to Red Sea diversion routes. "
            "Creates congestion at Suez, stresses port facilities at Jeddah/Yanbu, "
            "increases fuel burn by 25%, and escalates piracy insurance premiums. "
            "3-week transit delays cascade to port schedules and air freight demand."
        ),
        inject_events=[
            {
                "event_type": EventType.NAVAL_BLOCKADE.value,
                "latitude": 26.5667,
                "longitude": 56.2500,
                "severity": 0.90,
                "affected_corridors": ["cor-001", "cor-002"],
                "duration_hours": 336,
            },
            {
                "event_type": EventType.VESSEL_DIVERSION.value,
                "severity": 0.75,
                "reroute_distance_increase_nm": 400,
                "affected_ports": ["prt-001", "prt-003"],
                "duration_hours": 336,
            },
            {
                "event_type": EventType.PORT_DAMAGE.value,
                "affected_port": "prt-001",
                "severity": 0.60,
                "capacity_reduction": 0.40,
                "duration_hours": 336,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.70,
                "delay_hours_min": 168,
                "delay_hours_max": 240,
                "affected_ports": ["prt-001", "prt-003"],
                "duration_hours": 336,
            },
        ],
        affected_node_ids=[
            "prt-001",
            "prt-003",
            "prt-004",
            "prt-002",
            "apt-002",
            "apt-003",
            "cor-001",
            "cor-005",
            "cor-009",
        ],
        severity=0.75,
        time_horizon_hours=336,
        propagation_coefficient=0.73,
        expected_output={
            "risk_increase_min": 0.25,
            "risk_increase_max": 0.42,
            "affected_ports_min": 4,
            "affected_corridors_min": 3,
            "avg_delay_hours_min": 144,
            "avg_delay_hours_max": 216,
            "fuel_cost_increase_min": 0.22,
            "fuel_cost_increase_max": 0.32,
            "system_stress_level": "high",
            "cascade_depth_min": 3,
        },
    ),
    ScenarioSeed(
        scenario_id="dual_disruption",
        title="Dual Disruption (Maritime + Aviation)",
        title_ar="تعطل ثنائي",
        description=(
            "Simultaneous maritime and aviation disruptions (port damage + airspace "
            "closure) affecting complementary modal split. Removes modal redundancy, "
            "forces cargo onto congested remaining routes, and creates system-wide "
            "bottleneck. Affects 6+ ports/airports and 4+ corridors."
        ),
        inject_events=[
            {
                "event_type": EventType.PORT_DAMAGE.value,
                "affected_port": "prt-005",
                "severity": 0.80,
                "capacity_reduction": 0.60,
                "duration_hours": 240,
            },
            {
                "event_type": EventType.AIRSPACE_CLOSURE.value,
                "affected_airports": ["apt-001", "apt-006"],
                "severity": 0.75,
                "duration_hours": 240,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.70,
                "delay_hours_min": 96,
                "delay_hours_max": 168,
                "affected_ports": ["prt-005", "prt-006"],
                "duration_hours": 240,
            },
            {
                "event_type": EventType.FLIGHT_DIVERSION.value,
                "severity": 0.65,
                "reroute_distance_increase_nm": 200,
                "affected_airports": ["apt-001", "apt-006"],
                "duration_hours": 240,
            },
        ],
        affected_node_ids=[
            "apt-001",
            "apt-006",
            "apt-008",
            "prt-005",
            "prt-006",
            "prt-009",
            "cor-003",
            "cor-005",
        ],
        severity=0.78,
        time_horizon_hours=240,
        propagation_coefficient=0.77,
        expected_output={
            "risk_increase_min": 0.30,
            "risk_increase_max": 0.50,
            "affected_airports_min": 3,
            "affected_ports_min": 3,
            "affected_corridors_min": 2,
            "affected_flights_diverted_min": 150,
            "cargo_consolidation_min": 0.40,
            "system_stress_level": "critical",
            "cascade_depth_min": 3,
        },
    ),
    ScenarioSeed(
        scenario_id="oil_corridor_risk",
        title="Oil Corridor Economic Impact",
        title_ar="تأثير اقتصادي على ممرات النفط",
        description=(
            "Sustained threat to energy corridors (tanker routes) affecting crude/LNG "
            "shipments. Drives Brent crude +5-8 USD/barrel, escalates energy costs for "
            "electricity generation and desalination. Cascades to airline fuel costs, "
            "logistics margins, and insurance underwriting. 4-week event window."
        ),
        inject_events=[
            {
                "event_type": EventType.MARITIME_RISK_SURGE.value,
                "latitude": 26.5,
                "longitude": 56.2,
                "severity": 0.72,
                "affected_corridors": ["cor-001", "cor-002"],
                "duration_hours": 672,
            },
            {
                "event_type": EventType.INSURANCE_RATE_SPIKE.value,
                "severity": 0.48,
                "region": "Arabian Gulf - Energy",
                "duration_hours": 672,
            },
            {
                "event_type": EventType.LOGISTICS_DELAY.value,
                "severity": 0.55,
                "delay_hours_min": 48,
                "delay_hours_max": 96,
                "affected_ports": ["prt-002", "prt-010"],
                "duration_hours": 672,
            },
        ],
        affected_node_ids=[
            "prt-002",
            "prt-003",
            "prt-010",
            "prt-015",
            "cor-001",
            "cor-005",
            "apt-001",
            "apt-003",
        ],
        severity=0.68,
        time_horizon_hours=672,
        propagation_coefficient=0.69,
        expected_output={
            "risk_increase_min": 0.18,
            "risk_increase_max": 0.36,
            "affected_ports_min": 4,
            "affected_corridors_min": 2,
            "energy_cost_increase_min": 0.08,
            "energy_cost_increase_max": 0.15,
            "airline_fuel_cost_increase_min": 0.25,
            "insurance_surge_min": 0.30,
            "system_stress_level": "elevated",
            "cascade_depth_min": 2,
        },
    ),
    ScenarioSeed(
        scenario_id="false_signal",
        title="False Signal Low Confidence",
        title_ar="إشارة خاطئة",
        description=(
            "Unconfirmed intelligence report triggers defensive responses in supply "
            "chain (emergency rerouting, inventory builds). Information is later proven "
            "false, creating costly over-reaction and stranded inventory. Tests system "
            "confidence thresholds and intelligent filtering."
        ),
        inject_events=[
            {
                "event_type": EventType.MISSILE_THREAT.value,
                "latitude": 26.0,
                "longitude": 56.5,
                "severity": 0.45,
                "radius_nm": 60,
                "duration_hours": 24,
                "confidence": 0.35,
            },
        ],
        affected_node_ids=[
            "prt-005",
            "prt-006",
            "apt-006",
            "cor-001",
        ],
        severity=0.35,
        time_horizon_hours=24,
        propagation_coefficient=0.50,
        expected_output={
            "risk_increase_min": 0.08,
            "risk_increase_max": 0.15,
            "affected_ports_min": 2,
            "affected_airports_min": 1,
            "diversion_orders_executed_min": 5,
            "false_alarm_cost_min": 0.05,
            "system_stress_level": "nominal",
            "cascade_depth_min": 1,
            "confidence_adjustment_min": -0.25,
            "confidence_recovery_hours_min": 12,
        },
    ),
    ScenarioSeed(
        scenario_id="cascading_reroute",
        title="Cascading Reroute Overload",
        title_ar="التحويل المتسلسل والزيادة في الحمل",
        description=(
            "Single airport closure (apt-006 Dubai) triggers cascading reroutes to "
            "neighboring Sharjah (apt-007) and Abu Dhabi (apt-008). Secondary "
            "congestion forces further diversions, creating self-reinforcing reroute "
            "cascade. Models tipping points in network resilience."
        ),
        inject_events=[
            {
                "event_type": EventType.AIRPORT_SHUTDOWN.value,
                "affected_airport": "apt-006",
                "severity": 0.88,
                "duration_hours": 72,
            },
            {
                "event_type": EventType.FLIGHT_DIVERSION.value,
                "severity": 0.82,
                "reroute_distance_increase_nm": 120,
                "affected_airports": ["apt-007", "apt-008", "apt-001"],
                "duration_hours": 72,
            },
        ],
        affected_node_ids=[
            "apt-006",
            "apt-007",
            "apt-008",
            "apt-001",
            "prt-005",
            "prt-006",
            "cor-003",
            "cor-004",
        ],
        severity=0.80,
        time_horizon_hours=72,
        propagation_coefficient=0.79,
        expected_output={
            "risk_increase_min": 0.22,
            "risk_increase_max": 0.40,
            "affected_airports_min": 4,
            "affected_flights_diverted_min": 250,
            "cascade_wave_count_min": 2,
            "system_stress_level": "critical",
            "cascade_depth_min": 3,
            "secondary_airport_overload_pct_min": 0.60,
        },
    ),
]

# Validation helper
def get_scenario_seed_by_id(scenario_id: str) -> ScenarioSeed:
    """Retrieve a scenario seed by its ID."""
    for seed in SCENARIO_SEEDS:
        if seed.scenario_id == scenario_id:
            return seed
    raise ValueError(f"Scenario '{scenario_id}' not found in SCENARIO_SEEDS")


def list_scenario_ids() -> List[str]:
    """Return list of all scenario IDs."""
    return [seed.scenario_id for seed in SCENARIO_SEEDS]


def validate_scenario_seed(seed: ScenarioSeed) -> tuple[bool, List[str]]:
    """
    Validate a scenario seed for completeness.
    
    Returns:
        (is_valid, list of error messages)
    """
    errors = []
    
    if not seed.scenario_id:
        errors.append("scenario_id cannot be empty")
    if not seed.title:
        errors.append("title cannot be empty")
    if not seed.title_ar:
        errors.append("title_ar cannot be empty")
    if not seed.inject_events:
        errors.append("inject_events cannot be empty")
    if not seed.affected_node_ids:
        errors.append("affected_node_ids cannot be empty")
    if not (0.0 <= seed.severity <= 1.0):
        errors.append(f"severity must be 0.0-1.0, got {seed.severity}")
    if seed.time_horizon_hours <= 0:
        errors.append(f"time_horizon_hours must be > 0, got {seed.time_horizon_hours}")
    if not (0.0 <= seed.propagation_coefficient <= 1.0):
        errors.append(f"propagation_coefficient must be 0.0-1.0, got {seed.propagation_coefficient}")
    if not seed.expected_output:
        errors.append("expected_output cannot be empty")
    
    return len(errors) == 0, errors
