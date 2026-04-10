/**
 * @io/gcc-knowledge-graph — Node Registry
 *
 * 76 real GCC entities across 5 layers.
 * Canonical source — extracted from frontend/lib/gcc-graph.ts.
 * NEVER modify weights, coordinates, or sensitivity values without
 * updating the golden test suite and validating tolerance < 0.001.
 */

import { GCCNode, GCCLayer } from './types';

// ═══════════════════════════════════════════════
// Layer 1: Geography (7 nodes)
// ═══════════════════════════════════════════════
const GEOGRAPHY_NODES: GCCNode[] = [
  { id: 'geo_sa',      label: 'Saudi Arabia',       labelAr: 'السعودية',         layer: 'geography', type: 'Region',  lat: 24.7136, lng: 46.6753, weight: 0.95, sensitivity: 0.3,  damping_factor: 0.02, value: 0.95 },
  { id: 'geo_uae',     label: 'UAE',                labelAr: 'الإمارات',          layer: 'geography', type: 'Region',  lat: 25.2048, lng: 55.2708, weight: 0.90, sensitivity: 0.3,  damping_factor: 0.02, value: 0.90 },
  { id: 'geo_kw',      label: 'Kuwait',             labelAr: 'الكويت',           layer: 'geography', type: 'Region',  lat: 29.3759, lng: 47.9774, weight: 0.75, sensitivity: 0.35, damping_factor: 0.03, value: 0.75 },
  { id: 'geo_qa',      label: 'Qatar',              labelAr: 'قطر',              layer: 'geography', type: 'Region',  lat: 25.2854, lng: 51.5310, weight: 0.80, sensitivity: 0.3,  damping_factor: 0.02, value: 0.80 },
  { id: 'geo_om',      label: 'Oman',               labelAr: 'عُمان',            layer: 'geography', type: 'Region',  lat: 23.5880, lng: 58.3829, weight: 0.65, sensitivity: 0.4,  damping_factor: 0.04, value: 0.65 },
  { id: 'geo_bh',      label: 'Bahrain',            labelAr: 'البحرين',          layer: 'geography', type: 'Region',  lat: 26.0667, lng: 50.5577, weight: 0.60, sensitivity: 0.45, damping_factor: 0.04, value: 0.60 },
  { id: 'geo_hormuz',  label: 'Strait of Hormuz',   labelAr: 'مضيق هرمز',        layer: 'geography', type: 'Event',   lat: 26.5944, lng: 56.4667, weight: 0.98, sensitivity: 0.1,  damping_factor: 0.01, value: 0.98 },
];

