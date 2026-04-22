# 05 — GCC Data / Entity Expansion Plan

**Status:** Foundation (spec-only).
**Depends on:** [01-architecture-lock](./01-architecture-lock.md),
[02-scenario-taxonomy](./02-scenario-taxonomy.md).

---

## 0. What this document locks

The **scope** of data and entity coverage Impact Observatory 2.0 must
reach, the **priority ordering** for filling current coverage gaps in
Kuwait, Bahrain, and Oman, and the **realism rules** that keep the
expansion honest given GCC public-data availability.

This document does not tell Build *how* to ingest anything. It tells
Build *what* must be representable and *in what order*.

---

## 1. Current baseline (v1.0.1)

- Entity registry: 43 nodes covering Saudi Arabia, UAE, Qatar, and a
  shared GCC infrastructure layer; lighter coverage on Kuwait, Bahrain,
  Oman.
- Scenario catalog: 20 templates, heavily maritime + energy + banking.
- Signal inputs: SAMA open data, ACLED, AIS-Stream, OpenSky,
  Bloomberg-style reference feeds (where provisioned), synthetic
  conditioning series.
- Data tiers observed in v1.0.1: primarily `public` and `synthetic`; very
  limited `licensed` and no `institutional` tier yet.

2.0 does not require an immediate overhaul of this baseline. It requires
a **plan** that the Build team can execute in phases without breaking
the live product.

---

## 2. Target entity categories

The 2.0 entity registry must be structured into five categories. Every
entity belongs to exactly one.

| Category | Examples |
|---|---|
| `sovereign` | Ministries of finance; central banks; sovereign wealth funds; rating authorities |
| `financial_institution` | Commercial banks; insurers; reinsurers; payment operators; clearing houses |
| `corporate` | Publicly-listed GCC corporates with systemic footprint (national oil cos, aluminum, petrochemicals, ports, airlines) |
| `infrastructure` | Ports, refineries, LNG terminals, payment rails, data centers, submarine cables, major pipelines |
| `regulatory_instrument` | Basel / IFRS / macroprudential rules in force; sanctions lists; supervisory circulars |

Entities carry country membership, sector membership, systemic-importance
flag, and public-or-not flag. The registry is a **graph**, not a list —
edges carry mechanism type (per
[01-architecture-lock](./01-architecture-lock.md) §2).

---

## 3. Target source categories

Build will mix four source tiers. The contract locks the tiers; the
specific providers are Build choices informed by cost and availability.

### 3.1 `public` (stable baseline)

- Central-bank open-data portals (SAMA, CBUAE, QCB, CBB, CBK, CBO).
- Ministry-of-finance publications (budget statements, debt issuance
  calendars, reserve reports where published).
- National statistics offices (GCC-STAT, country-level NSOs).
- IMF Article IV reports (public versions); World Bank GCC indicators.
- Regulatory circulars (where published).
- Maritime open data: AIS feeds, port-authority publications.
- Energy open data: OPEC MOMR, JODI, IEA public releases.
- Credit / fixed-income public indices and sovereign risk spreads as
  reported through public terminals or mirror services.

This tier is the **stable public data base** that Foundation requires
Build to cover for all six GCC countries.

### 3.2 `licensed`

- Bloomberg / Refinitiv terminals (per seat).
- S&P / Fitch / Moody's data feeds.
- Kpler / Vortexa for shipping.
- Regulatory-filing databases where subscription is required.

Contracts procurement is a Build concern. Foundation locks only the slot.

### 3.3 `institutional`

- MoUs with central banks, ministries, exchanges, or regulators that
  provide data not available via public or licensed channels.
- This is the **relationship-based institutional intelligence layer**.
  It is strategically critical but it is **not** a Foundation blocker.
  Foundation assumes the product is useful without it and becomes
  progressively more useful with it.

### 3.4 `synthetic`

- Derived series, backfills, and scenario conditioning data produced by
  the simulation engine or by data-scientist work.
- Always tagged `source_tier = synthetic` so downstream layers can apply
  lower confidence weighting.

Foundation rule: synthetic signals are **first-class** in the system but
are never the sole basis for a DecisionOutput whose `confidence_class`
is `HIGH`.

---

## 4. Stable public data base — Foundation essentials

