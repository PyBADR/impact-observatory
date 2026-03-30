/* ═══════════════════════════════════════════════════
   GCC Node Coordinates — Geographic mapping for Globe
   ═══════════════════════════════════════════════════ */

export interface GeoCoordinate {
  lat: number
  lng: number
}

/** Map GCC graph node IDs to real geographic coordinates */
export const nodeCoordinates: Record<string, GeoCoordinate> = {
  // — Geography Layer —
  geo_sa:      { lat: 24.7136, lng: 46.6753 },  // Riyadh
  geo_uae:     { lat: 25.2048, lng: 55.2708 },  // Dubai
  geo_kw:      { lat: 29.3759, lng: 47.9774 },  // Kuwait City
  geo_qa:      { lat: 25.2854, lng: 51.5310 },  // Doha
  geo_om:      { lat: 23.5880, lng: 58.3829 },  // Muscat
  geo_bh:      { lat: 26.0667, lng: 50.5577 },  // Manama
  geo_hormuz:  { lat: 26.5944, lng: 56.4667 },  // Strait of Hormuz

  // — Infrastructure Layer —
  inf_ruh:     { lat: 24.9578, lng: 46.6989 },  // King Khalid Airport
  inf_dxb:     { lat: 25.2532, lng: 55.3657 },  // Dubai Airport
  inf_kwi:     { lat: 29.2266, lng: 47.9689 },  // Kuwait Airport
  inf_doh:     { lat: 25.2731, lng: 51.6081 },  // Hamad Airport
  inf_jebel:   { lat: 24.9857, lng: 55.0272 },  // Jebel Ali Port
  inf_dammam:  { lat: 26.4473, lng: 50.1014 },  // King Abdulaziz Port
  inf_doha_p:  { lat: 25.2960, lng: 51.5488 },  // Doha Port
  inf_desal:   { lat: 25.1100, lng: 55.2000 },  // Jebel Ali Desalination Complex
  inf_power:   { lat: 24.9200, lng: 46.7500 },  // SEC Power Grid Hub, Riyadh

  // — Economy Layer —
  eco_oil:     { lat: 26.3000, lng: 50.2000 },  // Eastern Province (oil hub)
  eco_aramco:  { lat: 26.3175, lng: 50.2083 },  // Dhahran (Aramco HQ)
  eco_adnoc:   { lat: 24.4539, lng: 54.3773 },  // Abu Dhabi (ADNOC HQ)
  eco_kpc:     { lat: 29.3375, lng: 48.0013 },  // Kuwait (KPC)
  eco_shipping:{ lat: 25.0000, lng: 55.1000 },  // Jebel Ali shipping zone
  eco_aviation:{ lat: 25.0657, lng: 55.1713 },  // UAE aviation hub
  eco_fuel:    { lat: 24.4700, lng: 54.3700 },  // Abu Dhabi fuel hub
  eco_gdp:     { lat: 24.4700, lng: 49.0000 },  // GCC center
  eco_tourism: { lat: 25.1970, lng: 55.2744 },  // Dubai tourism hub

  // — Finance Layer —
  fin_sama:    { lat: 24.6918, lng: 46.6855 },  // SAMA, Riyadh
  fin_uae_cb:  { lat: 24.4872, lng: 54.3613 },  // UAE CB, Abu Dhabi
  fin_kw_cb:   { lat: 29.3759, lng: 47.9850 },  // Kuwait CB
  fin_insurers:{ lat: 24.7500, lng: 46.7200 },  // Riyadh insurance hub
  fin_reinsure:{ lat: 25.1800, lng: 55.2800 },  // Dubai reinsurance hub
  fin_ins_risk:{ lat: 25.2200, lng: 55.2600 },  // Dubai risk center
  fin_tadawul: { lat: 24.6900, lng: 46.6900 },  // Tadawul, Riyadh

  // — Society Layer —
  soc_citizens: { lat: 24.7000, lng: 46.7000 },  // Riyadh
  soc_travelers:{ lat: 25.2000, lng: 55.3000 },  // Dubai
  soc_business: { lat: 25.0800, lng: 55.1400 },  // Dubai business district
  soc_media:    { lat: 25.2000, lng: 55.2500 },  // Dubai media city
  soc_social:   { lat: 24.7200, lng: 46.6800 },  // Riyadh
  soc_travel_d: { lat: 25.2500, lng: 55.3500 },  // Dubai
  soc_ticket:   { lat: 25.2532, lng: 55.3600 },  // Dubai airport area

  // — Additional Airports —
  inf_jed:      { lat: 21.6796, lng: 39.1565 },  // King Abdulaziz Airport
  inf_dmm:      { lat: 26.4712, lng: 49.7979 },  // King Fahd Airport
  inf_auh:      { lat: 24.4430, lng: 54.6511 },  // Abu Dhabi Airport
  inf_bah:      { lat: 26.2708, lng: 50.6336 },  // Bahrain Airport
  inf_mct:      { lat: 23.5933, lng: 58.2844 },  // Muscat Airport

  // — Additional Ports —
  inf_hamad:    { lat: 25.3800, lng: 51.5300 },  // Hamad Port, Qatar
  inf_khalifa:  { lat: 24.8100, lng: 54.6500 },  // Khalifa Port, Abu Dhabi
  inf_shuwaikh: { lat: 29.3500, lng: 47.9200 },  // Shuwaikh Port, Kuwait
  inf_sohar:    { lat: 24.3400, lng: 56.7100 },  // Sohar Port, Oman

  // — Telecom & Ministries (Infrastructure layer) —
  inf_telecom:  { lat: 24.7100, lng: 54.0000 },  // GCC Telecom hub
  gov_transport:{ lat: 24.6800, lng: 46.7200 },  // Min. of Transport, Riyadh
  gov_water:    { lat: 24.6900, lng: 46.7300 },  // Min. of Water & Elec., Riyadh

  // — Additional Economy Sectors & Ministries —
  eco_telecom:  { lat: 24.7000, lng: 54.1000 },  // Telecom Sector
  eco_food:     { lat: 25.0500, lng: 51.0000 },  // Food Security
  gov_energy:   { lat: 24.7000, lng: 46.7000 },  // Min. of Energy, Riyadh
  gov_tourism:  { lat: 24.7500, lng: 46.7100 },  // Min. of Tourism, Riyadh

  // — Additional Central Banks & Banking —
  fin_qa_cb:    { lat: 25.2867, lng: 51.5333 },  // Qatar Central Bank, Doha
  fin_om_cb:    { lat: 23.5900, lng: 58.3800 },  // Oman Central Bank, Muscat
  fin_bh_cb:    { lat: 26.2200, lng: 50.5900 },  // Bahrain Central Bank, Manama
  fin_banking:  { lat: 24.7200, lng: 46.6900 },  // Commercial Banks, Riyadh
  gov_finance:  { lat: 24.6850, lng: 46.6800 },  // Min. of Finance, Riyadh

  // — Additional Society Nodes —
  soc_expats:   { lat: 25.2000, lng: 55.2700 },  // Expatriate Workers, Dubai
  soc_hajj:     { lat: 21.4225, lng: 39.8262 },  // Hajj & Umrah, Makkah
  soc_food_d:   { lat: 25.3000, lng: 51.5000 },  // Food Demand, Qatar
  soc_housing:  { lat: 24.8000, lng: 46.8000 },  // Housing & Cost of Living, Riyadh
  soc_employment:{ lat: 24.7500, lng: 46.7500 }, // Employment, Riyadh
  soc_sentiment: { lat: 24.8000, lng: 46.7500 }, // Public Sentiment, Riyadh
  soc_stability: { lat: 24.6500, lng: 46.7100 }, // Public Stability, Riyadh
  eco_logistics: { lat: 25.0100, lng: 55.0800 }, // Logistics Hub, Jebel Ali
}

