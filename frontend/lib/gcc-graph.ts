/* âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
   GCC Reality Graph â 5-Layer Causal Dependency Model
   âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
   Layer 1: Geography   (GCC countries + chokepoints)
   Layer 2: Infrastructure (airports, ports)
   Layer 3: Economy     (oil, logistics, aviation)
   Layer 4: Finance     (banks, insurance, reinsurance)
   Layer 5: Society     (population, media, sentiment)
   âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ */

export type GCCLayer = 'geography' | 'infrastructure' | 'economy' | 'finance' | 'society'

export interface GCCNode {
  id: string
  label: string
  labelAr: string       // Arabic label
  layer: GCCLayer
  type: string          // entity sub-type for color mapping
  weight: number        // baseline importance 0â1
  sensitivity: number   // how reactive to incoming shocks 0â1
  value?: number        // computed impact (filled by propagation)
}

export interface GCCEdge {
  id: string
  source: string
  target: string
  weight: number        // causal strength â1 to 1 (negative = inverse)
  label: string         // human-readable relationship
  labelAr: string       // Arabic relationship label
  animated?: boolean
}

export interface GCCScenario {
  id: string
  title: string
  titleAr: string
  description: string
  descriptionAr: string
  category: string
  country: string
  shocks: { nodeId: string; impact: number }[]  // initial shock vector
}

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   NODES â 35 real GCC entities across 5 layers
   ââââââââââââââââââââââââââââââââââââââââââââââ */
