# PACK 3 — IMPACT ENGINE + DECISION BRAIN
## Architecture Brief | مرصد الأثر

**Version**: 1.0.0
**Date**: 2026-04-08
**Author**: Principal Architect
**Status**: DESIGN COMPLETE — Ready for Implementation

---

## 1. ARCHITECTURE DECISION

### What
Three new modules inserted **after** the existing 17-stage pipeline (Stages 1–17) and **before** the audit stage (Stage 18). The existing pipeline output becomes the **input** to Pack 3. No existing stage is modified.

### Why
The current pipeline terminates at **propagation + templated actions**. It answers "what happened and how it spread" but does not answer:

- **"What is the structured impact?"** — which domains, entities, and exposures are affected, with what severity and confidence, over what time horizon?
- **"What should we do and why?"** — what is the recommended action, ranked by urgency, with a reasoning chain traceable to the graph and propagation?

Pack 3 closes this gap by adding two computational layers and one integration bridge.

### Which Layer
```
Layer 5 (Agents) — Impact Engine    → synthesizes pipeline outputs into structured impact
Layer 5 (Agents) — Decision Brain   → produces decision-ready output with reasoning chains
Layer 6 (APIs)   — Decision Bridge  → connects impact + decision to audit, graph, explainability
```

### Trade-off Analysis

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Inline into simulation_engine.py | Single file, simple | Violates SRP, 1100+ line file grows to 1500+ | **Rejected** |
| Separate modules, called from engine | Clean separation, testable | Extra import layer | **Selected** |
| Microservice extraction | Independent scaling | Premature, adds latency + infra | **Rejected** |
| LLM-based decision | Flexible reasoning | Non-deterministic, violates "no black-box AI" rule | **Rejected** |

---

## 2. DATA FLOW

```
Source → Transform → Sink (explicit, typed, versioned)

┌─────────────────────────────────────────────────────────────────┐
│  EXISTING PIPELINE (Stages 1–17) — UNTOUCHED                   │
│                                                                 │
│  [Scenario] → [Event Severity] → [Sector Exposure]             │
│  → [Propagation] → [Liquidity Stress] → [Insurance Stress]     │
│  → [Financial Losses] → [URS] → [Confidence] → [Physics]       │
│  → [Bottlenecks] → [Shock Wave] → [Congestion] → [Recovery]    │
│  → [Flow Simulation] → [Decision Actions] → [Explainability]   │
│                                                                 │
│  OUTPUT: dict with 40+ fields (all typed, all defaulted)        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PACK 3 — STAGE 17A: IMPACT ENGINE                             │
│                                                                 │
│  INPUT:  PipelineOutput (typed wrapper around engine dict)      │
│  TRANSFORM:                                                     │
│    1. Domain classification (9 GCC sectors → affected domains)  │
│    2. Entity impact ranking (top-N entities by loss + stress)   │
│    3. Severity scoring (composite of URS + sector stress)       │
│    4. Confidence scoring (pipeline confidence × coverage)       │
│    5. Exposure estimation (sector_exposure × financial_impact)  │
│    6. Time horizon mapping (peak_day → recovery_trajectory)     │
│  OUTPUT: ImpactAssessment (Pydantic model, fully typed)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PACK 3 — STAGE 17B: DECISION BRAIN                            │
│                                                                 │
│  INPUT:  ImpactAssessment + PipelineOutput                     │
│  TRANSFORM:                                                     │
│    1. Action synthesis (impact-weighted re-ranking of actions)  │
│    2. Urgency classification (time_to_first_failure × severity) │
│    3. Confidence scoring (impact confidence × action coverage)  │
│    4. Reasoning chain construction (graph → propagation → loss) │
│    5. Fallback path (works without graph, uses propagation)     │
│  OUTPUT: DecisionOutput (Pydantic model, fully typed)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PACK 3 — STAGE 17C: DECISION BRIDGE                           │
│                                                                 │
│  INPUT:  ImpactAssessment + DecisionOutput + PipelineOutput    │
│  TRANSFORM:                                                     │
│    1. Audit record (SHA-256 hash of impact + decision)          │
│    2. Graph annotation (write impact/decision to graph store)   │
│    3. Explainability merge (append reasoning chain to causal)   │
│    4. Decision-ready envelope (final output structure)          │
│  OUTPUT: DecisionEnvelope (Pydantic model, final Pack 3 out)   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXISTING ORCHESTRATOR (run_orchestrator.py)                    │
│  Stage 18: Audit + response assembly                            │
│  Pack 3 output merged into response dict (additive, not mutate)│
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. SCHEMA / CONTRACT — Field-Level Definitions

### 3.1 PipelineOutput (Internal — typed wrapper, NOT a new schema)

No new Pydantic model needed. This is a `TypedDict` or protocol that types the existing engine output dict for static analysis:

```python
# backend/src/impact_engine/types.py
from typing import TypedDict, Any

