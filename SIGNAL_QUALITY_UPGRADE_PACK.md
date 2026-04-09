# Signal Quality Upgrade Pack — Architectural Plan

**Layer**: Signal Intelligence Layer (pre-Pack 1)
**Scope**: Classification, Region Detection, Domain Mapping, Severity Scoring
**Constraints**: No LLM, no UI, no external systems, deterministic only, zero regression

---

## 1. DEFICIENCY ANALYSIS

### 1.1 Classification (Signal Type + Source)

| Deficiency | Location | Impact |
|---|---|---|
| RSS adapter provides **zero** `signal_type_hint` — all RSS signals enter Pack 1 with `signal_type=None` | `rss_adapter.py` L97–117 | Pack 1 normalization must guess signal type; downstream routing is degraded |
| JSON API adapter provides **zero** `signal_type_hint` | `json_api_adapter.py` L165–179 | Same: no classification for JSON-sourced signals |
| Feed type → `SignalSource` is coarse: ALL RSS → `GEOPOLITICAL`, ALL JSON_API → `MARKET` | `mapper.py` L153–157 | A banking RSS feed is misclassified as geopolitical; a geopolitical JSON API is misclassified as market |
| RSS categories (e.g., `["Energy", "GCC"]`) are collected but **never used** for classification | `rss_adapter.py` L107–110, `mapper.py` L243 | Categories are carried as tags only — wasted classification signal |

### 1.2 Region Detection

| Deficiency | Location | Impact |
|---|---|---|
| RSS adapter copies only feed-level `default_regions` — **no per-item extraction** from title/description | `rss_adapter.py` L114 | Every item from the same RSS feed gets identical region, regardless of content |
| JSON API extracts a single `region` field but does **no content scanning** | `json_api_adapter.py` L151–155 | Signals without an explicit region field get only the feed default |
| City-to-region mapping is minimal: only Dubai, Abu Dhabi, Doha, Muscat | `mapper.py` L60–68 | Riyadh, Jeddah, Dammam, Sharjah, Salalah, Manama — all miss |
| Arabic aliases are incomplete — missing المملكة, دبي, أبوظبي, الدوحة, المنامة, مسقط | `mapper.py` L70–82 | Arabic-language feed items get GCC_WIDE fallback instead of correct country |
| `_resolve_regions` lowercases hint then does dict lookup — but ISO codes `"SA"` are stored both as `"SA"` and `"sa"` (redundant entries) while real matching only needs case-insensitive | `mapper.py` L86–100 | Minor: works but wastes dict space and is fragile if new codes added with wrong case |

### 1.3 Domain Mapping

| Deficiency | Location | Impact |
|---|---|---|
| RSS adapter copies only feed-level `default_domains` — **no per-item inference** | `rss_adapter.py` L115 | Every RSS item gets same domains regardless of content |
| RSS `categories` (e.g., `["Energy", "Banking"]`) are **never** resolved to `ImpactDomain` | `mapper.py` L243 | Structured categorization data is discarded |
| Domain alias dictionary is limited — missing: petroleum, crude, forex, bonds, ports, airports, reinsurance, fintech, construction, hospitality, tourism, water, desalination | `mapper.py` L105–133 | Common GCC industry terms fail to resolve → empty domain list |
| No keyword-based domain inference from title or description | `mapper.py` (absent) | A signal titled "Port of Jebel Ali container throughput drops 40%" gets zero domain resolution unless the feed config specifies it |

### 1.4 Severity Scoring

| Deficiency | Location | Impact |
|---|---|---|
| Default severity `0.3` for all non-economic signals — flat guess with zero signal analysis | `mapper.py` L218 | A signal about a full port closure gets the same 0.3 severity as a minor policy update |
| `source_quality` from FeedConfig is **never used** in severity computation | `mapper.py` L215–218 | A verified Reuters feed and an unknown blog get identical severity treatment |
| `confidence` is **never weighted** into severity | `mapper.py` L226–228 | VERIFIED and UNVERIFIED signals produce the same downstream severity weight |
| Economic adapter has good threshold-based scoring, but RSS and JSON API adapters have **none** — severity is either whatever the API provides or `None` | `rss_adapter.py`, `json_api_adapter.py` | Non-economic signals are systematically under- or over-scored |
| No keyword-based severity boosting from title content (e.g., "crisis", "collapse", "shutdown") | `mapper.py` (absent) | Critical signals without a numeric severity hint default to 0.3 |

