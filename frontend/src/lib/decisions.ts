/**
 * Impact Observatory | مرصد الأثر — Decision Briefing Manifest
 *
 * Sovereign-grade directive data for 15 GCC macro scenarios.
 * Each briefing elevates the primary directive and subordinates supporting actions.
 *
 * Structure:
 *   Directive Identity → Primary Directive → Supporting Actions → Expected Effect → Footer
 *
 * Static for SSG. Derived from scenario manifest decision data.
 */

/* ── Types ── */

export interface PrimaryDirective {
  action: string;
  owner: string;
  deadline: string;
  sector: string;
  rationale: string;
  consequenceOfInaction: string;
}

export interface SupportingAction {
  action: string;
  owner: string;
  deadline: string;
  sector: string;
}

export interface DecisionBriefing {
  id: string;
  directiveTitle: string;
  classification: 'Severe' | 'High' | 'Elevated' | 'Guarded';
  scenarioRef: string;
  summary: string;
  primaryDirective: PrimaryDirective;
  supportingActions: SupportingAction[];
  expectedEffect: string;
  monitoringCriteria: string[];
  issued: string;
  distribution: string[];
}

/* ── Manifest ── */

const manifest: DecisionBriefing[] = [
  {
    id: 'hormuz_chokepoint_disruption',
    directiveTitle: 'Activate Hormuz Emergency Protocol',
    classification: 'Severe',
    scenarioRef: 'hormuz_chokepoint_disruption',
    summary: 'Coordinate strategic reserve release and alternative export routing to contain projected $14.2B economic loss within a 72-hour disruption window.',
    primaryDirective: {
      action: 'Activate strategic petroleum reserve release protocol to signal supply continuity to global markets.',
      owner: 'Ministry of Energy (KSA)',
      deadline: '4 hours',
      sector: 'Energy',
      rationale: 'The reserve release is the single highest-leverage action available. It caps the global price spike, reassures consuming nations, and buys time for pipeline rerouting. Every hour of delay adds approximately $180M in cascading economic exposure across GCC export revenues.',
      consequenceOfInaction: 'Without reserve release within 4 hours, Brent crude exceeds $140/barrel, triggering secondary demand destruction and a sovereign revenue feedback loop. Projected loss escalates from $5.8B to $22B by day 5.',
    },
    supportingActions: [
      { action: 'Invoke force majeure on affected cargo contracts to limit legal exposure for national oil companies.', owner: 'ADNOC / Saudi Aramco Legal', deadline: '12 hours', sector: 'Energy' },
      { action: 'Trigger emergency liquidity backstop for trade finance portfolios exposed to Gulf shipping routes.', owner: 'Central Bank of the UAE', deadline: '24 hours', sector: 'Banking' },
      { action: 'Activate alternative export routing through the Fujairah–Habshan pipeline at maximum throughput.', owner: 'ADNOC Pipeline Operations', deadline: '6 hours', sector: 'Energy' },
      { action: 'Issue revised war-risk underwriting guidance to prevent complete marine cargo insurance withdrawal.', owner: 'UAE Insurance Authority', deadline: '48 hours', sector: 'Insurance' },
    ],
    expectedEffect: 'If strategic reserves are released within 4 hours and alternative pipeline routing activates within 6 hours, projected economic loss is reduced from $14.2B to $5.8B over the 72-hour horizon. The liquidity backstop prevents trade finance contagion from reaching the interbank market. Insurance market function is restored within 5 days.',
    monitoringCriteria: [
      'Brent crude spot price stabilizes below $130/barrel within 48 hours of reserve release',
      'Fujairah pipeline throughput reaches 1.5M barrels/day within 12 hours of activation',
      'No GCC bank reports LCR breach in the 72-hour window following liquidity backstop activation',
      'Marine cargo insurance issuance resumes on Gulf routes within 5 business days',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Ministry of Energy (KSA)', 'ADNOC', 'Central Bank of the UAE', 'UAE Insurance Authority'],
  },
  {
    id: 'hormuz_full_closure',
    directiveTitle: 'Execute GCC-Wide Emergency Coordination',
    classification: 'Severe',
    scenarioRef: 'hormuz_full_closure',
    summary: 'Coordinate simultaneous sovereign action across all six GCC states to contain economic damage from total Hormuz closure to $22B versus $55B under fragmented response.',
    primaryDirective: {
      action: 'Coordinate simultaneous strategic reserve release across all six GCC states and request IEA emergency action.',
      owner: 'GCC Supreme Council',
      deadline: '2 hours',
      sector: 'Government',
      rationale: 'Full closure is a global energy emergency. Unilateral state responses fragment the market signal and delay price stabilization. Only coordinated GCC-wide action, combined with IEA engagement, provides sufficient supply assurance to prevent market collapse.',
      consequenceOfInaction: 'Without coordination within 2 hours, individual state responses diverge and market confidence collapses. The 72-hour loss estimate rises from $22B to $55B as consuming nations begin emergency rationing.',
    },
    supportingActions: [
      { action: 'Activate all alternative pipeline export capacity — Fujairah, East-West, and IPSA lines at maximum throughput.', owner: 'National oil companies (joint)', deadline: '4 hours', sector: 'Energy' },
      { action: 'Establish emergency interbank liquidity facility with combined central bank backstop.', owner: 'GCC central banks (coordinated)', deadline: '12 hours', sector: 'Banking' },
    ],
    expectedEffect: 'Coordinated response limits total economic damage to $22B over 72 hours versus $41B under uncoordinated action. Alternative pipeline routes restore approximately 30 percent of export capacity within 6 hours. The interbank facility prevents a regional banking crisis.',
    monitoringCriteria: [
      'IEA confirms coordinated reserve release within 6 hours of Supreme Council request',
      'Combined alternative pipeline throughput exceeds 3M barrels/day within 8 hours',
      'No GCC central bank invokes emergency lending facility beyond the coordinated backstop',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['GCC Supreme Council', 'National oil companies (joint)', 'GCC central banks'],
  },
  {
    id: 'iran_regional_escalation',
    directiveTitle: 'Activate Joint Defense and Capital Stabilization',
    classification: 'Severe',
    scenarioRef: 'iran_regional_escalation',
    summary: 'Deploy coordinated defense, financial, and diplomatic measures to limit capital flight to $8B versus $25B and prevent energy infrastructure damage over a 7-day escalation window.',
    primaryDirective: {
      action: 'Activate GCC Joint Defense Council protocols and establish unified command for infrastructure protection.',
      owner: 'GCC Defense Council',
      deadline: '2 hours',
      sector: 'Government',
      rationale: 'Physical infrastructure protection is the prerequisite for every other mitigation. If energy facilities sustain damage, capital flight accelerates beyond any financial intervention capacity. The defense posture also provides the credible deterrent that enables diplomatic de-escalation.',
      consequenceOfInaction: 'Without unified defense coordination, individual state responses create gaps in infrastructure protection. Any physical damage to energy facilities triggers an immediate $15–25B capital flight that overwhelms financial controls.',
    },
    supportingActions: [
      { action: 'Impose temporary capital flow controls to limit outflow velocity while markets stabilize.', owner: 'GCC central banks (coordinated)', deadline: '12 hours', sector: 'Banking' },
      { action: 'Coordinate strategic reserve release with IEA to cap energy price escalation.', owner: 'Energy ministries (coordinated)', deadline: '24 hours', sector: 'Energy' },
      { action: 'Activate diplomatic de-escalation channels through multilateral intermediaries.', owner: 'GCC foreign ministries', deadline: '6 hours', sector: 'Government' },
    ],
    expectedEffect: 'Capital controls limit outflow to $8B versus $25B under unrestricted conditions. Strategic reserve coordination prevents energy price overshoot beyond $145/barrel. The critical monitoring window is 7 days — if no infrastructure damage occurs and diplomatic channels produce a de-escalation signal, market confidence stabilizes within 14 days.',
    monitoringCriteria: [
      'Daily foreign capital outflow rate declines below $1B/day within 5 days of capital controls',
      'No physical damage to GCC energy infrastructure within the 7-day monitoring window',
      'Diplomatic channel produces a public de-escalation statement within 7 days',
      'GCC sovereign CDS spreads stabilize within 50bps of pre-escalation levels by day 10',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['GCC Defense Council', 'GCC central banks', 'Energy ministries', 'GCC foreign ministries'],
  },
  {
    id: 'critical_port_throughput_disruption',
    directiveTitle: 'Declare Multi-Port Force Majeure and Activate Supply Corridors',
    classification: 'Severe',
    scenarioRef: 'critical_port_throughput_disruption',
    summary: 'Manage 60 percent maritime capacity loss through emergency supply corridors and coordinated tanker queue management to prevent essential goods shortages within 5–7 days.',
    primaryDirective: {
      action: 'Declare force majeure on affected port contracts and activate regional port mutual-aid agreements.',
      owner: 'Port authorities (coordinated)',
      deadline: '6 hours',
      sector: 'Shipping',
      rationale: 'Force majeure declaration is the legal prerequisite for activating mutual-aid agreements between GCC ports. Without it, diversion capacity at Jebel Ali and Dammam cannot be formally allocated and priority berth assignments cannot be enforced.',
      consequenceOfInaction: 'Without force majeure and mutual-aid activation within 6 hours, the 200+ vessel tanker queue grows at a rate that creates a secondary energy market disruption. Essential goods shortages become probable by day 5.',
    },
    supportingActions: [
      { action: 'Activate emergency food, medical, and essential goods supply corridors via air and overland routes.', owner: 'Civil defense authorities', deadline: '12 hours', sector: 'Government' },
      { action: 'Coordinate tanker queue management through OPEC secretariat to prevent secondary energy market disruption.', owner: 'Energy ministries', deadline: '24 hours', sector: 'Energy' },
    ],
    expectedEffect: 'Emergency supply corridors maintain essential goods availability throughout the disruption window. Tanker queue management prevents a secondary energy price spike. Full port restoration is targeted within 7 days.',
    monitoringCriteria: [
      'Emergency supply corridors operational within 18 hours of activation order',
      'No essential goods stockout reported in any GCC state during the disruption window',
      'Port throughput restored to 50 percent of normal capacity within 5 days',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Port authorities (coordinated)', 'Civil defense authorities', 'Energy ministries'],
  },
  {
    id: 'saudi_oil_shock',
    directiveTitle: 'Restore Saudi Production Capacity',
    classification: 'High',
    scenarioRef: 'saudi_oil_shock',
    summary: 'Activate surge capacity and coordinate international reserve release to restore 60 percent of lost production within 48 hours and limit global price impact to +$18/barrel.',
    primaryDirective: {
      action: 'Activate Shaybah and Khurais surge capacity to restore partial production within 48 hours.',
      owner: 'Saudi Aramco Operations',
      deadline: '12 hours',
      sector: 'Energy',
      rationale: 'Surge capacity activation is the only measure that directly addresses the supply deficit. IEA coordination and fiscal stabilization are necessary but insufficient without physical production restoration. The 12-hour activation deadline ensures the market receives a credible production recovery signal before the next trading session.',
      consequenceOfInaction: 'Without surge activation within 12 hours, global markets price in a sustained 5.7M barrel/day supply deficit. Brent crude exceeds $135/barrel and Saudi fiscal revenue loss compounds to $8–12B over 30 days.',
    },
    supportingActions: [
      { action: 'Request IEA coordinated strategic reserve release to cap global price escalation.', owner: 'Ministry of Energy', deadline: '24 hours', sector: 'Government' },
      { action: 'Activate fiscal stabilization fund drawdown to maintain government spending commitments.', owner: 'Ministry of Finance', deadline: '48 hours', sector: 'Government' },
    ],
    expectedEffect: 'Surge capacity at secondary fields restores 60 percent of lost production within 48 hours. IEA coordination limits the global price impact to +$18/barrel versus +$35/barrel under uncoordinated response. Fiscal stabilization fund provides a 90-day spending bridge.',
    monitoringCriteria: [
      'Surge capacity output exceeds 3M barrels/day within 48 hours of activation',
      'IEA member states confirm reserve release commitments within 36 hours',
      'Saudi government bond yields remain within 25bps of pre-shock levels',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Saudi Aramco Operations', 'Ministry of Energy', 'Ministry of Finance'],
  },
  {
    id: 'uae_banking_crisis',
    directiveTitle: 'Stabilize UAE Banking Liquidity',
    classification: 'High',
    scenarioRef: 'uae_banking_crisis',
    summary: 'Deploy emergency liquidity assistance and impose targeted market restrictions to restore bank LCR compliance within 48 hours and prevent a forced property liquidation cascade.',
    primaryDirective: {
      action: 'Activate emergency liquidity assistance facility with full collateral flexibility for affected banks.',
      owner: 'Central Bank of the UAE',
      deadline: '6 hours',
      sector: 'Banking',
      rationale: 'Three major banks have simultaneously breached LCR minimums. The interbank market is frozen. Without central bank intervention, the liquidity shortfall cascades from the banking sector into payment systems within 36 hours. Collateral flexibility is essential because the primary assets these banks hold are real estate-linked — precisely the assets under stress.',
      consequenceOfInaction: 'Without emergency liquidity within 6 hours, the interbank freeze deepens, settlement systems begin to fail, and depositor confidence erodes. Bank equity decline accelerates to 25–35 percent versus 8–12 percent under intervention.',
    },
    supportingActions: [
      { action: 'Impose temporary short-selling restriction on listed bank equities to prevent speculative pressure.', owner: 'Securities and Commodities Authority', deadline: '12 hours', sector: 'Banking' },
      { action: 'Issue standstill directive on real estate margin calls to prevent forced liquidation cascade.', owner: 'CBUAE / RERA (joint)', deadline: '24 hours', sector: 'Real Estate' },
    ],
    expectedEffect: 'Emergency liquidity restores LCR compliance at all three affected banks within 48 hours. Short-selling restriction limits bank equity decline to 8–12 percent. The standstill directive prevents forced property liquidation that would deepen bank losses by $15B.',
    monitoringCriteria: [
      'All three affected banks report LCR above 100 percent within 48 hours',
      'Interbank overnight lending resumes at 50 percent of normal volume within 72 hours',
      'No additional bank reports LCR breach in the 7 days following facility activation',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Central Bank of the UAE', 'Securities and Commodities Authority', 'RERA'],
  },
  {
    id: 'qatar_lng_disruption',
    directiveTitle: 'Manage Qatar LNG Contractual Exposure',
    classification: 'High',
    scenarioRef: 'qatar_lng_disruption',
    summary: 'Invoke force majeure, deploy strategic LNG reserves, and accelerate North Field capacity to maintain contractual relationships and limit sovereign fiscal exposure.',
    primaryDirective: {
      action: 'Deploy strategic LNG reserves from Ras Laffan storage to honor highest-priority contracts.',
      owner: 'QatarEnergy Operations',
      deadline: '12 hours',
      sector: 'Energy',
      rationale: 'Strategic reserve deployment is the only action that maintains delivery continuity to critical buyers. Force majeure provides legal protection, but preserving the contractual relationship requires demonstrated good-faith supply effort. The 12-hour deadline ensures reserves are dispatched before the first contract delivery window is formally breached.',
      consequenceOfInaction: 'Without reserve deployment within 12 hours, major Asian buyers invoke their own contractual protections and begin sourcing alternatives. Long-term contract renegotiations become inevitable, costing Qatar $3–5B annually in contract repricing.',
    },
    supportingActions: [
      { action: 'Invoke force majeure under all affected Sale and Purchase Agreements to limit contractual liability.', owner: 'QatarEnergy Legal', deadline: '24 hours', sector: 'Energy' },
      { action: 'Accelerate North Field East expansion to bring partial additional capacity online.', owner: 'Ministry of Energy and QatarEnergy', deadline: '72 hours', sector: 'Government' },
    ],
    expectedEffect: 'Strategic reserves cover 15 percent of contracted volume for 10 days, buying time for operational restoration. Force majeure limits legal exposure on breached contracts. North Field East acceleration provides partial additional capacity within 14 days if restoration is delayed.',
    monitoringCriteria: [
      'Ras Laffan operational status — restoration timeline confirmed within 48 hours',
      'No major buyer terminates a long-term SPA within the 14-day monitoring window',
      'Qatar sovereign CDS spread remains below 80bps',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['QatarEnergy Operations', 'QatarEnergy Legal', 'Ministry of Energy'],
  },
  {
    id: 'regional_liquidity_stress_event',
    directiveTitle: 'Restore GCC Interbank Liquidity',
    classification: 'High',
    scenarioRef: 'regional_liquidity_stress_event',
    summary: 'Inject emergency overnight liquidity and activate SME credit backstop to normalize interbank rates within 12 hours and prevent a regional credit contraction.',
    primaryDirective: {
      action: 'Inject emergency overnight liquidity via expanded repo facility with broadened collateral eligibility.',
      owner: 'GCC central banks (coordinated)',
      deadline: '4 hours',
      sector: 'Banking',
      rationale: 'Interbank freezes are the fastest-propagating financial contagion vector. Three banks are already in reserve breach. Within 24 hours, the freeze cascades from overnight lending into trade finance, SME credit lines, and payment settlement. The 4-hour deadline reflects the window before the freeze becomes self-reinforcing.',
      consequenceOfInaction: 'Without repo injection within 4 hours, the interbank freeze becomes structural. Trade finance halts within 8 hours. SME credit lines freeze within 24 hours, affecting 180,000 businesses. Retail depositor confidence begins to erode by hour 48.',
    },
    supportingActions: [
      { action: 'Activate SME credit guarantee backstop through development bank facilities.', owner: 'GCC development banks', deadline: '24 hours', sector: 'Fintech' },
    ],
    expectedEffect: 'Repo injection normalizes overnight rates within 12 hours and restores interbank lending to 70 percent of normal within 24 hours. The SME credit guarantee prevents a 30–40 percent reduction in regional SME lending over the following quarter.',
    monitoringCriteria: [
      'Overnight interbank rate returns within 50bps of pre-stress level within 24 hours',
      'All three banks in reserve breach return to compliance within 36 hours',
      'No retail deposit outflow exceeding 2 percent at any single institution',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['GCC central banks (coordinated)', 'GCC development banks'],
  },
  {
    id: 'financial_infrastructure_cyber_disruption',
    directiveTitle: 'Restore Critical Payment Infrastructure',
    classification: 'High',
    scenarioRef: 'financial_infrastructure_cyber_disruption',
    summary: 'Activate backup settlement systems and deploy forensic response to restore critical payment flows within 4 hours and full RTGS capability within 24 hours.',
    primaryDirective: {
      action: 'Activate backup settlement system on isolated infrastructure to restore critical payment flows.',
      owner: 'Central banks (affected states)',
      deadline: '2 hours',
      sector: 'Banking',
      rationale: 'Every hour of RTGS downtime accumulates a transaction backlog that compounds non-linearly — $2.4B per hour. The backup system on isolated infrastructure is the only path to partial restoration while forensic investigation proceeds on the compromised primary system.',
      consequenceOfInaction: 'Without backup activation within 2 hours, the accumulated transaction backlog exceeds $18B. Cash hoarding behavior emerges within 6 hours. Public confidence in the banking system begins to erode, and GDP loss reaches $850M per 24-hour outage period.',
    },
    supportingActions: [
      { action: 'Deploy national CERT forensic response team to identify attack vector and contain lateral movement.', owner: 'National Cybersecurity Authority', deadline: '1 hour', sector: 'Government' },
      { action: 'Enable bilateral netting for critical high-value transactions while RTGS is offline.', owner: 'Central banks (affected states)', deadline: '4 hours', sector: 'Banking' },
    ],
    expectedEffect: 'Backup settlement restores critical payment flows within 4 hours. Bilateral netting processes the accumulated backlog within 12 hours. Full RTGS restoration is achieved within 18–24 hours once forensic containment is confirmed.',
    monitoringCriteria: [
      'Backup settlement system processes first transactions within 4 hours of activation',
      'CERT confirms attack vector containment within 12 hours',
      'No secondary compromise detected on backup infrastructure within 48 hours',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Central banks (affected states)', 'National Cybersecurity Authority'],
  },
  {
    id: 'red_sea_trade_corridor_instability',
    directiveTitle: 'Secure GCC Essential Supply Continuity',
    classification: 'Elevated',
    scenarioRef: 'red_sea_trade_corridor_instability',
    summary: 'Deploy strategic reserves and negotiate emergency freight corridors to buffer essential goods supply gaps and reduce freight cost premiums from 250 percent to 120 percent.',
    primaryDirective: {
      action: 'Activate strategic commodity reserves to buffer essential goods supply gaps during the rerouting period.',
      owner: 'Ministries of Commerce',
      deadline: '72 hours',
      sector: 'Government',
      rationale: 'Unlike acute disruptions, Red Sea instability is sustained — costs accumulate daily and compound through supply chain repricing. Strategic reserves provide the 30-day buffer needed to negotiate freight corridors and establish alternative supply patterns without triggering consumer price inflation.',
      consequenceOfInaction: 'Without reserve activation within 72 hours, essential goods shortages begin appearing within 10 days. Imported inflation of 1.2–1.8 percent erodes purchasing power and creates political pressure on governments across the GCC.',
    },
    supportingActions: [
      { action: 'Negotiate emergency freight corridor agreements with major shipping lines for priority GCC cargo.', owner: 'GCC port authorities (coordinated)', deadline: '96 hours', sector: 'Shipping' },
      { action: 'Issue revised marine cargo insurance guidance to enable selective direct transit for critical cargo.', owner: 'Insurance regulatory authorities', deadline: '48 hours', sector: 'Insurance' },
    ],
    expectedEffect: 'Strategic reserves cover a 30-day supply gap for essential goods. Emergency freight corridors reduce the cost premium from 250 percent to 120 percent for priority cargo. Insurance guidance enables selective direct transit for military-escorted convoys carrying critical supplies.',
    monitoringCriteria: [
      'Essential goods stockout reports — zero tolerance during the disruption window',
      'Average freight rate on GCC-bound routes declines from peak within 14 days',
      'Imported inflation reading at next monthly CPI release',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Ministries of Commerce', 'GCC port authorities', 'Insurance regulatory authorities'],
  },
  {
    id: 'gcc_cyber_attack',
    directiveTitle: 'Contain Financial Infrastructure Cyber Campaign',
    classification: 'Elevated',
    scenarioRef: 'gcc_cyber_attack',
    summary: 'Deploy cross-border incident response, activate manual settlement fallback, and issue coordinated public communications to restore payment services within 48 hours.',
    primaryDirective: {
      action: 'Activate national CERT incident response protocol with cross-border intelligence sharing.',
      owner: 'National Cybersecurity Authorities',
      deadline: '1 hour',
      sector: 'Government',
      rationale: 'The coordinated nature of the attack across three states indicates a well-resourced threat actor. Cross-border intelligence sharing is essential to identify the common attack vector, prevent lateral spread to unaffected states, and coordinate the technical response. Every hour of delay increases the probability of the attack expanding to additional financial infrastructure.',
      consequenceOfInaction: 'Without coordinated CERT activation within 1 hour, the attack may spread to additional states. 42 million customers remain without banking services. Depositor anxiety escalates sharply after 8 hours of unexplained disruption.',
    },
    supportingActions: [
      { action: 'Switch to manual settlement procedures for critical payment transactions.', owner: 'Central banks (affected states)', deadline: '4 hours', sector: 'Banking' },
      { action: 'Issue coordinated public communications confirming deposit safety and outlining restoration timeline.', owner: 'Central banks and finance ministries', deadline: '6 hours', sector: 'Government' },
    ],
    expectedEffect: 'Manual settlement restores critical payment flows within 8 hours. Full automated recovery is estimated at 36–48 hours. The public communication strategy prevents a depositor confidence crisis.',
    monitoringCriteria: [
      'Manual settlement procedures operational at all major banks within 8 hours',
      'No depositor queue or withdrawal surge reported after public communications',
      'Full automated payment processing restored within 48 hours',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['National Cybersecurity Authorities', 'Central banks (affected states)', 'Finance ministries'],
  },
  {
    id: 'energy_market_volatility_shock',
    directiveTitle: 'Stabilize GCC Fiscal Capacity',
    classification: 'Elevated',
    scenarioRef: 'energy_market_volatility_shock',
    summary: 'Activate fiscal buffers and issue SOE hedging guidance to maintain government spending continuity through a period of extreme energy market volatility.',
    primaryDirective: {
      action: 'Activate fiscal buffer drawdown protocol to maintain spending commitments during the volatility window.',
      owner: 'Finance ministries',
      deadline: '24 hours',
      sector: 'Government',
      rationale: 'When oil price volatility exceeds the fiscal planning band, budget commitments become unfunded. The fiscal buffer drawdown is the only mechanism that maintains spending continuity without requiring emergency borrowing or spending cuts. The 24-hour deadline ensures government contractors and salary obligations are not disrupted.',
      consequenceOfInaction: 'Without buffer activation within 24 hours, precautionary spending freezes cascade through government procurement and contractor payments. Banking sector liquidity contracts as government deposits become unpredictable.',
    },
    supportingActions: [
      { action: 'Issue hedging guidance for state-owned enterprises to limit further mark-to-market exposure.', owner: 'Sovereign wealth fund governance boards', deadline: '48 hours', sector: 'Government' },
    ],
    expectedEffect: 'Fiscal buffers absorb the short-term revenue deviation and maintain government spending continuity. SOE hedging guidance limits incremental mark-to-market losses. The volatility window is expected to normalize within 7–10 days.',
    monitoringCriteria: [
      'Brent crude intraday volatility returns below $5/barrel within 7 trading days',
      'No GCC government announces spending cuts or project delays within 30 days',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Finance ministries', 'Sovereign wealth fund governance boards'],
  },
  {
    id: 'oman_port_closure',
    directiveTitle: 'Redirect Omani Maritime Throughput',
    classification: 'Elevated',
    scenarioRef: 'oman_port_closure',
    summary: 'Activate regional port mutual-aid and emergency customs procedures to absorb 70 percent of diverted transshipment volume within 48 hours.',
    primaryDirective: {
      action: 'Redirect transshipment to Jebel Ali and Dammam with priority berth allocation for diverted vessels.',
      owner: 'Port authorities (UAE and KSA)',
      deadline: '12 hours',
      sector: 'Shipping',
      rationale: 'Salalah and Sohar handle 3.8M TEU annually. The GCC has limited port redundancy — only Jebel Ali and Dammam have sufficient capacity to absorb the diverted volume. Priority berth allocation is essential to prevent diverted vessels from queuing behind scheduled traffic and compounding delays.',
      consequenceOfInaction: 'Without diversion within 12 hours, delivery delays extend to 14+ days for goods transiting through Omani ports. Congestion at Jebel Ali intensifies as vessels arrive without berth allocation, creating a secondary supply chain bottleneck.',
    },
    supportingActions: [
      { action: 'Activate emergency customs clearance procedures for all diverted cargo to prevent secondary delays.', owner: 'Customs authorities (UAE and KSA)', deadline: '24 hours', sector: 'Government' },
    ],
    expectedEffect: 'Diversion absorbs approximately 70 percent of affected transshipment volume within 48 hours. Emergency customs procedures prevent secondary bottlenecks at receiving ports. Full Omani port restoration is estimated at 5–7 days.',
    monitoringCriteria: [
      'Jebel Ali and Dammam average vessel wait time remains below 48 hours during diversion',
      'Salalah and Sohar operational status updates published every 12 hours',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Port authorities (UAE and KSA)', 'Customs authorities (UAE and KSA)'],
  },
  {
    id: 'bahrain_sovereign_stress',
    directiveTitle: 'Secure Bahrain Sovereign Rating',
    classification: 'Guarded',
    scenarioRef: 'bahrain_sovereign_stress',
    summary: 'Present a credible fiscal consolidation program and negotiate a GCC support package to maintain investment-grade rating before the agency review concludes.',
    primaryDirective: {
      action: 'Accelerate fiscal consolidation program with specific expenditure reduction targets to present to rating agencies.',
      owner: 'Ministry of Finance',
      deadline: '30 days',
      sector: 'Government',
      rationale: 'Bahrain\'s sovereign-bank nexus means a rating downgrade reprices the entire banking sector — an estimated $2–3B mark-to-market loss. The consolidation program must be credible and specific, not aspirational. Rating agencies require quantified targets before they will revise the negative outlook.',
      consequenceOfInaction: 'Without a credible consolidation program before the review concludes, the downgrade becomes probable. Bank funding costs increase, corporate borrowing costs rise, and Bahrain\'s ability to refinance maturing sovereign debt deteriorates significantly.',
    },
    supportingActions: [
      { action: 'Negotiate GCC fiscal support package to demonstrate sovereign backstop to international creditors.', owner: 'GCC Finance Ministers Council', deadline: '60 days', sector: 'Government' },
    ],
    expectedEffect: 'A credible fiscal consolidation program combined with a GCC support package has historically been sufficient to maintain Bahrain\'s investment-grade rating. The 2018 precedent — a $10B GCC support package — stabilized markets and prevented a downgrade cycle.',
    monitoringCriteria: [
      'Rating agency confirms review timeline within 14 days',
      'GCC Finance Ministers Council issues support commitment within 45 days',
      'Bahrain sovereign CDS spread remains below 350bps',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Ministry of Finance', 'GCC Finance Ministers Council'],
  },
  {
    id: 'kuwait_fiscal_shock',
    directiveTitle: 'Unlock Kuwait Sovereign Debt Authority',
    classification: 'Guarded',
    scenarioRef: 'kuwait_fiscal_shock',
    summary: 'Secure parliamentary approval for sovereign debt issuance and advance VAT legislation to extend fiscal runway from 24 months to 5+ years.',
    primaryDirective: {
      action: 'Implement sovereign debt issuance program — requires parliamentary approval of new debt law.',
      owner: 'Ministry of Finance / National Assembly',
      deadline: '30 days',
      sector: 'Government',
      rationale: 'Kuwait\'s fiscal structure is uniquely constrained — without debt market access, the government depends entirely on reserve fund drawdowns with a 24–30 month runway. Debt issuance is the only near-term mechanism that extends fiscal capacity without depleting sovereign wealth. The political dimension is the binding constraint.',
      consequenceOfInaction: 'Without debt authority, the General Reserve Fund continues to deplete at an accelerating rate. Expenditure caps become mandatory within 18 months, forcing spending cuts that affect government services, employment, and economic growth.',
    },
    supportingActions: [
      { action: 'Advance VAT framework legislation to establish non-oil revenue source.', owner: 'National Assembly / Ministry of Finance', deadline: '90 days', sector: 'Government' },
    ],
    expectedEffect: 'Debt issuance bridges the fiscal gap, extending the runway from 24 months to 5+ years. VAT implementation provides a structural non-oil revenue source estimated at 1.5–2 percent of GDP annually. The political risk is the binding constraint — parliamentary approval timelines are uncertain.',
    monitoringCriteria: [
      'Parliamentary committee advances debt law to floor vote within 30 days',
      'General Reserve Fund drawdown rate — monthly reporting confirms trend',
      'Kuwait sovereign rating remains stable through the monitoring period',
    ],
    issued: '2026-04-13T06:00:00Z',
    distribution: ['Ministry of Finance', 'National Assembly'],
  },
];

/* ── Lookup helpers ── */

const byId = new Map(manifest.map((d) => [d.id, d]));

export function getDecision(id: string): DecisionBriefing | undefined {
  return byId.get(id);
}

export function getAllDecisions(): DecisionBriefing[] {
  return manifest;
}

const tierOrder: Record<string, number> = { Severe: 0, High: 1, Elevated: 2, Guarded: 3 };

export function getDecisionsByClassification(): DecisionBriefing[] {
  return [...manifest].sort(
    (a, b) => (tierOrder[a.classification] ?? 9) - (tierOrder[b.classification] ?? 9),
  );
}