class PipelineOutput(TypedDict):
    """Typed view over SimulationEngine.run() output.
    Does NOT add new fields — just types the existing dict."""
    run_id: str
    scenario_id: str
    event_severity: float
    propagation_score: float
    unified_risk_score: float  # float or dict — engine returns both
    risk_level: str
    confidence_score: float
    peak_day: int
    financial_impact: dict[str, Any]
    sector_analysis: list[dict[str, Any]]
    propagation_chain: list[dict[str, Any]]
    banking_stress: dict[str, Any]
    insurance_stress: dict[str, Any]
    fintech_stress: dict[str, Any]
    flow_analysis: dict[str, Any]
    physical_system_status: dict[str, Any]
    bottlenecks: list[dict[str, Any]]
    recovery_trajectory: list[dict[str, Any]]
    explainability: dict[str, Any]
    decision_plan: dict[str, Any]
    headline: dict[str, Any]
```

### 3.2 ImpactAssessment (New Pydantic Model)

```python
# Added to backend/src/simulation_schemas.py

class AffectedDomain(BaseModel):
    """A single affected domain (sector) with impact metrics."""
    domain: str = ""                       # sector name (energy, maritime, banking, etc.)
    domain_ar: str = ""                    # Arabic sector name
    exposure_score: float = 0.0            # sector exposure [0,1]
    stress_score: float = 0.0             # max(liquidity, insurance, fintech stress for this sector)
    loss_usd: float = 0.0                 # total loss attributed to this domain
    loss_pct: float = 0.0                 # % of total loss
    entity_count: int = 0                  # entities in this domain
    critical_entity_count: int = 0         # entities at HIGH/SEVERE
    classification: str = "NOMINAL"        # NOMINAL|LOW|GUARDED|ELEVATED|HIGH|SEVERE
    is_primary_affected: bool = False      # True if domain contains shock nodes
    propagation_rank: int = 0              # rank by propagation contribution


class AffectedEntity(BaseModel):
    """A single affected entity with full impact profile."""
    entity_id: str = ""
    entity_label: str = ""
    entity_label_ar: str = ""
    sector: str = ""
    loss_usd: float = 0.0
    stress_score: float = 0.0
    classification: str = "NOMINAL"
    propagation_factor: float = 1.0
    is_shock_origin: bool = False          # True if entity is a shock node
    hop_distance: int = 0                  # 0 = shock origin, 1 = first hop, etc.
    impact_mechanism: str = ""             # primary propagation mechanism


class TimeHorizon(BaseModel):
    """Time-based impact profile."""
    peak_impact_day: int = 0
    peak_loss_usd: float = 0.0
    recovery_start_day: int = 0
    recovery_50pct_day: int = 0            # day when 50% recovered
    recovery_90pct_day: int = 0            # day when 90% recovered
    full_recovery_days: int = 0
    time_to_first_failure_hours: float = 9999.0
    horizon_classification: str = "ACUTE"  # ACUTE (<7d), SUSTAINED (7-30d), CHRONIC (>30d)


class ImpactAssessment(BaseModel):
    """Structured impact assessment — output of the Impact Engine.

    CONTRACT: Every signal produces an ImpactAssessment.
    All fields have safe defaults. No Optional numerics. No Optional lists.
    """
    # Identity
    run_id: str = ""
    scenario_id: str = ""
    assessment_version: str = "1.0.0"

    # Aggregate severity
    composite_severity: float = 0.0        # weighted composite [0,1]
    severity_classification: str = "NOMINAL"
    confidence: float = 0.0                # [0,1] — how confident is this assessment

    # Affected domains
    affected_domains: List[AffectedDomain] = Field(default_factory=list)
    primary_domain: str = ""               # most affected domain
    domain_count: int = 0                  # number of affected domains (exposure > 0.01)
    cross_domain_propagation: bool = False  # True if >1 domain affected

    # Affected entities
    affected_entities: List[AffectedEntity] = Field(default_factory=list)
    entity_count: int = 0
    critical_entity_count: int = 0

    # Exposure
    total_exposure_usd: float = 0.0
    direct_exposure_usd: float = 0.0
    indirect_exposure_usd: float = 0.0
    systemic_exposure_usd: float = 0.0
    gdp_impact_pct: float = 0.0

    # Time horizon
    time_horizon: TimeHorizon = Field(default_factory=TimeHorizon)

    # Source traceability
    source_pipeline_stages: List[str] = Field(default_factory=list)
    graph_enriched: bool = False