---

## 2. UPGRADE ARCHITECTURE

### 2.1 New Module: `signal_intel/enrichment.py`

A **pure-function enrichment module** that sits between adapters and the mapper. No new pipeline stage — it enhances `RawFeedItem` fields in-place before mapping.

```
Adapter.parse_items() → enrich_feed_item(item) → map_feed_item(item) → MacroSignalInput
```

The enrichment module contains four deterministic sub-functions:

1. `classify_signal_type(title, description, categories, feed_type) → str | None`
2. `extract_regions(title, description, existing_hints) → list[str]`
3. `extract_domains(title, description, categories, existing_hints) → list[str]`
4. `compute_severity(title, description, source_quality, confidence, existing_hint) → float`

**Architecture Decision**: Enrichment runs as pure functions called by the mapper — NOT as a new pipeline stage. This preserves the existing orchestrator contract (fetch → dedup → map → buffer → route) and avoids breaking the `IngestionStatus` enum.

**Trade-off**: Embedding enrichment in the mapper keeps the pipeline topology unchanged but increases mapper complexity. Alternative was a new pipeline stage, rejected because it would require `IngestionStatus` enum changes (breaking Pack 2/3 contracts).

### 2.2 Expanded Dictionaries: `signal_intel/dictionaries.py`

A new module containing all keyword/alias dictionaries, extracted from `mapper.py` and expanded:

- `REGION_ALIASES` — expanded from 30 → 80+ entries (cities, Arabic variants, transliterations)
- `DOMAIN_ALIASES` — expanded from 25 → 60+ entries (GCC industry terms, Arabic, synonyms)
- `SIGNAL_TYPE_KEYWORDS` — NEW: title/description keyword → SignalType mapping
- `SEVERITY_KEYWORDS` — NEW: title/description keyword → severity modifier
- `SOURCE_CLASSIFICATION_RULES` — NEW: category + keyword → SignalSource override

**Architecture Decision**: Separate module for dictionaries because they are configuration-grade data that changes more frequently than logic. Mapper imports from dictionaries; dictionaries import nothing from mapper.

---

## 3. FILES TO CREATE

| File | Purpose | Layer |
|---|---|---|
| `backend/src/signal_intel/enrichment.py` | Pure-function enrichment logic (classify, extract, score) | Signal Intelligence |
| `backend/src/signal_intel/dictionaries.py` | All keyword/alias dictionaries (extracted + expanded) | Signal Intelligence |
| `backend/tests/test_signal_enrichment.py` | Unit tests for all enrichment functions | Test |

## 4. FILES TO MODIFY

| File | Change | Risk |
|---|---|---|
| `backend/src/signal_intel/mapper.py` | Import enrichment functions; call `enrich_feed_item()` before mapping; replace inline `_REGION_ALIASES` / `_DOMAIN_ALIASES` with imports from `dictionaries.py` | **LOW** — mapper output contract (`MacroSignalInput`) unchanged |
| `backend/src/signal_intel/adapters/rss_adapter.py` | Extract RSS `<category>` tags into `domain_hints` and `signal_type_hint` (currently only into `payload.categories`) | **LOW** — only adds hints; existing fields unchanged |
| `backend/src/signal_intel/adapters/json_api_adapter.py` | Add `signal_type` to `DEFAULT_FIELD_MAP`; extract `signal_type_hint` from mapped data | **LOW** — additive field extraction |
| `backend/tests/test_signal_intel.py` | Add enrichment-aware assertions to existing mapper tests; verify backward compatibility | **LOW** — additive test cases |

## 5. FILES NOT TOUCHED (contract preservation)

| File | Reason |
|---|---|
| `backend/src/macro/macro_schemas.py` | MacroSignalInput contract is unchanged — enrichment only improves the quality of values mapped into existing fields |
| `backend/src/macro/macro_enums.py` | No new enum values needed — all improvements use existing enum members |
| `backend/src/macro/macro_normalizer.py` | Normalizer contract unchanged — receives same MacroSignalInput shape |
| `backend/src/macro/macro_signal_service.py` | Pack 1 intake unchanged |
| `backend/src/signal_intel/orchestrator.py` | Pipeline topology unchanged — enrichment is embedded in mapper |
| `backend/src/signal_intel/router.py` | Router contract unchanged |
| `backend/src/signal_intel/types.py` | RawFeedItem model unchanged — enrichment writes to existing optional fields |
| `backend/src/signal_intel/dedup.py` | Dedup logic unchanged |
| `backend/src/config.py` | No new simulation weights — enrichment weights are signal-intel-internal |

