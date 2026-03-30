/* ═══════════════════════════════════════════════════════════════
   GCC Reality Graph — 5-Layer Causal Dependency Model v3.0
   ═══════════════════════════════════════════════════════════════
   Layer 1: Geography   (GCC countries + chokepoints)
   Layer 2: Infrastructure (airports, ports)
   Layer 3: Economy     (oil, logistics, aviation)
   Layer 4: Finance     (banks, insurance, reinsurance)
   Layer 5: Society     (population, media, sentiment)
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

export interface GCCScenario {
  id: string
  title: string
  titleAr: string
  description: string
  descriptionAr: string
  category: string
  categoryAr: string
  country: string
  countryAr: string
  shocks: { nodeId: string; impact: number }[]
}

/* ════════════════════════════════════════════════
   NODES — 35 real GCC entities across 5 layers
   ════════════════════════════════════════════════ */
export const gccNodes: GCCNode[] = [
  // ── Layer 1: Geography ──
  { id: 'geo_sa',      label: 'Saudi Arabia',       labelAr: 'السعودية',         layer: 'geography', type: 'Region',       lat: 24.7136, lng: 46.6753, weight: 0.95, sensitivity: 0.3,  value: 0.95 },
  { id: 'geo_uae',     label: 'UAE',                labelAr: 'الإمارات',          layer: 'geography', type: 'Region',       lat: 25.2048, lng: 55.2708, weight: 0.90, sensitivity: 0.3,  value: 0.90 },
  { id: 'geo_kw',      label: 'Kuwait',             labelAr: 'الكويت',           layer: 'geography', type: 'Region',       lat: 29.3759, lng: 47.9774, weight: 0.75, sensitivity: 0.35, value: 0.75 },
  { id: 'geo_qa',      label: 'Qatar',              labelAr: 'قطر',              layer: 'geography', type: 'Region',       lat: 25.2854, lng: 51.5310, weight: 0.80, sensitivity: 0.3,  value: 0.80 },
  { id: 'geo_om',      label: 'Oman',               labelAr: 'عُمان',            layer: 'geography', type: 'Region',       lat: 23.5880, lng: 58.3829, weight: 0.65, sensitivity: 0.4,  value: 0.65 },
  { id: 'geo_bh',      label: 'Bahrain',            labelAr: 'البحرين',          layer: 'geography', type: 'Region',       lat: 26.0667, lng: 50.5577, weight: 0.60, sensitivity: 0.45, value: 0.60 },
  { id: 'geo_hormuz',  label: 'Strait of Hormuz',   labelAr: 'مضيق هرمز',        layer: 'geography', type: 'Event',        lat: 26.5944, lng: 56.4667, weight: 0.98, sensitivity: 0.1,  value: 0.98 },

  // ── Layer 2: Infrastructure ──
  { id: 'inf_ruh',     label: 'RUH Airport',        labelAr: 'مطار الرياض',       layer: 'infrastructure', type: 'Organization', lat: 24.9578, lng: 46.6989, weight: 0.80, sensitivity: 0.5,  value: 0.80 },
  { id: 'inf_dxb',     label: 'DXB Airport',        labelAr: 'مطار دبي',         layer: 'infrastructure', type: 'Organization', lat: 25.2532, lng: 55.3657, weight: 0.88, sensitivity: 0.5,  value: 0.88 },
  { id: 'inf_kwi',     label: 'KWI Airport',        labelAr: 'مطار الكويت',       layer: 'infrastructure', type: 'Organization', lat: 29.2266, lng: 47.9689, weight: 0.65, sensitivity: 0.55, value: 0.65 },
  { id: 'inf_doh',     label: 'DOH Airport',        labelAr: 'مطار الدوحة',       layer: 'infrastructure', type: 'Organization', lat: 25.2731, lng: 51.6081, weight: 0.75, sensitivity: 0.5,  value: 0.75 },
  { id: 'inf_jebel',   label: 'Jebel Ali Port',     labelAr: 'ميناء جبل علي',     layer: 'infrastructure', type: 'Organization', lat: 24.9857, lng: 55.0272, weight: 0.92, sensitivity: 0.6,  value: 0.92 },
  { id: 'inf_dammam',  label: 'Dammam Port',        labelAr: 'ميناء الدمام',      layer: 'infrastructure', type: 'Organization', lat: 26.4473, lng: 50.1014, weight: 0.78, sensitivity: 0.6,  value: 0.78 },
  { id: 'inf_doha_p',  label: 'Doha Port',          labelAr: 'ميناء الدوحة',      layer: 'infrastructure', type: 'Organization', lat: 25.2960, lng: 51.5488, weight: 0.60, sensitivity: 0.55, value: 0.60 },

  // ── Layer 3: Economy ──
  { id: 'eco_oil',     label: 'Oil Export',          labelAr: 'صادرات النفط',      layer: 'economy', type: 'Topic',         lat: 26.3000, lng: 50.2000, weight: 0.96, sensitivity: 0.7,  value: 0.96 },
  { id: 'eco_aramco',  label: 'Aramco',             labelAr: 'أرامكو',           layer: 'economy', type: 'Organization',  lat: 26.3175, lng: 50.2083, weight: 0.95, sensitivity: 0.5,  value: 0.95 },
  { id: 'eco_adnoc',   label: 'ADNOC',              labelAr: 'أدنوك',            layer: 'economy', type: 'Organization',  lat: 24.4539, lng: 54.3773, weight: 0.88, sensitivity: 0.5,  value: 0.88 },
  { id: 'eco_kpc',     label: 'KPC',                labelAr: 'مؤسسة البترول الكويتية', layer: 'economy', type: 'Organization', lat: 29.3375, lng: 48.0013, weight: 0.78, sensitivity: 0.55, value: 0.78 },
  { id: 'eco_shipping',label: 'Shipping & Logistics',labelAr: 'الشحن والخدمات اللوجستية', layer: 'economy', type: 'Topic', lat: 25.0000, lng: 55.1000, weight: 0.85, sensitivity: 0.65, value: 0.85 },
  { id: 'eco_aviation',label: 'Aviation Sector',     labelAr: 'قطاع الطيران',      layer: 'economy', type: 'Topic',         lat: 25.0657, lng: 55.1713, weight: 0.82, sensitivity: 0.6,  value: 0.82 },
  { id: 'eco_fuel',    label: 'Fuel Cost',           labelAr: 'تكلفة الوقود',      layer: 'economy', type: 'Topic',         lat: 24.4700, lng: 54.3700, weight: 0.88, sensitivity: 0.7,  value: 0.88 },
  { id: 'eco_gdp',     label: 'GCC GDP',            labelAr: 'الناتج المحلي الخليجي', layer: 'economy', type: 'Topic',      lat: 24.4700, lng: 49.0000, weight: 0.90, sensitivity: 0.4,  value: 0.90 },
  // ── Layer 3b: Tourism (new entity) ──
  { id: 'eco_tourism', label: 'Tourism Revenue',     labelAr: 'إيرادات السياحة',    layer: 'economy', type: 'Topic',         lat: 25.1970, lng: 55.2744, weight: 0.78, sensitivity: 0.65, value: 0.78 },

  // ── Layer 4: Finance ──
  { id: 'fin_sama',    label: 'SAMA',               labelAr: 'مؤسسة النقد',       layer: 'finance', type: 'Organization',  lat: 24.6918, lng: 46.6855, weight: 0.92, sensitivity: 0.35, value: 0.92 },
  { id: 'fin_uae_cb',  label: 'UAE Central Bank',   labelAr: 'مصرف الإمارات المركزي', layer: 'finance', type: 'Organization', lat: 24.4872, lng: 54.3613, weight: 0.88, sensitivity: 0.35, value: 0.88 },
  { id: 'fin_kw_cb',   label: 'Kuwait Central Bank',labelAr: 'بنك الكويت المركزي', layer: 'finance', type: 'Organization',  lat: 29.3759, lng: 47.9850, weight: 0.75, sensitivity: 0.4,  value: 0.75 },
  { id: 'fin_insurers',label: 'Insurers',           labelAr: 'شركات التأمين',      layer: 'finance', type: 'Organization',  lat: 24.7500, lng: 46.7200, weight: 0.80, sensitivity: 0.7,  value: 0.80 },
  { id: 'fin_reinsure', label: 'Reinsurers',        labelAr: 'إعادة التأمين',      layer: 'finance', type: 'Organization',  lat: 25.1800, lng: 55.2800, weight: 0.75, sensitivity: 0.65, value: 0.75 },
  { id: 'fin_ins_risk', label: 'Insurance Risk',    labelAr: 'مخاطر التأمين',      layer: 'finance', type: 'Topic',         lat: 25.2200, lng: 55.2600, weight: 0.82, sensitivity: 0.7,  value: 0.82 },
  // ── Layer 4b: Stock exchange (new entity) ──
  { id: 'fin_tadawul', label: 'Tadawul Exchange',   labelAr: 'تداول',             layer: 'finance', type: 'Organization',  lat: 24.6900, lng: 46.6900, weight: 0.85, sensitivity: 0.6,  value: 0.85 },

  // ── Layer 5: Society ──
  { id: 'soc_citizens', label: 'Citizens',          labelAr: 'المواطنون',         layer: 'society', type: 'Person',        lat: 24.7000, lng: 46.7000, weight: 0.85, sensitivity: 0.6,  value: 0.85 },
  { id: 'soc_travelers',label: 'Travelers',         labelAr: 'المسافرون',         layer: 'society', type: 'Person',        lat: 25.2000, lng: 55.3000, weight: 0.70, sensitivity: 0.65, value: 0.70 },
  { id: 'soc_business', label: 'Businesses',        labelAr: 'الشركات',           layer: 'society', type: 'Organization',  lat: 25.0800, lng: 55.1400, weight: 0.80, sensitivity: 0.55, value: 0.80 },
  { id: 'soc_media',    label: 'Media',             labelAr: 'الإعلام',           layer: 'society', type: 'Platform',      lat: 25.2000, lng: 55.2500, weight: 0.82, sensitivity: 0.5,  value: 0.82 },
  { id: 'soc_social',   label: 'Social Platforms',  labelAr: 'المنصات الاجتماعية', layer: 'society', type: 'Platform',     lat: 24.7200, lng: 46.6800, weight: 0.78, sensitivity: 0.4,  value: 0.78 },
  { id: 'soc_travel_d', label: 'Travel Demand',     labelAr: 'الطلب على السفر',    layer: 'society', type: 'Topic',         lat: 25.2500, lng: 55.3500, weight: 0.72, sensitivity: 0.7,  value: 0.72 },
  { id: 'soc_ticket',   label: 'Ticket Price',      labelAr: 'أسعار التذاكر',      layer: 'society', type: 'Topic',         lat: 25.2532, lng: 55.3600, weight: 0.68, sensitivity: 0.75, value: 0.68 },
]