```

### 3.3 DecisionOutput (New Pydantic Model)

```python
class ReasoningStep(BaseModel):
    """A single step in the decision reasoning chain."""
    step: int = 0
    layer: str = ""                        # "graph"|"propagation"|"impact"|"rule"
    source_entity: str = ""                # entity or node that originated this step
    mechanism: str = ""                    # mechanism (from explainability library)
    evidence_value: float = 0.0            # numeric evidence (score, loss, etc.)
    evidence_label: str = ""               # human-readable evidence
    confidence: float = 0.0


class RecommendedAction(BaseModel):
    """A decision action with full reasoning chain."""
    action_id: str = ""
    rank: int = 0
    action_type: str = ""                  # MITIGATE|HEDGE|TRANSFER|ACCEPT|ESCALATE|MONITOR
    sector: str = ""
    owner: str = ""
    action: str = ""
    action_ar: str = ""
    urgency: str = "MONITOR"               # IMMEDIATE|URGENT|MONITOR|WATCH
    urgency_score: float = 0.0             # [0,1]
    confidence: float = 0.0                # [0,1]
    loss_avoided_usd: float = 0.0
    cost_usd: float = 0.0
    net_benefit_usd: float = 0.0           # loss_avoided - cost
    roi_ratio: float = 0.0                 # loss_avoided / max(cost, 1)
    regulatory_risk: float = 0.0
    feasibility: float = 0.0
    time_to_act_hours: int = 24
    reasoning_chain: List[ReasoningStep] = Field(default_factory=list)
    impact_domains_addressed: List[str] = Field(default_factory=list)
    status: str = "PENDING_REVIEW"


class DecisionOutput(BaseModel):
    """Structured decision output — output of the Decision Brain.

    CONTRACT: Every ImpactAssessment produces a DecisionOutput.
    Output is deterministic and traceable. No black-box AI.
    """
    # Identity
    run_id: str = ""
    scenario_id: str = ""
    decision_version: str = "1.0.0"

    # Primary recommendation
    primary_action: str = ""               # top-ranked action text
    primary_action_type: str = "MONITOR"   # MITIGATE|HEDGE|TRANSFER|ACCEPT|ESCALATE|MONITOR
    overall_urgency: str = "MONITOR"       # IMMEDIATE|URGENT|MONITOR|WATCH
    overall_confidence: float = 0.0        # [0,1]

    # Recommended actions (ranked)
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)

    # Reasoning summary
    reasoning_summary_en: str = ""
    reasoning_summary_ar: str = ""
    reasoning_chain_length: int = 0

    # Decision metadata
    decision_basis: str = "deterministic"  # "deterministic"|"graph_enriched"|"fallback"
    graph_contribution_pct: float = 0.0    # % of reasoning from graph (0 if graph disabled)
    propagation_contribution_pct: float = 0.0
    rule_contribution_pct: float = 0.0

    # Fallback status
    fallback_active: bool = False          # True if graph was unavailable
    fallback_reason: str = ""
```

### 3.4 DecisionEnvelope (New Pydantic Model — Final Pack 3 Output)

```python
class AuditDigest(BaseModel):
    """SHA-256 digest for audit trail."""
    impact_hash: str = ""                  # SHA-256 of ImpactAssessment JSON
    decision_hash: str = ""                # SHA-256 of DecisionOutput JSON
    combined_hash: str = ""                # SHA-256 of impact_hash + decision_hash
    timestamp: str = ""
    pipeline_version: str = "2.1.0"
    pack_version: str = "3.0.0"


class DecisionEnvelope(BaseModel):
    """Final Pack 3 output — wraps impact + decision + audit.

    This is the decision-ready output that connects to:
    - Decision graph (via graph_annotation_status)
    - Audit trace (via audit_digest)
    - Explainability chain (via merged_reasoning_chain)
    """
    # Identity
    run_id: str = ""
    scenario_id: str = ""
    envelope_version: str = "1.0.0"

    # Core payloads
    impact_assessment: ImpactAssessment = Field(default_factory=ImpactAssessment)
    decision_output: DecisionOutput = Field(default_factory=DecisionOutput)

    # Audit
    audit_digest: AuditDigest = Field(default_factory=AuditDigest)

    # Graph integration
    graph_annotation_status: str = "NOT_CONNECTED"  # NOT_CONNECTED|ANNOTATED|SKIPPED

    # Merged explainability (graph + propagation + impact + decision)
    merged_reasoning_chain: List[Dict[str, Any]] = Field(default_factory=list)

    # Decision-readiness flag
    decision_ready: bool = False           # True when all validations pass
    decision_ready_reason: str = ""        # why it is/isn't ready