// ═══════════════════════════════════════════════
// Layer 2: Infrastructure (22 nodes)
// Airports (9) + Ports (7) + Utilities (2) + Telecom (1) + Ministries (2) + Throughput (1)
// ═══════════════════════════════════════════════
const INFRASTRUCTURE_NODES: GCCNode[] = [
  // Airports
  { id: 'inf_ruh',     label: 'RUH Airport',         labelAr: 'مطار الرياض',        layer: 'infrastructure', type: 'Organization', lat: 24.9578, lng: 46.6989, weight: 0.80, sensitivity: 0.5,  damping_factor: 0.05, value: 0.80 },
  { id: 'inf_jed',     label: 'JED Airport',         labelAr: 'مطار جدة',          layer: 'infrastructure', type: 'Organization', lat: 21.6796, lng: 39.1565, weight: 0.85, sensitivity: 0.5,  damping_factor: 0.05, value: 0.85 },
  { id: 'inf_dmm',     label: 'DMM Airport',         labelAr: 'مطار الدمام',        layer: 'infrastructure', type: 'Organization', lat: 26.4712, lng: 49.7979, weight: 0.70, sensitivity: 0.55, damping_factor: 0.06, value: 0.70 },
  { id: 'inf_dxb',     label: 'DXB Airport',         labelAr: 'مطار دبي',          layer: 'infrastructure', type: 'Organization', lat: 25.2532, lng: 55.3657, weight: 0.88, sensitivity: 0.5,  damping_factor: 0.05, value: 0.88 },
  { id: 'inf_auh',     label: 'AUH Airport',         labelAr: 'مطار أبوظبي',        layer: 'infrastructure', type: 'Organization', lat: 24.4330, lng: 54.6511, weight: 0.82, sensitivity: 0.5,  damping_factor: 0.05, value: 0.82 },
  { id: 'inf_doh',     label: 'DOH Airport',         labelAr: 'مطار الدوحة',        layer: 'infrastructure', type: 'Organization', lat: 25.2731, lng: 51.6081, weight: 0.75, sensitivity: 0.5,  damping_factor: 0.05, value: 0.75 },
  { id: 'inf_kwi',     label: 'KWI Airport',         labelAr: 'مطار الكويت',        layer: 'infrastructure', type: 'Organization', lat: 29.2266, lng: 47.9689, weight: 0.65, sensitivity: 0.55, damping_factor: 0.06, value: 0.65 },
  { id: 'inf_bah',     label: 'BAH Airport',         labelAr: 'مطار البحرين',       layer: 'infrastructure', type: 'Organization', lat: 26.2708, lng: 50.6336, weight: 0.60, sensitivity: 0.55, damping_factor: 0.06, value: 0.60 },
  { id: 'inf_mct',     label: 'MCT Airport',         labelAr: 'مطار مسقط',         layer: 'infrastructure', type: 'Organization', lat: 23.5933, lng: 58.2844, weight: 0.62, sensitivity: 0.55, damping_factor: 0.06, value: 0.62 },
  // Ports
  { id: 'inf_jebel',   label: 'Jebel Ali Port',      labelAr: 'ميناء جبل علي',      layer: 'infrastructure', type: 'Organization', lat: 24.9857, lng: 55.0272, weight: 0.92, sensitivity: 0.6,  damping_factor: 0.04, value: 0.92 },
  { id: 'inf_dammam',  label: 'Dammam Port',         labelAr: 'ميناء الدمام',       layer: 'infrastructure', type: 'Organization', lat: 26.4473, lng: 50.1014, weight: 0.78, sensitivity: 0.6,  damping_factor: 0.05, value: 0.78 },
  { id: 'inf_doha_p',  label: 'Doha Port',           labelAr: 'ميناء الدوحة',       layer: 'infrastructure', type: 'Organization', lat: 25.2960, lng: 51.5488, weight: 0.60, sensitivity: 0.55, damping_factor: 0.06, value: 0.60 },
  { id: 'inf_hamad',   label: 'Hamad Port',          labelAr: 'ميناء حمد',         layer: 'infrastructure', type: 'Organization', lat: 25.0147, lng: 51.6014, weight: 0.75, sensitivity: 0.55, damping_factor: 0.05, value: 0.75 },
  { id: 'inf_khalifa', label: 'Khalifa Port',        labelAr: 'ميناء خليفة',        layer: 'infrastructure', type: 'Organization', lat: 24.8125, lng: 54.6486, weight: 0.80, sensitivity: 0.55, damping_factor: 0.05, value: 0.80 },
  { id: 'inf_shuwaikh',label: 'Shuwaikh Port',       labelAr: 'ميناء الشويخ',       layer: 'infrastructure', type: 'Organization', lat: 29.3500, lng: 47.9200, weight: 0.65, sensitivity: 0.55, damping_factor: 0.06, value: 0.65 },
  { id: 'inf_sohar',   label: 'Sohar Port',          labelAr: 'ميناء صحار',        layer: 'infrastructure', type: 'Organization', lat: 24.3400, lng: 56.7400, weight: 0.68, sensitivity: 0.55, damping_factor: 0.06, value: 0.68 },
  // Utilities
  { id: 'inf_desal',   label: 'Desalination Plants', labelAr: 'محطات التحلية',      layer: 'infrastructure', type: 'Organization', lat: 25.6000, lng: 55.5000, weight: 0.82, sensitivity: 0.55, damping_factor: 0.04, value: 0.82 },
  { id: 'inf_power',   label: 'Power Grid',          labelAr: 'شبكة الكهرباء',      layer: 'infrastructure', type: 'Organization', lat: 24.9200, lng: 46.7500, weight: 0.85, sensitivity: 0.5,  damping_factor: 0.03, value: 0.85 },
  { id: 'inf_telecom', label: 'GCC Telecom',         labelAr: 'الاتصالات الخليجية',   layer: 'infrastructure', type: 'Organization', lat: 24.7100, lng: 54.0000, weight: 0.80, sensitivity: 0.45, damping_factor: 0.04, value: 0.80 },
  // Ministries (infrastructure oversight)
  { id: 'gov_transport',label: 'Min. of Transport',  labelAr: 'وزارة النقل',        layer: 'infrastructure', type: 'Ministry',     lat: 24.6800, lng: 46.7200, weight: 0.80, sensitivity: 0.35, damping_factor: 0.03, value: 0.80 },
  { id: 'gov_water',   label: 'Min. of Water & Elec.',labelAr: 'وزارة المياه والكهرباء', layer: 'infrastructure', type: 'Ministry', lat: 24.6900, lng: 46.7300, weight: 0.82, sensitivity: 0.4,  damping_factor: 0.03, value: 0.82 },
  // Airport throughput aggregate
  { id: 'inf_airport_throughput', label: 'Airport Throughput', labelAr: 'حركة المطارات', layer: 'infrastructure', type: 'Topic', lat: 25.15, lng: 55.20, weight: 0.82, sensitivity: 0.7, damping_factor: 0.05, value: 0.82 },
];

