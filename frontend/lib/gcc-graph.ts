/* ═══════════════════════════════════════════════════════════════
   GCC Reality Graph — 5-Layer Causal Dependency Model v5.0
   GCC Digital Twin: Full Real-World Entity Coverage
   ═══════════════════════════════════════════════════════════════
   Layer 1: Geography     (6 countries + chokepoints)
   Layer 2: Infrastructure (airports, ports, utilities, telecom, ministries)
   Layer 3: Economy       (oil, logistics, aviation, food, tourism, telecom)
   Layer 4: Finance       (central banks, commercial banks, insurance, markets)
   Layer 5: Society       (citizens, expats, travelers, Hajj, media)

   Entity Coverage:
   - 6 GCC countries
   - 9 airports (RUH, JED, DMM, DXB, AUH, DOH, KWI, BAH, MCT)
   - 7 ports (Jebel Ali, Dammam, Doha, Hamad, Khalifa, Shuwaikh, Sohar)
   - 5 ministries (Energy, Water, Transport, Tourism, Finance)
   - 10 sectors (Oil, Electricity, Water, Tourism, Aviation, Logistics,
                  Banking, Insurance, Food Security, Telecom)
   ═══════════════════════════════════════════════════════════════ */

export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society'

export interface GCCNode {
  id: string
  label: string
  labelAr: string
  layer: GCCLayer
  type: string
  weight: number        // baseline importance 0–1
  sensitivity: number   // reactivity to incoming shocks 0–1
  damping_factor: number // rate of self-decay per iteration 0–1
  lat: number
  lng: number
  value: number         // base economic/strategic value (normalized 0–1)
}

export interface GCCEdge {
  id: string
  source: string
  target: string
  weight: number        // causal strength 0–1
  polarity: 1 | -1      // +1 = amplifying, -1 = dampening
  label: string
  labelAr: string
  animated?: boolean
}

export type ScenarioGroup = 'geopolitics' | 'aviation' | 'ports_supply' | 'finance_markets' | 'utilities_state' | 'sovereign_projects'

export const SCENARIO_GROUPS: Record<ScenarioGroup, { label: string; labelAr: string; icon: string }> = {
  geopolitics:       { label: 'Geopolitics',              labelAr: 'الجيوسياسة',               icon: '🌍' },
  aviation:          { label: 'Aviation',                 labelAr: 'الطيران',                  icon: '✈️' },
  ports_supply:      { label: 'Ports & Supply Chains',    labelAr: 'الموانئ وسلاسل الإمداد',    icon: '🚢' },
  finance_markets:   { label: 'Finance & Markets',        labelAr: 'المالية والأسواق',          icon: '💰' },
  utilities_state:   { label: 'Utilities & State Capacity', labelAr: 'المرافق وقدرة الدولة',   icon: '⚡' },
  sovereign_projects:{ label: 'Sovereign / Strategic',     labelAr: 'المشاريع السيادية',        icon: '🏗️' },
}

export interface GCCScenario {
  id: string
  title: string
  titleAr: string
  description: string
  descriptionAr: string
  thesis: string
  thesisAr: string
  group: ScenarioGroup
  category: string
  categoryAr?: string
  country: string
  countryAr?: string
  sectors: string[]
  sectorsAr?: string[]
  entities?: string[]
  entitiesAr?: string[]
  mapRelevance?: string
  mapRelevanceAr?: string
  shocks: { nodeId: string; impact: number }[]
  keyEntities: string[]
  mapModes: string[]
  formulaTags: string[]
  severityDefault: number
  timeHorizon: string
  timeHorizonAr: string
  expectedPropagationDomains: string[]
  simulationType: 'deterministic' | 'probabilistic' | 'hybrid'
  chokePoints?: string[]
  geospatialAnchors?: string[]
}

/* ════════════════════════════════════════════════
   NODES — 65 real GCC entities across 5 layers
   ════════════════════════════════════════════════ */