---

## 6. LOGIC IMPROVEMENTS (Detailed)

### 6.1 Signal Type Classification (`enrichment.py::classify_signal_type`)

**Input**: `title: str, description: str | None, categories: list[str], feed_type: FeedType`
**Output**: `str | None` (signal type hint string)

**Algorithm** (priority-ordered):
1. If adapter already set `signal_type_hint` → pass through (no override)
2. Scan `categories` against `SIGNAL_TYPE_KEYWORDS` dict → first match wins
3. Scan title tokens (lowercased, split on whitespace + punctuation) against `SIGNAL_TYPE_KEYWORDS` → highest-priority match wins
4. If feed_type == ECONOMIC → default "market"
5. Return None if no match

**Keyword dictionary (excerpt)**:
```python
SIGNAL_TYPE_KEYWORDS: dict[str, tuple[str, int]] = {
    # keyword → (signal_type, priority)  — higher priority wins on conflict
    "war": ("geopolitical", 10),
    "conflict": ("geopolitical", 10),
    "sanctions": ("geopolitical", 9),
    "military": ("geopolitical", 9),
    "tensions": ("geopolitical", 8),
    "diplomacy": ("geopolitical", 7),
    "embargo": ("geopolitical", 9),
    "missile": ("geopolitical", 10),
    "policy": ("policy", 8),
    "regulation": ("regulatory", 8),
    "compliance": ("regulatory", 7),
    "legislation": ("regulatory", 8),
    "central bank": ("policy", 9),
    "interest rate": ("policy", 9),
    "fiscal": ("policy", 8),
    "monetary": ("policy", 8),
    "crude": ("commodity", 9),
    "brent": ("commodity", 9),
    "opec": ("commodity", 9),
    "lng": ("commodity", 8),
    "oil price": ("commodity", 9),
    "commodity": ("commodity", 8),
    "stock": ("market", 7),
    "equity": ("market", 7),
    "bond": ("market", 7),
    "yield": ("market", 7),
    "ipo": ("market", 8),
    "market": ("market", 6),
    "shipping": ("logistics", 8),
    "port": ("logistics", 8),
    "supply chain": ("logistics", 9),
    "freight": ("logistics", 8),
    "container": ("logistics", 7),
    "pipeline": ("logistics", 7),
    "sentiment": ("sentiment", 7),
    "confidence": ("sentiment", 6),
    "outlook": ("sentiment", 6),
    "systemic": ("systemic", 9),
    "contagion": ("systemic", 9),
    "cascade": ("systemic", 8),
}
```

**Determinism guarantee**: Keyword list is static; priority-based resolution is deterministic (same input → same output). No ML, no randomness.

### 6.2 Region Extraction (`enrichment.py::extract_regions`)

**Input**: `title: str, description: str | None, existing_hints: list[str]`
**Output**: `list[str]` (enriched region hints — superset of existing)

**Algorithm**:
1. Start with `existing_hints` as baseline
2. Build a search corpus = `title.lower()` + ` ` + `(description or "").lower()`
3. For each entry in `REGION_SCAN_PHRASES` (ordered longest-first to avoid partial matches):
   - If phrase found in corpus → add corresponding region code to hints
4. Deduplicate and return