```

### 3.5 Validation Rules

| Field | Rule | Error if Violated |
|-------|------|-------------------|
| `composite_severity` | `0.0 ≤ v ≤ 1.0` | Clamp + warn |
| `confidence` | `0.0 ≤ v ≤ 1.0` | Clamp + warn |
| `affected_domains` | `len > 0` | At least 1 domain (shock origin) |
| `affected_entities` | `len > 0` | At least 1 entity |
| `total_exposure_usd` | `≥ 0` | Clamp to 0 |
| `recommended_actions` | `len > 0` | At least MONITOR action generated |
| `reasoning_chain` per action | `len > 0` | At least 1 reasoning step |
| `audit_digest.combined_hash` | non-empty | Raise if hash generation fails |
| `decision_ready` | Must be explicitly set | Never default-true |

---

## 4. SERVICE DESIGN

### 4.1 File Structure

```
backend/src/
├── impact_engine/                    ← NEW PACKAGE
│   ├── __init__.py
│   ├── types.py                      ← PipelineOutput TypedDict
│   ├── engine.py                     ← compute_impact_assessment()
│   ├── domain_classifier.py          ← classify affected domains
│   ├── entity_ranker.py              ← rank affected entities
│   └── time_horizon.py               ← compute time horizon profile
│
├── decision_brain/                   ← NEW PACKAGE
│   ├── __init__.py
│   ├── brain.py                      ← compute_decision_output()
│   ├── action_synthesizer.py         ← re-rank actions with impact weighting
│   ├── reasoning_builder.py          ← construct reasoning chains
│   └── fallback.py                   ← fallback path when graph disabled
│
├── decision_bridge/                  ← NEW PACKAGE
│   ├── __init__.py
│   ├── bridge.py                     ← assemble_decision_envelope()
│   ├── audit_hasher.py               ← SHA-256 audit digest
│   ├── graph_annotator.py            ← write to graph store (fail-safe)
│   └── explainability_merger.py      ← merge reasoning into causal chain
│
├── simulation_engine.py              ← UNCHANGED (Pack 1/2)
├── simulation_schemas.py             ← ADDITIVE ONLY (new models appended)
├── config.py                         ← ADDITIVE ONLY (new constants appended)
├── decision_layer.py                 ← UNCHANGED (Pack 1/2)
├── explainability.py                 ← UNCHANGED (Pack 1/2)
└── services/
    └── run_orchestrator.py           ← MODIFIED (calls Pack 3 after engine.run())
```

### 4.2 Module Contracts

#### `impact_engine/engine.py`

```python
def compute_impact_assessment(
    pipeline_output: dict,          # raw engine.run() output
    gcc_nodes: list[dict],          # GCC_NODES registry
    scenario_catalog: dict,         # SCENARIO_CATALOG
    graph_store: Optional[Any] = None,  # GraphStore if available
) -> dict:
    """
    Compute structured impact assessment from pipeline output.

    DETERMINISTIC: Same input → same output.
    FAIL-SAFE: Works without graph_store.
    CONTRACT: Returns dict that passes ImpactAssessment.model_validate().
    """
```

#### `decision_brain/brain.py`

```python
def compute_decision_output(
    impact_assessment: dict,        # validated ImpactAssessment dict
    pipeline_output: dict,          # raw engine.run() output
    existing_actions: list[dict],   # from decision_layer.build_decision_actions()
    graph_store: Optional[Any] = None,
) -> dict:
    """
    Compute structured decision output from impact assessment.

    DETERMINISTIC: Same input → same output.
    FAIL-SAFE: Works without graph_store (sets fallback_active=True).
    CONTRACT: Returns dict that passes DecisionOutput.model_validate().
    """
```

#### `decision_bridge/bridge.py`

```python
def assemble_decision_envelope(
    impact_assessment: dict,
    decision_output: dict,
    pipeline_output: dict,
    graph_store: Optional[Any] = None,
) -> dict:
    """
    Assemble final decision envelope with audit + graph + explainability.

    CONTRACT: Returns dict that passes DecisionEnvelope.model_validate().
    AUDIT: Generates SHA-256 hashes for impact + decision.
    GRAPH: Annotates graph store if available (fail-safe).
    """
```

### 4.3 Integration into Pipeline

**run_orchestrator.py — Changes (ADDITIVE ONLY)**:

```python
# After line 64 (after _engine.run()):
from src.impact_engine.engine import compute_impact_assessment
from src.decision_brain.brain import compute_decision_output
from src.decision_bridge.bridge import assemble_decision_envelope

