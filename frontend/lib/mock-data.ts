// @ts-nocheck
/* =================================================
    Deevo Sim v2 — Mock Data
    Enterprise Decision Simulation Platform
   ================================================= */

import type {
  Scenario, Entity, GraphNode, GraphEdge,
  SimulationStep, SimulationReport, ChatMessage, Agent,
  DecisionOutput, BusinessImpact
} from './types'

/* -------------------------------------------------
   Scenarios (v2 Enterprise)
   ------------------------------------------------- */
export const mockScenarios: Scenario[] = [
  {
    id: 'sc-001',
    title: 'Fuel Price Increase in Saudi Arabia',
    titleAr: 'ارتفاع أسعار الوقود في السعودية',
    scenario: 'ارتفاع أسعار الوقود في السعودية بنسبة 10% وتأثير ذلك على تفاعل المستخدمين والرأي العام',
    raw_text: 'ارتفاع أسعار الوقود في السعودية بنسبة 10%',
    language: 'ar',
    country: 'Saudi Arabia',
    category: 'Economy',
    domain: 'energy',
    region: 'saudi',
    trigger: 'price-change',
    actors: ['Saudi Aramco', 'Ministry of Energy', 'SAMA', 'Citizens'],
    signals: ['economic', 'social', 'policy'],
    constraints: ['No official response yet', 'Ramadan proximity'],
    strategy: 'delayed',
    riskClass: 'HIGH',
    narrative: { en: 'A 10% fuel price surge triggers public debate across Saudi social media, testing government communication strategy.', ar: 'ارتفاع أسعار الوقود بنسبة 10% يثير نقاشا عاما عبر منصات التواصل الاجتماعي' },
    estimatedImpact: {
      financial: { score: 0.7, label: 'Revenue Risk', detail: 'Direct cost pass-through to consumers and logistics' },
      customer: { score: 0.8, label: 'Public Sentiment', detail: 'High social media reactivity expected' },
      regulatory: { score: 0.5, label: 'Policy Pressure', detail: 'May trigger subsidy review discussions' },
      reputation: { score: 0.6, label: 'Brand Trust', detail: 'Government credibility under scrutiny' },
    },
  },
  {
    id: 'sc-002',
    title: 'Kuwait Hashtag Trend',
    titleAr: 'هاشتاق فيرال في الكويت',
    scenario: 'انتشار هاشتاق مثير للجدل في الكويت يطالب بتغييرات سياسية',
    raw_text: 'انتشار هاشتاق مثير للجدل في الكويت',
    language: 'ar',
    country: 'Kuwait',
    category: 'Politics',
    domain: 'policy',
    region: 'kuwait',
    trigger: 'announcement',
    actors: ['Kuwait Parliament', 'Youth Activists', 'Media Outlets'],
    signals: ['social', 'media'],
    constraints: ['Active parliament session', 'Regional sensitivity'],
    strategy: 'silent',
    riskClass: 'MEDIUM',
    narrative: { en: 'A viral hashtag in Kuwait demanding political changes gains rapid momentum across GCC social platforms.', ar: 'هاشتاق فيرال في الكويت يطالب بتغييرات سياسية يكتسب زخما سريعا' },
    estimatedImpact: {
      financial: { score: 0.3, label: 'Minimal', detail: 'Low direct financial impact' },
      customer: { score: 0.7, label: 'High Engagement', detail: 'Youth-driven social amplification' },
      regulatory: { score: 0.6, label: 'Political Risk', detail: 'Parliamentary response likely' },
      reputation: { score: 0.5, label: 'Mixed', detail: 'Depends on government response speed' },
    },
  },
  {
    id: 'sc-003',
    title: 'Telecom Price Increase - UAE',
    titleAr: 'زيادة أسعار الاتصالات - الإمارات',
    scenario: 'رفع أسعار باقات الإنترنت بنسبة 15% في الإمارات',
    raw_text: 'رفع أسعار باقات الإنترنت 15%',
    language: 'ar',
    country: 'UAE',
    category: 'Telecom',
    domain: 'telecom',
    region: 'uae',
    trigger: 'price-change',
    actors: ['Etisalat', 'du', 'TRA', 'Consumers'],
    signals: ['economic', 'social', 'business'],
    constraints: ['Duopoly market', 'Expat-heavy user base'],
    strategy: 'soft',
    riskClass: 'MEDIUM',
    narrative: { en: 'A 15% internet package price hike by UAE telecoms triggers consumer backlash and regulatory scrutiny.', ar: 'زيادة 15% في أسعار باقات الإنترنت تثير ردة فعل المستهلكين' },
    estimatedImpact: {
      financial: { score: 0.6, label: 'Revenue Shift', detail: 'Churn risk vs price gain tradeoff' },
      customer: { score: 0.75, label: 'High Churn Risk', detail: 'Price-sensitive expat segment' },
      regulatory: { score: 0.4, label: 'TRA Review', detail: 'Regulator may intervene on consumer protection' },
      reputation: { score: 0.55, label: 'Negative Press', detail: 'Social media amplification of complaints' },
    },
  },
  {
    id: 'sc-004',
    title: 'Insurance Fraud Network Detected',
    titleAr: 'اكتشاف شبكة احتيال تأميني',
    scenario: 'اكتشاف شبكة احتيال منظمة في قطاع التأمين الصحي',
    raw_text: 'شبكة احتيال تأمين صحي',
    language: 'ar',
    country: 'Saudi Arabia',
    category: 'Insurance',
    domain: 'insurance',
    region: 'saudi',
    trigger: 'incident',
    actors: ['CCHI', 'Insurance Companies', 'Hospitals', 'SAMA'],
    signals: ['business', 'policy', 'media'],
    constraints: ['Ongoing investigation', 'PDPL data restrictions'],
    strategy: 'aggressive',
    riskClass: 'CRITICAL',
    narrative: { en: 'An organized health insurance fraud network is discovered, implicating hospitals and claims processors across the Kingdom.', ar: 'اكتشاف شبكة احتيال منظمة في قطاع التأمين الصحي تشمل مستشفيات ومعالجي مطالبات' },
    estimatedImpact: {
      financial: { score: 0.9, label: 'Major Loss', detail: 'Estimated SAR 500M+ in fraudulent claims' },
      customer: { score: 0.6, label: 'Trust Erosion', detail: 'Policyholders question claim processing integrity' },
      regulatory: { score: 0.85, label: 'SAMA Action', detail: 'Regulatory penalties and license reviews imminent' },
      reputation: { score: 0.8, label: 'Industry Crisis', detail: 'Sector-wide reputational damage' },
    },
  },
  {
    id: 'sc-005',
    title: 'Bank Liquidity Panic - Bahrain',
    titleAr: 'ذعر سيولة بنكية - البحرين',
    scenario: 'إشاعات عن أزمة سيولة في بنك بحريني كبير',
    raw_text: 'إشاعات أزمة سيولة بنكية',
    language: 'ar',
    country: 'Bahrain',
    category: 'Banking',
    domain: 'banking',
    region: 'bahrain',
    trigger: 'rumor',
    actors: ['CBB', 'National Banks', 'Depositors', 'Media'],
    signals: ['social', 'economic', 'media'],
    constraints: ['Banking secrecy laws', 'Regional contagion risk'],
    strategy: 'aggressive',
    riskClass: 'CRITICAL',
    narrative: { en: 'Rumors of a liquidity crisis at a major Bahraini bank spread via WhatsApp, risking a deposit run.', ar: 'إشاعات عن أزمة سيولة في بنك بحريني كبير تنتشر عبر واتساب' },
    estimatedImpact: {
      financial: { score: 0.95, label: 'Systemic Risk', detail: 'Potential bank run and cross-border contagion' },
      customer: { score: 0.9, label: 'Panic Level', detail: 'Mass withdrawal behavior expected' },
      regulatory: { score: 0.8, label: 'CBB Emergency', detail: 'Central bank intervention required' },
      reputation: { score: 0.85, label: 'Sector Collapse', detail: 'Bahrain financial hub reputation at stake' },
    },
  },
  {
    id: 'sc-006',
    title: 'Government Policy Shock - Qatar',
    titleAr: 'صدمة سياسة حكومية - قطر',
    scenario: 'إعلان مفاجئ عن تغيير سياسة الإقامة في قطر',
    raw_text: 'تغيير سياسة الإقامة قطر',
    language: 'ar',
    country: 'Qatar',
    category: 'Policy',
    domain: 'policy',
    region: 'qatar',
    trigger: 'regulatory',
    actors: ['Qatar Government', 'Expat Community', 'Employers', 'Media'],
    signals: ['policy', 'social', 'economic'],
    constraints: ['FIFA legacy commitments', 'Labor market dependency'],
    strategy: 'soft',
    riskClass: 'HIGH',
    narrative: { en: 'A sudden residency policy change in Qatar creates uncertainty for the expat workforce and employers.', ar: 'تغيير مفاجئ في سياسة الإقامة يخلق حالة عدم يقين للقوى العاملة' },
    estimatedImpact: {
      financial: { score: 0.65, label: 'Workforce Cost', detail: 'Employer compliance costs and talent flight' },
      customer: { score: 0.7, label: 'Expat Anxiety', detail: 'Mass uncertainty drives service demand spikes' },
      regulatory: { score: 0.75, label: 'Compliance Rush', detail: 'Employers scramble to meet new requirements' },
      reputation: { score: 0.6, label: 'Image Risk', detail: 'International media coverage of policy shift' },
    },
  },
  {
    id: 'sc-007',
    title: 'Misinformation Campaign - GCC Wide',
    titleAr: 'حملة معلومات مضللة - خليجي',
    scenario: 'حملة معلومات مضللة منظمة تستهدف القطاع المالي الخليجي',
    raw_text: 'حملة معلومات مضللة القطاع المالي',
    language: 'ar',
    country: 'GCC',
    category: 'Security',
    domain: 'security',
    region: 'gcc',
    trigger: 'cyberattack',
    actors: ['GCC Central Banks', 'Social Platforms', 'Bot Networks', 'Regulators'],
    signals: ['social', 'media', 'economic'],
    constraints: ['Cross-border coordination needed', 'Platform cooperation delays'],
    strategy: 'aggressive',
    riskClass: 'HIGH',
    narrative: { en: 'A coordinated misinformation campaign targets GCC financial institutions, spreading false bank failure narratives.', ar: 'حملة معلومات مضللة منظمة تستهدف المؤسسات المالية الخليجية' },
    estimatedImpact: {
      financial: { score: 0.8, label: 'Market Impact', detail: 'Stock market volatility and capital flight risk' },
      customer: { score: 0.85, label: 'Mass Panic', detail: 'Viral spread across WhatsApp and Twitter' },
      regulatory: { score: 0.7, label: 'Multi-State', detail: 'Requires coordinated GCC regulatory response' },
      reputation: { score: 0.75, label: 'Trust Crisis', detail: 'Long-term confidence erosion in GCC finance' },
    },
  },
  {
    id: 'sc-008',
    title: 'Supply Chain Disruption - Oman',
    titleAr: 'اضطراب سلسلة التوريد - عمان',
    scenario: 'انقطاع في سلسلة التوريد بسبب إعصار في عمان',
    raw_text: 'انقطاع سلسلة توريد إعصار عمان',
    language: 'ar',
    country: 'Oman',
    category: 'Supply Chain',
    domain: 'supply-chain',
    region: 'oman',
    trigger: 'incident',
    actors: ['Port of Sohar', 'Logistics Companies', 'Retailers', 'Civil Defense'],
    signals: ['economic', 'social', 'business'],
    constraints: ['Cyclone season', 'Limited alternative routes'],
    strategy: 'aggressive',
    riskClass: 'HIGH',
    narrative: { en: 'A cyclone disrupts Oman\'s major port operations, cascading supply shortages across GCC retail.', ar: 'إعصار يعطل عمليات ميناء عمان الرئيسي مما يسبب نقصا في الإمدادات' },
    estimatedImpact: {
      financial: { score: 0.75, label: 'Trade Loss', detail: 'Port closure costs and logistics rerouting' },
      customer: { score: 0.65, label: 'Shortages', detail: 'Consumer goods availability impacted' },
      regulatory: { score: 0.3, label: 'Emergency', detail: 'Standard disaster response protocols' },
      reputation: { score: 0.4, label: 'Manageable', detail: 'Natural disaster - limited reputational blame' },
    },
  },
  {
    id: 'sc-009',
    title: 'Brand Crisis - Major Saudi Corp',
    titleAr: 'أزمة علامة تجارية - شركة سعودية كبرى',
    scenario: 'فيديو مسرب يكشف ممارسات غير أخلاقية في شركة سعودية كبرى',
    raw_text: 'فيديو مسرب ممارسات غير أخلاقية',
    language: 'ar',
    country: 'Saudi Arabia',
    category: 'Brand',
    domain: 'brand',
    region: 'saudi',
    trigger: 'leak',
    actors: ['Corporation X', 'Whistleblower', 'Media', 'Social Influencers', 'CMA'],
    signals: ['social', 'media', 'business'],
    constraints: ['Legal proceedings', 'Employee NDA'],
    strategy: 'delayed',
    riskClass: 'CRITICAL',
    narrative: { en: 'A leaked video reveals unethical practices at a major Saudi corporation, going viral within hours.', ar: 'فيديو مسرب يكشف ممارسات غير أخلاقية في شركة سعودية كبرى ينتشر بسرعة' },
    estimatedImpact: {
      financial: { score: 0.85, label: 'Stock Drop', detail: 'Expected 5-15% stock price decline on Tadawul' },
      customer: { score: 0.9, label: 'Boycott Risk', detail: 'Consumer boycott campaigns likely' },
      regulatory: { score: 0.7, label: 'CMA Probe', detail: 'Capital Markets Authority investigation' },
      reputation: { score: 0.95, label: 'Severe Damage', detail: 'Long-term brand recovery needed' },
    },
  },
]