**Expanded REGION_SCAN_PHRASES (excerpt)**:
```python
REGION_SCAN_PHRASES: list[tuple[str, str]] = [
    # (phrase_lowercase, region_code)
    # Saudi Arabia — cities and variants
    ("saudi arabia", "SA"), ("kingdom of saudi arabia", "SA"),
    ("riyadh", "SA"), ("jeddah", "SA"), ("jidda", "SA"),
    ("dammam", "SA"), ("dhahran", "SA"), ("jubail", "SA"),
    ("yanbu", "SA"), ("mecca", "SA"), ("medina", "SA"),
    ("neom", "SA"), ("aramco", "SA"), ("sabic", "SA"),
    ("المملكة العربية السعودية", "SA"), ("الرياض", "SA"),
    ("جدة", "SA"), ("الدمام", "SA"), ("مكة", "SA"), ("المدينة", "SA"),
    # UAE — cities and variants
    ("united arab emirates", "AE"), ("abu dhabi", "AE"),
    ("dubai", "AE"), ("sharjah", "AE"), ("ajman", "AE"),
    ("ras al khaimah", "AE"), ("fujairah", "AE"),
    ("jebel ali", "AE"), ("adnoc", "AE"),
    ("دبي", "AE"), ("أبوظبي", "AE"), ("الشارقة", "AE"),
    # Qatar
    ("qatar", "QA"), ("doha", "QA"), ("lusail", "QA"),
    ("ras laffan", "QA"), ("qatargas", "QA"),
    ("الدوحة", "QA"), ("لوسيل", "QA"),
    # Kuwait
    ("kuwait", "KW"), ("kuwait city", "KW"),
    ("مدينة الكويت", "KW"),
    # Bahrain
    ("bahrain", "BH"), ("manama", "BH"),
    ("المنامة", "BH"),
    # Oman
    ("oman", "OM"), ("muscat", "OM"), ("salalah", "OM"),
    ("sohar", "OM"), ("duqm", "OM"),
    ("صلالة", "OM"), ("صحار", "OM"),
    # GCC-wide
    ("gcc", "GCC"), ("gulf cooperation council", "GCC"),
    ("hormuz", "GCC"), ("strait of hormuz", "GCC"),
    ("persian gulf", "GCC"), ("arabian gulf", "GCC"),
    ("مجلس التعاون", "GCC"), ("الخليج العربي", "GCC"),
]
```

**Longest-first ordering** prevents "oman" from matching inside "oman port" before "oman" is checked — and prevents "dubai" from matching before "abu dhabi" in "abu dhabi" strings (not an issue here, but the pattern prevents future bugs with overlapping names).

### 6.3 Domain Extraction (`enrichment.py::extract_domains`)

**Input**: `title: str, description: str | None, categories: list[str], existing_hints: list[str]`
**Output**: `list[str]` (enriched domain hints)

**Algorithm**:
1. Start with `existing_hints`
2. Resolve RSS/JSON `categories` against `DOMAIN_ALIASES` → add matched domains
3. Scan title+description corpus against `DOMAIN_SCAN_KEYWORDS` → add matched domains
4. Deduplicate and return

**Expanded DOMAIN_ALIASES (added entries)**:
```python
# Oil & Gas expansions
"petroleum": "oil_gas", "crude": "oil_gas", "brent": "oil_gas",
"wti": "oil_gas", "opec": "oil_gas", "lng": "oil_gas",
"natural gas": "oil_gas", "refinery": "oil_gas", "upstream": "oil_gas",
"downstream": "oil_gas", "aramco": "oil_gas", "adnoc": "oil_gas",

# Banking expansions
"bank": "banking", "lending": "banking", "credit": "banking",
"mortgage": "banking", "deposits": "banking", "central bank": "banking",

# Insurance expansions
"reinsurance": "insurance", "underwriting": "insurance",
"claims": "insurance", "premium": "insurance", "actuarial": "insurance",

# Trade & Logistics expansions
"port": "trade_logistics", "freight": "trade_logistics",
"container": "trade_logistics", "customs": "trade_logistics",
"supply chain": "trade_logistics", "warehouse": "trade_logistics",
"export": "trade_logistics", "import": "trade_logistics",

# Sovereign/Fiscal expansions
"budget": "sovereign_fiscal", "debt": "sovereign_fiscal",
"bond": "sovereign_fiscal", "treasury": "sovereign_fiscal",
"gdp": "sovereign_fiscal", "deficit": "sovereign_fiscal",

# Real Estate expansions
"construction": "real_estate", "housing": "real_estate",
"residential": "real_estate", "commercial property": "real_estate",

# Aviation expansions
"airport": "aviation", "airline": "aviation", "flight": "aviation",

# Maritime expansions
"shipping": "maritime", "vessel": "maritime", "tanker": "maritime",
"shipyard": "maritime", "fleet": "maritime",

# Capital Markets expansions
"equity": "capital_markets", "ipo": "capital_markets",
"exchange": "capital_markets", "tadawul": "capital_markets",
"dfm": "capital_markets", "adx": "capital_markets",
"forex": "capital_markets", "yield": "capital_markets",

# Cyber expansions
"cybersecurity": "cyber_infrastructure", "data breach": "cyber_infrastructure",
"ransomware": "cyber_infrastructure", "network": "cyber_infrastructure",

# Telecom expansions
"5g": "telecommunications", "broadband": "telecommunications",
"mobile": "telecommunications", "stc": "telecommunications",
"etisalat": "telecommunications", "du": "telecommunications",

# Energy Grid expansions
"power": "energy_grid", "electricity": "energy_grid",
"solar": "energy_grid", "renewable": "energy_grid",
"desalination": "energy_grid", "water": "energy_grid",
```

