"""
Scenario Templates for the Impact Observatory.

Defines 15 predefined disruption scenarios with comprehensive parameters
for modeling critical disruption events in GCC infrastructure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class DisruptionType(Enum):
    """Types of disruption scenarios."""
    GEOPOLITICAL = "geopolitical"
    INFRASTRUCTURE = "infrastructure"
    MARITIME = "maritime"
    AVIATION = "aviation"
    COMBINED = "combined"
    SYSTEMIC = "systemic"
    ENERGY = "energy"


class ScenarioDomain(Enum):
    """Domains affected by disruptions."""
    MARITIME = "maritime"
    AVIATION = "aviation"
    LAND = "land"
    ENERGY = "energy"
    TELECOMMUNICATION = "telecommunication"


@dataclass
class ScenarioTemplate:
    """
    Base template for disruption scenarios.
    
    Attributes:
        name: Unique scenario identifier (kebab-case)
        title: Human-readable scenario title
        description: Detailed scenario narrative
        disruption_type: Category of disruption
        severity: Baseline severity on 0.0-1.0 scale
        affected_domains: List of affected infrastructure domains
        affected_regions: Geographic regions impacted
        affected_countries: Countries directly impacted
        duration_hours: Expected scenario duration
        propagation_depth: Network propagation hops (shock cascade depth)
        key_assumptions: Critical modeling assumptions
        uncertainty_factors: Sources of uncertainty
        shock_event_locations: Dict of node_id -> shock severity for initial shocks
        propagation_coefficient: Alpha parameter for risk propagation (0.0-1.0)
        confidence_baseline: Baseline confidence in scenario parameters
        scenario_tags: Categorization tags for filtering
    """
    
    name: str
    title: str
    description: str
    disruption_type: DisruptionType
    severity: float
    affected_domains: List[ScenarioDomain]
    affected_regions: List[str]
    affected_countries: List[str]
    duration_hours: int
    propagation_depth: int
    key_assumptions: List[str]
    uncertainty_factors: List[str]
    shock_event_locations: Dict[str, float]
    propagation_coefficient: float = 0.7
    confidence_baseline: float = 0.85
    scenario_tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary."""
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'disruption_type': self.disruption_type.value,
            'severity': self.severity,
            'affected_domains': [d.value for d in self.affected_domains],
            'affected_regions': self.affected_regions,
            'affected_countries': self.affected_countries,
            'duration_hours': self.duration_hours,
            'propagation_depth': self.propagation_depth,
            'key_assumptions': self.key_assumptions,
            'uncertainty_factors': self.uncertainty_factors,
            'shock_event_locations': self.shock_event_locations,
            'propagation_coefficient': self.propagation_coefficient,
            'confidence_baseline': self.confidence_baseline,
            'scenario_tags': self.scenario_tags,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# 15 PREDEFINED SCENARIO TEMPLATES
# ============================================================================

HORMUZ_CLOSURE = ScenarioTemplate(
    name="hormuz_closure",
    title="Strait of Hormuz Closure",
    description="Complete closure of the Strait of Hormuz due to geopolitical crisis, "
                "blocking ~30% of global seaborne oil trade. Affects all maritime routes through "
                "the Persian Gulf and forces rerouting via alternative passages.",
    disruption_type=DisruptionType.MARITIME,
    severity=0.95,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
    affected_regions=["Persian Gulf", "Arabian Sea", "Indian Ocean"],
    affected_countries=["UAE", "Saudi Arabia", "Oman", "Iran", "Kuwait"],
    duration_hours=72,
    propagation_depth=4,
    key_assumptions=[
        "Complete blockade of maritime traffic",
        "Alternative routes via Suez and Cape of Good Hope are available",
        "Shipping delays of 15-30 days for rerouted vessels",
        "Oil price volatility of 20-40%"
    ],
    uncertainty_factors=[
        "Duration of closure (could extend beyond 72 hours)",
        "Extent of merchant vessel disruption vs. tanker prioritization",
        "Geopolitical escalation factors"
    ],
    shock_event_locations={
        "hormuz_strait_node": 0.9,
        "dubai_port": 0.6,
        "jebel_ali_node": 0.5
    },
    propagation_coefficient=0.75,
    confidence_baseline=0.88,
    scenario_tags=["maritime", "geopolitical", "critical", "high-impact"]
)