/* -------------------------------------------------
   Entities
   ------------------------------------------------- */
export const mockEntities: Entity[] = [
  { id: 'e-1', name: 'Saudi Citizen', nameAr: 'مواطن سعودي', type: 'person', weight: 0.85, description: 'Average Saudi citizen affected by price changes', influenceScore: 0.6, trustScore: 0.7, propagationScore: 0.8, stance: 'negative', channels: ['twitter', 'whatsapp'] },
  { id: 'e-2', name: 'Government Voice', nameAr: 'صوت حكومي', type: 'organization', weight: 0.95, description: 'Official government communication channel', influenceScore: 0.95, trustScore: 0.8, propagationScore: 0.9, stance: 'neutral', channels: ['twitter', 'news'] },
  { id: 'e-3', name: 'Social Influencer', nameAr: 'مؤثر اجتماعي', type: 'person', weight: 0.78, description: 'Popular social media personality', influenceScore: 0.85, trustScore: 0.5, propagationScore: 0.95, stance: 'mixed', channels: ['twitter', 'telegram'] },
  { id: 'e-4', name: 'Media Outlet', nameAr: 'وسيلة إعلامية', type: 'media', weight: 0.88, description: 'Major GCC news network', influenceScore: 0.9, trustScore: 0.75, propagationScore: 0.85, stance: 'neutral', channels: ['news', 'twitter'] },
  { id: 'e-5', name: 'Youth User', nameAr: 'مستخدم شاب', type: 'person', weight: 0.65, description: 'Young tech-savvy user, high engagement', influenceScore: 0.4, trustScore: 0.6, propagationScore: 0.9, stance: 'negative', channels: ['twitter', 'telegram', 'whatsapp'] },
  { id: 'e-6', name: 'Kuwaiti Citizen', nameAr: 'مواطن كويتي', type: 'person', weight: 0.72, description: 'Engaged Kuwaiti citizen', influenceScore: 0.5, trustScore: 0.65, propagationScore: 0.75, stance: 'negative', channels: ['twitter', 'whatsapp'] },
  { id: 'e-7', name: 'SAMA', nameAr: 'مؤسسة النقد العربي', type: 'organization', weight: 0.98, description: 'Saudi Central Bank - financial regulator', influenceScore: 0.98, trustScore: 0.9, propagationScore: 0.7, stance: 'neutral', channels: ['news'] },
  { id: 'e-8', name: 'Saudi Aramco', nameAr: 'أرامكو السعودية', type: 'organization', weight: 0.96, description: 'State oil company', influenceScore: 0.95, trustScore: 0.85, propagationScore: 0.6, stance: 'neutral', channels: ['news'] },
]