### 6.4 Severity Scoring (`enrichment.py::compute_severity`)

**Input**: `title: str, description: str | None, source_quality: float, confidence: str, existing_hint: float | None`
**Output**: `float` (severity score in [0.0, 1.0])

**Algorithm**:
1. **Base score**: If `existing_hint` is provided and > 0 → use it. Else → 0.3 (current default).
2. **Keyword modifier**: Scan title against `SEVERITY_KEYWORDS` → collect max modifier.
3. **Source quality weight**: `quality_factor = 0.7 + 0.3 * source_quality` (range 0.7–1.0; high-quality sources get full weight, low-quality get 30% discount).
4. **Confidence weight**: Map confidence level to multiplier:
   - verified → 1.0
   - high → 0.95
   - moderate → 0.85
   - low → 0.70
   - unverified → 0.60
5. **Final score**: `clamp(base_score * keyword_modifier * quality_factor * confidence_weight, 0.0, 1.0)`

**SEVERITY_KEYWORDS dictionary (excerpt)**:
```python
SEVERITY_KEYWORDS: dict[str, float] = {
    # keyword → multiplier applied to base severity
    # Crisis-level (amplify significantly)
    "war": 2.5, "invasion": 2.5, "collapse": 2.2,
    "crisis": 2.0, "shutdown": 2.0, "closure": 1.9,
    "blockade": 2.0, "default": 2.0, "bankruptcy": 2.0,
    "explosion": 2.0, "attack": 1.9, "catastrophe": 2.2,

    # High severity (moderate amplification)
    "surge": 1.6, "plunge": 1.6, "crash": 1.8,
    "disruption": 1.5, "suspension": 1.5, "embargo": 1.7,
    "sanctions": 1.6, "escalation": 1.6, "emergency": 1.7,
    "downgrade": 1.5, "recession": 1.7, "inflation": 1.4,

    # Moderate severity
    "decline": 1.3, "drop": 1.3, "fall": 1.2,
    "cut": 1.2, "reduce": 1.1, "risk": 1.2,
    "concern": 1.1, "warning": 1.3, "tension": 1.3,

    # Positive / stabilizing (dampen toward nominal)
    "recovery": 0.7, "growth": 0.7, "stable": 0.6,
    "improvement": 0.7, "record high": 0.8, "upgrade": 0.7,
    "agreement": 0.6, "peace": 0.5, "cooperation": 0.6,
}
```

**Design invariant**: The formula can only move severity within [0.0, 1.0]. The `clamp()` ensures no overflow. The multiplicative design means a "recovery" keyword on an already-low 0.3 base produces ~0.13 (nominal), while a "crisis" keyword on the same base produces ~0.6 (elevated) — matching intuitive expectations.

### 6.5 Source Classification Override

**Current problem**: `_FEED_TYPE_TO_SOURCE` maps ALL RSS → GEOPOLITICAL, ALL JSON_API → MARKET.

**Fix in mapper.py**: After enrichment, if `signal_type_hint` resolves to a known type, override `SignalSource` using a `SIGNAL_TYPE_TO_SOURCE` mapping:

```python
SIGNAL_TYPE_TO_SOURCE: dict[str, SignalSource] = {
    "geopolitical": SignalSource.GEOPOLITICAL,
    "policy": SignalSource.REGULATORY,
    "market": SignalSource.MARKET,
    "commodity": SignalSource.ENERGY,
    "regulatory": SignalSource.REGULATORY,
    "logistics": SignalSource.TRADE,
    "sentiment": SignalSource.MARKET,
    "systemic": SignalSource.GEOPOLITICAL,
}
```

This replaces the blunt feed-type-based assignment with a content-aware classification while keeping feed-type as fallback when no signal type is resolved.

---

## 7. IMPLEMENTATION SEQUENCE