GCC_AIRSPACE_CLOSURE = ScenarioTemplate(
    name="gcc_airspace_closure",
    title="GCC Airspace Closure",
    description="Airspace closure across GCC nations due to military escalation. "
                "Disrupts all civil aviation, forcing rerouting of international flights away from "
                "the Arabian Peninsula and through alternative corridors via Turkey or Pakistan.",
    disruption_type=DisruptionType.AVIATION,
    severity=0.92,
    affected_domains=[ScenarioDomain.AVIATION, ScenarioDomain.TELECOMMUNICATION],
    affected_regions=["Arabian Peninsula", "Persian Gulf Airspace", "Indian Ocean Lanes"],
    affected_countries=["UAE", "Saudi Arabia", "Qatar", "Oman", "Kuwait", "Bahrain"],
    duration_hours=168,
    propagation_depth=3,
    key_assumptions=[
        "Complete airspace closure across all GCC states",
        "All commercial flights rerouted via alternative FIRs",
        "25% increase in flight times to major destinations",
        "Additional fuel costs of 10-15% per flight"
    ],
    uncertainty_factors=[
        "Partial airspace reopening during crisis",
        "Humanitarian flight exemptions",
        "Military activity intensity"
    ],
    shock_event_locations={
        "dubai_intl_airport": 0.85,
        "abu_dhabi_airport": 0.80,
        "doha_airport": 0.75,
        "riyadh_airport": 0.70
    },
    propagation_coefficient=0.72,
    confidence_baseline=0.86,
    scenario_tags=["aviation", "geopolitical", "high-impact"]
)

MISSILE_ESCALATION = ScenarioTemplate(
    name="missile_escalation",
    title="Missile Escalation Event",
    description="Regional missile attacks targeting critical infrastructure (ports, airports, energy facilities). "
                "Creates widespread disruption through direct damage, secondary cascades, and defensive responses.",
    disruption_type=DisruptionType.GEOPOLITICAL,
    severity=0.88,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION, ScenarioDomain.ENERGY],
    affected_regions=["Persian Gulf", "Arabian Peninsula", "Strategic Corridors"],
    affected_countries=["UAE", "Saudi Arabia", "Kuwait"],
    duration_hours=240,
    propagation_depth=5,
    key_assumptions=[
        "Missiles target 3-5 major infrastructure nodes",
        "Direct damage reduces throughput by 50-70%",
        "Secondary cascades through network propagation",
        "Recovery requires 7-14 days for damaged facilities"
    ],
    uncertainty_factors=[
        "Number and precision of missile strikes",
        "Defensive system effectiveness",
        "Actual vs. threatened damage"
    ],
    shock_event_locations={
        "jebel_ali_port": 0.80,
        "dubai_intl_airport": 0.75,
        "ras_al_khaimah_energy": 0.70,
        "abu_dhabi_port": 0.65
    },
    propagation_coefficient=0.78,
    confidence_baseline=0.82,
    scenario_tags=["geopolitical", "military", "cascading", "high-impact"]
)

AIRPORT_SHUTDOWN = ScenarioTemplate(
    name="airport_shutdown",
    title="Major Airport Shutdown",
    description="Complete operational shutdown of a major hub airport (Dubai, Doha, Abu Dhabi, or Riyadh) "
                "due to infrastructure damage, technical failure, or security closure. Cascades to other airports "
                "and reduces network capacity significantly.",
    disruption_type=DisruptionType.AVIATION,
    severity=0.75,
    affected_domains=[ScenarioDomain.AVIATION],
    affected_regions=["Arabian Peninsula", "Regional Routes"],
    affected_countries=["UAE", "Qatar", "Saudi Arabia"],
    duration_hours=96,
    propagation_depth=2,
    key_assumptions=[
        "Single major airport completely non-operational",
        "Passenger and cargo redirection to adjacent airports",
        "30% capacity increase at substitute airports",
        "Operations return to normal within 4 days"
    ],
    uncertainty_factors=[
        "Duration of shutdown",
        "Spillover to secondary airports",
        "Airline routing flexibility"
    ],
    shock_event_locations={
        "dubai_intl_airport": 0.90
    },
    propagation_coefficient=0.65,
    confidence_baseline=0.90,
    scenario_tags=["aviation", "infrastructure", "operational"]
)