# Stage 17A: Impact Engine
t0 = time.monotonic()
impact_assessment = compute_impact_assessment(
    pipeline_output=result,
    gcc_nodes=GCC_NODES,
    scenario_catalog=SCENARIO_CATALOG,
    graph_store=None,  # Pass graph_store when available
)
stage_timings["impact_engine"] = round((time.monotonic() - t0) * 1000, 1)

# Stage 17B: Decision Brain
t0 = time.monotonic()
decision_output = compute_decision_output(
    impact_assessment=impact_assessment,
    pipeline_output=result,
    existing_actions=decision_plan.get("actions", []),
    graph_store=None,
)
stage_timings["decision_brain"] = round((time.monotonic() - t0) * 1000, 1)

# Stage 17C: Decision Bridge
t0 = time.monotonic()
decision_envelope = assemble_decision_envelope(
    impact_assessment=impact_assessment,
    decision_output=decision_output,
    pipeline_output=result,
    graph_store=None,
)
stage_timings["decision_bridge"] = round((time.monotonic() - t0) * 1000, 1)

# Merge into response (ADDITIVE — does not overwrite existing keys)
response["impact_assessment"] = impact_assessment
response["decision_output"] = decision_output
response["decision_envelope"] = decision_envelope
response["pipeline_stages_completed"] = 21  # was 18, now 18 + 3
```

**SimulateResponse — Changes (ADDITIVE ONLY)**:

```python
# New fields appended to SimulateResponse (never modifying existing fields)
impact_assessment: Dict[str, Any] = Field(default_factory=dict)
decision_output: Dict[str, Any] = Field(default_factory=dict)
decision_envelope: Dict[str, Any] = Field(default_factory=dict)
```

---

## 5. INTEGRATION POINTS

### 5.1 Upstream Dependencies (Pack 3 reads FROM)

| Source | Field | Used By |
|--------|-------|---------|
| `simulation_engine.run()` | full output dict | Impact Engine (input) |
| `config.py` | SECTOR_ALPHA, RISK_THRESHOLDS | Domain classifier |
| `config.py` | DL_P_W1–W5 | Action re-ranking |
| `GCC_NODES` | node registry | Entity ranker |
| `SCENARIO_CATALOG` | scenario metadata | Time horizon computation |
| `decision_layer.build_decision_actions()` | existing actions list | Decision Brain (re-ranks) |
| `explainability.build_causal_chain()` | causal chain | Reasoning builder |
| `graph_brain.store.GraphStore` | graph store (optional) | Graph annotator |

### 5.2 Downstream Consumers (Pack 3 writes TO)

| Consumer | Field | How |
|----------|-------|-----|
| `run_orchestrator.py` | response dict | Merged as `impact_assessment`, `decision_output`, `decision_envelope` |
| `audit_service` | audit digest | Appended to audit log |
| `graph_brain.store` | impact + decision nodes | Graph annotation (fail-safe) |
| `SimulateResponse` | 3 new dict fields | Schema-validated |
| Future: API endpoints | `/runs/{id}/impact`, `/runs/{id}/decision-brain` | New GET routes |

### 5.3 Pack 1/2 Boundary — Zero Modification Guarantee

| File | Pack 3 Impact |
|------|---------------|
| `simulation_engine.py` | **UNTOUCHED** — no imports, no calls, no edits |
| `risk_models.py` | **UNTOUCHED** |
| `physics_intelligence_layer.py` | **UNTOUCHED** |
| `flow_models.py` | **UNTOUCHED** |
| `decision_layer.py` | **UNTOUCHED** — Pack 3 re-ranks its output, does not modify it |
| `explainability.py` | **UNTOUCHED** — Pack 3 merges into reasoning chain, does not modify |
| `config.py` | **ADDITIVE ONLY** — new constants appended, existing untouched |
| `simulation_schemas.py` | **ADDITIVE ONLY** — new models appended, existing untouched |

---

## 6. CONFIG.PY ADDITIONS

```python
# ═══════════════════════════════════════════════════════════════════════════════
# Pack 3: Impact Engine Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Composite severity weights
# CompositeSeverity = IE_W1*URS + IE_W2*EventSev + IE_W3*PropScore + IE_W4*PeakStress
IE_W1: float = 0.35   # unified risk score weight
IE_W2: float = 0.25   # event severity weight
IE_W3: float = 0.25   # propagation score weight
IE_W4: float = 0.15   # peak sector stress weight

# Domain exposure threshold — below this, domain is not "affected"
IE_DOMAIN_EXPOSURE_THRESHOLD: float = 0.01

