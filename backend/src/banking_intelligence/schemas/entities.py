"""
Banking Intelligence — Entity Registry Schemas
================================================
7 canonical entity types for GCC banking + fintech decision intelligence.

Each entity carries:
- canonical_id:         Deterministic, globally unique identifier
- source_metadata:      Provenance chain (who said what, when)
- source_confidence:    0.0–1.0 trust score on the underlying data
- validation_status:    Lifecycle gate (DRAFT → VALIDATED → ACTIVE → DEPRECATED)
- dedup_key:            Deterministic merge key for idempotent upserts

Design rules:
  - Every field is typed and validated at ingestion time
  - No untyped JSON blobs — structured evidence only
  - All IDs are prefixed by entity type for cross-system traceability
  - Timestamps are UTC, always
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Shared Enums ───────────────────────────────────────────────────────────

class ValidationStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    REJECTED = "REJECTED"


class SourceConfidenceLevel(str, Enum):
    """Human-readable confidence tier mapped from numeric score."""
    DEFINITIVE = "DEFINITIVE"      # >= 0.90
    HIGH = "HIGH"                  # >= 0.75
    MODERATE = "MODERATE"          # >= 0.50
    LOW = "LOW"                    # >= 0.25
    SPECULATIVE = "SPECULATIVE"    # < 0.25


class GCCCountryCode(str, Enum):
    SA = "SA"   # Saudi Arabia
    AE = "AE"   # UAE
    QA = "QA"   # Qatar
    KW = "KW"   # Kuwait
    BH = "BH"   # Bahrain
    OM = "OM"   # Oman


class EntitySector(str, Enum):
    BANKING = "banking"
    FINTECH = "fintech"
    INSURANCE = "insurance"
    PAYMENTS = "payments"
    CAPITAL_MARKETS = "capital_markets"
    REGULATORY = "regulatory"
    GOVERNMENT = "government"
    ENERGY = "energy"
    MARITIME = "maritime"
    LOGISTICS = "logistics"
    INFRASTRUCTURE = "infrastructure"
    HEALTHCARE = "healthcare"


class LicenseType(str, Enum):
    FULL_BANKING = "full_banking"
    DIGITAL_BANKING = "digital_banking"
    INVESTMENT_BANKING = "investment_banking"
    ISLAMIC_BANKING = "islamic_banking"
    MICROFINANCE = "microfinance"
    EMI = "emi"                        # E-money institution
    PAYMENT_SERVICE = "payment_service"
    SANDBOX = "sandbox"
    NONE = "none"


class PaymentRailType(str, Enum):
    RTGS = "rtgs"                      # Real-time gross settlement
    ACH = "ach"                        # Automated clearing house
    CARD_NETWORK = "card_network"
    MOBILE_MONEY = "mobile_money"
    SWIFT = "swift"
    BLOCKCHAIN = "blockchain"
    DOMESTIC_IPS = "domestic_ips"       # Instant payment system (SADAD, IPP, etc.)
    CROSS_BORDER = "cross_border"


class DecisionPlaybookType(str, Enum):
    CRISIS_RESPONSE = "crisis_response"
    LIQUIDITY_MANAGEMENT = "liquidity_management"
    SANCTIONS_COMPLIANCE = "sanctions_compliance"
    CYBER_INCIDENT = "cyber_incident"
    REGULATORY_ENFORCEMENT = "regulatory_enforcement"
    MARKET_HALT = "market_halt"
    COUNTERPARTY_DEFAULT = "counterparty_default"
    OPERATIONAL_CONTINUITY = "operational_continuity"


# ─── Source Metadata (provenance chain) ─────────────────────────────────────

class SourceMetadata(BaseModel):
    """Provenance record attached to every entity and edge."""
    source_system: str = Field(
        ..., min_length=1,
        description="System that produced this data (e.g., 'SAMA_registry', 'CBUAE_opendata', 'manual_entry')"
    )
    source_document_id: Optional[str] = Field(
        None, description="Reference ID in the source system"
    )
    source_url: Optional[str] = Field(
        None, description="URL to source document or API"
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this data was extracted from source"
    )
    extracted_by: str = Field(
        ..., min_length=1,
        description="Agent or user who performed extraction"
    )
    notes: Optional[str] = None


# ─── Base Entity ────────────────────────────────────────────────────────────

class BaseEntity(BaseModel):
    """Common fields for all 7 entity types."""
    canonical_id: str = Field(
        ..., min_length=3, pattern=r"^[a-z]+:[a-z0-9_\-]+$",
        description="Prefixed ID: 'bank:sa_snb', 'fintech:ae_tabby'"
    )
    name_en: str = Field(..., min_length=1, description="English name")
    name_ar: Optional[str] = Field(None, description="Arabic name")
    source_metadata: SourceMetadata
    source_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Trust score on underlying data"
    )
    validation_status: ValidationStatus = Field(default=ValidationStatus.DRAFT)
    dedup_key: str = Field(
        default="",
        description="Deterministic merge key — auto-computed if empty"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def confidence_level(self) -> SourceConfidenceLevel:
        if self.source_confidence >= 0.90:
            return SourceConfidenceLevel.DEFINITIVE
        elif self.source_confidence >= 0.75:
            return SourceConfidenceLevel.HIGH
        elif self.source_confidence >= 0.50:
            return SourceConfidenceLevel.MODERATE
        elif self.source_confidence >= 0.25:
            return SourceConfidenceLevel.LOW
        return SourceConfidenceLevel.SPECULATIVE


# ─── 1. Country ─────────────────────────────────────────────────────────────

class Country(BaseEntity):
    """
    GCC sovereign state. Anchor node for all regulatory, banking,
    and fintech relationships.

    Dedup strategy: ISO 3166-1 alpha-2 code is globally unique.
    """
    iso_alpha2: GCCCountryCode
    iso_alpha3: str = Field(..., min_length=3, max_length=3)
    currency_code: str = Field(..., min_length=3, max_length=3)
    central_bank_id: Optional[str] = Field(
        None, description="canonical_id of the central bank Authority"
    )
    gdp_usd_billions: Optional[float] = Field(None, ge=0)
    population_millions: Optional[float] = Field(None, ge=0)
    financial_sector_gdp_pct: Optional[float] = Field(None, ge=0, le=100)
    sovereign_credit_rating: Optional[str] = None
    fatf_status: Optional[str] = Field(
        None, description="FATF mutual evaluation status"
    )

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "Country":
        if not self.dedup_key:
            self.dedup_key = f"country:{self.iso_alpha2.value}"
        return self


# ─── 2. Authority ───────────────────────────────────────────────────────────

class AuthorityType(str, Enum):
    CENTRAL_BANK = "central_bank"
    SECURITIES_REGULATOR = "securities_regulator"
    INSURANCE_REGULATOR = "insurance_regulator"
    FINTECH_SANDBOX = "fintech_sandbox"
    AML_AUTHORITY = "aml_authority"
    DATA_PROTECTION = "data_protection"
    MINISTRY = "ministry"


class Authority(BaseEntity):
    """
    Regulatory or supervisory body. The entity that grants licenses,
    enforces compliance, and is the legal basis for DecisionPlaybooks.

    Dedup strategy: SHA-256(authority_type + country_code + name_en.lower())
    """
    authority_type: AuthorityType
    country_code: GCCCountryCode
    jurisdiction_scope: str = Field(
        ..., description="'national', 'free_zone', 'sector_specific'"
    )
    supervisory_powers: list[str] = Field(
        default_factory=list,
        description="Enumerated powers: ['license_grant', 'license_revoke', 'fine', 'sanction', 'audit']"
    )
    regulations_administered: list[str] = Field(
        default_factory=list,
        description="Key regulation IDs: ['SAMA_BCR', 'CBUAE_RNCF', 'QCB_CIRC_2024_01']"
    )
    website_url: Optional[str] = None

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "Authority":
        if not self.dedup_key:
            raw = f"{self.authority_type.value}:{self.country_code.value}:{self.name_en.lower().strip()}"
            self.dedup_key = f"authority:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self


# ─── 3. Bank ────────────────────────────────────────────────────────────────

class BankTier(str, Enum):
    DSIB = "DSIB"       # Domestic Systemically Important Bank
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    FOREIGN_BRANCH = "foreign_branch"


class Bank(BaseEntity):
    """
    Licensed banking institution operating in a GCC jurisdiction.

    Dedup strategy: SHA-256(swift_code) when available, else SHA-256(license_number + country).
    """
    country_code: GCCCountryCode
    swift_code: Optional[str] = Field(None, min_length=8, max_length=11)
    license_number: Optional[str] = None
    license_type: LicenseType = LicenseType.FULL_BANKING
    bank_tier: BankTier = BankTier.TIER_2
    regulator_id: Optional[str] = Field(
        None, description="canonical_id of supervising Authority"
    )
    total_assets_usd_millions: Optional[float] = Field(None, ge=0)
    tier1_capital_ratio_pct: Optional[float] = Field(None, ge=0, le=100)
    npl_ratio_pct: Optional[float] = Field(None, ge=0, le=100)
    is_islamic: bool = False
    sectors_served: list[EntitySector] = Field(default_factory=list)
    payment_rails: list[str] = Field(
        default_factory=list,
        description="canonical_ids of connected PaymentRails"
    )

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "Bank":
        if not self.dedup_key:
            if self.swift_code:
                raw = self.swift_code.upper()
            elif self.license_number:
                raw = f"{self.license_number}:{self.country_code.value}"
            else:
                raw = f"{self.name_en.lower().strip()}:{self.country_code.value}"
            self.dedup_key = f"bank:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self

    @field_validator("swift_code")
    @classmethod
    def normalize_swift(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v


# ─── 4. Fintech ─────────────────────────────────────────────────────────────

class FintechCategory(str, Enum):
    PAYMENTS = "payments"
    LENDING = "lending"
    INSURTECH = "insurtech"
    WEALTHTECH = "wealthtech"
    REGTECH = "regtech"
    OPEN_BANKING = "open_banking"
    CRYPTO_DIGITAL_ASSETS = "crypto_digital_assets"
    NEOBANK = "neobank"
    BUY_NOW_PAY_LATER = "bnpl"
    REMITTANCE = "remittance"
    CROWDFUNDING = "crowdfunding"


class Fintech(BaseEntity):
    """
    Licensed or sandbox fintech entity in a GCC jurisdiction.

    Dedup strategy: SHA-256(license_number + country) when licensed,
                    else SHA-256(name_en.lower() + country + category).
    """
    country_code: GCCCountryCode
    category: FintechCategory
    license_type: LicenseType = LicenseType.SANDBOX
    license_number: Optional[str] = None
    regulator_id: Optional[str] = Field(
        None, description="canonical_id of supervising Authority"
    )
    founding_year: Optional[int] = Field(None, ge=1990, le=2030)
    total_funding_usd_millions: Optional[float] = Field(None, ge=0)
    active_users_estimate: Optional[int] = Field(None, ge=0)
    partner_bank_ids: list[str] = Field(
        default_factory=list,
        description="canonical_ids of partner banks"
    )
    payment_rails: list[str] = Field(
        default_factory=list,
        description="canonical_ids of connected PaymentRails"
    )
    api_connectivity: list[str] = Field(
        default_factory=list,
        description="Open banking or API standards supported"
    )

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "Fintech":
        if not self.dedup_key:
            if self.license_number:
                raw = f"{self.license_number}:{self.country_code.value}"
            else:
                raw = f"{self.name_en.lower().strip()}:{self.country_code.value}:{self.category.value}"
            self.dedup_key = f"fintech:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self


# ─── 5. PaymentRail ─────────────────────────────────────────────────────────

class PaymentRail(BaseEntity):
    """
    Payment infrastructure — RTGS, ACH, card network, mobile money, etc.
    This is the connective tissue between banks, fintechs, and cross-border flows.

    Dedup strategy: SHA-256(rail_type + operator_country + system_name.lower()).
    """
    rail_type: PaymentRailType
    operator_country: GCCCountryCode
    system_name: str = Field(
        ..., min_length=1,
        description="e.g., 'SARIE', 'SADAD', 'UAE_IPP', 'NAPS'"
    )
    operator_authority_id: Optional[str] = Field(
        None, description="canonical_id of the operating Authority"
    )
    settlement_currency: str = Field(..., min_length=3, max_length=3)
    settlement_finality_minutes: Optional[float] = Field(None, ge=0)
    max_transaction_usd: Optional[float] = Field(None, ge=0)
    daily_volume_estimate_usd_millions: Optional[float] = Field(None, ge=0)
    uptime_sla_pct: Optional[float] = Field(None, ge=0, le=100)
    connected_countries: list[GCCCountryCode] = Field(default_factory=list)
    is_cross_border: bool = False

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "PaymentRail":
        if not self.dedup_key:
            raw = f"{self.rail_type.value}:{self.operator_country.value}:{self.system_name.lower().strip()}"
            self.dedup_key = f"rail:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self


# ─── 6. ScenarioTrigger ────────────────────────────────────────────────────

class TriggerSeverity(str, Enum):
    INFORMATIONAL = "informational"
    WARNING = "warning"
    ELEVATED = "elevated"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class ScenarioTrigger(BaseEntity):
    """
    An observable event or condition that activates a scenario and
    initiates a decision workflow.

    Linked to the existing SCENARIO_CATALOG (15 scenarios) and
    propagation engine.

    Dedup strategy: SHA-256(scenario_id + trigger_type + trigger_source).
    """
    scenario_id: str = Field(
        ..., description="Maps to SCENARIO_CATALOG key (e.g., 'hormuz_chokepoint_disruption')"
    )
    trigger_type: str = Field(
        ..., description="'price_threshold', 'event_detection', 'indicator_breach', 'manual_escalation'"
    )
    trigger_source: str = Field(
        ..., description="Data source: 'bloomberg', 'acled', 'manual', 'aisstream', 'satellite'"
    )
    severity: TriggerSeverity = TriggerSeverity.WARNING
    threshold_condition: str = Field(
        ..., description="Machine-parseable condition: 'brent_crude_usd > 120', 'hormuz_transit_count < 5'"
    )
    affected_entity_ids: list[str] = Field(
        default_factory=list,
        description="canonical_ids of directly affected entities"
    )
    affected_sectors: list[EntitySector] = Field(default_factory=list)
    expected_propagation_hours: Optional[float] = Field(None, ge=0)
    historical_frequency_per_year: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "ScenarioTrigger":
        if not self.dedup_key:
            raw = f"{self.scenario_id}:{self.trigger_type}:{self.trigger_source}"
            self.dedup_key = f"trigger:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self


# ─── 7. DecisionPlaybook ───────────────────────────────────────────────────

class PlaybookStep(BaseModel):
    """Single step in a decision playbook."""
    step_number: int = Field(..., ge=1)
    action: str = Field(..., min_length=1)
    owner_entity_id: str = Field(
        ..., description="canonical_id of the entity responsible"
    )
    time_window_hours: Optional[float] = Field(None, ge=0)
    escalation_condition: Optional[str] = None
    requires_approval: bool = False
    approval_authority_id: Optional[str] = None
    evidence_required: list[str] = Field(default_factory=list)


class DecisionPlaybook(BaseEntity):
    """
    Predefined response playbook for a scenario class.
    Links triggers → decisions → owners → approval chains.

    Dedup strategy: SHA-256(playbook_type + scenario_id + version).
    """
    playbook_type: DecisionPlaybookType
    scenario_id: str = Field(
        ..., description="Maps to SCENARIO_CATALOG key"
    )
    version: str = Field(default="1.0.0")
    legal_authority_basis: str = Field(
        ..., description="Regulatory or legal basis: 'SAMA_BCR_Art_42', 'CBUAE_RNCF_S3'"
    )
    primary_owner_id: str = Field(
        ..., description="canonical_id of primary decision owner"
    )
    escalation_chain: list[str] = Field(
        default_factory=list,
        description="Ordered canonical_ids for escalation"
    )
    steps: list[PlaybookStep] = Field(
        ..., min_length=1,
        description="Ordered execution steps"
    )
    max_response_hours: float = Field(..., gt=0)
    review_frequency_hours: Optional[float] = Field(None, gt=0)
    applicable_sectors: list[EntitySector] = Field(default_factory=list)
    applicable_countries: list[GCCCountryCode] = Field(default_factory=list)

    @model_validator(mode="after")
    def compute_dedup_key(self) -> "DecisionPlaybook":
        if not self.dedup_key:
            raw = f"{self.playbook_type.value}:{self.scenario_id}:{self.version}"
            self.dedup_key = f"playbook:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return self

    @field_validator("steps")
    @classmethod
    def validate_step_order(cls, v: list[PlaybookStep]) -> list[PlaybookStep]:
        numbers = [s.step_number for s in v]
        if numbers != sorted(numbers):
            raise ValueError("Playbook steps must be in ascending order")
        if len(numbers) != len(set(numbers)):
            raise ValueError("Playbook step numbers must be unique")
        return v


# ─── Entity Type Registry (for dynamic dispatch) ───────────────────────────

ENTITY_TYPE_MAP: dict[str, type[BaseEntity]] = {
    "country": Country,
    "authority": Authority,
    "bank": Bank,
    "fintech": Fintech,
    "payment_rail": PaymentRail,
    "scenario_trigger": ScenarioTrigger,
    "decision_playbook": DecisionPlaybook,
}
