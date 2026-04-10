"""Pre-defined scenario templates for GCC decision intelligence.

Each template provides shocks, horizon, and metadata.
These are injected into the ScenarioEngine for simulation.
"""

from src.models.canonical import (
    DisruptionType,
    Provenance,
    Scenario,
    ScenarioShock,
    SourceType,
)

_PROV = Provenance(source_type=SourceType.MANUAL, source_name="scenario_library")


SCENARIO_TEMPLATES: list[Scenario] = [
    # 1. Strait of Hormuz disruption
    Scenario(
        id="hormuz_chokepoint_disruption",
        title="Strategic Maritime Chokepoint Disruption (Hormuz)",
        title_ar="تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)",
        description="Full or partial blockage of the Strait of Hormuz, disrupting oil tanker transit and Gulf shipping lanes.",
        description_ar="إغلاق كلي أو جزئي لمضيق هرمز مما يعطل عبور ناقلات النفط وممرات الشحن الخليجية.",
        scenario_type="disruption",
        horizon_hours=72,
        shocks=[
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.BLOCKADE, severity_score=0.95, description="Strait blockage"),
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.CLOSURE, severity_score=0.9, description="Gulf shipping halt"),
            ScenarioShock(target_entity_id="oil_sector", shock_type=DisruptionType.DELAY, severity_score=0.85, description="Oil export disruption"),
            ScenarioShock(target_entity_id="ras_tanura", shock_type=DisruptionType.CONGESTION, severity_score=0.8, description="Port backup"),
        ],
        provenance=_PROV,
    ),

    # 2. GCC airspace closure / partial rerouting
    Scenario(
        id="gcc_airspace_closure",
        title="GCC Airspace Closure / Rerouting",
        title_ar="إغلاق المجال الجوي الخليجي / إعادة توجيه",
        description="Partial or full closure of GCC airspace forcing mass flight rerouting, delays, and cancellations.",
        description_ar="إغلاق جزئي أو كلي للمجال الجوي الخليجي مما يفرض إعادة توجيه وتأخيرات جماعية.",
        scenario_type="disruption",
        horizon_hours=48,
        shocks=[
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.CLOSURE, severity_score=0.9, description="Airspace closure"),
            ScenarioShock(target_entity_id="dubai_apt", shock_type=DisruptionType.DELAY, severity_score=0.85, description="DXB grounded"),
            ScenarioShock(target_entity_id="riyadh_apt", shock_type=DisruptionType.DELAY, severity_score=0.8, description="RUH delays"),
            ScenarioShock(target_entity_id="doha_apt", shock_type=DisruptionType.REROUTE, severity_score=0.75, description="DOH rerouting"),
            ScenarioShock(target_entity_id="aviation", shock_type=DisruptionType.DELAY, severity_score=0.88, description="Aviation sector halt"),
        ],
        provenance=_PROV,
    ),

    # 3. Missile escalation near Gulf maritime corridors
    Scenario(
        id="missile_escalation_maritime",
        title="Missile Escalation Near Maritime Corridors",
        title_ar="تصعيد صاروخي قرب الممرات البحرية",
        description="Missile strikes or threats near Gulf shipping lanes, threatening vessel safety and forcing rerouting.",
        description_ar="ضربات أو تهديدات صاروخية قرب ممرات الشحن الخليجية تهدد سلامة السفن.",
        scenario_type="escalation",
        horizon_hours=72,
        shocks=[
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.REROUTE, severity_score=0.85, description="Vessel rerouting"),
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.ESCALATION, severity_score=0.7, description="Strait threat"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.8, description="War risk premium surge"),
            ScenarioShock(target_entity_id="jebel_ali", shock_type=DisruptionType.CONGESTION, severity_score=0.6, description="Port congestion from reroutes"),
        ],
        provenance=_PROV,
    ),

    # 4. Airport shutdown in a major GCC hub
    Scenario(
        id="major_airport_shutdown",
        title="Major GCC Airport Shutdown",
        title_ar="إغلاق مطار رئيسي في الخليج",
        description="Complete shutdown of Dubai International Airport due to security incident or infrastructure failure.",
        description_ar="إغلاق كامل لمطار دبي الدولي بسبب حادث أمني أو عطل بنية تحتية.",
        scenario_type="disruption",
        horizon_hours=24,
        shocks=[
            ScenarioShock(target_entity_id="dubai_apt", shock_type=DisruptionType.CLOSURE, severity_score=0.95, description="DXB full closure"),
            ScenarioShock(target_entity_id="aviation", shock_type=DisruptionType.DELAY, severity_score=0.7, description="Regional aviation cascade"),
            ScenarioShock(target_entity_id="tourism", shock_type=DisruptionType.DELAY, severity_score=0.6, description="Tourism disruption"),
            ScenarioShock(target_entity_id="travelers", shock_type=DisruptionType.DELAY, severity_score=0.65, description="Passenger stranding"),
        ],
        provenance=_PROV,
    ),

    # 5. Port congestion spike in UAE / KSA / Kuwait
    Scenario(
        id="port_congestion_surge",
        title="Gulf Port Congestion Surge",
        title_ar="ارتفاع حاد في ازدحام الموانئ الخليجية",
        description="Simultaneous congestion spikes at Jebel Ali, Ras Tanura, and Shuwaikh ports.",
        description_ar="ارتفاع متزامن في الازدحام بموانئ جبل علي ورأس تنورة والشويخ.",
        scenario_type="disruption",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="jebel_ali", shock_type=DisruptionType.CONGESTION, severity_score=0.8, description="Jebel Ali backup"),
            ScenarioShock(target_entity_id="ras_tanura", shock_type=DisruptionType.CONGESTION, severity_score=0.75, description="Ras Tanura backup"),
            ScenarioShock(target_entity_id="shuwaikh", shock_type=DisruptionType.CONGESTION, severity_score=0.7, description="Shuwaikh backup"),
            ScenarioShock(target_entity_id="supply_chain", shock_type=DisruptionType.DELAY, severity_score=0.65, description="Supply chain slowdown"),
            ScenarioShock(target_entity_id="logistics", shock_type=DisruptionType.DELAY, severity_score=0.6, description="Logistics degradation"),
        ],
        provenance=_PROV,
    ),

    # 6. Conflict spillover from Iraq / Iran / Yemen into GCC routes
    Scenario(
        id="conflict_spillover",
        title="Regional Conflict Spillover into GCC",
        title_ar="امتداد النزاع الإقليمي إلى مسارات الخليج",
        description="Armed conflict escalation in neighboring states spilling over into GCC trade routes and airspace.",
        description_ar="تصاعد النزاع المسلح في الدول المجاورة يمتد إلى مسارات التجارة والمجال الجوي الخليجي.",
        scenario_type="escalation",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.REROUTE, severity_score=0.7, description="Airspace restrictions"),
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.REROUTE, severity_score=0.65, description="Shipping detours"),
            ScenarioShock(target_entity_id="stability", shock_type=DisruptionType.ESCALATION, severity_score=0.6, description="Stability concern"),
            ScenarioShock(target_entity_id="sentiment", shock_type=DisruptionType.ESCALATION, severity_score=0.55, description="Public anxiety"),
            ScenarioShock(target_entity_id="fin_markets", shock_type=DisruptionType.DELAY, severity_score=0.5, description="Market volatility"),
        ],
        provenance=_PROV,
    ),

    # 7. Multi-point maritime risk surge across Gulf shipping lanes
    Scenario(
        id="maritime_risk_surge",
        title="Gulf Maritime Risk Surge",
        title_ar="ارتفاع مخاطر بحرية متعددة النقاط في الخليج",
        description="Coordinated incidents across multiple Gulf shipping corridors raising maritime risk simultaneously.",
        description_ar="حوادث منسقة عبر ممرات شحن خليجية متعددة ترفع المخاطر البحرية.",
        scenario_type="cascading",
        horizon_hours=72,
        shocks=[
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.ESCALATION, severity_score=0.8, description="Hormuz threat"),
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.REROUTE, severity_score=0.75, description="Lane disruptions"),
            ScenarioShock(target_entity_id="hamad_port", shock_type=DisruptionType.CONGESTION, severity_score=0.6, description="Hamad congestion"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.85, description="Marine insurance spike"),
            ScenarioShock(target_entity_id="reinsurance", shock_type=DisruptionType.ESCALATION, severity_score=0.7, description="Reinsurance exposure"),
        ],
        provenance=_PROV,
    ),

    # 8. Combined aviation + maritime + conflict cascade
    Scenario(
        id="triple_cascade",
        title="Triple Cascade: Aviation + Maritime + Conflict",
        title_ar="تصعيد ثلاثي: طيران + بحري + نزاع",
        description="Simultaneous aviation disruption, maritime chokepoint blockage, and active conflict escalation.",
        description_ar="تعطل طيران وانسداد ممرات بحرية وتصعيد نزاع مسلح في وقت واحد.",
        scenario_type="cascading",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.CLOSURE, severity_score=0.85, description="Airspace shutdown"),
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.BLOCKADE, severity_score=0.9, description="Strait blockade"),
            ScenarioShock(target_entity_id="stability", shock_type=DisruptionType.ESCALATION, severity_score=0.75, description="Conflict escalation"),
            ScenarioShock(target_entity_id="oil_sector", shock_type=DisruptionType.DELAY, severity_score=0.8, description="Oil disruption"),
            ScenarioShock(target_entity_id="gdp", shock_type=DisruptionType.DELAY, severity_score=0.7, description="GDP pressure"),
            ScenarioShock(target_entity_id="fin_markets", shock_type=DisruptionType.DELAY, severity_score=0.65, description="Market selloff"),
        ],
        provenance=_PROV,
    ),

    # 9. Insurance claims surge from logistics disruption
    Scenario(
        id="insurance_surge",
        title="Insurance Claims Surge from Logistics Disruption",
        title_ar="ارتفاع مطالبات التأمين من تعطل الخدمات اللوجستية",
        description="Cascading logistics failure triggers mass insurance claims across cargo, marine, and aviation lines.",
        description_ar="فشل لوجستي متسلسل يؤدي لمطالبات تأمين جماعية عبر خطوط الشحن والبحري والطيران.",
        scenario_type="cascading",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="logistics", shock_type=DisruptionType.DELAY, severity_score=0.8, description="Logistics breakdown"),
            ScenarioShock(target_entity_id="supply_chain", shock_type=DisruptionType.DELAY, severity_score=0.75, description="Supply chain cascade"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.9, description="Claims surge"),
            ScenarioShock(target_entity_id="reinsurance", shock_type=DisruptionType.ESCALATION, severity_score=0.8, description="Reinsurance stress"),
            ScenarioShock(target_entity_id="businesses", shock_type=DisruptionType.DELAY, severity_score=0.6, description="Business interruption"),
        ],
        provenance=_PROV,
    ),

    # 10. Executive board scenario: multi-horizon impact assessment
    Scenario(
        id="executive_board_assessment",
        title="Executive Board: GCC Mobility & Insurance Exposure",
        title_ar="تقييم مجلس الإدارة: التنقل والتعرض التأميني في الخليج",
        description="What will be the 24h / 72h / 7d impact on GCC mobility and insurance exposure from current threat conditions?",
        description_ar="ما هو تأثير 24 ساعة / 72 ساعة / 7 أيام على التنقل والتعرض التأميني في الخليج من الظروف الحالية؟",
        scenario_type="hypothetical",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.DELAY, severity_score=0.5, description="Elevated maritime risk"),
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.REROUTE, severity_score=0.4, description="Partial airspace restrictions"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.6, description="Rising premiums"),
            ScenarioShock(target_entity_id="oil_sector", shock_type=DisruptionType.DELAY, severity_score=0.35, description="Oil flow pressure"),
        ],
        provenance=_PROV,
    ),
]


# Merge extended templates
from src.engines.scenario.templates_extended import EXTENDED_TEMPLATES
SCENARIO_TEMPLATES.extend(EXTENDED_TEMPLATES)


def get_template(scenario_id: str) -> Scenario | None:
    """Look up a scenario template by ID."""
    for t in SCENARIO_TEMPLATES:
        if t.id == scenario_id:
            return t.model_copy(deep=True)
    return None


def list_templates() -> list[dict]:
    """Return summary of all templates."""
    return [
        {
            "id": t.id,
            "title": t.title,
            "title_ar": t.title_ar,
            "scenario_type": t.scenario_type,
            "horizon_hours": t.horizon_hours,
            "shock_count": len(t.shocks),
        }
        for t in SCENARIO_TEMPLATES
    ]
