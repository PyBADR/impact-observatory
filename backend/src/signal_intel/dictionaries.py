"""Signal Intelligence Layer — Keyword & Alias Dictionaries.

Single source of truth for all deterministic lookup tables used by
the enrichment and mapping engines. Configuration-grade data that
changes more frequently than logic — kept separate from mapper.py.

No imports from mapper, enrichment, or adapters.
No business logic. Pure data.

Dictionaries:
  REGION_ALIASES          — hint string → GCCRegion enum member
  REGION_SCAN_PHRASES     — (phrase, region_code) for title/description scanning
  DOMAIN_ALIASES          — hint string → ImpactDomain enum value string
  DOMAIN_SCAN_KEYWORDS    — keyword → domain value string for content scanning
  SIGNAL_TYPE_KEYWORDS    — keyword → (signal_type, priority) for classification
  SEVERITY_KEYWORDS       — keyword → multiplier for severity scoring
  CONFIDENCE_WEIGHTS      — confidence string → float multiplier
  SIGNAL_TYPE_TO_SOURCE   — signal_type string → SignalSource for source override
"""

from __future__ import annotations

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalSource,
)


# ═══════════════════════════════════════════════════════════════════════════════
# REGION ALIASES — hint string → GCCRegion
# Used by mapper._resolve_regions() and enrichment.extract_regions()
# Case-insensitive lookup: caller must .strip().lower() before lookup.
# ═══════════════════════════════════════════════════════════════════════════════