/** Shipping routes for globe arc rendering */
export const shippingRoutes: { from: GeoCoordinate; to: GeoCoordinate; label: string }[] = [
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 24.9857, lng: 55.0272 }, label: 'Hormuz → Jebel Ali' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 26.4473, lng: 50.1014 }, label: 'Hormuz → Dammam' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 25.2960, lng: 51.5488 }, label: 'Jebel Ali → Doha Port' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 24.3400, lng: 56.7100 }, label: 'Jebel Ali → Sohar' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 25.3800, lng: 51.5300 }, label: 'Hormuz → Hamad Port' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 24.8100, lng: 54.6500 }, label: 'Hormuz → Khalifa Port' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 29.3500, lng: 47.9200 }, label: 'Hormuz → Shuwaikh Port' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 24.8100, lng: 54.6500 }, label: 'Jebel Ali → Khalifa' },
  // ── Intercontinental oil/shipping routes (Hormuz impact visibility) ──
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 12.9000, lng: 45.0000 }, label: 'Hormuz → Gulf of Aden' },
  { from: { lat: 12.9000, lng: 45.0000 }, to: { lat: 30.0000, lng: 32.5500 }, label: 'Gulf of Aden → Suez' },
  { from: { lat: 30.0000, lng: 32.5500 }, to: { lat: 51.5074, lng:  1.1278 }, label: 'Suez → Europe (London)' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 19.0760, lng: 72.8777 }, label: 'Hormuz → Mumbai' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 31.2304, lng: 121.474 }, label: 'Hormuz → Shanghai' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat:  1.3521, lng: 103.820 }, label: 'Jebel Ali → Singapore' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 35.6762, lng: 139.650 }, label: 'Hormuz → Tokyo' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 22.3193, lng: 114.170 }, label: 'Jebel Ali → Hong Kong' },
]

/** Aviation routes */
export const aviationRoutes: { from: GeoCoordinate; to: GeoCoordinate; label: string }[] = [
  { from: { lat: 24.9578, lng: 46.6989 }, to: { lat: 25.2532, lng: 55.3657 }, label: 'RUH → DXB' },
  { from: { lat: 24.9578, lng: 46.6989 }, to: { lat: 29.2266, lng: 47.9689 }, label: 'RUH → KWI' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 25.2731, lng: 51.6081 }, label: 'DXB → DOH' },
  { from: { lat: 29.2266, lng: 47.9689 }, to: { lat: 25.2731, lng: 51.6081 }, label: 'KWI → DOH' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 23.5933, lng: 58.2844 }, label: 'DXB → MCT' },
  { from: { lat: 24.9578, lng: 46.6989 }, to: { lat: 21.6796, lng: 39.1565 }, label: 'RUH → JED' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 24.4430, lng: 54.6511 }, label: 'DXB → AUH' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 26.2708, lng: 50.6336 }, label: 'DXB → BAH' },
  { from: { lat: 21.6796, lng: 39.1565 }, to: { lat: 25.2731, lng: 51.6081 }, label: 'JED → DOH' },
]
