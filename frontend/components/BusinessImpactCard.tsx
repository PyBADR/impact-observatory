'use client'

import { motion } from 'framer-motion'
import {
  DollarSign, Users, Scale, Shield,
  TrendingUp, TrendingDown, Minus, AlertTriangle
} from 'lucide-react'
import { label } from '@/lib/i18n'
import type { BusinessImpact } from '@/lib/types'

interface BusinessImpactCardProps {
  impact: BusinessImpact
  compact?: boolean
}

const impactColor = (value: number): string => {
  if (value >= 0.7) return 'text-red-400 bg-red-500/10 border-red-500/20'
  if (value >= 0.4) return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
  return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
}

const impactBarColor = (value: number): string => {
  if (value >= 0.7) return 'bg-red-500'
  if (value >= 0.4) return 'bg-amber-500'
  return 'bg-emerald-500'
}

const impactIcon = (value: number) => {
  if (value >= 0.7) return <TrendingUp className="w-3 h-3" />
  if (value >= 0.4) return <Minus className="w-3 h-3" />
  return <TrendingDown className="w-3 h-3" />
}

const impactLabel = (value: number): string => {
  if (value >= 0.8) return 'CRITICAL'
  if (value >= 0.6) return 'HIGH'
  if (value >= 0.4) return 'MEDIUM'
  if (value >= 0.2) return 'LOW'
  return 'MINIMAL'
}

interface DimensionProps {
  icon: React.ReactNode
  title: string
  value: number
  description: string
  compact?: boolean
}

function ImpactDimension({ icon, title, value, description, compact }: DimensionProps) {
  const colors = impactColor(value)
  const barColor = impactBarColor(value)

  if (compact) {
    return (
      <div className={`flex items-center gap-2 px-2 py-1.5 rounded border ${colors}`}>
        {icon}
        <span className="text-[10px] font-mono uppercase">{title}</span>
        <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${barColor}`}
            initial={{ width: 0 }}
            animate={{ width: `${value * 100}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
        <span className="text-[10px] font-mono">{Math.round(value * 100)}%</span>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-3 rounded-lg border ${colors}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-mono uppercase tracking-wider">{title}</span>
        </div>
        <div className="flex items-center gap-1">
          {impactIcon(value)}
          <span className="text-[10px] font-mono font-bold">{impactLabel(value)}</span>
        </div>
      </div>
      <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-2">
        <motion.div
          className={`h-full rounded-full ${barColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
        />
      </div>
      <p className="text-[11px] text-zinc-500 leading-relaxed">{description}</p>
    </motion.div>
  )
}

export default function BusinessImpactCard({ impact, compact = false }: BusinessImpactCardProps) {
  const overallRisk = (
    impact.financial.score * 0.35 +
    impact.customer.score * 0.25 +
    impact.regulatory.score * 0.25 +
    impact.reputation.score * 0.15
  )

  const dimensions = [
    {
      icon: <DollarSign className="w-3.5 h-3.5" />,
      title: label('financialImpact'),
      value: impact.financial.score,
      description: impact.financial.detail || 'Potential revenue and cost implications from this scenario.',
    },
    {
      icon: <Users className="w-3.5 h-3.5" />,
      title: label('customerImpact'),
      value: impact.customer.score,
      description: impact.customer.detail || 'Expected impact on customer satisfaction, retention, and acquisition.',
    },
    {
      icon: <Scale className="w-3.5 h-3.5" />,
      title: label('regulatoryRisk'),
      value: impact.regulatory.score,
      description: impact.regulatory.detail || 'Regulatory exposure including SAMA, CMA, and PDPL compliance risk.',
    },
    {
      icon: <Shield className="w-3.5 h-3.5" />,
      title: label('reputationDamage'),
      value: impact.reputation.score,
      description: impact.reputation.detail || 'Brand perception and public trust impact assessment.',
    },
  ]

  return (
    <div className="border border-zinc-800 rounded-lg bg-zinc-950/80 backdrop-blur overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`w-4 h-4 ${impactColor(overallRisk).split(' ')[0]}`} />
          <span className="text-xs font-mono uppercase tracking-widest text-zinc-400">
            {label('businessImpact')}
          </span>
        </div>
        <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${impactColor(overallRisk)}`}>
          {impactLabel(overallRisk)}
          <span className="text-zinc-500 font-normal ml-1">{Math.round(overallRisk * 100)}%</span>
        </div>
      </div>

      {/* Impact Dimensions */}
      <div className={`p-3 ${compact ? 'space-y-2' : 'grid grid-cols-2 gap-3'}`}>
        {dimensions.map((dim, i) => (
          <ImpactDimension
            key={i}
            icon={dim.icon}
            title={dim.title}
            value={dim.value}
            description={dim.description}
            compact={compact}
          />
        ))}
      </div>

      {/* Summary Bar */}
      {!compact && (
        <div className="px-4 py-2 border-t border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-zinc-600 uppercase">Weighted Risk Score</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${impactBarColor(overallRisk)}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${overallRisk * 100}%` }}
                  transition={{ duration: 1, ease: 'easeOut', delay: 0.5 }}
                />
              </div>
              <span className={`text-xs font-mono font-bold ${impactColor(overallRisk).split(' ')[0]}`}>
                {Math.round(overallRisk * 100)}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
