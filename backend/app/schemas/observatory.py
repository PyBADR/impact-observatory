"""
Impact Observatory | مرصد الأثر — Canonical Domain Models
Bilingual schemas (AR/EN) for the unified observatory API output contract.
Runtime Flow (10 stages):
  Scenario → Physics → Graph Snapshot → Propagation → Financial →
  Sector Risk → Regulatory → Decision → Explanation → Output
Core Objects (12):
  Scenario, Entity, Edge, FlowState, FinancialImpact, BankingStress,
  InsuranceStress, FintechStress, DecisionAction, DecisionPlan,
  RegulatoryState, ExplanationPack
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from .base import VersionedModel


# ============================================================================
# DOMAIN MODELS
# ============================================================================

class ScenarioInput(BaseModel):
    """
    Input scenario describing an impact event.
    
    Attributes:
        id: Unique scenario identifier
        name: English scenario name
        name_ar: Arabic scenario name
        severity: Severity score from 0 (minimal) to 1 (catastrophic)
        duration_days: Expected duration of the event in days
        description: Detailed description of the scenario
    """
    id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="English scenario name")
    name_ar: str = Field(..., description="Arabic scenario name")
    severity: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Severity score from 0 (minimal) to 1 (catastrophic)"
    )
    duration_days: int = Field(..., ge=1, description="Duration in days")
    description: str = Field(..., description="Detailed event description")
    
    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: float) -> float:
        """Ensure severity is within valid bounds."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Severity must be between 0 and 1")
        return v


class FinancialImpact(BaseModel):
    """
    Quantified financial impact of the scenario.
    
    Attributes:
        headline_loss_usd: Total estimated loss in USD
        peak_day: Day on which maximum impact occurs (1-indexed from event start)
        time_to_failure_days: Days until critical failure point
        severity_code: Impact severity category
        confidence: Model confidence score (0-1)
    """
    headline_loss_usd: float = Field(
        ..., 
        ge=0.0, 
        description="Total estimated loss in USD"
    )
    peak_day: int = Field(..., ge=1, description="Peak impact day (1-indexed)")
    time_to_failure_days: int = Field(
        ..., 
        ge=1, 
        description="Days until critical failure"
    )
    severity_code: str = Field(
        ..., 
        pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$",
        description="Severity classification"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Model confidence (0-1)"
    )
    
    @field_validator("severity_code")
    @classmethod
    def validate_severity_code(cls, v: str) -> str:
        """Ensure severity code is valid."""
        valid_codes = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if v.upper() not in valid_codes:
            raise ValueError(f"Severity code must be one of {valid_codes}")
        return v.upper()
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid bounds."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class BankingStress(BaseModel):
    """
    Banking sector stress indicators.
    
    Attributes:
        liquidity_gap_usd: Unfunded liquidity requirement in USD
        capital_adequacy_ratio: Ratio relative to minimum requirement
        interbank_rate_spike: Basis point increase in interbank rates
        time_to_liquidity_breach_days: Days until liquidity covenant breach
        fx_reserve_drawdown_pct: Percentage of FX reserves needed
        stress_level: Qualitative stress assessment
    """
    liquidity_gap_usd: float = Field(..., ge=0.0, description="Liquidity gap in USD")
    capital_adequacy_ratio: float = Field(
        ..., 
        ge=0.0, 
        le=2.0,
        description="CAR relative to minimum (typically 8%)"
    )
    interbank_rate_spike: float = Field(
        ..., 
        ge=0.0, 
        le=1000.0,
        description="Basis point increase in interbank rates"
    )
    time_to_liquidity_breach_days: int = Field(
        ..., 
        ge=0, 
        description="Days until liquidity breach (0=immediate)"
    )
    fx_reserve_drawdown_pct: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Percentage of FX reserves needed"
    )
    stress_level: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$",
        description="Overall stress level"
    )
    stress_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Composite stress score (0-100) for dashboard gauges"
    )

    @field_validator("stress_level")
    @classmethod
    def validate_stress_level(cls, v: str) -> str:
        """Ensure stress level is valid."""
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Stress level must be one of {valid_levels}")
        return v.upper()


