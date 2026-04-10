"""Extended scenario templates 11-15."""

from src.models.canonical import (
    DisruptionType,
    Provenance,
    Scenario,
    ScenarioShock,
    SourceType,
)

_PROV = Provenance(source_type=SourceType.MANUAL, source_name="scenario_library")

EXTENDED_TEMPLATES: list[Scenario] = [
    # 11. Red Sea shipping diversion into Gulf consequences
    Scenario(
        id="red_sea_diversion",
        title="Red Sea Shipping Diversion into Gulf",
        title_ar="تحويل الشحن من البحر الأحمر إلى الخليج",
        description="Red Sea instability forces rerouting of major shipping through Gulf corridors, creating secondary congestion and insurance exposure.",
        description_ar="عدم استقرار البحر الأحمر يفرض إعادة توجيه الشحن الرئيسي عبر ممرات الخليج مما يخلق ازدحاماً ثانوياً وتعرضاً تأمينياً.",
        scenario_type="cascading",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.CONGESTION, severity_score=0.75, description="Rerouted traffic surge"),
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.CONGESTION, severity_score=0.65, description="Strait traffic spike"),
            ScenarioShock(target_entity_id="jebel_ali", shock_type=DisruptionType.CONGESTION, severity_score=0.7, description="Port overload"),
            ScenarioShock(target_entity_id="hamad_port", shock_type=DisruptionType.CONGESTION, severity_score=0.6, description="Port overload"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.7, description="War risk premium increase"),
            ScenarioShock(target_entity_id="logistics", shock_type=DisruptionType.DELAY, severity_score=0.6, description="Delivery delays"),
        ],
        provenance=_PROV,
    ),

    # 12. Simultaneous airport + port disruption in one GCC state
    Scenario(
        id="dual_hub_disruption_uae",
        title="Dual Hub Disruption: UAE Airport + Port",
        title_ar="تعطل مزدوج: مطار وميناء الإمارات",
        description="Simultaneous disruption of Dubai Airport and Jebel Ali Port due to coordinated infrastructure failure.",
        description_ar="تعطل متزامن لمطار دبي وميناء جبل علي بسبب فشل بنية تحتية منسق.",
        scenario_type="disruption",
        horizon_hours=48,
        shocks=[
            ScenarioShock(target_entity_id="dubai_apt", shock_type=DisruptionType.CLOSURE, severity_score=0.9, description="DXB shutdown"),
            ScenarioShock(target_entity_id="jebel_ali", shock_type=DisruptionType.CLOSURE, severity_score=0.85, description="Jebel Ali shutdown"),
            ScenarioShock(target_entity_id="aviation", shock_type=DisruptionType.REROUTE, severity_score=0.7, description="Flight diversions"),
            ScenarioShock(target_entity_id="shipping_sector", shock_type=DisruptionType.REROUTE, severity_score=0.65, description="Vessel rerouting"),
            ScenarioShock(target_entity_id="tourism", shock_type=DisruptionType.DELAY, severity_score=0.75, description="Tourism halt"),
            ScenarioShock(target_entity_id="supply_chain", shock_type=DisruptionType.DELAY, severity_score=0.8, description="Supply chain severed"),
        ],
        provenance=_PROV,
    ),

    # 13. Oil corridor risk escalation affecting logistics and insurance loss ratios
    Scenario(
        id="oil_corridor_escalation",
        title="Oil Corridor Risk Escalation — Insurance Impact",
        title_ar="تصعيد مخاطر ممرات النفط — التأثير التأميني",
        description="Sustained escalation along oil transport corridors drives up insurance loss ratios and logistics costs.",
        description_ar="تصعيد مستمر على طول ممرات نقل النفط يرفع نسب خسائر التأمين وتكاليف الخدمات اللوجستية.",
        scenario_type="escalation",
        horizon_hours=168,
        shocks=[
            ScenarioShock(target_entity_id="oil_sector", shock_type=DisruptionType.ESCALATION, severity_score=0.75, description="Oil corridor threat"),
            ScenarioShock(target_entity_id="ras_tanura", shock_type=DisruptionType.ESCALATION, severity_score=0.7, description="Export terminal risk"),
            ScenarioShock(target_entity_id="aramco_infra", shock_type=DisruptionType.ESCALATION, severity_score=0.65, description="Infrastructure risk"),
            ScenarioShock(target_entity_id="insurance", shock_type=DisruptionType.ESCALATION, severity_score=0.85, description="Loss ratio surge"),
            ScenarioShock(target_entity_id="reinsurance", shock_type=DisruptionType.ESCALATION, severity_score=0.75, description="Reinsurance capacity stress"),
            ScenarioShock(target_entity_id="logistics", shock_type=DisruptionType.DELAY, severity_score=0.55, description="Logistics cost increase"),
        ],
        provenance=_PROV,
    ),

    # 14. High-uncertainty false-signal scenario to test confidence logic
    Scenario(
        id="false_signal_uncertainty",
        title="High-Uncertainty False Signal Scenario",
        title_ar="سيناريو إشارة خاطئة عالية عدم اليقين",
        description="Low-confidence signals suggesting a threat that may not materialize. Tests system confidence scoring and uncertainty handling.",
        description_ar="إشارات منخفضة الثقة تشير لتهديد قد لا يتحقق. يختبر نظام تسجيل الثقة ومعالجة عدم اليقين.",
        scenario_type="hypothetical",
        horizon_hours=24,
        shocks=[
            ScenarioShock(target_entity_id="hormuz", shock_type=DisruptionType.ESCALATION, severity_score=0.3, description="Unconfirmed threat report"),
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.REROUTE, severity_score=0.2, description="Precautionary advisory"),
            ScenarioShock(target_entity_id="sentiment", shock_type=DisruptionType.ESCALATION, severity_score=0.4, description="Social media rumors"),
        ],
        provenance=_PROV,
    ),

    # 15. Cascading reroute overload scenario across aviation and maritime
    Scenario(
        id="reroute_overload_cascade",
        title="Cascading Reroute Overload: Aviation + Maritime",
        title_ar="تحميل زائد متتالي لإعادة التوجيه: طيران + بحري",
        description="Initial disruption forces reroutes which overload alternative corridors, creating secondary failures across both aviation and maritime.",
        description_ar="تعطل أولي يفرض إعادة توجيه تحمّل الممرات البديلة فوق طاقتها مما يخلق أعطالاً ثانوية.",
        scenario_type="cascading",
        horizon_hours=72,
        shocks=[
            ScenarioShock(target_entity_id="airspace", shock_type=DisruptionType.REROUTE, severity_score=0.8, description="Primary airspace closed"),
            ScenarioShock(target_entity_id="shipping", shock_type=DisruptionType.REROUTE, severity_score=0.75, description="Primary lane closed"),
            ScenarioShock(target_entity_id="doha_apt", shock_type=DisruptionType.CONGESTION, severity_score=0.7, description="DOH overloaded by reroutes"),
            ScenarioShock(target_entity_id="bahrain_apt", shock_type=DisruptionType.CONGESTION, severity_score=0.65, description="BAH overloaded"),
            ScenarioShock(target_entity_id="shuwaikh", shock_type=DisruptionType.CONGESTION, severity_score=0.6, description="Shuwaikh overloaded"),
            ScenarioShock(target_entity_id="hamad_port", shock_type=DisruptionType.CONGESTION, severity_score=0.65, description="Hamad overloaded"),
            ScenarioShock(target_entity_id="power_grid", shock_type=DisruptionType.DELAY, severity_score=0.4, description="Grid strain from demand spike"),
        ],
        provenance=_PROV,
    ),
]
