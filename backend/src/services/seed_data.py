"""GCC seed data — nodes, edges, sample events, flights, vessels.

This mirrors the DeevoSim.jsx node/edge graph, expanded for the
full decision intelligence platform.
"""

GCC_NODES = [
    # GEOGRAPHY
    {"id": "saudi", "label": "Saudi Arabia", "label_ar": "المملكة العربية السعودية", "layer": "geography", "lat": 24.0, "lng": 45.0},
    {"id": "uae", "label": "UAE", "label_ar": "الإمارات العربية المتحدة", "layer": "geography", "lat": 24.2, "lng": 54.4},
    {"id": "kuwait", "label": "Kuwait", "label_ar": "الكويت", "layer": "geography", "lat": 29.3, "lng": 47.5},
    {"id": "qatar", "label": "Qatar", "label_ar": "قطر", "layer": "geography", "lat": 25.35, "lng": 51.18},
    {"id": "oman", "label": "Oman", "label_ar": "عمان", "layer": "geography", "lat": 21.4, "lng": 55.9},
    {"id": "bahrain", "label": "Bahrain", "label_ar": "البحرين", "layer": "geography", "lat": 26.1, "lng": 50.55},

    # INFRASTRUCTURE
    {"id": "hormuz", "label": "Hormuz Strait", "label_ar": "مضيق هرمز", "layer": "infrastructure", "lat": 26.5, "lng": 56.3},
    {"id": "shipping", "label": "Gulf Shipping Lanes", "label_ar": "ممرات الشحن الخليجية", "layer": "infrastructure", "lat": 27.0, "lng": 52.0},
    {"id": "airspace", "label": "GCC Airspace", "label_ar": "المجال الجوي للمجلس", "layer": "infrastructure", "lat": 24.8, "lng": 50.5},
    {"id": "riyadh_apt", "label": "Riyadh Airport", "label_ar": "مطار الرياض", "layer": "infrastructure", "lat": 24.96, "lng": 46.70},
    {"id": "dubai_apt", "label": "Dubai Airport", "label_ar": "مطار دبي", "layer": "infrastructure", "lat": 25.25, "lng": 55.36},
    {"id": "kuwait_apt", "label": "Kuwait Airport", "label_ar": "مطار الكويت", "layer": "infrastructure", "lat": 29.23, "lng": 47.97},
    {"id": "doha_apt", "label": "Doha Airport", "label_ar": "مطار الدوحة", "layer": "infrastructure", "lat": 25.26, "lng": 51.60},
    {"id": "muscat_apt", "label": "Muscat Airport", "label_ar": "مطار مسقط", "layer": "infrastructure", "lat": 23.59, "lng": 58.28},
    {"id": "bahrain_apt", "label": "Bahrain Airport", "label_ar": "مطار البحرين", "layer": "infrastructure", "lat": 26.13, "lng": 50.29},
    {"id": "jebel_ali", "label": "Jebel Ali Port", "label_ar": "ميناء جبل علي", "layer": "infrastructure", "lat": 24.97, "lng": 55.00},
    {"id": "ras_tanura", "label": "Ras Tanura Port", "label_ar": "ميناء رأس تنورة", "layer": "infrastructure", "lat": 26.64, "lng": 50.04},
    {"id": "shuwaikh", "label": "Shuwaikh Port", "label_ar": "ميناء الشويخ", "layer": "infrastructure", "lat": 29.37, "lng": 47.80},
    {"id": "hamad_port", "label": "Hamad Port", "label_ar": "ميناء حمد", "layer": "infrastructure", "lat": 25.44, "lng": 50.77},
    {"id": "aramco_infra", "label": "Aramco Infrastructure", "label_ar": "البنية التحتية لأرامكو", "layer": "infrastructure", "lat": 26.0, "lng": 50.2},
    {"id": "power_grid", "label": "GCC Power Grid", "label_ar": "شبكة الكهرباء الخليجية", "layer": "infrastructure", "lat": 25.0, "lng": 52.0},

    # ECONOMY
    {"id": "oil_sector", "label": "Oil Sector", "label_ar": "قطاع النفط", "layer": "economy", "lat": 26.0, "lng": 49.0},
    {"id": "gas_sector", "label": "Gas Sector", "label_ar": "قطاع الغاز", "layer": "economy", "lat": 26.5, "lng": 50.5},
    {"id": "shipping_sector", "label": "Shipping Sector", "label_ar": "قطاع الشحن", "layer": "economy", "lat": 27.2, "lng": 52.5},
    {"id": "logistics", "label": "Logistics Sector", "label_ar": "قطاع الخدمات اللوجستية", "layer": "economy", "lat": 26.8, "lng": 51.8},
    {"id": "aviation", "label": "Aviation Sector", "label_ar": "قطاع الطيران", "layer": "economy", "lat": 25.5, "lng": 52.2},
    {"id": "tourism", "label": "Tourism Sector", "label_ar": "قطاع السياحة", "layer": "economy", "lat": 25.2, "lng": 53.5},
    {"id": "gdp", "label": "GCC GDP", "label_ar": "الناتج المحلي الإجمالي", "layer": "economy", "lat": 25.0, "lng": 51.0},
    {"id": "supply_chain", "label": "Supply Chain", "label_ar": "سلسلة التوريد", "layer": "economy", "lat": 26.5, "lng": 51.5},

    # FINANCE
    {"id": "sama", "label": "SAMA Central Bank", "label_ar": "البنك المركزي السعودي", "layer": "finance", "lat": 24.6, "lng": 46.7},
    {"id": "cbuae", "label": "CBUAE", "label_ar": "البنك المركزي الإماراتي", "layer": "finance", "lat": 24.5, "lng": 54.4},
    {"id": "cbk", "label": "CBK", "label_ar": "البنك المركزي الكويتي", "layer": "finance", "lat": 29.3, "lng": 47.5},
    {"id": "fin_markets", "label": "GCC Financial Markets", "label_ar": "الأسواق المالية الخليجية", "layer": "finance", "lat": 25.2, "lng": 51.5},
    {"id": "insurance", "label": "GCC Insurance Market", "label_ar": "سوق التأمين الخليجية", "layer": "finance", "lat": 25.8, "lng": 51.0},
    {"id": "reinsurance", "label": "GCC Reinsurance", "label_ar": "إعادة التأمين الخليجية", "layer": "finance", "lat": 25.9, "lng": 50.9},

    # SOCIETY
    {"id": "citizens", "label": "GCC Citizens", "label_ar": "مواطنو المجلس", "layer": "society", "lat": 24.5, "lng": 51.5},
    {"id": "travelers", "label": "GCC Travelers", "label_ar": "مسافرو المجلس", "layer": "society", "lat": 25.5, "lng": 52.5},
    {"id": "businesses", "label": "GCC Businesses", "label_ar": "الشركات الخليجية", "layer": "society", "lat": 25.2, "lng": 50.8},
    {"id": "media", "label": "GCC Media", "label_ar": "الإعلام الخليجي", "layer": "society", "lat": 25.0, "lng": 50.5},
    {"id": "social_platforms", "label": "Social Platforms", "label_ar": "منصات التواصل", "layer": "society", "lat": 25.1, "lng": 50.6},
    {"id": "sentiment", "label": "Public Sentiment", "label_ar": "الشعور العام", "layer": "society", "lat": 24.9, "lng": 50.7},
    {"id": "stability", "label": "Public Stability", "label_ar": "الاستقرار العام", "layer": "society", "lat": 25.0, "lng": 50.4},
]