class InsuranceStress(BaseModel):
    """
    Insurance sector stress indicators.
    
    Attributes:
        claims_surge_pct: Expected claims increase as percentage
        reinsurance_trigger: Whether reinsurance is triggered
        combined_ratio: Combined loss and expense ratio
        solvency_margin_pct: Margin above minimum capital requirement
        time_to_insolvency_days: Days until insolvency if unmitigated
        premium_adequacy: Premium coverage ratio
        stress_level: Qualitative stress assessment
    """
    claims_surge_pct: float = Field(
        ..., 
        ge=0.0, 
        le=1000.0,
        description="Expected claims increase as percentage"
    )
    reinsurance_trigger: bool = Field(
        ..., 
        description="Whether reinsurance treaty is triggered"
    )
    combined_ratio: float = Field(
        ..., 
        ge=0.0, 
        le=500.0,
        description="Combined loss and expense ratio"
    )
    solvency_margin_pct: float = Field(
        ..., 
        ge=-100.0, 
        le=100.0,
        description="Margin above minimum capital"
    )
    time_to_insolvency_days: int = Field(
        ..., 
        ge=0, 
        description="Days until insolvency (0=immediate)"
    )
    premium_adequacy: float = Field(
        ..., 
        ge=0.0, 
        le=2.0,
        description="Premium coverage ratio"
    )
    stress_level: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$",
        description="Overall stress level"
    )
    stress_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Composite stress score (0-100) for dashboard gauges"
    )

    @field_validator("stress_level")
    @classmethod
    def validate_stress_level(cls, v: str) -> str:
        """Ensure stress level is valid."""
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Stress level must be one of {valid_levels}")
        return v.upper()


class FintechStress(BaseModel):
    """
    Fintech and digital financial services stress indicators.
    
    Attributes:
        payment_failure_rate: Percentage of payments failing
        settlement_delay_hours: Hours of payment settlement delay
        gateway_downtime_pct: Percentage of gateway unavailability
        digital_banking_disruption: Fraction of digital banking service disruption
        time_to_payment_failure_days: Days until critical payment failure
        stress_level: Qualitative stress assessment
    """
    payment_failure_rate: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Fraction of payments failing"
    )
    settlement_delay_hours: float = Field(
        ..., 
        ge=0.0, 
        le=720.0,
        description="Settlement delay in hours"
    )
    gateway_downtime_pct: float = Field(
        ..., 
        ge=0.0, 
        le=100.0,
        description="Gateway unavailability percentage"
    )
    digital_banking_disruption: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Fraction of digital banking disruption"
    )
    time_to_payment_failure_days: int = Field(
        ..., 
        ge=0, 
        description="Days until critical payment failure"
    )
    stress_level: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$",
        description="Overall stress level"
    )
    stress_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Composite stress score (0-100) for dashboard gauges"
    )

    @field_validator("stress_level")
    @classmethod
    def validate_stress_level(cls, v: str) -> str:
        """Ensure stress level is valid."""
        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Stress level must be one of {valid_levels}")
        return v.upper()


class DecisionAction(BaseModel):
    """
    Recommended action to mitigate or respond to the scenario.
    
    Attributes:
        id: Unique action identifier
        title: English action title
        title_ar: Arabic action title
        urgency: Action urgency score (0-1, where 1 is immediate)
        value: Expected value impact (normalized 0-1)
        priority: Combined priority score (0-1)
        cost_usd: Implementation cost in USD
        loss_avoided_usd: Expected loss avoided in USD
        regulatory_risk: Regulatory risk score (0-1)
        sector: Target sector (banking/insurance/fintech/macroeconomic)
        description: Detailed action description
    """
    id: str = Field(..., description="Unique action identifier")
    rank: int = Field(default=0, ge=0, le=3, description="Action rank (1=highest priority, 2, 3)")
    title: str = Field(..., description="English action title")
    title_ar: str = Field(..., description="Arabic action title")
    urgency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Urgency score (0=routine, 1=immediate)"
    )
    value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Expected value impact (normalized)"
    )
    priority: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Combined 5-factor priority score"
    )
    feasibility: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Execution feasibility (probability * resource availability)"
    )
    time_effect: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Time effectiveness decay factor exp(-λ * time_to_effect)"
    )
    cost_usd: float = Field(..., ge=0.0, description="Implementation cost in USD")
    loss_avoided_usd: float = Field(
        ...,
        ge=0.0,
        description="Expected loss avoided in USD"
    )
    regulatory_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Regulatory risk score"
    )
    sector: str = Field(
        ...,
        pattern="^(banking|insurance|fintech|macroeconomic)$",
        description="Target sector"
    )
    description: str = Field(..., description="Detailed action description")
    status: str = Field(
        default="PENDING_REVIEW",
        pattern="^(PENDING_REVIEW|APPROVED|EXECUTING)$",
        description="Human-in-the-loop governance state"
    )
    
    @field_validator("sector")
    @classmethod
    def validate_sector(cls, v: str) -> str:
        """Ensure sector is valid."""
        valid_sectors = {"banking", "insurance", "fintech", "macroeconomic"}
        if v.lower() not in valid_sectors:
            raise ValueError(f"Sector must be one of {valid_sectors}")
        return v.lower()


