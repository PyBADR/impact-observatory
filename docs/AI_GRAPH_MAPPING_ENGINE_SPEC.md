# AI-Driven Graph Mapping Engine — Architecture Specification

**محرك رسم الخرائط البيانية بالذكاء الاصطناعي — مواصفات البنية**

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Layer** | Models → Agents (Layer 3-4) |
| **Owner** | AI Graph Mapping Engine |
| **Files** | `ai_entity_extractor.py`, `hybrid_graph_mapper.py`, `graph_expansion_service.py` (updated), `graph_expansion.py` (updated), `core/config.py` (updated) |
| **Date** | 2026-04-09 |

---

## 1. Architecture Decision

The AI Graph Mapping Engine adds an LLM-driven entity extraction layer alongside the existing deterministic rule-based mapper. Rather than replacing the rule-based path, we built a **hybrid merge architecture** where:

- Rule-based mapping is the **deterministic baseline** (always runs, always trusted)
- AI extraction is an **augmentation layer** (opt-in, confidence-gated, quarantinable)
- A merge decision layer combines both outputs with per-entity deduplication and three-tier confidence gating

**Trade-off analysis:** We chose rule-priority merge over confidence-max merge because GCC enterprise clients require deterministic auditability. AI entities augment the graph with novel discoveries that the rule mapper cannot express, but they never override structurally correct rule-based entities. This makes the system safe to enable in production with human-in-the-loop governance.

---

## 2. Data Flow

```
MacroSignal (dict)
  │
  ├──────────────────────────┐
  ▼                          ▼
map_signal_to_graph()    AIEntityExtractor.extract()
  │ (deterministic)          │ (LLM-driven, confidence-scored)
  │ Returns MappingResult    │ Returns MappingResult
  ▼                          ▼
  └──────────┬───────────────┘
             ▼
    HybridGraphMapper._merge_results()
      │  Deduplication (node_id + label similarity)
      │  Confidence gating (standard / low_conf / quarantine)
      │  Capacity limits (max_ai_nodes_per_signal)
      │  Returns HybridMappingResult:
      │    mapping: MappingResult (merged)
      │    merge_stats: HybridMergeStats
      │    quarantined_nodes/edges: list[dict]
      │    audit_hash: SHA-256
      ▼
InMemoryGraphWriter / Neo4jGraphWriter
      ▼
GraphExpansionResult (API response)
```

---

## 3. Component Architecture

### 3.1 AI Entity Extractor (`ai_entity_extractor.py`)

Extracts entities and relationships from a MacroSignal using an LLM backend.

| Aspect | Detail |
|--------|--------|
| **Input** | MacroSignal dict |
| **Output** | `MappingResult` (same type as rule-based mapper) |
| **LLM Backend** | Pluggable via `LLMBackend` protocol (Ollama, Mock, OpenAI) |
| **Validation** | `AIExtractedEntity` / `AIExtractedRelationship` with `@field_validator` |
| **Fuzzy Mapping** | 15+ common LLM outputs mapped to `GraphEntityType` / `GraphRelationType` |
| **Provenance** | All AI nodes carry `source_type="ai_extractor"`, `ai_extracted=True` |
| **Node IDs** | Prefixed `ai_{type}:{slug}` to distinguish from rule-based |
| **Failure Mode** | Returns empty `MappingResult` with warnings (never crashes) |

### 3.2 Hybrid Graph Mapper (`hybrid_graph_mapper.py`)

Merges rule-based and AI results into a single pipeline output.

| Aspect | Detail |
|--------|--------|
| **Merge Strategy** | `AI_AUGMENT` (default): AI adds novel entities only |
| **Deduplication** | Two-pass: exact `node_id` match, then normalized label match |
| **Confidence Tiers** | STANDARD (≥0.70), LOW_CONFIDENCE (0.30-0.69), QUARANTINE (<0.30) |
| **Capacity Limit** | `max_ai_nodes_per_signal=25` (configurable) |
| **Quarantine** | Below-threshold entities logged in `quarantined_nodes` for audit |
| **Audit Hash** | SHA-256 of merge decision metadata (PDPL compliance) |
| **Edge Remapping** | AI edges whose endpoints were deduplicated get remapped to rule node IDs |

### 3.3 Configuration (`core/config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `ai_extraction_enabled` | `false` | Master switch for AI path |
| `ollama_base_url` | `http://localhost:11434` | Ollama API endpoint |
| `ollama_model` | `llama3.1:8b` | Model for extraction |
| `ollama_timeout_seconds` | `30` | Request timeout |
| `ollama_temperature` | `0.1` | Low = more deterministic |
| `ai_min_entity_confidence` | `0.50` | Below this → entity dropped |
| `ai_min_relationship_confidence` | `0.45` | Below this → relationship dropped |
| `ai_merge_standard_threshold` | `0.70` | ≥ this → promoted directly |
| `ai_merge_quarantine_threshold` | `0.30` | < this → quarantined |
| `ai_max_nodes_per_signal` | `25` | Capacity safety limit |
| `ai_use_mock_backend` | `false` | Use mock for testing/CI |

