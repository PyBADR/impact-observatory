'use client'

import { Activity, TrendingDown, Layers, Info } from 'lucide-react'
import type { PropagationResult } from '@/lib/propagation-engine'
import { getLayerColor } from '@/lib/utils'

/* ═══════════════════════════════════════════════════
   Propagation Result Panels — Impact Chain, Top Drivers, Sector Impact
   Driven by real propagation engine output
   ═══════════════════════════════════════════════════ */

/** Impact Chain Panel — shows causal propagation path */
export function ImpactChainPanel({ chain }: { chain: PropagationResult['propagationChain'] }) {
  const displayChain = chain
    .filter((s, i, arr) => arr.findIndex(x => x.from === s.from && x.to === s.to) === i)
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
    .slice(0, 10)

  return (
    <div className="ds-card rounded-ds-lg p-3 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <Activity size={11} className="text-ds-accent" />
        <span className="text-nano font-mono uppercase tracking-widest text-ds-text-dim">Impact Chain</span>
        <span className="text-nano text-ds-text-dim ml-auto">{chain.length} paths</span>
      </div>
      <div className="space-y-1.5 max-h-[200px] overflow-y-auto">
        {displayChain.map((step, i) => {
          const absImpact = Math.abs(step.impact)
          const direction = step.impact > 0 ? '↑' : '↓'
          const barWidth = Math.max(8, absImpact * 100)
          return (
            <div key={i} className="flex items-center gap-2 text-[10px] font-mono">
              <div className="flex-1 min-w-0 truncate text-ds-text-muted">
                {step.fromLabel} → {step.toLabel}
              </div>
              <div className="w-[60px] bg-ds-bg-alt rounded-full h-1.5 flex-shrink-0">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${barWidth}%`,
                    backgroundColor: absImpact > 0.3 ? '#EF5454' : absImpact > 0.15 ? '#F5A623' : '#5B7BF8',
                  }}
                />
              </div>
              <span className={`w-[36px] text-right flex-shrink-0 ${absImpact > 0.3 ? 'text-ds-danger' : 'text-ds-text-secondary'}`}>
                {direction}{(absImpact * 100).toFixed(0)}%
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Top Drivers Panel */
export function TopDriversPanel({ drivers }: { drivers: PropagationResult['topDrivers'] }) {
  return (
    <div className="ds-card rounded-ds-lg p-3 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <TrendingDown size={11} className="text-ds-warning" />
        <span className="text-nano font-mono uppercase tracking-widest text-ds-text-dim">Top Drivers</span>
      </div>
      <div className="space-y-1.5">
        {drivers.slice(0, 5).map((driver, i) => (
          <div key={driver.nodeId} className="flex items-center gap-2 text-[10px] font-mono">
            <span className="text-ds-text-dim w-3">{i + 1}.</span>
            <div
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: getLayerColor(driver.layer) }}
            />
            <span className="flex-1 truncate text-ds-text-muted">{driver.label}</span>
            <span className="text-ds-text-secondary">{(driver.impact * 100).toFixed(0)}%</span>
            <span className="text-ds-text-dim">·{driver.outDegree}out</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Sector Impact Panel */
export function SectorImpactPanel({ sectors }: { sectors: PropagationResult['affectedSectors'] }) {
  return (
    <div className="ds-card rounded-ds-lg p-3 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <Layers size={11} className="text-ds-accent" />
        <span className="text-nano font-mono uppercase tracking-widest text-ds-text-dim">Sector Impact</span>
      </div>
      <div className="space-y-2">
        {sectors.map(sector => {
          const pct = Math.round(sector.avgImpact * 100)
          return (
            <div key={sector.sector} className="space-y-1">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: sector.color }} />
                  <span className="text-ds-text-muted">{sector.sectorLabel}</span>
                </div>
                <span className={pct > 30 ? 'text-ds-danger' : 'text-ds-text-secondary'}>
                  {pct}% avg
                </span>
              </div>
              <div className="w-full bg-ds-bg-alt rounded-full h-1.5">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(4, pct)}%`,
                    backgroundColor: sector.color,
                    opacity: 0.7,
                  }}
                />
              </div>
              <div className="flex justify-between text-[9px] text-ds-text-dim">
                <span>{sector.nodeCount} nodes</span>
                <span>Peak: {sector.topNode} ({Math.round(sector.maxImpact * 100)}%)</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Explanation Panel */
export function ExplanationPanel({
  explanation, confidence, totalLoss, spreadLevel,
}: {
  explanation: string
  confidence: number
  totalLoss: number
  spreadLevel: string
}) {
  const spreadColor = spreadLevel === 'critical' ? 'text-ds-danger' :
    spreadLevel === 'high' ? 'text-ds-warning' :
    spreadLevel === 'medium' ? 'text-ds-accent' : 'text-ds-success'

  return (
    <div className="ds-card rounded-ds-lg p-3 space-y-2 border border-ds-accent/15">
      <div className="flex items-center gap-2 mb-1">
        <Info size={11} className="text-ds-accent" />
        <span className="text-nano font-mono uppercase tracking-widest text-ds-text-dim">Analysis</span>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
        <div>
          <span className="text-ds-text-dim">Total Loss</span>
          <div className="text-ds-text font-semibold">${(totalLoss).toFixed(1)}B</div>
        </div>
        <div>
          <span className="text-ds-text-dim">Confidence</span>
          <div className="text-emerald-400 font-semibold">{Math.round(confidence * 100)}%</div>
        </div>
        <div>
          <span className="text-ds-text-dim">Spread</span>
          <div className={`font-semibold uppercase ${spreadColor}`}>{spreadLevel}</div>
        </div>
      </div>
      <p className="text-[10px] text-ds-text-muted leading-relaxed">{explanation}</p>
    </div>
  )
}