# ============================================================================
# GRAPH & FLOW DOMAIN OBJECTS (Entity, Edge, FlowState)
# ============================================================================

class Entity(BaseModel):
    """
    Graph node representing an entity in the GCC reality graph.
    Maps to gcc-knowledge-graph nodes (76 canonical entities).
    """
    id: str = Field(..., description="Entity ID (e.g. 'sa_aramco', 'hormuz_strait')")
    name: str = Field(..., description="English name")
    name_ar: str = Field(default="", description="Arabic name")
    layer: str = Field(..., description="GCC layer: geography|infrastructure|economy|finance|society")
    sector: str = Field(default="general", description="Sector classification")
    severity: float = Field(default=0.0, ge=0.0, le=1.0, description="Current stress severity")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entity-specific metadata")


class Edge(BaseModel):
    """
    Graph edge representing a causal/dependency link between entities.
    Maps to gcc-knowledge-graph edges (191 canonical edges).
    """
    source: str = Field(..., description="Source entity ID")
    target: str = Field(..., description="Target entity ID")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Edge weight (propagation strength)")
    propagation_factor: float = Field(default=0.5, ge=0.0, le=1.0, description="How much stress propagates")
    edge_type: str = Field(default="dependency", description="Edge type: dependency|supply|financial|regulatory")


class FlowState(BaseModel):
    """
    Snapshot of propagation state across the entity graph at a given timestep.
    Produced by the propagation engine: x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i
    """
    timestep: int = Field(..., ge=0, description="Simulation timestep")
    entity_states: Dict[str, float] = Field(default_factory=dict, description="Entity ID → severity map")
    total_stress: float = Field(default=0.0, ge=0.0, description="Sum of all entity stress values")
    peak_entity: str = Field(default="", description="Entity with highest stress at this timestep")
    converged: bool = Field(default=False, description="Whether propagation has stabilized")


# ============================================================================
# DECISION PLAN & REGULATORY STATE
# ============================================================================

class DecisionPlan(BaseModel):
    """
    Ordered set of DecisionActions forming a coherent response strategy.
    Includes sequencing, dependencies, and total resource requirements.
    """
    plan_id: str = Field(..., description="Unique plan identifier")
    name: str = Field(default="", description="Plan name (EN)")
    name_ar: str = Field(default="", description="Plan name (AR)")
    actions: List[DecisionAction] = Field(default_factory=list, description="Ordered actions")
    total_cost_usd: float = Field(default=0.0, ge=0.0, description="Sum of action costs")
    total_loss_avoided_usd: float = Field(default=0.0, ge=0.0, description="Sum of avoided losses")
    net_benefit_usd: float = Field(default=0.0, description="total_loss_avoided - total_cost")
    execution_days: int = Field(default=0, ge=0, description="Total execution timeline in days")
    sectors_covered: List[str] = Field(default_factory=list, description="Sectors addressed")