# Entity impact threshold — below this stress, entity excluded from assessment
IE_ENTITY_STRESS_THRESHOLD: float = 0.005

# Time horizon classification boundaries (days)
IE_ACUTE_THRESHOLD_DAYS: int = 7
IE_SUSTAINED_THRESHOLD_DAYS: int = 30

# Recovery interpolation for 50% and 90% milestones
IE_RECOVERY_50_FACTOR: float = 0.50
IE_RECOVERY_90_FACTOR: float = 0.90

# ═══════════════════════════════════════════════════════════════════════════════
# Pack 3: Decision Brain Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Action re-ranking weights (impact-aware)
# ReRank = DB_W1*original_priority + DB_W2*domain_severity + DB_W3*net_benefit + DB_W4*confidence
DB_W1: float = 0.30   # original priority score weight
DB_W2: float = 0.30   # domain severity alignment weight
DB_W3: float = 0.25   # net benefit (ROI) weight
DB_W4: float = 0.15   # confidence weight

# Urgency classification thresholds
DB_URGENCY_IMMEDIATE_THRESHOLD: float = 0.80
DB_URGENCY_URGENT_THRESHOLD: float = 0.60
DB_URGENCY_MONITOR_THRESHOLD: float = 0.35

# Action type classification thresholds
DB_MITIGATE_THRESHOLD: float = 0.65
DB_HEDGE_THRESHOLD: float = 0.45
DB_TRANSFER_THRESHOLD: float = 0.30
DB_ACCEPT_THRESHOLD: float = 0.15

# Graph contribution scaling (when graph available)
DB_GRAPH_CONTRIBUTION_BASE: float = 0.25  # base % of reasoning from graph

# ═══════════════════════════════════════════════════════════════════════════════
# Pack 3: Decision Bridge Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Decision readiness thresholds
BRIDGE_MIN_CONFIDENCE: float = 0.30        # below this → decision_ready=False
BRIDGE_MIN_ACTIONS: int = 1                # must have at least 1 action
BRIDGE_MIN_REASONING_STEPS: int = 1        # must have at least 1 reasoning step
```

---

## 7. IMPLEMENTATION STEPS — Ordered Execution Sequence

| Step | Module | Task | Owner | Depends On |
|------|--------|------|-------|------------|
| 1 | `simulation_schemas.py` | Append 7 new Pydantic models (AffectedDomain, AffectedEntity, TimeHorizon, ImpactAssessment, ReasoningStep, RecommendedAction, DecisionOutput, AuditDigest, DecisionEnvelope) | Backend | None |
| 2 | `config.py` | Append Pack 3 constants (IE_*, DB_*, BRIDGE_*) | Backend | None |
| 3 | `impact_engine/types.py` | Create PipelineOutput TypedDict | Backend | Step 1 |
| 4 | `impact_engine/domain_classifier.py` | Classify affected domains from sector_analysis + sector_exposure | Backend | Steps 1, 2 |
| 5 | `impact_engine/entity_ranker.py` | Rank entities from financial_impact.top_entities + propagation_chain | Backend | Steps 1, 2 |
| 6 | `impact_engine/time_horizon.py` | Compute time horizon from peak_day + recovery_trajectory | Backend | Steps 1, 2 |
| 7 | `impact_engine/engine.py` | Assemble ImpactAssessment from steps 4–6 | Backend | Steps 3–6 |
| 8 | `decision_brain/reasoning_builder.py` | Build reasoning chains from causal_chain + propagation | Backend | Step 1 |
| 9 | `decision_brain/action_synthesizer.py` | Re-rank actions using impact assessment | Backend | Steps 1, 2, 7 |
| 10 | `decision_brain/fallback.py` | Fallback path using propagation only | Backend | Steps 1, 8 |
| 11 | `decision_brain/brain.py` | Assemble DecisionOutput from steps 8–10 | Backend | Steps 7–10 |
| 12 | `decision_bridge/audit_hasher.py` | SHA-256 digest generation | Backend | Step 1 |
| 13 | `decision_bridge/graph_annotator.py` | Graph store annotation (fail-safe) | Backend | Step 1 |
| 14 | `decision_bridge/explainability_merger.py` | Merge reasoning into causal chain | Backend | Steps 1, 8 |
| 15 | `decision_bridge/bridge.py` | Assemble DecisionEnvelope | Backend | Steps 11–14 |
| 16 | `run_orchestrator.py` | Insert Pack 3 stages (17A/B/C) after engine.run() | Backend | Step 15 |
| 17 | `tests/test_pack3_contracts.py` | Contract tests for all new models | Backend | Step 16 |
| 18 | `tests/test_pack3_regression.py` | Regression tests against Pack 1/2 | Backend | Step 17 |

---

## 8. TEST PLAN

### 8.1 Contract Tests (`test_pack3_contracts.py`)

```python
# For every scenario × severity combination in the existing test matrix:

def test_impact_assessment_passes_schema(scenario_id, severity):
    """ImpactAssessment validates against Pydantic model."""

def test_decision_output_passes_schema(scenario_id, severity):
    """DecisionOutput validates against Pydantic model."""

def test_decision_envelope_passes_schema(scenario_id, severity):
    """DecisionEnvelope validates against Pydantic model."""

def test_every_signal_produces_decision(scenario_id, severity):
    """Every scenario produces decision_ready=True output."""

def test_output_is_deterministic(scenario_id, severity):
    """Two runs with same input produce identical output."""

def test_reasoning_chain_traceable(scenario_id, severity):
    """Every RecommendedAction has ≥1 ReasoningStep tracing to graph or propagation."""

def test_audit_hash_non_empty(scenario_id, severity):
    """SHA-256 hashes are present and correctly formatted."""

def test_fallback_without_graph(scenario_id, severity):
    """Pack 3 produces valid output when graph_store=None."""

def test_affected_domains_non_empty(scenario_id, severity):
    """At least 1 affected domain for every scenario."""

def test_recommended_actions_non_empty(scenario_id, severity):
    """At least 1 recommended action for every scenario."""

def test_numeric_fields_never_none(scenario_id, severity):
    """All numeric fields in Pack 3 output are float/int, never None."""

def test_list_fields_never_none(scenario_id, severity):
    """All list fields in Pack 3 output are list, never None."""
```

### 8.2 Regression Tests (`test_pack3_regression.py`)

```python
def test_pack1_output_unchanged(scenario_id, severity):
    """All 16 mandatory SimulateResponse fields match pre-Pack-3 values."""

def test_pack2_propagation_unchanged(scenario_id, severity):
    """propagation_chain, propagation_score identical to pre-Pack-3."""

def test_existing_decision_plan_preserved(scenario_id, severity):
    """decision_plan field is identical to pre-Pack-3 (Pack 3 does not overwrite)."""

def test_existing_explainability_preserved(scenario_id, severity):
    """explainability field is identical to pre-Pack-3."""

def test_pipeline_stages_count(scenario_id, severity):
    """pipeline_stages_completed = 21 (18 existing + 3 Pack 3)."""

def test_existing_api_endpoints_unchanged():
    """All 18+ existing endpoints return same shape."""
```

### 8.3 Performance Tests

```python
def test_pack3_latency_budget():
    """Pack 3 stages complete within 50ms total (p99)."""
    # Impact Engine: <15ms
    # Decision Brain: <20ms
    # Decision Bridge: <15ms