PORT_CONGESTION = ScenarioTemplate(
    name="port_congestion",
    title="Port Congestion Crisis",
    description="Severe port congestion in major GCC ports (Jebel Ali, Abu Dhabi, King Abdulaziz) "
                "due to volume surge, equipment failure, or labor disruptions. Creates cascading "
                "delays throughout maritime and supply chain networks.",
    disruption_type=DisruptionType.MARITIME,
    severity=0.65,
    affected_domains=[ScenarioDomain.MARITIME],
    affected_regions=["Persian Gulf", "Straits", "Regional Trade Routes"],
    affected_countries=["UAE", "Saudi Arabia"],
    duration_hours=120,
    propagation_depth=2,
    key_assumptions=[
        "Port capacity reduced by 40-50%",
        "Queue build-up of 300-500 vessels",
        "Dwell times increase to 10-15 days",
        "Alternative ports absorb overflow"
    ],
    uncertainty_factors=[
        "Root cause resolution speed",
        "Vessel diversion patterns",
        "Secondary congestion at alternative ports"
    ],
    shock_event_locations={
        "jebel_ali_port": 0.70,
        "abu_dhabi_port": 0.55
    },
    propagation_coefficient=0.68,
    confidence_baseline=0.85,
    scenario_tags=["maritime", "congestion", "operational"]
)

CONFLICT_SPILLOVER = ScenarioTemplate(
    name="conflict_spillover",
    title="Conflict Spillover into GCC",
    description="Regional conflict escalates and spills into GCC territory with limited military engagement. "
                "Creates uncertainty, temporary closures of critical nodes, and reduced throughput across "
                "maritime and aviation networks.",
    disruption_type=DisruptionType.GEOPOLITICAL,
    severity=0.72,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION],
    affected_regions=["Arabian Peninsula", "Persian Gulf"],
    affected_countries=["UAE", "Saudi Arabia", "Kuwait"],
    duration_hours=192,
    propagation_depth=3,
    key_assumptions=[
        "Limited direct military action within GCC",
        "Heightened security measures reduce throughput by 25-30%",
        "Insurance costs increase 15-25%",
        "Some shipping companies suspend routes temporarily"
    ],
    uncertainty_factors=[
        "Escalation probability",
        "International response timing",
        "Shipping industry risk appetite"
    ],
    shock_event_locations={
        "hormuz_strait_node": 0.60,
        "bab_el_mandeb": 0.50,
        "dubai_port": 0.40
    },
    propagation_coefficient=0.71,
    confidence_baseline=0.78,
    scenario_tags=["geopolitical", "uncertainty", "moderate-impact"]
)

MARITIME_RISK_SURGE = ScenarioTemplate(
    name="maritime_risk_surge",
    title="Maritime Risk Surge",
    description="Significant increase in maritime threats (piracy, mines, attacks on commercial vessels) "
                "reducing shipping appetite and increasing insurance costs. Routes through Red Sea and Persian Gulf "
                "see reduced utilization.",
    disruption_type=DisruptionType.MARITIME,
    severity=0.60,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
    affected_regions=["Red Sea", "Persian Gulf", "Arabian Sea"],
    affected_countries=["UAE", "Saudi Arabia", "Egypt", "Oman"],
    duration_hours=168,
    propagation_depth=2,
    key_assumptions=[
        "Maritime insurance premiums increase 20-40%",
        "10-15% of vessels reroute via longer but safer routes",
        "Shipping utilization drops 5-10% on risky routes",
        "Threat level gradually decreases over 7 days"
    ],
    uncertainty_factors=[
        "Actual threat incidents vs. threats",
        "Insurance market response speed",
        "Shipping company risk tolerance"
    ],
    shock_event_locations={
        "bab_el_mandeb": 0.55,
        "hormuz_strait_node": 0.50,
        "arabian_sea_corridor": 0.45
    },
    propagation_coefficient=0.66,
    confidence_baseline=0.81,
    scenario_tags=["maritime", "risk", "moderate-impact"]
)

