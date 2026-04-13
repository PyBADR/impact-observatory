/**
 * Impact Observatory | مرصد الأثر — Scenario Briefing Manifest
 *
 * Observatory-grade intelligence data for 15 GCC macro scenarios.
 * IDs match backend SCENARIO_TEMPLATES.
 *
 * Each briefing follows the institutional narrative:
 *   Context → Transmission → Impact → Decision → Outcome
 *
 * Static for SSG. In production, hydrated from GET /api/v1/runs/{id}.
 */

/* ── Types ── */

export interface TransmissionStep {
  from: string;
  to: string;
  mechanism: string;
  delayHours: number;
}

export interface ExposureLine {
  entity: string;
  sector: string;
  exposure: string;
  severity: 'Critical' | 'Severe' | 'High' | 'Elevated' | 'Guarded';
}

export interface DecisionLine {
  action: string;
  owner: string;
  deadline: string;
  sector: string;
}

export interface ScenarioBriefing {
  id: string;
  title: string;
  severity: 'Severe' | 'High' | 'Elevated' | 'Guarded';
  domain: string;
  horizonHours: number;
  sectors: string[];
  /** What happened — situational summary. */
  context: string;
  /** Why it matters now to GCC decision-makers. */
  significance: string;
  /** One-sentence framing for the transmission section. */
  transmissionFraming: string;
  transmission: TransmissionStep[];
  /** One-sentence framing for the impact section. */
  impactFraming: string;
  impact: ExposureLine[];
  /** One-sentence framing for the decision section. */
  decisionFraming: string;
  decisions: DecisionLine[];
  /** Prose describing expected result if decisions execute. */
  outcome: string;
  /** 2–4 signals that confirm or disprove the decision path. */
  monitoringCriteria: string[];
}

/* ── Manifest ── */