/* ════════════════════════════════════════════════
   EDGES — 53 weighted causal dependencies
   ════════════════════════════════════════════════ */
export const gccEdges: GCCEdge[] = [
  // ── Hormuz → Oil chain ──
  { id: 'e01', source: 'geo_hormuz',  target: 'eco_oil',      weight: 0.95, polarity: 1, label: 'controls export', labelAr: 'يتحكم بالتصدير',   animated: true },
  { id: 'e02', source: 'eco_oil',     target: 'eco_aramco',   weight: 0.90, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e03', source: 'eco_oil',     target: 'eco_adnoc',    weight: 0.85, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e04', source: 'eco_oil',     target: 'eco_kpc',      weight: 0.80, polarity: 1, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e05', source: 'eco_oil',     target: 'eco_shipping',  weight: 0.85, polarity: 1, label: 'shipping volume', labelAr: 'حجم الشحن',  animated: true },
  { id: 'e06', source: 'eco_oil',     target: 'eco_fuel',     weight: 0.88, polarity: 1, label: 'price driver', labelAr: 'محرك الأسعار' },

  // ── Shipping & Logistics chain ──
  { id: 'e07', source: 'eco_shipping', target: 'inf_jebel',   weight: 0.85, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e08', source: 'eco_shipping', target: 'inf_dammam',  weight: 0.78, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e09', source: 'eco_shipping', target: 'inf_doha_p',  weight: 0.60, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e10', source: 'eco_shipping', target: 'fin_ins_risk', weight: 0.80, polarity: 1, label: 'risk exposure', labelAr: 'التعرض للمخاطر',   animated: true },

  // ── Insurance chain ──
  { id: 'e11', source: 'fin_ins_risk', target: 'fin_insurers',  weight: 0.80, polarity: 1, label: 'premium impact', labelAr: 'تأثير الأقساط' },
  { id: 'e12', source: 'fin_ins_risk', target: 'fin_reinsure',  weight: 0.75, polarity: 1, label: 'reinsurance cost', labelAr: 'تكلفة إعادة التأمين' },
  { id: 'e13', source: 'fin_insurers', target: 'soc_business',  weight: 0.65, polarity: 1, label: 'cost pass-through', labelAr: 'تمرير التكاليف' },

  // ── Fuel → Aviation chain ──
  { id: 'e14', source: 'eco_fuel',     target: 'eco_aviation',  weight: 0.90, polarity: 1, label: 'fuel cost', labelAr: 'تكلفة الوقود',       animated: true },
  { id: 'e15', source: 'eco_aviation', target: 'soc_ticket',   weight: 0.85, polarity: 1, label: 'ticket pricing', labelAr: 'تسعير التذاكر' },
  { id: 'e16', source: 'soc_ticket',   target: 'soc_travel_d', weight: 0.70, polarity: -1, label: 'demand inverse', labelAr: 'عكس الطلب' },
  { id: 'e17', source: 'soc_travel_d', target: 'inf_dxb',     weight: 0.80, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e18', source: 'soc_travel_d', target: 'inf_ruh',     weight: 0.70, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e19', source: 'soc_travel_d', target: 'inf_kwi',     weight: 0.55, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e20', source: 'soc_travel_d', target: 'inf_doh',     weight: 0.60, polarity: 1, label: 'passenger flow', labelAr: 'تدفق الركاب' },

  // ── Aviation → GDP ──
  { id: 'e21', source: 'eco_aviation', target: 'eco_gdp',     weight: 0.60, polarity: 1, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e22', source: 'eco_oil',     target: 'eco_gdp',      weight: 0.75, polarity: 1, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e23', source: 'eco_shipping', target: 'eco_gdp',     weight: 0.55, polarity: 1, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },

  // ── Country connections ──
  { id: 'e24', source: 'geo_sa',      target: 'eco_aramco',   weight: 0.95, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e25', source: 'geo_uae',     target: 'eco_adnoc',    weight: 0.90, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e26', source: 'geo_kw',      target: 'eco_kpc',      weight: 0.85, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e27', source: 'geo_sa',      target: 'inf_ruh',      weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e28', source: 'geo_uae',     target: 'inf_dxb',      weight: 0.85, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e29', source: 'geo_uae',     target: 'inf_jebel',    weight: 0.90, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e30', source: 'geo_sa',      target: 'inf_dammam',   weight: 0.78, polarity: 1, label: 'operates', labelAr: 'يشغّل' },

  // ── Finance → Country regulators ──
  { id: 'e31', source: 'fin_sama',    target: 'fin_insurers',  weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e32', source: 'fin_uae_cb',  target: 'fin_insurers',  weight: 0.65, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e33', source: 'fin_kw_cb',   target: 'fin_insurers',  weight: 0.55, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e34', source: 'geo_sa',      target: 'fin_sama',      weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e35', source: 'geo_uae',     target: 'fin_uae_cb',   weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e36', source: 'geo_kw',      target: 'fin_kw_cb',    weight: 0.80, polarity: 1, label: 'governs', labelAr: 'يحكم' },

  // ── Society connections ──
  { id: 'e37', source: 'soc_citizens', target: 'soc_social',   weight: 0.75, polarity: 1, label: 'expresses via', labelAr: 'يعبّر عبر' },
  { id: 'e38', source: 'soc_social',   target: 'soc_media',    weight: 0.70, polarity: 1, label: 'feeds', labelAr: 'يغذي' },
  { id: 'e39', source: 'soc_media',    target: 'soc_citizens', weight: 0.60, polarity: 1, label: 'informs', labelAr: 'يُعلم' },
  { id: 'e40', source: 'eco_fuel',     target: 'soc_citizens', weight: 0.80, polarity: 1, label: 'cost of living', labelAr: 'تكلفة المعيشة' },
  { id: 'e41', source: 'soc_business', target: 'eco_gdp',     weight: 0.55, polarity: 1, label: 'economic activity', labelAr: 'نشاط اقتصادي' },
  { id: 'e42', source: 'eco_gdp',     target: 'soc_citizens', weight: 0.50, polarity: 1, label: 'prosperity', labelAr: 'الرخاء' },

  // ── Cross-layer feedbacks ──
  { id: 'e43', source: 'fin_insurers', target: 'eco_shipping',  weight: 0.40, polarity: -1, label: 'coverage constraint', labelAr: 'قيود التغطية' },
  { id: 'e44', source: 'fin_reinsure', target: 'fin_ins_risk',  weight: 0.35, polarity: -1, label: 'risk transfer', labelAr: 'نقل المخاطر' },
  { id: 'e45', source: 'soc_media',    target: 'fin_ins_risk',  weight: 0.30, polarity: 1, label: 'risk perception', labelAr: 'إدراك المخاطر' },
  { id: 'e46', source: 'eco_aramco',   target: 'eco_gdp',      weight: 0.70, polarity: 1, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e47', source: 'eco_adnoc',    target: 'eco_gdp',      weight: 0.55, polarity: 1, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e48', source: 'soc_travelers', target: 'soc_travel_d', weight: 0.65, polarity: 1, label: 'demand signal', labelAr: 'إشارة الطلب' },

  // ── New edges for tourism + tadawul ──
  { id: 'e49', source: 'soc_travel_d', target: 'eco_tourism',   weight: 0.85, polarity: 1, label: 'tourism demand', labelAr: 'طلب السياحة' },
  { id: 'e50', source: 'eco_tourism',  target: 'eco_gdp',       weight: 0.50, polarity: 1, label: 'tourism GDP', labelAr: 'ناتج السياحة' },
  { id: 'e51', source: 'eco_aramco',   target: 'fin_tadawul',   weight: 0.75, polarity: 1, label: 'market cap', labelAr: 'القيمة السوقية' },
  { id: 'e52', source: 'fin_tadawul',  target: 'fin_sama',      weight: 0.45, polarity: 1, label: 'market signal', labelAr: 'إشارة السوق' },
  { id: 'e53', source: 'eco_gdp',      target: 'fin_tadawul',   weight: 0.60, polarity: 1, label: 'economic health', labelAr: 'الصحة الاقتصادية' },

  // —— Connect Qatar, Oman, Bahrain (eliminate disconnected nodes) ——
  { id: 'e54', source: 'geo_qa',      target: 'inf_doh',       weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e55', source: 'geo_qa',      target: 'inf_doha_p',    weight: 0.75, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e56', source: 'geo_om',      target: 'eco_shipping',  weight: 0.55, polarity: 1, label: 'Strait access', labelAr: 'الوصول للمضيق' },
  { id: 'e57', source: 'geo_om',      target: 'geo_hormuz',    weight: 0.70, polarity: 1, label: 'controls strait', labelAr: 'يتحكم بالمضيق' },
  { id: 'e58', source: 'geo_bh',      target: 'fin_insurers',  weight: 0.45, polarity: 1, label: 'insurance hub', labelAr: 'مركز تأمين' },
  { id: 'e59', source: 'geo_bh',      target: 'eco_oil',       weight: 0.40, polarity: 1, label: 'oil production', labelAr: 'إنتاج النفط' },
]

/* ════════════════════════════════════════════════
   SCENARIOS — 8 real GCC risk scenarios
   ════════════════════════════════════════════════ */
export const gccScenarios: GCCScenario[] = [
  {
    id: 'hormuz_closure',
    title: 'Strait of Hormuz Closure',
    titleAr: 'إغلاق مضيق هرمز',
    description: 'Full or partial closure of the Strait of Hormuz disrupting 21% of global oil transit, triggering multi-sector cascade across the GCC.',
    descriptionAr: 'إغلاق كلي أو جزئي لمضيق هرمز يعطل 21% من عبور النفط العالمي، مما يطلق سلسلة تأثيرات متعددة القطاعات عبر دول الخليج.',
    category: 'economy',
    categoryAr: 'اقتصاد',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'geo_hormuz', impact: 0.90 },
    ],
  },
  {
    id: 'oil_price_crash',
    title: 'Oil Price Crash (-40%)',
    titleAr: 'انهيار أسعار النفط (-40%)',
    description: 'Sudden 40% drop in global oil prices due to demand destruction, impacting GCC fiscal positions and downstream sectors.',
    descriptionAr: 'انخفاض مفاجئ بنسبة 40% في أسعار النفط العالمية بسبب تراجع الطلب، مما يؤثر على الأوضاع المالية لدول الخليج والقطاعات التابعة.',
    category: 'economy',
    categoryAr: 'اقتصاد',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'eco_oil', impact: 0.85 },
      { nodeId: 'eco_fuel', impact: -0.30 },
    ],
  },
  {
    id: 'port_disruption',
    title: 'Jebel Ali Port Disruption',
    titleAr: 'تعطل ميناء جبل علي',
    description: 'Major disruption at Jebel Ali Port affecting 30% of Middle East trade volume, cascading through logistics and insurance.',
    descriptionAr: 'تعطل كبير في ميناء جبل علي يؤثر على 30% من حجم التجارة في الشرق الأوسط، مع تداعيات على اللوجستيات والتأمين.',
    category: 'business reaction',
    categoryAr: 'ردة فعل الأعمال',
    country: 'UAE',
    countryAr: 'الإمارات',
    shocks: [
      { nodeId: 'inf_jebel', impact: 0.85 },
      { nodeId: 'eco_shipping', impact: 0.70 },
    ],
  },
  {
    id: 'aviation_crisis',
    title: 'GCC Aviation Crisis',
    titleAr: 'أزمة الطيران الخليجي',
    description: 'Fuel price spike combined with reduced travel demand creates compounding pressure on GCC aviation sector.',
    descriptionAr: 'ارتفاع حاد في أسعار الوقود مع انخفاض الطلب على السفر يخلق ضغطاً مركباً على قطاع الطيران الخليجي.',
    category: 'economy',
    categoryAr: 'اقتصاد',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'eco_fuel', impact: 0.80 },
      { nodeId: 'soc_travel_d', impact: -0.60 },
    ],
  },
  {
    id: 'insurance_shock',
    title: 'Regional Insurance Crisis',
    titleAr: 'أزمة التأمين الإقليمية',
    description: 'Reinsurance withdrawal from GCC markets following catastrophic loss event, raising premiums across all sectors.',
    descriptionAr: 'انسحاب إعادة التأمين من أسواق الخليج بعد حدث خسائر كارثية، مما يرفع الأقساط في جميع القطاعات.',
    category: 'economy',
    categoryAr: 'اقتصاد',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'fin_reinsure', impact: 0.85 },
      { nodeId: 'fin_ins_risk', impact: 0.75 },
    ],
  },
  {
    id: 'cyber_banking',
    title: 'Cyber Attack on Banking Infrastructure',
    titleAr: 'هجوم سيبراني على البنية التحتية المصرفية',
    description: 'Coordinated cyber attack targeting GCC central banking systems and SWIFT gateways, disrupting cross-border transactions and triggering capital flight.',
    descriptionAr: 'هجوم سيبراني منسق يستهدف أنظمة البنوك المركزية الخليجية وبوابات سويفت، مما يعطل المعاملات عبر الحدود ويؤدي إلى هروب رؤوس الأموال.',
    category: 'finance',
    categoryAr: 'مالية',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'fin_sama', impact: 0.80 },
      { nodeId: 'fin_uae_cb', impact: 0.75 },
      { nodeId: 'fin_tadawul', impact: 0.70 },
    ],
  },
  {
    id: 'pandemic_outbreak',
    title: 'Regional Pandemic Outbreak',
    titleAr: 'تفشي وباء إقليمي',
    description: 'Novel respiratory virus outbreak originating in dense urban GCC centers, forcing border closures, grounding aviation, and collapsing tourism revenue.',
    descriptionAr: 'تفشي فيروس تنفسي جديد ينطلق من المراكز الحضرية المكتظة في الخليج، مما يفرض إغلاق الحدود وتوقف الطيران وانهيار إيرادات السياحة.',
    category: 'society',
    categoryAr: 'مجتمع',
    country: 'GCC',
    countryAr: 'دول الخليج',
    shocks: [
      { nodeId: 'soc_citizens', impact: 0.85 },
      { nodeId: 'soc_travel_d', impact: 0.90 },
      { nodeId: 'inf_ruh', impact: 0.60 },
      { nodeId: 'inf_dxb', impact: 0.65 },
    ],
  },
  {
    id: 'climate_flood',
    title: 'Extreme Flooding Event',
    titleAr: 'فيضانات كارثية',
    description: 'Unprecedented rainfall and flash flooding across UAE and Oman (similar to April 2024), damaging port infrastructure, energy facilities, and supply chains.',
    descriptionAr: 'أمطار غير مسبوقة وفيضانات مفاجئة عبر الإمارات وعُمان (مشابهة لأحداث أبريل 2024)، مما يضر بالبنية التحتية للموانئ ومنشآت الطاقة وسلاسل الإمداد.',
    category: 'infrastructure',
    categoryAr: 'بنية تحتية',
    country: 'UAE/Oman',
    countryAr: 'الإمارات/عُمان',
    shocks: [
      { nodeId: 'inf_jebel', impact: 0.80 },
      { nodeId: 'inf_dxb', impact: 0.70 },
      { nodeId: 'eco_shipping', impact: 0.75 },
    ],
  },
]

/* ════════════════════════════════════════════════
   LAYER METADATA — for layout & styling
   ════════════════════════════════════════════════ */
export const layerMeta: Record<GCCLayer, { label: string; labelAr: string; color: string; yBase: number }> = {
  geography:      { label: 'Geography',      labelAr: 'الجغرافيا',       color: '#2DD4A0', yBase: 40  },
  infrastructure: { label: 'Infrastructure', labelAr: 'البنية التحتية',  color: '#F5A623', yBase: 150 },
  economy:        { label: 'Economy',        labelAr: 'الاقتصاد',        color: '#5B7BF8', yBase: 270 },
  finance:        { label: 'Finance',        labelAr: 'المالية',          color: '#A78BFA', yBase: 380 },
  society:        { label: 'Society',        labelAr: 'المجتمع',          color: '#EF5454', yBase: 480 },
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
