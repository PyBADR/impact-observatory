'use client'

import { motion } from 'framer-motion'
import {
  FileText, TrendingUp, Users, Activity,
  Shield, BarChart3, ChevronRight, Eye
} from 'lucide-react'
import type { SimulationReport } from '@/lib/types'

interface ReportPanelProps {
  report: SimulationReport | null
  isActive: boolean
}

const spreadColors: Record<string, string> = {
  low: 'text-emerald-400 bg-emerald-500/10',
  medium: 'text-amber-400 bg-amber-500/10',
  high: 'text-orange-400 bg-orange-500/10',
  critical: 'text-red-400 bg-red-500/10',
}

export default function ReportPanel({ report, isActive }: ReportPanelProps) {
  if (!isActive || !report) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-600">
        <div className="text-center">
          <FileText className="w-8 h-8 mx-auto mb-3 opacity-40" />
          <p className="text-sm">Run a simulation to generate</p>
          <p className="text-sm">intelligence brief</p>
        </div>
      </div>
    )
  }

  const spreadStyle = spreadColors[report.spreadLevel] || spreadColors.medium

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full overflow-y-auto space-y-4 pr-1 custom-scrollbar"
    >
      {/* Section 1: Prediction Summary */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
            1. Prediction Summary
          </h4>
        </div>
        <p className="text-sm text-zinc-200 leading-relaxed">{report.prediction}</p>
      </div>

      {/* Section 2: Risk Analysis */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-indigo-400" />
          <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
            2. Risk Analysis
          </h4>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-zinc-800/50 rounded-md p-2.5">
            <p className="text-[10px] text-zinc-500 uppercase">Spread Level</p>
            <span className={`text-sm font-bold px-2 py-0.5 rounded ${spreadStyle}`}>
              {report.spreadLevel.toUpperCase()}
            </span>
          </div>
          <div className="bg-zinc-800/50 rounded-md p-2.5">
            <p className="text-[10px] text-zinc-500 uppercase">Main Driver</p>
            <p className="text-xs text-zinc-200 mt-0.5">{report.mainDriver}</p>
          </div>
        </div>
      </div>

      {/* Section 3: Key Influencers */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-indigo-400" />
          <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
            3. Key Influencers
          </h4>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {report.topInfluencers.map((name, i) => (
            <span
              key={i}
              className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
            >
              {name}
            </span>
          ))}
        </div>
      </div>

      {/* Section 4: Spread Dynamics */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
            4. Spread Dynamics
          </h4>
        </div>
        <div className="space-y-2">
          {report.keyObservations.map((obs, i) => (
            <div key={i} className="flex items-start gap-2">
              <ChevronRight className="w-3 h-3 text-zinc-600 mt-1 shrink-0" />
              <p className="text-xs text-zinc-300 leading-relaxed">{obs}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Section 5: Recommended Actions (from decision layer) */}
      {report.decision && (
        <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
          <div className="flex items-center gap-2 mb-3">
            <Eye className="w-4 h-4 text-indigo-400" />
            <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
              5. Recommended Actions
            </h4>
          </div>
          <div className="space-y-1.5">
            {report.decision.recommendedActions.slice(0, 3).map((a) => (
              <div key={a.id} className="flex items-start gap-2 text-xs">
                <span className={`shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full ${
                  a.priority === 'immediate' ? 'bg-red-400' :
                  a.priority === 'short-term' ? 'bg-amber-400' : 'bg-blue-400'
                }`} />
                <span className="text-zinc-300">{a.action}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 6: Confidence Score */}
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="w-4 h-4 text-indigo-400" />
          <h4 className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
            6. Confidence Score
          </h4>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-2.5 bg-zinc-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: (report.confidence * 100) + '%' }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
              className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-indigo-400"
            />
          </div>
          <span className="text-lg font-bold text-indigo-400 tabular-nums">
            {(report.confidence * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-[10px] text-zinc-500 mt-2">
          Based on entity density, agent behavior patterns, and historical GCC scenario correlation.
        </p>
      </div>
    </motion.div>
  )
}
