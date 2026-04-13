/**
 * Impact Observatory | مرصد الأثر — Evaluation Manifest
 *
 * Post-decision accountability data for 15 GCC macro scenarios.
 * Each evaluation answers: Did the decisions work? What did we learn?
 *
 * Structure:
 *   Outcome Assessment → Correctness → Analyst Commentary →
 *   Institutional Learning → Rule Performance
 *
 * Static for SSG. In production, hydrated from evaluation pipeline.
 */

/* ── Types ── */

export type Verdict = 'Confirmed' | 'Partially Confirmed' | 'Revised' | 'Inconclusive';

export interface EvaluationBriefing {
  id: string;
  scenarioRef: string;
  scenarioTitle: string;
  verdict: Verdict;
  correctness: number;
  summary: string;
  expectedOutcome: string;
  actualOutcome: string;
  correctnessRationale: string;
  analystCommentary: string;
  replaySummary: string;
  rulePerformance: string[];
  evaluatedDate: string;
}

/* ── Manifest ── */

const manifest: EvaluationBriefing[] = [
  {
    id: 'hormuz_chokepoint_disruption',
    scenarioRef: 'hormuz_chokepoint_disruption',
    scenarioTitle: 'Strait of Hormuz Disruption',
    verdict: 'Confirmed',
    correctness: 0.87,
    summary: 'Strategic reserve release and pipeline rerouting executed within target windows. Economic loss contained to $6.1B against a $5.8B projection.',
    expectedOutcome:
      'Projected economic loss reduced from $14.2B to $5.8B over 72 hours. Liquidity backstop prevents trade finance contagion. Insurance market function restored within 5 days.',
    actualOutcome:
      'Actual economic loss was $6.1B over the 72-hour window — 5 percent above projection due to a 2-hour delay in Fujairah pipeline activation. Liquidity backstop prevented interbank contagion as projected. Marine cargo insurance resumed on day 4, one day ahead of estimate.',
    correctnessRationale:
      'The decision framework performed within acceptable tolerance. The pipeline activation delay was an operational constraint, not a decision failure — the directive was issued on time but physical ramp-up exceeded engineering estimates. All other directives executed within window.',
    analystCommentary:
      'The reserve release was the correct primary directive. Market response confirmed that the signal effect mattered more than the actual volume released. The 2-hour pipeline delay should inform future operational estimates — Fujairah ramp-up time should be modeled at 8 hours, not 6. The insurance market recovered faster than projected, suggesting that the war-risk guidance had a stronger confidence effect than anticipated.',
    replaySummary:
      'This scenario establishes the baseline playbook for Hormuz disruptions. Three lessons for institutional memory: first, reserve release signal effect outweighs volume — prioritize announcement speed over reserve quantity. Second, pipeline ramp-up estimates should carry a 30 percent time buffer for engineering constraints. Third, insurance market guidance has outsized confidence effects and should be issued earlier in the sequence.',
    rulePerformance: [
      'Reserve release trigger rule activated correctly — price threshold breach detected at +$28/barrel, directive issued within 15 minutes',
      'Liquidity backstop trigger rule activated correctly — trade finance exposure threshold exceeded at $10.8B',
      'Pipeline routing rule underestimated ramp-up time by 2 hours — parameter adjustment required from 6h to 8h baseline',
      'Insurance guidance trigger rule activated on schedule — war-risk premium threshold of 400 percent confirmed',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'hormuz_full_closure',
    scenarioRef: 'hormuz_full_closure',
    scenarioTitle: 'Hormuz Full Closure',
    verdict: 'Partially Confirmed',
    correctness: 0.72,
    summary: 'GCC coordination executed within 3 hours versus 2-hour target. Economic damage contained to $26B against $22B projection due to IEA response delay.',
    expectedOutcome:
      'Economic damage limited to $22B over 72 hours. Alternative pipeline routes restore 30 percent of export capacity within 6 hours. Interbank facility prevents banking crisis.',
    actualOutcome:
      'Actual economic damage was $26B over 72 hours — 18 percent above projection. GCC Supreme Council coordination took 3 hours instead of 2. IEA reserve release confirmation was delayed by 4 hours beyond the requested timeline, contributing to a prolonged price spike. Pipeline capacity restored 28 percent within 7 hours. Interbank facility activated successfully and prevented systemic banking stress.',
    correctnessRationale:
      'The decision framework was directionally correct but the coordination timeline was optimistic. The 1-hour GCC coordination delay and the 4-hour IEA delay compounded to produce a price spike window that added approximately $4B to the damage estimate. The interbank facility performed as projected.',
    analystCommentary:
      'Full closure scenarios require a faster coordination pre-commitment mechanism. Relying on real-time Supreme Council assembly introduces irreducible delay. Recommendation: establish a pre-authorized coordination protocol that activates automatically when specific conditions are met, reducing the coordination decision from a convening exercise to a confirmation signal.',
    replaySummary:
      'This scenario demonstrates the limits of real-time multilateral coordination under extreme time pressure. Institutional learning: pre-authorized response protocols are essential for full-closure scenarios. The IEA dependency is a structural bottleneck that cannot be eliminated but can be mitigated through pre-positioned bilateral agreements with major consuming nations.',
    rulePerformance: [
      'GCC coordination trigger rule activated correctly but execution exceeded the 2-hour target by 60 minutes',
      'Pipeline routing rule performed within tolerance — 28 percent versus 30 percent target at 7 hours versus 6 hours',
      'Interbank facility trigger rule activated correctly — no systemic breach occurred',
      'IEA coordination rule assumes response within 6 hours — actual was 10 hours — external dependency parameter needs recalibration',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'iran_regional_escalation',
    scenarioRef: 'iran_regional_escalation',
    scenarioTitle: 'Iran Regional Escalation',
    verdict: 'Confirmed',
    correctness: 0.81,
    summary: 'Defense coordination and capital controls executed within targets. Capital outflow limited to $9.2B against $8B projection. No infrastructure damage.',
    expectedOutcome:
      'Capital outflow limited to $8B. Energy price overshoot capped below $145/barrel. Market confidence stabilizes within 14 days if no infrastructure damage.',
    actualOutcome:
      'Capital outflow totaled $9.2B over 7 days — 15 percent above projection, driven by faster-than-expected institutional investor withdrawal in the first 48 hours. Brent peaked at $142/barrel on day 3 before stabilizing. No physical infrastructure damage occurred. Diplomatic channel produced a de-escalation statement on day 6. Market confidence indicators returned to pre-escalation levels by day 12.',
    correctnessRationale:
      'The decision framework performed well. The capital outflow overshoot reflects institutional investor speed, which exceeded the model assumption. The defense coordination was the correct primary directive — no infrastructure damage validated the deterrent posture. Diplomatic de-escalation arrived within window.',
    analystCommentary:
      'The capital flow model underestimates institutional investor withdrawal speed in the first 48 hours of a geopolitical escalation. Recommend adjusting the flow velocity parameter to reflect the observed pattern: 65 percent of total outflow occurs in the first 2 days. The diplomatic channel timeline was accurate, reinforcing the value of pre-established intermediary relationships.',
    replaySummary:
      'Geopolitical scenarios confirm that deterrent posture and capital controls must be simultaneous, not sequential. The 12-day confidence restoration timeline provides a useful benchmark for future escalation scenarios. Key precedent: diplomatic de-escalation within 7 days is achievable when intermediary channels are pre-established.',
    rulePerformance: [
      'Defense coordination trigger activated correctly — unified command established within 2 hours of escalation signal',
      'Capital control rule activated correctly but outflow model underestimated first-48h velocity by 15 percent',
      'Energy price cap rule performed within tolerance — $142 peak versus $145 threshold',
      'Diplomatic engagement rule triggered on schedule — de-escalation statement confirmed on day 6',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'critical_port_throughput_disruption',
    scenarioRef: 'critical_port_throughput_disruption',
    scenarioTitle: 'Multi-Port Throughput Failure',
    verdict: 'Confirmed',
    correctness: 0.89,
    summary: 'Force majeure declared within 5 hours. Emergency supply corridors operational within 16 hours. No essential goods stockouts reported.',
    expectedOutcome:
      'Emergency supply corridors maintain essential goods availability. Tanker queue management prevents secondary energy price spike. Full port restoration within 7 days.',
    actualOutcome:
      'Force majeure declared in 5 hours versus 6-hour target. Emergency supply corridors operational in 16 hours versus 18-hour projection. Zero essential goods stockouts across all GCC states. Tanker queue management kept energy price impact to +$3/barrel, well within acceptable range. Port throughput restored to 55 percent by day 4 and full capacity by day 6.',
    correctnessRationale:
      'The decision framework outperformed projections on every metric. The force majeure declaration was faster than estimated. Supply corridor activation was 2 hours ahead of schedule. Port restoration was one day ahead of the 7-day target.',
    analystCommentary:
      'This scenario benefited from the mutual-aid agreements negotiated after the 2024 Jebel Ali congestion episode. Pre-existing agreements reduced coordination friction. The emergency customs procedures were the critical enabler — without them, the diversion would have created a secondary bottleneck as originally modeled. Recommendation: maintain and expand the mutual-aid framework to include Salalah, Sohar, and Dammam in the primary agreement.',
    replaySummary:
      'Multi-port disruption response demonstrates the value of pre-negotiated mutual-aid frameworks. Institutional learning: the customs clearance fast-track was the decisive intervention. Future port disruption playbooks should elevate customs coordination to the same priority as physical diversion.',
    rulePerformance: [
      'Force majeure trigger rule activated correctly and ahead of schedule',
      'Supply corridor activation rule performed within tolerance — 16 hours versus 18-hour estimate',
      'Tanker queue management rule successfully contained energy price secondary effects',
      'Port restoration monitoring rule tracked accurately — 55 percent at day 4 exceeded the 50 percent target',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'saudi_oil_shock',
    scenarioRef: 'saudi_oil_shock',
    scenarioTitle: 'Saudi Oil Production Shock',
    verdict: 'Partially Confirmed',
    correctness: 0.74,
    summary: 'Surge capacity restored 52 percent of lost production in 48 hours against 60 percent target. Global price impact was +$22/barrel versus +$18 projection.',
    expectedOutcome:
      'Surge capacity restores 60 percent of lost production within 48 hours. IEA coordination limits price impact to +$18/barrel. Fiscal stabilization fund provides 90-day bridge.',
    actualOutcome:
      'Shaybah and Khurais surge capacity restored 52 percent of lost production within 48 hours — below the 60 percent target due to shared processing infrastructure constraints. Brent crude settled at +$22/barrel above pre-shock levels. IEA confirmed reserve release commitments within 32 hours. Fiscal stabilization fund activated on schedule and government spending continuity was maintained.',
    correctnessRationale:
      'The decision framework was correct in priority ordering but the surge capacity model overestimated available independent processing capacity. The 8 percentage point shortfall in production restoration drove the $4/barrel price deviation. IEA coordination and fiscal stabilization performed well.',
    analystCommentary:
      'The surge capacity model assumes independent processing at Shaybah and Khurais, but approximately 15 percent of processing capacity shares infrastructure with the affected primary facilities. This coupling was not reflected in the model. Recommendation: re-survey shared infrastructure dependencies and adjust surge capacity estimates to reflect realistic independent processing capability.',
    replaySummary:
      'Production shock response confirms the correct priority hierarchy: physical restoration first, international coordination second, fiscal bridge third. The infrastructure coupling discovery is the critical institutional learning — surge capacity models must account for shared processing dependencies. Revise the Shaybah-Khurais independence assumption from 100 percent to 85 percent.',
    rulePerformance: [
      'Surge capacity activation rule triggered correctly at the 12-hour mark',
      'Production restoration model overestimated by 8 percentage points — infrastructure coupling not reflected',
      'IEA coordination rule performed within tolerance — 32 hours versus 36-hour outer limit',
      'Fiscal stabilization rule activated on schedule — no government spending disruption',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'uae_banking_crisis',
    scenarioRef: 'uae_banking_crisis',
    scenarioTitle: 'UAE Banking Sector Stress',
    verdict: 'Confirmed',
    correctness: 0.91,
    summary: 'All three banks restored LCR compliance within 36 hours. Bank equity decline contained to 9 percent. No forced property liquidation cascade.',
    expectedOutcome:
      'Emergency liquidity restores LCR compliance within 48 hours. Bank equity decline limited to 8–12 percent. Standstill directive prevents forced property liquidation.',
    actualOutcome:
      'LCR compliance restored at all three banks within 36 hours — 12 hours ahead of the 48-hour target. Bank equity declined 9 percent, within the projected 8–12 percent band. Interbank overnight lending resumed at 58 percent of normal volume within 60 hours. No additional banks reported LCR breach. The standstill directive successfully prevented any forced property liquidation.',
    correctnessRationale:
      'The decision framework performed at the upper end of expectations. The emergency liquidity facility restored compliance faster than projected, suggesting the collateral flexibility provision was well-calibrated. The equity impact fell in the center of the projected range.',
    analystCommentary:
      'The 6-hour liquidity activation deadline was correctly set. The collateral flexibility clause was the critical enabler — without it, the banks would have needed to post real estate assets at distressed valuations, defeating the purpose of the facility. The standstill directive prevented what would have been an estimated $15B in forced liquidation losses. Recommendation: make the standstill directive automatic when emergency liquidity is activated.',
    replaySummary:
      'Banking crisis response demonstrates the importance of simultaneous intervention across liquidity, equity markets, and property markets. The standstill directive was the unsung decisive intervention — it broke the feedback loop between bank losses and property liquidation. Future banking stress playbooks should pair liquidity assistance with automatic standstill provisions.',
    rulePerformance: [
      'LCR breach detection rule activated correctly — all three breaches identified within 90 minutes of occurrence',
      'Emergency liquidity trigger rule activated within the 6-hour window',
      'Short-selling restriction rule activated on schedule — equity decline contained within projected band',
      'Standstill directive rule activated within 24 hours — zero forced liquidation events recorded',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'qatar_lng_disruption',
    scenarioRef: 'qatar_lng_disruption',
    scenarioTitle: 'Qatar LNG Export Disruption',
    verdict: 'Partially Confirmed',
    correctness: 0.68,
    summary: 'Strategic reserves deployed within 10 hours. Two major Asian buyers initiated contract renegotiation despite force majeure, contrary to projection.',
    expectedOutcome:
      'Strategic reserves cover 15 percent of contracted volume for 10 days. Force majeure limits legal exposure. North Field East provides partial capacity within 14 days.',
    actualOutcome:
      'Strategic reserves deployed within 10 hours and covered 14 percent of contracted volume for 9 days. Force majeure was accepted by 12 of 14 major buyers. However, two major Asian buyers — representing 18 percent of contracted volume — initiated SPA renegotiation proceedings despite force majeure, arguing the disruption reflected structural operational risk. North Field East acceleration brought partial capacity online on day 16, two days behind schedule.',
    correctnessRationale:
      'The physical response performed close to projection, but the contractual dimension was more adversarial than modeled. The force majeure framework assumed universal acceptance; in practice, buyers with alternative supply options used the disruption as leverage for renegotiation. This is a model gap, not a decision error.',
    analystCommentary:
      'The decision to prioritize reserve deployment was correct — it preserved the relationship with 12 of 14 buyers. The two defections were from buyers with recently signed alternative supply agreements, making them structurally less dependent on Qatar. The model should incorporate buyer supply diversification as a variable affecting force majeure acceptance probability. North Field East acceleration was slower than projected due to workforce mobilization constraints.',
    replaySummary:
      'LNG disruption response reveals a critical model gap: force majeure acceptance is not universal and depends on buyer supply diversification. Institutional learning: maintain a buyer dependency matrix that scores each major customer on alternative supply availability. Buyers with low dependency scores require proactive commercial engagement, not just legal protection, during disruptions.',
    rulePerformance: [
      'Reserve deployment rule activated correctly — 10 hours versus 12-hour deadline',
      'Force majeure trigger rule activated on schedule but acceptance model overestimated compliance by 14 percent',
      'North Field East acceleration rule triggered correctly but completion exceeded estimate by 2 days',
      'Buyer retention model needs recalibration — did not account for supply diversification as an acceptance variable',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'regional_liquidity_stress_event',
    scenarioRef: 'regional_liquidity_stress_event',
    scenarioTitle: 'Regional Liquidity Stress',
    verdict: 'Confirmed',
    correctness: 0.93,
    summary: 'Overnight rates normalized within 10 hours. All three banks returned to reserve compliance within 28 hours. No retail deposit outflows detected.',
    expectedOutcome:
      'Repo injection normalizes overnight rates within 12 hours. All banks in breach return to compliance within 36 hours. No retail deposit outflow exceeding 2 percent.',
    actualOutcome:
      'Overnight interbank rate returned to within 35bps of pre-stress level within 10 hours — ahead of the 12-hour projection. All three banks in reserve breach returned to compliance within 28 hours. Retail deposit monitoring showed zero net outflow at any institution. SME credit guarantee backstop activated within 20 hours and prevented credit line freezes at an estimated 145,000 businesses.',
    correctnessRationale:
      'The decision framework performed above expectations on every metric. The repo injection was faster-acting than modeled, likely because collateral broadening gave banks access to a wider pool of eligible assets. The SME backstop activation was 4 hours ahead of the 24-hour deadline.',
    analystCommentary:
      'The 4-hour liquidity injection deadline was the critical design parameter. Post-event analysis confirms that the interbank freeze would have become self-reinforcing by hour 6 — the 4-hour window was correctly calibrated. The collateral broadening provision was the decisive technical element. Recommendation: make broadened collateral eligibility the default for emergency facilities rather than a special provision.',
    replaySummary:
      'Liquidity stress response establishes the gold-standard playbook for interbank freezes. Three confirmations for institutional doctrine: first, the 4-hour injection window is correctly calibrated — 6 hours is too late. Second, broadened collateral eligibility should be default, not exceptional. Third, SME credit backstops are essential parallel interventions, not optional follow-ups.',
    rulePerformance: [
      'Interbank rate spike detection rule activated correctly — 300bps threshold triggered immediate alert',
      'Repo injection trigger rule executed within the 4-hour window — system response ahead of schedule',
      'Reserve compliance monitoring rule tracked accurately — all three banks confirmed compliant at hour 28',
      'SME credit guarantee activation rule triggered 4 hours ahead of the 24-hour outer limit',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'financial_infrastructure_cyber_disruption',
    scenarioRef: 'financial_infrastructure_cyber_disruption',
    scenarioTitle: 'Financial System Cyber Attack',
    verdict: 'Confirmed',
    correctness: 0.84,
    summary: 'Backup settlement operational within 3.5 hours. CERT confirmed containment within 14 hours. Full RTGS restoration achieved in 21 hours.',
    expectedOutcome:
      'Backup settlement restores critical payments within 4 hours. Bilateral netting processes backlog within 12 hours. Full RTGS restoration within 18–24 hours.',
    actualOutcome:
      'Backup settlement system processed first transactions within 3.5 hours. CERT confirmed attack vector containment within 14 hours — 2 hours beyond the 12-hour target, due to a secondary lateral movement vector that required additional isolation. Bilateral netting cleared the $16B accumulated backlog within 11 hours. Full RTGS restoration achieved at hour 21. No secondary compromise detected on backup infrastructure.',
    correctnessRationale:
      'The decision framework performed well. The backup settlement activation was ahead of schedule. The CERT containment delay was caused by a secondary attack vector not present in the original threat model — this is a forensic intelligence gap, not a decision timing error. RTGS restoration fell within the projected 18–24 hour window.',
    analystCommentary:
      'The decision to activate backup settlement on isolated infrastructure was validated — it provided payment continuity while forensic work proceeded on the compromised primary system. The secondary lateral movement vector is a significant finding — the threat model assumed a single-vector attack, but the actual campaign used a second dormant payload that activated when the primary vector was contained. Threat model should be updated to include multi-vector attack scenarios.',
    replaySummary:
      'Cyber disruption response confirms the value of isolated backup infrastructure. Critical institutional learning: the threat model must assume multi-vector attacks as the baseline, not single-vector. The secondary payload discovery changes the containment timeline assumption from 12 hours to 16 hours for future planning. The bilateral netting fallback was the critical business continuity enabler.',
    rulePerformance: [
      'Backup settlement activation rule triggered correctly — 3.5 hours versus 4-hour target',
      'CERT deployment rule activated within 1 hour as specified',
      'Containment confirmation rule exceeded timeline — 14 hours versus 12-hour target due to secondary vector',
      'Bilateral netting activation rule performed within tolerance — backlog cleared in 11 hours versus 12-hour estimate',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'red_sea_trade_corridor_instability',
    scenarioRef: 'red_sea_trade_corridor_instability',
    scenarioTitle: 'Red Sea Corridor Instability',
    verdict: 'Partially Confirmed',
    correctness: 0.71,
    summary: 'Strategic reserves deployed successfully. Freight corridor negotiations achieved 140 percent premium versus 120 percent target. No essential goods stockouts.',
    expectedOutcome:
      'Strategic reserves cover 30-day supply gap. Freight corridors reduce cost premium from 250 percent to 120 percent. Insurance guidance enables selective direct transit.',
    actualOutcome:
      'Strategic reserves covered essential goods for 28 days before requiring replenishment. Emergency freight corridors negotiated a premium reduction to 140 percent — above the 120 percent target — as shipping lines demanded higher rates for guaranteed priority scheduling. Insurance guidance enabled selective direct transit for military-escorted convoys as projected. Zero essential goods stockouts across all GCC states. Imported inflation registered at 1.4 percent at the next CPI reading.',
    correctnessRationale:
      'The decision framework was correct in structure but the freight negotiation outcome was weaker than projected. Shipping lines had more bargaining power than modeled because the sustained nature of the disruption reduced competitive pressure — carriers had full order books regardless of the GCC priority corridor.',
    analystCommentary:
      'The freight negotiation model assumed that guaranteed volume commitments would give GCC ports sufficient leverage to achieve the 120 percent target. In practice, shipping lines were capacity-constrained across all routes, reducing the value of volume guarantees. The negotiation model should incorporate global capacity utilization as a variable. The reserve deployment and insurance guidance performed well.',
    replaySummary:
      'Sustained disruption scenarios require different negotiation assumptions than acute disruptions. Institutional learning: when global shipping capacity utilization exceeds 85 percent, volume-based freight negotiations lose leverage. Future Red Sea disruption playbooks should include pre-negotiated freight agreements activated by trigger conditions, rather than relying on real-time negotiation during the disruption.',
    rulePerformance: [
      'Strategic reserve activation rule triggered correctly within the 72-hour window',
      'Freight corridor negotiation rule achieved a weaker outcome than projected — 140 percent versus 120 percent target',
      'Insurance guidance rule performed as specified — selective transit enabled on schedule',
      'Essential goods monitoring rule confirmed zero stockouts throughout the disruption window',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'gcc_cyber_attack',
    scenarioRef: 'gcc_cyber_attack',
    scenarioTitle: 'GCC Cyber Infrastructure Attack',
    verdict: 'Confirmed',
    correctness: 0.86,
    summary: 'Cross-border CERT coordination achieved within 45 minutes. Manual settlement operational within 7 hours. No depositor confidence disruption.',
    expectedOutcome:
      'Manual settlement restores critical payments within 8 hours. Full automated recovery within 36–48 hours. Public communications prevent depositor crisis.',
    actualOutcome:
      'CERT incident response activated across all three affected states within 45 minutes. Manual settlement procedures operational within 7 hours. Coordinated public communications issued within 5 hours — 1 hour ahead of the 6-hour deadline. No depositor queue or withdrawal surge at any branch. Full automated payment processing restored within 42 hours.',
    correctnessRationale:
      'The decision framework performed above the baseline projection. The CERT activation was faster than expected due to the pre-existing cross-border intelligence sharing agreement activated in 2025. The public communications strategy was the critical confidence intervention.',
    analystCommentary:
      'The 6-hour public communication deadline was well-calibrated — market monitoring confirmed that social media speculation began escalating at hour 4. The 5-hour actual issuance caught the anxiety curve before it reached critical mass. The pre-existing CERT agreement was the decisive enabler for the faster-than-projected technical response. Recommendation: extend the cross-border CERT agreement to include the remaining three GCC states.',
    replaySummary:
      'Cyber campaign response validates the three-pillar approach: technical containment, operational continuity, and public confidence management. The public communications timeline is the most time-sensitive element — social media amplification means the confidence window is shrinking. Future playbooks should target 4-hour communications, not 6.',
    rulePerformance: [
      'CERT activation rule triggered within 45 minutes — well ahead of the 1-hour deadline',
      'Manual settlement activation rule performed ahead of schedule — 7 hours versus 8-hour target',
      'Public communications rule issued 1 hour ahead of deadline — no confidence disruption detected',
      'Automated restoration monitoring rule tracked accurately — full recovery at hour 42',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'energy_market_volatility_shock',
    scenarioRef: 'energy_market_volatility_shock',
    scenarioTitle: 'Energy Market Volatility',
    verdict: 'Confirmed',
    correctness: 0.82,
    summary: 'Fiscal buffers activated within 18 hours. No government spending disruptions. Volatility normalized within 9 trading days.',
    expectedOutcome:
      'Fiscal buffers maintain spending continuity. SOE hedging limits mark-to-market losses. Volatility normalizes within 7–10 days.',
    actualOutcome:
      'Fiscal buffer drawdown activated within 18 hours across four GCC states. No government spending cuts or project delays announced. SOE hedging guidance issued within 44 hours. Brent crude intraday volatility returned below $5/barrel within 9 trading days. No GCC government reported contractor payment delays.',
    correctnessRationale:
      'The decision framework performed within the projected band. Fiscal buffer activation was 6 hours ahead of the 24-hour deadline. Volatility normalization at day 9 was within the 7–10 day estimate.',
    analystCommentary:
      'The fiscal buffer mechanism worked as designed. The critical observation is that two smaller GCC states — Bahrain and Oman — required coordinated drawdown support from larger sovereign wealth funds, suggesting that the buffer framework should include a mutual-support provision for states with thinner fiscal reserves.',
    replaySummary:
      'Volatility scenarios confirm that fiscal buffers are the correct primary intervention. Institutional learning: the buffer framework should be formalized as a GCC-wide mutual-support mechanism, not a collection of independent state buffers. States with thinner reserves need access to pooled capacity during extreme volatility windows.',
    rulePerformance: [
      'Fiscal buffer activation rule triggered correctly — 18 hours versus 24-hour deadline',
      'SOE hedging guidance rule issued within the 48-hour window',
      'Volatility monitoring rule tracked accurately — normalization confirmed at day 9',
      'Government spending continuity rule confirmed — zero disruptions across all states',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'oman_port_closure',
    scenarioRef: 'oman_port_closure',
    scenarioTitle: 'Oman Port Closure',
    verdict: 'Confirmed',
    correctness: 0.88,
    summary: 'Transshipment redirected within 10 hours. Emergency customs operational within 20 hours. Full port restoration achieved in 5 days.',
    expectedOutcome:
      'Diversion absorbs 70 percent of volume within 48 hours. Emergency customs prevents secondary bottleneck. Full restoration within 5–7 days.',
    actualOutcome:
      'Priority berth allocation at Jebel Ali and Dammam established within 10 hours. Diversion absorbed 73 percent of affected transshipment volume within 44 hours. Emergency customs clearance procedures operational within 20 hours — 4 hours ahead of the 24-hour deadline. Average vessel wait time at Jebel Ali peaked at 38 hours during the diversion period. Salalah restored to full operations on day 5; Sohar on day 6.',
    correctnessRationale:
      'The decision framework outperformed on diversion volume (73 percent versus 70 percent) and customs activation (20 hours versus 24 hours). Port restoration was within the 5–7 day range. Vessel wait times remained below the 48-hour threshold.',
    analystCommentary:
      'The mutual-aid agreement between Jebel Ali and Salalah, established after the 2024 review, was the enabler for the 10-hour diversion timeline. Without the pre-existing agreement, coordination would have taken 18–24 hours. The emergency customs procedure was well-designed — it processed diverted cargo at 92 percent of normal clearance speed.',
    replaySummary:
      'Omani port disruption response validates the mutual-aid framework investment. Institutional learning: the customs fast-track procedure should become permanent infrastructure, not an emergency activation. Permanent fast-track for transshipment cargo would reduce baseline port processing time and provide immediate surge capability during disruptions.',
    rulePerformance: [
      'Diversion trigger rule activated correctly — priority berth allocation established within 10 hours',
      'Emergency customs rule activated 4 hours ahead of schedule',
      'Vessel wait time monitoring rule tracked accurately — peak of 38 hours within the 48-hour threshold',
      'Port restoration monitoring rule confirmed Salalah at day 5, Sohar at day 6',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'bahrain_sovereign_stress',
    scenarioRef: 'bahrain_sovereign_stress',
    scenarioTitle: 'Bahrain Fiscal Stress',
    verdict: 'Inconclusive',
    correctness: 0.55,
    summary: 'Fiscal consolidation program presented on day 28. GCC support discussions ongoing. Rating agency review extended by 30 days — verdict pending.',
    expectedOutcome:
      'Credible consolidation program plus GCC support package maintains investment-grade rating. Rating review concludes favorably.',
    actualOutcome:
      'Ministry of Finance presented a fiscal consolidation program on day 28, two days ahead of the 30-day deadline. The program included specific expenditure reduction targets totaling 2.4 percent of GDP over 3 years. GCC Finance Ministers Council discussions are ongoing but no formal support commitment has been issued within the 45-day target. The rating agency extended its review period by 30 days, citing the need to assess the credibility of the consolidation program and the status of GCC support. Bahrain sovereign CDS spread is at 310bps — below the 350bps threshold but elevated.',
    correctnessRationale:
      'The evaluation is inconclusive because the primary outcome — the rating decision — has not yet occurred. The consolidation program was delivered on schedule, but the GCC support package is behind timeline. The rating agency extension creates a new observation window.',
    analystCommentary:
      'The consolidation program was well-structured and the 2.4 percent GDP target is within the range that has historically satisfied rating agencies. However, the GCC support package delay introduces uncertainty. The 2018 precedent included a $10B package committed within 40 days. The current timeline suggests political dynamics among GCC states have shifted. Recommendation: escalate the support package negotiation to head-of-state level.',
    replaySummary:
      'Sovereign stress scenarios with extended timelines require a checkpoint evaluation framework. This scenario will be re-evaluated at the 90-day mark when the rating agency concludes its extended review. Preliminary institutional learning: GCC multilateral fiscal support is slower to mobilize than the 2018 precedent suggests — the political pre-conditions have evolved.',
    rulePerformance: [
      'Fiscal consolidation delivery rule met — program presented on day 28 versus 30-day deadline',
      'GCC support package rule has not been satisfied — no formal commitment within the 45-day outer limit',
      'CDS spread monitoring rule confirms 310bps — below 350bps threshold but trending upward',
      'Rating agency timeline rule requires recalibration — agency extended review beyond the modeled 60-day window',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
  {
    id: 'kuwait_fiscal_shock',
    scenarioRef: 'kuwait_fiscal_shock',
    scenarioTitle: 'Kuwait Oil Revenue Shock',
    verdict: 'Inconclusive',
    correctness: 0.48,
    summary: 'Debt law advanced to parliamentary committee but floor vote has not occurred within 30-day target. VAT legislation remains in preliminary discussion.',
    expectedOutcome:
      'Debt issuance extends fiscal runway from 24 months to 5+ years. VAT provides structural non-oil revenue. Parliamentary approval is the binding constraint.',
    actualOutcome:
      'The Ministry of Finance submitted the debt law to the parliamentary finance committee on day 12. The committee held two hearings but has not advanced the bill to a floor vote within the 30-day target. Political opposition has intensified, with three parliamentary blocs publicly opposing the bill. VAT framework legislation remains at the preliminary discussion stage with no committee referral. General Reserve Fund drawdown continues at the projected rate. Kuwait sovereign rating remains stable.',
    correctnessRationale:
      'The evaluation is inconclusive because neither primary decision has been fully executed. The political risk identified in the decision framework has materialized as the binding constraint. The fiscal and technical elements of the decision were sound, but the political pathway is blocked.',
    analystCommentary:
      'The decision framework correctly identified parliamentary approval as the binding constraint. The three-bloc opposition was not predicted at this intensity. The debt law may require a revised political strategy — either concessions to opposition blocs or executive action under emergency fiscal provisions. The VAT timeline was always aspirational; the 90-day target assumed political goodwill that does not exist in the current parliament.',
    replaySummary:
      'Kuwait fiscal scenarios confirm that political risk modeling must be more granular. Institutional learning: parliamentary bloc analysis should be incorporated into the decision framework as a pre-condition assessment, not an assumption. Future Kuwait fiscal playbooks should include a political pathway analysis with bloc-by-bloc vote counting before setting legislative timelines.',
    rulePerformance: [
      'Debt law submission rule met — bill submitted on day 12',
      'Parliamentary floor vote rule not met — bill remains in committee beyond 30-day target',
      'VAT legislation rule not met — no committee referral within the monitoring period',
      'Reserve fund drawdown monitoring rule tracking accurately — trajectory unchanged',
    ],
    evaluatedDate: '2026-04-13T18:00:00Z',
  },
];

/* ── Lookup helpers ── */

const byId = new Map(manifest.map((e) => [e.id, e]));

export function getEvaluation(id: string): EvaluationBriefing | undefined {
  return byId.get(id);
}

export function getAllEvaluations(): EvaluationBriefing[] {
  return manifest;
}

const verdictOrder: Record<string, number> = {
  Confirmed: 0,
  'Partially Confirmed': 1,
  Inconclusive: 2,
  Revised: 3,
};

export function getEvaluationsByVerdict(): EvaluationBriefing[] {
  return [...manifest].sort(
    (a, b) => (verdictOrder[a.verdict] ?? 9) - (verdictOrder[b.verdict] ?? 9),
  );
}
