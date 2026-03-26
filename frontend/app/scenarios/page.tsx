'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowLeft, Search, Globe, Shield, Zap, Filter, ChevronRight, AlertTriangle, TrendingUp, Building2, Landmark, Wifi, Fuel, ShieldAlert, Package, Megaphone } from 'lucide-react'
import Link from 'next/link'

// ── Scenario Data ───────────────────────────────

interface ScenarioCard {
  id: string
  title: string
  titleAr: string
  narrative: string
  narrativeAr: string
  domain: string
  region: string
  trigger: string
  riskClass: string
  actors: string[]
  signals: string[]
  impact: { financial: string; customer: string; regulatory: string; reputation: string }
}

const scenarios: ScenarioCard[] = [
  {
    id: 'sc-001', title: 'Fuel Price Increase', titleAr: '\u0627\u0631\u062A\u0641\u0627\u0639 \u0623\u0633\u0639\u0627\u0631 \u0627\u0644\u0648\u0642\u0648\u062F',
    narrative: 'A 10% fuel price hike in Saudi Arabia triggers public backlash, media amplification, and influencer-driven sentiment cascades across GCC social platforms.',
    narrativeAr: '\u0627\u0631\u062A\u0641\u0627\u0639 \u0623\u0633\u0639\u0627\u0631 \u0627\u0644\u0648\u0642\u0648\u062F \u0628\u0646\u0633\u0628\u0629 10% \u0641\u064A \u0627\u0644\u0633\u0639\u0648\u062F\u064A\u0629',
    domain: 'energy', region: 'Saudi Arabia', trigger: 'Price Change', riskClass: 'HIGH',
    actors: ['Ministry of Energy', 'Aramco', 'Citizens', 'Media'],
    signals: ['social', 'media', 'economic'],
    impact: { financial: 'medium', customer: 'high', regulatory: 'low', reputation: 'high' }
  },
  {
    id: 'sc-002', title: 'Kuwait Hashtag Trend', titleAr: '\u0647\u0627\u0634\u062A\u0627\u0642 \u0641\u064A\u0631\u0627\u0644 \u0641\u064A \u0627\u0644\u0643\u0648\u064A\u062A',
    narrative: 'A viral hashtag about a new economic policy in Kuwait spreads rapidly, with misinformation amplifying citizen concerns.',
    narrativeAr: '\u0627\u0646\u062A\u0634\u0627\u0631 \u0647\u0627\u0634\u062A\u0627\u0642 \u0641\u064A\u0631\u0627\u0644 \u062D\u0648\u0644 \u0633\u064A\u0627\u0633\u0629 \u0627\u0642\u062A\u0635\u0627\u062F\u064A\u0629 \u062C\u062F\u064A\u062F\u0629',
    domain: 'policy', region: 'Kuwait', trigger: 'Announcement', riskClass: 'MEDIUM',
    actors: ['Government', 'Parliament', 'Citizens', 'Influencers'],
    signals: ['social', 'media', 'policy'],
    impact: { financial: 'low', customer: 'medium', regulatory: 'medium', reputation: 'medium' }
  },
  {
    id: 'sc-003', title: 'Telecom Price Increase', titleAr: '\u0627\u0631\u062A\u0641\u0627\u0639 \u0623\u0633\u0639\u0627\u0631 \u0627\u0644\u0627\u062A\u0635\u0627\u0644\u0627\u062A',
    narrative: 'Simultaneous price increases by GCC telecom providers trigger coordinated consumer backlash and regulatory scrutiny.',
    narrativeAr: '\u0627\u0631\u062A\u0641\u0627\u0639 \u0623\u0633\u0639\u0627\u0631 \u062E\u062F\u0645\u0627\u062A \u0627\u0644\u0627\u062A\u0635\u0627\u0644\u0627\u062A \u0641\u064A \u062F\u0648\u0644 \u0627\u0644\u062E\u0644\u064A\u062C',
    domain: 'telecom', region: 'GCC', trigger: 'Price Change', riskClass: 'HIGH',
    actors: ['STC', 'Zain', 'CITC', 'Consumers'],
    signals: ['social', 'economic', 'policy'],
    impact: { financial: 'high', customer: 'high', regulatory: 'high', reputation: 'medium' }
  },
  {
    id: 'sc-004', title: 'Insurance Fraud Network', titleAr: '\u0634\u0628\u0643\u0629 \u0627\u062D\u062A\u064A\u0627\u0644 \u062A\u0623\u0645\u064A\u0646\u064A',
    narrative: 'AI detection reveals a cross-border insurance fraud ring operating across Saudi Arabia and UAE, involving coordinated fake claims.',
    narrativeAr: '\u0643\u0634\u0641 \u0634\u0628\u0643\u0629 \u0627\u062D\u062A\u064A\u0627\u0644 \u062A\u0623\u0645\u064A\u0646\u064A \u0639\u0627\u0628\u0631\u0629 \u0644\u0644\u062D\u062F\u0648\u062F',
    domain: 'insurance', region: 'GCC', trigger: 'Fraud', riskClass: 'CRITICAL',
    actors: ['Insurers', 'Fraud Ring', 'SAMA', 'Policyholders'],
    signals: ['business', 'economic', 'policy'],
    impact: { financial: 'critical', customer: 'medium', regulatory: 'critical', reputation: 'high' }
  },
  {
    id: 'sc-005', title: 'Bank Liquidity Panic', titleAr: '\u0630\u0639\u0631 \u0633\u064A\u0648\u0644\u0629 \u0628\u0646\u0643\u064A\u0629',
    narrative: 'A viral rumor about a major GCC bank facing liquidity issues triggers a social media firestorm and deposit withdrawal surge.',
    narrativeAr: '\u0625\u0634\u0627\u0639\u0629 \u0641\u064A\u0631\u0627\u0644\u064A\u0629 \u0639\u0646 \u0623\u0632\u0645\u0629 \u0633\u064A\u0648\u0644\u0629 \u0641\u064A \u0628\u0646\u0643 \u062E\u0644\u064A\u062C\u064A \u0643\u0628\u064A\u0631',
    domain: 'banking', region: 'GCC', trigger: 'Rumor', riskClass: 'CRITICAL',
    actors: ['Central Bank', 'Commercial Banks', 'Depositors', 'Media'],
    signals: ['social', 'media', 'economic', 'business'],
    impact: { financial: 'critical', customer: 'critical', regulatory: 'high', reputation: 'critical' }
  },
  {
    id: 'sc-006', title: 'Government Policy Shock', titleAr: '\u0635\u062F\u0645\u0629 \u0633\u064A\u0627\u0633\u0629 \u062D\u0643\u0648\u0645\u064A\u0629',
    narrative: 'An unexpected policy announcement on expat taxation in UAE triggers business community anxiety and talent flight concerns.',
    narrativeAr: '\u0625\u0639\u0644\u0627\u0646 \u0633\u064A\u0627\u0633\u0629 \u063A\u064A\u0631 \u0645\u062A\u0648\u0642\u0639 \u0639\u0646 \u0636\u0631\u0627\u0626\u0628 \u0627\u0644\u0648\u0627\u0641\u062F\u064A\u0646',
    domain: 'policy', region: 'UAE', trigger: 'Announcement', riskClass: 'HIGH',
    actors: ['Government', 'Business Community', 'Expats', 'Media'],
    signals: ['social', 'media', 'economic', 'policy'],
    impact: { financial: 'high', customer: 'high', regulatory: 'medium', reputation: 'high' }
  },
  {
    id: 'sc-007', title: 'Misinformation Campaign', titleAr: '\u062D\u0645\u0644\u0629 \u0645\u0639\u0644\u0648\u0645\u0627\u062A \u0645\u0636\u0644\u0644\u0629',
    narrative: 'Coordinated bot-driven misinformation campaign targets a GCC sovereign wealth fund, spreading false investment loss narratives.',
    narrativeAr: '\u062D\u0645\u0644\u0629 \u0645\u0639\u0644\u0648\u0645\u0627\u062A \u0645\u0636\u0644\u0644\u0629 \u062A\u0633\u062A\u0647\u062F\u0641 \u0635\u0646\u062F\u0648\u0642 \u062B\u0631\u0648\u0629 \u0633\u064A\u0627\u062F\u064A',
    domain: 'security', region: 'GCC', trigger: 'Cyber Attack', riskClass: 'CRITICAL',
    actors: ['Bot Network', 'SWF', 'Government', 'International Media'],
    signals: ['social', 'media', 'economic'],
    impact: { financial: 'critical', customer: 'medium', regulatory: 'medium', reputation: 'critical' }
  },
  {
    id: 'sc-008', title: 'Supply Chain Disruption', titleAr: '\u0627\u0636\u0637\u0631\u0627\u0628 \u0633\u0644\u0633\u0644\u0629 \u0627\u0644\u0625\u0645\u062F\u0627\u062F',
    narrative: 'A major port disruption in the Gulf affects food and medical supply chains, triggering panic buying and price gouging.',
    narrativeAr: '\u0627\u0636\u0637\u0631\u0627\u0628 \u0641\u064A \u0645\u064A\u0646\u0627\u0621 \u062E\u0644\u064A\u062C\u064A \u0631\u0626\u064A\u0633\u064A \u064A\u0624\u062B\u0631 \u0639\u0644\u0649 \u0633\u0644\u0627\u0633\u0644 \u0627\u0644\u0625\u0645\u062F\u0627\u062F',
    domain: 'supply-chain', region: 'GCC', trigger: 'Incident', riskClass: 'HIGH',
    actors: ['Port Authority', 'Importers', 'Consumers', 'Government'],
    signals: ['economic', 'social', 'media', 'business'],
    impact: { financial: 'high', customer: 'critical', regulatory: 'medium', reputation: 'medium' }
  },
  {
    id: 'sc-009', title: 'Brand Crisis — Viral Backlash', titleAr: '\u0623\u0632\u0645\u0629 \u0639\u0644\u0627\u0645\u0629 \u062A\u062C\u0627\u0631\u064A\u0629',
    narrative: 'A leaked internal document from a major GCC brand reveals discriminatory policies, triggering boycott campaigns.',
    narrativeAr: '\u062A\u0633\u0631\u064A\u0628 \u0648\u062B\u064A\u0642\u0629 \u062F\u0627\u062E\u0644\u064A\u0629 \u0645\u0646 \u0639\u0644\u0627\u0645\u0629 \u062A\u062C\u0627\u0631\u064A\u0629 \u062E\u0644\u064A\u062C\u064A\u0629 \u0643\u0628\u0631\u0649',
    domain: 'brand', region: 'Saudi Arabia', trigger: 'Leak', riskClass: 'HIGH',
    actors: ['Brand', 'Employees', 'Public', 'Competitors'],
    signals: ['social', 'media', 'business'],
    impact: { financial: 'high', customer: 'high', regulatory: 'medium', reputation: 'critical' }
  },
]