Build must be able to ingest and normalize the following for all six GCC
countries (SA, UAE, QA, KW, BH, OM) before the first 2.0 release:

1. **Sovereign fiscal basics:** policy rate, reserve requirement, headline
   fiscal-balance indicator, sovereign debt outstanding indicator,
   publicly-quoted sovereign risk spread proxy.
2. **FX basics:** official parity, published intervention corridor where
   applicable, published reserve level where published.
3. **Banking system basics:** aggregate banking-sector balance-sheet size,
   capital adequacy aggregate (where published), liquidity coverage
   aggregate (where published), interbank rate print.
4. **Energy basics (producers):** production level (where disclosed),
   export value, refinery throughput (where disclosed), LNG export
   volumes.
5. **Trade basics:** monthly goods-trade balance, major-port throughput
   (where published by port authority).
6. **Published regulatory-change signals:** supervisory circulars,
   central-bank press releases, ministry press releases.

This is the **floor**. Below this, a country is under-represented.

---

## 5. Relationship-based institutional intelligence — later

The `institutional` source tier is defined in §3.3. Foundation records its
existence and usage rules; Foundation does **not** require that any
specific relationship exist before 2.0 ships.

Rules:

1. An `institutional` source is always named and its counterparty agreed.
   No anonymous institutional feeds.
2. An `institutional` source always has a disclosure-handling policy
   attached (what can be shown, to whom, for how long).
3. An `institutional` signal never enters the `public` tier and is never
   echoed to an untiered UI surface.
4. Institutional signals feed the calibration channel like any other
   signal, but their `confidence_band` can be pinned to a specific value
   by governance rather than derived automatically.

Build is free to onboard relationships in parallel with product
development as long as the rules above are respected.

---

## 6. Country-level priorities

### 6.1 Saudi Arabia (already covered; maintain)
- Public feeds are strong. Ingestion hygiene is the work, not coverage.
- Priority entities already present: SAMA, MoF, Saudi Aramco, Ras Tanura,
  King Abdulaziz Port, major banks.
- Gap to close: regulatory-circular normalization into
  `regulatory_instrument` entities.

### 6.2 United Arab Emirates (already covered; maintain)
- CBUAE + major free zones well-represented.
- Priority entities already present: CBUAE, major banks (ENBD, FAB, etc.),
  DIFC, ADGM, Jebel Ali, Dubai Financial Market, Abu Dhabi Securities
  Exchange.
- Gap to close: reinsurance market coverage; payment-rail operators.

### 6.3 Qatar (already covered; maintain)
- QCB + QatarEnergy + LNG logistics.
- Gap to close: fintech / payment-rail specifics beyond QCB.

### 6.4 Kuwait — **priority expansion**

Foundation essentials to add before 2.0 release:

- `sovereign`: Central Bank of Kuwait (CBK); Kuwait Ministry of Finance;
  Kuwait Investment Authority (sovereign wealth; public disclosure
  limited, but `sovereign` membership must exist in the registry);
  Capital Markets Authority.
- `financial_institution`: National Bank of Kuwait; Kuwait Finance
  House; Boubyan Bank; Gulf Bank; Burgan Bank; Warba Bank; Kuwait
  Clearing Company.
- `corporate`: Kuwait Petroleum Corporation; Kuwait National Petroleum
  Company; Equate; Agility.
- `infrastructure`: Shuwaikh Port; Shuaiba Port; Mina Al Ahmadi
  refinery; Mina Abdullah refinery; Al-Zour refinery; KNet payment
  network.
- Data constraints: KIA disclosures are limited; refinery and oil
  production numbers are partially published; public fiscal detail is
  present. Kuwait's macro stability leans heavily on oil revenue —
  scenario coverage must reflect that.

### 6.5 Bahrain — **priority expansion**

Foundation essentials to add before 2.0 release:

- `sovereign`: Central Bank of Bahrain (CBB); Bahrain Ministry of
  Finance; Bahrain Economic Development Board.
- `financial_institution`: Ahli United Bank; Bank of Bahrain and
  Kuwait; BBK; Gulf International Bank; Arab Banking Corporation;
  Bahrain Clear; regional reinsurance entities hosted in Bahrain.
- `corporate`: Alba (aluminum); BAPCO; Garmco.
- `infrastructure`: Khalifa Bin Salman Port; Sitra refinery; BENEFIT
  payment network.