// ═══════════════════════════════════════════════
// Layer 3: Economy (21 nodes)
// Oil, gas companies, shipping, aviation, fuel, GDP, tourism, food, airlines, logistics, ministries
// ═══════════════════════════════════════════════
const ECONOMY_NODES: GCCNode[] = [
  { id: 'eco_oil',      label: 'Oil Export',           labelAr: 'صادرات النفط',       layer: 'economy', type: 'Topic',         lat: 26.3000, lng: 50.2000, weight: 0.96, sensitivity: 0.7,  damping_factor: 0.03, value: 0.96 },
  { id: 'eco_aramco',   label: 'Aramco',              labelAr: 'أرامكو',            layer: 'economy', type: 'Organization',  lat: 26.3175, lng: 50.2083, weight: 0.95, sensitivity: 0.5,  damping_factor: 0.03, value: 0.95 },
  { id: 'eco_adnoc',    label: 'ADNOC',               labelAr: 'أدنوك',             layer: 'economy', type: 'Organization',  lat: 24.4539, lng: 54.3773, weight: 0.88, sensitivity: 0.5,  damping_factor: 0.04, value: 0.88 },
  { id: 'eco_kpc',      label: 'KPC',                 labelAr: 'مؤسسة البترول الكويتية', layer: 'economy', type: 'Organization', lat: 29.3375, lng: 48.0013, weight: 0.78, sensitivity: 0.55, damping_factor: 0.04, value: 0.78 },
  { id: 'eco_shipping', label: 'Shipping Cost',       labelAr: 'تكلفة الشحن',        layer: 'economy', type: 'Topic',         lat: 25.0000, lng: 55.1000, weight: 0.85, sensitivity: 0.65, damping_factor: 0.05, value: 0.85 },
  { id: 'eco_aviation', label: 'Aviation Fuel Cost',  labelAr: 'تكلفة وقود الطيران',  layer: 'economy', type: 'Topic',         lat: 25.0657, lng: 55.1713, weight: 0.82, sensitivity: 0.6,  damping_factor: 0.05, value: 0.82 },
  { id: 'eco_fuel',     label: 'Fuel Cost',           labelAr: 'تكلفة الوقود',       layer: 'economy', type: 'Topic',         lat: 24.4700, lng: 54.3700, weight: 0.88, sensitivity: 0.7,  damping_factor: 0.04, value: 0.88 },
  { id: 'eco_gdp',      label: 'GCC GDP',             labelAr: 'الناتج المحلي الخليجي', layer: 'economy', type: 'Topic',      lat: 24.4700, lng: 49.0000, weight: 0.90, sensitivity: 0.4,  damping_factor: 0.02, value: 0.90 },
  { id: 'eco_tourism',  label: 'Tourism Revenue',     labelAr: 'إيرادات السياحة',     layer: 'economy', type: 'Topic',         lat: 25.1970, lng: 55.2744, weight: 0.78, sensitivity: 0.65, damping_factor: 0.05, value: 0.78 },
  { id: 'eco_food',     label: 'Food Security',       labelAr: 'الأمن الغذائي',       layer: 'economy', type: 'Topic',         lat: 25.0500, lng: 51.0000, weight: 0.88, sensitivity: 0.7,  damping_factor: 0.05, value: 0.88 },
  // Ministries
  { id: 'gov_energy',   label: 'Min. of Energy',      labelAr: 'وزارة الطاقة',       layer: 'economy', type: 'Ministry',      lat: 24.7000, lng: 46.7000, weight: 0.90, sensitivity: 0.3,  damping_factor: 0.02, value: 0.90 },
  { id: 'gov_tourism',  label: 'Min. of Tourism',     labelAr: 'وزارة السياحة',      layer: 'economy', type: 'Ministry',      lat: 24.7500, lng: 46.7100, weight: 0.75, sensitivity: 0.4,  damping_factor: 0.03, value: 0.75 },
  { id: 'eco_telecom',  label: 'Telecom Sector',      labelAr: 'قطاع الاتصالات',      layer: 'economy', type: 'Topic',         lat: 24.7000, lng: 54.1000, weight: 0.78, sensitivity: 0.5,  damping_factor: 0.04, value: 0.78 },
  // Logistics
  { id: 'eco_logistics',label: 'Logistics Hub',       labelAr: 'المركز اللوجستي',     layer: 'economy', type: 'Topic',         lat: 25.0100, lng: 55.0800, weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },
  // Airlines
  { id: 'eco_saudia',   label: 'Saudia Airlines',     labelAr: 'الخطوط السعودية',     layer: 'economy', type: 'Organization',  lat: 24.96,   lng: 46.70,   weight: 0.75, sensitivity: 0.65, damping_factor: 0.05, value: 0.75 },
  { id: 'eco_emirates', label: 'Emirates',            labelAr: 'طيران الإمارات',      layer: 'economy', type: 'Organization',  lat: 25.25,   lng: 55.37,   weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },
  { id: 'eco_qatar_aw', label: 'Qatar Airways',       labelAr: 'الخطوط القطرية',      layer: 'economy', type: 'Organization',  lat: 25.27,   lng: 51.57,   weight: 0.78, sensitivity: 0.6,  damping_factor: 0.05, value: 0.78 },
  { id: 'eco_kw_airways',label: 'Kuwait Airways',     labelAr: 'الخطوط الكويتية',     layer: 'economy', type: 'Organization',  lat: 29.23,   lng: 47.97,   weight: 0.65, sensitivity: 0.6,  damping_factor: 0.05, value: 0.65 },
  { id: 'eco_gulf_air', label: 'Gulf Air',            labelAr: 'طيران الخليج',        layer: 'economy', type: 'Organization',  lat: 26.27,   lng: 50.63,   weight: 0.60, sensitivity: 0.6,  damping_factor: 0.05, value: 0.60 },
  { id: 'eco_oman_air', label: 'Oman Air',            labelAr: 'الطيران العماني',      layer: 'economy', type: 'Organization',  lat: 23.59,   lng: 58.28,   weight: 0.58, sensitivity: 0.6,  damping_factor: 0.05, value: 0.58 },
  { id: 'eco_av_stress',label: 'Aviation Sector Stress', labelAr: 'ضغط قطاع الطيران', layer: 'economy', type: 'Topic',       lat: 25.10,   lng: 55.15,   weight: 0.80, sensitivity: 0.7,  damping_factor: 0.05, value: 0.80 },
];