REGION_ALIASES: dict[str, GCCRegion] = {
    # ── ISO codes (lowercase canonical) ──────────────────────────────────────
    "sa": GCCRegion.SAUDI_ARABIA,
    "ae": GCCRegion.UAE,
    "qa": GCCRegion.QATAR,
    "kw": GCCRegion.KUWAIT,
    "bh": GCCRegion.BAHRAIN,
    "om": GCCRegion.OMAN,
    "gcc": GCCRegion.GCC_WIDE,

    # ── Saudi Arabia ─────────────────────────────────────────────────────────
    "saudi arabia": GCCRegion.SAUDI_ARABIA,
    "saudi": GCCRegion.SAUDI_ARABIA,
    "ksa": GCCRegion.SAUDI_ARABIA,
    "kingdom of saudi arabia": GCCRegion.SAUDI_ARABIA,
    "riyadh": GCCRegion.SAUDI_ARABIA,
    "jeddah": GCCRegion.SAUDI_ARABIA,
    "jidda": GCCRegion.SAUDI_ARABIA,
    "dammam": GCCRegion.SAUDI_ARABIA,
    "dhahran": GCCRegion.SAUDI_ARABIA,
    "jubail": GCCRegion.SAUDI_ARABIA,
    "yanbu": GCCRegion.SAUDI_ARABIA,
    "mecca": GCCRegion.SAUDI_ARABIA,
    "medina": GCCRegion.SAUDI_ARABIA,
    "neom": GCCRegion.SAUDI_ARABIA,
    "tabuk": GCCRegion.SAUDI_ARABIA,
    "abha": GCCRegion.SAUDI_ARABIA,
    "khobar": GCCRegion.SAUDI_ARABIA,
    "al khobar": GCCRegion.SAUDI_ARABIA,
    "ras tanura": GCCRegion.SAUDI_ARABIA,
    "السعودية": GCCRegion.SAUDI_ARABIA,
    "المملكة العربية السعودية": GCCRegion.SAUDI_ARABIA,
    "المملكة": GCCRegion.SAUDI_ARABIA,
    "الرياض": GCCRegion.SAUDI_ARABIA,
    "جدة": GCCRegion.SAUDI_ARABIA,
    "الدمام": GCCRegion.SAUDI_ARABIA,
    "مكة": GCCRegion.SAUDI_ARABIA,
    "المدينة": GCCRegion.SAUDI_ARABIA,
    "نيوم": GCCRegion.SAUDI_ARABIA,
    "الجبيل": GCCRegion.SAUDI_ARABIA,
    "ينبع": GCCRegion.SAUDI_ARABIA,

    # ── UAE ──────────────────────────────────────────────────────────────────
    "united arab emirates": GCCRegion.UAE,
    "uae": GCCRegion.UAE,
    "dubai": GCCRegion.UAE,
    "abu dhabi": GCCRegion.UAE,
    "sharjah": GCCRegion.UAE,
    "ajman": GCCRegion.UAE,
    "ras al khaimah": GCCRegion.UAE,
    "fujairah": GCCRegion.UAE,
    "umm al quwain": GCCRegion.UAE,
    "jebel ali": GCCRegion.UAE,
    "khalifa port": GCCRegion.UAE,
    "الإمارات": GCCRegion.UAE,
    "الامارات": GCCRegion.UAE,
    "الإمارات العربية المتحدة": GCCRegion.UAE,
    "دبي": GCCRegion.UAE,
    "أبوظبي": GCCRegion.UAE,
    "ابوظبي": GCCRegion.UAE,
    "الشارقة": GCCRegion.UAE,
    "عجمان": GCCRegion.UAE,
    "رأس الخيمة": GCCRegion.UAE,
    "الفجيرة": GCCRegion.UAE,
    "جبل علي": GCCRegion.UAE,

    # ── Qatar ────────────────────────────────────────────────────────────────
    "qatar": GCCRegion.QATAR,
    "doha": GCCRegion.QATAR,
    "lusail": GCCRegion.QATAR,
    "ras laffan": GCCRegion.QATAR,
    "al wakrah": GCCRegion.QATAR,
    "mesaieed": GCCRegion.QATAR,
    "قطر": GCCRegion.QATAR,
    "الدوحة": GCCRegion.QATAR,
    "لوسيل": GCCRegion.QATAR,
    "رأس لفان": GCCRegion.QATAR,

    # ── Kuwait ───────────────────────────────────────────────────────────────
    "kuwait": GCCRegion.KUWAIT,
    "kuwait city": GCCRegion.KUWAIT,
    "al ahmadi": GCCRegion.KUWAIT,
    "shuwaikh": GCCRegion.KUWAIT,
    "الكويت": GCCRegion.KUWAIT,
    "مدينة الكويت": GCCRegion.KUWAIT,
    "الأحمدي": GCCRegion.KUWAIT,

    # ── Bahrain ──────────────────────────────────────────────────────────────
    "bahrain": GCCRegion.BAHRAIN,
    "manama": GCCRegion.BAHRAIN,
    "muharraq": GCCRegion.BAHRAIN,
    "isa town": GCCRegion.BAHRAIN,
    "البحرين": GCCRegion.BAHRAIN,
    "المنامة": GCCRegion.BAHRAIN,
    "المحرق": GCCRegion.BAHRAIN,

    # ── Oman ─────────────────────────────────────────────────────────────────
    "oman": GCCRegion.OMAN,
    "muscat": GCCRegion.OMAN,
    "salalah": GCCRegion.OMAN,
    "sohar": GCCRegion.OMAN,
    "duqm": GCCRegion.OMAN,
    "nizwa": GCCRegion.OMAN,
    "sur": GCCRegion.OMAN,
    "عمان": GCCRegion.OMAN,
    "مسقط": GCCRegion.OMAN,
    "صلالة": GCCRegion.OMAN,
    "صحار": GCCRegion.OMAN,
    "الدقم": GCCRegion.OMAN,

    # ── GCC-wide keywords ────────────────────────────────────────────────────
    "gulf": GCCRegion.GCC_WIDE,
    "gcc region": GCCRegion.GCC_WIDE,
    "middle east": GCCRegion.GCC_WIDE,
    "hormuz": GCCRegion.GCC_WIDE,
    "strait of hormuz": GCCRegion.GCC_WIDE,
    "persian gulf": GCCRegion.GCC_WIDE,
    "arabian gulf": GCCRegion.GCC_WIDE,
    "gulf cooperation council": GCCRegion.GCC_WIDE,
    "الخليج": GCCRegion.GCC_WIDE,
    "الخليج العربي": GCCRegion.GCC_WIDE,
    "مجلس التعاون": GCCRegion.GCC_WIDE,
    "مجلس التعاون الخليجي": GCCRegion.GCC_WIDE,
}


# ═══════════════════════════════════════════════════════════════════════════════
# REGION SCAN PHRASES — for title/description content scanning
# Ordered LONGEST FIRST to prevent partial matches.
# Each tuple: (lowercase_phrase, region_code_string)
# ═══════════════════════════════════════════════════════════════════════════════