| Step | Action | Owner | Depends On |
|---|---|---|---|
| 1 | Create `dictionaries.py` with all expanded alias/keyword dictionaries | Signal Intel | — |
| 2 | Create `enrichment.py` with four pure functions + unit test stubs | Signal Intel | Step 1 |
| 3 | Write `test_signal_enrichment.py` — full unit coverage for all four functions | Test | Step 2 |
| 4 | Run enrichment tests → green | Test | Step 3 |
| 5 | Modify `mapper.py`: import from `dictionaries.py`, call enrichment before mapping, add source override logic | Signal Intel | Step 4 |
| 6 | Modify `rss_adapter.py`: propagate categories into `domain_hints` and `signal_type_hint` | Signal Intel | Step 5 |
| 7 | Modify `json_api_adapter.py`: add `signal_type` to field map | Signal Intel | Step 5 |
| 8 | Run existing `test_signal_intel.py` → verify zero regression | Test | Step 5–7 |
| 9 | Add enrichment-aware assertions to `test_signal_intel.py` | Test | Step 8 |
| 10 | Run full backend test suite (`pytest tests/ -v`) → verify zero regression across Pack 1, Pack 2, Pack 3 | Test | Step 9 |

---

## 8. RISK REGISTER

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Keyword matching produces false-positive region (e.g., "Oman" inside "Ottoman") | LOW | Moderate — wrong region assignment | Use phrase-boundary matching (word boundaries via `\b` regex or whole-word check); longest-first ordering |
| Severity keyword amplification pushes signals to SEVERE that shouldn't be | MODERATE | Moderate — over-scoring causes alert fatigue | Cap multiplier at 2.5; clamp final score; add test cases with boundary-value coverage |
| New dictionary entries cause existing test assertions to fail | LOW | Low — test maintenance | All new tests are additive; existing tests assert minimum quality (e.g., `assert GCCRegion.GCC_WIDE in regions`) which will still pass with more-specific regions added |
| Mapper performance degrades with large keyword scans | LOW | Low — mapper runs per-item, not in hot loop | Dictionaries are O(k) scan where k ≈ 80 keywords; RSS/JSON feeds rarely exceed 100 items per poll. Sub-millisecond. |
| RSS categories contain unexpected strings that match domain aliases incorrectly | LOW | Low — additive domains don't break Pack 1 (it has its own SOURCE_DOMAIN_MAP fallback) | Log category resolution for observability; domain hints are additive, not exclusive |

---

## 9. OBSERVABILITY HOOKS

| Hook | Location | Type |
|---|---|---|
| `signal_intel.enrichment.classify` | `enrichment.py::classify_signal_type` | DEBUG log: input title snippet + resolved type |
| `signal_intel.enrichment.region` | `enrichment.py::extract_regions` | DEBUG log: added regions count, specific additions |
| `signal_intel.enrichment.domain` | `enrichment.py::extract_domains` | DEBUG log: added domains count |
| `signal_intel.enrichment.severity` | `enrichment.py::compute_severity` | DEBUG log: base → keyword_mod → quality_factor → confidence_weight → final |
| `signal_intel.mapper.source_override` | `mapper.py::_do_map` | INFO log: when source is overridden from feed-type default |

All logs use structured format: `logger.debug("enrichment.severity feed=%s base=%.2f keyword=%.2f quality=%.2f conf=%.2f final=%.2f", ...)` for grep/filter compatibility.

---

## 10. TEST STRATEGY

### 10.1 New Tests (`test_signal_enrichment.py`)

**Classification tests (15+ cases)**:
- Title with "sanctions" → GEOPOLITICAL
- Title with "interest rate" → POLICY
- Title with "crude" → COMMODITY
- Title with "port closure" → LOGISTICS
- Title with no keywords → None
- Category ["Energy"] → COMMODITY
- Category priority over title keyword when both present
- Feed type ECONOMIC fallback → "market"
- Existing signal_type_hint is never overridden

**Region extraction tests (20+ cases)**:
- Title "Riyadh stock exchange" → SA extracted
- Title "Jebel Ali port" → AE extracted
- Title "Ras Laffan LNG" → QA extracted
- Title "Salalah port closure" → OM extracted
- Arabic title "الرياض" → SA extracted
- Multiple regions in single title → all extracted
- No GCC region mentioned → existing hints preserved (no spurious additions)
- Word boundary: "Ottoman" does NOT match "Oman"
- Word boundary: "Romania" does NOT match "Oman"