export const gccNodes: GCCNode[] = [
  // ââ Layer 1: Geography ââ
  { id: 'geo_sa',      label: 'Saudi Arabia', labelAr: 'Saudi Arabia', labelAr: 'السعودية',    layer: 'geography', type: 'Region',       weight: 0.95, sensitivity: 0.3 },
  { id: 'geo_uae',     label: 'UAE', labelAr: 'UAE', labelAr: 'الإمارات',             layer: 'geography', type: 'Region',       weight: 0.90, sensitivity: 0.3 },
  { id: 'geo_kw',      label: 'Kuwait', labelAr: 'Kuwait', labelAr: 'الكويت',          layer: 'geography', type: 'Region',       weight: 0.75, sensitivity: 0.35 },
  { id: 'geo_qa',      label: 'Qatar', labelAr: 'Qatar', labelAr: 'قطر',           layer: 'geography', type: 'Region',       weight: 0.80, sensitivity: 0.3 },
  { id: 'geo_om',      label: 'Oman', labelAr: 'Oman', labelAr: 'عُمان',            layer: 'geography', type: 'Region',       weight: 0.65, sensitivity: 0.4 },
  { id: 'geo_bh',      label: 'Bahrain', labelAr: 'Bahrain', labelAr: 'البحرين',         layer: 'geography', type: 'Region',       weight: 0.60, sensitivity: 0.45 },
  { id: 'geo_hormuz',  label: 'Strait of Hormuz', labelAr: 'Strait of Hormuz', labelAr: 'مضيق هرمز',layer: 'geography', type: 'Event',        weight: 0.98, sensitivity: 0.1 },

  // ââ Layer 2: Infrastructure ââ
  { id: 'inf_ruh',     label: 'RUH Airport', labelAr: 'RUH Airport', labelAr: 'مطار الرياض',     layer: 'infrastructure', type: 'Organization', weight: 0.80, sensitivity: 0.5 },
  { id: 'inf_dxb',     label: 'DXB Airport', labelAr: 'DXB Airport', labelAr: 'مطار دبي',     layer: 'infrastructure', type: 'Organization', weight: 0.88, sensitivity: 0.5 },
  { id: 'inf_kwi',     label: 'KWI Airport', labelAr: 'KWI Airport', labelAr: 'مطار الكويت',     layer: 'infrastructure', type: 'Organization', weight: 0.65, sensitivity: 0.55 },
  { id: 'inf_doh',     label: 'DOH Airport', labelAr: 'DOH Airport', labelAr: 'مطار الدوحة',     layer: 'infrastructure', type: 'Organization', weight: 0.75, sensitivity: 0.5 },
  { id: 'inf_jebel',   label: 'Jebel Ali Port', labelAr: 'Jebel Ali Port', labelAr: 'ميناء جبل علي',  layer: 'infrastructure', type: 'Organization', weight: 0.92, sensitivity: 0.6 },
  { id: 'inf_dammam',  label: 'Dammam Port', labelAr: 'Dammam Port', labelAr: 'ميناء الدمام',     layer: 'infrastructure', type: 'Organization', weight: 0.78, sensitivity: 0.6 },
  { id: 'inf_doha_p',  label: 'Doha Port', labelAr: 'Doha Port', labelAr: 'ميناء الدوحة',       layer: 'infrastructure', type: 'Organization', weight: 0.60, sensitivity: 0.55 },

  // ââ Layer 3: Economy ââ
  { id: 'eco_oil',     label: 'Oil Export', labelAr: 'Oil Export', labelAr: 'صادرات النفط',       layer: 'economy', type: 'Topic',         weight: 0.96, sensitivity: 0.7 },
  { id: 'eco_aramco',  label: 'Aramco', labelAr: 'Aramco', labelAr: 'أرامكو',           layer: 'economy', type: 'Organization',  weight: 0.95, sensitivity: 0.5 },
  { id: 'eco_adnoc',   label: 'ADNOC', labelAr: 'ADNOC', labelAr: 'أدنوك',            layer: 'economy', type: 'Organization',  weight: 0.88, sensitivity: 0.5 },
  { id: 'eco_kpc',     label: 'KPC', labelAr: 'KPC', labelAr: 'مؤسسة البترول الكويتية',              layer: 'economy', type: 'Organization',  weight: 0.78, sensitivity: 0.55 },
  { id: 'eco_shipping',label: 'Shipping & Logistics', labelAr: 'Shipping & Logistics', labelAr: 'الشحن والخدمات اللوجستية', layer: 'economy', type: 'Topic',     weight: 0.85, sensitivity: 0.65 },
  { id: 'eco_aviation',label: 'Aviation Sector', labelAr: 'Aviation Sector', labelAr: 'قطاع الطيران',  layer: 'economy', type: 'Topic',         weight: 0.82, sensitivity: 0.6 },
  { id: 'eco_fuel',    label: 'Fuel Cost', labelAr: 'Fuel Cost', labelAr: 'تكلفة الوقود',        layer: 'economy', type: 'Topic',         weight: 0.88, sensitivity: 0.7 },
  { id: 'eco_gdp',     label: 'GCC GDP', labelAr: 'GCC GDP', labelAr: 'الناتج المحلي الخليجي',          layer: 'economy', type: 'Topic',         weight: 0.90, sensitivity: 0.4 },

  // ââ Layer 4: Finance ââ
  { id: 'fin_sama',    label: 'SAMA', labelAr: 'SAMA', labelAr: 'مؤسسة النقد',             layer: 'finance', type: 'Organization',  weight: 0.92, sensitivity: 0.35 },
  { id: 'fin_uae_cb',  label: 'UAE Central Bank', labelAr: 'UAE Central Bank', labelAr: 'مصرف الإمارات المركزي', layer: 'finance', type: 'Organization',  weight: 0.88, sensitivity: 0.35 },
  { id: 'fin_kw_cb',   label: 'Kuwait Central Bank', labelAr: 'Kuwait Central Bank', labelAr: 'بنك الكويت المركزي', layer: 'finance', type: 'Organization', weight: 0.75, sensitivity: 0.4 },
  { id: 'fin_insurers',label: 'Insurers', labelAr: 'Insurers', labelAr: 'شركات التأمين',         layer: 'finance', type: 'Organization',  weight: 0.80, sensitivity: 0.7 },
  { id: 'fin_reinsure', label: 'Reinsurers', labelAr: 'Reinsurers', labelAr: 'إعادة التأمين',      layer: 'finance', type: 'Organization',  weight: 0.75, sensitivity: 0.65 },
  { id: 'fin_ins_risk', label: 'Insurance Risk', labelAr: 'Insurance Risk', labelAr: 'مخاطر التأمين',  layer: 'finance', type: 'Topic',         weight: 0.82, sensitivity: 0.7 },

  // ââ Layer 5: Society ââ
  { id: 'soc_citizens', label: 'Citizens', labelAr: 'Citizens', labelAr: 'المواطنون',        layer: 'society', type: 'Person',        weight: 0.85, sensitivity: 0.6 },
  { id: 'soc_travelers',label: 'Travelers', labelAr: 'Travelers', labelAr: 'المسافرون',       layer: 'society', type: 'Person',        weight: 0.70, sensitivity: 0.65 },
  { id: 'soc_business', label: 'Businesses', labelAr: 'Businesses', labelAr: 'الشركات',      layer: 'society', type: 'Organization',  weight: 0.80, sensitivity: 0.55 },
  { id: 'soc_media',    label: 'Media', labelAr: 'Media', labelAr: 'الإعلام',           layer: 'society', type: 'Platform',      weight: 0.82, sensitivity: 0.5 },
  { id: 'soc_social',   label: 'Social Platforms', labelAr: 'Social Platforms', labelAr: 'المنصات الاجتماعية', layer: 'society', type: 'Platform',     weight: 0.78, sensitivity: 0.4 },
  { id: 'soc_travel_d', label: 'Travel Demand', labelAr: 'Travel Demand', labelAr: 'الطلب على السفر',   layer: 'society', type: 'Topic',         weight: 0.72, sensitivity: 0.7 },
  { id: 'soc_ticket',   label: 'Ticket Price', labelAr: 'Ticket Price', labelAr: 'أسعار التذاكر',    layer: 'society', type: 'Topic',         weight: 0.68, sensitivity: 0.75 },
]

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   EDGES â 48 weighted causal dependencies
   ââââââââââââââââââââââââââââââââââââââââââââââ */