const domainIcons: Record<string, any> = {
  energy: Fuel, telecom: Wifi, banking: Landmark, insurance: ShieldAlert,
  policy: Building2, brand: Megaphone, 'supply-chain': Package, security: Shield,
}

const domainColors: Record<string, string> = {
  energy: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  telecom: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  banking: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  insurance: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  policy: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  brand: 'text-pink-400 bg-pink-500/10 border-pink-500/20',
  'supply-chain': 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  security: 'text-red-400 bg-red-500/10 border-red-500/20',
}

const riskColors: Record<string, string> = {
  LOW: 'text-emerald-400 bg-emerald-500/10',
  MEDIUM: 'text-amber-400 bg-amber-500/10',
  HIGH: 'text-orange-400 bg-orange-500/10',
  CRITICAL: 'text-red-400 bg-red-500/10',
}

const impactDot: Record<string, string> = {
  low: 'bg-emerald-400', medium: 'bg-amber-400', high: 'bg-orange-400', critical: 'bg-red-400',
}

const domains = ['all', 'energy', 'telecom', 'banking', 'insurance', 'policy', 'brand', 'supply-chain', 'security']

export default function ScenariosPage() {
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  const filtered = scenarios.filter(s => {
    if (filter !== 'all' && s.domain !== filter) return false
    if (search && !s.title.toLowerCase().includes(search.toLowerCase()) && !s.titleAr.includes(search)) return false
    return true
  })

  return (
    <div className="min-h-screen bg-ds-bg text-ds-text">
      <header className="h-14 border-b border-zinc-800/60 flex items-center justify-between px-6 bg-zinc-950/80 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-zinc-500 hover:text-zinc-300 transition-colors"><ArrowLeft className="w-4 h-4" /></Link>
          <span className="text-xs font-mono font-bold tracking-wider text-indigo-400">DEEVO SIM</span>
          <span className="text-zinc-600">/</span>
          <span className="text-xs text-zinc-400">Scenario Library</span>
        </div>
        <Link href="/demo" className="text-xs px-4 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-colors">
          Open Control Room
        </Link>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-100 mb-2">Scenario Library</h1>
          <p className="text-sm text-zinc-500">Enterprise simulation scenarios for GCC risk intelligence and decision modeling</p>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search scenarios..." className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 outline-none focus:border-indigo-500/40" />
          </div>
          <div className="flex items-center gap-1">
            <Filter className="w-3.5 h-3.5 text-zinc-500 mr-1" />
            {domains.map(d => (
              <button key={d} onClick={() => setFilter(d)} className={`text-[10px] uppercase tracking-wider px-2.5 py-1.5 rounded-md transition-all ${filter === d ? 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30' : 'text-zinc-500 hover:text-zinc-400 border border-transparent'}`}>
                {d === 'all' ? 'All' : d === 'supply-chain' ? 'Supply' : d}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((sc, i) => {
            const DomainIcon = domainIcons[sc.domain] || Globe
            return (
              <motion.div key={sc.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-all group cursor-pointer">
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2 rounded-lg border ${domainColors[sc.domain] || 'text-zinc-400 bg-zinc-800 border-zinc-700'}`}>
                    <DomainIcon className="w-4 h-4" />
                  </div>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${riskColors[sc.riskClass]}`}>{sc.riskClass}</span>
                </div>
                <h3 className="text-sm font-semibold text-zinc-100 mb-1 group-hover:text-indigo-300 transition-colors">{sc.title}</h3>
                <p className="text-xs text-zinc-500 mb-1 text-right" dir="rtl">{sc.titleAr}</p>
                <p className="text-xs text-zinc-400 leading-relaxed mb-4 line-clamp-2">{sc.narrative}</p>
                <div className="flex flex-wrap gap-1 mb-3">
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">{sc.region}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">{sc.trigger}</span>
                  {sc.signals.slice(0, 2).map(s => (
                    <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400">{s}</span>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-zinc-800/60">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1"><span className={`w-1.5 h-1.5 rounded-full ${impactDot[sc.impact.financial]}`} /><span className="text-[9px] text-zinc-600">FIN</span></div>
                    <div className="flex items-center gap-1"><span className={`w-1.5 h-1.5 rounded-full ${impactDot[sc.impact.customer]}`} /><span className="text-[9px] text-zinc-600">CUS</span></div>
                    <div className="flex items-center gap-1"><span className={`w-1.5 h-1.5 rounded-full ${impactDot[sc.impact.regulatory]}`} /><span className="text-[9px] text-zinc-600">REG</span></div>
                    <div className="flex items-center gap-1"><span className={`w-1.5 h-1.5 rounded-full ${impactDot[sc.impact.reputation]}`} /><span className="text-[9px] text-zinc-600">REP</span></div>
                  </div>
                  <Link href="/demo" className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    Launch <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </motion.div>
            )
          })}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <Globe className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No scenarios match your filter</p>
          </div>
        )}

        <div className="mt-8 text-center">
          <p className="text-[10px] uppercase tracking-widest text-zinc-600">{filtered.length} of {scenarios.length} scenarios</p>
        </div>
      </div>
    </div>
  )
  }
