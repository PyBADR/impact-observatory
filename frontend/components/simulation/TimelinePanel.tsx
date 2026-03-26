'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, TrendingDown, TrendingUp, Minus, Play, Pause, SkipForward } from 'lucide-react'

interface SimStep {
  step: number
  label: string
  summary: string
  sentiment_score: number
  visibility_score: number
  events: string[]
}

interface TimelinePanelProps {
  steps: SimStep[]
  activeStep?: number
  onStepChange?: (step: number) => void
}

export default function TimelinePanel({ steps, activeStep = 0, onStepChange }: TimelinePanelProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentStep, setCurrentStep] = useState(activeStep)

  const getSentimentIcon = (score: number) => {
    if (score < 0.3) return <TrendingDown size={13} className="text-ds-danger" />
    if (score > 0.5) return <TrendingUp size={13} className="text-ds-success" />
    return <Minus size={13} className="text-ds-warning" />
  }

  const handleStepClick = (stepIdx: number) => {
    setCurrentStep(stepIdx)
    onStepChange?.(stepIdx)
  }

  return (
    <div className="bg-ds-surface rounded-ds-xl border border-ds-border overflow-hidden">
      <div className="ds-panel-header">
        <div className="ds-panel-header-title">
          <Activity size={14} className="text-ds-accent" />
          <span className="text-caption font-semibold text-ds-text tracking-tight">Simulation Timeline</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 mr-2">
            <button onClick={() => setIsPlaying(!isPlaying)} className="p-1 rounded-md hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-accent">
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            </button>
            <button onClick={() => handleStepClick(Math.min(currentStep + 1, steps.length - 1))} className="p-1 rounded-md hover:bg-ds-card transition-colors text-ds-text-muted hover:text-ds-text">
              <SkipForward size={13} />
            </button>
          </div>
          <div className="flex items-center gap-1">
            {steps.map((_, idx) => (
              <button key={idx} onClick={() => handleStepClick(idx)} className={`w-6 h-1.5 rounded-full transition-all duration-300 ${
                idx === currentStep ? 'bg-ds-accent shadow-ds-glow' : idx < currentStep ? 'bg-ds-accent/30' : 'bg-ds-border'
              }`} />
            ))}
          </div>
          <span className="ds-panel-header-meta ml-2">{currentStep + 1}/{steps.length}</span>
        </div>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {steps.map((step, i) => (
            <motion.button key={step.step} onClick={() => handleStepClick(i)} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08, duration: 0.4 }}
              className={`text-left p-4 rounded-ds-lg border transition-all duration-300 ${
                i === currentStep ? 'border-ds-accent/40 bg-ds-accent/5 shadow-ds-glow'
                  : i < currentStep ? 'border-ds-border bg-ds-card/50 opacity-70'
                  : 'border-ds-border bg-ds-card hover:bg-ds-card-hover hover:border-ds-border-hover'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-mono font-bold ${
                    i === currentStep ? 'bg-ds-accent/20 text-ds-accent' : 'bg-ds-surface text-ds-text-dim'
                  }`}>{step.step}</div>
                  <span className={`text-nano font-mono uppercase tracking-wider ${
                    i === currentStep ? 'text-ds-accent' : 'text-ds-text-dim'
                  }`}>{step.label}</span>
                </div>
                {getSentimentIcon(step.sentiment_score)}
              </div>
              <p className="text-[11px] text-ds-text-secondary leading-relaxed line-clamp-2 mb-3">{step.summary}</p>
              <div className="flex items-center gap-1.5">
                <div className={`h-1 rounded-full ${
                  step.visibility_score > 0.7 ? 'bg-ds-danger' : step.visibility_score > 0.4 ? 'bg-ds-warning' : 'bg-ds-success'
                }`} style={{ width: `${step.visibility_score * 48}px` }} />
                <span className="text-[9px] font-mono text-ds-text-dim">{Math.round(step.visibility_score * 100)}%</span>
              </div>
              {step.events.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1">
                  {step.events.slice(0, 2).map((event, j) => (
                    <span key={j} className="inline-block px-1.5 py-0.5 text-[8px] font-mono bg-ds-bg border border-ds-border-subtle rounded text-ds-text-dim truncate max-w-[90px]">{event}</span>
                  ))}
                  {step.events.length > 2 && (
                    <span className="text-[8px] text-ds-text-dim font-mono">+{step.events.length - 2}</span>
                  )}
                </div>
              )}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  )
  }
