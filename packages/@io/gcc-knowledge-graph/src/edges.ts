/**
 * @io/gcc-knowledge-graph — Edge Registry
 *
 * 191 weighted causal dependencies across 5 layers.
 * Canonical source — extracted from frontend/lib/gcc-graph.ts.
 * NEVER modify weights or polarity without updating the golden test suite.
 */

import { GCCEdge } from './types';

// ═══════════════════════════════════════════════
// HORMUZ → OIL CHAIN (core cascade)
// ═══════════════════════════════════════════════
const HORMUZ_OIL_CHAIN: GCCEdge[] = [
  { id: 'e01', source: 'geo_hormuz',  target: 'eco_oil',      weight: 0.95, polarity: -1, label: 'disrupts export', labelAr: 'يعطّل التصدير',   animated: true },
  { id: 'e02', source: 'eco_oil',     target: 'eco_aramco',   weight: 0.90, polarity: 1,  label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e03', source: 'eco_oil',     target: 'eco_adnoc',    weight: 0.85, polarity: 1,  label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e04', source: 'eco_oil',     target: 'eco_kpc',      weight: 0.80, polarity: 1,  label: 'revenue driver', labelAr: 'محرك الإيرادات' },
  { id: 'e05', source: 'eco_oil',     target: 'eco_shipping', weight: 0.85, polarity: -1, label: 'oil disruption raises shipping cost', labelAr: 'تعطل النفط يرفع تكلفة الشحن', animated: true },
  { id: 'e06', source: 'eco_oil',     target: 'eco_fuel',     weight: 0.88, polarity: -1, label: 'oil disruption raises fuel price', labelAr: 'تعطل النفط يرفع سعر الوقود' },
];