/* -------------------------------------------------
   Graph
   ------------------------------------------------- */
export const mockGraphNodes: GraphNode[] = [
  { id: 'n-1', label: 'Fuel Price', type: 'topic', weight: 0.9 },
  { id: 'n-2', label: 'Saudi Citizen', type: 'person', weight: 0.85 },
  { id: 'n-3', label: 'Government', type: 'organization', weight: 0.95 },
  { id: 'n-4', label: 'Social Media', type: 'platform', weight: 0.88 },
  { id: 'n-5', label: 'SAMA', type: 'organization', weight: 0.92 },
  { id: 'n-6', label: 'Influencer', type: 'person', weight: 0.78 },
  { id: 'n-7', label: 'News Media', type: 'media', weight: 0.86 },
  { id: 'n-8', label: 'Aramco', type: 'organization', weight: 0.96 },
  { id: 'n-9', label: 'Youth', type: 'person', weight: 0.65 },
  { id: 'n-10', label: 'WhatsApp', type: 'platform', weight: 0.7 },
]

export const mockGraphEdges: GraphEdge[] = [
  { id: 'ed-1', source: 'n-1', target: 'n-2', label: 'affects', weight: 0.9 },
  { id: 'ed-2', source: 'n-1', target: 'n-3', label: 'pressures', weight: 0.7 },
  { id: 'ed-3', source: 'n-2', target: 'n-4', label: 'posts_on', weight: 0.85 },
  { id: 'ed-4', source: 'n-3', target: 'n-7', label: 'issues_statement', weight: 0.8 },
  { id: 'ed-5', source: 'n-6', target: 'n-4', label: 'amplifies', weight: 0.9 },
  { id: 'ed-6', source: 'n-5', target: 'n-1', label: 'regulates', weight: 0.75 },
  { id: 'ed-7', source: 'n-8', target: 'n-1', label: 'controls', weight: 0.95 },
  { id: 'ed-8', source: 'n-9', target: 'n-10', label: 'shares_via', weight: 0.8 },
  { id: 'ed-9', source: 'n-4', target: 'n-7', label: 'feeds', weight: 0.7 },
  { id: 'ed-10', source: 'n-7', target: 'n-2', label: 'informs', weight: 0.65 },
  { id: 'ed-11', source: 'n-10', target: 'n-2', label: 'spreads_to', weight: 0.75 },
  { id: 'ed-12', source: 'n-6', target: 'n-9', label: 'influences', weight: 0.7 },
]