COMBINED_DISRUPTION = ScenarioTemplate(
    name="combined_disruption",
    title="Combined Maritime and Aviation Disruption",
    description="Simultaneous disruption of both maritime and aviation networks through a major regional crisis. "
                "Severely impacts trade, logistics, and passenger movement across GCC and beyond.",
    disruption_type=DisruptionType.COMBINED,
    severity=0.85,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION],
    affected_regions=["Arabian Peninsula", "Persian Gulf", "Red Sea"],
    affected_countries=["UAE", "Saudi Arabia", "Qatar", "Oman"],
    duration_hours=240,
    propagation_depth=4,
    key_assumptions=[
        "Both maritime and aviation networks disrupted simultaneously",
        "Combined impact multiplier of 1.3-1.5x individual disruptions",
        "Trade delays 20-30% across all modes",
        "Recovery staggered over 8-10 days"
    ],
    uncertainty_factors=[
        "Correlation between maritime and aviation impacts",
        "Network recovery sequence",
        "Alternative route availability"
    ],
    shock_event_locations={
        "dubai_intl_airport": 0.75,
        "jebel_ali_port": 0.75,
        "hormuz_strait_node": 0.65,
        "abu_dhabi_airport": 0.60
    },
    propagation_coefficient=0.74,
    confidence_baseline=0.80,
    scenario_tags=["combined", "systemic", "high-impact"]
)

INSURANCE_SURGE = ScenarioTemplate(
    name="insurance_surge",
    title="Insurance Cost Surge",
    description="Significant increase in insurance costs across maritime and aviation due to "
                "accumulated risk events. Creates secondary economic shock affecting trade margins and routing decisions.",
    disruption_type=DisruptionType.SYSTEMIC,
    severity=0.55,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION],
    affected_regions=["GCC Wide", "International Routes"],
    affected_countries=["UAE", "Saudi Arabia", "Qatar", "Oman", "Kuwait"],
    duration_hours=240,
    propagation_depth=1,
    key_assumptions=[
        "Insurance costs increase 30-50% for GCC corridors",
        "Trade margins compressed by 2-3 percentage points",
        "Some routes become unprofitable, reduced utilization",
        "Recovery as underwriting appetite returns"
    ],
    uncertainty_factors=[
        "Insurance market volatility",
        "Actual loss experience",
        "Reinsurance capacity"
    ],
    shock_event_locations={
        "gcc_maritime_nodes": 0.40,
        "gcc_aviation_nodes": 0.35
    },
    propagation_coefficient=0.60,
    confidence_baseline=0.87,
    scenario_tags=["economic", "systemic", "moderate-impact"]
)

EXECUTIVE_BOARD = ScenarioTemplate(
    name="executive_board",
    title="Executive Board Crisis Decision Point",
    description="Hypothetical scenario for executive board decision-making and strategy review. "
                "Moderate geopolitical tension with cascading infrastructure impacts requiring strategic response.",
    disruption_type=DisruptionType.GEOPOLITICAL,
    severity=0.70,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION, ScenarioDomain.ENERGY],
    affected_regions=["Arabian Peninsula", "Persian Gulf"],
    affected_countries=["UAE", "Saudi Arabia"],
    duration_hours=120,
    propagation_depth=3,
    key_assumptions=[
        "Moderate geopolitical escalation with defined parameters",
        "Clear start and end conditions for crisis",
        "Multiple intervention points for decision-making",
        "Quantifiable outcomes for strategy evaluation"
    ],
    uncertainty_factors=[
        "Escalation trajectory",
        "Intervention effectiveness",
        "Market behavioral responses"
    ],
    shock_event_locations={
        "critical_port_node": 0.65,
        "major_airport_node": 0.60
    },
    propagation_coefficient=0.70,
    confidence_baseline=0.85,
    scenario_tags=["strategic", "exercise", "moderate-impact"]
)