export const gccNodes: GCCNode[] = [
  // ═══════════════════════════════════
  // Layer 1: Geography (7 nodes)
  // ═══════════════════════════════════
  { id: 'geo_sa',      label: 'Saudi Arabia',       labelAr: 'السعودية',         layer: 'geography', type: 'Region',       lat: 24.7136, lng: 46.6753, weight: 0.95, sensitivity: 0.3,  damping_factor: 0.02, value: 0.95 },
  { id: 'geo_uae',     label: 'UAE',                labelAr: 'الإمارات',          layer: 'geography', type: 'Region',       lat: 25.2048, lng: 55.2708, weight: 0.90, sensitivity: 0.3,  damping_factor: 0.02, value: 0.90 },
  { id: 'geo_kw',      label: 'Kuwait',             labelAr: 'الكويت',           layer: 'geography', type: 'Region',       lat: 29.3759, lng: 47.9774, weight: 0.75, sensitivity: 0.35, damping_factor: 0.03, value: 0.75 },
  { id: 'geo_qa',      label: 'Qatar',              labelAr: 'قطر',              layer: 'geography', type: 'Region',       lat: 25.2854, lng: 51.5310, weight: 0.80, sensitivity: 0.3,  damping_factor: 0.02, value: 0.80 },
  { id: 'geo_om',      label: 'Oman',               labelAr: 'عُمان',            layer: 'geography', type: 'Region',       lat: 23.5880, lng: 58.3829, weight: 0.65, sensitivity: 0.4,  damping_factor: 0.04, value: 0.65 },
  { id: 'geo_bh',      label: 'Bahrain',            labelAr: 'البحرين',          layer: 'geography', type: 'Region',       lat: 26.0667, lng: 50.5577, weight: 0.60, sensitivity: 0.45, damping_factor: 0.04, value: 0.60 },
  { id: 'geo_hormuz',  label: 'Strait of Hormuz',   labelAr: 'مضيق هرمز',        layer: 'geography', type: 'Event',        lat: 26.5944, lng: 56.4667, weight: 0.98, sensitivity: 0.1,  damping_factor: 0.01, value: 0.98 },

  // ═══════════════════════════════════
  // Layer 2: Infrastructure (21 nodes)
  // Airports (9) + Ports (7) + Utilities (2) + Telecom (1) + Ministries (2)
  // ═══════════════════════════════════

  // ── Airports ──
  { id: 'inf_ruh',     label: 'RUH Airport',        labelAr: 'مطار الرياض',       layer: 'infrastructure', type: 'Organization', lat: 24.9578, lng: 46.6989, weight: 0.80, sensitivity: 0.5,  damping_factor: 0.05, value: 0.80 },
  { id: 'inf_jed',     label: 'JED Airport',        labelAr: 'مطار جدة',         layer: 'infrastructure', type: 'Organization', lat: 21.6796, lng: 39.1565, weight: 0.85, sensitivity: 0.5,  damping_factor: 0.05, value: 0.85 },
  { id: 'inf_dmm',     label: 'DMM Airport',        labelAr: 'مطار الدمام',       layer: 'infrastructure', type: 'Organization', lat: 26.4712, lng: 49.7979, weight: 0.70, sensitivity: 0.55, damping_factor: 0.06, value: 0.70 },
  { id: 'inf_dxb',     label: 'DXB Airport',        labelAr: 'مطار دبي',         layer: 'infrastructure', type: 'Organization', lat: 25.2532, lng: 55.3657, weight: 0.88, sensitivity: 0.5,  damping_factor: 0.05, value: 0.88 },
  { id: 'inf_auh',     label: 'AUH Airport',        labelAr: 'مطار أبوظبي',       layer: 'infrastructure', type: 'Organization', lat: 24.4330, lng: 54.6511, weight: 0.82, sensitivity: 0.5,  damping_factor: 0.05, value: 0.82 },
  { id: 'inf_doh',     label: 'DOH Airport',        labelAr: 'مطار الدوحة',       layer: 'infrastructure', type: 'Organization', lat: 25.2731, lng: 51.6081, weight: 0.75, sensitivity: 0.5,  damping_factor: 0.05, value: 0.75 },
  { id: 'inf_kwi',     label: 'KWI Airport',        labelAr: 'مطار الكويت',       layer: 'infrastructure', type: 'Organization', lat: 29.2266, lng: 47.9689, weight: 0.65, sensitivity: 0.55, damping_factor: 0.06, value: 0.65 },
  { id: 'inf_bah',     label: 'BAH Airport',        labelAr: 'مطار البحرين',      layer: 'infrastructure', type: 'Organization', lat: 26.2708, lng: 50.6336, weight: 0.60, sensitivity: 0.55, damping_factor: 0.06, value: 0.60 },
  { id: 'inf_mct',     label: 'MCT Airport',        labelAr: 'مطار مسقط',        layer: 'infrastructure', type: 'Organization', lat: 23.5933, lng: 58.2844, weight: 0.62, sensitivity: 0.55, damping_factor: 0.06, value: 0.62 },

  // ── Ports ──
  { id: 'inf_jebel',   label: 'Jebel Ali Port',     labelAr: 'ميناء جبل علي',     layer: 'infrastructure', type: 'Organization', lat: 24.9857, lng: 55.0272, weight: 0.92, sensitivity: 0.6,  damping_factor: 0.04, value: 0.92 },
  { id: 'inf_dammam',  label: 'Dammam Port',        labelAr: 'ميناء الدمام',      layer: 'infrastructure', type: 'Organization', lat: 26.4473, lng: 50.1014, weight: 0.78, sensitivity: 0.6,  damping_factor: 0.05, value: 0.78 },
  { id: 'inf_doha_p',  label: 'Doha Port',          labelAr: 'ميناء الدوحة',      layer: 'infrastructure', type: 'Organization', lat: 25.2960, lng: 51.5488, weight: 0.60, sensitivity: 0.55, damping_factor: 0.06, value: 0.60 },
  { id: 'inf_hamad',   label: 'Hamad Port',         labelAr: 'ميناء حمد',        layer: 'infrastructure', type: 'Organization', lat: 25.0147, lng: 51.6014, weight: 0.75, sensitivity: 0.55, damping_factor: 0.05, value: 0.75 },
  { id: 'inf_khalifa', label: 'Khalifa Port',       labelAr: 'ميناء خليفة',       layer: 'infrastructure', type: 'Organization', lat: 24.8125, lng: 54.6486, weight: 0.80, sensitivity: 0.55, damping_factor: 0.05, value: 0.80 },
  { id: 'inf_shuwaikh',label: 'Shuwaikh Port',      labelAr: 'ميناء الشويخ',      layer: 'infrastructure', type: 'Organization', lat: 29.3500, lng: 47.9200, weight: 0.65, sensitivity: 0.55, damping_factor: 0.06, value: 0.65 },
  { id: 'inf_sohar',   label: 'Sohar Port',         labelAr: 'ميناء صحار',       layer: 'infrastructure', type: 'Organization', lat: 24.3400, lng: 56.7400, weight: 0.68, sensitivity: 0.55, damping_factor: 0.06, value: 0.68 },

  // ── Utilities ──
  { id: 'inf_desal',   label: 'Desalination Plants', labelAr: 'محطات التحلية',   layer: 'infrastructure', type: 'Organization', lat: 25.6000, lng: 55.5000, weight: 0.82, sensitivity: 0.55, damping_factor: 0.04, value: 0.82 },
  { id: 'inf_power',   label: 'Power Grid',         labelAr: 'شبكة الكهرباء',     layer: 'infrastructure', type: 'Organization', lat: 24.9200, lng: 46.7500, weight: 0.85, sensitivity: 0.5,  damping_factor: 0.03, value: 0.85 },
  { id: 'inf_telecom', label: 'GCC Telecom',        labelAr: 'الاتصالات الخليجية',  layer: 'infrastructure', type: 'Organization', lat: 24.7100, lng: 54.0000, weight: 0.80, sensitivity: 0.45, damping_factor: 0.04, value: 0.80 },

  // ── Transport & Water Ministries (infrastructure oversight) ──
  { id: 'gov_transport',label: 'Min. of Transport',  labelAr: 'وزارة النقل',       layer: 'infrastructure', type: 'Ministry',    lat: 24.6800, lng: 46.7200, weight: 0.80, sensitivity: 0.35, damping_factor: 0.03, value: 0.80 },
  { id: 'gov_water',   label: 'Min. of Water & Elec.',labelAr: 'وزارة المياه والكهرباء', layer: 'infrastructure', type: 'Ministry', lat: 24.6900, lng: 46.7300, weight: 0.82, sensitivity: 0.4,  damping_factor: 0.03, value: 0.82 },

  // ═══════════════════════════════════
  // Layer 3: Economy (13 nodes)
  // Oil, gas companies, shipping, aviation, fuel, GDP, tourism, food, + ministries
  // ═══════════════════════════════════
  { id: 'eco_oil',     label: 'Oil Export',          labelAr: 'صادرات النفط',      layer: 'economy', type: 'Topic',         lat: 26.3000, lng: 50.2000, weight: 0.96, sensitivity: 0.7,  damping_factor: 0.03, value: 0.96 },
  { id: 'eco_aramco',  label: 'Aramco',             labelAr: 'أرامكو',           layer: 'economy', type: 'Organization',  lat: 26.3175, lng: 50.2083, weight: 0.95, sensitivity: 0.5,  damping_factor: 0.03, value: 0.95 },
  { id: 'eco_adnoc',   label: 'ADNOC',              labelAr: 'أدنوك',            layer: 'economy', type: 'Organization',  lat: 24.4539, lng: 54.3773, weight: 0.88, sensitivity: 0.5,  damping_factor: 0.04, value: 0.88 },
  { id: 'eco_kpc',     label: 'KPC',                labelAr: 'مؤسسة البترول الكويتية', layer: 'economy', type: 'Organization', lat: 29.3375, lng: 48.0013, weight: 0.78, sensitivity: 0.55, damping_factor: 0.04, value: 0.78 },
  { id: 'eco_shipping',label: 'Shipping Cost',labelAr: 'تكلفة الشحن', layer: 'economy', type: 'Topic', lat: 25.0000, lng: 55.1000, weight: 0.85, sensitivity: 0.65, damping_factor: 0.05, value: 0.85 },
  { id: 'eco_aviation',label: 'Aviation Fuel Cost',   labelAr: 'تكلفة وقود الطيران', layer: 'economy', type: 'Topic',         lat: 25.0657, lng: 55.1713, weight: 0.82, sensitivity: 0.6,  damping_factor: 0.05, value: 0.82 },
  { id: 'eco_fuel',    label: 'Fuel Cost',           labelAr: 'تكلفة الوقود',      layer: 'economy', type: 'Topic',         lat: 24.4700, lng: 54.3700, weight: 0.88, sensitivity: 0.7,  damping_factor: 0.04, value: 0.88 },
  { id: 'eco_gdp',     label: 'GCC GDP',            labelAr: 'الناتج المحلي الخليجي', layer: 'economy', type: 'Topic',      lat: 24.4700, lng: 49.0000, weight: 0.90, sensitivity: 0.4,  damping_factor: 0.02, value: 0.90 },
  { id: 'eco_tourism', label: 'Tourism Revenue',      labelAr: 'إيرادات السياحة',    layer: 'economy', type: 'Topic',         lat: 25.1970, lng: 55.2744, weight: 0.78, sensitivity: 0.65, damping_factor: 0.05, value: 0.78 },
  { id: 'eco_food',    label: 'Food Security',       labelAr: 'الأمن الغذائي',      layer: 'economy', type: 'Topic',         lat: 25.0500, lng: 51.0000, weight: 0.88, sensitivity: 0.7,  damping_factor: 0.05, value: 0.88 },

  // ── Economy-layer Ministries ──
  { id: 'gov_energy',  label: 'Min. of Energy',     labelAr: 'وزارة الطاقة',      layer: 'economy', type: 'Ministry',      lat: 24.7000, lng: 46.7000, weight: 0.90, sensitivity: 0.3,  damping_factor: 0.02, value: 0.90 },
  { id: 'gov_tourism', label: 'Min. of Tourism',    labelAr: 'وزارة السياحة',     layer: 'economy', type: 'Ministry',      lat: 24.7500, lng: 46.7100, weight: 0.75, sensitivity: 0.4,  damping_factor: 0.03, value: 0.75 },
  { id: 'eco_telecom', label: 'Telecom Sector',     labelAr: 'قطاع الاتصالات',     layer: 'economy', type: 'Topic',         lat: 24.7000, lng: 54.1000, weight: 0.78, sensitivity: 0.5,  damping_factor: 0.04, value: 0.78 },

  // ═══════════════════════════════════
  // Layer 4: Finance (12 nodes)
  // Central banks (6), commercial banking, insurers, reinsurers, risk, market, ministry
  // ═══════════════════════════════════
  { id: 'fin_sama',    label: 'SAMA',               labelAr: 'مؤسسة النقد',       layer: 'finance', type: 'Organization',  lat: 24.6918, lng: 46.6855, weight: 0.92, sensitivity: 0.35, damping_factor: 0.02, value: 0.92 },
  { id: 'fin_uae_cb',  label: 'UAE Central Bank',   labelAr: 'مصرف الإمارات المركزي', layer: 'finance', type: 'Organization', lat: 24.4872, lng: 54.3613, weight: 0.88, sensitivity: 0.35, damping_factor: 0.02, value: 0.88 },
  { id: 'fin_kw_cb',   label: 'Kuwait Central Bank',labelAr: 'بنك الكويت المركزي', layer: 'finance', type: 'Organization',  lat: 29.3759, lng: 47.9850, weight: 0.75, sensitivity: 0.4,  damping_factor: 0.03, value: 0.75 },
  { id: 'fin_qa_cb',   label: 'Qatar Central Bank', labelAr: 'مصرف قطر المركزي',   layer: 'finance', type: 'Organization',  lat: 25.2867, lng: 51.5333, weight: 0.78, sensitivity: 0.35, damping_factor: 0.02, value: 0.78 },
  { id: 'fin_om_cb',   label: 'Oman Central Bank',  labelAr: 'البنك المركزي العماني', layer: 'finance', type: 'Organization', lat: 23.5900, lng: 58.3800, weight: 0.65, sensitivity: 0.4,  damping_factor: 0.03, value: 0.65 },
  { id: 'fin_bh_cb',   label: 'Bahrain Central Bank',labelAr: 'مصرف البحرين المركزي', layer: 'finance', type: 'Organization', lat: 26.2200, lng: 50.5900, weight: 0.68, sensitivity: 0.4,  damping_factor: 0.03, value: 0.68 },
  { id: 'fin_banking', label: 'Commercial Banks',   labelAr: 'البنوك التجارية',    layer: 'finance', type: 'Organization',  lat: 24.7200, lng: 46.6900, weight: 0.88, sensitivity: 0.55, damping_factor: 0.04, value: 0.88 },
  { id: 'fin_insurers',label: 'Insurance Risk',      labelAr: 'مخاطر التأمين',      layer: 'finance', type: 'Organization',  lat: 24.7500, lng: 46.7200, weight: 0.80, sensitivity: 0.7,  damping_factor: 0.06, value: 0.80 },
  { id: 'fin_reinsure', label: 'Reinsurers',        labelAr: 'إعادة التأمين',      layer: 'finance', type: 'Organization',  lat: 25.1800, lng: 55.2800, weight: 0.75, sensitivity: 0.65, damping_factor: 0.05, value: 0.75 },
  { id: 'fin_ins_risk', label: 'Insurance Risk',    labelAr: 'مخاطر التأمين',      layer: 'finance', type: 'Topic',         lat: 25.2200, lng: 55.2600, weight: 0.82, sensitivity: 0.7,  damping_factor: 0.06, value: 0.82 },
  { id: 'fin_tadawul', label: 'Tadawul Exchange',   labelAr: 'تداول',             layer: 'finance', type: 'Organization',  lat: 24.6900, lng: 46.6900, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.04, value: 0.85 },
  { id: 'gov_finance', label: 'Min. of Finance',    labelAr: 'وزارة المالية',      layer: 'finance', type: 'Ministry',      lat: 24.6850, lng: 46.6800, weight: 0.88, sensitivity: 0.3,  damping_factor: 0.02, value: 0.88 },

  // ═══════════════════════════════════
  // Layer 5: Society (12 nodes)
  // Citizens, expats, travelers, Hajj, business, media, platforms, demand, tickets
  // ═══════════════════════════════════
  { id: 'soc_citizens', label: 'Citizens',          labelAr: 'المواطنون',         layer: 'society', type: 'Person',        lat: 24.7000, lng: 46.7000, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.06, value: 0.85 },
  { id: 'soc_expats',  label: 'Expatriate Workers', labelAr: 'العمالة الوافدة',    layer: 'society', type: 'Person',        lat: 25.2000, lng: 55.2700, weight: 0.80, sensitivity: 0.65, damping_factor: 0.06, value: 0.80 },
  { id: 'soc_travelers',label: 'Travelers',         labelAr: 'المسافرون',         layer: 'society', type: 'Person',        lat: 25.2000, lng: 55.3000, weight: 0.70, sensitivity: 0.65, damping_factor: 0.07, value: 0.70 },
  { id: 'soc_hajj',    label: 'Hajj & Umrah',       labelAr: 'الحج والعمرة',       layer: 'society', type: 'Event',         lat: 21.4225, lng: 39.8262, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.05, value: 0.85 },
  { id: 'soc_business', label: 'Businesses',        labelAr: 'الشركات',           layer: 'society', type: 'Organization',  lat: 25.0800, lng: 55.1400, weight: 0.80, sensitivity: 0.55, damping_factor: 0.05, value: 0.80 },
  { id: 'soc_media',    label: 'Media',             labelAr: 'الإعلام',           layer: 'society', type: 'Platform',      lat: 25.2000, lng: 55.2500, weight: 0.82, sensitivity: 0.5,  damping_factor: 0.06, value: 0.82 },
  { id: 'soc_social',   label: 'Social Platforms',  labelAr: 'المنصات الاجتماعية', layer: 'society', type: 'Platform',     lat: 24.7200, lng: 46.6800, weight: 0.78, sensitivity: 0.4,  damping_factor: 0.05, value: 0.78 },
  { id: 'soc_travel_d', label: 'Travel Demand',     labelAr: 'الطلب على السفر',    layer: 'society', type: 'Topic',         lat: 25.2500, lng: 55.3500, weight: 0.72, sensitivity: 0.7,  damping_factor: 0.07, value: 0.72 },
  { id: 'soc_ticket',   label: 'Flight Cost',        labelAr: 'تكلفة الرحلات',      layer: 'society', type: 'Topic',         lat: 25.2532, lng: 55.3600, weight: 0.68, sensitivity: 0.75, damping_factor: 0.08, value: 0.68 },
  { id: 'soc_food_d',  label: 'Food Demand',        labelAr: 'الطلب على الغذاء',   layer: 'society', type: 'Topic',         lat: 25.3000, lng: 51.5000, weight: 0.82, sensitivity: 0.7,  damping_factor: 0.06, value: 0.82 },
  { id: 'soc_housing', label: 'Housing & Cost of Living', labelAr: 'السكن وتكلفة المعيشة', layer: 'society', type: 'Topic', lat: 24.8000, lng: 46.8000, weight: 0.75, sensitivity: 0.6, damping_factor: 0.06, value: 0.75 },
  { id: 'soc_employment',label: 'Employment',       labelAr: 'التوظيف',           layer: 'society', type: 'Topic',         lat: 24.7500, lng: 46.7500, weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },
  { id: 'soc_sentiment',label: 'Public Sentiment',  labelAr: 'المشاعر العامة',     layer: 'society', type: 'Topic',         lat: 24.8000, lng: 46.7500, weight: 0.72, sensitivity: 0.65, damping_factor: 0.06, value: 0.72 },
  { id: 'soc_stability',label: 'Public Stability',  labelAr: 'الاستقرار العام',    layer: 'society', type: 'Topic',         lat: 24.6500, lng: 46.7100, weight: 0.80, sensitivity: 0.4,  damping_factor: 0.03, value: 0.80 },

  // ── Economy: Logistics Hub ──
  { id: 'eco_logistics',label: 'Logistics Hub',     labelAr: 'المركز اللوجستي',    layer: 'economy', type: 'Topic',         lat: 25.0100, lng: 55.0800, weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },

  // ── Aviation Phase 2: Airport Throughput + Airlines ──
  { id: 'inf_airport_throughput', label: 'Airport Throughput', labelAr: 'حركة المطارات', layer: 'infrastructure', type: 'Topic', lat: 25.15, lng: 55.20, weight: 0.82, sensitivity: 0.7, damping_factor: 0.05, value: 0.82 },
  { id: 'eco_saudia',   label: 'Saudia Airlines',    labelAr: 'الخطوط السعودية',    layer: 'economy', type: 'Organization',  lat: 24.96, lng: 46.70, weight: 0.75, sensitivity: 0.65, damping_factor: 0.05, value: 0.75 },
  { id: 'eco_emirates',  label: 'Emirates',           labelAr: 'طيران الإمارات',     layer: 'economy', type: 'Organization',  lat: 25.25, lng: 55.37, weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },
  { id: 'eco_qatar_aw',  label: 'Qatar Airways',      labelAr: 'الخطوط القطرية',     layer: 'economy', type: 'Organization',  lat: 25.27, lng: 51.57, weight: 0.78, sensitivity: 0.6,  damping_factor: 0.05, value: 0.78 },
  { id: 'eco_kw_airways',label: 'Kuwait Airways',     labelAr: 'الخطوط الكويتية',    layer: 'economy', type: 'Organization',  lat: 29.23, lng: 47.97, weight: 0.65, sensitivity: 0.6,  damping_factor: 0.05, value: 0.65 },
  { id: 'eco_gulf_air',  label: 'Gulf Air',           labelAr: 'طيران الخليج',       layer: 'economy', type: 'Organization',  lat: 26.27, lng: 50.63, weight: 0.60, sensitivity: 0.6,  damping_factor: 0.05, value: 0.60 },
  { id: 'eco_oman_air',  label: 'Oman Air',           labelAr: 'الطيران العماني',     layer: 'economy', type: 'Organization',  lat: 23.59, lng: 58.28, weight: 0.58, sensitivity: 0.6,  damping_factor: 0.05, value: 0.58 },
  { id: 'eco_av_stress', label: 'Aviation Sector Stress', labelAr: 'ضغط قطاع الطيران', layer: 'economy', type: 'Topic',      lat: 25.10, lng: 55.15, weight: 0.80, sensitivity: 0.7,  damping_factor: 0.05, value: 0.80 },
]