/* -------------------------------------------------
   Simulation Steps
   ------------------------------------------------- */
export const mockSimulationSteps: SimulationStep[] = [
  { id: 1, timestamp: 'T+0h', title: 'Initial Trigger', description: 'Fuel price increase announced via official channels', sentiment: -0.3, visibility: 0.4, events: ['Price announcement published', 'News agencies pick up story'] },
  { id: 2, timestamp: 'T+2h', title: 'Social Reaction', description: 'Citizens begin reacting on social media platforms', sentiment: -0.6, visibility: 0.65, events: ['Hashtag trending on Twitter', 'WhatsApp forwards begin'] },
  { id: 3, timestamp: 'T+6h', title: 'Influencer Amplification', description: 'Key influencers share opinions, amplifying reach', sentiment: -0.7, visibility: 0.82, events: ['Top influencers post', 'Meme creation begins'] },
  { id: 4, timestamp: 'T+12h', title: 'Media Coverage', description: 'Major news outlets run detailed analysis pieces', sentiment: -0.5, visibility: 0.9, events: ['TV coverage begins', 'Expert panels formed'] },
  { id: 5, timestamp: 'T+24h', title: 'Government Response', description: 'Official government statement addressing concerns', sentiment: -0.2, visibility: 0.95, events: ['Ministry statement issued', 'Subsidy details announced'] },
  { id: 6, timestamp: 'T+48h', title: 'Stabilization', description: 'Sentiment begins to stabilize as information spreads', sentiment: -0.1, visibility: 0.85, events: ['Public accepts rationale', 'Alternative solutions discussed'] },
  { id: 7, timestamp: 'T+72h', title: 'New Equilibrium', description: 'Market adjusts, conversation shifts to next topic', sentiment: 0.0, visibility: 0.5, events: ['Prices normalized', 'Attention shifts'] },
]