const manifest: ScenarioBriefing[] = [
  {
    id: 'hormuz_chokepoint_disruption',
    title: 'Strait of Hormuz Disruption',
    severity: 'Severe',
    domain: 'Maritime & Energy',
    horizonHours: 72,
    sectors: ['Energy', 'Shipping', 'Insurance', 'Banking'],
    context:
      'A partial blockage of the Strait of Hormuz has disrupted oil tanker transit and Gulf shipping lanes. Approximately 21 percent of global petroleum consumption passes through this chokepoint daily. The disruption has triggered immediate energy price spikes, forced shipping rerouting around the Cape of Good Hope, and caused insurance war-risk premiums to surge across all Gulf-origin cargo.',
    significance:
      'This is the single highest-impact maritime disruption scenario for the GCC. Every Gulf state depends on Hormuz for energy export revenue. The disruption simultaneously pressures sovereign fiscal inflows, trade finance portfolios, and reinsurance capacity — creating a multi-sector stress event that requires coordinated response within hours, not days.',
    transmissionFraming: 'Economic pressure propagates from physical blockade through energy pricing, sovereign revenue, and financial system liquidity in under 24 hours.',
    transmission: [
      { from: 'Strait of Hormuz', to: 'Oil export infrastructure', mechanism: 'Physical blockade halts tanker transit at the chokepoint, creating an immediate queue of 80–120 loaded vessels', delayHours: 0 },
      { from: 'Oil export infrastructure', to: 'Global energy markets', mechanism: 'Supply constraint of 17–20M barrels/day drives Brent crude spot price escalation of $25–40/barrel within hours', delayHours: 4 },
      { from: 'Global energy markets', to: 'GCC sovereign revenue', mechanism: 'Despite price spike, export volume collapse reduces net fiscal inflows — Saudi Arabia alone loses $4.2B/day in export capacity', delayHours: 12 },
      { from: 'Gulf shipping lanes', to: 'Marine insurance markets', mechanism: 'War-risk premium on Gulf-origin cargo surges 400–800 percent, effectively halting new policy issuance on transiting vessels', delayHours: 6 },
      { from: 'Marine insurance markets', to: 'GCC banking sector', mechanism: 'Reinsurance capital calls and trade finance letter-of-credit freezes pressure bank liquidity ratios across the region', delayHours: 24 },
    ],
    impactFraming: 'The disruption creates simultaneous exposure across energy, shipping, insurance, and banking — affecting sovereign entities, national oil companies, and regional financial institutions.',
    impact: [
      { entity: 'Saudi Aramco', sector: 'Energy', exposure: '$4.2B daily export revenue at risk from tanker transit halt', severity: 'Critical' },
      { entity: 'ADNOC', sector: 'Energy', exposure: '$1.8B daily export revenue at risk; Fujairah pipeline capacity insufficient for full diversion', severity: 'Critical' },
      { entity: 'DP World', sector: 'Shipping', exposure: '38 percent throughput reduction at Jebel Ali as rerouted vessels overwhelm alternative capacity', severity: 'Severe' },
      { entity: 'Emirates NBD', sector: 'Banking', exposure: 'Trade finance portfolio under stress — $12B in outstanding letters of credit on Gulf shipping routes', severity: 'High' },
      { entity: 'QatarEnergy', sector: 'Energy', exposure: 'LNG tanker rerouting via Bab el-Mandeb adds 7–10 days transit time and $2.8M per cargo', severity: 'High' },
      { entity: 'GCC reinsurance market', sector: 'Insurance', exposure: 'War-risk premium surge of 400–800 percent renders new marine cargo underwriting commercially unviable', severity: 'Severe' },
    ],
    decisionFraming: 'Five decisions are required within the first 48 hours to contain economic damage and prevent the disruption from cascading into a regional financial stress event.',
    decisions: [
      { action: 'Activate strategic petroleum reserve release protocol to signal supply continuity to global markets', owner: 'Ministry of Energy (KSA)', deadline: '4 hours', sector: 'Energy' },
      { action: 'Invoke force majeure on affected cargo contracts to limit legal exposure for national oil companies', owner: 'ADNOC / Saudi Aramco Legal', deadline: '12 hours', sector: 'Energy' },
      { action: 'Trigger emergency liquidity backstop for trade finance portfolios exposed to Gulf shipping routes', owner: 'Central Bank of the UAE', deadline: '24 hours', sector: 'Banking' },
      { action: 'Activate alternative export routing through the Fujairah–Habshan pipeline at maximum throughput', owner: 'ADNOC Pipeline Operations', deadline: '6 hours', sector: 'Energy' },
      { action: 'Issue revised war-risk underwriting guidance to prevent complete marine cargo insurance withdrawal', owner: 'UAE Insurance Authority', deadline: '48 hours', sector: 'Insurance' },
    ],
    outcome:
      'If strategic reserves are released within 4 hours and alternative pipeline routing activates within 6 hours, projected economic loss is reduced from $14.2B to $5.8B over the 72-hour horizon. The liquidity backstop prevents trade finance contagion from reaching the interbank market. Insurance market function is restored within 5 days once revised war-risk guidance is issued. Without coordinated action, losses compound to $22B by day 5 as secondary effects propagate through sovereign budgets.',
    monitoringCriteria: [
      'Brent crude spot price stabilizes below $130/barrel within 48 hours of reserve release announcement',
      'Fujairah pipeline throughput reaches 1.5M barrels/day within 12 hours of activation',
      'No GCC bank reports LCR breach in the 72-hour window following liquidity backstop activation',
      'Marine cargo insurance issuance resumes on Gulf routes within 5 business days of revised guidance',
    ],
  },
  {
    id: 'hormuz_full_closure',
    title: 'Hormuz Full Closure',
    severity: 'Severe',
    domain: 'Maritime & Energy',
    horizonHours: 72,
    sectors: ['Energy', 'Shipping', 'Government', 'Banking'],
    context:
      'The Strait of Hormuz has been fully closed to all maritime traffic. This is the maximum-severity energy supply scenario — no tanker transit, no LNG shipments, no container traffic through the Gulf. All six GCC states lose maritime export and import capacity simultaneously.',
    significance:
      'Full closure removes approximately 20 million barrels per day from global oil supply and halts all Gulf LNG exports. This is not a localized disruption — it is a global energy emergency that triggers immediate coordination between GCC sovereigns, the IEA, and major consuming nations. The fiscal, banking, and social stability consequences escalate by the hour.',
    transmissionFraming: 'Pressure moves from total maritime halt through energy markets, sovereign budgets, banking liquidity, and eventually social stability within 72 hours.',
    transmission: [
      { from: 'Strait of Hormuz', to: 'All Gulf ports', mechanism: 'Total maritime transit cessation — no vessels enter or exit the Persian Gulf', delayHours: 0 },
      { from: 'All Gulf ports', to: 'Global energy supply', mechanism: '20M barrels/day and 28 percent of global LNG supply removed from market simultaneously', delayHours: 2 },
      { from: 'Global energy supply', to: 'GCC sovereign budgets', mechanism: 'Export revenue collapses across all six states despite global price spike — no volume to sell', delayHours: 8 },
      { from: 'GCC sovereign budgets', to: 'Regional banking systems', mechanism: 'Government deposit drawdowns and spending freezes cascade into interbank liquidity pressure', delayHours: 24 },
    ],
    impactFraming: 'Every GCC economy faces simultaneous fiscal, energy, and financial stress with no regional diversification possible.',
    impact: [
      { entity: 'GCC economies (combined)', sector: 'Government', exposure: '$6.2B combined daily export revenue loss across all six states', severity: 'Critical' },
      { entity: 'Global oil markets', sector: 'Energy', exposure: 'Brent crude projected to spike above $140/barrel within 24 hours', severity: 'Critical' },
      { entity: 'GCC banking sector', sector: 'Banking', exposure: 'Systemic liquidity pressure as government deposits are drawn down for fiscal stabilization', severity: 'Severe' },
    ],
    decisionFraming: 'Three coordinated decisions are required at the GCC-wide level within 12 hours.',
    decisions: [
      { action: 'Coordinate simultaneous strategic reserve release across all six GCC states and request IEA emergency action', owner: 'GCC Supreme Council', deadline: '2 hours', sector: 'Government' },
      { action: 'Activate all alternative pipeline export capacity — Fujairah, East-West, and IPSA lines at maximum throughput', owner: 'National oil companies (joint)', deadline: '4 hours', sector: 'Energy' },
      { action: 'Establish emergency interbank liquidity facility with combined central bank backstop', owner: 'GCC central banks (coordinated)', deadline: '12 hours', sector: 'Banking' },
    ],
    outcome:
      'Coordinated response limits total economic damage to $22B over 72 hours versus $41B under uncoordinated or delayed action. Alternative pipeline routes restore approximately 30 percent of export capacity within 6 hours. The interbank liquidity facility prevents a regional banking crisis. Without coordination, individual state responses fragment and the 72-hour loss estimate rises to $55B as market confidence collapses.',
    monitoringCriteria: [
      'IEA confirms coordinated reserve release within 6 hours of GCC Supreme Council request',
      'Combined alternative pipeline throughput exceeds 3M barrels/day within 8 hours',
      'No GCC central bank invokes emergency lending facility beyond the coordinated backstop',
    ],
  },
  {
    id: 'iran_regional_escalation',
    title: 'Iran Regional Escalation',
    severity: 'Severe',
    domain: 'Geopolitical',
    horizonHours: 168,
    sectors: ['Energy', 'Shipping', 'Banking', 'Insurance', 'Government'],
    context:
      'A regional geopolitical escalation involving Iran has introduced military, economic, and diplomatic threat vectors simultaneously. Energy infrastructure in multiple GCC states faces direct or proximate threat. Shipping lanes are under operational risk. Financial markets have begun repricing GCC sovereign and corporate exposure.',
    significance:
      'This scenario combines the worst elements of energy disruption, capital flight, and sovereign risk repricing. Unlike a single-vector disruption, the geopolitical dimension means market confidence — not just physical infrastructure — is the primary casualty. Foreign capital outflow from the GCC accelerates as international investors reduce regional exposure across all asset classes.',
    transmissionFraming: 'Pressure transmits through threat perception before physical disruption occurs — markets reprice on risk, not on realized damage.',
    transmission: [
      { from: 'Geopolitical escalation', to: 'Energy infrastructure', mechanism: 'Direct or proximate threat to production facilities, export terminals, and pipeline networks across the region', delayHours: 0 },
      { from: 'Energy infrastructure threat', to: 'Global commodity markets', mechanism: 'Risk premium surge across oil, gas, and petrochemical futures as traders price in supply disruption probability', delayHours: 4 },
      { from: 'Global commodity markets', to: 'International capital flows', mechanism: 'Foreign institutional investors reduce GCC allocation — equity, bond, and real estate outflows accelerate', delayHours: 24 },
      { from: 'Capital outflows', to: 'GCC banking and real estate', mechanism: 'Asset repricing, currency pressure, and liquidity contraction across the financial system', delayHours: 48 },
    ],
    impactFraming: 'Five sectors face simultaneous pressure, with banking and real estate most vulnerable to secondary effects from capital flight.',
    impact: [
      { entity: 'GCC energy sector', sector: 'Energy', exposure: 'Production and export facilities under direct threat — output reduction of 15–30 percent probable', severity: 'Critical' },
      { entity: 'GCC financial markets', sector: 'Banking', exposure: 'Foreign capital outflow of $15–25B projected over the first 7 days', severity: 'Severe' },
      { entity: 'GCC real estate sector', sector: 'Real Estate', exposure: 'Foreign investor withdrawal and project financing freeze across UAE and Saudi markets', severity: 'High' },
      { entity: 'Gulf shipping lanes', sector: 'Shipping', exposure: 'Marine cargo insurance suspended on Gulf routes pending escalation assessment', severity: 'Severe' },
    ],
    decisionFraming: 'Four decisions are required across defense, financial, energy, and diplomatic channels — each within different time horizons.',
    decisions: [
      { action: 'Activate GCC Joint Defense Council protocols and establish unified command for infrastructure protection', owner: 'GCC Defense Council', deadline: '2 hours', sector: 'Government' },
      { action: 'Impose temporary capital flow controls to limit outflow velocity while markets stabilize', owner: 'GCC central banks (coordinated)', deadline: '12 hours', sector: 'Banking' },
      { action: 'Coordinate strategic reserve release with IEA to cap energy price escalation', owner: 'Energy ministries (coordinated)', deadline: '24 hours', sector: 'Energy' },
      { action: 'Activate diplomatic de-escalation channels through multilateral intermediaries', owner: 'GCC foreign ministries', deadline: '6 hours', sector: 'Government' },
    ],
    outcome:
      'Capital controls limit outflow to $8B versus $25B under unrestricted conditions. Strategic reserve coordination prevents energy price overshoot beyond $145/barrel. Diplomatic engagement reduces escalation probability by an estimated 35–40 percent based on historical precedent. The critical monitoring window is 7 days — if no physical infrastructure damage occurs and diplomatic channels produce a de-escalation signal, market confidence stabilizes within 14 days.',
    monitoringCriteria: [
      'Daily foreign capital outflow rate declines below $1B/day within 5 days of capital controls',
      'No physical damage to GCC energy infrastructure within the 7-day monitoring window',
      'Diplomatic channel produces a public de-escalation statement from at least one party within 7 days',
      'GCC sovereign CDS spreads stabilize within 50bps of pre-escalation levels by day 10',
    ],
  },
  {
    id: 'critical_port_throughput_disruption',
    title: 'Multi-Port Throughput Failure',
    severity: 'Severe',
    domain: 'Logistics',
    horizonHours: 168,
    sectors: ['Shipping', 'Energy', 'Insurance', 'Banking'],
    context:
      'Simultaneous throughput failure at Jebel Ali, Ras Tanura, and Shuwaikh ports has reduced combined GCC maritime capacity by over 60 percent. The cause is operational — coordinated systems failure, not geopolitical — but the effect is identical: energy exports queue, container imports halt, and supply chain pressure builds across the region.',
    significance:
      'The GCC has limited port redundancy. When three major ports fail simultaneously, there is no regional diversion capacity sufficient to absorb the volume. This scenario tests the physical limits of GCC trade infrastructure and exposes the region to essential goods shortage risk within 5–7 days.',
    transmissionFraming: 'Pressure transmits simultaneously through energy export queues and consumer import backlogs, converging on inflation and sovereign fiscal pressure.',
    transmission: [
      { from: 'Major GCC ports', to: 'Energy export operations', mechanism: 'Tanker loading halts at Ras Tanura — 200+ vessels enter queue within 48 hours', delayHours: 0 },
      { from: 'Major GCC ports', to: 'Container import operations', mechanism: 'Consumer goods, industrial inputs, and food imports backlog at Jebel Ali and Shuwaikh', delayHours: 12 },
      { from: 'Container import backlog', to: 'Consumer price inflation', mechanism: 'Supply shortage drives price pressure on essential goods within 5–7 days', delayHours: 72 },
    ],
    impactFraming: 'The disruption creates acute exposure in shipping and energy, with secondary effects on consumer markets and sovereign stability.',
    impact: [
      { entity: 'GCC port system', sector: 'Shipping', exposure: 'Over 60 percent of combined maritime throughput capacity offline', severity: 'Critical' },
      { entity: 'Energy export operations', sector: 'Energy', exposure: 'Tanker queue exceeds 200 vessels — loading delays of 7–14 days', severity: 'Severe' },
      { entity: 'GCC consumer markets', sector: 'Government', exposure: 'Essential goods shortage risk within 5–7 days if port restoration is delayed', severity: 'High' },
    ],
    decisionFraming: 'Three decisions are required to manage the immediate logistics crisis, protect essential supply lines, and prevent secondary energy market disruption.',
    decisions: [
      { action: 'Declare force majeure on affected port contracts and activate regional port mutual-aid agreements', owner: 'Port authorities (coordinated)', deadline: '6 hours', sector: 'Shipping' },
      { action: 'Activate emergency food, medical, and essential goods supply corridors via air and overland routes', owner: 'Civil defense authorities', deadline: '12 hours', sector: 'Government' },
      { action: 'Coordinate tanker queue management through OPEC secretariat to prevent secondary energy market disruption', owner: 'Energy ministries', deadline: '24 hours', sector: 'Energy' },
    ],
    outcome:
      'Emergency supply corridors maintain essential goods availability throughout the disruption window. Tanker queue management prevents a secondary energy price spike by signaling orderly resolution to markets. Full port restoration is targeted within 7 days. The critical risk is days 5–7: if ports remain offline beyond this window, consumer price inflation accelerates and political pressure on governments intensifies.',
    monitoringCriteria: [
      'Emergency supply corridors operational within 18 hours of activation order',
      'No essential goods stockout reported in any GCC state during the disruption window',
      'Port throughput restored to 50 percent of normal capacity within 5 days',
    ],
  },
  {
    id: 'saudi_oil_shock',
    title: 'Saudi Oil Production Shock',
    severity: 'High',
    domain: 'Energy',
    horizonHours: 168,
    sectors: ['Energy', 'Government', 'Banking', 'Real Estate'],
    context:
      'A sudden disruption to Saudi Aramco production capacity has reduced output by 5.7 million barrels per day — approximately half of the Kingdom\'s normal production. The cause is infrastructure failure at major processing facilities. Global energy markets have reacted with a sharp price spike, but Saudi fiscal revenue declines because the lost volume exceeds the price benefit.',
    significance:
      'Saudi Arabia is the world\'s swing producer. A production shock of this magnitude signals to markets that spare capacity — the global safety net — is compromised. The fiscal impact on the Kingdom is immediate, and the downstream effects on petrochemical supply chains, government spending programs, and banking sector liquidity follow within days.',
    transmissionFraming: 'Pressure transmits from production loss through fiscal revenue, government spending, and banking liquidity over a 7-day horizon.',
    transmission: [
      { from: 'Aramco production facilities', to: 'Global oil supply', mechanism: 'Supply deficit of 5.7M barrels/day — the largest single-source reduction since 2019', delayHours: 0 },
      { from: 'Global oil supply deficit', to: 'Saudi fiscal revenue', mechanism: 'Net revenue loss despite price spike — volume loss exceeds per-barrel price gain', delayHours: 24 },
      { from: 'Saudi fiscal revenue', to: 'Banking sector', mechanism: 'Government spending contraction and deposit drawdowns cascade into bank liquidity pressure', delayHours: 72 },
    ],
    impactFraming: 'The shock concentrates on Saudi entities but cascades into regional banking and petrochemical supply chains.',
    impact: [
      { entity: 'Saudi Aramco', sector: 'Energy', exposure: 'Production loss valued at $2.8B per day at current market prices', severity: 'Critical' },
      { entity: 'Saudi government', sector: 'Government', exposure: 'Fiscal buffer drawdown accelerates — deficit widens by $8–12B over 30 days', severity: 'High' },
      { entity: 'SABIC', sector: 'Energy', exposure: 'Feedstock supply disruption halts 40 percent of petrochemical output', severity: 'High' },
    ],
    decisionFraming: 'Three decisions are required to restore production, stabilize global markets, and protect fiscal capacity.',
    decisions: [
      { action: 'Activate Shaybah and Khurais surge capacity to restore partial production within 48 hours', owner: 'Saudi Aramco Operations', deadline: '12 hours', sector: 'Energy' },
      { action: 'Request IEA coordinated strategic reserve release to cap global price escalation', owner: 'Ministry of Energy', deadline: '24 hours', sector: 'Government' },
      { action: 'Activate fiscal stabilization fund drawdown to maintain government spending commitments', owner: 'Ministry of Finance', deadline: '48 hours', sector: 'Government' },
    ],
    outcome:
      'Surge capacity at secondary fields restores 60 percent of lost production within 48 hours. IEA coordination limits the global price impact to +$18/barrel versus +$35/barrel under uncoordinated response. Fiscal stabilization fund provides a 90-day spending bridge while full production recovery proceeds.',
    monitoringCriteria: [
      'Surge capacity output exceeds 3M barrels/day within 48 hours of activation',
      'IEA member states confirm reserve release commitments within 36 hours',
      'Saudi government bond yields remain within 25bps of pre-shock levels',
    ],
  },
  {
    id: 'uae_banking_crisis',
    title: 'UAE Banking Sector Stress',
    severity: 'High',
    domain: 'Financial',
    horizonHours: 72,
    sectors: ['Banking', 'Fintech', 'Real Estate', 'Insurance'],
    context:
      'Systemic stress has emerged across UAE banking institutions, triggered by rapid deterioration in real estate loan portfolios and accelerating cross-border capital flight. Three major banks have simultaneously breached minimum liquidity coverage ratios. The interbank market has frozen as counterparty risk repricing halts overnight lending.',
    significance:
      'The UAE banking sector is the largest in the GCC by assets. A liquidity crisis here does not remain contained — it propagates through correspondent banking relationships to every GCC state. The real estate exposure is the trigger, but the systemic risk is interbank contagion and payment system disruption.',
    transmissionFraming: 'Pressure transmits from real estate asset quality through bank balance sheets, the interbank market, and into the broader payment and settlement system.',
    transmission: [
      { from: 'UAE real estate market', to: 'Bank loan portfolios', mechanism: 'Non-performing loan surge on property exposure as valuations decline 15–22 percent', delayHours: 0 },
      { from: 'Bank loan portfolios', to: 'Interbank market', mechanism: 'Counterparty risk repricing freezes overnight lending — banks hoard liquidity', delayHours: 12 },
      { from: 'Interbank market', to: 'GCC banking system', mechanism: 'Cross-border contagion through correspondent banking and trade finance linkages', delayHours: 24 },
      { from: 'GCC banking system', to: 'Fintech and payment rails', mechanism: 'Settlement delays and credit line freezes disrupt digital payment infrastructure', delayHours: 36 },
    ],
    impactFraming: 'Four sectors face direct exposure, with banking and real estate bearing the primary stress and fintech and insurance absorbing secondary effects.',
    impact: [
      { entity: 'Emirates NBD', sector: 'Banking', exposure: 'Liquidity coverage ratio breach — $8B gap between required and available high-quality liquid assets', severity: 'Critical' },
      { entity: 'First Abu Dhabi Bank', sector: 'Banking', exposure: 'Real estate NPL ratio surges to 6.2 percent from 2.1 percent pre-crisis', severity: 'High' },
      { entity: 'Dubai real estate market', sector: 'Real Estate', exposure: 'Valuation markdown of 15–22 percent triggers margin calls on leveraged property holdings', severity: 'Severe' },
      { entity: 'UAE fintech ecosystem', sector: 'Fintech', exposure: 'Payment rail settlement delays as credit lines to payment service providers are frozen', severity: 'High' },
    ],
    decisionFraming: 'Three decisions are required to restore banking liquidity, contain equity market contagion, and prevent a forced liquidation cascade in property markets.',
    decisions: [
      { action: 'Activate emergency liquidity assistance facility with full collateral flexibility for affected banks', owner: 'Central Bank of the UAE', deadline: '6 hours', sector: 'Banking' },
      { action: 'Impose temporary short-selling restriction on listed bank equities to prevent speculative pressure', owner: 'Securities and Commodities Authority', deadline: '12 hours', sector: 'Banking' },
      { action: 'Issue standstill directive on real estate margin calls to prevent forced liquidation cascade', owner: 'CBUAE / RERA (joint)', deadline: '24 hours', sector: 'Real Estate' },
    ],
    outcome:
      'The emergency liquidity facility restores LCR compliance at all three affected banks within 48 hours. Short-selling restriction limits bank equity decline to 8–12 percent versus 25–35 percent under unrestricted trading. The standstill directive prevents a forced property liquidation spiral that would deepen bank losses by an additional $15B.',
    monitoringCriteria: [
      'All three affected banks report LCR above 100 percent within 48 hours of facility activation',
      'Interbank overnight lending resumes at volumes above 50 percent of normal within 72 hours',
      'No additional bank reports LCR breach in the 7 days following facility activation',
    ],
  },
  {
    id: 'qatar_lng_disruption',
    title: 'Qatar LNG Export Disruption',
    severity: 'High',
    domain: 'Energy',
    horizonHours: 168,
    sectors: ['Energy', 'Shipping', 'Government'],
    context:
      'A major operational failure at the Ras Laffan Industrial City has disrupted Qatar\'s LNG export operations. Qatar supplies approximately 22 percent of global LNG trade. European and Asian long-term contract holders have initiated force majeure discussions as delivery schedules are breached.',
    significance:
      'Qatar\'s economy is more concentrated on LNG than any other GCC state is on crude oil. A disruption to Ras Laffan does not merely reduce export revenue — it threatens the contractual architecture of global LNG supply, with cascading effects on European energy security and Asian industrial supply chains.',
    transmissionFraming: 'Pressure transmits from operational failure through global gas markets, contractual relationships, and sovereign fiscal position.',
    transmission: [
      { from: 'Ras Laffan operations', to: 'Global LNG supply', mechanism: 'Export terminal failure removes 77M tonnes/year of committed LNG supply from the market', delayHours: 0 },
      { from: 'Global LNG supply deficit', to: 'European gas markets', mechanism: 'Spot gas prices spike 40–60 percent as buyers scramble for alternative supply', delayHours: 12 },
      { from: 'Qatar fiscal revenue', to: 'Sovereign wealth fund', mechanism: 'Revenue shortfall triggers QIA drawdown for fiscal stabilization', delayHours: 48 },
    ],
    impactFraming: 'The disruption concentrates on Qatar but has global buyer-side consequences that amplify diplomatic and fiscal pressure.',
    impact: [
      { entity: 'QatarEnergy', sector: 'Energy', exposure: '$420M daily export revenue at risk from terminal shutdown', severity: 'Critical' },
      { entity: 'Qatar government', sector: 'Government', exposure: 'Fiscal surplus converts to deficit within 30 days if disruption persists', severity: 'High' },
      { entity: 'Asian LNG buyers', sector: 'Energy', exposure: 'Long-term contract delivery failure affecting 14 major industrial customers', severity: 'High' },
    ],
    decisionFraming: 'Three decisions are required to manage contractual exposure, deploy reserves, and accelerate alternative supply.',
    decisions: [
      { action: 'Invoke force majeure under all affected Sale and Purchase Agreements to limit contractual liability', owner: 'QatarEnergy Legal', deadline: '24 hours', sector: 'Energy' },
      { action: 'Deploy strategic LNG reserves from Ras Laffan storage to honor highest-priority contracts', owner: 'QatarEnergy Operations', deadline: '12 hours', sector: 'Energy' },
      { action: 'Accelerate North Field East expansion to bring partial additional capacity online', owner: 'Ministry of Energy and QatarEnergy', deadline: '72 hours', sector: 'Government' },
    ],
    outcome:
      'Strategic reserves cover 15 percent of contracted volume for 10 days, buying time for operational restoration. Force majeure limits legal exposure on breached contracts. North Field East acceleration provides partial additional capacity within 14 days if restoration is delayed.',
    monitoringCriteria: [
      'Ras Laffan operational status — restoration timeline confirmed within 48 hours',
      'No major buyer terminates a long-term SPA within the 14-day monitoring window',
      'Qatar sovereign CDS spread remains below 80bps',
    ],
  },
  {
    id: 'regional_liquidity_stress_event',
    title: 'Regional Liquidity Stress',
    severity: 'High',
    domain: 'Financial',
    horizonHours: 48,
    sectors: ['Banking', 'Fintech', 'Insurance', 'Government'],
    context:
      'Overnight interbank rates across the GCC have spiked 300 basis points in a single session. Three banks — one in the UAE, one in Saudi Arabia, one in Bahrain — have failed to meet overnight reserve requirements. The interbank market has effectively frozen as institutions hoard liquidity and refuse to lend to perceived weaker counterparties.',
    significance:
      'Interbank market freezes are the fastest-propagating financial contagion vector. Within 24 hours, the freeze cascades from overnight lending into trade finance, SME credit lines, and payment settlement. The 48-hour horizon is not arbitrary — it is the window before retail depositor confidence begins to erode.',
    transmissionFraming: 'Pressure transmits from the interbank market through trade finance and SME lending into the real economy within 24 hours.',
    transmission: [
      { from: 'Interbank overnight market', to: 'Overnight lending', mechanism: 'Rate spike of 300bps triggers collateral calls and counterparty risk reassessment', delayHours: 0 },
      { from: 'Overnight lending freeze', to: 'Trade finance', mechanism: 'Banks freeze credit lines to trade finance counterparties perceived as higher risk', delayHours: 8 },
      { from: 'Trade finance freeze', to: 'Real economy', mechanism: 'Import financing disruption affects food, industrial inputs, and consumer goods supply chains', delayHours: 24 },
    ],
    impactFraming: 'Banking and fintech bear the direct stress; government faces secondary pressure through import supply chain disruption.',
    impact: [
      { entity: 'GCC interbank system', sector: 'Banking', exposure: 'Overnight rate +300bps with three banks in reserve requirement breach', severity: 'Critical' },
      { entity: 'SME lending ecosystem', sector: 'Fintech', exposure: 'Credit line freezes affect an estimated 180,000 SMEs across the region', severity: 'High' },
      { entity: 'Import financing', sector: 'Banking', exposure: 'Letter of credit issuance halted at four major banks pending liquidity resolution', severity: 'High' },
    ],
    decisionFraming: 'Two decisions are required — one immediate (central bank liquidity injection) and one within 24 hours (SME credit backstop).',
    decisions: [
      { action: 'Inject emergency overnight liquidity via expanded repo facility with broadened collateral eligibility', owner: 'GCC central banks (coordinated)', deadline: '4 hours', sector: 'Banking' },
      { action: 'Activate SME credit guarantee backstop through development bank facilities', owner: 'GCC development banks', deadline: '24 hours', sector: 'Fintech' },
    ],
    outcome:
      'Repo injection normalizes overnight rates within 12 hours and restores interbank lending volumes to 70 percent of normal within 24 hours. The SME credit guarantee prevents a credit contraction cascade that would otherwise reduce regional SME lending by 30–40 percent over the following quarter.',
    monitoringCriteria: [
      'Overnight interbank rate returns within 50bps of pre-stress level within 24 hours',
      'All three banks in reserve breach return to compliance within 36 hours',
      'No retail deposit outflow exceeding 2 percent at any single institution',
    ],
  },
  {
    id: 'financial_infrastructure_cyber_disruption',
    title: 'Financial System Cyber Attack',
    severity: 'High',
    domain: 'Cyber & Financial',
    horizonHours: 24,
    sectors: ['Banking', 'Fintech', 'Government'],
    context:
      'A targeted cyber attack has compromised RTGS and payment clearing systems across two GCC states. Interbank settlement is halted. ATM networks are offline. Card payment processing is intermittent. The attack vector suggests a sophisticated state-sponsored or organized criminal operation.',
    significance:
      'Modern economies cannot function without payment settlement. Every hour of RTGS downtime accumulates a transaction backlog that compounds non-linearly. The 24-hour horizon reflects the maximum tolerable outage before public confidence in the banking system begins to erode and cash hoarding behavior emerges.',
    transmissionFraming: 'Pressure transmits from infrastructure compromise through settlement systems into commercial activity within 6 hours.',
    transmission: [
      { from: 'Settlement infrastructure', to: 'Interbank payments', mechanism: 'RTGS system compromise halts all high-value interbank settlement', delayHours: 0 },
      { from: 'Interbank payments', to: 'Commercial banking', mechanism: 'Transaction processing freeze — no new transfers, no salary payments, no vendor settlements', delayHours: 2 },
      { from: 'Commercial banking', to: 'Economic activity', mechanism: 'Cash hoarding and payment disruption halt commercial activity in affected states', delayHours: 6 },
    ],
    impactFraming: 'The disruption is concentrated in payment infrastructure but radiates into every sector through commercial activity disruption.',
    impact: [
      { entity: 'GCC RTGS systems', sector: 'Fintech', exposure: 'Complete settlement halt across two states', severity: 'Critical' },
      { entity: 'Commercial banks', sector: 'Banking', exposure: 'Transaction backlog accumulating at $2.4B per hour of downtime', severity: 'Severe' },
      { entity: 'GCC economic activity', sector: 'Government', exposure: 'GDP loss estimated at $850M per 24 hours of full outage', severity: 'High' },
    ],
    decisionFraming: 'Three decisions are required within 4 hours to restore critical payment capability and contain the forensic investigation.',
    decisions: [
      { action: 'Activate backup settlement system on isolated infrastructure to restore critical payment flows', owner: 'Central banks (affected states)', deadline: '2 hours', sector: 'Banking' },
      { action: 'Deploy national CERT forensic response team to identify attack vector and contain lateral movement', owner: 'National Cybersecurity Authority', deadline: '1 hour', sector: 'Government' },
      { action: 'Enable bilateral netting for critical high-value transactions while RTGS is offline', owner: 'Central banks (affected states)', deadline: '4 hours', sector: 'Banking' },
    ],
    outcome:
      'Backup settlement restores critical payment flows within 4 hours, covering salary payments, government transactions, and high-value commercial settlements. Bilateral netting processes the $18B accumulated backlog within 12 hours. Full RTGS restoration is achieved within 18–24 hours once forensic containment is confirmed.',
    monitoringCriteria: [
      'Backup settlement system processes first transactions within 4 hours of activation',
      'CERT confirms attack vector containment within 12 hours',
      'No secondary compromise detected on backup infrastructure within 48 hours',
    ],
  },
  {
    id: 'red_sea_trade_corridor_instability',
    title: 'Red Sea Corridor Instability',
    severity: 'Elevated',
    domain: 'Maritime & Trade',
    horizonHours: 168,
    sectors: ['Shipping', 'Insurance', 'Energy', 'Banking'],
    context:
      'Sustained security threats along the Red Sea corridor have forced major shipping lines to reroute around the Cape of Good Hope. Transit times for GCC-bound cargo increase by 10–14 days. Marine insurance premiums on Red Sea routes have surged, making direct transit commercially unviable for most carriers.',
    significance:
      'The Red Sea corridor handles approximately 12 percent of global trade. GCC states are disproportionately affected because they depend on this route for European imports and Suez Canal transit revenue. Unlike a sudden disruption, this scenario involves sustained degradation — the costs accumulate daily and compound through supply chain repricing.',
    transmissionFraming: 'Pressure transmits slowly but persistently from shipping rerouting through freight costs, import prices, and consumer inflation.',
    transmission: [
      { from: 'Red Sea corridor', to: 'Suez Canal traffic', mechanism: 'Vessel rerouting away from Bab el-Mandeb reduces canal traffic by 40 percent', delayHours: 0 },
      { from: 'Suez Canal traffic reduction', to: 'GCC import costs', mechanism: 'Freight rate surge of 180–250 percent on affected routes with 10–14 day schedule delays', delayHours: 48 },
      { from: 'GCC import costs', to: 'Consumer prices', mechanism: 'Supply chain cost pass-through drives imported inflation of 1.2–1.8 percent across the region', delayHours: 96 },
    ],
    impactFraming: 'Shipping and insurance bear the direct cost; governments face inflationary pressure on essential imports.',
    impact: [
      { entity: 'GCC import supply chain', sector: 'Shipping', exposure: 'Freight costs increase 180–250 percent on all Red Sea routes', severity: 'High' },
      { entity: 'Marine insurance market', sector: 'Insurance', exposure: 'War-risk premium surge makes direct Red Sea transit commercially unviable', severity: 'Elevated' },
      { entity: 'GCC consumer prices', sector: 'Government', exposure: 'Imported inflation of 1.2–1.8 percent on essential goods', severity: 'Elevated' },
    ],
    decisionFraming: 'Three decisions address supply continuity, freight cost management, and insurance market stabilization.',
    decisions: [
      { action: 'Activate strategic commodity reserves to buffer essential goods supply gaps during rerouting period', owner: 'Ministries of Commerce', deadline: '72 hours', sector: 'Government' },
      { action: 'Negotiate emergency freight corridor agreements with major shipping lines for priority GCC cargo', owner: 'GCC port authorities (coordinated)', deadline: '96 hours', sector: 'Shipping' },
      { action: 'Issue revised marine cargo insurance guidance to enable selective direct transit for critical cargo', owner: 'Insurance regulatory authorities', deadline: '48 hours', sector: 'Insurance' },
    ],
    outcome:
      'Strategic reserves cover a 30-day supply gap for essential goods. Emergency freight corridor agreements reduce the cost premium from 250 percent to approximately 120 percent for priority cargo. Insurance guidance enables selective direct transit for military-escorted convoys carrying critical medical and food supplies.',
    monitoringCriteria: [
      'Essential goods stockout reports — zero tolerance threshold during the disruption window',
      'Average freight rate on GCC-bound routes declines from peak within 14 days of corridor agreements',
      'Imported inflation reading at next monthly CPI release',
    ],
  },
  {
    id: 'gcc_cyber_attack',
    title: 'GCC Cyber Infrastructure Attack',
    severity: 'Elevated',
    domain: 'Cyber',
    horizonHours: 48,
    sectors: ['Banking', 'Fintech', 'Government', 'Energy'],
    context:
      'A coordinated cyber attack has targeted financial infrastructure across three GCC states. SWIFT connectivity is degraded, ATM networks are intermittently offline, and payment gateways are experiencing processing failures. The attack appears designed to disrupt rather than extract — a denial-of-service campaign against financial infrastructure.',
    significance:
      'Unlike a targeted attack on a single institution, this campaign affects the shared infrastructure layer that all banks and fintech companies depend on. The coordinated nature across three states suggests a well-resourced threat actor. The primary risk is not financial loss but erosion of public confidence in digital payment systems.',
    transmissionFraming: 'Pressure transmits from infrastructure outage through consumer banking, commercial settlement, and cross-border trade in stages.',
    transmission: [
      { from: 'Payment infrastructure', to: 'Consumer banking', mechanism: 'ATM and card network outages across three states affect 42 million customers', delayHours: 0 },
      { from: 'Consumer banking disruption', to: 'Commercial settlement', mechanism: 'B2B payment delays cascade as banks prioritize retail transaction recovery', delayHours: 6 },
      { from: 'Commercial settlement delays', to: 'Cross-border trade', mechanism: 'Letter of credit processing halts pending payment system verification', delayHours: 12 },
    ],
    impactFraming: 'Fintech infrastructure bears the technical impact; banking and government absorb the operational and reputational consequences.',
    impact: [
      { entity: 'GCC payment networks', sector: 'Fintech', exposure: 'Full or intermittent outage affecting digital payments across three states', severity: 'Critical' },
      { entity: 'GCC retail banking', sector: 'Banking', exposure: '42 million customers unable to access routine banking services', severity: 'High' },
      { entity: 'Trade finance operations', sector: 'Banking', exposure: 'LC processing halted at 6 major banks pending system integrity verification', severity: 'Elevated' },
    ],
    decisionFraming: 'Three decisions are required — incident response, operational continuity, and public communication.',
    decisions: [
      { action: 'Activate national CERT incident response protocol with cross-border intelligence sharing', owner: 'National Cybersecurity Authorities', deadline: '1 hour', sector: 'Government' },
      { action: 'Switch to manual settlement procedures for critical payment transactions', owner: 'Central banks (affected states)', deadline: '4 hours', sector: 'Banking' },
      { action: 'Issue coordinated public communications confirming deposit safety and outlining restoration timeline', owner: 'Central banks and finance ministries', deadline: '6 hours', sector: 'Government' },
    ],
    outcome:
      'Manual settlement restores critical payment flows within 8 hours. Full automated system recovery is estimated at 36–48 hours. The public communication strategy prevents a depositor confidence crisis. The 6-hour communication deadline is critical — historical precedent shows that depositor anxiety escalates sharply after 8 hours of unexplained service disruption.',
    monitoringCriteria: [
      'Manual settlement procedures operational at all major banks within 8 hours',
      'No depositor queue or withdrawal surge reported at any branch after public communications',
      'Full automated payment processing restored within 48 hours',
    ],
  },
  {
    id: 'energy_market_volatility_shock',
    title: 'Energy Market Volatility',
    severity: 'Elevated',
    domain: 'Energy & Fiscal',
    horizonHours: 72,
    sectors: ['Energy', 'Government', 'Banking'],
    context:
      'Extreme intraday volatility in global energy markets — Brent crude swinging $15/barrel within single trading sessions — has invalidated GCC fiscal planning assumptions. Budget projections based on $75–85/barrel are no longer reliable. Sovereign wealth fund holdings in energy-linked assets face mark-to-market losses.',
    significance:
      'GCC fiscal planning depends on oil price stability within a forecast band. When volatility exceeds the band, budget commitments become unfunded, government spending must be frozen or reduced, and the banking sector — which holds large government deposits — faces liquidity uncertainty. The issue is not the price level but the unpredictability.',
    transmissionFraming: 'Pressure transmits from price volatility through fiscal forecasting, government spending, and banking liquidity.',
    transmission: [
      { from: 'Energy markets', to: 'Sovereign budgets', mechanism: 'Revenue forecast deviation of $8–12B across GCC states as price band assumptions break', delayHours: 0 },
      { from: 'Sovereign budgets', to: 'Government spending', mechanism: 'Precautionary expenditure freeze triggered as finance ministries reassess fiscal capacity', delayHours: 24 },
      { from: 'Government spending contraction', to: 'Banking sector', mechanism: 'Reduced government deposits and delayed payments to contractors pressure bank liquidity', delayHours: 48 },
    ],
    impactFraming: 'Government fiscal capacity absorbs the primary shock; banking experiences secondary liquidity pressure.',
    impact: [
      { entity: 'GCC finance ministries', sector: 'Government', exposure: 'Combined budget deviation of $8–12B from fiscal year projections', severity: 'High' },
      { entity: 'Sovereign wealth funds', sector: 'Government', exposure: 'Mark-to-market losses on energy-linked holdings', severity: 'Elevated' },
      { entity: 'GCC banking sector', sector: 'Banking', exposure: 'Government deposit volatility as spending patterns become unpredictable', severity: 'Elevated' },
    ],
    decisionFraming: 'Two decisions address fiscal stabilization and hedging guidance.',
    decisions: [
      { action: 'Activate fiscal buffer drawdown protocol to maintain spending commitments during volatility window', owner: 'Finance ministries', deadline: '24 hours', sector: 'Government' },
      { action: 'Issue hedging guidance for state-owned enterprises to limit further mark-to-market exposure', owner: 'Sovereign wealth fund governance boards', deadline: '48 hours', sector: 'Government' },
    ],
    outcome:
      'Fiscal buffers absorb the short-term revenue deviation and maintain government spending continuity. SOE hedging guidance limits incremental mark-to-market losses. The volatility window is expected to normalize within 7–10 days based on historical patterns.',
    monitoringCriteria: [
      'Brent crude intraday volatility returns below $5/barrel within 7 trading days',
      'No GCC government announces spending cuts or project delays within 30 days',
    ],
  },
  {
    id: 'oman_port_closure',
    title: 'Oman Port Closure',
    severity: 'Elevated',
    domain: 'Logistics',
    horizonHours: 72,
    sectors: ['Shipping', 'Energy', 'Government'],
    context:
      'Salalah and Sohar ports — Oman\'s two major maritime facilities — have been closed due to severe weather and infrastructure damage. Salalah handles significant container transshipment for the wider Indian Ocean trade network. Sohar is a key petrochemical and metals export hub.',
    significance:
      'Oman\'s ports serve as overflow and transshipment capacity for the broader GCC. Their closure forces rerouting to already-congested Jebel Ali and Dammam, creating cascading delays across the regional supply chain.',
    transmissionFraming: 'Pressure transmits from Omani port closure through container transshipment networks and into regional supply chain timelines.',
    transmission: [
      { from: 'Salalah and Sohar ports', to: 'Container transshipment', mechanism: 'Operational closure halts 3.8M TEU annual transshipment throughput', delayHours: 0 },
      { from: 'Container transshipment halt', to: 'GCC supply chain', mechanism: 'Rerouting to Jebel Ali and Dammam adds congestion and 3–5 day delays', delayHours: 24 },
      { from: 'GCC supply chain delays', to: 'Retail and manufacturing', mechanism: 'Delivery delays of 7–14 days for imported goods and industrial inputs', delayHours: 48 },
    ],
    impactFraming: 'Oman bears the direct operational loss; the wider GCC absorbs supply chain delay costs.',
    impact: [
      { entity: 'Port of Salalah', sector: 'Shipping', exposure: '3.8M TEU annual throughput halted — transshipment customers diverted', severity: 'Severe' },
      { entity: 'Omani economy', sector: 'Government', exposure: 'Trade corridor revenue loss and petrochemical export delays', severity: 'High' },
      { entity: 'GCC importers', sector: 'Shipping', exposure: 'Supply chain delays of 7–14 days on goods transiting through Omani ports', severity: 'Elevated' },
    ],
    decisionFraming: 'Two decisions are required to manage the diversion and prevent secondary customs bottlenecks.',
    decisions: [
      { action: 'Redirect transshipment to Jebel Ali and Dammam with priority berth allocation for diverted vessels', owner: 'Port authorities (UAE and KSA)', deadline: '12 hours', sector: 'Shipping' },
      { action: 'Activate emergency customs clearance procedures for all diverted cargo to prevent secondary delays', owner: 'Customs authorities (UAE and KSA)', deadline: '24 hours', sector: 'Government' },
    ],
    outcome:
      'Diversion absorbs approximately 70 percent of affected transshipment volume within 48 hours. Emergency customs procedures prevent the diversion from creating a secondary bottleneck at receiving ports. Full Omani port restoration is estimated at 5–7 days.',
    monitoringCriteria: [
      'Jebel Ali and Dammam average vessel wait time remains below 48 hours during diversion period',
      'Salalah and Sohar operational status updates published every 12 hours',
    ],
  },
  {
    id: 'bahrain_sovereign_stress',
    title: 'Bahrain Fiscal Stress',
    severity: 'Guarded',
    domain: 'Sovereign & Fiscal',
    horizonHours: 720,
    sectors: ['Government', 'Banking'],
    context:
      'Sustained low oil revenue has widened Bahrain\'s fiscal deficit and accelerated sovereign debt accumulation. Debt-to-GDP has exceeded 120 percent. International credit rating agencies have placed the Kingdom on negative outlook review.',
    significance:
      'Bahrain is the most fiscally constrained GCC state. A sovereign rating downgrade would reprice the entire Bahraini banking sector through the sovereign-bank nexus — banks hold large sovereign bond portfolios whose value is tied to the sovereign rating. The 30-day horizon reflects the typical rating agency review cycle.',
    transmissionFraming: 'Pressure transmits slowly from fiscal deterioration through sovereign rating and into banking sector asset values.',
    transmission: [
      { from: 'Oil revenue shortfall', to: 'Fiscal balance', mechanism: 'Sustained revenue underperformance widens deficit beyond consolidation targets', delayHours: 0 },
      { from: 'Fiscal balance deterioration', to: 'Sovereign credit rating', mechanism: 'Rating agencies trigger formal review — negative outlook places downgrade within 30–60 days', delayHours: 720 },
      { from: 'Sovereign rating pressure', to: 'Banking sector', mechanism: 'Sovereign-bank nexus reprices bank bond holdings and increases funding costs', delayHours: 720 },
    ],
    impactFraming: 'Government fiscal capacity is the primary concern; banking faces secondary exposure through sovereign bond holdings.',
    impact: [
      { entity: 'Kingdom of Bahrain', sector: 'Government', exposure: 'Deficit widening to 8 percent of GDP with debt sustainability under question', severity: 'Elevated' },
      { entity: 'Bahraini banking sector', sector: 'Banking', exposure: 'Sovereign exposure repricing if downgrade materializes — estimated $2–3B mark-to-market loss', severity: 'Guarded' },
    ],
    decisionFraming: 'Two medium-term decisions are required to address the rating review and secure fiscal sustainability.',
    decisions: [
      { action: 'Accelerate fiscal consolidation program with specific expenditure reduction targets to present to rating agencies', owner: 'Ministry of Finance', deadline: '30 days', sector: 'Government' },
      { action: 'Negotiate GCC fiscal support package to demonstrate sovereign backstop to international creditors', owner: 'GCC Finance Ministers Council', deadline: '60 days', sector: 'Government' },
    ],
    outcome:
      'A credible fiscal consolidation program combined with a GCC support package has historically been sufficient to maintain Bahrain\'s investment-grade rating. The 2018 precedent — a $10B GCC support package — stabilized markets and prevented a downgrade cycle. The decision path must be visibly in motion before the rating review concludes.',
    monitoringCriteria: [
      'Rating agency confirms review timeline within 14 days',
      'GCC Finance Ministers Council issues support commitment statement within 45 days',
      'Bahrain sovereign CDS spread remains below 350bps',
    ],
  },
  {
    id: 'kuwait_fiscal_shock',
    title: 'Kuwait Oil Revenue Shock',
    severity: 'Guarded',
    domain: 'Sovereign & Fiscal',
    horizonHours: 720,
    sectors: ['Government', 'Banking', 'Energy'],
    context:
      'Kuwait faces a sustained oil revenue shock from OPEC+ production quota tightening coinciding with a global demand slowdown. The General Reserve Fund is being drawn down at an accelerating rate. Parliamentary debate on accessing the Future Generations Fund has intensified political pressure on the government.',
    significance:
      'Kuwait\'s fiscal structure is uniquely constrained — the parliament controls debt issuance authority, and political deadlock has prevented new borrowing for years. Without debt market access, the government depends entirely on reserve fund drawdowns, which have a finite runway. The political dimension makes this scenario as much a governance challenge as a fiscal one.',
    transmissionFraming: 'Pressure transmits from revenue shortfall through reserve drawdown and spending caps into banking sector deposits.',
    transmission: [
      { from: 'Oil revenue decline', to: 'General Reserve Fund', mechanism: 'Accelerated drawdown as expenditure exceeds revenue by widening margin', delayHours: 0 },
      { from: 'General Reserve Fund depletion trajectory', to: 'Government spending', mechanism: 'Expenditure caps triggered as fund runway shortens below 18-month threshold', delayHours: 168 },
    ],
    impactFraming: 'Government fiscal capacity is the primary concern; banking faces secondary effects through government deposit reduction.',
    impact: [
      { entity: 'State of Kuwait', sector: 'Government', exposure: 'Reserve fund drawdown acceleration — runway estimated at 24–30 months at current pace', severity: 'Elevated' },
      { entity: 'Kuwaiti banking sector', sector: 'Banking', exposure: 'Government deposit reduction of 10–15 percent over 6 months', severity: 'Guarded' },
    ],
    decisionFraming: 'Two decisions are required — one near-term (debt issuance) and one structural (revenue diversification).',
    decisions: [
      { action: 'Implement sovereign debt issuance program — requires parliamentary approval of new debt law', owner: 'Ministry of Finance / National Assembly', deadline: '30 days', sector: 'Government' },
      { action: 'Advance VAT framework legislation to establish non-oil revenue source', owner: 'National Assembly / Ministry of Finance', deadline: '90 days', sector: 'Government' },
    ],
    outcome:
      'Debt issuance bridges the fiscal gap without depleting reserves, extending the fiscal runway from 24 months to 5+ years. VAT implementation provides a structural non-oil revenue source estimated at 1.5–2 percent of GDP annually. The political risk is the binding constraint — parliamentary approval timelines are uncertain.',
    monitoringCriteria: [
      'Parliamentary committee advances debt law to floor vote within 30 days',
      'General Reserve Fund drawdown rate — monthly reporting confirms trend',
      'Kuwait sovereign rating remains stable through the monitoring period',
    ],
  },
];

/* ── Lookup helpers ── */

const byId = new Map(manifest.map((s) => [s.id, s]));

export function getScenario(id: string): ScenarioBriefing | undefined {
  return byId.get(id);
}

export function getAllScenarios(): ScenarioBriefing[] {
  return manifest;
}

const tierOrder: Record<string, number> = { Severe: 0, High: 1, Elevated: 2, Guarded: 3 };

export function getScenariosBySeverity(): ScenarioBriefing[] {
  return [...manifest].sort((a, b) => (tierOrder[a.severity] ?? 9) - (tierOrder[b.severity] ?? 9));
}