```

---

## 9. RISK REGISTER

| # | Failure Mode | Probability | Impact | Mitigation |
|---|-------------|-------------|--------|------------|
| R1 | Pack 3 increases pipeline latency beyond SLA | LOW | MEDIUM | Latency budget: 50ms total. Early-exit if no affected domains. Benchmark in CI. |
| R2 | Graph store unavailable at runtime | MEDIUM | LOW | Fallback path tested independently. `fallback_active=True` flag in output. |
| R3 | SHA-256 hash collision | NEGLIGIBLE | LOW | Use full SHA-256 (256-bit). Collision probability 2⁻¹²⁸ for birthday attack. |
| R4 | Impact assessment produces empty domains | LOW | HIGH | Validation rule: at least 1 domain (shock origin always affected). Contract test enforces. |
| R5 | Decision Brain re-ranking inverts correct priority | LOW | MEDIUM | Original action priority preserved at DB_W1=0.30 weight. A/B test against existing ranking. |
| R6 | New schemas break frontend deserialization | MEDIUM | HIGH | New fields are ADDITIVE (default to empty dict). Frontend ignores unknown keys. SimulateResponse backward-compat validator preserved. |
| R7 | Circular import with existing modules | LOW | MEDIUM | Pack 3 modules import from config.py and utils.py only. Never import from simulation_engine.py directly. |
| R8 | Audit hash generation fails on edge-case input | LOW | MEDIUM | Wrap in try/except. On failure, set hash to "ERROR:{reason}" and log. Never block pipeline. |
| R9 | PDPL compliance — impact assessment contains PII | LOW | HIGH | Impact assessment uses entity_id/entity_label from GCC_NODES (institutional, not personal). No PII in pipeline. |
| R10 | IFRS-17 audit trail gap | MEDIUM | HIGH | Decision Bridge generates immutable audit digest. SHA-256 hash chain links to run_id. Audit service records Pack 3 stage timings. |

---

## 10. OBSERVABILITY HOOKS

| Hook | Location | Type | Purpose |
|------|----------|------|---------|
| `stage_complete:impact_engine` | `run_orchestrator.py` | Structured log | Latency + domain count |
| `stage_complete:decision_brain` | `run_orchestrator.py` | Structured log | Latency + action count + fallback status |
| `stage_complete:decision_bridge` | `run_orchestrator.py` | Structured log | Latency + audit hash + graph status |
| `impact_assessment.composite_severity` | `impact_engine/engine.py` | Metric | Histogram of severity distribution |
| `decision_output.overall_urgency` | `decision_brain/brain.py` | Metric | Counter by urgency level |
| `decision_envelope.decision_ready` | `decision_bridge/bridge.py` | Metric | Boolean rate (should be ~100%) |
| `audit_digest.combined_hash` | `decision_bridge/audit_hasher.py` | Audit log | SHA-256 chain for IFRS-17 |
| `graph_annotation_status` | `decision_bridge/graph_annotator.py` | Metric | Success/skip/error rate |
| `pack3_total_ms` | `run_orchestrator.py` | Metric | P50/P95/P99 total Pack 3 latency |

---

## 11. DECISION GATE — What Must Be True Before Proceeding

### Gate 1: Schema Validation (before Step 3)
- [ ] All 9 new Pydantic models parse with default values
- [ ] `ImpactAssessment.model_validate({})` succeeds (safe defaults)
- [ ] `DecisionOutput.model_validate({})` succeeds (safe defaults)
- [ ] `DecisionEnvelope.model_validate({})` succeeds (safe defaults)

### Gate 2: Impact Engine (before Step 11)
- [ ] `compute_impact_assessment()` produces valid output for all 11 test scenarios
- [ ] At least 1 affected domain per scenario
- [ ] Composite severity monotonically increases with input severity
- [ ] Time horizon classification is consistent with peak_day

### Gate 3: Decision Brain (before Step 15)
- [ ] `compute_decision_output()` produces valid output for all 11 test scenarios
- [ ] Every RecommendedAction has ≥1 ReasoningStep
- [ ] Fallback path produces valid output when graph_store=None
- [ ] Action re-ranking preserves relative ordering for equal-weight scenarios

### Gate 4: Integration (before merge to main)
- [ ] All 113 existing contract tests pass (zero regression)
- [ ] All 27 existing API endpoint tests pass
- [ ] Pack 3 contract tests pass (new ~60 tests)
- [ ] Pack 3 regression tests pass (new ~20 tests)
- [ ] Total pipeline latency increase < 50ms (p99)
- [ ] `pipeline_stages_completed` = 21

---

## 12. FORMULAS

### Impact Engine — Composite Severity
```
CompositeSeverity = IE_W1 × URS + IE_W2 × EventSeverity + IE_W3 × PropagationScore + IE_W4 × PeakStectorStress
                  = 0.35 × URS + 0.25 × Es + 0.25 × PS + 0.15 × max(LSI, ISI)
```

### Impact Engine — Domain Exposure
```
DomainExposure_j = SectorExposure_j × (SectorLoss_j / TotalLoss)
```

### Decision Brain — Action Re-Ranking
```
ReRankScore = DB_W1 × OriginalPriority + DB_W2 × DomainSeverity + DB_W3 × NetBenefit_norm + DB_W4 × Confidence
            = 0.30 × P_orig + 0.30 × D_sev + 0.25 × NB_norm + 0.15 × Conf
```

Where:
- `DomainSeverity` = composite_severity of the domain this action addresses
- `NetBenefit_norm` = (loss_avoided - cost) / max(total_loss, 1)
- `Confidence` = pipeline confidence × domain coverage factor

### Decision Brain — Urgency Classification
```
UrgencyScore = 0.40 × (1 - time_to_act_hours/168) + 0.30 × composite_severity + 0.30 × regulatory_risk

IMMEDIATE: UrgencyScore ≥ 0.80
URGENT:    UrgencyScore ≥ 0.60
MONITOR:   UrgencyScore ≥ 0.35
WATCH:     UrgencyScore < 0.35
```

### Decision Brain — Action Type Classification
```
RiskScore = composite_severity × (1 - feasibility) × regulatory_risk

ESCALATE:  risk_level ∈ {HIGH, SEVERE} AND time_to_first_failure < 12h
MITIGATE:  RiskScore ≥ 0.65
HEDGE:     RiskScore ≥ 0.45
TRANSFER:  RiskScore ≥ 0.30
ACCEPT:    RiskScore ≥ 0.15
MONITOR:   RiskScore < 0.15
```
