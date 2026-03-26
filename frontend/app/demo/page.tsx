'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, Settings, Zap, Globe, ChevronDown, Play, Languages } from 'lucide-react'
import Link from 'next/link'
import type { Node, Edge } from '@xyflow/react'
import GraphPanel from '@/components/graph/GraphPanel'
import ReportPanel from '@/components/report/ReportPanel'
import DecisionPanel from '@/components/decision/DecisionPanel'
import ChatPanel from '@/components/chat/ChatPanel'
import TimelinePanel from '@/components/simulation/TimelinePanel'
import ScenarioComposer from '@/components/ScenarioComposer'
import BusinessImpactCard from '@/components/BusinessImpactCard'
import {
  mockScenarios,
  mockGraphNodes,
  mockGraphEdges,
  mockSimulationSteps,
  mockReport,
  mockDecision,
} from '@/lib/mock-data'
import { label, setLanguage, getLanguage } from '@/lib/i18n'

type ViewTab = 'brief' | 'decision'

export default function DemoPage() {
  const [selectedScenario, setSelectedScenario] = useState(mockScenarios[0])
  const [isSimulating, setIsSimulating] = useState(false)
  const [simulationComplete, setSimulationComplete] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [rightTab, setRightTab] = useState<ViewTab>('brief')
  const [lang, setLang] = useState<'en' | 'ar'>(getLanguage())
  const [showComposer, setShowComposer] = useState(false)

  const toggleLanguage = () => {
    const next = lang === 'en' ? 'ar' : 'en'
    setLanguage(next)
    setLang(next)
  }

  /* ---- convert GraphNode[] -> React Flow Node[] ---- */
  const rfNodes: Node[] = mockGraphNodes.map((n, i) => ({
    id: n.id,
    position: {
      x: Math.cos((i * Math.PI * 2) / mockGraphNodes.length) * 250 + 350,
      y: Math.sin((i * Math.PI * 2) / mockGraphNodes.length) * 200 + 250,
    },
    data: { label: n.label, type: n.type, weight: n.weight },
    type: 'custom' as const,
  }))

  const rfEdges: Edge[] = mockGraphEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    animated: true,
  }))

  /* ---- convert SimulationStep[] -> SimStep[] ---- */
  const timelineSteps = mockSimulationSteps.map((s) => ({
    step: s.id,
    label: s.timestamp,
    summary: s.description,
    sentiment_score: (s.sentiment + 1) / 2,
    visibility_score: s.visibility,
    events: s.events,
  }))

  const runSimulation = () => {
    setIsSimulating(true)
    setSimulationComplete(false)
    setCurrentStep(0)

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= mockSimulationSteps.length - 1) {
          clearInterval(interval)
          setIsSimulating(false)
          setSimulationComplete(true)
          return prev
        }
        return prev + 1
      })
    }, 1200)
  }

  const statusLabel = simulationComplete ? label('complete') : isSimulating ? label('simulating') : label('ready')

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0f] text-zinc-100 overflow-hidden">
      {/* ===== Top Bar ===== */}
      <header className="h-11 border-b border-zinc-800/60 flex items-center justify-between px-4 bg-zinc-950/80 backdrop-blur shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <Zap className="w-4 h-4 text-indigo-500" />
          <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Deevo Sim</span>
          <span className="text-zinc-700">/</span>
          <span className="text-xs text-zinc-400">{label('controlRoom')}</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${simulationComplete ? 'bg-emerald-400' : isSimulating ? 'bg-amber-400 animate-pulse' : 'bg-zinc-600'}`} />
            <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              {statusLabel}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1 px-2 py-1 rounded border border-zinc-800 text-[10px] font-mono text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors"
          >
            <Languages className="w-3 h-3" />
            {lang === 'en' ? 'AR' : 'EN'}
          </button>
          <Link href="/scenarios" className="text-[10px] font-mono text-indigo-400 hover:text-indigo-300 uppercase tracking-wider">
            {label('scenarioLibrary')}
          </Link>
          <Settings className="w-3.5 h-3.5 text-zinc-600" />
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* ===== LEFT RAIL — Control ===== */}
        <aside className="w-72 border-r border-zinc-800/60 flex flex-col bg-zinc-950/40 shrink-0">
          {/* Scenario Selector */}
          <div className="p-3 border-b border-zinc-800/40">
            <div className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-2">{label('presets')}</div>
            <div className="relative">
              <select
                value={selectedScenario.id}
                onChange={(e) => {
                  const sc = mockScenarios.find((s) => s.id === e.target.value)
                  if (sc) setSelectedScenario(sc)
                }}
                className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-200 appearance-none pr-8 focus:border-indigo-500 focus:outline-none"
              >
                {mockScenarios.map((sc) => (
                  <option key={sc.id} value={sc.id}>{sc.title}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-zinc-500 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            {selectedScenario.titleAr && (
              <p className="text-xs text-zinc-500 mt-1 text-right" dir="rtl">{selectedScenario.titleAr}</p>
            )}
          </div>

          {/* Scenario Meta */}
          <div className="p-3 border-b border-zinc-800/40 space-y-2">
            <div className="flex flex-wrap gap-1">
              {selectedScenario.domain && (
                <span className="px-1.5 py-0.5 bg-indigo-500/10 border border-indigo-500/20 rounded text-[9px] font-mono text-indigo-400 uppercase">{selectedScenario.domain}</span>
              )}
              {selectedScenario.region && (
                <span className="px-1.5 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-[9px] font-mono text-cyan-400 uppercase">{selectedScenario.region}</span>
              )}
              {selectedScenario.trigger && (
                <span className="px-1.5 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded text-[9px] font-mono text-amber-400 uppercase">{selectedScenario.trigger}</span>
              )}
              {selectedScenario.riskClass && (
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono uppercase font-bold ${
                  selectedScenario.riskClass === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                  selectedScenario.riskClass === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                  selectedScenario.riskClass === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                  'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                }`}>{selectedScenario.riskClass}</span>
              )}
            </div>
            {selectedScenario.narrative && (
              <p className="text-[11px] text-zinc-500 leading-relaxed">
                {lang === 'ar' && selectedScenario.narrative.ar ? selectedScenario.narrative.ar : selectedScenario.narrative.en}
              </p>
            )}
          </div>

          {/* Composer Toggle */}
          <div className="p-3 border-b border-zinc-800/40">
            <button
              onClick={() => setShowComposer(!showComposer)}
              className="w-full text-[10px] font-mono text-indigo-400 hover:text-indigo-300 uppercase tracking-wider text-center py-1"
            >
              {showComposer ? 'Hide Composer' : 'Open Scenario Composer'}
            </button>
          </div>

          {showComposer && (
            <div className="p-2 border-b border-zinc-800/40 overflow-y-auto max-h-[300px]">
              <ScenarioComposer collapsed={false} />
            </div>
          )}

          {/* Run Button */}
          <div className="p-3 border-b border-zinc-800/40">
            <button
              onClick={runSimulation}
              disabled={isSimulating}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded font-mono text-xs uppercase tracking-wider transition-all ${
                isSimulating
                  ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              }`}
            >
              <Play className="w-4 h-4" />
              {label('runSimulation')}
            </button>
          </div>

          {/* Business Impact */}
          <div className="flex-1 overflow-y-auto p-2">
            {selectedScenario.estimatedImpact && (
              <BusinessImpactCard impact={selectedScenario.estimatedImpact} compact />
            )}
          </div>
        </aside>

        {/* ===== CENTER — Visualization ===== */}
        <main className="flex-1 flex flex-col min-w-0">
          {/* Graph */}
          <div className="flex-1 relative">
            <GraphPanel initialNodes={rfNodes} initialEdges={rfEdges} />
            <div className="absolute top-3 left-3 flex items-center gap-2">
              <span className="text-[9px] font-mono text-zinc-600 uppercase tracking-widest bg-zinc-950/80 px-2 py-1 rounded border border-zinc-800/50">
                Entity Graph
              </span>
            </div>
          </div>

          {/* Timeline */}
          <div className="h-48 border-t border-zinc-800/60 bg-zinc-950/60">
            <TimelinePanel
              steps={timelineSteps}
              activeStep={currentStep}
              onStepChange={setCurrentStep}
            />
          </div>
        </main>

        {/* ===== RIGHT RAIL — Decision ===== */}
        <aside className="w-96 border-l border-zinc-800/60 flex flex-col bg-zinc-950/40 shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-zinc-800/60">
            {(['brief', 'decision'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setRightTab(tab)}
                className={`flex-1 py-2.5 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                  rightTab === tab
                    ? 'text-indigo-400 border-b-2 border-indigo-500 bg-indigo-500/5'
                    : 'text-zinc-600 hover:text-zinc-400'
                }`}
              >
                {tab === 'brief' ? label('intelligenceBrief') : label('decisionOutput')}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            <AnimatePresence mode="wait">
              {rightTab === 'brief' && (
                <motion.div
                  key="brief"
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.15 }}
                >
                  <ReportPanel report={simulationComplete ? mockReport : null} isActive={simulationComplete} />
                </motion.div>
              )}
              {rightTab === 'decision' && (
                <motion.div
                  key="decision"
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.15 }}
                >
                  <DecisionPanel decision={mockDecision} isActive={simulationComplete} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Chat Panel */}
          <div className="h-64 border-t border-zinc-800/60">
            <ChatPanel />
          </div>
        </aside>
      </div>
    </div>
  )
}