/* ════════════════════════════════════════════════
   EDGES — 115 weighted causal dependencies
   ════════════════════════════════════════════════ */
export const gccEdges: GCCEdge[] = [
  // ═══════════════════════════════════
  // HORMUZ → OIL CHAIN (core cascade)
  // ═══════════════════════════════════
  { id: 'e01', source: 'geo_hormuz',  target: 'eco_oil',      weight: 0.95, polarity: -1, label: 'disrupts export', labelAr: 'يعطّل التصدير',   animated: true },
  { id: 'e02', source: 'eco_oil',     target: 'eco_aramco',   weight: 0.90, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e03', source: 'eco_oil',     target: 'eco_adnoc',    weight: 0.85, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e04', source: 'eco_oil',     target: 'eco_kpc',      weight: 0.80, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e05', source: 'eco_oil',     target: 'eco_shipping',  weight: 0.85, polarity: -1, label: 'oil disruption raises shipping cost', labelAr: 'تعطل النفط يرفع تكلفة الشحن', animated: true },
  { id: 'e06', source: 'eco_oil',     target: 'eco_fuel',     weight: 0.88, polarity: -1, label: 'oil disruption raises fuel price', labelAr: 'تعطل النفط يرفع سعر الوقود' },

  // ═══════════════════════════════════
  // SHIPPING & LOGISTICS → PORTS
  // ═══════════════════════════════════
  { id: 'e07', source: 'eco_shipping', target: 'inf_jebel',   weight: 0.85, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e08', source: 'eco_shipping', target: 'inf_dammam',  weight: 0.78, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e09', source: 'eco_shipping', target: 'inf_doha_p',  weight: 0.60, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e10', source: 'eco_shipping', target: 'fin_ins_risk', weight: 0.80, polarity: 1, label: 'risk exposure', labelAr: 'التعرض للمخاطر',   animated: true },
  { id: 'e67', source: 'eco_shipping', target: 'inf_hamad',   weight: 0.70, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e68', source: 'eco_shipping', target: 'inf_khalifa', weight: 0.75, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e69', source: 'eco_shipping', target: 'inf_shuwaikh',weight: 0.55, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e70', source: 'eco_shipping', target: 'inf_sohar',   weight: 0.60, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },

  // ═══════════════════════════════════
  // INSURANCE CHAIN
  // ═══════════════════════════════════
  { id: 'e11', source: 'fin_ins_risk', target: 'fin_insurers',  weight: 0.80, polarity: 1, label: 'premium impact', labelAr: 'تأثير الأقساط' },
  { id: 'e12', source: 'fin_ins_risk', target: 'fin_reinsure',  weight: 0.75, polarity: 1, label: 'reinsurance cost', labelAr: 'تكلفة إعادة التأمين' },
  { id: 'e13', source: 'fin_insurers', target: 'soc_business',  weight: 0.65, polarity: 1, label: 'cost pass-through', labelAr: 'تمرير التكاليف' },
  // ── CRITICAL: Insurance Risk → Fuel Cost (completes Hormuz cascade) ──
  { id: 'e136', source: 'fin_ins_risk', target: 'eco_fuel',     weight: 0.75, polarity: 1, label: 'insurance surcharge', labelAr: 'رسوم التأمين الإضافية', animated: true },

  // ═══════════════════════════════════
  // FUEL → AVIATION → TICKET → DEMAND → AIRPORTS
  // ═══════════════════════════════════
  { id: 'e14', source: 'eco_fuel',     target: 'eco_aviation',  weight: 0.90, polarity: 1, label: 'fuel cost', labelAr: 'تكلفة الوقود',       animated: true },
  { id: 'e15', source: 'eco_aviation', target: 'soc_ticket',   weight: 0.85, polarity: 1, label: 'fuel raises flight cost', labelAr: 'الوقود يرفع تكلفة الرحلات', animated: true },
  // ── CRITICAL: Aviation Cost → Tourism (higher cost reduces tourism) ──
  { id: 'e137', source: 'eco_aviation', target: 'eco_tourism',  weight: 0.70, polarity: -1, label: 'cost dampens tourism', labelAr: 'التكلفة تخفض السياحة', animated: true },
  // e16 removed — replaced by stronger e150 in Aviation Phase 2 chain
  { id: 'e17', source: 'soc_travel_d', target: 'inf_dxb',     weight: 0.80, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e18', source: 'soc_travel_d', target: 'inf_ruh',     weight: 0.70, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e19', source: 'soc_travel_d', target: 'inf_kwi',     weight: 0.55, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e20', source: 'soc_travel_d', target: 'inf_doh',     weight: 0.60, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e71', source: 'soc_travel_d', target: 'inf_jed',     weight: 0.75, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e72', source: 'soc_travel_d', target: 'inf_dmm',     weight: 0.45, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e73', source: 'soc_travel_d', target: 'inf_auh',     weight: 0.65, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e74', source: 'soc_travel_d', target: 'inf_bah',     weight: 0.40, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e75', source: 'soc_travel_d', target: 'inf_mct',     weight: 0.45, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },

  // ═══════════════════════════════════
  // GDP CONTRIBUTIONS
  // ═══════════════════════════════════
  { id: 'e21', source: 'eco_aviation', target: 'eco_gdp',     weight: 0.60, polarity: -1, label: 'fuel cost drags GDP', labelAr: 'تكلفة الوقود تضغط الناتج' },
  { id: 'e22', source: 'eco_oil',     target: 'eco_gdp',      weight: 0.75, polarity: 1, label: 'oil revenue drives GDP', labelAr: 'إيرادات النفط تدعم الناتج' },
  { id: 'e23', source: 'eco_shipping', target: 'eco_gdp',     weight: 0.55, polarity: -1, label: 'shipping cost drags GDP', labelAr: 'تكلفة الشحن تضغط الناتج' },
  { id: 'e46', source: 'eco_aramco',   target: 'eco_gdp',      weight: 0.70, polarity: 1, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e47', source: 'eco_adnoc',    target: 'eco_gdp',      weight: 0.55, polarity: 1, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e50', source: 'eco_tourism',  target: 'eco_gdp',       weight: 0.60, polarity: 1, label: 'tourism GDP', labelAr: 'ناتج السياحة' },
  { id: 'e76', source: 'eco_food',     target: 'eco_gdp',       weight: 0.35, polarity: 1, label: 'food sector GDP', labelAr: 'ناتج قطاع الغذاء' },
  { id: 'e77', source: 'eco_telecom',  target: 'eco_gdp',       weight: 0.40, polarity: 1, label: 'telecom GDP', labelAr: 'ناتج الاتصالات' },
  { id: 'e78', source: 'fin_banking',  target: 'eco_gdp',       weight: 0.60, polarity: 1, label: 'credit multiplier', labelAr: 'مضاعف الائتمان' },

  // ═══════════════════════════════════
  // COUNTRY → NATIONAL ENTITIES
  // ═══════════════════════════════════
  { id: 'e24', source: 'geo_sa',      target: 'eco_aramco',   weight: 0.95, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e25', source: 'geo_uae',     target: 'eco_adnoc',    weight: 0.90, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e26', source: 'geo_kw',      target: 'eco_kpc',      weight: 0.85, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },

  // Country → Airports
  { id: 'e27', source: 'geo_sa',      target: 'inf_ruh',      weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e28', source: 'geo_uae',     target: 'inf_dxb',      weight: 0.85, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e30', source: 'geo_sa',      target: 'inf_dammam',   weight: 0.78, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e79', source: 'geo_sa',      target: 'inf_jed',      weight: 0.85, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e80', source: 'geo_sa',      target: 'inf_dmm',      weight: 0.70, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e81', source: 'geo_uae',     target: 'inf_auh',      weight: 0.82, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e82', source: 'geo_bh',      target: 'inf_bah',      weight: 0.75, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e83', source: 'geo_om',      target: 'inf_mct',      weight: 0.72, polarity: 1, label: 'operates', labelAr: 'يشغّل' },

  // Country → Ports
  { id: 'e29', source: 'geo_uae',     target: 'inf_jebel',    weight: 0.90, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e84', source: 'geo_uae',     target: 'inf_khalifa',  weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e85', source: 'geo_kw',      target: 'inf_shuwaikh', weight: 0.70, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e86', source: 'geo_om',      target: 'inf_sohar',    weight: 0.68, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e54', source: 'geo_qa',      target: 'inf_doh',       weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e55', source: 'geo_qa',      target: 'inf_doha_p',    weight: 0.75, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e87', source: 'geo_qa',      target: 'inf_hamad',     weight: 0.78, polarity: 1, label: 'operates', labelAr: 'يشغّل' },

  // ═══════════════════════════════════
  // CENTRAL BANK GOVERNANCE
  // ═══════════════════════════════════
  { id: 'e34', source: 'geo_sa',      target: 'fin_sama',      weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e35', source: 'geo_uae',     target: 'fin_uae_cb',   weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e36', source: 'geo_kw',      target: 'fin_kw_cb',    weight: 0.80, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e88', source: 'geo_qa',      target: 'fin_qa_cb',    weight: 0.80, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e89', source: 'geo_om',      target: 'fin_om_cb',    weight: 0.75, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e90', source: 'geo_bh',      target: 'fin_bh_cb',    weight: 0.75, polarity: 1, label: 'governs', labelAr: 'يحكم' },

  // Central Banks → Regulation
  { id: 'e31', source: 'fin_sama',    target: 'fin_insurers',  weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e32', source: 'fin_uae_cb',  target: 'fin_insurers',  weight: 0.65, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e33', source: 'fin_kw_cb',   target: 'fin_insurers',  weight: 0.55, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e91', source: 'fin_qa_cb',   target: 'fin_insurers',  weight: 0.55, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e92', source: 'fin_om_cb',   target: 'fin_insurers',  weight: 0.45, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e93', source: 'fin_bh_cb',   target: 'fin_insurers',  weight: 0.50, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e94', source: 'fin_sama',    target: 'fin_banking',   weight: 0.80, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e95', source: 'fin_uae_cb',  target: 'fin_banking',   weight: 0.75, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },

  // ═══════════════════════════════════
  // COMMERCIAL BANKING
  // ═══════════════════════════════════
  { id: 'e96', source: 'fin_banking', target: 'soc_business',  weight: 0.70, polarity: 1, label: 'business lending', labelAr: 'إقراض الشركات' },
  { id: 'e97', source: 'fin_banking', target: 'soc_housing',   weight: 0.65, polarity: 1, label: 'mortgage lending', labelAr: 'إقراض السكن' },
  { id: 'e98', source: 'fin_banking', target: 'fin_insurers',  weight: 0.50, polarity: 1, label: 'bancassurance', labelAr: 'التأمين المصرفي' },

  // ═══════════════════════════════════
  // SOCIETY CONNECTIONS
  // ═══════════════════════════════════
  { id: 'e37', source: 'soc_citizens', target: 'soc_social',   weight: 0.75, polarity: 1, label: 'expresses via', labelAr: 'يعبّر عبر' },
  { id: 'e38', source: 'soc_social',   target: 'soc_media',    weight: 0.70, polarity: 1, label: 'feeds', labelAr: 'يغذي' },
  { id: 'e39', source: 'soc_media',    target: 'soc_citizens', weight: 0.60, polarity: 1, label: 'informs', labelAr: 'يُعلم' },
  { id: 'e40', source: 'eco_fuel',     target: 'soc_citizens', weight: 0.80, polarity: 1, label: 'cost of living', labelAr: 'تكلفة المعيشة' },
  { id: 'e41', source: 'soc_business', target: 'eco_gdp',     weight: 0.55, polarity: 1, label: 'economic activity', labelAr: 'نشاط اقتصادي' },
  { id: 'e42', source: 'eco_gdp',     target: 'soc_citizens', weight: 0.50, polarity: 1, label: 'prosperity', labelAr: 'الرخاء' },
  { id: 'e48', source: 'soc_travelers', target: 'soc_travel_d', weight: 0.65, polarity: 1, label: 'demand signal', labelAr: 'إشارة الطلب' },

  // Expat workers
  { id: 'e99',  source: 'soc_expats',  target: 'soc_business',  weight: 0.75, polarity: 1, label: 'workforce', labelAr: 'القوى العاملة' },
  { id: 'e100', source: 'soc_expats',  target: 'eco_gdp',       weight: 0.55, polarity: 1, label: 'labor contribution', labelAr: 'مساهمة العمالة' },
  { id: 'e101', source: 'soc_expats',  target: 'soc_housing',   weight: 0.60, polarity: 1, label: 'housing demand', labelAr: 'الطلب على السكن' },
  { id: 'e102', source: 'eco_gdp',     target: 'soc_employment',weight: 0.65, polarity: 1, label: 'job creation', labelAr: 'خلق الوظائف' },
  { id: 'e103', source: 'soc_employment',target: 'soc_citizens', weight: 0.60, polarity: 1, label: 'citizen welfare', labelAr: 'رفاهية المواطنين' },
  { id: 'e104', source: 'soc_employment',target: 'soc_expats',   weight: 0.55, polarity: 1, label: 'expat demand', labelAr: 'الطلب على العمالة' },

  // ═══════════════════════════════════
  // CROSS-LAYER FEEDBACKS
  // ═══════════════════════════════════
  { id: 'e43', source: 'fin_insurers', target: 'eco_shipping',  weight: 0.40, polarity: -1, label: 'coverage constraint', labelAr: 'قيود التغطية' },
  { id: 'e44', source: 'fin_reinsure', target: 'fin_ins_risk',  weight: 0.35, polarity: -1, label: 'risk transfer', labelAr: 'نقل المخاطر' },
  { id: 'e45', source: 'soc_media',    target: 'fin_ins_risk',  weight: 0.30, polarity: 1, label: 'risk perception', labelAr: 'إدراك المخاطر' },

  // ═══════════════════════════════════
  // TOURISM + HAJJ
  // ═══════════════════════════════════
  { id: 'e49', source: 'soc_travel_d', target: 'eco_tourism',   weight: 0.85, polarity: 1, label: 'tourism demand', labelAr: 'طلب السياحة' },
  { id: 'e105', source: 'soc_hajj',   target: 'eco_tourism',    weight: 0.80, polarity: 1, label: 'pilgrimage revenue', labelAr: 'إيرادات الحج' },
  { id: 'e106', source: 'soc_hajj',   target: 'inf_jed',        weight: 0.85, polarity: 1, label: 'pilgrim flow', labelAr: 'تدفق الحجاج',      animated: true },
  { id: 'e107', source: 'soc_hajj',   target: 'soc_travelers',  weight: 0.70, polarity: 1, label: 'travel demand', labelAr: 'الطلب على السفر' },
  { id: 'e108', source: 'geo_sa',     target: 'soc_hajj',       weight: 0.90, polarity: 1, label: 'hosts', labelAr: 'يستضيف' },
  { id: 'e109', source: 'gov_tourism',target: 'eco_tourism',    weight: 0.70, polarity: 1, label: 'tourism policy', labelAr: 'سياسة السياحة' },
  { id: 'e110', source: 'gov_tourism',target: 'soc_hajj',       weight: 0.65, polarity: 1, label: 'pilgrim policy', labelAr: 'سياسة الحج' },

  // ═══════════════════════════════════
  // MARKET + FINANCE
  // ═══════════════════════════════════
  { id: 'e51', source: 'eco_aramco',   target: 'fin_tadawul',   weight: 0.75, polarity: 1, label: 'market cap', labelAr: 'القيمة السوقية' },
  { id: 'e52', source: 'fin_tadawul',  target: 'fin_sama',      weight: 0.45, polarity: 1, label: 'market signal', labelAr: 'إشارة السوق' },
  { id: 'e53', source: 'eco_gdp',      target: 'fin_tadawul',   weight: 0.60, polarity: 1, label: 'economic health', labelAr: 'الصحة الاقتصادية' },
  { id: 'e111', source: 'gov_finance', target: 'fin_sama',      weight: 0.75, polarity: 1, label: 'fiscal policy', labelAr: 'السياسة المالية' },
  { id: 'e112', source: 'gov_finance', target: 'fin_tadawul',   weight: 0.60, polarity: 1, label: 'market oversight', labelAr: 'الرقابة على السوق' },
  { id: 'e113', source: 'gov_finance', target: 'fin_banking',   weight: 0.65, polarity: 1, label: 'fiscal regulation', labelAr: 'التنظيم المالي' },

  // ═══════════════════════════════════
  // HORMUZ / OMAN / BAHRAIN CONNECTIONS
  // ═══════════════════════════════════
  { id: 'e56', source: 'geo_om',      target: 'eco_shipping',  weight: 0.55, polarity: 1, label: 'Strait access', labelAr: 'الوصول للمضيق' },
  { id: 'e57', source: 'geo_om',      target: 'geo_hormuz',    weight: 0.70, polarity: 1, label: 'controls strait', labelAr: 'يتحكم بالمضيق' },
  { id: 'e58', source: 'geo_bh',      target: 'fin_insurers',  weight: 0.45, polarity: 1, label: 'insurance hub', labelAr: 'مركز تأمين' },
  { id: 'e59', source: 'geo_bh',      target: 'eco_oil',       weight: 0.40, polarity: 1, label: 'oil production', labelAr: 'إنتاج النفط' },

  // ═══════════════════════════════════
  // UTILITIES (Power, Water, Telecom)
  // ═══════════════════════════════════
  { id: 'e60', source: 'eco_oil',     target: 'inf_power',     weight: 0.70, polarity: 1, label: 'fuel for power', labelAr: 'وقود للطاقة' },
  { id: 'e61', source: 'inf_power',   target: 'inf_desal',     weight: 0.85, polarity: 1, label: 'powers desalination', labelAr: 'يغذي التحلية' },
  { id: 'e62', source: 'inf_desal',   target: 'soc_citizens',  weight: 0.75, polarity: 1, label: 'water supply', labelAr: 'إمدادات المياه' },
  { id: 'e63', source: 'inf_power',   target: 'soc_citizens',  weight: 0.70, polarity: 1, label: 'electricity supply', labelAr: 'إمدادات الكهرباء' },
  { id: 'e64', source: 'inf_power',   target: 'soc_business',  weight: 0.65, polarity: 1, label: 'business power', labelAr: 'طاقة الأعمال' },
  { id: 'e65', source: 'geo_sa',      target: 'inf_power',     weight: 0.80, polarity: 1, label: 'national grid', labelAr: 'الشبكة الوطنية' },
  { id: 'e66', source: 'geo_uae',     target: 'inf_desal',     weight: 0.75, polarity: 1, label: 'water infrastructure', labelAr: 'البنية التحتية للمياه' },
  { id: 'e114', source: 'inf_power',  target: 'inf_telecom',   weight: 0.70, polarity: 1, label: 'powers telecom', labelAr: 'يغذي الاتصالات' },
  { id: 'e115', source: 'inf_telecom',target: 'eco_telecom',   weight: 0.80, polarity: 1, label: 'service delivery', labelAr: 'تقديم الخدمات' },
  { id: 'e116', source: 'eco_telecom',target: 'soc_business',  weight: 0.60, polarity: 1, label: 'digital services', labelAr: 'الخدمات الرقمية' },
  { id: 'e117', source: 'eco_telecom',target: 'soc_social',    weight: 0.55, polarity: 1, label: 'platform infra', labelAr: 'بنية المنصات' },

  // Ministry oversight
  { id: 'e118', source: 'gov_water',   target: 'inf_desal',    weight: 0.80, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e119', source: 'gov_water',   target: 'inf_power',    weight: 0.75, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e120', source: 'gov_transport',target: 'eco_shipping', weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e121', source: 'gov_transport',target: 'eco_aviation', weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },

  // ═══════════════════════════════════
  // FOOD SECURITY (Critical GCC chain)
  // ═══════════════════════════════════
  { id: 'e122', source: 'eco_shipping', target: 'eco_food',    weight: 0.85, polarity: 1, label: 'food imports', labelAr: 'واردات الغذاء',    animated: true },
  { id: 'e123', source: 'inf_jebel',   target: 'eco_food',     weight: 0.70, polarity: 1, label: 'port intake', labelAr: 'استقبال الموانئ' },
  { id: 'e124', source: 'inf_dammam',  target: 'eco_food',     weight: 0.60, polarity: 1, label: 'port intake', labelAr: 'استقبال الموانئ' },
  { id: 'e125', source: 'geo_hormuz',  target: 'eco_food',     weight: 0.65, polarity: 1, label: 'supply route', labelAr: 'طريق الإمداد',     animated: true },
  { id: 'e126', source: 'eco_food',    target: 'soc_citizens', weight: 0.80, polarity: 1, label: 'food supply', labelAr: 'الإمداد الغذائي' },
  { id: 'e127', source: 'eco_food',    target: 'soc_food_d',   weight: 0.75, polarity: 1, label: 'food availability', labelAr: 'توفر الغذاء' },
  { id: 'e128', source: 'soc_food_d',  target: 'soc_citizens', weight: 0.70, polarity: -1, label: 'food stress', labelAr: 'ضغط غذائي' },
  { id: 'e129', source: 'eco_food',    target: 'soc_expats',   weight: 0.65, polarity: 1, label: 'worker food supply', labelAr: 'إمداد غذاء العمالة' },

  // ═══════════════════════════════════
  // MINISTRY OF ENERGY
  // ═══════════════════════════════════
  { id: 'e130', source: 'gov_energy',  target: 'eco_oil',      weight: 0.85, polarity: 1, label: 'energy policy', labelAr: 'سياسة الطاقة' },
  { id: 'e131', source: 'gov_energy',  target: 'eco_aramco',   weight: 0.80, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e132', source: 'gov_energy',  target: 'eco_fuel',     weight: 0.70, polarity: 1, label: 'fuel policy', labelAr: 'سياسة الوقود' },
  { id: 'e133', source: 'gov_energy',  target: 'inf_power',    weight: 0.65, polarity: 1, label: 'energy supply', labelAr: 'إمداد الطاقة' },

  // ═══════════════════════════════════
  // HOUSING & COST OF LIVING
  // ═══════════════════════════════════
  { id: 'e134', source: 'eco_fuel',    target: 'soc_housing',  weight: 0.55, polarity: 1, label: 'cost driver', labelAr: 'محرك التكاليف' },
  { id: 'e135', source: 'soc_housing', target: 'soc_citizens', weight: 0.60, polarity: 1, label: 'living costs', labelAr: 'تكاليف المعيشة' },

  // ═══════════════════════════════════
  // SENTIMENT → STABILITY → MARKET
  // ═══════════════════════════════════
  { id: 'e148', source: 'soc_media',    target: 'soc_sentiment', weight: 0.70, polarity: 1, label: 'shapes sentiment', labelAr: 'يشكّل المشاعر' },
  { id: 'e149', source: 'soc_social',   target: 'soc_sentiment', weight: 0.65, polarity: 1, label: 'amplifies', labelAr: 'يضخّم' },
  { id: 'e138', source: 'soc_sentiment',target: 'soc_stability', weight: 0.75, polarity: 1, label: 'affects stability', labelAr: 'يؤثر على الاستقرار' },
  { id: 'e139', source: 'soc_stability',target: 'fin_tadawul',   weight: 0.50, polarity: 1, label: 'market confidence', labelAr: 'ثقة السوق' },
  { id: 'e140', source: 'eco_gdp',      target: 'soc_stability', weight: 0.55, polarity: 1, label: 'prosperity signal', labelAr: 'إشارة الرخاء' },
  { id: 'e141', source: 'eco_food',     target: 'soc_stability', weight: 0.65, polarity: 1, label: 'food stability', labelAr: 'استقرار غذائي' },

  // ═══════════════════════════════════
  // LOGISTICS HUB
  // ═══════════════════════════════════
  { id: 'e142', source: 'inf_jebel',    target: 'eco_logistics', weight: 0.85, polarity: 1, label: 'logistics hub', labelAr: 'مركز لوجستي' },
  { id: 'e143', source: 'eco_logistics', target: 'eco_gdp',     weight: 0.50, polarity: 1, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e144', source: 'eco_logistics', target: 'eco_food',    weight: 0.60, polarity: 1, label: 'food distribution', labelAr: 'توزيع الغذاء' },
  { id: 'e145', source: 'inf_dmm',      target: 'eco_logistics', weight: 0.45, polarity: 1, label: 'cargo hub', labelAr: 'مركز شحن' },

  // ── Oil + Hormuz Core Chain ──
  // Shipping Cost → Insurance Risk (disruption raises premiums)
  { id: 'e146', source: 'eco_shipping', target: 'fin_insurers',  weight: 0.80, polarity: 1, label: 'shipping risk drives premiums', labelAr: 'مخاطر الشحن ترفع الأقساط', animated: true },
  // Insurance Risk → Aviation Fuel Cost (higher insurance raises fuel cost)
  { id: 'e147', source: 'fin_insurers', target: 'eco_aviation',  weight: 0.75, polarity: 1, label: 'insurance raises fuel cost', labelAr: 'التأمين يرفع تكلفة الوقود', animated: true },
  // Aviation Cost → Tourism Demand: already exists as e137 (w=0.70, polarity=-1)

  // ── Aviation Phase 2: Extended Chain ──
  // Aviation Fuel Cost → Flight Cost: exists as e15 (w=0.85, p=1)
  // Flight Cost → Travel Demand (higher ticket price → less demand — negative polarity)
  { id: 'e150', source: 'soc_ticket',    target: 'soc_travel_d',           weight: 0.80, polarity: -1, label: 'price suppresses demand',        labelAr: 'السعر يخفض الطلب',           animated: true },
  // Travel Demand → Airport Throughput (less demand → less throughput)
  { id: 'e151', source: 'soc_travel_d',  target: 'inf_airport_throughput', weight: 0.85, polarity: 1,  label: 'demand drives throughput',       labelAr: 'الطلب يحرك حركة المطارات',   animated: true },
  // Airport Throughput → Tourism (less throughput → less tourism)
  { id: 'e152', source: 'inf_airport_throughput', target: 'eco_tourism',   weight: 0.80, polarity: 1,  label: 'throughput drives tourism',      labelAr: 'حركة المطارات تدعم السياحة', animated: true },

  // Airport Throughput → individual airports (fan-out)
  { id: 'e153', source: 'inf_airport_throughput', target: 'inf_ruh', weight: 0.85, polarity: 1, label: 'throughput → RUH', labelAr: 'الحركة → الرياض' },
  { id: 'e154', source: 'inf_airport_throughput', target: 'inf_dxb', weight: 0.90, polarity: 1, label: 'throughput → DXB', labelAr: 'الحركة → دبي' },
  { id: 'e155', source: 'inf_airport_throughput', target: 'inf_doh', weight: 0.80, polarity: 1, label: 'throughput → DOH', labelAr: 'الحركة → الدوحة' },
  { id: 'e156', source: 'inf_airport_throughput', target: 'inf_jed', weight: 0.80, polarity: 1, label: 'throughput → JED', labelAr: 'الحركة → جدة' },
  { id: 'e157', source: 'inf_airport_throughput', target: 'inf_kwi', weight: 0.70, polarity: 1, label: 'throughput → KWI', labelAr: 'الحركة → الكويت' },
  { id: 'e158', source: 'inf_airport_throughput', target: 'inf_auh', weight: 0.75, polarity: 1, label: 'throughput → AUH', labelAr: 'الحركة → أبوظبي' },
  { id: 'e159', source: 'inf_airport_throughput', target: 'inf_bah', weight: 0.60, polarity: 1, label: 'throughput → BAH', labelAr: 'الحركة → البحرين' },
  { id: 'e160', source: 'inf_airport_throughput', target: 'inf_mct', weight: 0.55, polarity: 1, label: 'throughput → MCT', labelAr: 'الحركة → مسقط' },
  { id: 'e161', source: 'inf_airport_throughput', target: 'inf_dmm', weight: 0.65, polarity: 1, label: 'throughput → DMM', labelAr: 'الحركة → الدمام' },

  // Airlines ← Aviation Fuel Cost (fuel cost hits airlines)
  { id: 'e162', source: 'eco_aviation',  target: 'eco_saudia',    weight: 0.80, polarity: 1, label: 'fuel cost → Saudia',   labelAr: 'تكلفة الوقود → السعودية' },
  { id: 'e163', source: 'eco_aviation',  target: 'eco_emirates',  weight: 0.85, polarity: 1, label: 'fuel cost → Emirates', labelAr: 'تكلفة الوقود → الإمارات' },
  { id: 'e164', source: 'eco_aviation',  target: 'eco_qatar_aw',  weight: 0.80, polarity: 1, label: 'fuel cost → Qatar',    labelAr: 'تكلفة الوقود → القطرية' },
  // Airlines → GDP (airline revenue)
  { id: 'e165', source: 'eco_saudia',    target: 'eco_gdp', weight: 0.45, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e166', source: 'eco_emirates',  target: 'eco_gdp', weight: 0.50, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e167', source: 'eco_qatar_aw',  target: 'eco_gdp', weight: 0.40, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  // Airlines ← Airport Throughput (passenger volume)
  { id: 'e168', source: 'inf_airport_throughput', target: 'eco_saudia',   weight: 0.70, polarity: 1, label: 'passengers → Saudia',   labelAr: 'المسافرون → السعودية' },
  { id: 'e169', source: 'inf_airport_throughput', target: 'eco_emirates', weight: 0.80, polarity: 1, label: 'passengers → Emirates', labelAr: 'المسافرون → الإمارات' },
  { id: 'e170', source: 'inf_airport_throughput', target: 'eco_qatar_aw', weight: 0.70, polarity: 1, label: 'passengers → Qatar',    labelAr: 'المسافرون → القطرية' },

  // Airlines → Hub Airports (airline operations drive hub traffic)
  { id: 'e171', source: 'eco_saudia',   target: 'inf_ruh', weight: 0.80, polarity: 1, label: 'Saudia hub → RUH',   labelAr: 'مركز السعودية → الرياض',   animated: true },
  { id: 'e172', source: 'eco_emirates',  target: 'inf_dxb', weight: 0.90, polarity: 1, label: 'Emirates hub → DXB', labelAr: 'مركز الإمارات → دبي',    animated: true },
  { id: 'e173', source: 'eco_qatar_aw',  target: 'inf_doh', weight: 0.85, polarity: 1, label: 'Qatar hub → DOH',   labelAr: 'مركز القطرية → الدوحة',   animated: true },
  // Saudia also serves JED (Hajj gateway)
  { id: 'e174', source: 'eco_saudia',   target: 'inf_jed', weight: 0.75, polarity: 1, label: 'Saudia → JED',       labelAr: 'السعودية → جدة',          animated: true },

  // ── Additional Airlines ──
  // Fuel cost → airlines
  { id: 'e175', source: 'eco_aviation', target: 'eco_kw_airways', weight: 0.70, polarity: 1, label: 'fuel cost → Kuwait Airways', labelAr: 'تكلفة الوقود → الكويتية' },
  { id: 'e176', source: 'eco_aviation', target: 'eco_gulf_air',   weight: 0.65, polarity: 1, label: 'fuel cost → Gulf Air',      labelAr: 'تكلفة الوقود → طيران الخليج' },
  { id: 'e177', source: 'eco_aviation', target: 'eco_oman_air',   weight: 0.60, polarity: 1, label: 'fuel cost → Oman Air',      labelAr: 'تكلفة الوقود → الطيران العماني' },
  // Airlines → hub airports
  { id: 'e178', source: 'eco_kw_airways', target: 'inf_kwi', weight: 0.80, polarity: 1, label: 'Kuwait Airways hub → KWI', labelAr: 'الكويتية → الكويت', animated: true },
  { id: 'e179', source: 'eco_gulf_air',   target: 'inf_bah', weight: 0.80, polarity: 1, label: 'Gulf Air hub → BAH',      labelAr: 'طيران الخليج → البحرين', animated: true },
  { id: 'e180', source: 'eco_oman_air',   target: 'inf_mct', weight: 0.80, polarity: 1, label: 'Oman Air hub → MCT',      labelAr: 'الطيران العماني → مسقط', animated: true },
  // Throughput → airlines
  { id: 'e181', source: 'inf_airport_throughput', target: 'eco_kw_airways', weight: 0.60, polarity: 1, label: 'passengers → Kuwait Airways', labelAr: 'المسافرون → الكويتية' },
  { id: 'e182', source: 'inf_airport_throughput', target: 'eco_gulf_air',   weight: 0.55, polarity: 1, label: 'passengers → Gulf Air',      labelAr: 'المسافرون → طيران الخليج' },
  { id: 'e183', source: 'inf_airport_throughput', target: 'eco_oman_air',   weight: 0.50, polarity: 1, label: 'passengers → Oman Air',      labelAr: 'المسافرون → الطيران العماني' },
  // Airlines → GDP
  { id: 'e184', source: 'eco_kw_airways', target: 'eco_gdp', weight: 0.30, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e185', source: 'eco_gulf_air',   target: 'eco_gdp', weight: 0.25, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e186', source: 'eco_oman_air',   target: 'eco_gdp', weight: 0.25, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },

  // ── Aviation Sector Stress (aggregate) ──
  // Inputs: fuel cost, insurance risk, flight cost, throughput decline
  { id: 'e187', source: 'eco_aviation',          target: 'eco_av_stress', weight: 0.85, polarity: 1,  label: 'fuel cost → stress',       labelAr: 'تكلفة الوقود → الضغط' },
  { id: 'e188', source: 'fin_insurers',           target: 'eco_av_stress', weight: 0.70, polarity: 1,  label: 'insurance → stress',       labelAr: 'التأمين → الضغط' },
  { id: 'e189', source: 'soc_ticket',             target: 'eco_av_stress', weight: 0.65, polarity: 1,  label: 'flight cost → stress',     labelAr: 'تكلفة الرحلات → الضغط' },
  { id: 'e190', source: 'inf_airport_throughput',  target: 'eco_av_stress', weight: 0.60, polarity: -1, label: 'throughput drop → stress',  labelAr: 'انخفاض الحركة → الضغط' },
  // Stress → GDP
  { id: 'e191', source: 'eco_av_stress', target: 'eco_gdp', weight: 0.50, polarity: -1, label: 'aviation stress drags GDP', labelAr: 'ضغط الطيران يضغط الناتج' },
]

/* ════════════════════════════════════════════════
   SCENARIOS — 18 Strategic GCC Command Scenarios
   Grouped: Geopolitics · Aviation · Ports · Finance · Utilities · Sovereign
   ════════════════════════════════════════════════ */
export const gccScenarios: GCCScenario[] = [
  // ═══════════════════════════════════════════════
  // GROUP 1: GEOPOLITICS (3 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'hormuz_closure',
    title: 'Strait of Hormuz Closure',
    titleAr: 'إغلاق مضيق هرمز',
    description: 'Full or partial closure of the Strait of Hormuz disrupting 21% of global oil transit, triggering multi-sector cascade across the GCC.',
    descriptionAr: 'إغلاق كلي أو جزئي لمضيق هرمز يعطّل 21% من عبور النفط العالمي، مما يُطلق تسلسل تأثيرات متعدد القطاعات عبر دول الخليج.',
    category: 'geopolitics',
    country: 'GCC',
    group: 'geopolitics',
    thesis: 'A Hormuz blockade does not just cut oil — it reprices every insurance contract, reroutes every ship, and grounds aviation within 72 hours.',
    thesisAr: 'إغلاق هرمز لا يقطع النفط فحسب — بل يعيد تسعير كل عقد تأمين، ويغير مسار كل سفينة، ويوقف الطيران خلال 72 ساعة.',
    sectors: ['oil', 'shipping', 'insurance', 'aviation', 'tourism', 'GDP'],
    keyEntities: ['geo_hormuz', 'eco_oil', 'eco_shipping', 'fin_insurers', 'eco_aviation', 'eco_tourism', 'eco_gdp'],
    mapModes: ['globe', 'shipping', 'heat', 'corridor'],
    formulaTags: ['F_flow', 'oil_export', 'shipping_cost', 'insurance_risk', 'aviation_cost', 'tourism_revenue', 'gdp_loss'],
    severityDefault: 0.90,
    timeHorizon: '72 hours – 30 days',
    timeHorizonAr: '72 ساعة – 30 يوم',
    expectedPropagationDomains: ['geography', 'infrastructure', 'economy', 'finance', 'society'],
    simulationType: 'deterministic',
    chokePoints: ['geo_hormuz'],
    geospatialAnchors: ['geo_hormuz', 'inf_jebel', 'inf_dammam', 'eco_oil'],
    shocks: [{ nodeId: 'geo_hormuz', impact: 0.90 }],
  },
  {
    id: 'us_iran_escalation',
    title: 'Limited US\u2013Iran Escalation',
    titleAr: 'تصعيد أمريكي–إيراني محدود',
    description: 'A contained military exchange near the Strait triggers insurance repricing, capital flight, and aviation rerouting without full blockade.',
    descriptionAr: 'تبادل عسكري محدود بالقرب من المضيق يُطلق إعادة تسعير التأمين وهروب رؤوس الأموال وتغيير مسارات الطيران دون إغلاق كامل.',
    category: 'geopolitics',
    country: 'GCC',
    group: 'geopolitics',
    thesis: 'Even without blockade, proximity of conflict reprices GCC risk by 200\u2013400 bps and diverts 30% of shipping tonnage.',
    thesisAr: 'حتى بدون إغلاق، قرب الصراع يعيد تسعير مخاطر الخليج بـ 200-400 نقطة أساس ويحوّل 30% من حمولة الشحن.',
    sectors: ['insurance', 'shipping', 'aviation', 'finance', 'GDP'],
    keyEntities: ['geo_hormuz', 'fin_insurers', 'fin_reinsure', 'eco_shipping', 'eco_aviation', 'fin_tadawul'],
    mapModes: ['globe', 'shipping', 'flights', 'heat'],
    formulaTags: ['insurance_risk', 'shipping_cost', 'aviation_cost', 'capital_flight'],
    severityDefault: 0.65,
    timeHorizon: '48 hours – 14 days',
    timeHorizonAr: '48 ساعة – 14 يوم',
    expectedPropagationDomains: ['geography', 'economy', 'finance'],
    simulationType: 'probabilistic',
    chokePoints: ['geo_hormuz'],
    geospatialAnchors: ['geo_hormuz', 'fin_tadawul', 'eco_shipping'],
    shocks: [
      { nodeId: 'geo_hormuz', impact: 0.55 },
      { nodeId: 'fin_insurers', impact: 0.70 },
      { nodeId: 'fin_reinsure', impact: 0.65 },
      { nodeId: 'eco_shipping', impact: 0.40 },
    ],
  },
  {
    id: 'military_repositioning',
    title: 'Military Repositioning in the Gulf',
    titleAr: 'إعادة تموضع عسكري في الخليج',
    description: 'Large-scale military movement near GCC waters triggers precautionary shipping rerouting, port delays, and airspace restrictions.',
    descriptionAr: 'تحركات عسكرية واسعة بالقرب من مياه الخليج تُطلق تحويل مسارات الشحن الاحترازية وتأخيرات الموانئ وتقييد المجال الجوي.',
    category: 'geopolitics',
    country: 'GCC',
    group: 'geopolitics',
    thesis: 'Military posturing without engagement still disrupts 15\u201320% of port throughput and triggers precautionary airspace closures.',
    thesisAr: 'الاستعراض العسكري بدون اشتباك يعطّل 15-20% من طاقة الموانئ ويُطلق إغلاقات جوية احترازية.',
    sectors: ['shipping', 'aviation', 'ports', 'insurance'],
    keyEntities: ['geo_hormuz', 'inf_jebel', 'inf_khalifa', 'eco_shipping', 'eco_aviation', 'inf_airport_throughput'],
    mapModes: ['globe', 'shipping', 'flights', 'corridor'],
    formulaTags: ['shipping_cost', 'port_throughput', 'aviation_cost', 'insurance_risk'],
    severityDefault: 0.50,
    timeHorizon: '1 – 21 days',
    timeHorizonAr: '1 – 21 يوم',
    expectedPropagationDomains: ['geography', 'infrastructure', 'economy'],
    simulationType: 'deterministic',
    chokePoints: ['geo_hormuz'],
    geospatialAnchors: ['geo_hormuz', 'inf_jebel', 'inf_khalifa', 'inf_dammam'],
    shocks: [
      { nodeId: 'geo_hormuz', impact: 0.40 },
      { nodeId: 'eco_shipping', impact: 0.50 },
      { nodeId: 'inf_jebel', impact: 0.35 },
      { nodeId: 'inf_airport_throughput', impact: -0.30 },
    ],
  },

  // ═══════════════════════════════════════════════
  // GROUP 2: AVIATION (3 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'airspace_restriction',
    title: 'GCC Airspace Restriction',
    titleAr: 'تقييد المجال الجوي الخليجي',
    description: 'Partial GCC airspace closure forces rerouting of international flights, increasing fuel burn, ticket prices, and airline stress.',
    descriptionAr: 'إغلاق جزئي للمجال الجوي الخليجي يفرض تغيير مسارات الرحلات الدولية، مما يزيد استهلاك الوقود وأسعار التذاكر وضغط شركات الطيران.',
    category: 'economy',
    country: 'GCC',
    group: 'aviation',
    thesis: 'GCC airspace carries 40% of East-West air traffic. Restrictions cascade into global airline economics within 48 hours.',
    thesisAr: 'المجال الجوي الخليجي يحمل 40% من حركة الطيران بين الشرق والغرب. القيود تتسلسل إلى اقتصاديات الطيران العالمي خلال 48 ساعة.',
    sectors: ['aviation', 'tourism', 'airports', 'GDP'],
    keyEntities: ['eco_aviation', 'eco_saudia', 'eco_emirates', 'eco_qatar_aw', 'inf_airport_throughput', 'eco_tourism'],
    mapModes: ['flights', 'globe', 'heat'],
    formulaTags: ['aviation_cost', 'flight_cost', 'travel_demand', 'airport_throughput', 'aviation_stress'],
    severityDefault: 0.70,
    timeHorizon: '24 hours – 14 days',
    timeHorizonAr: '24 ساعة – 14 يوم',
    expectedPropagationDomains: ['infrastructure', 'economy', 'society'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['inf_dxb', 'inf_doh', 'inf_ruh', 'inf_auh'],
    shocks: [
      { nodeId: 'eco_aviation', impact: 0.75 },
      { nodeId: 'inf_airport_throughput', impact: -0.60 },
      { nodeId: 'eco_saudia', impact: -0.50 },
      { nodeId: 'eco_emirates', impact: -0.55 },
      { nodeId: 'eco_qatar_aw', impact: -0.50 },
    ],
  },
  {
    id: 'hajj_disruption',
    title: 'Hajj / Umrah Season Disruption',
    titleAr: 'تعطل موسم الحج والعمرة',
    description: 'Major disruption to Hajj season affecting 2M+ pilgrims, cascading through aviation, tourism revenue, JED airport operations, and Saudi GDP.',
    descriptionAr: 'تعطل كبير لموسم الحج يؤثر على أكثر من مليوني حاج، يتسلسل عبر الطيران وإيرادات السياحة وعمليات مطار جدة والناتج المحلي السعودي.',
    category: 'society',
    country: 'Saudi Arabia',
    group: 'aviation',
    thesis: 'Hajj is Saudi Arabia\'s second-largest revenue event. Disruption eliminates $12B+ in seasonal GDP and strands millions across 3 airports.',
    thesisAr: 'الحج ثاني أكبر حدث إيرادي للسعودية. التعطل يلغي أكثر من 12 مليار دولار من الناتج الموسمي ويُعلّق الملايين عبر 3 مطارات.',
    sectors: ['aviation', 'tourism', 'airports', 'society', 'GDP'],
    keyEntities: ['soc_hajj', 'inf_jed', 'eco_saudia', 'eco_tourism', 'soc_travel_d', 'eco_gdp'],
    mapModes: ['flights', 'globe', 'heat', 'corridor'],
    formulaTags: ['travel_demand', 'airport_throughput', 'tourism_revenue', 'gdp_loss'],
    severityDefault: 0.85,
    timeHorizon: '7 – 45 days',
    timeHorizonAr: '7 – 45 يوم',
    expectedPropagationDomains: ['infrastructure', 'economy', 'society'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['soc_hajj', 'inf_jed', 'inf_ruh', 'inf_dmm'],
    shocks: [
      { nodeId: 'soc_hajj', impact: 0.90 },
      { nodeId: 'inf_jed', impact: 0.75 },
      { nodeId: 'soc_travel_d', impact: 0.65 },
    ],
  },
  {
    id: 'flight_rerouting',
    title: 'Flight Re-Routing under Regional Conflict',
    titleAr: 'تحويل مسارات الطيران تحت صراع إقليمي',
    description: 'Active conflict forces airlines to avoid GCC airspace, adding 2-4 hours to East-West routes and spiking fuel and ticket costs.',
    descriptionAr: 'صراع نشط يجبر شركات الطيران على تجنب المجال الجوي الخليجي، مما يضيف 2-4 ساعات للرحلات بين الشرق والغرب ويرفع تكاليف الوقود والتذاكر.',
    category: 'economy',
    country: 'GCC',
    group: 'aviation',
    thesis: 'Re-routing costs $8M/day per major airline. Six GCC carriers face simultaneous margin collapse while airports lose transit revenue.',
    thesisAr: 'تكلفة تغيير المسارات 8 ملايين دولار/يوم لكل شركة طيران كبرى. ست شركات خليجية تواجه انهيار هوامش متزامن بينما تفقد المطارات إيرادات العبور.',
    sectors: ['aviation', 'fuel', 'airports', 'tourism'],
    keyEntities: ['eco_aviation', 'eco_fuel', 'eco_emirates', 'eco_qatar_aw', 'eco_saudia', 'eco_av_stress'],
    mapModes: ['flights', 'globe', 'heat'],
    formulaTags: ['aviation_cost', 'flight_cost', 'aviation_stress', 'travel_demand'],
    severityDefault: 0.60,
    timeHorizon: '1 – 30 days',
    timeHorizonAr: '1 – 30 يوم',
    expectedPropagationDomains: ['economy', 'infrastructure', 'society'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['inf_dxb', 'inf_doh', 'inf_ruh', 'inf_auh', 'inf_bah', 'inf_mct'],
    shocks: [
      { nodeId: 'eco_aviation', impact: 0.65 },
      { nodeId: 'eco_fuel', impact: 0.55 },
      { nodeId: 'eco_av_stress', impact: 0.70 },
      { nodeId: 'inf_airport_throughput', impact: -0.40 },
    ],
  },

  // ═══════════════════════════════════════════════
  // GROUP 3: PORTS & SUPPLY CHAINS (3 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'jebel_ali_disruption',
    title: 'Jebel Ali Port Disruption',
    titleAr: 'تعطل ميناء جبل علي',
    description: 'Major disruption at Jebel Ali Port affecting 30% of Middle East trade volume, cascading through logistics, insurance, and re-export economy.',
    descriptionAr: 'تعطل كبير في ميناء جبل علي يؤثر على 30% من حجم تجارة الشرق الأوسط، يتسلسل عبر الخدمات اللوجستية والتأمين واقتصاد إعادة التصدير.',
    category: 'economy',
    country: 'UAE',
    group: 'ports_supply',
    thesis: 'Jebel Ali handles 14.7M TEU/year. A 2-week shutdown cascades into $4.2B in trade delays and triggers regional port congestion.',
    thesisAr: 'ميناء جبل علي يتعامل مع 14.7 مليون حاوية/سنة. توقف أسبوعين يتسلسل إلى 4.2 مليار دولار تأخيرات تجارية ويُطلق ازدحام موانئ إقليمي.',
    sectors: ['shipping', 'logistics', 'insurance', 'trade', 'GDP'],
    keyEntities: ['inf_jebel', 'eco_shipping', 'eco_logistics', 'fin_insurers', 'eco_gdp'],
    mapModes: ['shipping', 'globe', 'heat', 'corridor'],
    formulaTags: ['port_throughput', 'shipping_cost', 'insurance_risk', 'gdp_loss'],
    severityDefault: 0.80,
    timeHorizon: '3 – 21 days',
    timeHorizonAr: '3 – 21 يوم',
    expectedPropagationDomains: ['infrastructure', 'economy', 'finance'],
    simulationType: 'deterministic',
    chokePoints: ['inf_jebel'],
    geospatialAnchors: ['inf_jebel', 'inf_khalifa', 'inf_hamad', 'eco_logistics'],
    shocks: [
      { nodeId: 'inf_jebel', impact: 0.85 },
      { nodeId: 'eco_shipping', impact: 0.70 },
    ],
  },
  {
    id: 'gcc_port_congestion',
    title: 'GCC Port Congestion Crisis',
    titleAr: 'أزمة ازدحام الموانئ الخليجية',
    description: 'Simultaneous congestion across GCC ports due to rerouted global shipping, increasing dwell times, insurance costs, and food import delays.',
    descriptionAr: 'ازدحام متزامن عبر موانئ الخليج بسبب تحويل مسارات الشحن العالمي، مما يزيد أوقات الانتظار وتكاليف التأمين وتأخيرات استيراد الغذاء.',
    category: 'economy',
    country: 'GCC',
    group: 'ports_supply',
    thesis: 'GCC ports operate at 85% capacity. A 15% surge in rerouted vessels creates cascading delays that take 45+ days to clear.',
    thesisAr: 'موانئ الخليج تعمل بطاقة 85%. زيادة 15% في السفن المحوّلة تُنشئ تأخيرات متتالية تحتاج 45+ يوماً للتطهير.',
    sectors: ['shipping', 'ports', 'food', 'logistics', 'insurance'],
    keyEntities: ['inf_jebel', 'inf_dammam', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'eco_shipping', 'eco_food'],
    mapModes: ['shipping', 'globe', 'heat'],
    formulaTags: ['port_throughput', 'shipping_cost', 'food_stress', 'insurance_risk'],
    severityDefault: 0.60,
    timeHorizon: '7 – 45 days',
    timeHorizonAr: '7 – 45 يوم',
    expectedPropagationDomains: ['infrastructure', 'economy', 'society'],
    simulationType: 'probabilistic',
    chokePoints: ['inf_jebel', 'inf_dammam'],
    geospatialAnchors: ['inf_jebel', 'inf_dammam', 'inf_hamad', 'inf_khalifa', 'inf_shuwaikh', 'inf_sohar'],
    shocks: [
      { nodeId: 'inf_jebel', impact: 0.55 },
      { nodeId: 'inf_dammam', impact: 0.50 },
      { nodeId: 'inf_hamad', impact: 0.45 },
      { nodeId: 'inf_khalifa', impact: 0.40 },
      { nodeId: 'inf_shuwaikh', impact: 0.40 },
      { nodeId: 'eco_shipping', impact: 0.55 },
    ],
  },
  {
    id: 'food_security_shock',
    title: 'Gulf Food Security Shock',
    titleAr: 'صدمة الأمن الغذائي الخليجي',
    description: 'Global grain supply disruption combined with Hormuz shipping bottleneck. GCC imports 85% of food — cascading through ports, cost of living, and social stability.',
    descriptionAr: 'تعطل إمدادات الحبوب العالمية مع اختناق شحن هرمز. دول الخليج تستورد 85% من الغذاء — يتسلسل عبر الموانئ وتكلفة المعيشة والاستقرار الاجتماعي.',
    category: 'economy',
    country: 'GCC',
    group: 'ports_supply',
    thesis: 'GCC imports 85% of calories. A 3-week shipping disruption creates 40-day food buffer depletion and triggers social instability signals.',
    thesisAr: 'دول الخليج تستورد 85% من السعرات الحرارية. تعطل شحن 3 أسابيع يستنفد المخزون الغذائي خلال 40 يوماً ويُطلق إشارات عدم استقرار اجتماعي.',
    sectors: ['food', 'shipping', 'society', 'ports', 'stability'],
    keyEntities: ['eco_food', 'soc_food_d', 'eco_shipping', 'geo_hormuz', 'soc_stability', 'soc_housing'],
    mapModes: ['shipping', 'globe', 'heat'],
    formulaTags: ['food_stress', 'shipping_cost', 'port_throughput'],
    severityDefault: 0.80,
    timeHorizon: '14 – 60 days',
    timeHorizonAr: '14 – 60 يوم',
    expectedPropagationDomains: ['geography', 'infrastructure', 'economy', 'society'],
    simulationType: 'hybrid',
    chokePoints: ['geo_hormuz'],
    geospatialAnchors: ['geo_hormuz', 'inf_jebel', 'inf_dammam', 'eco_food'],
    shocks: [
      { nodeId: 'eco_food', impact: 0.90 },
      { nodeId: 'eco_shipping', impact: 0.60 },
      { nodeId: 'geo_hormuz', impact: 0.50 },
    ],
  },

  // ═══════════════════════════════════════════════
  // GROUP 4: FINANCE & MARKETS (3 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'liquidity_stress',
    title: 'GCC Liquidity Stress',
    titleAr: 'ضغط السيولة الخليجي',
    description: 'Oil revenue collapse triggers sovereign deposit withdrawal, creating GCC-wide banking liquidity crunch affecting commercial lending and business credit.',
    descriptionAr: 'انهيار إيرادات النفط يُطلق سحب الودائع السيادية، مما يخلق أزمة سيولة مصرفية خليجية تؤثر على الإقراض التجاري والائتمان.',
    category: 'finance',
    country: 'GCC',
    group: 'finance_markets',
    thesis: 'GCC banks hold 60% sovereign deposits. A coordinated withdrawal triggers a liquidity spiral that freezes commercial lending within 5 days.',
    thesisAr: 'البنوك الخليجية تحتفظ بـ 60% ودائع سيادية. سحب منسق يُطلق دوامة سيولة تجمّد الإقراض التجاري خلال 5 أيام.',
    sectors: ['banking', 'finance', 'oil', 'business', 'employment'],
    keyEntities: ['fin_banking', 'fin_sama', 'fin_uae_cb', 'fin_kw_cb', 'eco_oil', 'soc_business'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['banking_stress', 'gdp_loss'],
    severityDefault: 0.75,
    timeHorizon: '3 – 30 days',
    timeHorizonAr: '3 – 30 يوم',
    expectedPropagationDomains: ['finance', 'economy', 'society'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['fin_sama', 'fin_uae_cb', 'fin_tadawul'],
    shocks: [
      { nodeId: 'fin_banking', impact: 0.85 },
      { nodeId: 'fin_sama', impact: 0.60 },
      { nodeId: 'eco_oil', impact: 0.70 },
    ],
  },
  {
    id: 'fx_gold_crypto_shock',
    title: 'FX / Gold / Crypto Market Shock',
    titleAr: 'صدمة أسواق العملات والذهب والعملات الرقمية',
    description: 'Simultaneous dollar strengthening, gold spike, and crypto volatility create cross-asset stress on GCC financial markets and central bank reserves.',
    descriptionAr: 'تعزيز الدولار وارتفاع الذهب وتقلبات العملات الرقمية المتزامنة تخلق ضغطاً عبر الأصول على الأسواق المالية الخليجية واحتياطيات البنوك المركزية.',
    category: 'finance',
    country: 'GCC',
    group: 'finance_markets',
    thesis: 'GCC currencies are dollar-pegged. A rapid dollar move forces central banks to defend pegs while managing $180B in sovereign wealth rebalancing.',
    thesisAr: 'العملات الخليجية مربوطة بالدولار. تحرك سريع للدولار يجبر البنوك المركزية على الدفاع عن الربط مع إدارة 180 مليار دولار إعادة توازن ثروات سيادية.',
    sectors: ['finance', 'banking', 'markets', 'sovereign'],
    keyEntities: ['fin_sama', 'fin_uae_cb', 'fin_kw_cb', 'fin_qa_cb', 'fin_tadawul', 'fin_banking'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['banking_stress', 'gdp_loss'],
    severityDefault: 0.60,
    timeHorizon: '1 – 14 days',
    timeHorizonAr: '1 – 14 يوم',
    expectedPropagationDomains: ['finance', 'economy'],
    simulationType: 'probabilistic',
    chokePoints: [],
    geospatialAnchors: ['fin_sama', 'fin_uae_cb', 'fin_kw_cb', 'fin_qa_cb', 'fin_tadawul'],
    shocks: [
      { nodeId: 'fin_sama', impact: 0.55 },
      { nodeId: 'fin_uae_cb', impact: 0.50 },
      { nodeId: 'fin_kw_cb', impact: 0.45 },
      { nodeId: 'fin_qa_cb', impact: 0.45 },
      { nodeId: 'fin_tadawul', impact: 0.65 },
    ],
  },
  {
    id: 'insurance_repricing',
    title: 'Insurance & Reinsurance Risk Repricing',
    titleAr: 'إعادة تسعير مخاطر التأمين وإعادة التأمين',
    description: 'Reinsurance withdrawal from GCC markets following catastrophic loss event, raising premiums across shipping, aviation, and infrastructure sectors.',
    descriptionAr: 'انسحاب إعادة التأمين من أسواق الخليج بعد حدث خسارة كارثية، مما يرفع أقساط التأمين عبر قطاعات الشحن والطيران والبنية التحتية.',
    category: 'finance',
    country: 'GCC',
    group: 'finance_markets',
    thesis: 'Reinsurers pulling $15B in GCC capacity forces self-insurance, raising operational costs by 30-50% across all logistics sectors.',
    thesisAr: 'سحب شركات إعادة التأمين 15 مليار دولار من طاقة الخليج يفرض التأمين الذاتي، مما يرفع التكاليف التشغيلية 30-50% عبر جميع قطاعات الخدمات اللوجستية.',
    sectors: ['insurance', 'shipping', 'aviation', 'infrastructure'],
    keyEntities: ['fin_reinsure', 'fin_ins_risk', 'fin_insurers', 'eco_shipping', 'eco_aviation'],
    mapModes: ['globe', 'heat', 'shipping', 'flights'],
    formulaTags: ['insurance_risk', 'shipping_cost', 'aviation_cost'],
    severityDefault: 0.75,
    timeHorizon: '7 – 90 days',
    timeHorizonAr: '7 – 90 يوم',
    expectedPropagationDomains: ['finance', 'economy', 'infrastructure'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['fin_insurers', 'fin_reinsure', 'eco_shipping'],
    shocks: [
      { nodeId: 'fin_reinsure', impact: 0.85 },
      { nodeId: 'fin_ins_risk', impact: 0.75 },
    ],
  },

  // ═══════════════════════════════════════════════
  // GROUP 5: UTILITIES & STATE CAPACITY (3 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'gcc_grid_failure',
    title: 'GCC Power Grid Failure',
    titleAr: 'انهيار شبكة الكهرباء الخليجية',
    description: 'Peak summer power grid failure cascading through desalination, telecom infrastructure, business operations, and citizen welfare.',
    descriptionAr: 'انهيار شبكة الكهرباء في ذروة الصيف يتسلسل عبر التحلية والبنية التحتية للاتصالات والعمليات التجارية ورفاهية المواطنين.',
    category: 'infrastructure',
    country: 'GCC',
    group: 'utilities_state',
    thesis: 'GCC power grids run at 95% capacity in summer. A 10% drop cascades into desalination failure within 6 hours, creating a water crisis.',
    thesisAr: 'شبكات الكهرباء الخليجية تعمل بطاقة 95% في الصيف. انخفاض 10% يتسلسل إلى فشل التحلية خلال 6 ساعات، مما يخلق أزمة مياه.',
    sectors: ['power', 'water', 'telecom', 'society', 'business'],
    keyEntities: ['inf_power', 'inf_desal', 'inf_telecom', 'soc_citizens', 'soc_business'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['utility_availability', 'gdp_loss'],
    severityDefault: 0.85,
    timeHorizon: '6 hours – 7 days',
    timeHorizonAr: '6 ساعات – 7 أيام',
    expectedPropagationDomains: ['infrastructure', 'society', 'economy'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['inf_power', 'inf_desal', 'inf_telecom'],
    shocks: [
      { nodeId: 'inf_power', impact: 0.90 },
      { nodeId: 'inf_desal', impact: 0.80 },
      { nodeId: 'inf_telecom', impact: 0.70 },
    ],
  },
  {
    id: 'water_electricity_disruption',
    title: 'Electricity & Water Disruption',
    titleAr: 'تعطل الكهرباء والمياه',
    description: 'Coordinated infrastructure failure affecting power generation and desalination plants, threatening public health and economic activity.',
    descriptionAr: 'فشل بنية تحتية منسق يؤثر على توليد الطاقة ومحطات التحلية، مما يهدد الصحة العامة والنشاط الاقتصادي.',
    category: 'infrastructure',
    country: 'GCC',
    group: 'utilities_state',
    thesis: 'GCC produces 99% of drinking water from desalination. Power failure means water failure means public health emergency within 48 hours.',
    thesisAr: 'دول الخليج تنتج 99% من مياه الشرب من التحلية. انقطاع الكهرباء يعني انقطاع المياه يعني طوارئ صحية عامة خلال 48 ساعة.',
    sectors: ['power', 'water', 'health', 'society', 'stability'],
    keyEntities: ['inf_power', 'inf_desal', 'gov_water', 'soc_citizens', 'soc_stability'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['utility_availability', 'gdp_loss'],
    severityDefault: 0.80,
    timeHorizon: '12 hours – 14 days',
    timeHorizonAr: '12 ساعة – 14 يوم',
    expectedPropagationDomains: ['infrastructure', 'society'],
    simulationType: 'deterministic',
    chokePoints: [],
    geospatialAnchors: ['inf_power', 'inf_desal', 'gov_water'],
    shocks: [
      { nodeId: 'inf_power', impact: 0.85 },
      { nodeId: 'inf_desal', impact: 0.85 },
      { nodeId: 'gov_water', impact: 0.70 },
    ],
  },
  {
    id: 'summer_utility_stress',
    title: 'Summer Utility Stress under Conflict',
    titleAr: 'ضغط المرافق الصيفي تحت الصراع',
    description: 'Peak summer demand combined with regional conflict disrupts fuel supply for power generation, creating cascading utility and social stress.',
    descriptionAr: 'ذروة الطلب الصيفي مع صراع إقليمي تعطّل إمدادات الوقود لتوليد الطاقة، مما يخلق ضغطاً متتالياً على المرافق والمجتمع.',
    category: 'infrastructure',
    country: 'GCC',
    group: 'utilities_state',
    thesis: 'Summer + conflict = double stress on utilities. Fuel supply disruption during peak cooling demand creates cascading failures across the power-water-telecom nexus.',
    thesisAr: 'الصيف + الصراع = ضغط مزدوج على المرافق. تعطل إمدادات الوقود أثناء ذروة طلب التبريد يخلق فشلاً متتالياً عبر ترابط الكهرباء-المياه-الاتصالات.',
    sectors: ['power', 'water', 'fuel', 'telecom', 'society'],
    keyEntities: ['inf_power', 'inf_desal', 'eco_fuel', 'inf_telecom', 'soc_citizens', 'soc_stability', 'geo_hormuz'],
    mapModes: ['globe', 'heat', 'shipping'],
    formulaTags: ['utility_availability', 'shipping_cost', 'gdp_loss'],
    severityDefault: 0.75,
    timeHorizon: '3 – 30 days',
    timeHorizonAr: '3 – 30 يوم',
    expectedPropagationDomains: ['geography', 'infrastructure', 'economy', 'society'],
    simulationType: 'hybrid',
    chokePoints: ['geo_hormuz'],
    geospatialAnchors: ['inf_power', 'inf_desal', 'eco_fuel', 'geo_hormuz'],
    shocks: [
      { nodeId: 'inf_power', impact: 0.75 },
      { nodeId: 'inf_desal', impact: 0.65 },
      { nodeId: 'eco_fuel', impact: 0.70 },
      { nodeId: 'geo_hormuz', impact: 0.45 },
    ],
  },

  // ═══════════════════════════════════════════════
  // GROUP 6: SOVEREIGN / STRATEGIC PROJECTS (2 scenarios)
  // ═══════════════════════════════════════════════
  {
    id: 'vision2030_stress',
    title: 'Vision 2030 Stress under Regional Shock',
    titleAr: 'ضغط رؤية 2030 تحت صدمة إقليمية',
    description: 'Regional instability threatens Vision 2030 investment timeline, affecting tourism corridors, mega projects, FDI flows, and employment targets.',
    descriptionAr: 'عدم الاستقرار الإقليمي يهدد الجدول الزمني لاستثمارات رؤية 2030، مما يؤثر على ممرات السياحة والمشاريع الكبرى وتدفقات الاستثمار الأجنبي وأهداف التوظيف.',
    category: 'economy',
    country: 'Saudi Arabia',
    group: 'sovereign_projects',
    thesis: 'Vision 2030 depends on $1.3T in committed investment. Regional conflict delays 20-30% of project timelines and diverts sovereign capital to defense.',
    thesisAr: 'رؤية 2030 تعتمد على 1.3 تريليون دولار استثمارات ملتزمة. الصراع الإقليمي يؤخر 20-30% من الجداول الزمنية للمشاريع ويحوّل رأس المال السيادي للدفاع.',
    sectors: ['tourism', 'GDP', 'employment', 'aviation', 'finance'],
    keyEntities: ['eco_tourism', 'eco_gdp', 'soc_employment', 'gov_tourism', 'fin_sama', 'eco_saudia'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['tourism_revenue', 'gdp_loss', 'aviation_stress'],
    severityDefault: 0.65,
    timeHorizon: '30 – 365 days',
    timeHorizonAr: '30 – 365 يوم',
    expectedPropagationDomains: ['economy', 'finance', 'society'],
    simulationType: 'probabilistic',
    chokePoints: [],
    geospatialAnchors: ['eco_tourism', 'eco_gdp', 'fin_sama', 'gov_tourism'],
    shocks: [
      { nodeId: 'eco_tourism', impact: -0.65 },
      { nodeId: 'soc_employment', impact: -0.50 },
      { nodeId: 'fin_sama', impact: 0.40 },
      { nodeId: 'eco_gdp', impact: -0.55 },
    ],
  },
  {
    id: 'mega_projects_pressure',
    title: 'Mega Projects & Tourism Corridor Pressure',
    titleAr: 'ضغط المشاريع الكبرى وممرات السياحة',
    description: 'Construction delays, labor shortages, and financing stress on GCC mega projects create ripple effects through employment, housing, and economic growth.',
    descriptionAr: 'تأخيرات البناء ونقص العمالة وضغط التمويل على المشاريع الكبرى الخليجية تخلق تأثيرات متموجة عبر التوظيف والإسكان والنمو الاقتصادي.',
    category: 'economy',
    country: 'GCC',
    group: 'sovereign_projects',
    thesis: 'GCC mega projects employ 3M+ workers. Construction delays cascade into housing oversupply, labor unrest, and banking exposure to project finance.',
    thesisAr: 'المشاريع الكبرى الخليجية توظف أكثر من 3 ملايين عامل. تأخيرات البناء تتسلسل إلى فائض إسكان واضطرابات عمالية وتعرض بنكي لتمويل المشاريع.',
    sectors: ['employment', 'housing', 'tourism', 'banking', 'GDP'],
    keyEntities: ['soc_employment', 'soc_housing', 'soc_expats', 'eco_tourism', 'fin_banking', 'eco_gdp'],
    mapModes: ['globe', 'heat'],
    formulaTags: ['banking_stress', 'gdp_loss', 'tourism_revenue'],
    severityDefault: 0.55,
    timeHorizon: '90 – 365 days',
    timeHorizonAr: '90 – 365 يوم',
    expectedPropagationDomains: ['economy', 'finance', 'society'],
    simulationType: 'probabilistic',
    chokePoints: [],
    geospatialAnchors: ['eco_tourism', 'soc_employment', 'soc_housing', 'fin_banking'],
    shocks: [
      { nodeId: 'soc_employment', impact: -0.55 },
      { nodeId: 'soc_housing', impact: 0.50 },
      { nodeId: 'soc_expats', impact: -0.45 },
      { nodeId: 'fin_banking', impact: 0.40 },
      { nodeId: 'eco_tourism', impact: -0.45 },
    ],
  },
]

/* ════════════════════════════════════════════════
   LAYER METADATA — for layout & styling
   ════════════════════════════════════════════════ */
export const layerMeta: Record<GCCLayer, { label: string; labelAr: string; color: string; yBase: number }> = {
  geography:      { label: 'Geography',      labelAr: 'الجغرافيا',       color: '#2DD4A0', yBase: 40  },
  infrastructure: { label: 'Infrastructure', labelAr: 'البنية التحتية',  color: '#F5A623', yBase: 170 },
  economy:        { label: 'Economy',        labelAr: 'الاقتصاد',        color: '#5B7BF8', yBase: 310 },
  finance:        { label: 'Finance',        labelAr: 'المالية',          color: '#A78BFA', yBase: 450 },
  society:        { label: 'Society',        labelAr: 'المجتمع',          color: '#EF5454', yBase: 580 },
}

/* ════════════════════════════════════════════════
   GRAPH — GraphNode/GraphEdge conversion
   ════════════════════════════════════════════════ */
export function gccNodesToGraphNodes(nodes: GCCNode[]): { id: string; label: string; type: string; weight: number; layer: GCCLayer }[] {
  return nodes.map(n => ({
    id: n.id,
    label: n.label,
    type: n.type,
    weight: n.weight,
    layer: n.layer,
  }))
}

export function gccEdgesToGraphEdges(edges: GCCEdge[]): { id: string; source: string; target: string; label: string; animated?: boolean }[] {
  return edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: e.animated,
  }))
}