RED_SEA_DIVERSION = ScenarioTemplate(
    name="red_sea_diversion",
    title="Red Sea Route Diversion",
    description="Significant diversion of Red Sea traffic away from traditional routes due to "
                "geopolitical tensions or security threats. Forces rerouting around Cape of Good Hope, "
                "significantly increasing transit times and costs.",
    disruption_type=DisruptionType.MARITIME,
    severity=0.68,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
    affected_regions=["Red Sea", "Suez Canal", "Indian Ocean", "Arabian Sea"],
    affected_countries=["Egypt", "Saudi Arabia", "UAE", "Oman"],
    duration_hours=192,
    propagation_depth=2,
    key_assumptions=[
        "30-50% of Red Sea traffic diverts around Cape",
        "Transit time increases by 10-15 days",
        "Shipping costs increase 15-25%",
        "Suez Canal revenues decrease significantly"
    ],
    uncertainty_factors=[
        "Severity and duration of Red Sea threat",
        "Shipping industry diversion willingness",
        "Fuel price impacts on longer routes"
    ],
    shock_event_locations={
        "red_sea_corridor": 0.70,
        "suez_canal_equivalent": 0.55,
        "gulf_of_aden": 0.60
    },
    propagation_coefficient=0.69,
    confidence_baseline=0.83,
    scenario_tags=["maritime", "routing", "high-impact"]
)

DUAL_DISRUPTION = ScenarioTemplate(
    name="dual_disruption",
    title="Dual Regional Disruption",
    description="Simultaneous crisis events in two different regions (e.g., Red Sea and Persian Gulf) "
                "creating multiple shock points and forcing major rerouting decisions across global trade networks.",
    disruption_type=DisruptionType.COMBINED,
    severity=0.80,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
    affected_regions=["Red Sea", "Persian Gulf", "Arabian Sea"],
    affected_countries=["Egypt", "Saudi Arabia", "UAE", "Oman", "Yemen"],
    duration_hours=240,
    propagation_depth=4,
    key_assumptions=[
        "Two independent crisis events occurring simultaneously",
        "Combined impact exceeds sum of individual impacts",
        "Global supply chain facing acute rerouting decisions",
        "Extended recovery due to dual disruption"
    ],
    uncertainty_factors=[
        "Correlation between dual events",
        "Global supply chain flexibility",
        "Demand destruction from higher costs"
    ],
    shock_event_locations={
        "red_sea_corridor": 0.70,
        "hormuz_strait_node": 0.70,
        "bab_el_mandeb": 0.60,
        "arabian_sea_node": 0.50
    },
    propagation_coefficient=0.73,
    confidence_baseline=0.77,
    scenario_tags=["combined", "systemic", "high-impact"]
)

OIL_CORRIDOR_RISK = ScenarioTemplate(
    name="oil_corridor_risk",
    title="Oil Corridor Risk Escalation",
    description="Escalation of threats to oil corridor infrastructure and shipping, creating "
                "significant uncertainty about energy supply security. Impacts global energy markets and GCC economic outlook.",
    disruption_type=DisruptionType.ENERGY,
    severity=0.78,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
    affected_regions=["Persian Gulf", "Oil Transit Routes"],
    affected_countries=["Saudi Arabia", "UAE", "Kuwait", "Oman"],
    duration_hours=168,
    propagation_depth=3,
    key_assumptions=[
        "Oil corridor infrastructure at elevated risk",
        "Insurance costs for tankers increase 25-40%",
        "Some producers reduce exports to avoid risk",
        "Oil price volatility increases 20-30%"
    ],
    uncertainty_factors=[
        "Actual vs. perceived risk to infrastructure",
        "Producer response decisions",
        "Global oil demand impacts"
    ],
    shock_event_locations={
        "hormuz_strait_node": 0.75,
        "bab_el_mandeb": 0.60,
        "arabian_gulf_production": 0.55
    },
    propagation_coefficient=0.70,
    confidence_baseline=0.80,
    scenario_tags=["energy", "risk", "high-impact"]
)