// ═══════════════════════════════════════════════
// SHIPPING & LOGISTICS → PORTS
// ═══════════════════════════════════════════════
const SHIPPING_PORT_EDGES: GCCEdge[] = [
  { id: 'e07', source: 'eco_shipping', target: 'inf_jebel',    weight: 0.85, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e08', source: 'eco_shipping', target: 'inf_dammam',   weight: 0.78, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e09', source: 'eco_shipping', target: 'inf_doha_p',   weight: 0.60, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e10', source: 'eco_shipping', target: 'fin_ins_risk', weight: 0.80, polarity: 1, label: 'risk exposure', labelAr: 'التعرض للمخاطر', animated: true },
  { id: 'e67', source: 'eco_shipping', target: 'inf_hamad',    weight: 0.70, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e68', source: 'eco_shipping', target: 'inf_khalifa',  weight: 0.75, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e69', source: 'eco_shipping', target: 'inf_shuwaikh', weight: 0.55, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
  { id: 'e70', source: 'eco_shipping', target: 'inf_sohar',    weight: 0.60, polarity: 1, label: 'port traffic', labelAr: 'حركة الميناء' },
];

// ═══════════════════════════════════════════════
// INSURANCE CHAIN
// ═══════════════════════════════════════════════
const INSURANCE_CHAIN: GCCEdge[] = [
  { id: 'e11',  source: 'fin_ins_risk', target: 'fin_insurers',  weight: 0.80, polarity: 1, label: 'premium impact', labelAr: 'تأثير الأقساط' },
  { id: 'e12',  source: 'fin_ins_risk', target: 'fin_reinsure',  weight: 0.75, polarity: 1, label: 'reinsurance cost', labelAr: 'تكلفة إعادة التأمين' },
  { id: 'e13',  source: 'fin_insurers', target: 'soc_business',  weight: 0.65, polarity: 1, label: 'cost pass-through', labelAr: 'تمرير التكاليف' },
  { id: 'e136', source: 'fin_ins_risk', target: 'eco_fuel',      weight: 0.75, polarity: 1, label: 'insurance surcharge', labelAr: 'رسوم التأمين الإضافية', animated: true },
];

// ═══════════════════════════════════════════════
// FUEL → AVIATION → TICKET → DEMAND → AIRPORTS
// ═══════════════════════════════════════════════
const AVIATION_CHAIN: GCCEdge[] = [
  { id: 'e14',  source: 'eco_fuel',     target: 'eco_aviation',  weight: 0.90, polarity: 1,  label: 'fuel cost', labelAr: 'تكلفة الوقود', animated: true },
  { id: 'e15',  source: 'eco_aviation', target: 'soc_ticket',    weight: 0.85, polarity: 1,  label: 'fuel raises flight cost', labelAr: 'الوقود يرفع تكلفة الرحلات', animated: true },
  { id: 'e137', source: 'eco_aviation', target: 'eco_tourism',   weight: 0.70, polarity: -1, label: 'cost dampens tourism', labelAr: 'التكلفة تخفض السياحة', animated: true },
  { id: 'e17',  source: 'soc_travel_d', target: 'inf_dxb',       weight: 0.80, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e18',  source: 'soc_travel_d', target: 'inf_ruh',       weight: 0.70, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e19',  source: 'soc_travel_d', target: 'inf_kwi',       weight: 0.55, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e20',  source: 'soc_travel_d', target: 'inf_doh',       weight: 0.60, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e71',  source: 'soc_travel_d', target: 'inf_jed',       weight: 0.75, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e72',  source: 'soc_travel_d', target: 'inf_dmm',       weight: 0.45, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e73',  source: 'soc_travel_d', target: 'inf_auh',       weight: 0.65, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e74',  source: 'soc_travel_d', target: 'inf_bah',       weight: 0.40, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
  { id: 'e75',  source: 'soc_travel_d', target: 'inf_mct',       weight: 0.45, polarity: 1,  label: 'passenger flow', labelAr: 'تدفق الركاب' },
];

// ═══════════════════════════════════════════════
// GDP CONTRIBUTIONS
// ═══════════════════════════════════════════════
const GDP_EDGES: GCCEdge[] = [
  { id: 'e21', source: 'eco_aviation', target: 'eco_gdp',  weight: 0.60, polarity: -1, label: 'fuel cost drags GDP', labelAr: 'تكلفة الوقود تضغط الناتج' },
  { id: 'e22', source: 'eco_oil',      target: 'eco_gdp',  weight: 0.75, polarity: 1,  label: 'oil revenue drives GDP', labelAr: 'إيرادات النفط تدعم الناتج' },
  { id: 'e23', source: 'eco_shipping', target: 'eco_gdp',  weight: 0.55, polarity: -1, label: 'shipping cost drags GDP', labelAr: 'تكلفة الشحن تضغط الناتج' },
  { id: 'e46', source: 'eco_aramco',   target: 'eco_gdp',  weight: 0.70, polarity: 1,  label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e47', source: 'eco_adnoc',    target: 'eco_gdp',  weight: 0.55, polarity: 1,  label: 'revenue', labelAr: 'إيرادات' },
  { id: 'e50', source: 'eco_tourism',  target: 'eco_gdp',  weight: 0.60, polarity: 1,  label: 'tourism GDP', labelAr: 'ناتج السياحة' },
  { id: 'e76', source: 'eco_food',     target: 'eco_gdp',  weight: 0.35, polarity: 1,  label: 'food sector GDP', labelAr: 'ناتج قطاع الغذاء' },
  { id: 'e77', source: 'eco_telecom',  target: 'eco_gdp',  weight: 0.40, polarity: 1,  label: 'telecom GDP', labelAr: 'ناتج الاتصالات' },
  { id: 'e78', source: 'fin_banking',  target: 'eco_gdp',  weight: 0.60, polarity: 1,  label: 'credit multiplier', labelAr: 'مضاعف الائتمان' },
];

// ═══════════════════════════════════════════════
// COUNTRY → NATIONAL ENTITIES
// ═══════════════════════════════════════════════
const COUNTRY_ENTITY_EDGES: GCCEdge[] = [
  { id: 'e24', source: 'geo_sa',  target: 'eco_aramco',  weight: 0.95, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e25', source: 'geo_uae', target: 'eco_adnoc',   weight: 0.90, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  { id: 'e26', source: 'geo_kw',  target: 'eco_kpc',     weight: 0.85, polarity: 1, label: 'national company', labelAr: 'شركة وطنية' },
  // Country → Airports
  { id: 'e27', source: 'geo_sa',  target: 'inf_ruh',     weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e28', source: 'geo_uae', target: 'inf_dxb',     weight: 0.85, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e30', source: 'geo_sa',  target: 'inf_dammam',  weight: 0.78, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e79', source: 'geo_sa',  target: 'inf_jed',     weight: 0.85, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e80', source: 'geo_sa',  target: 'inf_dmm',     weight: 0.70, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e81', source: 'geo_uae', target: 'inf_auh',     weight: 0.82, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e82', source: 'geo_bh',  target: 'inf_bah',     weight: 0.75, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e83', source: 'geo_om',  target: 'inf_mct',     weight: 0.72, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  // Country → Ports
  { id: 'e29', source: 'geo_uae', target: 'inf_jebel',   weight: 0.90, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e84', source: 'geo_uae', target: 'inf_khalifa', weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e85', source: 'geo_kw',  target: 'inf_shuwaikh',weight: 0.70, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e86', source: 'geo_om',  target: 'inf_sohar',   weight: 0.68, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e54', source: 'geo_qa',  target: 'inf_doh',     weight: 0.80, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e55', source: 'geo_qa',  target: 'inf_doha_p',  weight: 0.75, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
  { id: 'e87', source: 'geo_qa',  target: 'inf_hamad',   weight: 0.78, polarity: 1, label: 'operates', labelAr: 'يشغّل' },
];

// ═══════════════════════════════════════════════
// CENTRAL BANK GOVERNANCE
// ═══════════════════════════════════════════════
const CENTRAL_BANK_EDGES: GCCEdge[] = [
  { id: 'e34', source: 'geo_sa',  target: 'fin_sama',    weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e35', source: 'geo_uae', target: 'fin_uae_cb',  weight: 0.85, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e36', source: 'geo_kw',  target: 'fin_kw_cb',   weight: 0.80, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e88', source: 'geo_qa',  target: 'fin_qa_cb',   weight: 0.80, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e89', source: 'geo_om',  target: 'fin_om_cb',   weight: 0.75, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  { id: 'e90', source: 'geo_bh',  target: 'fin_bh_cb',   weight: 0.75, polarity: 1, label: 'governs', labelAr: 'يحكم' },
  // Central Banks → Regulation
  { id: 'e31', source: 'fin_sama',   target: 'fin_insurers', weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e32', source: 'fin_uae_cb', target: 'fin_insurers', weight: 0.65, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e33', source: 'fin_kw_cb',  target: 'fin_insurers', weight: 0.55, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e91', source: 'fin_qa_cb',  target: 'fin_insurers', weight: 0.55, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e92', source: 'fin_om_cb',  target: 'fin_insurers', weight: 0.45, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e93', source: 'fin_bh_cb',  target: 'fin_insurers', weight: 0.50, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e94', source: 'fin_sama',   target: 'fin_banking',  weight: 0.80, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e95', source: 'fin_uae_cb', target: 'fin_banking',  weight: 0.75, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
];

// ═══════════════════════════════════════════════
// COMMERCIAL BANKING
// ═══════════════════════════════════════════════
const BANKING_EDGES: GCCEdge[] = [
  { id: 'e96', source: 'fin_banking', target: 'soc_business', weight: 0.70, polarity: 1, label: 'business lending', labelAr: 'إقراض الشركات' },
  { id: 'e97', source: 'fin_banking', target: 'soc_housing',  weight: 0.65, polarity: 1, label: 'mortgage lending', labelAr: 'إقراض السكن' },
  { id: 'e98', source: 'fin_banking', target: 'fin_insurers', weight: 0.50, polarity: 1, label: 'bancassurance', labelAr: 'التأمين المصرفي' },
];

// ═══════════════════════════════════════════════
// SOCIETY CONNECTIONS
// ═══════════════════════════════════════════════
const SOCIETY_EDGES: GCCEdge[] = [
  { id: 'e37',  source: 'soc_citizens',   target: 'soc_social',    weight: 0.75, polarity: 1, label: 'expresses via', labelAr: 'يعبّر عبر' },
  { id: 'e38',  source: 'soc_social',     target: 'soc_media',     weight: 0.70, polarity: 1, label: 'feeds', labelAr: 'يغذي' },
  { id: 'e39',  source: 'soc_media',      target: 'soc_citizens',  weight: 0.60, polarity: 1, label: 'informs', labelAr: 'يُعلم' },
  { id: 'e40',  source: 'eco_fuel',       target: 'soc_citizens',  weight: 0.80, polarity: 1, label: 'cost of living', labelAr: 'تكلفة المعيشة' },
  { id: 'e41',  source: 'soc_business',   target: 'eco_gdp',       weight: 0.55, polarity: 1, label: 'economic activity', labelAr: 'نشاط اقتصادي' },
  { id: 'e42',  source: 'eco_gdp',        target: 'soc_citizens',  weight: 0.50, polarity: 1, label: 'prosperity', labelAr: 'الرخاء' },
  { id: 'e48',  source: 'soc_travelers',  target: 'soc_travel_d',  weight: 0.65, polarity: 1, label: 'demand signal', labelAr: 'إشارة الطلب' },
  // Expat workers
  { id: 'e99',  source: 'soc_expats',     target: 'soc_business',  weight: 0.75, polarity: 1, label: 'workforce', labelAr: 'القوى العاملة' },
  { id: 'e100', source: 'soc_expats',     target: 'eco_gdp',       weight: 0.55, polarity: 1, label: 'labor contribution', labelAr: 'مساهمة العمالة' },
  { id: 'e101', source: 'soc_expats',     target: 'soc_housing',   weight: 0.60, polarity: 1, label: 'housing demand', labelAr: 'الطلب على السكن' },
  { id: 'e102', source: 'eco_gdp',        target: 'soc_employment',weight: 0.65, polarity: 1, label: 'job creation', labelAr: 'خلق الوظائف' },
  { id: 'e103', source: 'soc_employment', target: 'soc_citizens',  weight: 0.60, polarity: 1, label: 'citizen welfare', labelAr: 'رفاهية المواطنين' },
  { id: 'e104', source: 'soc_employment', target: 'soc_expats',    weight: 0.55, polarity: 1, label: 'expat demand', labelAr: 'الطلب على العمالة' },
];

// ═══════════════════════════════════════════════
// CROSS-LAYER FEEDBACKS
// ═══════════════════════════════════════════════
const CROSSLAYER_EDGES: GCCEdge[] = [
  { id: 'e43', source: 'fin_insurers', target: 'eco_shipping', weight: 0.40, polarity: -1, label: 'coverage constraint', labelAr: 'قيود التغطية' },
  { id: 'e44', source: 'fin_reinsure', target: 'fin_ins_risk', weight: 0.35, polarity: -1, label: 'risk transfer', labelAr: 'نقل المخاطر' },
  { id: 'e45', source: 'soc_media',    target: 'fin_ins_risk', weight: 0.30, polarity: 1,  label: 'risk perception', labelAr: 'إدراك المخاطر' },
];

// ═══════════════════════════════════════════════
// TOURISM + HAJJ
// ═══════════════════════════════════════════════
const TOURISM_HAJJ_EDGES: GCCEdge[] = [
  { id: 'e49',  source: 'soc_travel_d', target: 'eco_tourism', weight: 0.85, polarity: 1, label: 'tourism demand', labelAr: 'طلب السياحة' },
  { id: 'e105', source: 'soc_hajj',     target: 'eco_tourism', weight: 0.80, polarity: 1, label: 'pilgrimage revenue', labelAr: 'إيرادات الحج' },
  { id: 'e106', source: 'soc_hajj',     target: 'inf_jed',     weight: 0.85, polarity: 1, label: 'pilgrim flow', labelAr: 'تدفق الحجاج', animated: true },
  { id: 'e107', source: 'soc_hajj',     target: 'soc_travelers',weight: 0.70, polarity: 1, label: 'travel demand', labelAr: 'الطلب على السفر' },
  { id: 'e108', source: 'geo_sa',       target: 'soc_hajj',    weight: 0.90, polarity: 1, label: 'hosts', labelAr: 'يستضيف' },
  { id: 'e109', source: 'gov_tourism',  target: 'eco_tourism', weight: 0.70, polarity: 1, label: 'tourism policy', labelAr: 'سياسة السياحة' },
  { id: 'e110', source: 'gov_tourism',  target: 'soc_hajj',    weight: 0.65, polarity: 1, label: 'pilgrim policy', labelAr: 'سياسة الحج' },
];

// ═══════════════════════════════════════════════
// MARKET + FINANCE
// ═══════════════════════════════════════════════
const MARKET_FINANCE_EDGES: GCCEdge[] = [
  { id: 'e51',  source: 'eco_aramco',   target: 'fin_tadawul', weight: 0.75, polarity: 1, label: 'market cap', labelAr: 'القيمة السوقية' },
  { id: 'e52',  source: 'fin_tadawul',  target: 'fin_sama',    weight: 0.45, polarity: 1, label: 'market signal', labelAr: 'إشارة السوق' },
  { id: 'e53',  source: 'eco_gdp',      target: 'fin_tadawul', weight: 0.60, polarity: 1, label: 'economic health', labelAr: 'الصحة الاقتصادية' },
  { id: 'e111', source: 'gov_finance',  target: 'fin_sama',    weight: 0.75, polarity: 1, label: 'fiscal policy', labelAr: 'السياسة المالية' },
  { id: 'e112', source: 'gov_finance',  target: 'fin_tadawul', weight: 0.60, polarity: 1, label: 'market oversight', labelAr: 'الرقابة على السوق' },
  { id: 'e113', source: 'gov_finance',  target: 'fin_banking', weight: 0.65, polarity: 1, label: 'fiscal regulation', labelAr: 'التنظيم المالي' },
];

// ═══════════════════════════════════════════════
// HORMUZ / OMAN / BAHRAIN CONNECTIONS
// ═══════════════════════════════════════════════
const REGIONAL_EDGES: GCCEdge[] = [
  { id: 'e56', source: 'geo_om', target: 'eco_shipping', weight: 0.55, polarity: 1, label: 'Strait access', labelAr: 'الوصول للمضيق' },
  { id: 'e57', source: 'geo_om', target: 'geo_hormuz',   weight: 0.70, polarity: 1, label: 'controls strait', labelAr: 'يتحكم بالمضيق' },
  { id: 'e58', source: 'geo_bh', target: 'fin_insurers', weight: 0.45, polarity: 1, label: 'insurance hub', labelAr: 'مركز تأمين' },
  { id: 'e59', source: 'geo_bh', target: 'eco_oil',      weight: 0.40, polarity: 1, label: 'oil production', labelAr: 'إنتاج النفط' },
];

// ═══════════════════════════════════════════════
// UTILITIES (Power, Water, Telecom)
// ═══════════════════════════════════════════════
const UTILITY_EDGES: GCCEdge[] = [
  { id: 'e60',  source: 'eco_oil',     target: 'inf_power',   weight: 0.70, polarity: 1, label: 'fuel for power', labelAr: 'وقود للطاقة' },
  { id: 'e61',  source: 'inf_power',   target: 'inf_desal',   weight: 0.85, polarity: 1, label: 'powers desalination', labelAr: 'يغذي التحلية' },
  { id: 'e62',  source: 'inf_desal',   target: 'soc_citizens',weight: 0.75, polarity: 1, label: 'water supply', labelAr: 'إمدادات المياه' },
  { id: 'e63',  source: 'inf_power',   target: 'soc_citizens',weight: 0.70, polarity: 1, label: 'electricity supply', labelAr: 'إمدادات الكهرباء' },
  { id: 'e64',  source: 'inf_power',   target: 'soc_business',weight: 0.65, polarity: 1, label: 'business power', labelAr: 'طاقة الأعمال' },
  { id: 'e65',  source: 'geo_sa',      target: 'inf_power',   weight: 0.80, polarity: 1, label: 'national grid', labelAr: 'الشبكة الوطنية' },
  { id: 'e66',  source: 'geo_uae',     target: 'inf_desal',   weight: 0.75, polarity: 1, label: 'water infrastructure', labelAr: 'البنية التحتية للمياه' },
  { id: 'e114', source: 'inf_power',   target: 'inf_telecom', weight: 0.70, polarity: 1, label: 'powers telecom', labelAr: 'يغذي الاتصالات' },
  { id: 'e115', source: 'inf_telecom', target: 'eco_telecom', weight: 0.80, polarity: 1, label: 'service delivery', labelAr: 'تقديم الخدمات' },
  { id: 'e116', source: 'eco_telecom', target: 'soc_business',weight: 0.60, polarity: 1, label: 'digital services', labelAr: 'الخدمات الرقمية' },
  { id: 'e117', source: 'eco_telecom', target: 'soc_social',  weight: 0.55, polarity: 1, label: 'platform infra', labelAr: 'بنية المنصات' },
  // Ministry oversight
  { id: 'e118', source: 'gov_water',    target: 'inf_desal',   weight: 0.80, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e119', source: 'gov_water',    target: 'inf_power',   weight: 0.75, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e120', source: 'gov_transport',target: 'eco_shipping',weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
  { id: 'e121', source: 'gov_transport',target: 'eco_aviation',weight: 0.70, polarity: 1, label: 'regulates', labelAr: 'ينظّم' },
];

// ═══════════════════════════════════════════════
// FOOD SECURITY (Critical GCC chain)
// ═══════════════════════════════════════════════
const FOOD_SECURITY_EDGES: GCCEdge[] = [
  { id: 'e122', source: 'eco_shipping', target: 'eco_food',     weight: 0.85, polarity: 1, label: 'food imports', labelAr: 'واردات الغذاء', animated: true },
  { id: 'e123', source: 'inf_jebel',    target: 'eco_food',     weight: 0.70, polarity: 1, label: 'port intake', labelAr: 'استقبال الموانئ' },
  { id: 'e124', source: 'inf_dammam',   target: 'eco_food',     weight: 0.60, polarity: 1, label: 'port intake', labelAr: 'استقبال الموانئ' },
  { id: 'e125', source: 'geo_hormuz',   target: 'eco_food',     weight: 0.65, polarity: 1, label: 'supply route', labelAr: 'طريق الإمداد', animated: true },
  { id: 'e126', source: 'eco_food',     target: 'soc_citizens', weight: 0.80, polarity: 1, label: 'food supply', labelAr: 'الإمداد الغذائي' },
  { id: 'e127', source: 'eco_food',     target: 'soc_food_d',   weight: 0.75, polarity: 1, label: 'food availability', labelAr: 'توفر الغذاء' },
  { id: 'e128', source: 'soc_food_d',   target: 'soc_citizens', weight: 0.70, polarity: -1, label: 'food stress', labelAr: 'ضغط غذائي' },
  { id: 'e129', source: 'eco_food',     target: 'soc_expats',   weight: 0.65, polarity: 1, label: 'worker food supply', labelAr: 'إمداد غذاء العمالة' },
];

// ═══════════════════════════════════════════════
// MINISTRY OF ENERGY
// ═══════════════════════════════════════════════
const ENERGY_MINISTRY_EDGES: GCCEdge[] = [
  { id: 'e130', source: 'gov_energy', target: 'eco_oil',    weight: 0.85, polarity: 1, label: 'energy policy', labelAr: 'سياسة الطاقة' },
  { id: 'e131', source: 'gov_energy', target: 'eco_aramco', weight: 0.80, polarity: 1, label: 'oversees', labelAr: 'يشرف على' },
  { id: 'e132', source: 'gov_energy', target: 'eco_fuel',   weight: 0.70, polarity: 1, label: 'fuel policy', labelAr: 'سياسة الوقود' },
  { id: 'e133', source: 'gov_energy', target: 'inf_power',  weight: 0.65, polarity: 1, label: 'energy supply', labelAr: 'إمداد الطاقة' },
];

// ═══════════════════════════════════════════════
// HOUSING & COST OF LIVING
// ═══════════════════════════════════════════════
const HOUSING_EDGES: GCCEdge[] = [
  { id: 'e134', source: 'eco_fuel',    target: 'soc_housing',  weight: 0.55, polarity: 1, label: 'cost driver', labelAr: 'محرك التكاليف' },
  { id: 'e135', source: 'soc_housing', target: 'soc_citizens', weight: 0.60, polarity: 1, label: 'living costs', labelAr: 'تكاليف المعيشة' },
];

// ═══════════════════════════════════════════════
// SENTIMENT → STABILITY → MARKET
// ═══════════════════════════════════════════════
const SENTIMENT_EDGES: GCCEdge[] = [
  { id: 'e148', source: 'soc_media',     target: 'soc_sentiment', weight: 0.70, polarity: 1, label: 'shapes sentiment', labelAr: 'يشكّل المشاعر' },
  { id: 'e149', source: 'soc_social',    target: 'soc_sentiment', weight: 0.65, polarity: 1, label: 'amplifies', labelAr: 'يضخّم' },
  { id: 'e138', source: 'soc_sentiment', target: 'soc_stability', weight: 0.75, polarity: 1, label: 'affects stability', labelAr: 'يؤثر على الاستقرار' },
  { id: 'e139', source: 'soc_stability', target: 'fin_tadawul',   weight: 0.50, polarity: 1, label: 'market confidence', labelAr: 'ثقة السوق' },
  { id: 'e140', source: 'eco_gdp',       target: 'soc_stability', weight: 0.55, polarity: 1, label: 'prosperity signal', labelAr: 'إشارة الرخاء' },
  { id: 'e141', source: 'eco_food',      target: 'soc_stability', weight: 0.65, polarity: 1, label: 'food stability', labelAr: 'استقرار غذائي' },
];

// ═══════════════════════════════════════════════
// LOGISTICS HUB
// ═══════════════════════════════════════════════
const LOGISTICS_EDGES: GCCEdge[] = [
  { id: 'e142', source: 'inf_jebel',    target: 'eco_logistics', weight: 0.85, polarity: 1, label: 'logistics hub', labelAr: 'مركز لوجستي' },
  { id: 'e143', source: 'eco_logistics', target: 'eco_gdp',      weight: 0.50, polarity: 1, label: 'GDP contribution', labelAr: 'مساهمة الناتج المحلي' },
  { id: 'e144', source: 'eco_logistics', target: 'eco_food',     weight: 0.60, polarity: 1, label: 'food distribution', labelAr: 'توزيع الغذاء' },
  { id: 'e145', source: 'inf_dmm',      target: 'eco_logistics', weight: 0.45, polarity: 1, label: 'cargo hub', labelAr: 'مركز شحن' },
];

// ═══════════════════════════════════════════════
// OIL + HORMUZ CORE CASCADE CHAIN
// ═══════════════════════════════════════════════
const CASCADE_CHAIN_EDGES: GCCEdge[] = [
  { id: 'e146', source: 'eco_shipping', target: 'fin_insurers',  weight: 0.80, polarity: 1, label: 'shipping risk drives premiums', labelAr: 'مخاطر الشحن ترفع الأقساط', animated: true },
  { id: 'e147', source: 'fin_insurers', target: 'eco_aviation',  weight: 0.75, polarity: 1, label: 'insurance raises fuel cost', labelAr: 'التأمين يرفع تكلفة الوقود', animated: true },
];

// ═══════════════════════════════════════════════
// AVIATION PHASE 2: Extended Chain
// ═══════════════════════════════════════════════
const AVIATION_PHASE2_EDGES: GCCEdge[] = [
  { id: 'e150', source: 'soc_ticket',             target: 'soc_travel_d',          weight: 0.80, polarity: -1, label: 'price suppresses demand', labelAr: 'السعر يخفض الطلب', animated: true },
  { id: 'e151', source: 'soc_travel_d',           target: 'inf_airport_throughput',weight: 0.85, polarity: 1,  label: 'demand drives throughput', labelAr: 'الطلب يحرك حركة المطارات', animated: true },
  { id: 'e152', source: 'inf_airport_throughput',  target: 'eco_tourism',          weight: 0.80, polarity: 1,  label: 'throughput drives tourism', labelAr: 'حركة المطارات تدعم السياحة', animated: true },
  // Airport Throughput → individual airports (fan-out)
  { id: 'e153', source: 'inf_airport_throughput',  target: 'inf_ruh', weight: 0.85, polarity: 1, label: 'throughput → RUH', labelAr: 'الحركة → الرياض' },
  { id: 'e154', source: 'inf_airport_throughput',  target: 'inf_dxb', weight: 0.90, polarity: 1, label: 'throughput → DXB', labelAr: 'الحركة → دبي' },
  { id: 'e155', source: 'inf_airport_throughput',  target: 'inf_doh', weight: 0.80, polarity: 1, label: 'throughput → DOH', labelAr: 'الحركة → الدوحة' },
  { id: 'e156', source: 'inf_airport_throughput',  target: 'inf_jed', weight: 0.80, polarity: 1, label: 'throughput → JED', labelAr: 'الحركة → جدة' },
  { id: 'e157', source: 'inf_airport_throughput',  target: 'inf_kwi', weight: 0.70, polarity: 1, label: 'throughput → KWI', labelAr: 'الحركة → الكويت' },
  { id: 'e158', source: 'inf_airport_throughput',  target: 'inf_auh', weight: 0.75, polarity: 1, label: 'throughput → AUH', labelAr: 'الحركة → أبوظبي' },
  { id: 'e159', source: 'inf_airport_throughput',  target: 'inf_bah', weight: 0.60, polarity: 1, label: 'throughput → BAH', labelAr: 'الحركة → البحرين' },
  { id: 'e160', source: 'inf_airport_throughput',  target: 'inf_mct', weight: 0.55, polarity: 1, label: 'throughput → MCT', labelAr: 'الحركة → مسقط' },
  { id: 'e161', source: 'inf_airport_throughput',  target: 'inf_dmm', weight: 0.65, polarity: 1, label: 'throughput → DMM', labelAr: 'الحركة → الدمام' },
  // Airlines ← Aviation Fuel Cost
  { id: 'e162', source: 'eco_aviation', target: 'eco_saudia',    weight: 0.80, polarity: 1, label: 'fuel cost → Saudia',   labelAr: 'تكلفة الوقود → السعودية' },
  { id: 'e163', source: 'eco_aviation', target: 'eco_emirates',  weight: 0.85, polarity: 1, label: 'fuel cost → Emirates', labelAr: 'تكلفة الوقود → الإمارات' },
  { id: 'e164', source: 'eco_aviation', target: 'eco_qatar_aw',  weight: 0.80, polarity: 1, label: 'fuel cost → Qatar',    labelAr: 'تكلفة الوقود → القطرية' },
  // Airlines → GDP
  { id: 'e165', source: 'eco_saudia',   target: 'eco_gdp', weight: 0.45, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e166', source: 'eco_emirates', target: 'eco_gdp', weight: 0.50, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e167', source: 'eco_qatar_aw', target: 'eco_gdp', weight: 0.40, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  // Airlines ← Airport Throughput
  { id: 'e168', source: 'inf_airport_throughput', target: 'eco_saudia',   weight: 0.70, polarity: 1, label: 'passengers → Saudia',   labelAr: 'المسافرون → السعودية' },
  { id: 'e169', source: 'inf_airport_throughput', target: 'eco_emirates', weight: 0.80, polarity: 1, label: 'passengers → Emirates', labelAr: 'المسافرون → الإمارات' },
  { id: 'e170', source: 'inf_airport_throughput', target: 'eco_qatar_aw', weight: 0.70, polarity: 1, label: 'passengers → Qatar',    labelAr: 'المسافرون → القطرية' },
  // Airlines → Hub Airports
  { id: 'e171', source: 'eco_saudia',   target: 'inf_ruh', weight: 0.80, polarity: 1, label: 'Saudia hub → RUH',   labelAr: 'مركز السعودية → الرياض', animated: true },
  { id: 'e172', source: 'eco_emirates', target: 'inf_dxb', weight: 0.90, polarity: 1, label: 'Emirates hub → DXB', labelAr: 'مركز الإمارات → دبي', animated: true },
  { id: 'e173', source: 'eco_qatar_aw', target: 'inf_doh', weight: 0.85, polarity: 1, label: 'Qatar hub → DOH',   labelAr: 'مركز القطرية → الدوحة', animated: true },
  { id: 'e174', source: 'eco_saudia',   target: 'inf_jed', weight: 0.75, polarity: 1, label: 'Saudia → JED',       labelAr: 'السعودية → جدة', animated: true },
  // Additional Airlines
  { id: 'e175', source: 'eco_aviation', target: 'eco_kw_airways', weight: 0.70, polarity: 1, label: 'fuel cost → Kuwait Airways', labelAr: 'تكلفة الوقود → الكويتية' },
  { id: 'e176', source: 'eco_aviation', target: 'eco_gulf_air',   weight: 0.65, polarity: 1, label: 'fuel cost → Gulf Air',      labelAr: 'تكلفة الوقود → طيران الخليج' },
  { id: 'e177', source: 'eco_aviation', target: 'eco_oman_air',   weight: 0.60, polarity: 1, label: 'fuel cost → Oman Air',      labelAr: 'تكلفة الوقود → الطيران العماني' },
  // Additional Airlines → Hub Airports
  { id: 'e178', source: 'eco_kw_airways', target: 'inf_kwi', weight: 0.80, polarity: 1, label: 'Kuwait Airways hub → KWI', labelAr: 'الكويتية → الكويت', animated: true },
  { id: 'e179', source: 'eco_gulf_air',   target: 'inf_bah', weight: 0.80, polarity: 1, label: 'Gulf Air hub → BAH',      labelAr: 'طيران الخليج → البحرين', animated: true },
  { id: 'e180', source: 'eco_oman_air',   target: 'inf_mct', weight: 0.80, polarity: 1, label: 'Oman Air hub → MCT',      labelAr: 'الطيران العماني → مسقط', animated: true },
  // Throughput → Additional Airlines
  { id: 'e181', source: 'inf_airport_throughput', target: 'eco_kw_airways', weight: 0.60, polarity: 1, label: 'passengers → Kuwait Airways', labelAr: 'المسافرون → الكويتية' },
  { id: 'e182', source: 'inf_airport_throughput', target: 'eco_gulf_air',   weight: 0.55, polarity: 1, label: 'passengers → Gulf Air',      labelAr: 'المسافرون → طيران الخليج' },
  { id: 'e183', source: 'inf_airport_throughput', target: 'eco_oman_air',   weight: 0.50, polarity: 1, label: 'passengers → Oman Air',      labelAr: 'المسافرون → الطيران العماني' },
  // Additional Airlines → GDP
  { id: 'e184', source: 'eco_kw_airways', target: 'eco_gdp', weight: 0.30, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e185', source: 'eco_gulf_air',   target: 'eco_gdp', weight: 0.25, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
  { id: 'e186', source: 'eco_oman_air',   target: 'eco_gdp', weight: 0.25, polarity: -1, label: 'airline cost drags GDP', labelAr: 'تكلفة الطيران تضغط الناتج' },
];

// ═══════════════════════════════════════════════
// AVIATION SECTOR STRESS (aggregate)
// ═══════════════════════════════════════════════
const AVIATION_STRESS_EDGES: GCCEdge[] = [
  { id: 'e187', source: 'eco_aviation',          target: 'eco_av_stress', weight: 0.85, polarity: 1,  label: 'fuel cost → stress',       labelAr: 'تكلفة الوقود → الضغط' },
  { id: 'e188', source: 'fin_insurers',           target: 'eco_av_stress', weight: 0.70, polarity: 1,  label: 'insurance → stress',       labelAr: 'التأمين → الضغط' },
  { id: 'e189', source: 'soc_ticket',             target: 'eco_av_stress', weight: 0.65, polarity: 1,  label: 'flight cost → stress',     labelAr: 'تكلفة الرحلات → الضغط' },
  { id: 'e190', source: 'inf_airport_throughput',  target: 'eco_av_stress', weight: 0.60, polarity: -1, label: 'throughput drop → stress',  labelAr: 'انخفاض الحركة → الضغط' },
  { id: 'e191', source: 'eco_av_stress',          target: 'eco_gdp',       weight: 0.50, polarity: -1, label: 'aviation stress drags GDP', labelAr: 'ضغط الطيران يضغط الناتج' },
];

// ═══════════════════════════════════════════════
// Canonical Export — All Edges
// ═══════════════════════════════════════════════
export const gccEdges: ReadonlyArray<GCCEdge> = Object.freeze([
  ...HORMUZ_OIL_CHAIN,
  ...SHIPPING_PORT_EDGES,
  ...INSURANCE_CHAIN,
  ...AVIATION_CHAIN,
  ...GDP_EDGES,
  ...COUNTRY_ENTITY_EDGES,
  ...CENTRAL_BANK_EDGES,
  ...BANKING_EDGES,
  ...SOCIETY_EDGES,
  ...CROSSLAYER_EDGES,
  ...TOURISM_HAJJ_EDGES,
  ...MARKET_FINANCE_EDGES,
  ...REGIONAL_EDGES,
  ...UTILITY_EDGES,
  ...FOOD_SECURITY_EDGES,
  ...ENERGY_MINISTRY_EDGES,
  ...HOUSING_EDGES,
  ...SENTIMENT_EDGES,
  ...LOGISTICS_EDGES,
  ...CASCADE_CHAIN_EDGES,
  ...AVIATION_PHASE2_EDGES,
  ...AVIATION_STRESS_EDGES,
]);

/** Lookup edge by ID — O(1) after first call */
const _edgeIndex = new Map<string, GCCEdge>();
export function getEdge(id: string): GCCEdge | undefined {
  if (_edgeIndex.size === 0) {
    for (const e of gccEdges) _edgeIndex.set(e.id, e);
  }
  return _edgeIndex.get(id);
}

/** Get all edges originating from a given node */
export function getOutEdges(nodeId: string): GCCEdge[] {
  return gccEdges.filter(e => e.source === nodeId);
}

/** Get all edges targeting a given node */
export function getInEdges(nodeId: string): GCCEdge[] {
  return gccEdges.filter(e => e.target === nodeId);
}

/** Get animated (critical cascade) edges */
export function getAnimatedEdges(): GCCEdge[] {
  return gccEdges.filter(e => e.animated === true);
}