class RegulatoryState(BaseModel):
    """
    Regulatory compliance and trigger state for GCC financial authorities.
    Tracks PDPL, IFRS 17, Basel III, and SAMA/CBUAE/CBK compliance status.
    """
    pdpl_compliant: bool = Field(default=True, description="PDPL data sovereignty compliance")
    ifrs17_impact: float = Field(default=0.0, ge=0.0, description="IFRS 17 liability adjustment (billions USD)")
    basel3_car_floor: float = Field(default=0.08, ge=0.0, le=1.0, description="Basel III CAR floor (8%)")
    sama_alert_level: str = Field(default="NORMAL", description="SAMA alert: NORMAL|WATCH|WARNING|CRITICAL")
    cbuae_alert_level: str = Field(default="NORMAL", description="CBUAE alert: NORMAL|WATCH|WARNING|CRITICAL")
    sanctions_exposure: float = Field(default=0.0, ge=0.0, le=1.0, description="Sanctions risk score (0-1)")
    regulatory_triggers: List[str] = Field(default_factory=list, description="Triggered regulatory thresholds")


class ExplanationPack(BaseModel):
    """
    Human-readable explanation of observatory results.
    Bilingual (AR/EN), structured for executive, analyst, and regulatory audiences.
    """
    summary_en: str = Field(default="", description="1-2 sentence executive summary (EN)")
    summary_ar: str = Field(default="", description="1-2 sentence executive summary (AR)")
    key_findings: List[Dict[str, str]] = Field(default_factory=list, description="List of {en, ar} finding pairs")
    causal_chain: List[str] = Field(default_factory=list, description="Entity chain showing propagation path")
    confidence_note: str = Field(default="", description="Model confidence explanation")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used in computation")
    audit_trail: Dict[str, Any] = Field(default_factory=dict, description="Step-by-step computation log")


# ============================================================================
# OBSERVATORY OUTPUT (CANONICAL CONTRACT)
# ============================================================================

class ObservatoryOutput(VersionedModel):
    """
    Complete Impact Observatory pipeline output — canonical contract.

    Inherits schema_version from VersionedModel for audit traceability.

    Runtime Flow (10 stages):
      Scenario → Physics → Graph Snapshot → Propagation → Financial →
      Sector Risk → Regulatory → Decision → Explanation → Output

    Core Objects (12):
      Scenario, Entity, Edge, FlowState, FinancialImpact, BankingStress,
      InsuranceStress, FintechStress, DecisionAction, DecisionPlan,
      RegulatoryState, ExplanationPack
    """
    # Pipeline completion tracking
    pipeline_stages_completed: int = Field(
        default=10,
        ge=0,
        le=10,
        description="Number of pipeline stages successfully completed (0-10)"
    )

    # Stage 1: Scenario
    scenario: ScenarioInput = Field(..., description="Input scenario")

    # Stage 3: Graph Snapshot (optional — populated when graph engine runs)
    entities: List[Entity] = Field(default_factory=list, description="Affected entities snapshot")
    edges: List[Edge] = Field(default_factory=list, description="Active edges snapshot")

    # Stage 4: Propagation
    flow_states: List[FlowState] = Field(default_factory=list, description="Propagation timeline")

    # Stage 5: Financial
    financial_impact: FinancialImpact = Field(..., description="Financial impact")

    # Stage 6: Sector Risk
    banking_stress: BankingStress = Field(..., description="Banking stress")
    insurance_stress: InsuranceStress = Field(..., description="Insurance stress")
    fintech_stress: FintechStress = Field(..., description="Fintech stress")

    # Stage 7: Regulatory
    regulatory: RegulatoryState = Field(default_factory=RegulatoryState, description="Regulatory state")

    # Stage 8: Decision
    decisions: List[DecisionAction] = Field(default_factory=list, description="Top decision actions")
    decision_plan: Optional[DecisionPlan] = Field(default=None, description="Coordinated decision plan")

    # Stage 9: Explanation
    explanation: Optional[ExplanationPack] = Field(default=None, description="Explanation pack")

    # Stage 10: Output metadata
    timestamp: datetime = Field(..., description="Analysis timestamp")
    audit_hash: str = Field(..., description="SHA256 audit hash")
    computed_in_ms: float = Field(default=0.0, ge=0.0, description="Computation time in milliseconds")
    runtime_flow: List[str] = Field(
        default=["scenario", "physics", "graph_snapshot", "propagation", "financial",
                 "sector_risk", "regulatory", "decision", "explanation", "output"],
        description="Runtime flow stages executed"
    )
    stage_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-stage timing in milliseconds"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# LOCALIZATION & FLOW METADATA
# ============================================================================