REGION_SCAN_PHRASES: list[tuple[str, str]] = sorted(
    [
        # Saudi Arabia
        ("kingdom of saudi arabia", "SA"),
        ("المملكة العربية السعودية", "SA"),
        ("saudi arabia", "SA"), ("saudi aramco", "SA"), ("aramco", "SA"),
        ("sabic", "SA"), ("neom", "SA"), ("riyadh", "SA"), ("jeddah", "SA"),
        ("jidda", "SA"), ("dammam", "SA"), ("dhahran", "SA"), ("jubail", "SA"),
        ("yanbu", "SA"), ("mecca", "SA"), ("medina", "SA"), ("tabuk", "SA"),
        ("khobar", "SA"), ("al khobar", "SA"), ("ras tanura", "SA"),
        ("tadawul", "SA"),
        ("السعودية", "SA"), ("المملكة", "SA"), ("الرياض", "SA"),
        ("جدة", "SA"), ("الدمام", "SA"), ("مكة", "SA"), ("المدينة", "SA"),
        ("نيوم", "SA"), ("أرامكو", "SA"), ("سابك", "SA"),
        ("تداول", "SA"),

        # UAE
        ("united arab emirates", "AE"), ("abu dhabi", "AE"),
        ("jebel ali", "AE"), ("khalifa port", "AE"),
        ("ras al khaimah", "AE"), ("umm al quwain", "AE"),
        ("dubai", "AE"), ("sharjah", "AE"), ("ajman", "AE"),
        ("fujairah", "AE"), ("adnoc", "AE"), ("emaar", "AE"),
        ("الإمارات العربية المتحدة", "AE"), ("الإمارات", "AE"),
        ("الامارات", "AE"), ("دبي", "AE"), ("أبوظبي", "AE"),
        ("ابوظبي", "AE"), ("الشارقة", "AE"), ("جبل علي", "AE"),
        ("أدنوك", "AE"), ("إعمار", "AE"),
        ("dfm", "AE"), ("adx", "AE"),

        # Qatar
        ("ras laffan", "QA"), ("qatargas", "QA"), ("qatar energy", "QA"),
        ("qatar", "QA"), ("doha", "QA"), ("lusail", "QA"),
        ("al wakrah", "QA"), ("mesaieed", "QA"),
        ("قطر", "QA"), ("الدوحة", "QA"), ("لوسيل", "QA"),
        ("رأس لفان", "QA"), ("قطر للطاقة", "QA"),

        # Kuwait
        ("kuwait city", "KW"), ("مدينة الكويت", "KW"),
        ("kuwait", "KW"), ("al ahmadi", "KW"), ("shuwaikh", "KW"),
        ("الكويت", "KW"), ("الأحمدي", "KW"),

        # Bahrain
        ("bahrain", "BH"), ("manama", "BH"), ("muharraq", "BH"),
        ("البحرين", "BH"), ("المنامة", "BH"), ("المحرق", "BH"),

        # Oman
        ("salalah", "OM"), ("sohar", "OM"), ("duqm", "OM"),
        ("muscat", "OM"), ("nizwa", "OM"),
        ("صلالة", "OM"), ("صحار", "OM"), ("الدقم", "OM"),
        ("مسقط", "OM"),
        # "oman" handled via word-boundary check to avoid "ottoman"/"romania"

        # GCC-wide
        ("gulf cooperation council", "GCC"), ("مجلس التعاون الخليجي", "GCC"),
        ("strait of hormuz", "GCC"), ("arabian gulf", "GCC"),
        ("persian gulf", "GCC"), ("مجلس التعاون", "GCC"),
        ("الخليج العربي", "GCC"), ("الخليج", "GCC"),
        ("hormuz", "GCC"),
    ],
    key=lambda x: -len(x[0]),  # longest first
)

