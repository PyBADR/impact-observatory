"""Signal Intelligence Layer — Quality Types.

Typed output contracts for the three quality engines:
  RegionMapping    — output of region_engine.resolve_regions()
  DomainMapping    — output of domain_engine.resolve_domains()
  SeverityEstimate — output of severity_engine.compute_severity()
  SignalClassification — combined quality assessment from mapper.classify_event()

Design rules:
  - All types are dataclasses (not Pydantic) for speed — they are ephemeral
  - All fields are read-only where possible (frozen=True or plain)
  - No Pack 1 types imported here — types.py has zero upward dependencies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SignalQuality(str, Enum):
    """Composite quality tier for a classified SourceEvent.

    Derived from region coverage, domain coverage, source confidence,
    and data completeness. NOT the same as signal severity.

    POOR       — minimal usable data (no region, no domain, unverified)
    LOW        — some data but significant gaps
    ACCEPTABLE — GCC region identified or domain identified, moderate confidence
    GOOD       — both region + domain identified, reasonable confidence
    HIGH       — GCC region + domain + description + timestamp, good confidence
    """
    POOR       = "poor"
    LOW        = "low"
    ACCEPTABLE = "acceptable"
    GOOD       = "good"
    HIGH       = "high"


@dataclass
class RegionMatch:
    """A single matched region with source traceability."""
    region_value: str               # GCCRegion.value (e.g. "SA")
    matched_keyword: str            # the keyword that triggered this match
    matched_text: str               # the original hint text it was found in
    confidence: float               # 0.0–1.0, set by engine per keyword type


@dataclass
class RegionMapping:
    """Output of region_engine.resolve_regions().

    Contains all matched GCC regions, confidence, and traceability.
    """
    matched_regions: list[str] = field(default_factory=list)
    # GCCRegion.value strings — e.g. ["SA", "AE"]

    gcc_detected: bool = False
    # True if any GCC member state (or GCC_WIDE) was identified

    region_matches: list[RegionMatch] = field(default_factory=list)
    # Detailed per-match traceability

    confidence: float = 0.0
    # Aggregate confidence: max(match.confidence) across all matches

    coverage_score: float = 0.0
    # 0.0–1.0: how many GCC members are covered (6 members = 1.0)
    # GCC_WIDE alone counts as 0.5

    @property
    def is_empty(self) -> bool:
        return len(self.matched_regions) == 0


@dataclass
class DomainMatch:
    """A single matched domain with weight and source traceability."""
    domain_value: str           # ImpactDomain.value
    matched_keyword: str        # keyword that triggered match
    matched_text: str           # original hint text
    match_weight: float         # 0.0–1.0 strength of this keyword match


@dataclass
class DomainMapping:
    """Output of domain_engine.resolve_domains().

    Contains all matched ImpactDomains with per-domain confidence.
    """
    matched_domains: list[str] = field(default_factory=list)
    # ImpactDomain.value strings, ordered by total match weight descending

    domain_weights: dict[str, float] = field(default_factory=dict)
    # {domain_value: aggregate_weight}

    domain_matches: list[DomainMatch] = field(default_factory=list)
    # All individual keyword hits for traceability

    primary_domain: str | None = None
    # Highest-weighted domain (or None if no domains matched)

    confidence: float = 0.0
    # Aggregate confidence: based on number of domain hits and weights

    @property
    def is_empty(self) -> bool:
        return len(self.matched_domains) == 0

    @property
    def domain_count(self) -> int:
        return len(self.matched_domains)


@dataclass
class SeverityEstimate:
    """Output of severity_engine.compute_severity().

    Multi-factor severity score with per-factor breakdown.
    """
    score: float = 0.25
    # Final severity score [0.0, 1.0]

    # ── Per-factor contributions ───────────────────────────────────────────────
    confidence_factor: float = 0.25
    # From source_confidence level (base factor, weight 0.45)

    domain_factor: float = 0.0
    # From matched domain exposure weights (weight 0.20)

    urgency_factor: float = 0.0
    # From urgency keyword presence (weight 0.25)

    region_factor: float = 0.0
    # From GCC region coverage breadth (weight 0.10)

    # ── Explanation ───────────────────────────────────────────────────────────
    urgency_keywords_found: list[str] = field(default_factory=list)
    # Which urgency keywords triggered the urgency_factor

    high_exposure_domains: list[str] = field(default_factory=list)
    # Domain values that contributed to domain_factor

    notes: str = ""
    # Human-readable explanation of how the score was derived


@dataclass
class SignalClassification:
    """Full quality classification output from mapper.classify_event().

    Combines all three engine outputs into a single typed result.
    """
    quality: SignalQuality = SignalQuality.POOR

    region_mapping: RegionMapping = field(default_factory=RegionMapping)
    domain_mapping: DomainMapping = field(default_factory=DomainMapping)
    severity_estimate: SeverityEstimate = field(default_factory=SeverityEstimate)

    # ── Quality score components ───────────────────────────────────────────────
    quality_score: float = 0.0
    # Normalized quality score [0.0, 1.0] before tier mapping

    quality_factors: dict[str, float] = field(default_factory=dict)
    # {factor_name: score} for each quality dimension

    notes: list[str] = field(default_factory=list)
    # Human-readable notes about quality assessment

    @property
    def has_gcc_region(self) -> bool:
        return self.region_mapping.gcc_detected

    @property
    def has_domain(self) -> bool:
        return not self.domain_mapping.is_empty

    @property
    def suggested_severity(self) -> float:
        return self.severity_estimate.score