---

## 4. Confidence Gating — Three-Tier Model

```
AI Entity Confidence Score
         │
    ≥ 0.70 ───▶ STANDARD: promoted directly into merged result
         │
  0.30-0.69 ──▶ LOW_CONFIDENCE: promoted with quarantine_status="low_confidence"
         │                        + requires_review=true
    < 0.30 ───▶ QUARANTINE: NOT added to result, logged for audit
```

---

## 5. Merge Decision Observability

Every merge decision is logged as a `MappingDecision`:

```json
{
  "stage": "hybrid_merge",
  "action": "promote | skip | quarantine",
  "element_id": "ai_indicator:brent_crude",
  "reason": "AI entity promoted (standard): conf=0.90",
  "confidence": "high"
}
```

`HybridMergeStats` captures:
- `rule_nodes`, `rule_edges` — baseline counts
- `ai_nodes_total`, `ai_edges_total` — raw AI output counts  
- `ai_nodes_promoted`, `ai_nodes_deduplicated`, `ai_nodes_quarantined` — merge outcomes
- `rule_duration_ms`, `ai_duration_ms`, `merge_duration_ms` — per-phase timing
- `ai_available`, `ai_enabled` — runtime status

---

## 6. API Changes (Additive Only)

### Updated: `POST /api/v1/graph/expand`

Response now includes `hybrid_stats` and `ai_enabled` fields:

```json
{
  "signal_id": "abc",
  "mapping": { "nodes_mapped": 17, ... },
  "write": { "nodes_merged": 17, ... },
  "hybrid_stats": {
    "rule_nodes": 14,
    "ai_nodes_promoted": 3,
    "ai_nodes_quarantined": 0,
    "total_duration_ms": 45.2
  },
  "ai_enabled": true,
  "success": true
}
```

### Updated: `POST /api/v1/graph/expand/preview`

New query parameter: `?use_ai=true` enables hybrid preview.

### Updated: `GET /api/v1/graph/expand/stats`

Now includes `ai_enabled` and `ai_available` fields.

---

## 7. LLM Backend Protocol

```python
class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...
```

Implementations:
- `OllamaBackend` — HTTP client for local Ollama (Mac M4 Max GPU)
- `MockLLMBackend` — Deterministic mock for testing/CI
- Future: `OpenAIBackend`, `AnthropicBackend` for cloud LLM

---

## 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucinated entity types | Medium | Low | Fuzzy mapping + `@field_validator` rejects unknowns |
| LLM timeout/unavailability | Medium | None | Returns empty `MappingResult`, rule-based still runs |
| AI entity duplicates rule-based | High | Low | Two-pass dedup (node_id + label normalization) |
| AI floods graph with low-quality nodes | Low | Medium | Capacity limit + quarantine gating |
| Model drift degrades extraction quality | Medium | Medium | `ai_confidence` tracked per-entity, alertable via stats |
| Config change enables AI in production accidentally | Low | High | `ai_extraction_enabled=false` default + env var override |

---

## 9. Files Delivered

| File | Purpose |
|------|---------|
| `backend/src/graph_brain/ai_entity_extractor.py` | LLM-driven entity/relationship extraction |
| `backend/src/graph_brain/hybrid_graph_mapper.py` | Hybrid merge: AI + rule-based with confidence gating |
| `backend/src/graph_brain/graph_expansion_service.py` | Updated: wires hybrid mapper from config |
| `backend/src/api/v1/graph_expansion.py` | Updated: `?use_ai=true` preview, hybrid stats in response |
| `backend/src/core/config.py` | Updated: 13 new AI/Ollama settings |
| `backend/tests/test_hybrid_graph_mapper.py` | 11 end-to-end validation tests |
| `docs/AI_GRAPH_MAPPING_ENGINE_SPEC.md` | This document |

---

## 10. Decision Gate — What Must Be True Before Next Phase

- [ ] All 11 hybrid mapper tests pass (✅ validated)
- [ ] Existing contract tests unaffected (no imports changed)
- [ ] `AI_EXTRACTION_ENABLED=false` in all environments until explicit promotion
- [ ] Ollama available on Mac M4 Max with `llama3.1:8b` model pulled
- [ ] Neo4j MERGE writer tested with AI-prefixed node IDs
- [ ] Human-in-the-loop review of quarantined entities workflow defined
- [ ] Monitoring dashboard for `ai_nodes_promoted` / `ai_nodes_quarantined` ratio

**Next Phase:** LangGraph agent orchestration — the AI extractor becomes a tool callable by the Vercept (Vy) agent within the SCP methodology execution loop.

---

*Document generated for Deevo Analytics — Impact Observatory | مرصد الأثر*