# Phrases requiring word-boundary check (to avoid partial match inside other words)
REGION_BOUNDARY_PHRASES: list[tuple[str, str]] = [
    ("oman", "OM"),
    ("ksa", "SA"),
    ("uae", "AE"),
    ("gcc", "GCC"),
    ("gulf", "GCC"),
    ("sur", "OM"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN ALIASES — hint string → ImpactDomain value string
# Used by mapper._resolve_domains() and enrichment.extract_domains()
# Case-insensitive: caller must .strip().lower() before lookup.
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_ALIASES: dict[str, str] = {
    # ── Oil & Gas ────────────────────────────────────────────────────────────
    "oil": "oil_gas",
    "oil_gas": "oil_gas",
    "oil & gas": "oil_gas",
    "oil and gas": "oil_gas",
    "petroleum": "oil_gas",
    "crude": "oil_gas",
    "crude oil": "oil_gas",
    "brent": "oil_gas",
    "wti": "oil_gas",
    "opec": "oil_gas",
    "lng": "oil_gas",
    "natural gas": "oil_gas",
    "refinery": "oil_gas",
    "upstream": "oil_gas",
    "downstream": "oil_gas",
    "petrochemical": "oil_gas",
    "hydrocarbon": "oil_gas",
    "gas": "oil_gas",

    # ── Energy Grid ──────────────────────────────────────────────────────────
    "energy": "energy_grid",
    "energy_grid": "energy_grid",
    "power": "energy_grid",
    "electricity": "energy_grid",
    "solar": "energy_grid",
    "renewable": "energy_grid",
    "renewables": "energy_grid",
    "desalination": "energy_grid",
    "nuclear": "energy_grid",
    "grid": "energy_grid",
    "utilities": "energy_grid",

    # ── Banking ──────────────────────────────────────────────────────────────
    "banking": "banking",
    "finance": "banking",
    "financial": "banking",
    "bank": "banking",
    "lending": "banking",
    "credit": "banking",
    "mortgage": "banking",
    "deposits": "banking",
    "central bank": "banking",
    "interest rate": "banking",
    "monetary": "banking",
    "fintech": "banking",

    # ── Insurance ────────────────────────────────────────────────────────────
    "insurance": "insurance",
    "reinsurance": "insurance",
    "underwriting": "insurance",
    "claims": "insurance",
    "premium": "insurance",
    "actuarial": "insurance",
    "takaful": "insurance",

    # ── Trade & Logistics ────────────────────────────────────────────────────
    "trade": "trade_logistics",
    "trade_logistics": "trade_logistics",
    "logistics": "trade_logistics",
    "shipping": "trade_logistics",
    "port": "trade_logistics",
    "freight": "trade_logistics",
    "container": "trade_logistics",
    "customs": "trade_logistics",
    "supply chain": "trade_logistics",
    "warehouse": "trade_logistics",
    "export": "trade_logistics",
    "import": "trade_logistics",
    "cargo": "trade_logistics",
    "transit": "trade_logistics",
    "free zone": "trade_logistics",
    "free trade": "trade_logistics",

    # ── Sovereign / Fiscal ───────────────────────────────────────────────────
    "sovereign": "sovereign_fiscal",
    "sovereign_fiscal": "sovereign_fiscal",
    "fiscal": "sovereign_fiscal",
    "budget": "sovereign_fiscal",
    "debt": "sovereign_fiscal",
    "treasury": "sovereign_fiscal",
    "gdp": "sovereign_fiscal",
    "deficit": "sovereign_fiscal",
    "government": "sovereign_fiscal",
    "public finance": "sovereign_fiscal",
    "sovereign wealth": "sovereign_fiscal",
    "vision 2030": "sovereign_fiscal",

    # ── Real Estate ──────────────────────────────────────────────────────────
    "real_estate": "real_estate",
    "real estate": "real_estate",
    "property": "real_estate",
    "construction": "real_estate",
    "housing": "real_estate",
    "residential": "real_estate",
    "commercial property": "real_estate",
    "development": "real_estate",

    # ── Telecommunications ───────────────────────────────────────────────────
    "telecom": "telecommunications",
    "telecommunications": "telecommunications",
    "5g": "telecommunications",
    "broadband": "telecommunications",
    "mobile": "telecommunications",
    "fiber": "telecommunications",

    # ── Aviation ─────────────────────────────────────────────────────────────
    "aviation": "aviation",
    "airport": "aviation",
    "airline": "aviation",
    "flight": "aviation",
    "airspace": "aviation",
    "aerospace": "aviation",

    # ── Maritime ─────────────────────────────────────────────────────────────
    "maritime": "maritime",
    "vessel": "maritime",
    "tanker": "maritime",
    "shipyard": "maritime",
    "fleet": "maritime",
    "naval": "maritime",
    "seaport": "maritime",

    # ── Cyber Infrastructure ─────────────────────────────────────────────────
    "cyber": "cyber_infrastructure",
    "cyber_infrastructure": "cyber_infrastructure",
    "cybersecurity": "cyber_infrastructure",
    "data breach": "cyber_infrastructure",
    "ransomware": "cyber_infrastructure",
    "hacking": "cyber_infrastructure",
    "cyber attack": "cyber_infrastructure",

    # ── Capital Markets ──────────────────────────────────────────────────────
    "capital_markets": "capital_markets",
    "capital markets": "capital_markets",
    "markets": "capital_markets",
    "stock": "capital_markets",
    "equity": "capital_markets",
    "equities": "capital_markets",
    "ipo": "capital_markets",
    "exchange": "capital_markets",
    "forex": "capital_markets",
    "bond": "capital_markets",
    "bonds": "capital_markets",
    "yield": "capital_markets",
    "index": "capital_markets",
    "securities": "capital_markets",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN SCAN KEYWORDS — for title/description content scanning
# Subset of DOMAIN_ALIASES that are safe for substring/word-boundary scanning
# (excludes overly generic terms like "power", "mobile", "development")
# ═══════════════════════════════════════════════════════════════════════════════

DOMAIN_SCAN_KEYWORDS: dict[str, str] = {
    # Oil & Gas
    "petroleum": "oil_gas", "crude oil": "oil_gas", "crude": "oil_gas",
    "brent": "oil_gas", "wti": "oil_gas", "opec": "oil_gas",
    "lng": "oil_gas", "natural gas": "oil_gas", "refinery": "oil_gas",
    "petrochemical": "oil_gas", "hydrocarbon": "oil_gas",
    "oil price": "oil_gas", "oil production": "oil_gas",
    "oil output": "oil_gas",

    # Energy Grid
    "power grid": "energy_grid", "electricity": "energy_grid",
    "solar energy": "energy_grid", "renewable energy": "energy_grid",
    "desalination": "energy_grid", "nuclear energy": "energy_grid",

    # Banking
    "central bank": "banking", "interest rate": "banking",
    "banking sector": "banking", "bank lending": "banking",
    "mortgage": "banking", "fintech": "banking",
    "monetary policy": "banking",

    # Insurance
    "insurance": "insurance", "reinsurance": "insurance",
    "underwriting": "insurance", "claims": "insurance",
    "takaful": "insurance", "premium": "insurance",

    # Trade & Logistics
    "supply chain": "trade_logistics", "free trade": "trade_logistics",
    "port closure": "trade_logistics", "freight": "trade_logistics",
    "container": "trade_logistics", "customs": "trade_logistics",
    "trade corridor": "trade_logistics", "logistics": "trade_logistics",
    "shipping lane": "trade_logistics", "cargo": "trade_logistics",
    "warehouse": "trade_logistics",

    # Sovereign/Fiscal
    "sovereign debt": "sovereign_fiscal", "sovereign bond": "sovereign_fiscal",
    "fiscal policy": "sovereign_fiscal", "budget deficit": "sovereign_fiscal",
    "government spending": "sovereign_fiscal", "treasury": "sovereign_fiscal",
    "sovereign wealth": "sovereign_fiscal", "vision 2030": "sovereign_fiscal",
    "gdp growth": "sovereign_fiscal", "gdp": "sovereign_fiscal",

    # Real Estate
    "real estate": "real_estate", "property market": "real_estate",
    "construction": "real_estate", "housing": "real_estate",

    # Aviation
    "airport": "aviation", "airline": "aviation", "airspace": "aviation",
    "aviation": "aviation", "aerospace": "aviation",

    # Maritime
    "maritime": "maritime", "tanker": "maritime", "vessel": "maritime",
    "shipyard": "maritime", "naval": "maritime", "seaport": "maritime",
    "shipping": "maritime",

    # Cyber
    "cybersecurity": "cyber_infrastructure", "data breach": "cyber_infrastructure",
    "ransomware": "cyber_infrastructure", "cyber attack": "cyber_infrastructure",
    "hacking": "cyber_infrastructure",

    # Capital Markets
    "stock market": "capital_markets", "equity market": "capital_markets",
    "bond market": "capital_markets", "capital markets": "capital_markets",
    "ipo": "capital_markets", "forex": "capital_markets",
    "stock exchange": "capital_markets", "securities": "capital_markets",

    # Telecom
    "telecommunications": "telecommunications", "5g": "telecommunications",
    "broadband": "telecommunications", "fiber optic": "telecommunications",
}


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL TYPE KEYWORDS — keyword → (signal_type, priority)
# Higher priority wins on conflict. For title/description classification.
# ═══════════════════════════════════════════════════════════════════════════════

SIGNAL_TYPE_KEYWORDS: dict[str, tuple[str, int]] = {
    # ── Geopolitical (highest priority for conflict terms) ───────────────────
    "war": ("geopolitical", 10),
    "invasion": ("geopolitical", 10),
    "missile": ("geopolitical", 10),
    "military": ("geopolitical", 9),
    "conflict": ("geopolitical", 10),
    "sanctions": ("geopolitical", 9),
    "embargo": ("geopolitical", 9),
    "blockade": ("geopolitical", 9),
    "tensions": ("geopolitical", 8),
    "diplomacy": ("geopolitical", 7),
    "diplomatic": ("geopolitical", 7),
    "geopolitical": ("geopolitical", 8),
    "territorial": ("geopolitical", 8),
    "sovereignty": ("geopolitical", 8),
    "escalation": ("geopolitical", 9),
    "ceasefire": ("geopolitical", 8),
    "treaty": ("geopolitical", 7),
    "alliance": ("geopolitical", 7),
    "drone attack": ("geopolitical", 10),
    "naval": ("geopolitical", 7),

    # ── Policy ───────────────────────────────────────────────────────────────
    "policy": ("policy", 8),
    "central bank": ("policy", 9),
    "interest rate": ("policy", 9),
    "monetary policy": ("policy", 9),
    "fiscal policy": ("policy", 9),
    "fiscal": ("policy", 8),
    "monetary": ("policy", 8),
    "government spending": ("policy", 8),
    "budget": ("policy", 7),
    "subsidy": ("policy", 7),
    "tax": ("policy", 7),
    "stimulus": ("policy", 8),
    "austerity": ("policy", 8),
    "reform": ("policy", 7),
    "privatization": ("policy", 8),
    "nationalization": ("policy", 8),
    "vision 2030": ("policy", 8),

    # ── Market ───────────────────────────────────────────────────────────────
    "stock": ("market", 7),
    "equity": ("market", 7),
    "bond": ("market", 7),
    "yield": ("market", 7),
    "ipo": ("market", 8),
    "market": ("market", 6),
    "trading": ("market", 6),
    "rally": ("market", 7),
    "selloff": ("market", 7),
    "sell-off": ("market", 7),
    "volatility": ("market", 7),
    "index": ("market", 6),
    "forex": ("market", 7),
    "exchange rate": ("market", 7),
    "bull": ("market", 6),
    "bear": ("market", 6),

    # ── Commodity ────────────────────────────────────────────────────────────
    "crude": ("commodity", 9),
    "brent": ("commodity", 9),
    "wti": ("commodity", 9),
    "opec": ("commodity", 9),
    "oil price": ("commodity", 9),
    "oil production": ("commodity", 9),
    "oil output": ("commodity", 9),
    "commodity": ("commodity", 8),
    "lng": ("commodity", 8),
    "natural gas": ("commodity", 8),
    "petrochemical": ("commodity", 7),
    "gold": ("commodity", 7),
    "metals": ("commodity", 6),

    # ── Regulatory ───────────────────────────────────────────────────────────
    "regulation": ("regulatory", 8),
    "regulatory": ("regulatory", 8),
    "compliance": ("regulatory", 7),
    "legislation": ("regulatory", 8),
    "law": ("regulatory", 6),
    "legal": ("regulatory", 6),
    "licensing": ("regulatory", 7),
    "anti-money laundering": ("regulatory", 8),
    "aml": ("regulatory", 7),
    "kyc": ("regulatory", 7),
    "ifrs": ("regulatory", 7),
    "basel": ("regulatory", 7),
    "solvency": ("regulatory", 7),

    # ── Logistics ────────────────────────────────────────────────────────────
    "shipping": ("logistics", 8),
    "port": ("logistics", 8),
    "port closure": ("logistics", 9),
    "supply chain": ("logistics", 9),
    "freight": ("logistics", 8),
    "container": ("logistics", 7),
    "pipeline": ("logistics", 7),
    "trade route": ("logistics", 8),
    "chokepoint": ("logistics", 9),
    "strait": ("logistics", 8),
    "canal": ("logistics", 7),
    "logistics": ("logistics", 7),
    "cargo": ("logistics", 7),

    # ── Sentiment ────────────────────────────────────────────────────────────
    "sentiment": ("sentiment", 7),
    "confidence": ("sentiment", 6),
    "outlook": ("sentiment", 6),
    "forecast": ("sentiment", 6),
    "survey": ("sentiment", 6),
    "consumer confidence": ("sentiment", 8),
    "investor sentiment": ("sentiment", 8),
    "pmi": ("sentiment", 7),
    "mood": ("sentiment", 6),
    "expectation": ("sentiment", 6),

    # ── Systemic ─────────────────────────────────────────────────────────────
    "systemic": ("systemic", 9),
    "contagion": ("systemic", 9),
    "cascade": ("systemic", 8),
    "domino": ("systemic", 8),
    "spillover": ("systemic", 8),
    "systemic risk": ("systemic", 10),
    "financial crisis": ("systemic", 9),
    "banking crisis": ("systemic", 9),
    "liquidity crisis": ("systemic", 9),
    "meltdown": ("systemic", 9),
    "collapse": ("systemic", 8),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SEVERITY KEYWORDS — keyword → multiplier
# Applied to base severity score. >1.0 amplifies, <1.0 dampens.
# ═══════════════════════════════════════════════════════════════════════════════

SEVERITY_KEYWORDS: dict[str, float] = {
    # ── Crisis-level (strong amplification) ──────────────────────────────────
    "war": 2.5,
    "invasion": 2.5,
    "catastrophe": 2.2,
    "collapse": 2.2,
    "meltdown": 2.2,
    "crisis": 2.0,
    "shutdown": 2.0,
    "blockade": 2.0,
    "default": 2.0,
    "bankruptcy": 2.0,
    "explosion": 2.0,
    "closure": 1.9,
    "attack": 1.9,
    "destroyed": 2.0,

    # ── High severity (moderate amplification) ──────────────────────────────
    "crash": 1.8,
    "embargo": 1.7,
    "emergency": 1.7,
    "recession": 1.7,
    "sanctions": 1.6,
    "escalation": 1.6,
    "surge": 1.6,
    "plunge": 1.6,
    "disruption": 1.5,
    "suspension": 1.5,
    "downgrade": 1.5,
    "outage": 1.5,
    "breach": 1.5,
    "contagion": 1.6,
    "panic": 1.6,

    # ── Moderate severity ────────────────────────────────────────────────────
    "inflation": 1.4,
    "spike": 1.4,
    "warning": 1.3,
    "tension": 1.3,
    "decline": 1.3,
    "drop": 1.3,
    "risk": 1.2,
    "fall": 1.2,
    "cut": 1.2,
    "volatility": 1.3,
    "uncertainty": 1.2,
    "concern": 1.1,
    "reduce": 1.1,
    "slow": 1.1,
    "pressure": 1.2,

    # ── Positive / stabilizing (dampen severity) ────────────────────────────
    "recovery": 0.7,
    "growth": 0.7,
    "stable": 0.6,
    "improvement": 0.7,
    "upgrade": 0.7,
    "agreement": 0.6,
    "peace": 0.5,
    "cooperation": 0.6,
    "record high": 0.8,
    "expansion": 0.7,
    "resilient": 0.6,
    "surplus": 0.7,
    "boost": 0.8,
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIDENCE WEIGHTS — confidence string → multiplier for severity scoring
# ═══════════════════════════════════════════════════════════════════════════════

CONFIDENCE_WEIGHTS: dict[str, float] = {
    "verified": 1.00,
    "high": 0.95,
    "moderate": 0.85,
    "low": 0.70,
    "unverified": 0.60,
}


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNAL TYPE → SOURCE OVERRIDE
# When enrichment resolves a signal_type, override the blunt feed-type-based
# source classification with a content-aware mapping.
# ═══════════════════════════════════════════════════════════════════════════════

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
