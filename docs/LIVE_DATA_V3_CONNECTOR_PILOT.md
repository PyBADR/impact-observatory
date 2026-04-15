# Live Data v3 — One Connector Pilot (RSS)

**Date:** 2026-04-15
**Branch:** `feature/live-data-v3-one-connector-pilot`
**Status:** Implemented — read-only, fixture-based, zero scenario changes

---

## 1. What This Is

A **one-connector pilot** that proves the connector architecture works end-to-end using a static RSS fixture. It does NOT make network calls, require secrets, or change scenario outputs.

### What this IS:
- A `BaseConnector` abstract interface (fetch, normalize, health_check)
- An `RSSConnector` that parses RSS 2.0 XML from local files/strings
- A 5-item RSS fixture with realistic GCC energy/market signals
- Category-to-scenario mapping (RSS categories → scenario IDs)
- Full audit log integration
- 48 contract tests — all from local fixtures, zero network

### What this is NOT:
- NOT making HTTP requests (reads local XML only)
- NOT requiring API keys or secrets
- NOT connected to the simulation engine
- NOT modifying scenario numbers
- NOT visible in the UI

---

## 2. Read-Only Only

The connector architecture is strictly read-only:
- `BaseConnector._fetch_raw()` returns raw dicts — never writes
- `BaseConnector.normalize()` produces frozen `SignalSnapshot` objects
- `ConnectorState` tracks metrics — never feeds back to scoring
- Test `test_catalog_unchanged_after_connector_run` verifies invariant

---

## 3. Does Not Affect Scenario Numbers

The connector modules do NOT import `simulation_engine`, `config`, or `run_orchestrator`. The only reference to `SCENARIO_CATALOG` is in the test file, solely to verify it is untouched.

---

## 4. No Live Scoring Yet

Signals from the connector are stored as snapshots. They are NOT passed to `compute_trust_score()` or any scoring function. The future path:

```
v3 (current): Connector → SignalSnapshot (stored, not used)
v4 (future):  Feature flag → SignalSnapshot → signal_inputs → TrustScore
v5 (future):  Live HTTP fetch → SignalSnapshot → scoring → UI
```

---

## 5. Connector Interface

```python
class BaseConnector(abc.ABC):
    connector_id: str          # Unique connector identifier
    source: SignalSource       # Registered signal source
    enabled: bool              # Must be True to fetch
    state: ConnectorState      # Runtime health/metrics

    # Abstract — subclasses implement:
    _fetch_raw() -> list[dict]           # Get raw entries
    _parse_entry(raw) -> dict            # Normalize one entry
    _health_ping() -> bool               # Check availability

    # Public API:
    health_check(audit_log?) -> ConnectorStatus
    fetch(audit_log?) -> list[dict]      # Fetch + parse
    normalize(audit_log?) -> list[SignalSnapshot]  # Full pipeline
```

### ConnectorStatus enum:
- `HEALTHY` — Source reachable, data parseable
- `DEGRADED` — Reachable but partial data
- `UNAVAILABLE` — Not reachable or parseable
- `DISABLED` — Connector explicitly disabled
- `UNCHECKED` — Never checked

---

## 6. RSS Connector Details

The `RSSConnector`:
- Reads RSS 2.0 XML from `fixture_path` (file) or `xml_content` (string)
- Parses `<item>` elements: title, link, description, pubDate, category
- Converts RFC 2822 dates to ISO-8601
- Maps `<category>` tags to scenario IDs, countries, and sectors
- Never makes HTTP requests

### Category Mapping:
| RSS Category | Scenarios | Countries |
|-------------|-----------|-----------|
| energy | energy_market_volatility_shock, saudi_oil_shock | SAUDI, UAE, KUWAIT |
| maritime | hormuz_chokepoint_disruption, red_sea_trade_corridor_instability | UAE, OMAN, QATAR |
| banking | uae_banking_crisis, regional_liquidity_stress_event | UAE, BAHRAIN |
| fintech | gcc_cyber_attack | UAE |
| insurance | bahrain_sovereign_stress | UAE, BAHRAIN |
| logistics | oman_port_closure, critical_port_throughput_disruption | UAE, OMAN |

---

## 7. Fixture Data

`backend/tests/fixtures/sample_rss_feed.xml` — 5 items:

| Title | Categories | Date |
|-------|-----------|------|
| Brent crude rises 3% on Hormuz tension | energy, maritime | Apr 10 |
| CBUAE holds rates, flags liquidity tightening | banking, fintech | Apr 12 |
| Qatar LNG rerouted via Cape of Good Hope | energy, maritime, logistics | Apr 8 |
| Aramco Q1 exceeds OPEC+ quota | energy | Apr 7 |
| GCC insurance reserves adequate — S&P | insurance | Apr 9 |

---

## 8. Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/src/signal_ingestion/connectors/__init__.py` | ~15 | Package exports |
| `backend/src/signal_ingestion/connectors/base.py` | ~190 | BaseConnector abstract + ConnectorState |
| `backend/src/signal_ingestion/connectors/rss_connector.py` | ~190 | RSSConnector + category mapping |
| `backend/tests/fixtures/sample_rss_feed.xml` | ~50 | Static RSS fixture |
| `backend/tests/test_connector_pilot.py` | ~300 | 48 contract tests |
| `docs/LIVE_DATA_V3_CONNECTOR_PILOT.md` | this file | Documentation |

**Files modified:** None. Zero existing files changed.

---

## 9. How This Prepares v4/v5

| Version | What It Adds | Gated By |
|---------|-------------|----------|
| v3 (this) | Connector interface + RSS pilot + fixture tests | Nothing — safe baseline |
| v4 | HTTP fetch in RSSConnector + rate limiting | Feature flag: `ENABLE_RSS_FETCH` |
| v5 | Signal → scoring integration | Feature flag: `ENABLE_LIVE_SIGNAL_SCORING` |
| v6 | Multiple connectors (market, AIS, central bank) | Per-source enable flags |

---

## 10. Decision Gate — Before v4

Before enabling HTTP fetch in the RSS connector:

1. **Rate limiting** implemented (1 req per `refresh_frequency_minutes`)
2. **Timeout** configured (max 10s per request)
3. **Error budget** defined (max 3 consecutive failures → disable)
4. **Feature flag** `ENABLE_RSS_FETCH` defaults to `false`
5. **No secrets required** for public RSS feeds
6. **Audit trail** records every fetch attempt
7. **No scoring connection** until v5 with its own flag