/* -------------------------------------------------
   Agents
   ------------------------------------------------- */
export const mockAgents: Agent[] = [
  { id: 'a-1', name: 'Saudi Citizen', nameAr: 'مواطن سعودي', type: 'person', archetype: 'reactive', platform: 'twitter', influence: 0.6, sentiment: -0.5 },
  { id: 'a-2', name: 'Kuwaiti Citizen', nameAr: 'مواطن كويتي', type: 'person', archetype: 'reactive', platform: 'twitter', influence: 0.5, sentiment: -0.3 },
  { id: 'a-3', name: 'Influencer', nameAr: 'مؤثر', type: 'person', archetype: 'reactive', platform: 'twitter', influence: 0.85, sentiment: -0.4 },
  { id: 'a-4', name: 'Media Account', nameAr: 'حساب إعلامي', type: 'media', archetype: 'analytical', platform: 'news', influence: 0.9, sentiment: -0.1 },
  { id: 'a-5', name: 'Government Voice', nameAr: 'صوت حكومي', type: 'organization', archetype: 'analytical', platform: 'twitter', influence: 0.95, sentiment: 0.2 },
  { id: 'a-6', name: 'Youth User', nameAr: 'مستخدم شاب', type: 'person', archetype: 'reactive', platform: 'whatsapp', influence: 0.4, sentiment: -0.6 },
]