// ═══════════════════════════════════════════════
// Layer 4: Finance (12 nodes)
// Central banks (6), commercial banking, insurers, reinsurers, risk, market, ministry
// ═══════════════════════════════════════════════
const FINANCE_NODES: GCCNode[] = [
  { id: 'fin_sama',     label: 'SAMA',                labelAr: 'مؤسسة النقد',        layer: 'finance', type: 'Organization',  lat: 24.6918, lng: 46.6855, weight: 0.92, sensitivity: 0.35, damping_factor: 0.02, value: 0.92 },
  { id: 'fin_uae_cb',   label: 'UAE Central Bank',    labelAr: 'مصرف الإمارات المركزي', layer: 'finance', type: 'Organization', lat: 24.4872, lng: 54.3613, weight: 0.88, sensitivity: 0.35, damping_factor: 0.02, value: 0.88 },
  { id: 'fin_kw_cb',    label: 'Kuwait Central Bank', labelAr: 'بنك الكويت المركزي',  layer: 'finance', type: 'Organization',  lat: 29.3759, lng: 47.9850, weight: 0.75, sensitivity: 0.4,  damping_factor: 0.03, value: 0.75 },
  { id: 'fin_qa_cb',    label: 'Qatar Central Bank',  labelAr: 'مصرف قطر المركزي',    layer: 'finance', type: 'Organization',  lat: 25.2867, lng: 51.5333, weight: 0.78, sensitivity: 0.35, damping_factor: 0.02, value: 0.78 },
  { id: 'fin_om_cb',    label: 'Oman Central Bank',   labelAr: 'البنك المركزي العماني', layer: 'finance', type: 'Organization', lat: 23.5900, lng: 58.3800, weight: 0.65, sensitivity: 0.4,  damping_factor: 0.03, value: 0.65 },
  { id: 'fin_bh_cb',    label: 'Bahrain Central Bank',labelAr: 'مصرف البحرين المركزي', layer: 'finance', type: 'Organization', lat: 26.2200, lng: 50.5900, weight: 0.68, sensitivity: 0.4,  damping_factor: 0.03, value: 0.68 },
  { id: 'fin_banking',  label: 'Commercial Banks',    labelAr: 'البنوك التجارية',     layer: 'finance', type: 'Organization',  lat: 24.7200, lng: 46.6900, weight: 0.88, sensitivity: 0.55, damping_factor: 0.04, value: 0.88 },
  { id: 'fin_insurers', label: 'Insurance Risk',      labelAr: 'مخاطر التأمين',       layer: 'finance', type: 'Organization',  lat: 24.7500, lng: 46.7200, weight: 0.80, sensitivity: 0.7,  damping_factor: 0.06, value: 0.80 },
  { id: 'fin_reinsure',  label: 'Reinsurers',         labelAr: 'إعادة التأمين',       layer: 'finance', type: 'Organization',  lat: 25.1800, lng: 55.2800, weight: 0.75, sensitivity: 0.65, damping_factor: 0.05, value: 0.75 },
  { id: 'fin_ins_risk',  label: 'Insurance Risk',     labelAr: 'مخاطر التأمين',       layer: 'finance', type: 'Topic',         lat: 25.2200, lng: 55.2600, weight: 0.82, sensitivity: 0.7,  damping_factor: 0.06, value: 0.82 },
  { id: 'fin_tadawul',  label: 'Tadawul Exchange',    labelAr: 'تداول',              layer: 'finance', type: 'Organization',  lat: 24.6900, lng: 46.6900, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.04, value: 0.85 },
  { id: 'gov_finance',  label: 'Min. of Finance',     labelAr: 'وزارة المالية',       layer: 'finance', type: 'Ministry',      lat: 24.6850, lng: 46.6800, weight: 0.88, sensitivity: 0.3,  damping_factor: 0.02, value: 0.88 },
];

