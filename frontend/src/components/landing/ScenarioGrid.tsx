/**
 * ScenarioGrid — renders the full scenario catalog on the landing page.
 * Static data reflecting the 15 backend templates.
 * Wired to ScenarioCard for each entry.
 */

import { ScenarioCard } from './ScenarioCard';
import type { ScenarioCardProps } from './ScenarioCard';

/**
 * Static scenario manifest — sourced from backend SCENARIO_TEMPLATES.
 * Kept static for landing page performance (no API call needed).
 * severity_level derived from base shock intensity ranges.
 */
const scenarios: ScenarioCardProps[] = [
  {
    id: 'hormuz_chokepoint_disruption',
    title: 'Strait of Hormuz Disruption',
    description: 'Full or partial blockage of the Strait of Hormuz, disrupting oil tanker transit and Gulf shipping lanes.',
    severityLevel: 'severe',
    affectedSectors: ['Energy', 'Shipping', 'Insurance', 'Banking'],
    horizonHours: 72,
  },
  {
    id: 'hormuz_full_closure',
    title: 'Hormuz Full Closure',
    description: 'Complete closure of the Strait of Hormuz with all transit halted.',
    severityLevel: 'severe',
    affectedSectors: ['Energy', 'Shipping', 'Government', 'Banking'],
    horizonHours: 72,
  },
  {
    id: 'saudi_oil_shock',
    title: 'Saudi Oil Production Shock',
    description: 'Sudden disruption to Saudi Aramco production capacity affecting global energy supply.',
    severityLevel: 'high',
    affectedSectors: ['Energy', 'Government', 'Banking', 'Real Estate'],
    horizonHours: 168,
  },
  {
    id: 'uae_banking_crisis',
    title: 'UAE Banking Sector Stress',
    description: 'Systemic stress across UAE banking institutions with liquidity and credit contagion risk.',
    severityLevel: 'high',
    affectedSectors: ['Banking', 'Fintech', 'Real Estate', 'Insurance'],
    horizonHours: 72,
  },
  {
    id: 'gcc_cyber_attack',
    title: 'GCC Cyber Infrastructure Attack',
    description: 'Coordinated cyber attack targeting critical financial and energy infrastructure across the GCC.',
    severityLevel: 'elevated',
    affectedSectors: ['Banking', 'Fintech', 'Government', 'Energy'],
    horizonHours: 48,
  },
  {
    id: 'qatar_lng_disruption',
    title: 'Qatar LNG Export Disruption',
    description: 'Disruption to Qatar LNG export operations affecting global gas supply commitments.',
    severityLevel: 'high',
    affectedSectors: ['Energy', 'Shipping', 'Government'],
    horizonHours: 168,
  },
  {
    id: 'red_sea_trade_corridor_instability',
    title: 'Red Sea Corridor Instability',
    description: 'Shipping disruption along the Red Sea trade corridor, forcing rerouting and increased costs.',
    severityLevel: 'elevated',
    affectedSectors: ['Shipping', 'Insurance', 'Energy', 'Banking'],
    horizonHours: 168,
  },
  {
    id: 'energy_market_volatility_shock',
    title: 'Energy Market Volatility Shock',
    description: 'Sudden extreme volatility in GCC energy markets with cascading fiscal and sovereign effects.',
    severityLevel: 'elevated',
    affectedSectors: ['Energy', 'Government', 'Banking'],
    horizonHours: 72,
  },
  {
    id: 'regional_liquidity_stress_event',
    title: 'Regional Liquidity Stress',
    description: 'Cross-border liquidity stress across GCC banking systems with interbank contagion.',
    severityLevel: 'high',
    affectedSectors: ['Banking', 'Fintech', 'Insurance', 'Government'],
    horizonHours: 48,
  },
  {
    id: 'bahrain_sovereign_stress',
    title: 'Bahrain Fiscal Stress',
    description: 'Fiscal and sovereign stress on Bahrain with debt sustainability and rating pressure.',
    severityLevel: 'guarded',
    affectedSectors: ['Government', 'Banking', 'Real Estate'],
    horizonHours: 720,
  },
  {
    id: 'kuwait_fiscal_shock',
    title: 'Kuwait Oil Revenue Shock',
    description: 'Kuwait fiscal shock from sustained low oil revenue with budget and reserves pressure.',
    severityLevel: 'guarded',
    affectedSectors: ['Government', 'Banking', 'Energy'],
    horizonHours: 720,
  },
  {
    id: 'oman_port_closure',
    title: 'Oman Port Closure',
    description: 'Closure of Salalah and Sohar ports disrupting Omani trade and transit logistics.',
    severityLevel: 'elevated',
    affectedSectors: ['Shipping', 'Energy', 'Government'],
    horizonHours: 72,
  },
  {
    id: 'critical_port_throughput_disruption',
    title: 'Multi-Port Throughput Failure',
    description: 'Simultaneous throughput failure across multiple GCC ports causing supply chain cascades.',
    severityLevel: 'severe',
    affectedSectors: ['Shipping', 'Energy', 'Insurance', 'Banking'],
    horizonHours: 168,
  },
  {
    id: 'financial_infrastructure_cyber_disruption',
    title: 'Financial System Cyber Attack',
    description: 'Targeted cyber attack on GCC financial settlement and payment infrastructure.',
    severityLevel: 'high',
    affectedSectors: ['Banking', 'Fintech', 'Insurance', 'Government'],
    horizonHours: 24,
  },
  {
    id: 'iran_regional_escalation',
    title: 'Iran Regional Escalation',
    description: 'Regional geopolitical escalation involving Iran with cross-sector economic consequences.',
    severityLevel: 'severe',
    affectedSectors: ['Energy', 'Shipping', 'Banking', 'Insurance', 'Government'],
    horizonHours: 168,
  },
];

export function ScenarioGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {scenarios.map((scenario) => (
        <ScenarioCard key={scenario.id} {...scenario} />
      ))}
    </div>
  );
}