GCC_EDGES = [
    # Geography → Infrastructure
    {"source": "saudi", "target": "riyadh_apt", "weight": 0.8, "polarity": 1, "category": "regional_control"},
    {"source": "saudi", "target": "ras_tanura", "weight": 0.9, "polarity": 1, "category": "regional_control"},
    {"source": "uae", "target": "dubai_apt", "weight": 0.85, "polarity": 1, "category": "regional_control"},
    {"source": "uae", "target": "jebel_ali", "weight": 0.88, "polarity": 1, "category": "regional_control"},
    {"source": "kuwait", "target": "kuwait_apt", "weight": 0.8, "polarity": 1, "category": "regional_control"},
    {"source": "kuwait", "target": "shuwaikh", "weight": 0.82, "polarity": 1, "category": "regional_control"},
    {"source": "qatar", "target": "doha_apt", "weight": 0.8, "polarity": 1, "category": "regional_control"},
    {"source": "qatar", "target": "hamad_port", "weight": 0.85, "polarity": 1, "category": "regional_control"},
    {"source": "oman", "target": "muscat_apt", "weight": 0.78, "polarity": 1, "category": "regional_control"},
    {"source": "bahrain", "target": "bahrain_apt", "weight": 0.75, "polarity": 1, "category": "regional_control"},

    # Infrastructure → Infrastructure
    {"source": "hormuz", "target": "shipping", "weight": 0.95, "polarity": 1, "category": "critical_path"},
    {"source": "hormuz", "target": "oil_sector", "weight": 0.92, "polarity": 1, "category": "critical_path"},
    {"source": "hormuz", "target": "gas_sector", "weight": 0.88, "polarity": 1, "category": "critical_path"},
    {"source": "airspace", "target": "aviation", "weight": 0.90, "polarity": 1, "category": "critical_path"},
    {"source": "shipping", "target": "jebel_ali", "weight": 0.85, "polarity": 1, "category": "logistics"},
    {"source": "shipping", "target": "ras_tanura", "weight": 0.83, "polarity": 1, "category": "logistics"},
    {"source": "power_grid", "target": "aramco_infra", "weight": 0.87, "polarity": 1, "category": "critical_infrastructure"},

    # Infrastructure → Economy
    {"source": "hormuz", "target": "shipping_sector", "weight": 0.90, "polarity": 1, "category": "trade_flow"},
    {"source": "hormuz", "target": "gdp", "weight": 0.88, "polarity": 1, "category": "trade_flow"},
    {"source": "jebel_ali", "target": "logistics", "weight": 0.88, "polarity": 1, "category": "logistics"},
    {"source": "ras_tanura", "target": "oil_sector", "weight": 0.91, "polarity": 1, "category": "production"},
    {"source": "dubai_apt", "target": "aviation", "weight": 0.86, "polarity": 1, "category": "transport"},
    {"source": "riyadh_apt", "target": "aviation", "weight": 0.84, "polarity": 1, "category": "transport"},
    {"source": "airspace", "target": "tourism", "weight": 0.85, "polarity": 1, "category": "transport"},
    {"source": "power_grid", "target": "oil_sector", "weight": 0.84, "polarity": 1, "category": "production"},

    # Economy → Finance
    {"source": "oil_sector", "target": "sama", "weight": 0.88, "polarity": 1, "category": "revenue"},
    {"source": "oil_sector", "target": "gdp", "weight": 0.90, "polarity": 1, "category": "production"},
    {"source": "gas_sector", "target": "gdp", "weight": 0.82, "polarity": 1, "category": "production"},
    {"source": "shipping_sector", "target": "insurance", "weight": 0.80, "polarity": 1, "category": "risk_transfer"},
    {"source": "aviation", "target": "insurance", "weight": 0.75, "polarity": 1, "category": "risk_transfer"},
    {"source": "gdp", "target": "fin_markets", "weight": 0.85, "polarity": 1, "category": "market_signal"},
    {"source": "insurance", "target": "reinsurance", "weight": 0.88, "polarity": 1, "category": "risk_transfer"},
    {"source": "logistics", "target": "supply_chain", "weight": 0.87, "polarity": 1, "category": "operations"},

    # Economy/Finance → Society
    {"source": "aviation", "target": "travelers", "weight": 0.82, "polarity": 1, "category": "mobility"},
    {"source": "tourism", "target": "travelers", "weight": 0.80, "polarity": 1, "category": "mobility"},
    {"source": "gdp", "target": "citizens", "weight": 0.78, "polarity": 1, "category": "welfare"},
    {"source": "supply_chain", "target": "businesses", "weight": 0.85, "polarity": 1, "category": "operations"},
    {"source": "fin_markets", "target": "businesses", "weight": 0.80, "polarity": 1, "category": "capital"},

    # Society internal
    {"source": "media", "target": "sentiment", "weight": 0.75, "polarity": 1, "category": "influence"},
    {"source": "social_platforms", "target": "sentiment", "weight": 0.72, "polarity": 1, "category": "influence"},
    {"source": "sentiment", "target": "stability", "weight": 0.80, "polarity": 1, "category": "feedback"},
    {"source": "stability", "target": "gdp", "weight": 0.60, "polarity": 1, "category": "feedback"},
    {"source": "stability", "target": "fin_markets", "weight": 0.55, "polarity": 1, "category": "feedback"},

    # Cross-layer feedback
    {"source": "insurance", "target": "shipping_sector", "weight": 0.65, "polarity": -1, "category": "cost_pressure"},
    {"source": "reinsurance", "target": "insurance", "weight": 0.70, "polarity": 1, "category": "capacity"},
]