FALSE_SIGNAL = ScenarioTemplate(
    name="false_signal",
    title="False Signal / Flash Crisis",
    description="Sudden false information or misinterpreted signals triggering temporary market panic "
                "and operational changes. Short duration but significant impact on decision-making and routing patterns.",
    disruption_type=DisruptionType.SYSTEMIC,
    severity=0.50,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION],
    affected_regions=["GCC Wide"],
    affected_countries=["UAE", "Saudi Arabia", "Qatar"],
    duration_hours=24,
    propagation_depth=2,
    key_assumptions=[
        "False alert triggers immediate operational responses",
        "Market prices spike initially then revert",
        "Shipping companies alter routing temporarily",
        "Crisis resolves quickly once signal verified as false"
    ],
    uncertainty_factors=[
        "Signal origin and credibility",
        "Market overreaction magnitude",
        "Information cascade effects"
    ],
    shock_event_locations={
        "critical_nodes": 0.40
    },
    propagation_coefficient=0.65,
    confidence_baseline=0.75,
    scenario_tags=["flash", "short-duration", "psychological"]
)

CASCADING_REROUTE = ScenarioTemplate(
    name="cascading_reroute",
    title="Cascading Reroute Scenario",
    description="Initial disruption triggers sequential rerouting decisions across network that cascade "
                "into secondary bottlenecks. Models how shipping and aviation networks respond dynamically to "
                "initial shocks.",
    disruption_type=DisruptionType.SYSTEMIC,
    severity=0.73,
    affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.AVIATION],
    affected_regions=["GCC Wide", "Regional Routes"],
    affected_countries=["UAE", "Saudi Arabia", "Qatar", "Oman"],
    duration_hours=144,
    propagation_depth=5,
    key_assumptions=[
        "Initial shock creates congestion at primary route",
        "Traffic diverts to secondary routes",
        "Secondary routes reach capacity, creating tertiary bottlenecks",
        "Network finds new equilibrium after 5-6 days"
    ],
    uncertainty_factors=[
        "Alternative route capacity",
        "Shipper/airline routing behavior",
        "Rate impact on demand"
    ],
    shock_event_locations={
        "primary_corridor": 0.70,
        "secondary_corridor_1": 0.30,
        "secondary_corridor_2": 0.30
    },
    propagation_coefficient=0.76,
    confidence_baseline=0.82,
    scenario_tags=["cascading", "dynamic", "network-effects"]
)


# Template registry for easy access
SCENARIO_TEMPLATES = {
    "hormuz_closure": HORMUZ_CLOSURE,
    "gcc_airspace_closure": GCC_AIRSPACE_CLOSURE,
    "missile_escalation": MISSILE_ESCALATION,
    "airport_shutdown": AIRPORT_SHUTDOWN,
    "port_congestion": PORT_CONGESTION,
    "conflict_spillover": CONFLICT_SPILLOVER,
    "maritime_risk_surge": MARITIME_RISK_SURGE,
    "combined_disruption": COMBINED_DISRUPTION,
    "insurance_surge": INSURANCE_SURGE,
    "executive_board": EXECUTIVE_BOARD,
    "red_sea_diversion": RED_SEA_DIVERSION,
    "dual_disruption": DUAL_DISRUPTION,
    "oil_corridor_risk": OIL_CORRIDOR_RISK,
    "false_signal": FALSE_SIGNAL,
    "cascading_reroute": CASCADING_REROUTE,
}


def get_template(name: str) -> Optional[ScenarioTemplate]:
    """Get a scenario template by name."""
    return SCENARIO_TEMPLATES.get(name)


def list_templates() -> List[str]:
    """List all available template names."""
    return list(SCENARIO_TEMPLATES.keys())


def get_templates_by_disruption_type(disruption_type: DisruptionType) -> List[ScenarioTemplate]:
    """Get all templates of a specific disruption type."""
    return [t for t in SCENARIO_TEMPLATES.values() if t.disruption_type == disruption_type]


def get_templates_by_domain(domain: ScenarioDomain) -> List[ScenarioTemplate]:
    """Get all templates affecting a specific domain."""
    return [t for t in SCENARIO_TEMPLATES.values() if domain in t.affected_domains]
