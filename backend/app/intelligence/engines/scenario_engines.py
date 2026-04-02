"""
GCC Knowledge Graph Scenario Formula Engines
Exact port of frontend/lib/scenario-engines.ts (875 lines)
Implements 17 scenario engines + generic fallback for disruption modeling
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from .gcc_constants import BASES


# ============================================================================
# Helper Functions
# ============================================================================

def imp(base: float, multiplier: float) -> float:
    """Impact function: base * multiplier"""
    return base * multiplier


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class ScenarioChainStep:
    """Single step in a scenario impact chain"""
    node: str
    metric: str
    impact: float
    direction: str  # "increase" | "decrease"


@dataclass
class ScenarioEngineResult:
    """Complete result from a scenario engine"""
    scenarioId: str
    scenarioName: str
    narrative: Dict[str, str]  # {"en": "...", "ar": "..."}
    keyMetrics: Dict[str, Any]
    impactChain: List[ScenarioChainStep] = field(default_factory=list)
    totalGccImpact: float = 0.0
    estimatedCost: float = 0.0


@dataclass
class ScenarioEngine:
    """Scenario engine definition"""
    id: str
    name: str
    description: str
    compute: callable


# ============================================================================
# Engine Implementations
# ============================================================================

def engine_1_hormuz_strait_closure(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Hormuz Strait Closure
    Immediate 30-day block of strait transit capacity
    Formulas:
    - oilPrice: base * 2.8 (market shock)
    - shippingCost: base * 2.4 (rerouting)
    - insuranceCost: base * 3.2 (high risk premium)
    - aviationFuel: base * 1.9 (alternative sourcing)
    - tourism: base * 0.35 (geopolitical risk aversion)
    - gdpMultiplier: 0.55
    """
    base_oil = BASES["oilRevenue"]
    base_shipping = BASES["shippingCost"]
    base_insurance = BASES["insurancePremium"]
    base_aviation = BASES["aviationFuel"]
    base_tourism = BASES["tourismRevenue"]
    base_gdp = BASES["gccGDP"]
    
    oil_impact = imp(base_oil, 2.8)
    shipping_impact = imp(base_shipping, 2.4)
    insurance_impact = imp(base_insurance, 3.2)
    aviation_impact = imp(base_aviation, 1.9)
    tourism_impact = imp(base_tourism, 0.35)
    gdp_multiplier = 0.55
    
    total_cost = (oil_impact + shipping_impact + insurance_impact + 
                  aviation_impact + (base_tourism - tourism_impact))
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="1",
        scenarioName="Hormuz Strait Closure",
        narrative={
            "en": "A 30-day closure of the Strait of Hormuz disrupts 30% of global maritime trade. Oil prices spike 180%, shipping costs triple, and insurance premiums surge. GCC tourism plummets as geopolitical risk sentiment shifts.",
            "ar": "إغلاق مضيق هرمز لمدة 30 يوماً يعطل 30% من التجارة البحرية العالمية. تقفز أسعار النفط 180%، وتتضاعف تكاليف الشحن ثلاث مرات، وتقفز علاوات التأمين. ينهار السياحة في دول مجلس التعاون تحت ضغط المشاعر الجيوسياسية."
        },
        keyMetrics={
            "oilPrice": round(oil_impact, 2),
            "shippingCost": round(shipping_impact, 2),
            "insurancePremium": round(insurance_impact, 2),
            "aviationFuel": round(aviation_impact, 2),
            "tourismRevenue": round(tourism_impact, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_2_cyber_critical_infrastructure(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Cyber Attack on Critical Infrastructure
    Cascading digital disruption across interconnected systems
    Formulas:
    - bankingAssets: base * 0.82 (35-40% operational slowdown)
    - power: base * 0.70 (30% capacity loss)
    - telecom: base * 0.75 (25% service degradation)
    - desalination: base * 0.65 (35% water supply loss)
    - gdpMultiplier: 0.48
    """
    base_banking = BASES["bankingAssets"]
    base_power = BASES["powerCapacity"]
    base_telecom = 100  # Telecom revenue proxy
    base_desal = BASES["desalCapacity"]
    base_gdp = BASES["gccGDP"]
    
    banking_impact = base_banking * (1 - 0.82)
    power_impact = base_power * (1 - 0.70)
    telecom_impact = base_telecom * (1 - 0.75)
    desal_impact = base_desal * (1 - 0.65)
    gdp_multiplier = 0.48
    
    total_cost = banking_impact + power_impact + telecom_impact + desal_impact
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="2",
        scenarioName="Cyber Attack on Critical Infrastructure",
        narrative={
            "en": "Coordinated cyberattacks target banking networks, power grids, telecom hubs, and desalination plants. Banking operations slow 35-40%, power output drops 30%, water supply falls 35%. Critical service cascades propagate across the region.",
            "ar": "تستهدف الهجمات الإلكترونية المنسقة شبكات البنوك والشبكات الكهربائية ومحاور الاتصالات ومحطات تحلية المياه. تبطأ العمليات المصرفية بنسبة 35-40%، وتنخفض إنتاجية الكهرباء بنسبة 30%، وتنخفض إمدادات المياه بنسبة 35%."
        },
        keyMetrics={
            "bankingAssets": round(base_banking * 0.82, 2),
            "powerCapacity": round(base_power * 0.70, 2),
            "telecomService": round(telecom_impact, 2),
            "desalCapacity": round(base_desal * 0.65, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_3_global_recession(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Global Recession / Demand Shock
    Sustained contraction in external demand
    Formulas:
    - oilDemand: base * 0.75 (demand down 25%)
    - airportPax: base * 0.60 (capacity down 40%)
    - portTEU: base * 0.65 (throughput down 35%)
    - tourismRevenue: base * 0.45 (down 55%)
    - fdiInflows: base * 0.35 (down 65%)
    - gdpMultiplier: 0.62
    """
    base_oil = BASES["oilRevenue"]
    base_airport = BASES["airportPax"]
    base_port = BASES["portTEU"]
    base_tourism = BASES["tourismRevenue"]
    base_fdi = BASES["fdiInflows"]
    base_gdp = BASES["gccGDP"]
    
    oil_impact = imp(base_oil, 0.75)
    airport_impact = imp(base_airport, 0.60)
    port_impact = imp(base_port, 0.65)
    tourism_impact = imp(base_tourism, 0.45)
    fdi_impact = imp(base_fdi, 0.35)
    gdp_multiplier = 0.62
    
    total_cost = ((base_oil - oil_impact) + (base_airport - airport_impact) +
                  (base_port - port_impact) + (base_tourism - tourism_impact) +
                  (base_fdi - fdi_impact))
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="3",
        scenarioName="Global Recession",
        narrative={
            "en": "Global recession cuts external demand sharply. Oil demand drops 25%, aviation passenger traffic falls 40%, port throughput declines 35%, and tourism collapses 55%. Foreign direct investment plummets 65% as investors shift to safe havens.",
            "ar": "تقلل الركود العالمي الطلب الخارجي بشكل حاد. ينخفض الطلب على النفط بنسبة 25%، وينخفض حركة الركاب بنسبة 40%، وينخفض معدل الإنتاجية في الموانئ بنسبة 35%، وينهار السياحة بنسبة 55%."
        },
        keyMetrics={
            "oilDemand": round(oil_impact, 2),
            "airportPax": round(airport_impact, 2),
            "portTEU": round(port_impact, 2),
            "tourismRevenue": round(tourism_impact, 2),
            "fdiInflows": round(fdi_impact, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_4_currency_crisis(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Currency Crisis / Peg Break
    Loss of currency confidence and capital flight
    Formulas:
    - cbReserves: base * 0.55 (45% reserves drain)
    - swfAssets: base * 0.70 (30% SWF drawdown)
    - fdiInflows: base * 0.20 (80% FDI halt)
    - investmentReturns: -0.15 (portfolio losses)
    - gdpMultiplier: 0.58
    """
    base_cb = BASES["cbReserves"]
    base_swf = BASES["swfAssets"]
    base_fdi = BASES["fdiInflows"]
    base_gdp = BASES["gccGDP"]
    
    cb_reserves = imp(base_cb, 0.55)
    swf_assets = imp(base_swf, 0.70)
    fdi_impact = imp(base_fdi, 0.20)
    portfolio_loss = 0.15
    gdp_multiplier = 0.58
    
    total_cost = ((base_cb - cb_reserves) + (base_swf - swf_assets) + 
                  (base_fdi - fdi_impact) + (base_gdp * portfolio_loss))
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="4",
        scenarioName="Currency Crisis",
        narrative={
            "en": "Loss of currency confidence triggers capital flight. Central bank reserves drain 45%, sovereign wealth fund assets decline 30%, and foreign investment stops (80% decline). Portfolio losses accelerate as investors flee regional assets.",
            "ar": "فقدان الثقة في العملة يؤدي إلى هروب رأس المال. تنضب احتياطيات البنك المركزي بنسبة 45%، وتنخفض أصول صندوق الثروة السيادية بنسبة 30%، والاستثمار الأجنبي يتوقف بنسبة 80%."
        },
        keyMetrics={
            "cbReserves": round(cb_reserves, 2),
            "swfAssets": round(swf_assets, 2),
            "fdiInflows": round(fdi_impact, 2),
            "portfolioLoss": -portfolio_loss,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_5_extreme_weather_event(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Extreme Weather Event (heat wave, flooding)
    Physical climate hazard affecting production and infrastructure
    Formulas:
    - powerDemand: base * 1.4 (spike from cooling demand)
    - desalOutput: base * 0.60 (capacity loss 40%)
    - oilProduction: base * 0.85 (operational disruption)
    - constructionDelay: -0.20 (project delays)
    - gdpMultiplier: 0.52
    """
    base_power = BASES["powerCapacity"]
    base_desal = BASES["desalCapacity"]
    base_oil = BASES["oilRevenue"]
    base_gdp = BASES["gccGDP"]
    
    power_demand = imp(base_power, 1.4)
    desal_output = imp(base_desal, 0.60)
    oil_production = imp(base_oil, 0.85)
    construction_loss = base_gdp * 0.20
    gdp_multiplier = 0.52
    
    total_cost = ((power_demand - base_power) + (base_desal - desal_output) +
                  (base_oil - oil_production) + construction_loss)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="5",
        scenarioName="Extreme Weather Event",
        narrative={
            "en": "Extreme heat wave and flooding damage infrastructure and disrupt production. Power demand surges 40% from cooling loads. Desalination capacity drops 40% from heat stress. Oil operations lose 15% throughput. Construction projects face 20% delays.",
            "ar": "موجة حر شديدة وفيضانات تضر البنية التحتية وتعطل الإنتاج. يرتفع الطلب على الكهرباء بنسبة 40% من أحمال التبريد. تنخفض طاقة التحلية بنسبة 40% من الضغط الحراري. تخسر عمليات النفط 15% من الإنتاجية."
        },
        keyMetrics={
            "powerDemandSpike": round(power_demand, 2),
            "desalOutput": round(desal_output, 2),
            "oilProduction": round(oil_production, 2),
            "constructionDelay": -0.20,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_6_rapid_energy_transition(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Rapid Energy Transition / Stranded Assets
    Fast shift away from hydrocarbon dependence
    Formulas:
    - oilDemand: base * 0.55 (45% demand loss to renewables)
    - gasRevenue: base * 0.60 (40% decline)
    - investmentNeeded: base_gdp * 0.08 (8% of GDP for transition)
    - jobDisplacement: 0.12 (12% workforce disruption)
    - gdpMultiplier: 0.65
    """
    base_oil = BASES["oilRevenue"]
    base_gdp = BASES["gccGDP"]
    
    oil_demand = imp(base_oil, 0.55)
    gas_decline = base_oil * 0.40  # Proxy for gas revenue
    transition_investment = base_gdp * 0.08
    job_displacement = 0.12
    gdp_multiplier = 0.65
    
    total_cost = ((base_oil - oil_demand) + gas_decline + transition_investment)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="6",
        scenarioName="Rapid Energy Transition",
        narrative={
            "en": "Global energy shift to renewables cuts oil demand 45% and gas revenue 40%. Requires 8% of GDP investment in transition infrastructure. Workforce displacement affects 12% of energy sector workers.",
            "ar": "التحول العالمي للطاقة المتجددة يقطع الطلب على النفط بنسبة 45% وإيرادات الغاز بنسبة 40%. يتطلب استثمار 8% من الناتج المحلي الإجمالي في البنية التحتية للتحول. يؤثر إزاحة القوى العاملة على 12% من عاملي قطاع الطاقة."
        },
        keyMetrics={
            "oilDemand": round(oil_demand, 2),
            "gasRevenue": round(base_oil - gas_decline, 2),
            "transitionInvestment": round(transition_investment, 2),
            "jobDisplacement": -job_displacement,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_7_regional_conflict_escalation(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Regional Conflict Escalation
    Armed conflict affecting trade routes and investor confidence
    Formulas:
    - tourism: base * 0.25 (75% drop)
    - portTEU: base * 0.50 (50% cargo rerouting)
    - aviationCapacity: base * 0.40 (60% reduction)
    - defenseBudget: base_gdp * 0.10 (emergency 10% GDP military spending)
    - gdpMultiplier: 0.60
    """
    base_tourism = BASES["tourismRevenue"]
    base_port = BASES["portTEU"]
    base_aviation = BASES["aviationFuel"]
    base_gdp = BASES["gccGDP"]
    
    tourism_impact = imp(base_tourism, 0.25)
    port_impact = imp(base_port, 0.50)
    aviation_impact = imp(base_aviation, 0.40)
    defense_spending = base_gdp * 0.10
    gdp_multiplier = 0.60
    
    total_cost = ((base_tourism - tourism_impact) + (base_port - port_impact) +
                  (base_aviation - aviation_impact) + defense_spending)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="7",
        scenarioName="Regional Conflict Escalation",
        narrative={
            "en": "Armed conflict cascades across the region. Tourism collapses 75% as travel warnings spread. Port cargo reroutes 50% away from conflict zones. Aviation capacity shrinks 60%. Defense spending surges to 10% of GDP as states mobilize.",
            "ar": "تتسع النزاعات المسلحة عبر المنطقة. ينهار السياحة بنسبة 75% مع انتشار تحذيرات السفر. يتم إعادة توجيه البضائع في الموانئ بنسبة 50% بعيداً عن مناطق الصراع. تنكمش طاقة الطيران بنسبة 60%."
        },
        keyMetrics={
            "tourismRevenue": round(tourism_impact, 2),
            "portTEU": round(port_impact, 2),
            "aviationCapacity": round(aviation_impact, 2),
            "defenseBudget": round(defense_spending, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_8_pandemics_health_crisis(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Pandemics / Health Crisis
    Disease outbreak with mobility restrictions
    Formulas:
    - tourism: base * 0.30 (70% decline)
    - airportPax: base * 0.35 (65% drop)
    - workforceAvailability: 0.85 (15% absence rate)
    - healthExpenditure: base_gdp * 0.05 (emergency 5% of GDP)
    - gdpMultiplier: 0.58
    """
    base_tourism = BASES["tourismRevenue"]
    base_airport = BASES["airportPax"]
    base_gdp = BASES["gccGDP"]
    
    tourism_impact = imp(base_tourism, 0.30)
    airport_impact = imp(base_airport, 0.35)
    workforce_impact = 0.85
    health_spending = base_gdp * 0.05
    gdp_multiplier = 0.58
    
    total_cost = ((base_tourism - tourism_impact) + (base_airport - airport_impact) +
                  health_spending)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="8",
        scenarioName="Pandemic / Health Crisis",
        narrative={
            "en": "Major pandemic forces lockdowns and mobility restrictions. Tourism plummets 70%, aviation passenger traffic crashes 65%. Workforce availability drops 15% from illness and isolation. Emergency health spending reaches 5% of GDP.",
            "ar": "جائحة كبرى تفرض الحجر الصحي وقيود الحركة. ينهار السياحة بنسبة 70%، وحركة الركاب في الطيران بنسبة 65%. ينخفض توفر القوى العاملة بنسبة 15% من المرض والعزل. يصل الإنفاق الصحي الطارئ إلى 5% من الناتج المحلي الإجمالي."
        },
        keyMetrics={
            "tourismRevenue": round(tourism_impact, 2),
            "airportPax": round(airport_impact, 2),
            "workforceAvailability": workforce_impact,
            "healthExpenditure": round(health_spending, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_9_debt_crisis_fiscal_stress(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Debt Crisis / Fiscal Stress
    Unsustainable debt levels trigger refinancing crisis
    Formulas:
    - borrowingCost: base_gdp * 0.02 (2% spike in rates)
    - spendingCuts: base_gdp * 0.15 (15% austerity)
    - privateInvestment: base_gdp * 0.10 (10% decline)
    - creditRating: -2 (notches)
    - gdpMultiplier: 0.48
    """
    base_gdp = BASES["gccGDP"]
    
    borrowing_cost = base_gdp * 0.02
    spending_cuts = base_gdp * 0.15
    investment_decline = base_gdp * 0.10
    gdp_multiplier = 0.48
    
    total_cost = borrowing_cost + spending_cuts + investment_decline
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="9",
        scenarioName="Debt Crisis",
        narrative={
            "en": "Unsustainable debt triggers refinancing crisis. Borrowing costs spike 2% above baseline. Governments enact 15% spending cuts. Private investment retreats 10%. Credit ratings face 2-notch downgrades.",
            "ar": "الديون غير المستدامة تؤدي إلى أزمة إعادة تمويل. ترتفع تكاليف الاقتراض بنسبة 2% فوق خط الأساس. تنفذ الحكومات تخفيضات إنفاق بنسبة 15%. ينسحب الاستثمار الخاص بنسبة 10%."
        },
        keyMetrics={
            "borrowingCost": round(borrowing_cost, 2),
            "spendingCuts": round(spending_cuts, 2),
            "privateInvestment": round(-investment_decline, 2),
            "creditRating": -2,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_10_water_scarcity_crisis(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Water Scarcity Crisis
    Groundwater depletion forces production cuts
    Formulas:
    - desalCapacity: base * 0.70 (30% capacity loss to drought stress)
    - agricultureOutput: base_gdp * 0.02 * 0.40 (40% of small ag sector)
    - oilProduction: base * 0.92 (8% EOR water stress)
    - investmentNeeded: base_gdp * 0.04 (4% for water infra)
    - gdpMultiplier: 0.55
    """
    base_desal = BASES["desalCapacity"]
    base_oil = BASES["oilRevenue"]
    base_gdp = BASES["gccGDP"]
    
    desal_capacity = imp(base_desal, 0.70)
    ag_loss = base_gdp * 0.02 * 0.40
    oil_stress = imp(base_oil, 0.92)
    water_investment = base_gdp * 0.04
    gdp_multiplier = 0.55
    
    total_cost = ((base_desal - desal_capacity) + ag_loss + 
                  (base_oil - oil_stress) + water_investment)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="10",
        scenarioName="Water Scarcity Crisis",
        narrative={
            "en": "Groundwater depletion forces cuts to water-intensive production. Desalination capacity drops 30% from thermal stress. Agricultural output (2% of GDP) loses 40%. Oil operations lose 8% from enhanced oil recovery water stress. Requires 4% GDP investment in water infrastructure.",
            "ar": "استنزاف المياه الجوفية يفرض تخفيضات على الإنتاج كثيف استهلاك المياه. تنخفض طاقة التحلية بنسبة 30% من الضغط الحراري. يخسر الإنتاج الزراعي (2% من الناتج المحلي الإجمالي) 40%. تخسر عمليات النفط 8% من استخلاص النفط المحسّن المرتبط بالمياه."
        },
        keyMetrics={
            "desalCapacity": round(desal_capacity, 2),
            "agriculturalOutput": round(base_gdp * 0.02 - ag_loss, 2),
            "oilProduction": round(oil_stress, 2),
            "waterInfraInvestment": round(water_investment, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_11_talent_exodus_brain_drain(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Talent Exodus / Brain Drain
    Skilled workforce migration triggered by political or economic stress
    Formulas:
    - workforceProductivity: 0.85 (15% loss)
    - salaryCosts: base_gdp * 0.20 * 0.10 (10% wage inflation)
    - investmentInEducation: base_gdp * 0.03 (3% replacement training)
    - entrepreneurshipRate: 0.90 (10% startup decline)
    - gdpMultiplier: 0.52
    """
    base_gdp = BASES["gccGDP"]
    
    workforce_productivity = 0.85
    salary_inflation = base_gdp * 0.20 * 0.10
    education_investment = base_gdp * 0.03
    entrepreneurship_rate = 0.90
    gdp_multiplier = 0.52
    
    total_cost = salary_inflation + education_investment
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="11",
        scenarioName="Talent Exodus",
        narrative={
            "en": "Political or economic stress triggers skilled worker migration. Workforce productivity drops 15%. Remaining talent demands 10% wage premiums. Requires 3% of GDP for accelerated replacement training. Startup rate declines 10%.",
            "ar": "الضغط السياسي أو الاقتصادي يؤدي إلى هجرة العمال المهرة. تنخفض إنتاجية القوى العاملة بنسبة 15%. يطالب الموهوبون المتبقيون بعلاوات أجور بنسبة 10%. يتطلب 3% من الناتج المحلي الإجمالي لتدريب استبدال معجل."
        },
        keyMetrics={
            "workforceProductivity": workforce_productivity,
            "salaryInflation": round(salary_inflation, 2),
            "educationInvestment": round(education_investment, 2),
            "entrepreneurshipRate": entrepreneurship_rate,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_12_supply_chain_disruption(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Supply Chain Disruption
    Manufacturing input bottlenecks and logistics failures
    Formulas:
    - manufacturingOutput: base_gdp * 0.15 * 0.60 (60% of 15% manufacturing)
    - portTEU: base * 0.70 (30% cargo slowdown)
    - shippingCost: base * 1.5 (50% cost inflation)
    - productionDelay: 0.20 (20% of orders delayed)
    - gdpMultiplier: 0.53
    """
    base_port = BASES["portTEU"]
    base_shipping = BASES["shippingCost"]
    base_gdp = BASES["gccGDP"]
    
    manufacturing_loss = base_gdp * 0.15 * 0.60
    port_impact = imp(base_port, 0.70)
    shipping_cost = imp(base_shipping, 1.5)
    production_delay = 0.20
    gdp_multiplier = 0.53
    
    total_cost = manufacturing_loss + (base_shipping - imp(base_shipping, 0.70))
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="12",
        scenarioName="Supply Chain Disruption",
        narrative={
            "en": "Manufacturing input bottlenecks cascade through production networks. 60% of the 15% manufacturing sector faces output cuts. Port throughput drops 30% from congestion. Shipping costs spike 50%. 20% of orders face production delays.",
            "ar": "اختناقات المدخلات التصنيعية تنتشر عبر شبكات الإنتاج. يواجه 60% من قطاع التصنيع بنسبة 15% تخفيضات في الإنتاج. ينخفض معدل الإنتاجية في الموانئ بنسبة 30% من الازدحام. ترتفع تكاليف الشحن بنسبة 50%."
        },
        keyMetrics={
            "manufacturingOutput": round(base_gdp * 0.15 - manufacturing_loss, 2),
            "portTEU": round(port_impact, 2),
            "shippingCost": round(shipping_cost, 2),
            "productionDelay": production_delay,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_13_renewable_energy_surge_grid_stress(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Renewable Energy Surge / Grid Stress
    Rapid RE integration without grid modernization
    Formulas:
    - powerCapacity: base * 1.5 (50% capacity addition)
    - gridInfraInvestment: base_gdp * 0.06 (6% required for grid upgrade)
    - energyStorageCost: base_gdp * 0.03 (3% battery/storage)
    - blackoutRisk: 0.15 (15% probability of cascade)
    - gdpMultiplier: 0.92 (8% loss from integration costs)
    """
    base_power = BASES["powerCapacity"]
    base_gdp = BASES["gccGDP"]
    
    power_capacity = imp(base_power, 1.5)
    grid_investment = base_gdp * 0.06
    storage_cost = base_gdp * 0.03
    blackout_risk = 0.15
    gdp_multiplier = 0.92
    
    total_cost = grid_investment + storage_cost
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="13",
        scenarioName="Renewable Energy Surge",
        narrative={
            "en": "Rapid renewable energy deployment adds 50% capacity but grid isn't ready. Requires 6% of GDP for grid modernization and 3% for energy storage. Blackout cascade risk reaches 15% without proper integration infrastructure.",
            "ar": "نشر الطاقة المتجددة السريع يضيف 50% من الطاقة لكن الشبكة غير جاهزة. يتطلب 6% من الناتج المحلي الإجمالي لتحديث الشبكة و 3% لتخزين الطاقة. تصل مخاطر انقطاع التيار الكهربائي إلى 15% بدون بنية تحتية للتكامل المناسب."
        },
        keyMetrics={
            "powerCapacity": round(power_capacity, 2),
            "gridInfraInvestment": round(grid_investment, 2),
            "energyStorageCost": round(storage_cost, 2),
            "blackoutRisk": blackout_risk,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_14_real_estate_market_collapse(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Real Estate Market Collapse
    Property price crash from over-leverage
    Formulas:
    - realEstatePrices: 0.50 (50% value loss)
    - constructionActivity: base_gdp * 0.08 * 0.70 (70% of 8% construction)
    - bankingAssets: base * 0.90 (10% NPL shock)
    - propertyTax: base_gdp * 0.01 * 0.60 (60% of 1% tax revenue)
    - gdpMultiplier: 0.58
    """
    base_banking = BASES["bankingAssets"]
    base_gdp = BASES["gccGDP"]
    
    real_estate_loss = 0.50
    construction_loss = base_gdp * 0.08 * 0.70
    banking_impact = base_banking * 0.10
    tax_loss = base_gdp * 0.01 * 0.60
    gdp_multiplier = 0.58
    
    total_cost = construction_loss + banking_impact + tax_loss
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="14",
        scenarioName="Real Estate Collapse",
        narrative={
            "en": "Over-leveraged real estate sector collapses 50% in value. Construction (8% of GDP) plummets 70%. Banking sector absorbs 10% non-performing loans. Property tax revenue (1% of GDP) drops 60% from valuation collapse.",
            "ar": "ينهار قطاع العقارات الممول بشكل زائد بنسبة 50% من القيمة. ينهار البناء (8% من الناتج المحلي الإجمالي) بنسبة 70%. يمتص القطاع المصرفي 10% من القروض غير المنتجة. ينخفض إيراد ضريبة الملكية (1% من الناتج المحلي الإجمالي) بنسبة 60%."
        },
        keyMetrics={
            "realEstatePrices": -real_estate_loss,
            "constructionActivity": round(base_gdp * 0.08 - construction_loss, 2),
            "bankingNPL": round(banking_impact, 2),
            "propertyTaxRevenue": round(base_gdp * 0.01 - tax_loss, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_15_foreign_direct_investment_freeze(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Foreign Direct Investment Freeze
    Capital controls or investor confidence collapse
    Formulas:
    - fdiInflows: base * 0.10 (90% halt)
    - enterpriseCapitalAvailable: base_gdp * 0.04 * 0.80 (80% of 4% CapEx)
    - jobCreation: 0.60 (40% employment growth loss)
    - technologyTransfer: 0.70 (30% tech inflow loss)
    - gdpMultiplier: 0.55
    """
    base_fdi = BASES["fdiInflows"]
    base_gdp = BASES["gccGDP"]
    
    fdi_impact = imp(base_fdi, 0.10)
    capex_loss = base_gdp * 0.04 * 0.80
    job_creation = 0.60
    tech_transfer = 0.70
    gdp_multiplier = 0.55
    
    total_cost = (base_fdi - fdi_impact) + capex_loss
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="15",
        scenarioName="FDI Freeze",
        narrative={
            "en": "Capital controls or confidence collapse halts foreign investment 90%. Enterprise capital for projects (4% of GDP) falls 80%. Employment growth from FDI drops 40%. Technology transfer and skills upgrading decline 30%.",
            "ar": "تحكم رأس المال أو انهيار الثقة يوقف الاستثمار الأجنبي بنسبة 90%. رأس المال المشروع للمشاريع (4% من الناتج المحلي الإجمالي) ينخفض بنسبة 80%. ينخفض نمو التوظيف من الاستثمار الأجنبي المباشر بنسبة 40%. ينخفض نقل التكنولوجيا والترقية المهنية بنسبة 30%."
        },
        keyMetrics={
            "fdiInflows": round(fdi_impact, 2),
            "enterpriseCapital": round(base_gdp * 0.04 - capex_loss, 2),
            "jobCreation": job_creation,
            "technologyTransfer": tech_transfer,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_16_hajj_disruption_pilgrimage_crash(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Hajj Disruption / Pilgrimage Crash
    Travel restrictions or security incidents halt hajj
    Formulas:
    - hajjRevenue: base * 0.05 (95% halt)
    - touristDays: base * 0.70 (30% decline)
    - hotelOccupancy: base_gdp * 0.02 * 0.50 (50% of 2% hospitality)
    - retailSpend: base_gdp * 0.01 * 0.60 (60% of 1% retail)
    - gdpMultiplier: 0.52
    """
    base_hajj = BASES["hajjRevenue"]
    base_tourism = BASES["tourismRevenue"]
    base_gdp = BASES["gccGDP"]
    
    hajj_impact = imp(base_hajj, 0.05)
    tourism_impact = imp(base_tourism, 0.70)
    hotel_loss = base_gdp * 0.02 * 0.50
    retail_loss = base_gdp * 0.01 * 0.60
    gdp_multiplier = 0.52
    
    total_cost = ((base_hajj - hajj_impact) + (base_tourism - tourism_impact) +
                  hotel_loss + retail_loss)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="16",
        scenarioName="Hajj Disruption",
        narrative={
            "en": "Travel restrictions or security incidents halt hajj pilgrimage 95%. Overall tourism declines 30%. Hotel occupancy (2% of GDP sector) drops 50%. Retail spending from pilgrims (1% of GDP) falls 60%.",
            "ar": "تحد قيود السفر أو الحوادث الأمنية من فريضة الحج بنسبة 95%. ينخفض السياحة الكلية بنسبة 30%. تنخفض إشغالية الفنادق (2% من قطاع الناتج المحلي الإجمالي) بنسبة 50%. ينخفض الإنفاق على البيع بالتجزئة من الحجاج (1% من الناتج المحلي الإجمالي) بنسبة 60%."
        },
        keyMetrics={
            "hajjRevenue": round(hajj_impact, 2),
            "touristDays": round(tourism_impact, 2),
            "hotelOccupancy": round(base_gdp * 0.02 - hotel_loss, 2),
            "retailSpend": round(base_gdp * 0.01 - retail_loss, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_17_aviation_sector_crisis(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Aviation Sector Crisis
    Aircraft grounding, airline bankruptcy, or route collapse
    Formulas:
    - airportPax: base * 0.40 (60% capacity loss)
    - aviationFuel: base * 0.50 (50% cost reduction from demand crash)
    - baseTicket: base * 0.60 (40% price decline)
    - airlineDebtDefault: base_gdp * 0.01 * 0.70 (70% of 1% sector debt)
    - gdpMultiplier: 0.54
    """
    base_airport = BASES["airportPax"]
    base_aviation = BASES["aviationFuel"]
    base_ticket = BASES["baseTicket"]
    base_gdp = BASES["gccGDP"]
    
    airport_impact = imp(base_airport, 0.40)
    fuel_impact = imp(base_aviation, 0.50)
    ticket_impact = imp(base_ticket, 0.60)
    debt_loss = base_gdp * 0.01 * 0.70
    gdp_multiplier = 0.54
    
    total_cost = ((base_airport - airport_impact) + (base_aviation - fuel_impact) +
                  (base_ticket - ticket_impact) + debt_loss)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    return ScenarioEngineResult(
        scenarioId="17",
        scenarioName="Aviation Crisis",
        narrative={
            "en": "Aircraft groundings or airline bankruptcies halt 60% of passenger traffic. Fuel demand crashes, reducing costs 50%, but revenue collapses 40%. Airline sector debt (1% of GDP) defaults 70%. Network cascades to tourism and business travel.",
            "ar": "توقف الطائرات أو إفلاس شركات الطيران توقف 60% من حركة الركاب. ينهار الطلب على الوقود، مما يقلل التكاليف بنسبة 50%، لكن الإيرادات تنخفض بنسبة 40%. يتخلف قطاع شركات الطيران عن السداد بنسبة 70%."
        },
        keyMetrics={
            "airportPax": round(airport_impact, 2),
            "aviationFuel": round(fuel_impact, 2),
            "baseTicket": round(ticket_impact, 2),
            "airlineDebtDefault": round(debt_loss, 2),
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(total_cost, 2)
    )


def engine_fallback_generic_disruption(inputs: Dict[str, Any]) -> ScenarioEngineResult:
    """
    Fallback/Generic Disruption
    Generic shock scenario when no specific engine matches
    Formulas:
    - severity: inputs.get('severity', 0.5) [0-1 scale]
    - spreadFactor: inputs.get('spreadFactor', 0.5) [0-1 scale]
    - gdpMultiplier: 0.3 + (0.5 * severity * spreadFactor)
    """
    severity = inputs.get('severity', 0.5)
    spread_factor = inputs.get('spreadFactor', 0.5)
    base_gdp = BASES["gccGDP"]
    
    gdp_multiplier = 0.3 + (0.5 * severity * spread_factor)
    gdp_impact = base_gdp * (1 - gdp_multiplier)
    
    severity_text = "moderate"
    if severity > 0.7:
        severity_text = "severe"
    elif severity < 0.3:
        severity_text = "minor"
    
    return ScenarioEngineResult(
        scenarioId="0",
        scenarioName="Generic Disruption",
        narrative={
            "en": f"A {severity_text} disruption propagates across interconnected economic systems with {spread_factor*100:.0f}% regional spread.",
            "ar": f"انقطاع {severity_text} ينتشر عبر الأنظمة الاقتصادية المترابطة مع انتشار إقليمي بنسبة {spread_factor*100:.0f}%"
        },
        keyMetrics={
            "severity": severity,
            "spreadFactor": spread_factor,
            "gdpMultiplier": gdp_multiplier,
            "gccGdpImpact": round(gdp_impact, 2)
        },
        totalGccImpact=round(gdp_impact, 2),
        estimatedCost=round(base_gdp * (1 - gdp_multiplier), 2)
    )


# ============================================================================
# Engine Registry
# ============================================================================

SCENARIO_ENGINES = {
    "1": ScenarioEngine(
        id="1",
        name="Hormuz Strait Closure",
        description="30-day block of strait transit capacity affecting global oil trade",
        compute=engine_1_hormuz_strait_closure
    ),
    "2": ScenarioEngine(
        id="2",
        name="Cyber Attack on Critical Infrastructure",
        description="Coordinated cyberattacks on banking, power, telecom, desalination",
        compute=engine_2_cyber_critical_infrastructure
    ),
    "3": ScenarioEngine(
        id="3",
        name="Global Recession",
        description="Sustained contraction in external demand and investment",
        compute=engine_3_global_recession
    ),
    "4": ScenarioEngine(
        id="4",
        name="Currency Crisis",
        description="Loss of currency confidence and capital flight",
        compute=engine_4_currency_crisis
    ),
    "5": ScenarioEngine(
        id="5",
        name="Extreme Weather Event",
        description="Heat wave or flooding affecting infrastructure and production",
        compute=engine_5_extreme_weather_event
    ),
    "6": ScenarioEngine(
        id="6",
        name="Rapid Energy Transition",
        description="Fast shift away from hydrocarbon dependence",
        compute=engine_6_rapid_energy_transition
    ),
    "7": ScenarioEngine(
        id="7",
        name="Regional Conflict Escalation",
        description="Armed conflict affecting trade routes and investor confidence",
        compute=engine_7_regional_conflict_escalation
    ),
    "8": ScenarioEngine(
        id="8",
        name="Pandemic / Health Crisis",
        description="Disease outbreak with mobility restrictions",
        compute=engine_8_pandemics_health_crisis
    ),
    "9": ScenarioEngine(
        id="9",
        name="Debt Crisis",
        description="Unsustainable debt levels trigger refinancing crisis",
        compute=engine_9_debt_crisis_fiscal_stress
    ),
    "10": ScenarioEngine(
        id="10",
        name="Water Scarcity Crisis",
        description="Groundwater depletion forcing production cuts",
        compute=engine_10_water_scarcity_crisis
    ),
    "11": ScenarioEngine(
        id="11",
        name="Talent Exodus",
        description="Skilled workforce migration triggered by political/economic stress",
        compute=engine_11_talent_exodus_brain_drain
    ),
    "12": ScenarioEngine(
        id="12",
        name="Supply Chain Disruption",
        description="Manufacturing input bottlenecks and logistics failures",
        compute=engine_12_supply_chain_disruption
    ),
    "13": ScenarioEngine(
        id="13",
        name="Renewable Energy Surge",
        description="Rapid RE integration without grid modernization",
        compute=engine_13_renewable_energy_surge_grid_stress
    ),
    "14": ScenarioEngine(
        id="14",
        name="Real Estate Collapse",
        description="Property price crash from over-leverage",
        compute=engine_14_real_estate_market_collapse
    ),
    "15": ScenarioEngine(
        id="15",
        name="FDI Freeze",
        description="Capital controls or investor confidence collapse",
        compute=engine_15_foreign_direct_investment_freeze
    ),
    "16": ScenarioEngine(
        id="16",
        name="Hajj Disruption",
        description="Travel restrictions or security incidents halt pilgrimage",
        compute=engine_16_hajj_disruption_pilgrimage_crash
    ),
    "17": ScenarioEngine(
        id="17",
        name="Aviation Crisis",
        description="Aircraft grounding, airline bankruptcy, or route collapse",
        compute=engine_17_aviation_sector_crisis
    ),
    "0": ScenarioEngine(
        id="0",
        name="Generic Disruption",
        description="Fallback scenario for unmapped disruptions",
        compute=engine_fallback_generic_disruption
    ),
}


# ============================================================================
# Result Serialization
# ============================================================================

def result_to_dict(result: ScenarioEngineResult) -> Dict[str, Any]:
    """Convert ScenarioEngineResult to JSON-serializable dictionary"""
    return {
        "scenarioId": result.scenarioId,
        "scenarioName": result.scenarioName,
        "narrative": result.narrative,
        "keyMetrics": result.keyMetrics,
        "impactChain": [asdict(step) for step in result.impactChain],
        "totalGccImpact": result.totalGccImpact,
        "estimatedCost": result.estimatedCost,
    }


# ============================================================================
# Engine Lookup Function
# ============================================================================

def get_scenario_engine(scenario_id: str) -> ScenarioEngine:
    """
    Get a scenario engine by ID.
    Returns the requested engine or the generic fallback if not found.
    
    Args:
        scenario_id: ID of the scenario (1-17 for specific engines, 0 for fallback)
    
    Returns:
        ScenarioEngine with matching ID, or generic fallback engine
    """
    return SCENARIO_ENGINES.get(scenario_id, SCENARIO_ENGINES["0"])


def compute_scenario(scenario_id: str, inputs: Dict[str, Any] = None) -> ScenarioEngineResult:
    """
    Compute a scenario result.
    
    Args:
        scenario_id: ID of the scenario engine to use
        inputs: Optional input parameters for the scenario
    
    Returns:
        ScenarioEngineResult with complete impact modeling
    """
    if inputs is None:
        inputs = {}
    
    engine = get_scenario_engine(scenario_id)
    return engine.compute(inputs)