**Domain extraction tests (15+ cases)**:
- Title "crude oil prices surge" → oil_gas
- Title "central bank rate decision" → banking
- Title "airport delays" → aviation
- Categories ["Energy", "Trading"] → oil_gas, trade_logistics
- Multiple domains from single title
- Unknown category → no domain added (not crash)

**Severity scoring tests (20+ cases)**:
- Base 0.3 + "crisis" keyword → elevated range (>0.50)
- Base 0.3 + "recovery" keyword → nominal range (<0.20)
- High source_quality (0.9) vs low (0.3) → measurable difference
- Verified confidence vs unverified → measurable difference
- Existing hint 0.8 + "crisis" → clamped at 1.0
- Existing hint 0.8 + "recovery" → reduced but still meaningful
- No keywords → base × quality × confidence (no amplification)
- All outputs in [0.0, 1.0] — boundary value analysis

### 10.2 Regression Tests (existing suite)

| Test File | Expected Result |
|---|---|
| `test_signal_intel.py` (75+ tests) | ALL PASS — output contract unchanged |
| `test_signal_adapters.py` | ALL PASS — adapter parse output structure unchanged |
| `test_signal_dedup.py` | ALL PASS — dedup logic untouched |
| `test_signal_router.py` | ALL PASS — router logic untouched |
| `test_macro_contracts.py` | ALL PASS — MacroSignalInput schema unchanged |
| `test_macro_models.py` | ALL PASS — no enum changes |
| `test_macro_normalizer.py` | ALL PASS — normalizer receives same shape |
| `test_pipeline_contracts.py` | ALL PASS — simulation pipeline untouched |
| `test_pack3_contracts.py` | ALL PASS — downstream untouched |

### 10.3 Integration Smoke Test

End-to-end test with mock RSS + JSON + Economic data → verify:
1. Enriched signals have non-None signal_type more often than before
2. Region specificity improved (fewer GCC_WIDE fallbacks)
3. Domain coverage improved (fewer empty domain lists)
4. Severity distribution more varied (not clustered at 0.3)

---

## 11. DECISION GATE

**What must be true before proceeding to implementation:**

- [ ] All four enrichment functions have complete unit test coverage (>95%)
- [ ] Existing `test_signal_intel.py` passes with zero modification to assertions
- [ ] Full `pytest tests/ -v` green with zero regressions
- [ ] No new dependencies added (stdlib + existing Pydantic only)
- [ ] `MacroSignalInput` schema fingerprint unchanged (Pydantic model_json_schema hash)
- [ ] Severity scoring produces scores in [0.0, 1.0] for ALL test vectors
- [ ] Region extraction produces zero false positives on the "Ottoman/Romania/Oman" boundary suite
- [ ] Performance: enrichment adds <1ms per signal on average (benchmark with 1000-item synthetic feed)

---

## 12. DATA FLOW DIAGRAM

```
┌─────────────┐
│  RSS Feed   │──→ RSSFeedAdapter.parse_items()
└─────────────┘         │
                        ▼
┌─────────────┐   ┌──────────────┐
│  JSON API   │──→│ JSONAPIAdapter│──→ RawFeedItem (with categories, hints)
└─────────────┘   └──────────────┘         │
                                           ▼
┌─────────────┐   ┌───────────────┐  ┌──────────────────────────────────┐
│ Economic API│──→│EconomicAdapter│  │ enrichment.py (NEW)              │
└─────────────┘   └───────────────┘  │  ├─ classify_signal_type()       │
                        │            │  ├─ extract_regions()             │
                        ▼            │  ├─ extract_domains()             │
                  ┌──────────┐       │  └─ compute_severity()            │
                  │ DedupEngine│     └──────────────────────────────────┘
                  └──────────┘                    │
                        │                         ▼
                        ▼              ┌────────────────────┐
                  ┌──────────┐         │ mapper.py (MODIFIED)│
                  │map_feed_ │◄────────│  calls enrich()     │
                  │  item()  │         │  then maps to        │
                  └──────────┘         │  MacroSignalInput    │
                        │              └────────────────────┘
                        ▼
                  MacroSignalInput ──→ Pack 1 intake (UNCHANGED)
                                  ──→ Graph Brain (UNCHANGED)
```

---

*Generated: 2026-04-08 | Architecture Layer: Signal Intelligence | Pack: Signal Quality Upgrade*
