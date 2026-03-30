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
}

/** Shipping routes for globe arc rendering */
export const shippingRoutes: { from: GeoCoordinate; to: GeoCoordinate; label: string }[] = [
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 24.9857, lng: 55.0272 }, label: 'Hormuz → Jebel Ali' },
  { from: { lat: 26.5944, lng: 56.4667 }, to: { lat: 26.4473, lng: 50.1014 }, label: 'Hormuz → Dammam' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 25.2960, lng: 51.5488 }, label: 'Jebel Ali → Doha Port' },
  { from: { lat: 24.9857, lng: 55.0272 }, to: { lat: 23.6345, lng: 57.5893 }, label: 'Jebel Ali → Sohar' },
]

/** Aviation routes */
export const aviationRoutes: { from: GeoCoordinate; to: GeoCoordinate; label: string }[] = [
  { from: { lat: 24.9578, lng: 46.6989 }, to: { lat: 25.2532, lng: 55.3657 }, label: 'RUH → DXB' },
  { from: { lat: 24.9578, lng: 46.6989 }, to: { lat: 29.2266, lng: 47.9689 }, label: 'RUH → KWI' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 25.2731, lng: 51.6081 }, label: 'DXB → DOH' },
  { from: { lat: 29.2266, lng: 47.9689 }, to: { lat: 25.2731, lng: 51.6081 }, label: 'KWI → DOH' },
  { from: { lat: 25.2532, lng: 55.3657 }, to: { lat: 23.5880, lng: 58.3829 }, label: 'DXB → MCT' },
]