export const gccEdges: GCCEdge[] = [
  // ââ Hormuz â Oil chain ââ
  { id: 'e01', source: 'geo_hormuz',  target: 'eco_oil',      weight: 0.95, label: 'controls export', labelAr: 'يتحكم بالتصدير',   animated: true },
  { id: 'e02', source: 'eco_oil',     target: 'eco_aramco',   weight: 0.90, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e03', source: 'eco_oil',     target: 'eco_adnoc',    weight: 0.85, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e04', source: 'eco_oil',     target: 'eco_kpc',      weight: 0.80, label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e05', source: 'eco_oil',     target: 'eco_shipping',  weight: 0.85, label: 'shipping volume', labelAr: 'حجم الشحن',  animated: true },
  { id: 'e06', source: 'eco_oil',     target: 'eco_fuel',     weight: 0.88, label: 'price driver', labelAr: 'محرك الأسعار' },

  // ââ Shipping & Logistics chain ââ
  { id: 'e07', source: 'eco_shipping', target: 'inf_jebel',   weight: 0.85, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e08', source: 'eco_shipping', target: 'inf_dammam',  weight: 0.78, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e09', source: 'eco_shipping', target: 'inf_doha_p',  weight: 0.60, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e10', source: 'eco_shipping', target: 'fin_ins_risk', weight: 0.80, label: 'risk exposure', labelAr: 'التعرض للمخاطر',   animated: true },

  // ââ Insurance chain ââ
  { id: 'e11', source: 'fin_ins_risk', target: 'fin_insurers',  weight: 0.80, label: 'premium impact', labelAr: 'تأثير الأقساط' },
  { id: 'e12', source: 'fin_ins_risk', target: 'fin_reinsure',  weight: 0.75, label: 'reinsurance cost', labelAr: 'تكلفة إعادة التأمين' },
  { id: 'e13', source: 'fin_insurers', target: 'soc_business',  weight: 0.65, label: 'cost pass-through', labelAr: 'تمرير التكاليف' },

  // ââ Fuel â Aviation chain ââ
  { id: 'e14', source: 'eco_fuel',     target: 'eco_aviation',  weight: 0.90, label: 'fuel cost', labelAr: 'تكلفة الوقود',       animated: true },
  { id: 'e15', source: 'eco_aviation', target: 'soc_ticket',   weight: 0.85, label: 'ticket pricing', labelAr: 'تسعير التذاكر' },
  { id: 'e16', source: 'soc_ticket',   target: 'soc_travel_d', weight: -0.70, label: 'demand inverse', labelAr: 'عكس الطلب' },
  { id: 'e17', source: 'soc_travel_d', target: 'inf_dxb',     weight: 0.80, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e18', source: 'soc_travel_d', target: 'inf_ruh',     weight: 0.70, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e19', source: 'soc_travel_d', target: 'inf_kwi',     weight: 0.55, label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e20', source: 'soc_travel_d', target: 'inf_doh',     weight: 0.60, label: 'passenger flow', labelAr: 'تدفق الركاب' },

  // ââ Aviation â GDP ââ
  { id: 'e21', source: 'eco_aviation', target: 'eco_gdp',     weight: 0.60, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e22', source: 'eco_oil',     target: 'eco_gdp',      weight: 0.75, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e23', source: 'eco_shipping', target: 'eco_gdp',     weight: 0.55, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },

  // ââ Country connections ââ
  { id: 'e24', source: 'geo_sa',      target: 'eco_aramco',   weight: 0.95, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e25', source: 'geo_uae',     target: 'eco_adnoc',    weight: 0.90, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e26', source: 'geo_kw',      target: 'eco_kpc',      weight: 0.85, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e27', source: 'geo_sa',      target: 'inf_ruh',      weight: 0.80, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e28', source: 'geo_uae',     target: 'inf_dxb',      weight: 0.85, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e29', source: 'geo_uae',     target: 'inf_jebel',    weight: 0.90, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e30', source: 'geo_sa',      target: 'inf_dammam',   weight: 0.78, label: 'operates', labelAr: 'يشغّل' },

  // ââ Finance â Country regulators ââ
  { id: 'e31', source: 'fin_sama',    target: 'fin_insurers',  weight: 0.70, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e32', source: 'fin_uae_cb',  target: 'fin_insurers',  weight: 0.65, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e33', source: 'fin_kw_cb',   target: 'fin_insurers',  weight: 0.55, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e34', source: 'geo_sa',      target: 'fin_sama',      weight: 0.85, label: 'governs', labelAr: 'يحكم' },
  { id: 'e35', source: 'geo_uae',     target: 'fin_uae_cb',   weight: 0.85, label: 'governs', labelAr: 'يحكم' },
  { id: 'e36', source: 'geo_kw',      target: 'fin_kw_cb',    weight: 0.80, label: 'governs', labelAr: 'يحكم' },

  // ââ Society connections ââ
  { id: 'e37', source: 'soc_citizens', target: 'soc_social',   weight: 0.75, label: 'expresses via', labelAr: 'يعبّر عبر' },
  { id: 'e38', source: 'soc_social',   target: 'soc_media',    weight: 0.70, label: 'feeds', labelAr: 'يغذي' },
  { id: 'e39', source: 'soc_media',    target: 'soc_citizens', weight: 0.60, label: 'informs', labelAr: 'يُعلم' },
  { id: 'e40', source: 'eco_fuel',     target: 'soc_citizens', weight: 0.80, label: 'cost of living', labelAr: 'تكلفة المعيشة' },
  { id: 'e41', source: 'soc_business', target: 'eco_gdp',     weight: 0.55, label: 'economic activity', labelAr: 'نشاط اقتصادي' },
  { id: 'e42', source: 'eco_gdp',     target: 'soc_citizens', weight: 0.50, label: 'prosperity', labelAr: 'الرخاء' },

  // ââ Cross-layer feedbacks ââ
  { id: 'e43', source: 'fin_insurers', target: 'eco_shipping',  weight: -0.40, label: 'coverage constraint', labelAr: 'قيود التغطية' },
  { id: 'e44', source: 'fin_reinsure', target: 'fin_ins_risk',  weight: -0.35, label: 'risk transfer', labelAr: 'نقل المخاطر' },
  { id: 'e45', source: 'soc_media',    target: 'fin_ins_risk',  weight: 0.30, label: 'risk perception', labelAr: 'إدراك المخاطر' },
  { id: 'e46', source: 'eco_aramco',   target: 'eco_gdp',      weight: 0.70, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e47', source: 'eco_adnoc',    target: 'eco_gdp',      weight: 0.55, label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e48', source: 'soc_travelers', target: 'soc_travel_d', weight: 0.65, label: 'demand signal', labelAr: 'إشارة الطلب' },
]

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   SCENARIOS â real GCC risk scenarios
   ââââââââââââââââââââââââââââââââââââââââââââââ */
export const gccScenarios: GCCScenario[] = [
  {
    id: 'hormuz_closure',
    title: 'Strait of Hormuz Closure',
    titleAr: 'إغلاق مضيق هرمز',
    description: 'Full or partial closure of the Strait of Hormuz disrupting 21% of global oil transit, triggering multi-sector cascade across the GCC.',
    descriptionAr: 'إغلاق كلي أو جزئي لمضيق هرمز يعطل 21% من عبور النفط العالمي، مما يطلق سلسلة تأثيرات متعددة القطاعات عبر دول الخليج.',
    category: 'economy',
    country: 'GCC',
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
    country: 'GCC',
    shocks: [
      { nodeId: 'eco_oil', impact: 0.85 },
      { nodeId: 'eco_fuel', impact: -0.30 }, // fuel gets cheaper
    ],
  },
  {
    id: 'port_disruption',
    title: 'Jebel Ali Port Disruption',
    titleAr: 'تعطل ميناء جبل علي',
    description: 'Major disruption at Jebel Ali Port affecting 30% of Middle East trade volume, cascading through logistics and insurance.',
    descriptionAr: 'تعطل كبير في ميناء جبل علي يؤثر على 30% من حجم التجارة في الشرق الأوسط، مع تداعيات على اللوجستيات والتأمين.',
    category: 'business reaction',
    country: 'UAE',
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
    country: 'GCC',
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
    country: 'GCC',
    shocks: [
      { nodeId: 'fin_reinsure', impact: 0.85 },
      { nodeId: 'fin_ins_risk', impact: 0.75 },
    ],
  },
]

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   LAYER METADATA â for layout & styling
   ââââââââââââââââââââââââââââââââââââââââââââââ */
export const layerMeta: Record<GCCLayer, { label: string; color: string; yBase: number }> = {
  geography:      { label: 'Geography', labelAr: 'Geography',      color: '#2DD4A0', yBase: 40  },
  infrastructure: { label: 'Infrastructure', labelAr: 'Infrastructure', color: '#F5A623', yBase: 150 },
  economy:        { label: 'Economy', labelAr: 'Economy',        color: '#5B7BF8', yBase: 270 },
  finance:        { label: 'Finance', labelAr: 'Finance',        color: '#A78BFA', yBase: 380 },
  society:        { label: 'Society', labelAr: 'Society',        color: '#EF5454', yBase: 480 },
}

/* ââââââââââââââââââââââââââââââââââââââââââââââ
   GRAPH â GraphNode/GraphEdge conversion
   (for compatibility with existing GraphPanel)
   ââââââââââââââââââââââââââââââââââââââââââââââ */
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
