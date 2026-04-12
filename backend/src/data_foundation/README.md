# P1 Data Foundation | أساس البيانات — المرحلة الأولى

Production-grade data layer for the Impact Observatory (مرصد الأثر) GCC macro intelligence platform.

## Architecture Position

```
Layer 1: DATA (this package)
  ↓
Layer 2: Features → Feature Store, Knowledge Graph
  ↓
Layer 3: Models → Risk Models, Simulation Engine
  ↓
Layer 4: Agents → Decision Brain, Alert System
  ↓
Layer 5: APIs → FastAPI Routes
  ↓
Layer 6: UI → Next.js Dashboard
  ↓
Layer 7: Governance → Audit Trail, Compliance
```

## Package Structure

```
data_foundation/
├── __init__.py                 # Package root (version: 1.0.0)
├── README.md                   # This file
├── schemas/                    # Pydantic models for all P1 datasets
│   ├── __init__.py             # Re-exports all schemas
│   ├── enums.py                # Shared enumerations (GCCCountry, Sector, etc.)
│   ├── base.py                 # FoundationModel base class
│   ├── dataset_registry.py     # A: Dataset catalog
│   ├── source_registry.py      # B: Source catalog
│   ├── entity_registry.py      # C: Entity master data
│   ├── macro_indicators.py     # D: GDP, CPI, unemployment, fiscal
│   ├── interest_rate_signals.py # E: Policy rates, interbank, yield curve
│   ├── oil_energy_signals.py   # F: Crude, OPEC, LNG, production
│   ├── fx_signals.py           # G: FX rates, peg deviation
│   ├── cbk_indicators.py       # H: Kuwait CBK monetary/banking
│   ├── event_signals.py        # I: Geopolitical/economic events
│   ├── banking_sector_profiles.py # J: Bank financial profiles
│   ├── insurance_sector_profiles.py # K: Insurer profiles + IFRS 17
│   ├── logistics_nodes.py      # L: Ports, airports, logistics hubs
│   ├── decision_rules.py       # M: Configurable decision rules
│   └── decision_logs.py        # N: Immutable decision audit log
├── seed/                       # JSON seed files with realistic GCC data
│   ├── dataset_registry_seed.json
│   ├── source_registry_seed.json
│   ├── entity_registry_seed.json
│   ├── macro_indicators_seed.json
│   ├── interest_rate_signals_seed.json
│   ├── oil_energy_signals_seed.json
│   ├── fx_signals_seed.json
│   ├── cbk_indicators_seed.json
│   ├── event_signals_seed.json
│   ├── banking_profiles_seed.json
│   ├── insurance_profiles_seed.json
│   ├── logistics_nodes_seed.json
│   └── decision_rules_seed.json
├── ingestion/                  # Ingestion contracts
│   ├── __init__.py
│   └── contracts.py            # Declarative ingestion contracts per dataset
├── validation/                 # Validation framework
│   ├── __init__.py
│   └── validators.py           # Quality gate evaluation engine
└── metadata/                   # Loaders and catalog utilities
    ├── __init__.py
    └── loader.py               # Seed data loader with validation
```

## 14 P1 Datasets

| ID | Dataset | Schema | Records | Refresh |
|----|---------|--------|---------|---------|
| A | Dataset Registry | DatasetRegistryEntry | ~14 | Static |
| B | Source Registry | SourceRegistryEntry | ~11 | Static |
| C | Entity Registry | EntityRegistryEntry | ~500 | On-demand |
| D | Macro Indicators | MacroIndicatorRecord | ~5,000 | Monthly |
| E | Interest Rate Signals | InterestRateSignal | ~10,000 | Daily |
| F | Oil & Energy Signals | OilEnergySignal | ~20,000 | Daily |
| G | FX Signals | FXSignal | ~15,000 | Daily |
| H | Kuwait CBK Indicators | CBKIndicatorRecord | ~3,000 | Monthly |
| I | Event Signals | EventSignal | ~50,000 | Near-RT |
| J | Banking Sector Profiles | BankingSectorProfile | ~2,000 | Quarterly |
| K | Insurance Sector Profiles | InsuranceSectorProfile | ~1,500 | Quarterly |
| L | Logistics Nodes | LogisticsNode | ~200 | Monthly |
| M | Decision Rules | DecisionRule | ~200 | On-demand |
| N | Decision Logs | DecisionLogEntry | ~100,000 | Real-time |

## Usage

```python
# Import schemas
from src.data_foundation.schemas import EntityRegistryEntry, MacroIndicatorRecord

# Load seed data
from src.data_foundation.metadata.loader import load_seed_data
entities = load_seed_data("entity_registry", EntityRegistryEntry)

# Validate a record
from src.data_foundation.validation import validate_record
from src.data_foundation.ingestion.contracts import P1_INGESTION_CONTRACTS
contract = next(c for c in P1_INGESTION_CONTRACTS if c.dataset_id == "p1_macro_indicators")
report = validate_record({"indicator_id": "KW-GDP-2024Q4", "value": 2.3, "country": "KW"}, contract)
```

## Design Decisions

1. **FoundationModel base**: All schemas inherit from FoundationModel providing schema_version, tenant_id, created_at, updated_at, and SHA-256 provenance_hash.

2. **Enums over strings**: GCC countries, sectors, entity types, and severity levels are strictly typed enums. This prevents data drift and enables IDE autocomplete.

3. **Confidence + source tracking**: Every data record carries confidence_score, confidence_method, and source_id. This feeds the trust scoring engine and enables provenance tracing.

4. **Ingestion contracts**: Declarative contracts separate the "what" from the "how". The runtime engine interprets contracts to perform field mapping, transformation, and quality gate checks.

5. **Quality gates**: Validation rules are defined per-contract and evaluated at ingestion time. Gates can be WARN (log and continue) or ERROR (reject record).

6. **IFRS 17 fields**: Insurance profiles include CSM, risk adjustment, and insurance revenue fields for IFRS 17 compliance — a hard requirement for GCC insurers.

7. **KWD as default currency**: Kuwait is the primary deployment market. CBK indicators default to KWD. Other datasets use explicit currency fields.

## Assumptions

1. All GCC central banks publish comparable monetary statistics (they do, with minor lag differences).
2. OPEC MOMR is the authoritative source for production quotas (verified against country-level reports).
3. GCC FX pegs to USD are stable within ±50bps under normal conditions.
4. Bank financial data is available quarterly with a 45-90 day reporting lag.
5. Insurance data follows IFRS 17 format for all GCC markets (Saudi mandated 2023, others 2024-2025).
6. Logistics node data is semi-static — major capacity changes happen annually.
7. Event signal severity maps directly to the simulation engine's URS thresholds.
8. Decision rules require human-in-the-loop approval before execution (default: true).

## P2 and P3 Roadmap

### P2 — Enrichment Layer (Next)
- Real-time AIS maritime vessel tracking integration
- Bloomberg/Reuters terminal data feeds
- Satellite imagery for infrastructure monitoring
- Social media sentiment signals (Arabic NLP)
- Cross-entity relationship graph (Neo4j import)
- Historical time series backfill (10-year)
- Automated data quality scoring and drift detection

### P3 — Advanced Intelligence
- ML-derived features (anomaly detection, regime classification)
- Causal inference models for event → impact chains
- Real-time streaming ingestion (Kafka/Redis Streams)
- Multi-tenant access control (row-level security)
- Data lineage visualization
- Automated report generation from data changes
- GraphRAG integration with knowledge graph