# Sample events for demo/seed
SEED_EVENTS = [
    {
        "id": "evt-001",
        "title": "Naval exercise near Hormuz",
        "event_type": "military",
        "severity_score": 0.6,
        "lat": 26.55,
        "lng": 56.25,
        "region_id": "oman",
    },
    {
        "id": "evt-002",
        "title": "Drone incident over Gulf shipping lane",
        "event_type": "security",
        "severity_score": 0.75,
        "lat": 27.1,
        "lng": 52.3,
        "region_id": "qatar",
    },
    {
        "id": "evt-003",
        "title": "Port congestion at Jebel Ali",
        "event_type": "logistics",
        "severity_score": 0.5,
        "lat": 24.97,
        "lng": 55.00,
        "region_id": "uae",
    },
    {
        "id": "evt-004",
        "title": "Political tension escalation in region",
        "event_type": "political",
        "severity_score": 0.65,
        "lat": 25.0,
        "lng": 51.0,
        "region_id": "qatar",
    },
]

SEED_FLIGHTS = [
    {
        "id": "flt-001",
        "flight_number": "EK501",
        "status": "en_route",
        "origin_airport_id": "dubai_apt",
        "destination_airport_id": "riyadh_apt",
        "latitude": 24.8,
        "longitude": 50.5,
    },
    {
        "id": "flt-002",
        "flight_number": "QR402",
        "status": "scheduled",
        "origin_airport_id": "doha_apt",
        "destination_airport_id": "kuwait_apt",
        "latitude": 25.26,
        "longitude": 51.60,
    },
    {
        "id": "flt-003",
        "flight_number": "SV118",
        "status": "cancelled",
        "origin_airport_id": "riyadh_apt",
        "destination_airport_id": "bahrain_apt",
        "latitude": 24.96,
        "longitude": 46.70,
    },
]

SEED_VESSELS = [
    {
        "id": "vsl-001",
        "name": "Gulf Voyager",
        "mmsi": "538007921",
        "vessel_type": "tanker",
        "latitude": 26.5,
        "longitude": 56.2,
        "speed_knots": 12.5,
        "heading": 270,
        "destination_port_id": "jebel_ali",
    },
    {
        "id": "vsl-002",
        "name": "Arabian Carrier",
        "mmsi": "477123456",
        "vessel_type": "container",
        "latitude": 27.0,
        "longitude": 52.5,
        "speed_knots": 14.2,
        "heading": 180,
        "destination_port_id": "hamad_port",
    },
    {
        "id": "vsl-003",
        "name": "Kuwait Trader",
        "mmsi": "447654321",
        "vessel_type": "cargo",
        "latitude": 29.0,
        "longitude": 48.5,
        "speed_knots": 10.0,
        "heading": 90,
        "destination_port_id": "shuwaikh",
    },
]