/* -------------------------------------------------
   Reports
   ------------------------------------------------- */
export const mockReport: SimulationReport = {
  prediction: 'Fuel price increase will cause significant but temporary public backlash. Social media will drive initial sentiment, but government response within 24h will begin stabilization. Full normalization expected within 72h.',
  predictionAr: 'سيؤدي ارتفاع أسعار الوقود إلى ردة فعل عامة كبيرة ولكن مؤقتة',
  main_driver: 'Social Media Amplification',
  top_influencers: ['Government Voice', 'Social Influencer', 'Media Account'],
  spread_level: 'high' as const,
  confidence: 0.82,
  sentiment_score: -0.35,
  total_reach: 4500000,
  timeline_hours: 72,
}

/* -------------------------------------------------
   Decision Output
   ------------------------------------------------- */
export const mockDecision: DecisionOutput = {
  recommendation: 'Issue proactive government statement within 6 hours. Deploy official social media response. Brief key media outlets.',
  recommendationAr: 'إصدار بيان حكومي استباقي خلال 6 ساعات',
  risk_level: 'high' as const,
  confidence: 0.78,
  key_factors: [
    { factor: 'Social media velocity', impact: 'high' as const, direction: 'amplifying' as const },
    { factor: 'Government credibility', impact: 'high' as const, direction: 'dampening' as const },
    { factor: 'Ramadan proximity', impact: 'medium' as const, direction: 'amplifying' as const },
    { factor: 'Historical precedent', impact: 'medium' as const, direction: 'dampening' as const },
  ],
  actions: [
    { action: 'Deploy official social media response', priority: 'immediate' as const, owner: 'Communications' },
    { action: 'Brief key media outlets', priority: 'immediate' as const, owner: 'Media Relations' },
    { action: 'Monitor WhatsApp forwards', priority: 'short-term' as const, owner: 'Intelligence' },
    { action: 'Prepare subsidy adjustment details', priority: 'short-term' as const, owner: 'Policy Team' },
  ],
  spreadVelocity: 0.85,
  businessImpact: {
    financial: { score: 0.7, label: 'Revenue Risk', detail: 'Direct cost pass-through to consumers and logistics' },
    customer: { score: 0.8, label: 'Public Sentiment', detail: 'High social media reactivity expected' },
    regulatory: { score: 0.5, label: 'Policy Pressure', detail: 'May trigger subsidy review discussions' },
    reputation: { score: 0.6, label: 'Brand Trust', detail: 'Government credibility under scrutiny' },
  },
}

/* -------------------------------------------------
   Chat Messages
   ------------------------------------------------- */
export const mockChatMessages: ChatMessage[] = [
  { id: 'cm-1', role: 'user', content: 'What is the expected public reaction?', timestamp: new Date().toISOString() },
  { id: 'cm-2', role: 'assistant', content: 'Based on simulation analysis, public reaction follows a predictable pattern: Initial shock (0-2h), social media amplification (2-12h), peak negativity (12-24h), then gradual stabilization as official responses are absorbed.', timestamp: new Date().toISOString() },
  { id: 'cm-3', role: 'user', content: 'Which platform will drive the most spread?', timestamp: new Date().toISOString() },
  { id: 'cm-4', role: 'assistant', content: 'Twitter/X will be the primary driver with 65% of visible discussion. However, WhatsApp is the hidden amplifier — private groups share content 3x faster than public platforms in GCC markets. Monitor both channels.', timestamp: new Date().toISOString() },
]

export const mockChatResponses: Record<string, string> = {
  'default': 'Based on simulation data, I can analyze that pattern. Let me process the scenario parameters.',
  'why': 'The simulation identifies three key drivers: social media velocity, government response timing, and historical precedent in similar GCC scenarios.',
  'risk': 'Current risk assessment: HIGH. The primary risk vector is uncontrolled social media amplification before official response.',
  'recommendation': 'Recommended actions: 1) Proactive statement within 6h, 2) Social media monitoring activation, 3) Key influencer briefing.',
      }