- Data constraints: Bahrain's reinsurance hub role needs explicit
  modeling; its sovereign sensitivity (smaller reserves, higher public
  debt to GDP) must be represented with published figures, not
  proxies.

### 6.6 Oman — **priority expansion**

Foundation essentials to add before 2.0 release:

- `sovereign`: Central Bank of Oman (CBO); Oman Ministry of Finance;
  Oman Investment Authority; Capital Market Authority.
- `financial_institution`: Bank Muscat; National Bank of Oman;
  HSBC Oman; Sohar International Bank; Bank Dhofar; Oman Arab Bank.
- `corporate`: OQ Group (integrated energy); Oman Air; Oman Cement.
- `infrastructure`: Port of Sohar; Port of Salalah (strategic
  Indian-Ocean gateway); Port of Duqm; Oman LNG; Mina al Fahal.
- Data constraints: Oman's budget is oil-sensitive; its Salalah and Duqm
  ports play a strategic Indian-Ocean role often under-modeled in GCC
  analysis. Scenario family `maritime` should have an explicit
  Oman-relevant sub-scenario by Build.

---

## 7. What is essential for Foundation vs. later for Build

**Essential in Foundation (this document locks them):**
- Entity categories (§2).
- Source tiers (§3).
- Stable public data base per-country requirements (§4).
- Rules for institutional signals (§5).
- Country priority list with explicit entities for KW / BH / OM (§6).

**Defer to Build phases (not Foundation):**
- Specific provider selection for each `licensed` slot.
- MoU / onboarding work for `institutional` sources.
- Data-pipeline technology choices (Kafka vs. batch vs. poll loops).
- Storage layer choices (Postgres schema, Neo4j vs. relational entity
  graph, columnar warehouse for time-series).
- Backfill and historical calibration runs.
- Specific refresh cadences per indicator.
- Data-residency and export-control compliance implementation.

**Explicitly NOT in 2.0:**
- Non-GCC coverage beyond what is needed for GCC transmission (e.g. IEA,
  global rating agencies, Brent price). The product is a GCC platform.
- Retail or consumer-level data.
- Private-client / investment-advisory data.

---

## 8. Realism rules (mandatory)

1. **Public first, synthetic last.** Any dashboard number that lands on an
   executive's screen must prefer a public-tier source over a synthetic
   fill whenever both exist.
2. **No hidden synthetic.** Synthetic signals are always tagged and
   always flow through `source_tier = synthetic`.
3. **Per-country parity before depth.** Before any country gets a fifth
   specialized source, every country must have the §4 floor.
4. **Entity identifiers are stable.** An entity once registered keeps its
   ID forever; renames happen at the display layer.
5. **Graph over list.** New entities join the graph with at least one
   typed edge to an existing entity at the time of registration. Orphan
   entities are not admitted.
6. **Licensed feeds do not enter the user interface without a public
   anchor.** Every customer-visible indicator must have a public-tier
   reference the user can be pointed at — the licensed feed is the
   high-resolution companion, not the sole truth.
7. **Institutional data never silently overrides public data.** An
   institutional signal may raise a flag, but a user-visible override
   requires a governance event (see
   [04-outcome-learning-spec](./04-outcome-learning-spec.md) §8).

---

## 9. Quality gates before Build declares coverage complete

For each GCC country, Build declares Foundation-level coverage complete
when:

1. Every §4 item has at least one `public` source ingested and normalized
   into a canonical `SignalObservation`.
2. Every §6 priority entity is represented in the registry with stable
   ID, category, sector, and at least one typed graph edge.
3. Every entity in the registry is resolvable by both ID and display
   label in both `en` and `ar`.
4. Every synthetic signal in use is listed against a justified reason
   (why no public source exists yet).
5. Coverage parity is visible in a governance-facing ledger: "SA, UAE,
   QA, KW, BH, OM each have X of N §4 floor items covered."

When all six countries hit 100% of the §4 floor, the product can
legitimately describe itself as **GCC-wide Macroeconomic Intelligence**
without caveat.

---

## 10. Exit criteria

Locked when §2–§9 are accepted. Changes to the country priority list in
§6, to the §4 public-data floor, or to the §8 realism rules require a
new revision of this file before Build onboards new sources.