// ═══════════════════════════════════════════════
// Layer 5: Society (14 nodes)
// Citizens, expats, travelers, Hajj, business, media, platforms, demand, tickets
// ═══════════════════════════════════════════════
const SOCIETY_NODES: GCCNode[] = [
  { id: 'soc_citizens',  label: 'Citizens',           labelAr: 'المواطنون',          layer: 'society', type: 'Person',        lat: 24.7000, lng: 46.7000, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.06, value: 0.85 },
  { id: 'soc_expats',    label: 'Expatriate Workers', labelAr: 'العمالة الوافدة',     layer: 'society', type: 'Person',        lat: 25.2000, lng: 55.2700, weight: 0.80, sensitivity: 0.65, damping_factor: 0.06, value: 0.80 },
  { id: 'soc_travelers', label: 'Travelers',          labelAr: 'المسافرون',          layer: 'society', type: 'Person',        lat: 25.2000, lng: 55.3000, weight: 0.70, sensitivity: 0.65, damping_factor: 0.07, value: 0.70 },
  { id: 'soc_hajj',      label: 'Hajj & Umrah',      labelAr: 'الحج والعمرة',        layer: 'society', type: 'Event',         lat: 21.4225, lng: 39.8262, weight: 0.85, sensitivity: 0.6,  damping_factor: 0.05, value: 0.85 },
  { id: 'soc_business',  label: 'Businesses',         labelAr: 'الشركات',            layer: 'society', type: 'Organization',  lat: 25.0800, lng: 55.1400, weight: 0.80, sensitivity: 0.55, damping_factor: 0.05, value: 0.80 },
  { id: 'soc_media',     label: 'Media',              labelAr: 'الإعلام',            layer: 'society', type: 'Platform',      lat: 25.2000, lng: 55.2500, weight: 0.82, sensitivity: 0.5,  damping_factor: 0.06, value: 0.82 },
  { id: 'soc_social',    label: 'Social Platforms',   labelAr: 'المنصات الاجتماعية',  layer: 'society', type: 'Platform',      lat: 24.7200, lng: 46.6800, weight: 0.78, sensitivity: 0.4,  damping_factor: 0.05, value: 0.78 },
  { id: 'soc_travel_d',  label: 'Travel Demand',      labelAr: 'الطلب على السفر',     layer: 'society', type: 'Topic',         lat: 25.2500, lng: 55.3500, weight: 0.72, sensitivity: 0.7,  damping_factor: 0.07, value: 0.72 },
  { id: 'soc_ticket',    label: 'Flight Cost',        labelAr: 'تكلفة الرحلات',       layer: 'society', type: 'Topic',         lat: 25.2532, lng: 55.3600, weight: 0.68, sensitivity: 0.75, damping_factor: 0.08, value: 0.68 },
  { id: 'soc_food_d',    label: 'Food Demand',        labelAr: 'الطلب على الغذاء',    layer: 'society', type: 'Topic',         lat: 25.3000, lng: 51.5000, weight: 0.82, sensitivity: 0.7,  damping_factor: 0.06, value: 0.82 },
  { id: 'soc_housing',   label: 'Housing & Cost of Living', labelAr: 'السكن وتكلفة المعيشة', layer: 'society', type: 'Topic', lat: 24.8000, lng: 46.8000, weight: 0.75, sensitivity: 0.6, damping_factor: 0.06, value: 0.75 },
  { id: 'soc_employment',label: 'Employment',         labelAr: 'التوظيف',            layer: 'society', type: 'Topic',         lat: 24.7500, lng: 46.7500, weight: 0.80, sensitivity: 0.6,  damping_factor: 0.05, value: 0.80 },
  { id: 'soc_sentiment', label: 'Public Sentiment',   labelAr: 'المشاعر العامة',      layer: 'society', type: 'Topic',         lat: 24.8000, lng: 46.7500, weight: 0.72, sensitivity: 0.65, damping_factor: 0.06, value: 0.72 },
  { id: 'soc_stability', label: 'Public Stability',   labelAr: 'الاستقرار العام',     layer: 'society', type: 'Topic',         lat: 24.6500, lng: 46.7100, weight: 0.80, sensitivity: 0.4,  damping_factor: 0.03, value: 0.80 },
];