LABELS = {
    # Financial Impact
    "headline_loss":              {"en": "Headline Loss",              "ar": "إجمالي الخسارة"},
    "financial_impact":           {"en": "Financial Impact",           "ar": "الأثر المالي"},
    "peak_day":                   {"en": "Peak Day",                   "ar": "يوم الذروة"},
    "severity_code":              {"en": "Severity Code",              "ar": "مستوى الشدة"},
    "confidence":                 {"en": "Model Confidence",           "ar": "ثقة النموذج"},
    # Sector Stress
    "banking_stress":             {"en": "Banking Stress",             "ar": "ضغط القطاع البنكي"},
    "insurance_stress":           {"en": "Insurance Stress",           "ar": "ضغط التأمين"},
    "fintech_stress":             {"en": "Fintech Stress",             "ar": "اضطراب الفنتك"},
    "liquidity_gap":              {"en": "Liquidity Gap",              "ar": "فجوة السيولة"},
    "capital_adequacy":           {"en": "Capital Adequacy Ratio",     "ar": "نسبة كفاية رأس المال"},
    # Time-to-failure variants
    "time_to_liquidity_breach":   {"en": "Time to Liquidity Breach",   "ar": "الوقت إلى كسر السيولة"},
    "time_to_insurance_failure":  {"en": "Time to Insurance Failure",  "ar": "الوقت إلى فشل التأمين"},
    "time_to_payment_failure":    {"en": "Time to Payment Failure",    "ar": "الوقت إلى فشل المدفوعات"},
    # Decision & Explanation
    "decision_actions":           {"en": "Decision Actions",           "ar": "الإجراءات المقترحة"},
    "explanation":                {"en": "Explanation",                "ar": "التفسير"},
    # Modes
    "executive_mode":             {"en": "Executive Mode",             "ar": "وضع الإدارة التنفيذية"},
    "analyst_mode":               {"en": "Analyst Mode",               "ar": "وضع المحلل"},
    "regulatory_brief":           {"en": "Regulatory Brief",           "ar": "موجز تنظيمي"},
}

FLOW_STAGES = [
    {"id": "scenario",       "en": "Event Scenario",    "ar": "سيناريو الحدث"},
    {"id": "physics",        "en": "Flow Impact",       "ar": "تأثير التدفق"},
    {"id": "graph_snapshot", "en": "Graph Snapshot",     "ar": "لقطة الرسم البياني"},
    {"id": "propagation",    "en": "Impact Chain",       "ar": "سلسلة الأثر"},
    {"id": "financial",      "en": "Financial Impact",   "ar": "الأثر المالي"},
    {"id": "sector_risk",    "en": "Sector Risk",        "ar": "مخاطر القطاع"},
    {"id": "regulatory",     "en": "Regulatory Check",   "ar": "الفحص التنظيمي"},
    {"id": "decision",       "en": "Decision Actions",   "ar": "إجراءات القرار"},
    {"id": "explanation",    "en": "Explanation",         "ar": "التفسير"},
    {"id": "output",         "en": "Output",             "ar": "المخرجات"},
]


# Canonical runtime flow order
RUNTIME_FLOW = [s["id"] for s in FLOW_STAGES]

# Core domain objects registry
CORE_OBJECTS = [
    "Scenario", "Entity", "Edge", "FlowState",
    "FinancialImpact", "BankingStress", "InsuranceStress", "FintechStress",
    "DecisionAction", "DecisionPlan", "RegulatoryState", "ExplanationPack",
]

# Project identity
PROJECT = {
    "name_en": "Impact Observatory",
    "name_ar": "مرصد الأثر",
    "short_name": "impact-observatory",
    "default_locale": "ar",
    "supported_locales": ["ar", "en"],
    "category": "executive_decision_intelligence_platform",
    "positioning_en": "Decision Intelligence for Financial Impact",
    "positioning_ar": "ذكاء القرار لقياس الأثر المالي",
    "v1_focus": "hormuz_closure",
    "primary_views": ["banking", "insurance", "fintech"],
    "secondary_views": ["sovereign"],
    "principles": [
        "financial_first", "decision_terminal", "gcc_aware",
        "auditable", "explainable", "modular",
        "json_first", "white_light_ui", "safe_migration_in_place",
    ],
}