// ═══════════════════════════════════════════════
// Canonical Export — All 76 Nodes
// ═══════════════════════════════════════════════
export const gccNodes: ReadonlyArray<GCCNode> = Object.freeze([
  ...GEOGRAPHY_NODES,
  ...INFRASTRUCTURE_NODES,
  ...ECONOMY_NODES,
  ...FINANCE_NODES,
  ...SOCIETY_NODES,
]);

/** Node count by layer */
export const NODE_COUNTS = {
  geography: GEOGRAPHY_NODES.length,
  infrastructure: INFRASTRUCTURE_NODES.length,
  economy: ECONOMY_NODES.length,
  finance: FINANCE_NODES.length,
  society: SOCIETY_NODES.length,
  total: GEOGRAPHY_NODES.length + INFRASTRUCTURE_NODES.length + ECONOMY_NODES.length + FINANCE_NODES.length + SOCIETY_NODES.length,
} as const;

/** Lookup node by ID — O(1) after first call */
const _nodeIndex = new Map<string, GCCNode>();
export function getNode(id: string): GCCNode | undefined {
  if (_nodeIndex.size === 0) {
    for (const n of gccNodes) _nodeIndex.set(n.id, n);
  }
  return _nodeIndex.get(id);
}

/** Get all nodes for a given layer */
export function getNodesByLayer(layer: GCCLayer): GCCNode[] {
  return gccNodes.filter(n => n.layer === layer);
}

// Re-export layer arrays for direct access
export { GEOGRAPHY_NODES, INFRASTRUCTURE_NODES, ECONOMY_NODES, FINANCE_NODES, SOCIETY_NODES };
